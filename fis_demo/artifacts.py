"""Build the FIS finance notebook, Direct Lake, report, graph and ontology artifacts."""

from __future__ import annotations

import argparse
import ast
import json
import uuid
from pathlib import Path

from fis_demo.data import AS_OF, FACTS, KEYS, RELATIONSHIPS, ROOT, build_data, column_type, write_data


SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item"
MONEY = r"\$#,##0.00;(\$#,##0.00)"
YTD = "KEEPFILTERS('DIM_DATE'[YEAR] = 2026), KEEPFILTERS('DIM_DATE'[DATE] <= DATE(2026,9,30))"
MEASURES: dict[str, tuple[str, str]] = {}
for fact, prefix in (("ACTUALS", "Actual"), ("PLAN", "Plan"), ("FORECAST", "Forecast")):
    for label, category in (("Revenue", "Revenue"), ("Opex", "Operating Expense")):
        MEASURES[f"{prefix} {label}"] = (
            f'CALCULATE(DIVIDE(SUM(\'{fact}\'[AmountCents]),100), \'account\'[AccountType] = "{category}")',
            MONEY,
        )
        MEASURES[f"{prefix} {label} YTD"] = (f"CALCULATE([{prefix} {label}], {YTD})", MONEY)
    MEASURES[f"{prefix} Operating Profit"] = (f"[{prefix} Revenue] - [{prefix} Opex]", MONEY)
    MEASURES[f"{prefix} Operating Profit YTD"] = (f"[{prefix} Revenue YTD] - [{prefix} Opex YTD]", MONEY)
    MEASURES[f"{prefix} Operating Margin YTD"] = (
        f"DIVIDE([{prefix} Operating Profit YTD],[{prefix} Revenue YTD])", "0.0%"
    )
MEASURES.update({
    "Revenue Variance YTD": ("[Actual Revenue YTD] - [Plan Revenue YTD]", MONEY),
    "Revenue Variance Pct YTD": ("DIVIDE([Revenue Variance YTD],[Plan Revenue YTD])", "0.0%"),
    "Favorable Expense Variance YTD": ("[Plan Opex YTD] - [Actual Opex YTD]", MONEY),
    "Favorable Expense Variance Pct YTD": ("DIVIDE([Favorable Expense Variance YTD],[Plan Opex YTD])", "0.0%"),
    "Operating Profit Variance YTD": ("[Actual Operating Profit YTD] - [Plan Operating Profit YTD]", MONEY),
    "Forecast Revenue FY": ("CALCULATE([Forecast Revenue], KEEPFILTERS('DIM_DATE'[YEAR] = 2026))", MONEY),
    "Plan Revenue FY": ("CALCULATE([Plan Revenue], KEEPFILTERS('DIM_DATE'[YEAR] = 2026))", MONEY),
    "Forecast Operating Profit FY": (
        "CALCULATE([Forecast Operating Profit], KEEPFILTERS('DIM_DATE'[YEAR] = 2026))", MONEY
    ),
    "Plan Operating Profit FY": (
        "CALCULATE([Plan Operating Profit], KEEPFILTERS('DIM_DATE'[YEAR] = 2026))", MONEY
    ),
    "Forecast Operating Profit Variance FY": ("[Forecast Operating Profit FY] - [Plan Operating Profit FY]", MONEY),
    "Prior Year Revenue YTD": (
        "CALCULATE([Actual Revenue], REMOVEFILTERS('DIM_DATE'), "
        "'DIM_DATE'[YEAR] = 2025, 'DIM_DATE'[DATE] <= DATE(2025,9,30))", MONEY
    ),
    "Revenue Growth YoY": ("DIVIDE([Actual Revenue YTD] - [Prior Year Revenue YTD],[Prior Year Revenue YTD])", "0.0%"),
    "As Of Date": ("DATE(2026,9,30)", "yyyy-mm-dd"),
    "Review Threshold USD": ("100000", MONEY),
})

