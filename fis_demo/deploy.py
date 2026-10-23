"""Deploy only to the dedicated, single-user FIS demo workspace."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from fis_demo import artifacts
from fis_demo.data import AS_OF, FACTS, RELATIONSHIPS, ROOT, build_data, validate


sys.path.insert(0, str(ROOT.parent / "deployment"))
from fabric_deploy import Fabric, az_token, normalize_notebook  # noqa: E402


RECEIPT = ROOT / "deployment.json"
PRIVACY_MARKER = "FIS synthetic FP&A demo; dedicated single-user workspace."
NAMES = {
    "bronze": "FIS_Finance_Bronze", "silver": "FIS_Finance_Silver", "gold": "FIS_Finance_Gold",
    "notebook": "FIS_01_Finance_Medallion", "model": "FIS_Finance_IQ_Model",
    "report": "FIS Finance IQ - Synthetic FP&A", "ontology": "FIS_Finance_Ontology",
    "graph": "FIS_Finance_Relationship_Graph", "agent": "FIS_Finance_Data_Agent",
}


def save(receipt: dict) -> None:
    receipt["updatedUtc"] = datetime.now(timezone.utc).isoformat()
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def response_json(response: requests.Response) -> dict:
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code} {response.url}: {response.text[:3000]}")
    return response.json() if response.content else {}


def verify_privacy(fabric: Fabric, name: str) -> dict:
    workspace = fabric.request("GET", f"/workspaces/{fabric.workspace_id}").json()
    if workspace["displayName"] != name or PRIVACY_MARKER not in workspace.get("description", ""):
        raise ValueError("Refusing to modify a workspace without the dedicated FIS identity and description marker")
    token = az_token("https://api.fabric.microsoft.com")
    payload = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assignments = []
    url = f"/workspaces/{fabric.workspace_id}/roleAssignments"
    while url:
        page = fabric.request("GET", url).json()
        assignments.extend(page.get("value", []))
        url = page.get("continuationUri")
    if len(assignments) != 1:
        raise ValueError(f"Expected exactly one workspace role assignment, found {len(assignments)}")
    assignment = assignments[0]
    if assignment["principal"]["id"] != claims["oid"] or assignment["principal"]["type"] != "User" or assignment["role"] != "Admin":
        raise ValueError("Workspace must have only the authenticated user as Admin")
    return {
        "workspace": workspace, "roleAssignments": assignments, "tenantId": claims["tid"],
        "explicitMembers": 1, "privacyVerified": True,
        "boundary": "Only the caller is assigned a workspace role. Tenant administrative policies still apply.",
    }


def parts(files: dict[str, str | dict]) -> list[dict]:
    return [{
        "path": name, "payloadType": "InlineBase64",
        "payload": base64.b64encode((value if isinstance(value, str) else json.dumps(value)).encode("utf-8")).decode("ascii"),
    } for name, value in files.items()]


def upsert(fabric: Fabric, name: str, item_type: str, collection: str,
           files: dict[str, str | dict], fmt: str | None = None) -> dict:
    matches = [item for item in fabric.items() if item["displayName"] == name and item["type"] == item_type]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous {item_type}: {name}")
    definition = {"parts": parts(files)}
    if fmt is not None:
        definition["format"] = fmt
    path = f"/workspaces/{fabric.workspace_id}/{collection}"
    if item_type == "Ontology" and not matches:
        matches = [fabric.create_or_reuse(name, item_type, "FIS synthetic finance demo. Not actual FIS results.")]
    if matches:
        item = matches[0]
        result = fabric.request("POST", f"{path}/{item['id']}/updateDefinition", json={"definition": definition})
    else:
        result = fabric.request("POST", path, json={
            "displayName": name, "description": "FIS synthetic finance demo. Not actual FIS results.",
            "definition": definition,
        })
    fabric.wait_lro(result)
    for _ in range(30):
        matches = [item for item in fabric.items() if item["displayName"] == name and item["type"] == item_type]
        if len(matches) == 1:
            print(f"DEPLOYED {item_type} {name} {matches[0]['id']}", flush=True)
            return matches[0]
        time.sleep(2)
    raise TimeoutError(f"Could not discover deployed {item_type} {name}")


def get_definition(fabric: Fabric, collection: str, item_id: str) -> dict[str, str]:
    response = fabric.request("POST", f"/workspaces/{fabric.workspace_id}/{collection}/{item_id}/getDefinition")
    if response.status_code == 202:
        fabric.wait_lro(response)
        body = fabric.request("GET", response.headers["Location"].rstrip("/") + "/result").json()
    else:
        body = response.json()
    return {part["path"]: base64.b64decode(part["payload"]).decode("utf-8") for part in body["definition"]["parts"]}


def read_live_validation(fabric: Fabric, gold: str) -> dict:
    response = requests.get(
        f"https://onelake.dfs.fabric.microsoft.com/{fabric.workspace_id}/{gold}/Files/fis_finance_iq/live-validation.json",
        headers={"Authorization": f"Bearer {az_token('https://storage.azure.com/')}"},
        timeout=120,
    )
    report = response_json(response)
    expected = validate(build_data())
    if report["status"] != "PASS" or report["tableRows"] != expected["tableRows"] or report["metrics"] != expected["metrics"]:
        raise ValueError("Live Gold validation does not match the expected finance demo")
    if report["foreignKeyChecks"] != 51840 or sum(report["edgeRows"].values()) != 51840:
        raise ValueError("Live relationship checks or materialized graph edges do not match")
    return report


def deploy_data(fabric: Fabric, receipt: dict) -> None:
    layers = {}
    for layer in ("bronze", "silver", "gold"):
        layers[layer] = fabric.create_or_reuse(
            NAMES[layer], "Lakehouse", f"FIS synthetic finance {layer} layer; isolated demo only.",
        )
    receipt["lakehouses"] = layers
    document = artifacts.notebook(fabric.workspace_id, layers["bronze"]["id"], layers["silver"]["id"], layers["gold"]["id"])
    document = normalize_notebook(document, layers["gold"], fabric.workspace_id)
    item = upsert(fabric, NAMES["notebook"], "Notebook", "notebooks", {"notebook-content.ipynb": document}, "ipynb")
    receipt["notebook"] = item
    save(receipt)
    receipt["notebookJob"] = fabric.run_notebook(item, layers["gold"])
    save(receipt)
    receipt["liveData"] = read_live_validation(fabric, layers["gold"]["id"])
    save(receipt)


def pbi_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {az_token('https://analysis.windows.net/powerbi/api')}"})
    return session


def dax(session: requests.Session, workspace: str, model: str, query: str) -> list[dict]:
    body = response_json(session.post(
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets/{model}/executeQueries",
        json={"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}, timeout=120,
    ))
    if body.get("error") or any(result.get("error") for result in body.get("results", [])):
        raise RuntimeError(f"DAX query returned errors: {json.dumps(body)}")
    return body["results"][0]["tables"][0].get("rows", [])


def refresh_model(session: requests.Session, workspace: str, model: str) -> None:
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets/{model}/refreshes"
    response_json(session.post(url, json={"type": "Full"}, timeout=120))
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        history = response_json(session.get(url, params={"$top": 1}, timeout=60))
        latest = history.get("value", [{}])[0]
        status = latest.get("status")
        if status == "Completed":
            return
        if status in {"Failed", "Disabled", "Cancelled"}:
            raise RuntimeError(f"Semantic model refresh failed: {json.dumps(latest)}")
        time.sleep(5)
    raise TimeoutError("Direct Lake semantic model refresh did not complete within 900 seconds")


def verify_model(fabric: Fabric, model: str) -> dict:
    session = pbi_session()
    metric_measures = {
        "ActualRevenueYTD": "Actual Revenue YTD", "PlanRevenueYTD": "Plan Revenue YTD",
        "ActualOpexYTD": "Actual Opex YTD", "PlanOpexYTD": "Plan Opex YTD",
        "ActualProfitYTD": "Actual Operating Profit YTD", "PlanProfitYTD": "Plan Operating Profit YTD",
        "RevenueVarianceYTD": "Revenue Variance YTD", "ExpenseVarianceYTD": "Favorable Expense Variance YTD",
        "ProfitVarianceYTD": "Operating Profit Variance YTD", "ForecastRevenueFY": "Forecast Revenue FY",
        "PlanRevenueFY": "Plan Revenue FY", "ForecastProfitFY": "Forecast Operating Profit FY",
        "PlanProfitFY": "Plan Operating Profit FY", "ForecastProfitVarianceFY": "Forecast Operating Profit Variance FY",
    }
    fields = [f'"{key}", [{measure}]' for key, measure in metric_measures.items()]
    hero_filter = "'account'[Account]=\"500100\", 'cost_center'[CostCenter]=\"300110\", 'product'[ProductLine]=\"DIGITAL\""
    fields += [
        f'"CloudDigitalActualYTD", CALCULATE([Actual Opex YTD], {hero_filter})',
        f'"CloudDigitalPlanYTD", CALCULATE([Plan Opex YTD], {hero_filter})',
    ]
    rows = dax(session, fabric.workspace_id, model, "EVALUATE ROW(" + ",".join(fields) + ")")
    if len(rows) != 1:
        raise ValueError(f"Expected one CFO metric row, received {len(rows)}")
    actual = {key.strip("[]"): value for key, value in rows[0].items()}
    expected = validate(build_data())["metrics"]
    for key, value in actual.items():
        if value is None or abs(value - expected[key]) > 0.005:
            raise ValueError(f"DAX KPI mismatch for {key}: {value} != {expected[key]}")
    if set(actual) != set(metric_measures) | {"CloudDigitalActualYTD", "CloudDigitalPlanYTD"}:
        raise ValueError("DAX response omitted required CFO metrics")

    filters = [
        ("account", "ACCOUNT", "Account", "500100", '"500100"'),
        ("cost_center", "COSTCENTER", "CostCenter", "300110", '"300110"'),
        ("DIM_DATE", "DATE", "DATE", "2026-09-01", "DATE(2026,9,1)"),
        ("product", "PRODUCTLINE", "ProductLine", "DIGITAL", '"DIGITAL"'),
    ]
    tables = build_data()
    counts, expected_counts = [], {}
    for dimension, fact_column, column, value, literal in filters:
        for fact in FACTS:
            alias = f"{fact}_{dimension}"
            counts.append(f'"{alias}", CALCULATE(COUNTROWS(\'{fact}\'), \'{dimension}\'[{column}]={literal})')
            expected_counts[alias] = sum(row[fact_column] == value for row in tables[fact])
    filter_rows = dax(session, fabric.workspace_id, model, "EVALUATE ROW(" + ",".join(counts) + ")")
    filtered_counts = {key.strip("[]"): value for key, value in filter_rows[0].items()}
    if filtered_counts != expected_counts:
        raise ValueError(f"One or more of the 12 relationship filters failed: {filtered_counts}")
    definition = get_definition(fabric, "semanticModels", model)
    relationship_text = definition["definition/relationships.tmdl"]
    if relationship_text.count("relationship ") != 12:
        raise ValueError("Deployed semantic model does not contain exactly 12 relationships")
    return {"status": "PASS", "metrics": actual, "relationshipFilterChecks": filtered_counts, "relationships": 12}


def deploy_semantic_and_report(fabric: Fabric, receipt: dict) -> None:
    layers = receipt["lakehouses"]
    gold = layers["gold"]["id"]
    artifacts.build(fabric.workspace_id, layers["bronze"]["id"], layers["silver"]["id"], gold)
    model = upsert(fabric, NAMES["model"], "SemanticModel", "semanticModels",
                   artifacts.semantic_files(fabric.workspace_id, gold), "TMDL")
    receipt["semanticModel"] = model
    save(receipt)
    session = pbi_session()
    refresh_model(session, fabric.workspace_id, model["id"])
    receipt["semanticVerification"] = verify_model(fabric, model["id"])
    save(receipt)
    report_files = artifacts.report_files(model["id"])
    artifacts.write_bundle(ROOT / "generated" / "report", report_files)
    report = upsert(fabric, NAMES["report"], "Report", "reports", report_files, "PBIR")
    details = response_json(session.get(
        f"https://api.powerbi.com/v1.0/myorg/groups/{fabric.workspace_id}/reports/{report['id']}", timeout=60,
    ))
    if details["datasetId"] != model["id"]:
        raise ValueError("The report is bound to an unexpected semantic model")
    receipt["report"] = {**report, "url": details["webUrl"], "datasetId": details["datasetId"]}
    save(receipt)


def refresh_graph(fabric: Fabric, graph_id: str) -> dict:
    jobs = fabric.recent_jobs(graph_id)
    active = [job for job in jobs if job.get("status") in {"NotStarted", "InProgress"}]
    if active:
        job_id = active[0]["id"]
    else:
        response = fabric.request("POST", f"/workspaces/{fabric.workspace_id}/graphModels/{graph_id}/jobs/refreshGraph/instances")
        job_id = response.headers.get("Location", "").rstrip("/").split("/")[-1]
        if not job_id:
            raise ValueError("Graph refresh did not return a job location")
    deadline = time.monotonic() + 1500
    while time.monotonic() < deadline:
        job = fabric.request("GET", f"/workspaces/{fabric.workspace_id}/items/{graph_id}/jobs/instances/{job_id}").json()
        if job["status"] in {"Completed", "Succeeded"}:
            return job
        if job["status"] in {"Failed", "Cancelled", "Deduped"}:
            raise RuntimeError(f"Graph refresh failed: {json.dumps(job)}")
        time.sleep(10)
    raise TimeoutError(f"Graph refresh did not finish: {job_id}")


def verify_graph(fabric: Fabric, graph_id: str) -> list[dict]:
    results = []
    for query, expected_rows in zip(artifacts.GQL_QUERIES, (9, 6, 12), strict=True):
        result = fabric.request(
            "POST", f"/workspaces/{fabric.workspace_id}/graphModels/{graph_id}/executeQuery?beta=true",
            json={"query": query},
        ).json()
        if result.get("status", {}).get("code") != "00000":
            raise RuntimeError(f"GQL execution failed: {json.dumps(result)}")
        rows = result.get("result", {}).get("data", [])
        if len(rows) != expected_rows:
            raise ValueError(f"GQL returned {len(rows)} rows; expected {expected_rows}")
        results.append({"status": "00000", "rows": len(rows), "sample": rows[:2]})
    return results


def agent_files(workspace: str, model: str, gold: str) -> dict[str, dict]:
    schema = artifacts.SCHEMA
    instructions = (
        "You are the FIS Finance IQ synthetic FP&A demo assistant. All figures are fictional, in USD, "
        "and must never be described as FIS reported financial results. As-of date: 2026-09-30. "
        "Use FIS_Finance_IQ_Model saved measures for governed KPIs; use the Gold Lakehouse for RecordID evidence. "
        "ACTUALS contains 2025 plus January-September 2026. Always filter YEAR=2026 for current-year questions. "
        "PLAN is full-year 2026; FORECAST is the September full-year outlook, including closed-month actuals. "
        "Never add ACTUALS, PLAN and FORECAST together. Compare YTD actuals with YTD plan, not full-year plan. "
        "Amounts are positive for both revenue and expense. Revenue variance is actual minus plan; favorable expense "
        "variance is plan minus actual. Operating profit is revenue minus operating expense, not GAAP net income or EBITDA. "
        "AmountCents is integer USD cents; divide by 100 for dollars. Amount is already dollars. "
        "For Digital Banking cloud investigation use ACCOUNT=500100, COSTCENTER=300110, PRODUCTLINE=DIGITAL. "
        "Join each fact separately to account.Account, cost_center.CostCenter, DIM_DATE.DATE, product.ProductLine. "
        "Never join facts without all four grain keys (ACCOUNT,COSTCENTER,PRODUCTLINE,DATE). "
        "Cite source RecordIDs, scenario, version and period; flag uncertainties. No accounting entries, notifications or autonomous decisions."
    )
    model_source = {
        "$schema": f"{schema}/dataAgent/definition/dataSource/1.0.0/schema.json",
        "artifactId": model, "workspaceId": workspace, "displayName": NAMES["model"],
        "type": "semantic_model", "dataSourceInstructions": instructions, "metadata": {},
        "userDescription": "Seven-table Direct Lake model, 12 shared-dimension relationships, governed finance measures.",
        "elements": [{
            "id": artifacts.stable_id(f"agent/model/{name}"), "is_selected": True,
            "display_name": name, "type": "semantic_model.table", "children": [],
        } for name in build_data()],
    }
    lakehouse_source = {
        "$schema": f"{schema}/dataAgent/definition/dataSource/1.0.0/schema.json",
        "artifactId": gold, "workspaceId": workspace, "displayName": NAMES["gold"],
        "type": "lakehouse_tables", "dataSourceInstructions": instructions, "metadata": {},
        "userDescription": "Synthetic finance evidence and variance drivers; Amount is USD and AmountCents is cents.",
        "elements": [{
            "id": artifacts.stable_id("agent/schema"), "is_selected": True, "display_name": "dbo",
            "type": "lakehouse_tables.schema", "children": [{
                "id": artifacts.stable_id(f"agent/lakehouse/{name}"), "is_selected": True,
                "display_name": name.lower(), "type": "lakehouse_tables.table", "children": [],
            } for name in [*build_data(), "variance_drivers"]],
        }],
    }
    return {
        "Files/Config/data_agent.json": {"$schema": f"{schema}/dataAgent/definition/dataAgent/2.1.0/schema.json"},
        "Files/Config/draft/stage_config.json": {
            "$schema": f"{schema}/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
            "aiInstructions": instructions,
        },
        f"Files/Config/draft/semantic_model-{NAMES['model']}/datasource.json": model_source,
        f"Files/Config/draft/lakehouse-tables-{NAMES['gold']}/datasource.json": lakehouse_source,
        f"Files/Config/draft/lakehouse-tables-{NAMES['gold']}/fewshots.json": {
            "$schema": f"{schema}/dataAgent/definition/fewShots/1.0.0/schema.json",
            "fewShots": [{"id": artifacts.stable_id(f"fewshot/{index}"), **example}
                         for index, example in enumerate(artifacts.FEW_SHOTS, 1)],
        },
    }


def deploy_iq(fabric: Fabric, receipt: dict) -> None:
    gold = receipt["lakehouses"]["gold"]["id"]
    if len(receipt.get("graph", {}).get("gqlVerification", [])) != 3:
        graph = upsert(fabric, NAMES["graph"], "GraphModel", "graphModels",
                       artifacts.graph_files(fabric.workspace_id, gold), "json")
        receipt["graph"] = graph
        save(receipt)
        receipt["graph"]["refreshJob"] = refresh_graph(fabric, graph["id"])
        receipt["graph"]["gqlVerification"] = verify_graph(fabric, graph["id"])
        save(receipt)
    else:
        print("REUSE previously verified relationship graph", flush=True)
    if receipt.get("ontologyDateKeyJob", {}).get("status") != "Completed":
        date_notebook = artifacts.ontology_date_keys_notebook(fabric.workspace_id, gold)
        artifacts.write_bundle(ROOT / "generated", {"FIS_02_Prepare_Ontology_Date_Keys.ipynb": date_notebook})
        date_item = upsert(
            fabric, "FIS_02_Prepare_Ontology_Date_Keys", "Notebook", "notebooks",
            {"notebook-content.ipynb": date_notebook}, "ipynb",
        )
        receipt["ontologyDateKeyNotebook"] = date_item
        save(receipt)
        receipt["ontologyDateKeyJob"] = fabric.run_notebook(date_item, receipt["lakehouses"]["gold"])
        save(receipt)
    ontology = upsert(fabric, NAMES["ontology"], "Ontology", "ontologies",
                      artifacts.ontology_files(fabric.workspace_id, gold))
    receipt["ontology"] = ontology
    definition = get_definition(fabric, "ontologies", ontology["id"])
    entity_count = sum(path.startswith("entities/") and path.endswith(".tmdl") for path in definition)
    relationship_count = sum(
        line.startswith("entityRelationship ")
        for line in definition.get("entityRelationships.tmdl", "").splitlines()
    )
    if (entity_count, relationship_count) != (7, 12):
        raise ValueError(f"Unexpected deployed ontology shape: {entity_count} entities, {relationship_count} relationships")
    receipt["ontology"].update({"entityTypes": entity_count, "relationshipTypes": relationship_count})
    save(receipt)
    model = receipt["semanticModel"]["id"]
    definitions = agent_files(fabric.workspace_id, model, gold)
    artifacts.write_bundle(ROOT / "generated" / "agent", definitions)
    agent = upsert(fabric, NAMES["agent"], "DataAgent", "dataAgents", definitions)
    receipt["agent"] = agent
    save(receipt)
    response = fabric.request(
        "POST", f"/workspaces/{fabric.workspace_id}/dataAgents/{agent['id']}/staging/publish",
        json={"publishedDescription": "FIS synthetic FP&A demo; governed measures and row-level evidence."},
    )
    fabric.wait_lro(response)
    published = get_definition(fabric, "dataAgents", agent["id"])
    if "Files/Config/published/stage_config.json" not in published:
        raise ValueError("Data Agent publish returned without a published configuration")
    receipt["agent"].update({
        "published": True, "sqlExamplesValidatedInSpark": 4,
        "conversationalResponsesVerified": False,
    })
    save(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--workspace-name", default="FIS-Finance-IQ")
    parser.add_argument("--phase", choices=("data", "semantic", "iq", "verify", "all"), default="all")
    args = parser.parse_args()
    fabric = Fabric(args.workspace_id)
    privacy = verify_privacy(fabric, args.workspace_name)
    receipt = json.loads(RECEIPT.read_text()) if RECEIPT.exists() else {
        "baseRepository": "https://github.com/deepugun/fabric-iq-commercial-insurance-poc",
        "baseCommit": "501f412f68ce4b048d5eb4fadcf3e04abe00265f",
        "synthetic": True, "asOf": AS_OF.isoformat(),
    }
    if receipt.get("workspaceId", args.workspace_id) != args.workspace_id:
        raise ValueError("Deployment receipt belongs to a different workspace; refusing to overwrite it")
    receipt.update({
        "workspaceId": args.workspace_id, "workspaceName": args.workspace_name, "privacy": privacy,
        "workspaceUrl": f"https://app.fabric.microsoft.com/groups/{args.workspace_id}/list",
        "status": "in_progress",
    })
    save(receipt)
    try:
        if args.phase in {"data", "all"}:
            deploy_data(fabric, receipt)
        if args.phase in {"semantic", "all"}:
            deploy_semantic_and_report(fabric, receipt)
        if args.phase in {"iq", "all"}:
            deploy_iq(fabric, receipt)
        if args.phase in {"verify", "all"}:
            receipt["liveData"] = read_live_validation(fabric, receipt["lakehouses"]["gold"]["id"])
            receipt["semanticVerification"] = verify_model(fabric, receipt["semanticModel"]["id"])
            receipt["graph"]["gqlVerification"] = verify_graph(fabric, receipt["graph"]["id"])
        receipt["privacy"] = verify_privacy(fabric, args.workspace_name)
        complete = (
            all(key in receipt for key in ("liveData", "semanticVerification", "report", "ontology", "graph", "agent"))
            and receipt["agent"].get("published") is True
            and len(receipt["graph"].get("gqlVerification", [])) == 3
            and receipt["ontology"].get("relationshipTypes") == 12
        )
        receipt["status"] = "verified" if complete else "phase_complete"
        receipt.pop("error", None)
        save(receipt)
    except (RuntimeError, ValueError, TimeoutError, requests.RequestException) as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        save(receipt)
        raise
    print(json.dumps({"status": receipt["status"], "workspaceUrl": receipt["workspaceUrl"]}, indent=2))


if __name__ == "__main__":
    main()
