"""Deploy and run the Commercial Insurance demo in Microsoft Fabric.

Authentication is obtained at runtime from Azure CLI. No token or secret is persisted.
All item names and IDs are supplied through arguments or discovered from Fabric.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
FABRIC = "https://api.fabric.microsoft.com/v1"
ONELAKE = "https://onelake.dfs.fabric.microsoft.com"

NOTEBOOKS = [
    ("01_generate_synthetic_data.ipynb", "CI_01_Generate_Synthetic_Data_Dev", "bronze"),
    ("02_create_delta_tables.ipynb", "CI_02_Create_Bronze_Delta_Tables_Dev", "bronze"),
    ("03_underwriting_features.ipynb", "CI_03_Bronze_To_Silver_Features_Dev", "silver"),
    ("04_renewal_risk_pulse.ipynb", "CI_04_Silver_Renewal_Risk_Pulse_Dev", "silver"),
    ("05_material_change_signals.ipynb", "CI_05_Silver_Material_Change_Signals_Dev", "silver"),
    ("06_graph_nodes_edges.ipynb", "CI_06_Silver_To_Gold_Graph_Inputs_Dev", "gold"),
    ("07_live_demo_events.ipynb", "CI_07_Stage_Live_Demo_Events_Dev", "gold"),
]


def az_token(resource: str) -> str:
    executable = shutil.which("az.cmd" if os.name == "nt" else "az")
    if not executable:
        raise RuntimeError("Azure CLI was not found on PATH")
    command = [executable, "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class Fabric:
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {az_token('https://api.fabric.microsoft.com')}", "Content-Type": "application/json"}
        )

    def request(self, method: str, path_or_url: str, **kwargs) -> requests.Response:
        url = path_or_url if path_or_url.startswith("http") else f"{FABRIC}{path_or_url}"
        response = None
        for attempt in range(5):
            try:
                response = self.session.request(method, url, timeout=120, **kwargs)
                break
            except requests.RequestException:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
        assert response is not None
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {url}: HTTP {response.status_code}: {response.text[:2000]}")
        return response

    def wait_lro(self, response: requests.Response, timeout: int = 900) -> dict:
        if response.status_code != 202:
            return response.json() if response.content else {}
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError(f"202 response omitted Location header: {response.headers}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            poll = self.request("GET", location)
            body = poll.json() if poll.content else {}
            status = body.get("status")
            if status in {"Succeeded", "Completed"}:
                return body
            if status in {"Failed", "Cancelled", "Deduped"}:
                raise RuntimeError(f"Fabric operation ended as {status}: {json.dumps(body)}")
            time.sleep(int(poll.headers.get("Retry-After", "5")))
        raise TimeoutError(f"Fabric operation did not complete within {timeout}s: {location}")

    def items(self) -> list[dict]:
        values: list[dict] = []
        url = f"/workspaces/{self.workspace_id}/items"
        while url:
            body = self.request("GET", url).json()
            values.extend(body.get("value", []))
            url = body.get("continuationUri")
        return values

    def create_or_reuse(self, display_name: str, item_type: str, description: str) -> dict:
        matches = [x for x in self.items() if x["displayName"] == display_name and x["type"] == item_type]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple {item_type} items named {display_name}; refusing an ambiguous update")
        if matches:
            print(f"REUSE {item_type} {display_name} {matches[0]['id']}")
            return matches[0]
        response = self.request(
            "POST",
            f"/workspaces/{self.workspace_id}/items",
            data=json.dumps({"displayName": display_name, "type": item_type, "description": description}),
        )
        body = self.wait_lro(response)
        item_id = body.get("id") or body.get("itemId")
        if not item_id:
            matches = [x for x in self.items() if x["displayName"] == display_name and x["type"] == item_type]
            if len(matches) != 1:
                raise RuntimeError(f"Could not discover newly created {item_type} {display_name}: {body}")
            return matches[0]
        item = {"id": item_id, "displayName": display_name, "type": item_type}
        print(f"CREATE {item_type} {display_name} {item_id}")
        return item

    def update_notebook(self, notebook_id: str, notebook: dict) -> None:
        raw = json.dumps(notebook, separators=(",", ":"), ensure_ascii=False).encode()
        body = {
            "definition": {
                "format": "ipynb",
                "parts": [
                    {
                        "path": "notebook-content.ipynb",
                        "payload": base64.b64encode(raw).decode(),
                        "payloadType": "InlineBase64",
                    }
                ],
            }
        }
        response = self.request(
            "POST",
            f"/workspaces/{self.workspace_id}/notebooks/{notebook_id}/updateDefinition",
            data=json.dumps(body),
        )
        self.wait_lro(response)
        print(f"UPDATED Notebook {notebook_id}")

    def recent_jobs(self, item_id: str) -> list[dict]:
        response = self.request("GET", f"/workspaces/{self.workspace_id}/items/{item_id}/jobs/instances")
        return response.json().get("value", [])

    def run_notebook(self, item: dict, lakehouse: dict, timeout: int = 2400) -> dict:
        # Idempotency gate: monitor a non-terminal job submitted in the preceding five minutes.
        now = time.time()
        recent = []
        for job in self.recent_jobs(item["id"]):
            started = job.get("startTimeUtc") or job.get("startTime")
            try:
                epoch = __import__("datetime").datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
            except Exception:
                epoch = 0
            if now - epoch <= 300 and job.get("status") not in {"Completed", "Failed", "Cancelled", "Deduped"}:
                recent.append(job)
        if recent:
            job_id = recent[0]["id"]
            print(f"MONITOR existing Notebook job {item['displayName']} {job_id}")
        else:
            body = {
                "executionData": {
                    "configuration": {
                        "defaultLakehouse": {"id": lakehouse["id"], "name": lakehouse["displayName"]}
                    }
                }
            }
            response = self.request(
                "POST",
                f"/workspaces/{self.workspace_id}/items/{item['id']}/jobs/instances?jobType=RunNotebook",
                data=json.dumps(body),
            )
            job_id = response.headers.get("Location", "").rstrip("/").split("/")[-1]
            if not job_id and response.content:
                job_id = response.json().get("id")
            if not job_id:
                jobs = self.recent_jobs(item["id"])
                if not jobs:
                    raise RuntimeError(f"No job ID returned for {item['displayName']}")
                job_id = jobs[0]["id"]
            print(f"SUBMITTED Notebook {item['displayName']} job={job_id}")

        deadline = time.time() + timeout
        while time.time() < deadline:
            job = self.request(
                "GET", f"/workspaces/{self.workspace_id}/items/{item['id']}/jobs/instances/{job_id}"
            ).json()
            status = job.get("status")
            print(f"JOB {item['displayName']} {job_id} {status}")
            if status == "Completed":
                return job
            if status in {"Failed", "Cancelled", "Deduped"}:
                raise RuntimeError(f"Notebook {item['displayName']} ended as {status}: {json.dumps(job)}")
            time.sleep(20)
        raise TimeoutError(f"Notebook {item['displayName']} timed out: {job_id}")


def normalize_notebook(notebook: dict, lakehouse: dict, workspace_id: str) -> dict:
    for cell in notebook.get("cells", []):
        cell.setdefault("metadata", {})
        if cell.get("cell_type") == "code":
            cell.setdefault("outputs", [])
            cell.setdefault("execution_count", None)
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else str(source)
        lines = text.splitlines(keepends=True)
        if lines and lines[-1].endswith(("\n", "\r")):
            lines[-1] = lines[-1].rstrip("\r\n")
        cell["source"] = lines
    metadata = notebook.setdefault("metadata", {})
    metadata.setdefault("kernelspec", {"display_name": "Synapse PySpark", "language": "Python", "name": "synapse_pyspark"})
    metadata.setdefault("language_info", {"name": "python"})
    metadata.setdefault("dependencies", {})["lakehouse"] = {
        "default_lakehouse": lakehouse["id"],
        "default_lakehouse_name": lakehouse["displayName"],
        "default_lakehouse_workspace_id": workspace_id,
    }
    notebook["nbformat"] = 4
    notebook.setdefault("nbformat_minor", 5)
    return notebook


def parameter_cell(workspace_name: str, bronze_name: str, silver_name: str, gold_name: str) -> dict:
    source = (
        f"ENVIRONMENT = 'dev'\n"
        f"WORKSPACE_NAME = {workspace_name!r}\n"
        f"BRONZE_LAKEHOUSE_NAME = {bronze_name!r}\n"
        f"SILVER_LAKEHOUSE_NAME = {silver_name!r}\n"
        f"GOLD_LAKEHOUSE_NAME = {gold_name!r}\n"
        "RUN_ID = 'rehearsal-001'\n"
        "PHASE = 'baseline'"
    )
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tags": ["parameters"]},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def patch_notebook(notebook: dict, filename: str, args: argparse.Namespace) -> dict:
    notebook["cells"].insert(
        1, parameter_cell(args.workspace_name, args.bronze_name, args.silver_name, args.gold_name)
    )
    if filename not in {"01_generate_synthetic_data.ipynb", "02_create_delta_tables.ipynb"}:
        module_source = (ROOT / "src" / "insurance_demo.py").read_text(encoding="utf-8")
        bootstrap_source = (
            "from pathlib import Path\n"
            "module_path = Path('/lakehouse/default/Files/underwriting_demo/src/insurance_demo.py')\n"
            "module_path.parent.mkdir(parents=True, exist_ok=True)\n"
            f"module_path.write_text({module_source!r}, encoding='utf-8')\n"
            "assert module_path.exists()\n"
        )
        notebook["cells"].insert(
            2,
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": bootstrap_source.splitlines(keepends=True),
            },
        )
    code_cell = next(
        cell
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and (filename == "01_generate_synthetic_data.ipynb" or "import sys" in "".join(cell["source"]))
    )
    code = "".join(code_cell["source"])
    if filename == "02_create_delta_tables.ipynb":
        old = "frame.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(destination)"
        new = """frame = (frame.withColumn('_ingested_at', F.current_timestamp())
                  .withColumn('_source_file', F.lit('Files/underwriting_demo/csv/' + name + '.csv'))
                  .withColumn('_batch_id', F.lit('dev-20260928'))
                  .withColumn('_ingestion_date', F.current_date()))
    frame.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').partitionBy('_ingestion_date').saveAsTable(destination)"""
        if old not in code:
            raise RuntimeError("Bronze notebook write pattern not found")
        code = code.replace(old, new, 1)

    if filename == "03_underwriting_features.ipynb":
        old = "data = {name: [row.asDict() for row in spark.table(TABLE_PREFIX + name).collect()] for name in build_data()}"
        new = f"""BRONZE_ROOT = 'abfss://{args.workspace_id}@onelake.dfs.fabric.microsoft.com/{args.bronze_id}/Tables'
def read_bronze(name):
    return spark.read.format('delta').load(f'{{BRONZE_ROOT}}/{{(TABLE_PREFIX + name).lower()}}')
data = {{name: [row.asDict() for row in read_bronze(name).collect()] for name in build_data()}}"""
        if old not in code:
            raise RuntimeError("Silver source pattern not found")
        code = code.replace(old, new)

    if filename == "06_graph_nodes_edges.ipynb":
        marker = "for entity, table in ENTITIES.items():"
        prefix = f"""spark.conf.set('spark.sql.parquet.vorder.default', 'true')
spark.conf.set('spark.databricks.delta.optimizeWrite.enabled', 'true')
spark.conf.set('spark.databricks.delta.optimizeWrite.binSize', '1g')
BRONZE_ROOT = 'abfss://{args.workspace_id}@onelake.dfs.fabric.microsoft.com/{args.bronze_id}/Tables'
SILVER_ROOT = 'abfss://{args.workspace_id}@onelake.dfs.fabric.microsoft.com/{args.silver_id}/Tables'
CURATED = {{'UnderwritingFeatures', 'RiskPulse', 'RenewalSignals'}}
SOURCE_TABLES = list(build_data().keys())
for table in SOURCE_TABLES:
    root = SILVER_ROOT if table in CURATED else BRONZE_ROOT
    frame = spark.read.format('delta').load(f'{{root}}/{{(TABLE_PREFIX + table).lower()}}')
    frame.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(TABLE_PREFIX + table)

"""
        if marker not in code:
            raise RuntimeError("Gold graph loop not found")
        code = code.replace(marker, prefix + marker)

    if filename == "07_live_demo_events.ipynb":
        code = code.replace("RUN_ID = 'rehearsal-001'\nPHASE = 'baseline'\n", "")

    code_cell["source"] = code.splitlines(keepends=True)
    if code_cell["source"] and code_cell["source"][-1].endswith(("\n", "\r")):
        code_cell["source"][-1] = code_cell["source"][-1].rstrip("\r\n")
    return notebook