FEW_SHOTS = [
    {
        "question": "Which cost centers and products have an unfavorable cloud expense variance YTD?",
        "query": """SELECT a.COSTCENTER, c.Description AS CostCenterName, a.PRODUCTLINE,
SUM(a.AmountCents) / 100.0 AS ActualUSD, SUM(p.AmountCents) / 100.0 AS PlanUSD,
(SUM(p.AmountCents) - SUM(a.AmountCents)) / 100.0 AS FavorableVarianceUSD
FROM actuals a JOIN plan p ON a.ACCOUNT=p.ACCOUNT AND a.COSTCENTER=p.COSTCENTER
AND a.PRODUCTLINE=p.PRODUCTLINE AND a.DATE=p.DATE
JOIN cost_center c ON a.COSTCENTER=c.CostCenter
WHERE a.ACCOUNT='500100' AND a.YEAR=2026 AND a.PERIOD<=9
GROUP BY a.COSTCENTER, c.Description, a.PRODUCTLINE
HAVING SUM(a.AmountCents)>SUM(p.AmountCents)
ORDER BY FavorableVarianceUSD""",
    },
    {
        "question": "Show the monthly evidence for Digital Banking cloud overspend.",
        "query": """SELECT a.RecordID AS ActualRecordID, p.RecordID AS PlanRecordID, a.DATE,
a.Amount AS ActualUSD, p.Amount AS PlanUSD, p.Amount-a.Amount AS FavorableVarianceUSD
FROM actuals a JOIN plan p ON a.ACCOUNT=p.ACCOUNT AND a.COSTCENTER=p.COSTCENTER
AND a.PRODUCTLINE=p.PRODUCTLINE AND a.DATE=p.DATE
WHERE a.ACCOUNT='500100' AND a.COSTCENTER='300110' AND a.PRODUCTLINE='DIGITAL'
AND a.YEAR=2026 AND a.PERIOD<=9 ORDER BY a.DATE""",
    },
    {
        "question": "Compare full-year revenue forecast and plan by product.",
        "query": """WITH f AS (
SELECT PRODUCTLINE, SUM(AmountCents)/100.0 AS ForecastUSD FROM forecast
WHERE YEAR=2026 AND ACCOUNT IN ('400100','400200','400300') GROUP BY PRODUCTLINE
), p AS (
SELECT PRODUCTLINE, SUM(AmountCents)/100.0 AS PlanUSD FROM plan
WHERE YEAR=2026 AND ACCOUNT IN ('400100','400200','400300') GROUP BY PRODUCTLINE
)
SELECT f.PRODUCTLINE, f.ForecastUSD, p.PlanUSD, f.ForecastUSD-p.PlanUSD AS VarianceUSD
FROM f JOIN p ON f.PRODUCTLINE=p.PRODUCTLINE ORDER BY f.PRODUCTLINE""",
    },
    {
        "question": "What is the actual revenue versus plan by month in 2026 through September?",
        "query": """WITH a AS (
SELECT PERIOD, SUM(AmountCents)/100.0 AS ActualUSD FROM actuals
WHERE YEAR=2026 AND PERIOD<=9 AND ACCOUNT IN ('400100','400200','400300') GROUP BY PERIOD
), p AS (
SELECT PERIOD, SUM(AmountCents)/100.0 AS PlanUSD FROM plan
WHERE YEAR=2026 AND PERIOD<=9 AND ACCOUNT IN ('400100','400200','400300') GROUP BY PERIOD
)
SELECT a.PERIOD, a.ActualUSD, p.PlanUSD, a.ActualUSD-p.PlanUSD AS VarianceUSD
FROM a JOIN p ON a.PERIOD=p.PERIOD ORDER BY a.PERIOD""",
    },
]

