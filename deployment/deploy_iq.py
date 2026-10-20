"""Deploy and verify the Microsoft Fabric IQ semantic, ontology, graph, RTI, and agent layers.

Authentication is obtained at runtime from Azure CLI (`az account get-access-token`).
No credentials or secrets are persisted in source control.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import time
import uuid
from pathlib import Path

import requests

from fabric_deploy import Fabric, az_token


ROOT = Path(__file__).resolve().parents[1]


def infer_ontology_type(values: list[str]) -> str:
    nonempty = [v for v in values if v != ""]
    if not nonempty:
        return "String"
    if all(v.lower() in {"true", "false"} for v in nonempty):
        return "Boolean"
    try:
        [int(v) for v in nonempty]
        return "BigInt"
    except ValueError:
        pass
    try:
        [float(v) for v in nonempty]
        return "Double"
    except ValueError:
        pass
    if all(len(v) >= 10 and v[4:5] == "-" and v[7:8] == "-" for v in nonempty):
        return "DateTime"
    return "String"


def b64_part(path: str, obj: dict) -> dict:
    raw = json.dumps(obj, indent=2).encode("utf-8")
    return {
        "path": path,
        "payload": base64.b64encode(raw).decode("ascii"),
        "payloadType": "InlineBase64",
    }


def deploy_and_verify_semantic_model(fabric: Fabric, workspace_id: str, model_name: str) -> dict:
    item = fabric.create_or_reuse(
        model_name,
        "SemanticModel",
        "Direct Lake semantic model for Commercial Insurance IQ.",
    )
    sm_id = item["id"]
    tmdl_root = ROOT / "semantic" / "tmdl"
    parts = []
    for path in sorted(tmdl_root.rglob("*")):
        if path.is_file():
            parts.append(
                {
                    "path": path.relative_to(tmdl_root).as_posix(),
                    "payload": base64.b64encode(path.read_bytes()).decode("ascii"),
                    "payloadType": "InlineBase64",
                }
            )
    resp = fabric.request(
        "POST",
        f"/workspaces/{workspace_id}/semanticModels/{sm_id}/updateDefinition",
        data=json.dumps({"definition": {"parts": parts}}),
    )
    fabric.wait_lro(resp)

    pbi_token = az_token("https://analysis.windows.net/powerbi/api")
    pbi_headers = {"Authorization": f"Bearer {pbi_token}", "Content-Type": "application/json"}
    requests.post(
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{sm_id}/refreshes",
        headers=pbi_headers,
        data=json.dumps({"type": "Full"}),
        timeout=120,
    )
    refresh_status = "Unknown"
    for _ in range(30):
        time.sleep(5)
        hist = requests.get(
            f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{sm_id}/refreshes?$top=1",
            headers=pbi_headers,
            timeout=60,
        ).json()
        latest = hist.get("value", [{}])[0]
        refresh_status = latest.get("status", "Unknown")
        if refresh_status in {"Completed", "Failed", "Disabled"}:
            break
    if refresh_status != "Completed":
        raise RuntimeError(f"SemanticModel refresh ended with status {refresh_status}")

    dax_query = """
    EVALUATE
    CALCULATETABLE(
        ROW(
            "AccountCount", [Account Count],
            "TIV", [Total Insured Value],
            "CAT_AAL", [Modeled CAT Loss],
            "Incurred", [Incurred Loss],
            "Paid", [Paid Loss],
            "Outstanding", [Outstanding Loss],
            "WrittenPremium", [Written Premium],
            "EarnedPremium", [Earned Premium],
            "LossRatio", [Loss Ratio],
            "ClaimCount", [Claim Count],
            "CriticalRecs", [Critical Recommendations],
            "OpenRecs", [Open Recommendations],
            "CompletionRate", [Engineering Completion Rate],
            "HighSignals", [High Materiality Signals],
            "Pulse", [Average Risk Pulse],
            "TIV_YoY", [TIV YoY],
            "CAT_Change", [CAT Exposure Change]
        ),
        Accounts[AccountId] = "A001"
    )
    """
    dax_resp = requests.post(
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{sm_id}/executeQueries",
        headers=pbi_headers,
        data=json.dumps({"queries": [{"query": dax_query}], "serializerSettings": {"includeNulls": True}}),
        timeout=120,
    )
    if dax_resp.status_code >= 400:
        raise RuntimeError(f"DAX verification failed: {dax_resp.status_code} {dax_resp.text}")
    row = dax_resp.json()["results"][0]["tables"][0]["rows"][0]
    return {"id": sm_id, "refreshStatus": refresh_status, "heroMetrics": row}


def verify_eventhouse_kql(fabric: Fabric, workspace_id: str, kql_db_id: str) -> dict:
    details = fabric.request("GET", f"/workspaces/{workspace_id}/kqlDatabases/{kql_db_id}").json()
    query_uri = details["properties"]["queryServiceUri"].rstrip("/")
    db_name = details["displayName"]
    kusto_token = az_token("https://api.kusto.windows.net")
    kusto_headers = {"Authorization": f"Bearer {kusto_token}", "Content-Type": "application/json"}
    csl = (
        'DedupedEvents() | where RunId == "deployed-001" '
        "| sort by AccountId asc, EventTime asc, Sequence asc | serialize "
        "| extend PreviousAccount = prev(AccountId), PreviousPulse = prev(Pulse) "
        "| where AccountId == PreviousAccount and PreviousPulse < 80.0 and Pulse >= 80.0 "
        "| project AccountId, PreviousPulse, Pulse"
    )
    resp = requests.post(
        f"{query_uri}/v2/rest/query",
        headers=kusto_headers,
        data=json.dumps({"db": db_name, "csl": csl}),
        timeout=120,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"KQL query failed: {resp.status_code} {resp.text}")
    frames = resp.json()
    primary = next(f for f in frames if f.get("TableKind") == "PrimaryResult")
    rows = primary.get("Rows", [])
    return {
        "database": db_name,
        "queryServiceUri": query_uri,
        "crossingRows": len(rows),
        "accountId": rows[0][0] if rows else None,
        "previousPulse": rows[0][1] if rows else None,
        "currentPulse": rows[0][2] if rows else None,
    }


def deploy_ontology(
    fabric: Fabric,
    workspace_id: str,
    gold_id: str,
    kql_db_id: str,
    cluster_uri: str,
    ontology_name: str,
) -> dict:
    item = fabric.create_or_reuse(
        ontology_name,
        "Ontology",
        "Commercial Insurance domain ontology for Asterion Global Commercial.",
    )
    ont_id = item["id"]
    manifest = json.loads((ROOT / "graph" / "mapping-manifest.json").read_text(encoding="utf-8"))

    parts = [
        b64_part(".platform", {"metadata": {"type": "Ontology", "displayName": ontology_name}}),
        b64_part("definition.json", {}),
    ]

    entity_ids: dict[str, str] = {}
    entity_pk_prop: dict[str, tuple[str, str]] = {}

    for idx, node in enumerate(manifest["nodes"], start=1):
        label = node["label"]
        table = node["table"].lower()
        pk_col = node["key"]
        eid = str(1000000000000 + idx)
        entity_ids[label] = eid

        csv_path = ROOT / "graph" / f"{node['table']}.csv"
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        cols = list(rows[0].keys())

        props = []
        prop_bindings = []
        display_prop_id = None
        pk_prop_id = None
        for c_idx, col in enumerate(cols, start=1):
            pid = str(2000000000000 + idx * 100 + c_idx)
            vtype = infer_ontology_type([r[col] for r in rows])
            props.append(
                {
                    "id": pid,
                    "name": col,
                    "redefines": None,
                    "baseTypeNamespaceType": None,
                    "valueType": vtype,
                }
            )
            prop_bindings.append({"sourceColumnName": col, "targetPropertyId": pid})
            if col == pk_col:
                pk_prop_id = pid
            if (col.endswith("Name") or col == "Title") and display_prop_id is None and vtype == "String":
                display_prop_id = pid
        if display_prop_id is None:
            display_prop_id = pk_prop_id
        assert pk_prop_id is not None
        entity_pk_prop[label] = (pk_col, pk_prop_id)

        ts_props = []
        if label == "Account":
            for t_idx, (t_name, t_type) in enumerate(
                [
                    ("EventTime", "DateTime"),
                    ("Pulse", "Double"),
                    ("EventType", "String"),
                    ("RunId", "String"),
                    ("EvidenceRef", "String"),
                ],
                start=1,
            ):
                ts_props.append(
                    {
                        "id": str(2900000000000 + t_idx),
                        "name": t_name,
                        "redefines": None,
                        "baseTypeNamespaceType": None,
                        "valueType": t_type,
                    }
                )

        parts.append(
            b64_part(
                f"EntityTypes/{eid}/definition.json",
                {
                    "id": eid,
                    "namespace": "usertypes",
                    "baseEntityTypeId": None,
                    "name": label,
                    "entityIdParts": [pk_prop_id],
                    "displayNamePropertyId": display_prop_id,
                    "namespaceType": "Custom",
                    "visibility": "Visible",
                    "properties": props,
                    "timeseriesProperties": ts_props,
                },
            )
        )

        bind_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ci.ontology.entity.{label}"))
        parts.append(
            b64_part(
                f"EntityTypes/{eid}/DataBindings/{bind_id}.json",
                {
                    "id": bind_id,
                    "dataBindingConfiguration": {
                        "dataBindingType": "NonTimeSeries",
                        "propertyBindings": prop_bindings,
                        "sourceTableProperties": {
                            "sourceType": "LakehouseTable",
                            "workspaceId": workspace_id,
                            "itemId": gold_id,
                            "sourceTableName": table,
                        },
                    },
                },
            )
        )

        if label == "Account":
            ts_bind_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "ci.ontology.entity.Account.timeseries"))
            ts_bindings = [{"sourceColumnName": "AccountId", "targetPropertyId": pk_prop_id}] + [
                {"sourceColumnName": tp["name"], "targetPropertyId": tp["id"]} for tp in ts_props
            ]
            parts.append(
                b64_part(
                    f"EntityTypes/{eid}/DataBindings/{ts_bind_id}.json",
                    {
                        "id": ts_bind_id,
                        "dataBindingConfiguration": {
                            "dataBindingType": "TimeSeries",
                            "timestampColumnName": "EventTime",
                            "propertyBindings": ts_bindings,
                            "sourceTableProperties": {
                                "sourceType": "KustoTable",
                                "workspaceId": workspace_id,
                                "itemId": kql_db_id,
                                "clusterUri": cluster_uri,
                                "databaseName": "CI_Underwriting_RTI",
                                "sourceTableName": "UnderwritingEvents",
                            },
                        },
                    },
                )
            )

    seen_rel_names: set[str] = set()
    for r_idx, edge in enumerate(manifest["edges"], start=1):
        rel_label = edge["label"]
        src_label = edge["sourceLabel"]
        tgt_label = edge["targetLabel"]
        rel_name = rel_label if rel_label not in seen_rel_names else f"{src_label}_{rel_label}"
        seen_rel_names.add(rel_name)
        rid = str(3000000000000 + r_idx)
        parts.append(
            b64_part(
                f"RelationshipTypes/{rid}/definition.json",
                {
                    "namespace": "usertypes",
                    "id": rid,
                    "name": rel_name,
                    "namespaceType": "Custom",
                    "source": {"entityTypeId": entity_ids[src_label]},
                    "target": {"entityTypeId": entity_ids[tgt_label]},
                },
            )
        )
        ctx_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ci.ontology.edge.{src_label}.{rel_label}.{tgt_label}"))
        parts.append(
            b64_part(
                f"RelationshipTypes/{rid}/Contextualizations/{ctx_id}.json",
                {
                    "id": ctx_id,
                    "dataBindingTable": {
                        "workspaceId": workspace_id,
                        "itemId": gold_id,
                        "sourceTableName": edge["table"].lower(),
                        "sourceType": "LakehouseTable",
                    },
                    "sourceKeyRefBindings": [
                        {
                            "sourceColumnName": edge["sourceColumn"],
                            "targetPropertyId": entity_pk_prop[src_label][1],
                        }
                    ],
                    "targetKeyRefBindings": [
                        {
                            "sourceColumnName": edge["targetColumn"],
                            "targetPropertyId": entity_pk_prop[tgt_label][1],
                        }
                    ],
                },
            )
        )

    resp = fabric.request(
        "POST",
        f"/workspaces/{workspace_id}/ontologies/{ont_id}/updateDefinition",
        data=json.dumps({"definition": {"parts": parts}}),
    )
    fabric.wait_lro(resp)

    comp_prefix = f"{ontology_name}_graph_{ont_id.replace('-', '')}"
    comp_matches = [
        x
        for x in fabric.items()
        if x["type"] == "GraphModel" and x["displayName"].startswith(f"{ontology_name}_graph_")
    ]
    companion_graph_id = None
    if comp_matches:
        companion_graph_id = comp_matches[0]["id"]
        gr = fabric.request(
            "POST",
            f"/workspaces/{workspace_id}/graphModels/{companion_graph_id}/getDefinition?format=json",
        )
        if gr.status_code == 202:
            fabric.wait_lro(gr)
            gres = fabric.request("GET", gr.headers["Location"].rstrip("/") + "/result").json()
        else:
            gres = gr.json()
        new_parts = []
        needs_patch = False
        for p in gres.get("definition", {}).get("parts", []):
            if p["path"] == ".platform":
                continue
            txt = base64.b64decode(p["payload"]).decode("utf-8")
            if p["path"] == "dataSources.json" and "/Tables/dbo/" in txt:
                needs_patch = True
                txt = txt.replace("/Tables/dbo/", "/Tables/")
            new_parts.append(
                {
                    "path": p["path"],
                    "payload": base64.b64encode(txt.encode("utf-8")).decode("ascii"),
                    "payloadType": "InlineBase64",
                }
            )
        if needs_patch:
            ur = fabric.request(
                "POST",
                f"/workspaces/{workspace_id}/graphModels/{companion_graph_id}/updateDefinition",
                data=json.dumps({"definition": {"format": "json", "parts": new_parts}}),
            )
            fabric.wait_lro(ur)

    return {
        "id": ont_id,
        "companionGraphId": companion_graph_id,
        "companionGraphPrefix": comp_prefix,
        "entityTypes": len(manifest["nodes"]),
        "relationshipTypes": len(manifest["edges"]),
    }


def deploy_agents(
    fabric: Fabric,
    workspace_id: str,
    sm_id: str,
    gold_id: str,
    kql_db_id: str,
) -> dict:
    da = fabric.create_or_reuse(
        "CommercialInsuranceDataAgent",
        "DataAgent",
        "Governed commercial insurance underwriting Data Agent grounded in CommercialInsuranceIQModel.",
    )
    da_id = da["id"]

    ai_instructions = (
        "Use CommercialInsuranceIQModel and CI_Gold_Dev for commercial insurance underwriting questions.\n"
        "Use AccountId (for example A001 for Meridian Specialty Chemicals) as the mastered account identity.\n"
        "Keep monetary source values in integer cents (*USDCents) and convert to USD by dividing by 100 or referencing saved semantic measures.\n"
        "Default snapshot date is 2026-09-14 and prior comparison snapshot date is 2025-09-14 unless another date is explicitly requested.\n"
        "For A001 KPIs, reference saved measures [Total Insured Value], [Modeled CAT Loss], [Incurred Loss], [Paid Loss], [Outstanding Loss], [Written Premium], [Earned Premium], [Loss Ratio], [Critical Recommendations], [Open Recommendations], [Engineering Completion Rate], [High Materiality Signals], [Average Risk Pulse], [TIV YoY], and [CAT Exposure Change].\n"
        "Always include evidence IDs (AccountId, LocationId, PolicyId, ClaimId, RecommendationId, LocalPolicyId, RequirementId, SignalId) and state that results support human underwriting review rather than automated pricing, binding, or declination."
    )
    sm_tables = [
        "Accounts",
        "Calendar",
        "Brokers",
        "Underwriters",
        "Industries",
        "Countries",
        "Perils",
        "Policies",
        "PolicyValuations",
        "Coverages",
        "Locations",
        "Exposures",
        "CATRisk",
        "Claims",
        "ClaimValuations",
        "EngineeringInspections",
        "EngineeringRecommendations",
        "Renewals",
        "RenewalSignals",
        "PricingScenarios",
        "UnderwritingDecisions",
        "MultinationalPrograms",
        "LocalPolicies",
        "ProgramRequirements",
        "Submissions",
        "UnderwritingFeatures",
        "RiskPulse",
    ]
    sm_ds = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
        "artifactId": sm_id,
        "workspaceId": workspace_id,
        "dataSourceInstructions": "Primary governed Direct Lake semantic model for Asterion Global Commercial underwriting KPIs and account A001 renewal review.",
        "displayName": "CommercialInsuranceIQModel",
        "type": "semantic_model",
        "userDescription": "Direct Lake semantic model with 27 underwriting tables, 25 relationships, and 30 saved DAX measures.",
        "metadata": {},
        "elements": [
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ci.sm.table.{t}")),
                "is_selected": True,
                "display_name": t,
                "type": "semantic_model.table",
                "description": f"Curated {t} table in CommercialInsuranceIQModel",
                "children": [],
            }
            for t in sm_tables
        ],
    }
    lh_ds = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataSource/1.0.0/schema.json",
        "artifactId": gold_id,
        "workspaceId": workspace_id,
        "dataSourceInstructions": "Use demo_* tables in CI_Gold_Dev for row-level evidence keys (RecommendationId, LocalPolicyId, RequirementId, SignalId, ClaimId, LocationId). Divide *USDCents columns by 100.0 for USD.",
        "displayName": "CI_Gold_Dev",
        "type": "lakehouse_tables",
        "userDescription": "Gold Lakehouse containing curated demo_* tables and graph node_*/edge_* tables.",
        "metadata": {},
        "elements": [
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "ci.lh.schema.dbo")),
                "is_selected": True,
                "display_name": "dbo",
                "type": "lakehouse_tables.schema",
                "children": [
                    {
                        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ci.lh.table.demo_{t.lower()}")),
                        "is_selected": True,
                        "display_name": f"demo_{t.lower()}",
                        "type": "lakehouse_tables.table",
                        "description": f"Gold Delta table demo_{t.lower()}",
                        "children": [],
                    }
                    for t in sm_tables
                ],
            }
        ],
    }
    lh_fewshots = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/fewShots/1.0.0/schema.json",
        "fewShots": [
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "ci.fewshot.1")),
                "question": "What changed for account A001 before renewal?",
                "query": "SELECT AccountId, TIVUSDCents / 100.0 AS TIV_USD, PriorTIVUSDCents / 100.0 AS Prior_TIV_USD, AALUSDCents / 100.0 AS CAT_AAL_USD, PriorAALUSDCents / 100.0 AS Prior_CAT_AAL_USD, IncurredUSDCents / 100.0 AS Incurred_USD, PriorIncurredUSDCents / 100.0 AS Prior_Incurred_USD, TIVGrowth, CATGrowth, ClaimsGrowth, DaysToRenewal, OpenCritical FROM demo_underwritingfeatures WHERE AccountId = 'A001'",
            },
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "ci.fewshot.2")),
                "question": "What is A001's current TIV, CAT AAL, and incurred loss?",
                "query": "SELECT f.AccountId, f.TIVUSDCents / 100.0 AS Current_TIV_USD, f.AALUSDCents / 100.0 AS Current_CAT_AAL_USD, f.IncurredUSDCents / 100.0 AS Current_Incurred_USD, p.Pulse AS Baseline_Pulse FROM demo_underwritingfeatures f JOIN demo_riskpulse p ON f.AccountId = p.AccountId WHERE f.AccountId = 'A001'",
            },
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "ci.fewshot.3")),
                "question": "Which critical engineering recommendations remain open for A001?",
                "query": "SELECT RecommendationId, LocationId, Title, MaterialityWeight, Status, IsCritical, DueDate, ClosureEvidence FROM demo_engineeringrecommendations WHERE AccountId = 'A001' AND Status = 'Open' AND IsCritical = true ORDER BY RecommendationId",
            },
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "ci.fewshot.4")),
                "question": "Which local-program requirements are not aligned for A001?",
                "query": "SELECT r.RequirementId, r.ProgramId, r.CountryId, r.LocalPolicyId, r.RequiredBIMonths, lp.BIIndemnityMonths, lp.CoverageStatus, r.Status FROM demo_programrequirements r JOIN demo_localpolicies lp ON r.LocalPolicyId = lp.LocalPolicyId WHERE r.ProgramId = 'MP001' AND r.Status <> 'Aligned' ORDER BY r.RequirementId",
            },
        ],
    }
    da_parts = [
        b64_part(
            "Files/Config/data_agent.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/dataAgent/2.1.0/schema.json"
            },
        ),
        b64_part(
            "Files/Config/draft/stage_config.json",
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/dataAgent/definition/stageConfiguration/1.0.0/schema.json",
                "aiInstructions": ai_instructions,
            },
        ),
        b64_part("Files/Config/draft/semantic_model-CommercialInsuranceIQModel/datasource.json", sm_ds),
        b64_part("Files/Config/draft/lakehouse-tables-CI_Gold_Dev/datasource.json", lh_ds),
        b64_part("Files/Config/draft/lakehouse-tables-CI_Gold_Dev/fewshots.json", lh_fewshots),
    ]
    da_resp = fabric.request(
        "POST",
        f"/workspaces/{workspace_id}/dataAgents/{da_id}/updateDefinition",
        data=json.dumps({"definition": {"parts": da_parts}}),
    )
    fabric.wait_lro(da_resp)
    fabric.request(
        "POST",
        f"/workspaces/{workspace_id}/dataAgents/{da_id}/staging/publish",
        data=json.dumps(
            {
                "publishedDescription": "Governed Commercial Insurance Data Agent grounded in CommercialInsuranceIQModel and CI_Gold_Dev."
            }
        ),
    )

    oa = fabric.create_or_reuse(
        "RenewalRiskOperationsAgent",
        "OperationsAgent",
        "Governed renewal-risk threshold monitor (stopped by default until human approval).",
    )
    oa_id = oa["id"]

    oa_config = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/operationsAgents/definition/1.0.0/schema.json",
        "configuration": {
            "instructions": (
                "Monitor LatestPulse() in CI_Underwriting_RTI using EvaluationKey (AccountId:RunId:Sequence) as the stable evaluation identity. "
                "Evaluate fresh deduplicated underwriting events where Pulse >= 80.0 and DaysToRenewal <= 45. "
                "Surface account A001 threshold crossings (77.0 to 83.0) with EvidenceRef and component scores (CAT, Claims, Growth, Engineering, Concentration, Missing, Proximity) for human underwriter review. "
                "Do not autonomously bind, price, decline, or issue external notifications without human approval."
            ),
            "dataSources": {
                "underwritingRti": {
                    "id": kql_db_id,
                    "type": "KustoDatabase",
                    "workspaceId": workspace_id,
                }
            },
            "actions": {},
        },
        "shouldRun": False,
    }
    resp = fabric.request(
        "POST",
        f"/workspaces/{workspace_id}/operationsAgents/{oa_id}/updateDefinition",
        data=json.dumps({"definition": {"parts": [b64_part("Configurations.json", oa_config)]}}),
    )
    fabric.wait_lro(resp)

    return {
        "dataAgentId": da_id,
        "dataAgentPublished": True,
        "dataAgentFewShots": 4,
        "operationsAgentId": oa_id,
        "operationsAgentShouldRun": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--gold-id", required=True)
    parser.add_argument("--kql-db-id", required=True)
    args = parser.parse_args()

    fabric = Fabric(args.workspace_id)
    sm = deploy_and_verify_semantic_model(fabric, args.workspace_id, "CommercialInsuranceIQModel")
    kql = verify_eventhouse_kql(fabric, args.workspace_id, args.kql_db_id)
    ont = deploy_ontology(
        fabric,
        args.workspace_id,
        args.gold_id,
        args.kql_db_id,
        kql["queryServiceUri"],
        "CommercialInsuranceOntology",
    )
    agents = deploy_agents(fabric, args.workspace_id, sm["id"], args.gold_id, args.kql_db_id)
    print(
        json.dumps(
            {
                "semanticModel": sm,
                "eventhouse": kql,
                "ontology": ont,
                "agents": agents,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