def upload_onelake(workspace_id: str, lakehouse_id: str, relative_path: str, source: Path) -> None:
    token = az_token("https://storage.azure.com/")
    url = f"{ONELAKE}/{workspace_id}/{lakehouse_id}/{relative_path}"
    headers = {"Authorization": f"Bearer {token}", "x-ms-version": "2023-11-03"}
    create = requests.put(url, params={"resource": "file"}, headers=headers, timeout=120)
    if create.status_code not in {200, 201}:
        raise RuntimeError(f"OneLake create {relative_path}: {create.status_code} {create.text}")
    data = source.read_bytes()
    append = requests.patch(url, params={"action": "append", "position": 0}, headers=headers, data=data, timeout=180)
    if append.status_code not in {200, 202}:
        raise RuntimeError(f"OneLake append {relative_path}: {append.status_code} {append.text}")
    flush = requests.patch(
        url, params={"action": "flush", "position": len(data)}, headers=headers, timeout=120
    )
    if flush.status_code not in {200, 201, 202}:
        raise RuntimeError(f"OneLake flush {relative_path}: {flush.status_code} {flush.text}")
    print(f"UPLOAD {source} -> {relative_path} ({len(data)} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--workspace-name", default="Fabric_AI")
    parser.add_argument("--bronze-name", default="CI_Bronze_Dev")
    parser.add_argument("--silver-name", default="CI_Silver_Dev")
    parser.add_argument("--gold-name", default="CI_Gold_Dev")
    parser.add_argument("--phase", choices=["deploy", "run", "all"], default="all")
    parser.add_argument("--start-at", type=int, choices=range(1, 8), default=1)
    args = parser.parse_args()

    fabric = Fabric(args.workspace_id)
    items = fabric.items()
    layers = {}
    for layer, name in [
        ("bronze", args.bronze_name),
        ("silver", args.silver_name),
        ("gold", args.gold_name),
    ]:
        matches = [x for x in items if x["displayName"] == name and x["type"] == "Lakehouse"]
        if len(matches) != 1:
            raise RuntimeError(f"Expected one Lakehouse named {name}, found {len(matches)}")
        layers[layer] = matches[0]
    args.bronze_id = layers["bronze"]["id"]
    args.silver_id = layers["silver"]["id"]
    args.gold_id = layers["gold"]["id"]

    deployed = []
    if args.phase in {"deploy", "all"}:
        for filename, display_name, layer in NOTEBOOKS:
            item = fabric.create_or_reuse(
                display_name,
                "Notebook",
                f"Commercial Insurance demo notebook {filename}; environment=dev; layer={layer}.",
            )
            notebook = json.loads((ROOT / "notebooks" / filename).read_text(encoding="utf-8"))
            notebook = patch_notebook(notebook, filename, args)
            notebook = normalize_notebook(notebook, layers[layer], args.workspace_id)
            fabric.update_notebook(item["id"], notebook)
            deployed.append((item, layer))
    else:
        current = fabric.items()
        for _, display_name, layer in NOTEBOOKS:
            matches = [x for x in current if x["displayName"] == display_name and x["type"] == "Notebook"]
            if len(matches) != 1:
                raise RuntimeError(f"Expected one deployed Notebook named {display_name}, found {len(matches)}")
            deployed.append((matches[0], layer))

    if args.phase in {"run", "all"}:
        outcomes = []
        for item, layer in deployed[args.start_at - 1 :]:
            outcomes.append(
                {
                    "name": item["displayName"],
                    "itemId": item["id"],
                    "layer": layer,
                    "job": fabric.run_notebook(item, layers[layer]),
                }
            )
        print("OUTCOMES")
        print(json.dumps(outcomes, indent=2))


if __name__ == "__main__":
    main()