GQL_QUERIES = [
    """MATCH (f:`ACTUALS`)-[:`ACTUALS_account`]->(a:`account`),
      (f)-[:`ACTUALS_cost_center`]->(c:`cost_center`),
      (f)-[:`ACTUALS_product`]->(p:`product`),
      (f)-[:`ACTUALS_DIM_DATE`]->(d:`DIM_DATE`)
FILTER a.`Account` = '500100' AND c.`CostCenter` = '300110'
  AND p.`ProductLine` = 'DIGITAL' AND d.`YEAR` = 2026
RETURN f.`RecordID` AS `EvidenceId`, d.`DATE` AS `Period`, f.`AmountCents` AS `ActualCents`
ORDER BY `Period`""",
    """MATCH (f:`FORECAST`)-[:`FORECAST_account`]->(a:`account`),
      (f)-[:`FORECAST_product`]->(p:`product`)
FILTER a.`AccountType` = 'Revenue'
LET productId = p.`ProductLine`
RETURN productId AS `Product`, SUM(f.`AmountCents`) AS `ForecastRevenueCents`
GROUP BY productId ORDER BY `Product`""",
    """MATCH (f:`PLAN`)-[:`PLAN_account`]->(a:`account`),
      (f)-[:`PLAN_cost_center`]->(c:`cost_center`),
      (f)-[:`PLAN_product`]->(p:`product`),
      (f)-[:`PLAN_DIM_DATE`]->(d:`DIM_DATE`)
FILTER a.`Account` = '500100' AND c.`CostCenter` = '300110' AND p.`ProductLine` = 'DIGITAL'
RETURN d.`DATE` AS `Period`, f.`AmountCents` AS `PlanCents` ORDER BY `Period`""",
]


