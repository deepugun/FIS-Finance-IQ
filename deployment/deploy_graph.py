"""Deploy the project's Graph Model definition from its generated manifest."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import uuid
from pathlib import Path

from fabric_deploy import Fabric


ROOT = Path(__file__).resolve().parents[1]


def infer_type(values: list[str]) -> str:
    nonempty = [v for v in values if v != ""]
    if not nonempty:
        return "STRING"
    if all(v.lower() in {"true", "false"} for v in nonempty):
        return "BOOLEAN"
    try:
        [int(v) for v in nonempty]
        return "INT"
    except ValueError:
        pass
    try:
        [float(v) for v in nonempty]
        return "FLOAT"
    except ValueError:
        pass
    if all(len(v) >= 10 and v[4:5] == "-" and v[7:8] == "-" for v in nonempty):
        return "DATETIME"
    return "STRING"


def csv_schema(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [{"name": name, "type": infer_type([row[name] for row in rows])} for name in rows[0]]


def part(path: str, content: dict) -> dict:
    payload = base64.b64encode(json.dumps(content, separators=(",", ":")).encode()).decode()
    return {"path": path, "payload": payload, "payloadType": "InlineBase64"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--gold-id", required=True)
    parser.add_argument("--graph-name", default="CI_Underwriting_Graph_Dev")
    parser.add_argument("--refresh", action="store_true", help="Wait for or trigger RefreshGraph job.")
    parser.add_argument("--verify", action="store_true", help="Execute all GQL queries in gql/underwriting.gql.")
    args = parser.parse_args()

    manifest = json.loads((ROOT / "graph" / "mapping-manifest.json").read_text(encoding="utf-8"))
    prefix = (
        f"abfss://{args.workspace_id}@onelake.dfs.fabric.microsoft.com/"
        f"{args.gold_id}/Tables"
    )
    data_sources = []
    node_tables = []
    edge_tables = []
    node_types = []
    edge_types = []
    positions = {}
    styles = {}

    for index, node in enumerate(manifest["nodes"]):
        label = node["label"]
        table = node["table"].lower()
        alias = f"{label}_nodeType"
        source_name = f"{label}_Table"
        source_file = ROOT / "graph" / f"{node['table']}.csv"
        properties = csv_schema(source_file)
        data_sources.append(
            {"name": source_name, "type": "DeltaTable", "properties": {"path": f"{prefix}/{table}"}}
        )
        node_tables.append(
            {
                "id": f"{label}_{uuid.uuid4()}",
                "nodeTypeAlias": alias,
                "dataSourceName": source_name,
                "propertyMappings": [
                    {"propertyName": prop["name"], "sourceColumn": prop["name"]} for prop in properties
                ],
            }
        )
        node_types.append(
            {
                "alias": alias,
                "labels": [label],
                "primaryKeyProperties": [node["key"]],
                "properties": properties,
            }
        )
        positions[alias] = {"x": (index % 5) * 240, "y": (index // 5) * 160}
        styles[alias] = {"size": 30}

    for edge in manifest["edges"]:
        label = edge["label"]
        source_label = edge["sourceLabel"]
        target_label = edge["targetLabel"]
        table = edge["table"].lower()
        alias = f"{source_label}_{label}_{target_label}_edgeType"
        source_name = f"{source_label}_{label}_{target_label}_Table"
        properties = [
            {"name": "EdgeId", "type": "STRING"},
            {"name": "SourceId", "type": "STRING"},
            {"name": "TargetId", "type": "STRING"},
        ]
        data_sources.append(
            {"name": source_name, "type": "DeltaTable", "properties": {"path": f"{prefix}/{table}"}}
        )
        edge_tables.append(
            {
                "id": f"{source_label}_{label}_{target_label}_{uuid.uuid4()}",
                "edgeTypeAlias": alias,
                "dataSourceName": source_name,
                "sourceNodeKeyColumns": [edge["sourceColumn"]],
                "destinationNodeKeyColumns": [edge["targetColumn"]],
                "propertyMappings": [
                    {"propertyName": prop["name"], "sourceColumn": prop["name"]} for prop in properties
                ],
            }
        )
        edge_types.append(
            {
                "alias": alias,
                "labels": [label],
                "sourceNodeType": {"alias": f"{source_label}_nodeType"},
                "destinationNodeType": {"alias": f"{target_label}_nodeType"},
                "properties": properties,
            }
        )
        styles[alias] = {"size": 20}

    definitions = [
        part(
            "dataSources.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphIndex/definition/dataSources/1.0.0/schema.json",
                "dataSources": data_sources,
            },
        ),
        part(
            "graphDefinition.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphIndex/definition/graphDefinition/1.0.0/schema.json",
                "nodeTables": node_tables,
                "edgeTables": edge_tables,
            },
        ),
        part(
            "graphType.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphIndex/definition/graphType/1.0.0/schema.json",
                "nodeTypes": node_types,
                "edgeTypes": edge_types,
            },
        ),
        part(
            "stylingConfiguration.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/graphIndex/definition/stylingConfiguration/1.0.0/schema.json",
                "modelLayout": {
                    "positions": positions,
                    "styles": styles,
                    "pan": {"x": 0, "y": 0},
                    "zoomLevel": 1,
                },
            },
        ),
    ]

    fabric = Fabric(args.workspace_id)
    matches = [
        item
        for item in fabric.items()
        if item["displayName"] == args.graph_name and item["type"] == "GraphModel"
    ]
    if matches:
        item = matches[0]
        response = fabric.request(
            "POST",
            f"/workspaces/{args.workspace_id}/graphModels/{item['id']}/updateDefinition",
            data=json.dumps({"definition": {"format": "json", "parts": definitions}}),
        )
        fabric.wait_lro(response)
    else:
        response = fabric.request(
            "POST",
            f"/workspaces/{args.workspace_id}/graphModels",
            data=json.dumps(
                {
                    "displayName": args.graph_name,
                    "description": "Commercial Insurance relationship graph. Environment dev.",
                    "definition": {"format": "json", "parts": definitions},
                }
            ),
        )
        fabric.wait_lro(response)
        item = next(
            item
            for item in fabric.items()
            if item["displayName"] == args.graph_name and item["type"] == "GraphModel"
        )

    if args.refresh:
        import time

        jobs = fabric.recent_jobs(item["id"])
        active = [j for j in jobs if j.get("status") in {"NotStarted", "InProgress"}]
        if active:
            job_id = active[0]["id"]
        else:
            r = fabric.request(
                "POST",
                f"/workspaces/{args.workspace_id}/graphModels/{item['id']}/jobs/refreshGraph/instances",
            )
            loc = r.headers.get("Location", "")
            job_id = loc.rstrip("/").split("/")[-1]
        for _ in range(90):
            job = fabric.request(
                "GET",
                f"/workspaces/{args.workspace_id}/items/{item['id']}/jobs/instances/{job_id}",
            ).json()
            if job.get("status") in {"Completed", "Succeeded"}:
                item["refreshJob"] = job
                break
            if job.get("status") in {"Failed", "Cancelled", "Deduped"}:
                raise RuntimeError(f"Graph refresh ended as {job.get('status')}: {json.dumps(job)}")
            time.sleep(10)

    if args.verify:
        gql_text = (ROOT / "gql" / "underwriting.gql").read_text(encoding="utf-8").strip()
        queries = [q.strip() for q in gql_text.split("\n\n") if q.strip()]
        results = []
        for idx, query in enumerate(queries, start=1):
            res = fabric.request(
                "POST",
                f"/workspaces/{args.workspace_id}/graphModels/{item['id']}/executeQuery?beta=true",
                data=json.dumps({"query": query}),
            ).json()
            code = res.get("status", {}).get("code")
            rows = res.get("result", {}).get("data", [])
            if code != "00000":
                raise RuntimeError(f"GQL query {idx} failed with status {code}: {json.dumps(res)}")
            results.append({"query": idx, "status": code, "rowCount": len(rows)})
        item["gqlVerification"] = results

    print(json.dumps(item, indent=2))


if __name__ == "__main__":
    main()