def cell(kind: str, source: str, identifier: str) -> dict:
    result = {"cell_type": kind, "id": identifier, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        ast.parse(source, filename=identifier)
        result.update({"outputs": [], "execution_count": None})
    return result


def notebook(workspace: str, bronze: str, silver: str, gold: str) -> dict:
    source = (ROOT / "data.py").read_text(encoding="utf-8")
    parameters = (
        f"WORKSPACE_ID = {workspace!r}\nBRONZE_ID = {bronze!r}\n"
        f"SILVER_ID = {silver!r}\nGOLD_ID = {gold!r}\n"
    )
    bootstrap = f"""import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, LongType, DecimalType

namespace = {{"__name__": "fis_finance_data", "__file__": "/lakehouse/default/Files/fis_finance_iq/data.py"}}
exec(compile({source!r}, namespace["__file__"], "exec"), namespace)
data = namespace["build_data"]()
expected = namespace["validate"](data)
base = f"abfss://{{WORKSPACE_ID}}@onelake.dfs.fabric.microsoft.com"
roots = {{"bronze": f"{{base}}/{{BRONZE_ID}}", "silver": f"{{base}}/{{SILVER_ID}}", "gold": f"{{base}}/{{GOLD_ID}}"}}
notebookutils.fs.mkdirs(roots["gold"] + "/Files/fis_finance_iq")
print(json.dumps(expected, indent=2))
"""
    bronze_code = """for name, rows in data.items():
    fields = []
    typed_rows = [dict(row) for row in rows]
    for column, value in rows[0].items():
        kind = namespace["column_type"](column, value)
        datatype = LongType() if kind == "int64" else DecimalType(18,2) if kind == "decimal" else StringType()
        fields.append(StructField(column, datatype, False))
        if kind == "decimal":
            for row in typed_rows:
                row[column] = Decimal(str(row[column]))
    frame = spark.createDataFrame(typed_rows, StructType(fields))
    frame.write.format("delta").mode("overwrite").option("overwriteSchema","true").save(roots["bronze"] + "/Tables/" + name.lower())
    print("BRONZE", name, frame.count())
"""
    silver_code = """for name, rows in data.items():
    frame = spark.read.format("delta").load(roots["bronze"] + "/Tables/" + name.lower())
    for column, value in rows[0].items():
        kind = namespace["column_type"](column, value)
        if kind == "date":
            frame = frame.withColumn(column, F.to_date(column))
        elif kind == "timestamp":
            frame = frame.withColumn(column, F.to_timestamp(column))
        elif kind == "string":
            frame = frame.withColumn(column, F.trim(F.col(column)))
    null_counts = frame.select([
        F.sum(F.col(column).isNull().cast("int")).alias(column) for column in frame.columns
    ]).first().asDict()
    invalid = [column for column, count in null_counts.items() if count]
    if invalid:
        raise ValueError(f"Invalid or missing values in {name}: {invalid}")
    key = namespace["KEYS"][name]
    if frame.select(key).distinct().count() != len(rows):
        raise ValueError(f"Duplicate key in {name}")
    frame.write.format("delta").mode("overwrite").option("overwriteSchema","true").save(roots["silver"] + "/Tables/" + name.lower())
    print("SILVER", name, frame.count())
"""
    gold_code = """spark.conf.set("spark.sql.parquet.vorder.default", "true")
for name in data:
    frame = spark.read.format("delta").load(roots["silver"] + "/Tables/" + name.lower())
    frame.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable(name.lower())
    print("GOLD", name, spark.table(name.lower()).count())

edge_counts = {}
for relation in namespace["RELATIONSHIPS"]:
    fact, dimension = relation["fromTable"], relation["toTable"]
    edge_name = f"edge_{fact}_{dimension}".lower()
    frame = spark.table(fact.lower()).select(
        F.concat(F.col("RecordID"), F.lit(":" + dimension)).alias("EdgeId"),
        F.col("RecordID").alias("SourceId"), F.col(relation["fromColumn"]).alias("TargetId")
    )
    if dimension == "DIM_DATE":
        frame = frame.withColumn("TargetDateInteger", F.date_format("TargetId", "yyyyMMdd").cast("long"))
    frame.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable(edge_name)
    edge_counts[edge_name] = frame.count()

grain = ["ACCOUNT", "COSTCENTER", "PRODUCTLINE"]
actual = (spark.table("actuals").where((F.col("YEAR")==2026) & (F.col("PERIOD")<=9))
          .groupBy(*grain).agg(F.sum("Amount").alias("ActualAmount")))
plan = (spark.table("plan").where((F.col("YEAR")==2026) & (F.col("PERIOD")<=9))
        .groupBy(*grain).agg(F.sum("Amount").alias("PlanAmount")))
account_types = spark.table("account").select(F.col("Account").alias("ACCOUNT"), "AccountType", "FavorableSign")
drivers = (actual.join(plan, grain).join(account_types, "ACCOUNT")
    .withColumn("FavorableVariance", (F.col("ActualAmount")-F.col("PlanAmount"))*F.col("FavorableSign"))
    .withColumn("VariancePct", F.col("FavorableVariance")/F.col("PlanAmount"))
    .withColumn("ReviewRequired", (F.col("FavorableVariance")<=-100000) & (F.col("VariancePct")<=-0.10)))
drivers.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable("variance_drivers")
print("Review flags support human review; no automated notifications or accounting actions.")
"""
    verification = f"""def scalar(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value

persisted = {{
    name: [{{key: scalar(value) for key, value in row.asDict().items()}} for row in spark.table(name.lower()).collect()]
    for name in data
}}
report = namespace["validate"](persisted)
if report["metrics"] != expected["metrics"] or report["tableRows"] != expected["tableRows"]:
    raise ValueError("Persisted Gold Delta tables differ from deterministic reference values")
report["edgeRows"] = edge_counts
report["reviewFlags"] = spark.table("variance_drivers").where("ReviewRequired").count()
fewshot_checks = []
for example in {FEW_SHOTS!r}:
    result = spark.sql(example["query"])
    fewshot_checks.append({{"question": example["question"], "rows": result.count()}})
if [check["rows"] for check in fewshot_checks] != [36, 9, 6, 9]:
    raise ValueError(f"Unexpected few-shot results: {{fewshot_checks}}")
report["fewShots"] = fewshot_checks
notebookutils.fs.put(roots["gold"] + "/Files/fis_finance_iq/live-validation.json", json.dumps(report, indent=2), True)
print(json.dumps(report, indent=2))
display(spark.table("variance_drivers").where("ReviewRequired").orderBy("FavorableVariance"))
"""
    cells = [
        cell("markdown", "# FIS Finance IQ - synthetic FP&A demo\n\nAs of 2026-09-30. Not FIS financial results. "
             "This notebook overwrites only the dedicated demo Lakehouses. No schedules, notifications or source-system writes.", "intro"),
        cell("code", parameters, "parameters"),
        cell("code", bootstrap, "bootstrap"),
        cell("markdown", "## Bronze: deterministic source ledger", "bronze-title"),
        cell("code", bronze_code, "bronze"),
        cell("markdown", "## Silver: typed, validated finance data", "silver-title"),
        cell("code", silver_code, "silver"),
        cell("markdown", "## Gold: conformed star schema, variance drivers, relationship edges", "gold-title"),
        cell("code", gold_code, "gold"),
        cell("markdown", "## Acceptance: persisted data, all 12 relationships and four SQL examples", "verify-title"),
        cell("code", verification, "verify"),
    ]
    cells[1]["metadata"]["tags"] = ["parameters"]
    return {
        "nbformat": 4, "nbformat_minor": 5, "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
            "language_info": {"name": "python"},
            "dependencies": {"lakehouse": {
                "default_lakehouse": gold, "default_lakehouse_name": "FIS_Finance_Gold",
                "default_lakehouse_workspace_id": workspace,
            }},
        },
    }


def semantic_files(workspace: str, gold: str) -> dict[str, str]:
    tables = build_data()
    files = {
        "definition.pbism": json.dumps({"version": "4.0", "settings": {}}),
        "definition/database.tmdl": "database\n\tcompatibilityLevel: 1702\n\tcompatibilityMode: powerBI\n",
        "definition/model.tmdl": (
            "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
            "\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n\n"
            + "".join(f"ref table '{name}'\n" for name in tables) + "ref expression DL_FIS_Finance\n"
        ),
        "definition/expressions.tmdl": (
            "expression DL_FIS_Finance =\n\tlet\n"
            f'\t\tSource = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/{workspace}/{gold}", '
            "[HierarchicalNavigation=true])\n\tin\n\t\tSource\n"
        ),
        "definition/relationships.tmdl": "\n".join(
            f"relationship '{r['fromTable']} to {r['toTable']}'\n"
            f"\tfromColumn: '{r['fromTable']}'.{r['fromColumn']}\n"
            f"\ttoColumn: '{r['toTable']}'.{r['toColumn']}\n"
            "\tfromCardinality: many\n\ttoCardinality: one\n\tcrossFilteringBehavior: oneDirection\n"
            for r in RELATIONSHIPS
        ),
    }
    for name, rows in tables.items():
        lines = [f"table '{name}'", ""]
        if name == "ACTUALS":
            for measure, (expression, formatting) in MEASURES.items():
                lines += [
                    f"\tmeasure '{measure}' = {expression}", f"\t\tformatString: {formatting}",
                    "\t\tdisplayFolder: Finance KPIs", "",
                ]
        for column, value in rows[0].items():
            kind = column_type(column, value)
            dtype = "dateTime" if kind in {"date", "timestamp"} else kind
            lines += [f"\tcolumn '{column}'", f"\t\tdataType: {dtype}", "\t\tsummarizeBy: none"]
            if name not in FACTS and column == KEYS[name]:
                lines += ["\t\tisKey"]
            if column == "MONTH_YEAR":
                lines += ["\t\tsortByColumn: MONTH_ID"]
            if kind == "date":
                lines += ["\t\tformatString: yyyy-mm-dd"]
            if kind == "decimal":
                lines += [f"\t\tformatString: {MONEY}"]
            lines += [f"\t\tsourceColumn: {column}", ""]
        lines += [
            f"\tpartition '{name}' = entity", "\t\tmode: directLake", "\t\tsource",
            f"\t\t\tentityName: {name.lower()}", "\t\t\texpressionSource: DL_FIS_Finance", "",
        ]
        files[f"definition/tables/{name}.tmdl"] = "\n".join(lines)
    return files


def ontology_date_keys_notebook(workspace: str, gold: str) -> dict:
    code = """for fact in ("ACTUALS", "FORECAST", "PLAN"):
    table = f"edge_{fact}_dim_date".lower()
    if "TargetDateInteger" not in spark.table(table).columns:
        spark.sql(f"ALTER TABLE {table} ADD COLUMNS (TargetDateInteger BIGINT)")
    spark.sql(f"UPDATE {table} SET TargetDateInteger = CAST(date_format(TargetId, 'yyyyMMdd') AS BIGINT)")
    invalid = spark.sql(f"SELECT COUNT(*) AS n FROM {table} WHERE TargetDateInteger IS NULL OR TargetDateInteger <> CAST(date_format(TargetId, 'yyyyMMdd') AS BIGINT)").first()["n"]
    if invalid:
        raise ValueError(f"Invalid integer ontology date keys in {table}: {invalid}")
    print(table, "validated", spark.table(table).count())
"""
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
            "language_info": {"name": "python"},
            "dependencies": {"lakehouse": {
                "default_lakehouse": gold, "default_lakehouse_name": "FIS_Finance_Gold",
                "default_lakehouse_workspace_id": workspace,
            }},
        },
        "cells": [
            cell("markdown", "# FIS ontology date keys\n\nOntology entity keys require String or BigInt. "
                 "Preserve the original DATE relationships and add an integer yyyyMMdd key only to the date edges.", "intro"),
            cell("code", code, "date-keys"),
        ],
    }


def stable_id(value: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"fis-finance-iq/{value}"))


def ontology_files(workspace: str, gold: str) -> dict[str, str | dict]:
    tables = build_data()
    semantic = semantic_files(workspace, gold)
    files: dict[str, str | dict] = {
        path.removeprefix("definition/"): value
        for path, value in semantic.items()
        if path.startswith("definition/") and path not in {"definition/model.tmdl", "definition/database.tmdl"}
    }
    files[".platform"] = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Ontology", "displayName": "FIS_Finance_Ontology"},
        "config": {"version": "2.0", "logicalId": stable_id("ontology")},
    }
    files["database.tmdl"] = "database\n\tcompatibilityLevel: 1000000\n"
    files["namespaces/default.tmdl"] = "namespace default\n\tlineageTag: default\n"
    files["model.tmdl"] = (
        "model Model\n\nref namespace default\n"
        + "".join(f"ref table '{name}'\nref entity '{name}'\n" for name in tables)
        + "ref expression DL_FIS_Finance\n"
    )
    for name, rows in tables.items():
        key = "DATE_INTEGER" if name == "DIM_DATE" else KEYS[name]
        lines = [
            f"entity '{name}'", f"\tlineageTag: {stable_id(f'entity/{name}')}",
            f"\tbackingTable: '{name}'", f"\tkeyProperty: {key}", "",
        ]
        for column, value in rows[0].items():
            kind = column_type(column, value)
            dtype = "dateTime" if kind in {"date", "timestamp"} else kind
            lines += [
                f"\tproperty '{column}'", f"\t\tdataType: {dtype}",
                f"\t\tlineageTag: {stable_id(f'entity/{name}/{column}')}",
                "\t\tbackingConfiguration", f"\t\t\tvalueColumn: '{name}'.'{column}'", "",
            ]
        files[f"entities/{name}.tmdl"] = "\n".join(lines)
    files["entityRelationships.tmdl"] = "\n".join(
        f"entityRelationship '{r['fromTable']}_{r['toTable']}'\n"
        f"\tlineageTag: {stable_id('relationship/' + r['fromTable'] + '/' + r['toTable'])}\n"
        f"\tfromEntity: '{r['fromTable']}'\n\ttoEntity: '{r['toTable']}'\n"
        f"\tbackingConfiguration\n\t\trelationship: '{r['fromTable']} to {r['toTable']}'\n"
        for r in RELATIONSHIPS
    )
    return files


def graph_files(workspace: str, gold: str) -> dict[str, dict]:
    tables = build_data()
    prefix = f"abfss://{workspace}@onelake.dfs.fabric.microsoft.com/{gold}/Tables"
    sources, node_tables, edge_tables, node_types, edge_types = [], [], [], [], []
    types = {"date": "DATETIME", "timestamp": "DATETIME", "decimal": "FLOAT", "int64": "INT", "string": "STRING"}
    positions = {}
    for index, (name, rows) in enumerate(tables.items()):
        alias = f"{name}_nodeType"
        properties = [{"name": column, "type": types[column_type(column, value)]} for column, value in rows[0].items()]
        sources.append({"name": name, "type": "DeltaTable", "properties": {"path": f"{prefix}/{name.lower()}"}})
        node_types.append({"alias": alias, "labels": [name], "primaryKeyProperties": [KEYS[name]], "properties": properties})
        node_tables.append({
            "id": stable_id(f"graph/node/{name}"), "nodeTypeAlias": alias, "dataSourceName": name,
            "propertyMappings": [{"propertyName": p["name"], "sourceColumn": p["name"]} for p in properties],
        })
        positions[alias] = {"x": index % 4 * 280, "y": index // 4 * 280}
    for relation in RELATIONSHIPS:
        source, target = relation["fromTable"], relation["toTable"]
        name = f"{source}_{target}"
        properties = [
            {"name": "EdgeId", "type": "STRING"}, {"name": "SourceId", "type": "STRING"},
            {"name": "TargetId", "type": "DATETIME" if target == "DIM_DATE" else "STRING"},
        ]
        sources.append({
            "name": name, "type": "DeltaTable", "properties": {"path": f"{prefix}/edge_{name.lower()}"},
        })
        edge_types.append({
            "alias": name, "labels": [name], "sourceNodeType": {"alias": f"{source}_nodeType"},
            "destinationNodeType": {"alias": f"{target}_nodeType"}, "properties": properties,
        })
        edge_tables.append({
            "id": stable_id(f"graph/edge/{name}"), "edgeTypeAlias": name, "dataSourceName": name,
            "sourceNodeKeyColumns": ["SourceId"], "destinationNodeKeyColumns": ["TargetId"],
            "propertyMappings": [{"propertyName": p["name"], "sourceColumn": p["name"]} for p in properties],
        })
    return {
        "dataSources.json": {"dataSources": sources},
        "graphDefinition.json": {"nodeTables": node_tables, "edgeTables": edge_tables},
        "graphType.json": {"nodeTypes": node_types, "edgeTypes": edge_types},
        "stylingConfiguration.json": {
            "modelLayout": {"positions": positions, "styles": {}, "pan": {"x": 0, "y": 0}, "zoomLevel": 1},
        },
    }


def field(table: str, column: str, measure: bool = False) -> dict:
    expression = {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}
    return {"field": expression, "queryRef": f"{table}.{column}", "nativeQueryRef": column}


def report_files(model_id: str) -> dict[str, dict]:
    files = {
        "definition.pbir": {
            "$schema": f"{SCHEMA}/report/definitionProperties/2.0.0/schema.json", "version": "4.0",
            "datasetReference": {"byConnection": {"connectionString": f"semanticmodelid={model_id}"}},
        },
        "definition/version.json": {
            "$schema": f"{SCHEMA}/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0",
        },
        "definition/report.json": {
            "$schema": f"{SCHEMA}/report/definition/report/1.1.0/schema.json",
            "layoutOptimization": "None",
            "themeCollection": {
                "baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.56", "type": "SharedResources"},
            },
        },
    }
    pages = [
        ("executive", "FIS | Executive - SYNTHETIC", [
            "Actual Revenue YTD", "Plan Revenue YTD", "Revenue Variance YTD",
            "Actual Operating Profit YTD", "Actual Operating Margin YTD", "Operating Profit Variance YTD",
        ], "product", "Description", ["Actual Revenue YTD", "Plan Revenue YTD", "Operating Profit Variance YTD"]),
        ("drivers", "FIS | Variance Drivers - SYNTHETIC", [
            "Actual Opex YTD", "Plan Opex YTD", "Favorable Expense Variance YTD",
            "Revenue Variance Pct YTD", "Favorable Expense Variance Pct YTD", "As Of Date",
        ], "cost_center", "Description", ["Actual Opex YTD", "Plan Opex YTD", "Favorable Expense Variance YTD"]),
        ("outlook", "FIS | FY2026 Outlook - SYNTHETIC", [
            "Forecast Revenue FY", "Plan Revenue FY", "Forecast Operating Profit FY",
            "Plan Operating Profit FY", "Forecast Operating Profit Variance FY", "As Of Date",
        ], "product", "Description", ["Forecast Revenue FY", "Plan Revenue FY", "Forecast Operating Profit Variance FY"]),
    ]

    def visual(page: str, name: str, kind: str, query: dict, x: int, y: int, width: int, height: int) -> None:
        files[f"definition/pages/{page}/visuals/{name}/visual.json"] = {
            "$schema": f"{SCHEMA}/report/definition/visualContainer/2.4.0/schema.json", "name": name,
            "position": {"x": x, "y": y, "z": len(files), "height": height, "width": width, "tabOrder": len(files)},
            "visual": {
                "visualType": kind, "query": {"queryState": query}, "drillFilterOtherVisuals": True,
            },
        }

    for page, title, cards, dimension, description, values in pages:
        files[f"definition/pages/{page}/page.json"] = {
            "$schema": f"{SCHEMA}/report/definition/page/2.0.0/schema.json", "name": page,
            "displayName": title, "displayOption": "FitToPage", "height": 800, "width": 1440,
        }
        for index, measure in enumerate(cards):
            visual(page, f"card{index}", "card", {"Values": {"projections": [field("ACTUALS", measure, True)]}},
                   20 + index % 3 * 470, 20 + index // 3 * 145, 450, 130)
        visual(page, "varianceTable", "tableEx", {"Values": {"projections": [
            field(dimension, description), *[field("ACTUALS", measure, True) for measure in values],
        ]}}, 20, 325, 1400, 220)
        monthly = ["Forecast Revenue", "Plan Revenue"] if page == "outlook" else ["Actual Revenue YTD", "Plan Revenue YTD"]
        visual(page, "monthly", "clusteredColumnChart", {
            "Category": {"projections": [field("DIM_DATE", "MONTH_YEAR")]},
            "Y": {"projections": [field("ACTUALS", measure, True) for measure in monthly]},
        }, 20, 565, 1400, 215)
    files["definition/pages/pages.json"] = {
        "$schema": f"{SCHEMA}/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [page[0] for page in pages], "activePageName": "executive",
    }
    return files


def write_bundle(target: Path, files: dict[str, str | dict]) -> None:
    for relative, value in files.items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build(workspace: str = "__WORKSPACE_ID__", bronze: str = "__BRONZE_ID__",
          silver: str = "__SILVER_ID__", gold: str = "__GOLD_ID__", model: str = "__MODEL_ID__") -> dict:
    report = write_data()
    generated = ROOT / "generated"
    write_bundle(generated / "semantic", semantic_files(workspace, gold))
    write_bundle(generated / "ontology", ontology_files(workspace, gold))
    write_bundle(generated / "graph", graph_files(workspace, gold))
    write_bundle(generated / "report", report_files(model))
    write_bundle(generated, {
        "FIS_01_Finance_Medallion.ipynb": notebook(workspace, bronze, silver, gold),
        "FIS_02_Prepare_Ontology_Date_Keys.ipynb": ontology_date_keys_notebook(workspace, gold),
        "fewshots.json": {"fewShots": FEW_SHOTS},
        "gql-queries.json": {"queries": GQL_QUERIES},
    })
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default="__WORKSPACE_ID__")
    parser.add_argument("--bronze", default="__BRONZE_ID__")
    parser.add_argument("--silver", default="__SILVER_ID__")
    parser.add_argument("--gold", default="__GOLD_ID__")
    parser.add_argument("--model", default="__MODEL_ID__")
    args = parser.parse_args()
    print(json.dumps(build(args.workspace, args.bronze, args.silver, args.gold, args.model), indent=2))
