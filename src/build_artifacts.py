import ast
import csv
import hashlib
import json
from pathlib import Path

from insurance_demo import ROOT, KEYS, AS_OF, build_data, validate

ENTITIES = {
    "Account": "Accounts", "Insured": "Insureds", "Broker": "Brokers", "Policy": "Policies",
    "Coverage": "Coverages", "Location": "Locations", "Exposure": "Exposures", "Asset": "Assets",
    "Claim": "Claims", "LossEvent": "LossEvents", "CATRisk": "CATRisk", "Peril": "Perils",
    "RiskEngineeringInspection": "EngineeringInspections", "EngineeringRecommendation": "EngineeringRecommendations",
    "Renewal": "Renewals", "RenewalSignal": "RenewalSignals", "Submission": "Submissions",
    "Industry": "Industries", "Country": "Countries", "MultinationalProgram": "MultinationalPrograms",
    "LocalPolicy": "LocalPolicies", "Underwriter": "Underwriters", "PricingScenario": "PricingScenarios",
    "UnderwritingDecision": "UnderwritingDecisions", "ProgramRequirement": "ProgramRequirements",
}
RELATIONS = [
    ("Broker", "SERVICES", "Account", "Accounts", "BrokerId", "AccountId"),
    ("Underwriter", "OWNS", "Account", "Accounts", "UnderwriterId", "AccountId"),
    ("Account", "CLASSIFIED_AS", "Industry", "Accounts", "AccountId", "IndustryId"),
    ("Account", "HAS_INSURED", "Insured", "Insureds", "AccountId", "InsuredId"),
    ("Account", "HOLDS", "Policy", "Policies", "AccountId", "PolicyId"),
    ("Policy", "PROVIDES", "Coverage", "Coverages", "PolicyId", "CoverageId"),
    ("Account", "OPERATES", "Location", "Locations", "AccountId", "LocationId"),
    ("Insured", "OCCUPIES", "Location", "Locations", "InsuredId", "LocationId"),
    ("Location", "IN_COUNTRY", "Country", "Locations", "LocationId", "CountryId"),
    ("Location", "HAS_EXPOSURE", "Exposure", "Exposures", "LocationId", "ExposureId"),
    ("Location", "CONTAINS", "Asset", "Assets", "LocationId", "AssetId"),
    ("Location", "HAS_CAT", "CATRisk", "CATRisk", "LocationId", "CATId"),
    ("CATRisk", "FOR_PERIL", "Peril", "CATRisk", "CATId", "PerilId"),
    ("Location", "HAS_CLAIM", "Claim", "Claims", "LocationId", "ClaimId"),
    ("Claim", "ON_POLICY", "Policy", "Claims", "ClaimId", "PolicyId"),
    ("Claim", "ON_COVERAGE", "Coverage", "Claims", "ClaimId", "CoverageId"),
    ("Claim", "FROM_EVENT", "LossEvent", "Claims", "ClaimId", "LossEventId"),
    ("LossEvent", "OF_PERIL", "Peril", "LossEvents", "LossEventId", "PerilId"),
    ("Location", "INSPECTED_BY", "RiskEngineeringInspection", "EngineeringInspections", "LocationId", "InspectionId"),
    ("RiskEngineeringInspection", "ISSUED", "EngineeringRecommendation", "EngineeringRecommendations", "InspectionId", "RecommendationId"),
    ("Account", "RENEWS", "Renewal", "Renewals", "AccountId", "RenewalId"),
    ("Renewal", "HAS_SIGNAL", "RenewalSignal", "RenewalSignals", "RenewalId", "SignalId"),
    ("Account", "HAS_SUBMISSION", "Submission", "Submissions", "AccountId", "SubmissionId"),
    ("Account", "HAS_PROGRAM", "MultinationalProgram", "MultinationalPrograms", "AccountId", "ProgramId"),
    ("MultinationalProgram", "HAS_LOCAL", "LocalPolicy", "LocalPolicies", "ProgramId", "LocalPolicyId"),
    ("LocalPolicy", "IN_COUNTRY", "Country", "LocalPolicies", "LocalPolicyId", "CountryId"),
    ("MultinationalProgram", "REQUIRES", "ProgramRequirement", "ProgramRequirements", "ProgramId", "RequirementId"),
    ("ProgramRequirement", "MATCHES_LOCAL", "LocalPolicy", "ProgramRequirements", "RequirementId", "LocalPolicyId"),
    ("Renewal", "CONSIDERS", "PricingScenario", "PricingScenarios", "RenewalId", "ScenarioId"),
    ("Renewal", "HAS_DECISION", "UnderwritingDecision", "UnderwritingDecisions", "RenewalId", "DecisionId"),
]


def graph_data(tables):
    nodes = {}
    for entity, table in ENTITIES.items():
        rows = tables[table]
        if table in ("Exposures", "CATRisk"):
            rows = [row for row in rows if row["SnapshotDate"] == AS_OF.isoformat()]
        nodes[entity] = rows
    edges = {}
    for source, relation, target, table, source_key, target_key in RELATIONS:
        source_ids = {row[KEYS[ENTITIES[source]]] for row in nodes[source]}
        target_ids = {row[KEYS[ENTITIES[target]]] for row in nodes[target]}
        rows = [{"EdgeId": f"{source}_{relation}_{target}_{row[source_key]}_{row[target_key]}",
                 "SourceId": row[source_key], "TargetId": row[target_key]}
                for row in tables[table] if row[source_key] in source_ids and row[target_key] in target_ids]
        assert len({row["EdgeId"] for row in rows}) == len(rows)
        edges[f"{source}_{relation}_{target}"] = rows
    return nodes, edges


def write_graph(tables):
    nodes, edges = graph_data(tables)
    target = ROOT / "graph"
    target.mkdir(exist_ok=True)
    manifest = {"nodes": [], "edges": []}
    for entity, rows in nodes.items():
        path = target / f"node_{entity}.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        manifest["nodes"].append({"label": entity, "table": f"node_{entity}", "key": KEYS[ENTITIES[entity]], "rows": len(rows)})
    for source, relation, dest, table, source_key, dest_key in RELATIONS:
        name = f"{source}_{relation}_{dest}"
        rows = edges[name]
        with (target / f"edge_{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["EdgeId", "SourceId", "TargetId"])
            writer.writeheader()
            writer.writerows(rows)
        manifest["edges"].append({"label": relation, "sourceLabel": source, "targetLabel": dest,
                                  "table": f"edge_{name}", "sourceColumn": "SourceId", "targetColumn": "TargetId", "rows": len(rows)})
    (target / "mapping-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def notebook(title, instructions, code):
    ast.parse(code)
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Synapse PySpark", "language": "python", "name": "synapse_pyspark"},
        "language_info": {"name": "python"}}, "cells": [
        {"cell_type": "markdown", "id": "intro", "metadata": {}, "source": (f"# {title}\n\n{instructions}\n").splitlines(True)},
        {"cell_type": "code", "id": "execute", "metadata": {}, "execution_count": None, "outputs": [], "source": (code.strip() + "\n").splitlines(True)}]}


def write_notebook_templates():
    source_code = (ROOT / "src/insurance_demo.py").read_text(encoding="utf-8")
    source_code = source_code.replace("ROOT = Path(__file__).resolve().parents[1]", 'ROOT = Path("/lakehouse/default/Files/underwriting_demo")')
    source_code = source_code.split('if __name__ == "__main__":')[0]
    bootstrap = """import sys
from pathlib import Path
BASE = Path('/lakehouse/default/Files/underwriting_demo')
sys.path.insert(0, str(BASE / 'src'))
from insurance_demo import build_data, validate, column_type, AS_OF, ROOT
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType
TABLE_PREFIX = 'demo_'

def save_rows(name, rows):
    types = {'bit': BooleanType(), 'bigint': LongType(), 'float': DoubleType()}
    schema = StructType([StructField(field, types.get(column_type(field, rows), StringType()), True) for field in rows[0]])
    frame = spark.createDataFrame(rows, schema)
    for field in rows[0]:
        datatype = column_type(field, rows)
        if datatype == 'date':
            frame = frame.withColumn(field, F.to_date(field))
        elif datatype == 'datetime2(6)':
            frame = frame.withColumn(field, F.to_timestamp(field))
    destination = TABLE_PREFIX + name
    if spark.catalog.tableExists(destination):
        properties = {row.key: row.value for row in spark.sql(f'SHOW TBLPROPERTIES {destination}').collect()}
        assert properties.get('delta.columnMapping.mode', 'none') == 'none', 'Use a new managed demo table without column mapping'
    frame.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(destination)
    assert spark.table(destination).count() == len(rows)
    return frame
"""
    entries = [
        ("01_generate_synthetic_data", "Generate the synthetic portfolio", "Attach a dedicated default demo lakehouse. This writes only under Files/underwriting_demo. No production data or credentials are used.",
         source_code + "\ndata = build_data()\nprint(validate(data))\nwrite_outputs(data)\nmodule_dir = ROOT / 'src'\nmodule_dir.mkdir(parents=True, exist_ok=True)\n" +
         f"(module_dir / 'insurance_demo.py').write_text({source_code!r}, encoding='utf-8')\n"),
        ("02_create_delta_tables", "Create managed Delta tables", "Run after 01. Overwrites only demo_ tables in the attached lakehouse. Do not enable Delta column mapping. Verify the lakehouse is the dedicated demo destination before running.",
         bootstrap + "\ndata = build_data()\nvalidate(data)\nfor table, rows in data.items():\n    save_rows(table, rows)\nprint('Managed Delta tables created')\n"),
        ("03_underwriting_features", "Derive underwriting features", "Read persisted source tables, validate, and recompute feature rows. This small demo collects source rows locally; replace with distributed aggregation for production volumes.",
         bootstrap + "\nfrom insurance_demo import calculate_features\ndata = {name: [row.asDict() for row in spark.table(TABLE_PREFIX + name).collect()] for name in build_data()}\nfor rows in data.values():\n    for row in rows:\n        for key, value in row.items():\n            if hasattr(value, 'isoformat'):\n                row[key] = value.isoformat()\nvalidate(data)\nfeatures = calculate_features(data)\nsave_rows('UnderwritingFeatures', features)\ndisplay(spark.table(TABLE_PREFIX + 'UnderwritingFeatures'))\n"),
        ("04_renewal_risk_pulse", "Calculate transparent Renewal Risk Pulse", "Every component is clipped to [0,1]. Weights sum to 100. No actuarial or predictive claim is made.",
         bootstrap + "\nfrom insurance_demo import WEIGHTS\nfeatures = spark.table(TABLE_PREFIX + 'UnderwritingFeatures')\nscore = sum(F.lit(weight) * F.least(F.lit(1.0), F.greatest(F.lit(0.0), F.col(component))) for component, weight in WEIGHTS.items())\npulses = features.select('AccountId', 'SnapshotDate', *WEIGHTS).withColumn('PulseId', F.concat(F.lit('PULSE'), F.col('AccountId'))).withColumn('Pulse', F.round(score, 2))\npulses.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(TABLE_PREFIX + 'RiskPulse')\nassert pulses.filter(F.col('AccountId') == 'A001').first().Pulse == 77.0\ndisplay(pulses.orderBy(F.desc('Pulse')))\n"),
        ("05_material_change_signals", "Identify material changes", "Use matched valuation dates and versioned evidence keys. Signals are triage flags, not binding recommendations.",
         bootstrap + "\nfrom functools import reduce\nfeatures = spark.table(TABLE_PREFIX + 'UnderwritingFeatures')\nrules = [('CAT deterioration', 'CATGrowth', 0.25, 'CATRisk'), ('Claims development', 'ClaimsGrowth', 0.25, 'ClaimValuations'), ('Exposure growth', 'TIVGrowth', 0.20, 'Exposures'), ('Engineering deficiencies', 'Engineering', 0.50, 'EngineeringRecommendations'), ('Missing information', 'Missing', 0.50, 'Renewals')]\nframes = []\nfor index, (name, field, threshold, source) in enumerate(rules):\n    frames.append(features.filter(F.col(field) >= threshold).select('AccountId', F.concat(F.lit('SIG'), F.col('AccountId'), F.lit(str(index))).alias('SignalId'), F.concat(F.lit('R'), F.substring('AccountId', 2, 3)).alias('RenewalId'), F.lit(name).alias('SignalType'), F.col(field).alias('Value'), F.lit(threshold).alias('Threshold'), F.lit('High').alias('Materiality'), F.lit(source).alias('SourceTable'), F.col('AccountId').alias('EvidenceKey'), F.col('SnapshotDate').alias('DetectedDate')))\nsignals = reduce(lambda left, right: left.unionByName(right), frames)\nsignals.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable(TABLE_PREFIX + 'RenewalSignals')\ndisplay(signals)\n"),
        ("06_graph_nodes_edges", "Materialize Graph inputs", "Node properties use source column names for the standalone Graph demo. The ontology uses separate short aliases. Import mapping-manifest.json as a mapping guide, not an undocumented Fabric API definition.",
         bootstrap + f"\nENTITIES = {ENTITIES!r}\nRELATIONS = {RELATIONS!r}\n" + "\nfor entity, table in ENTITIES.items():\n    frame = spark.table(TABLE_PREFIX + table)\n    if table in ('Exposures', 'CATRisk'):\n        frame = frame.filter(F.col('SnapshotDate') == F.lit(AS_OF.isoformat()))\n    frame.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable('node_' + entity)\nfor source, relation, target, table, source_key, target_key in RELATIONS:\n    frame = spark.table(TABLE_PREFIX + table)\n    if table in ('Exposures', 'CATRisk'):\n        frame = frame.filter(F.col('SnapshotDate') == F.lit(AS_OF.isoformat()))\n    edges = frame.select(F.col(source_key).alias('SourceId'), F.col(target_key).alias('TargetId')).dropDuplicates()\n    edges = edges.withColumn('EdgeId', F.concat_ws('_', F.lit(source + '_' + relation + '_' + target), 'SourceId', 'TargetId'))\n    edges.write.format('delta').mode('overwrite').option('overwriteSchema', 'true').saveAsTable('edge_' + source + '_' + relation + '_' + target)\nprint('Build/refresh Graph and refresh ontology manually before rehearsal')\n"),
        ("07_live_demo_events", "Stage the live pulse crossing", "Run twice: PHASE='baseline', then after the agent has observed baseline set PHASE='update'. Upload the resulting one-line JSON file through Eventhouse Get data > Local file. This notebook does NOT claim automatic Eventhouse ingestion. Use a unique RUN_ID and the same value on both runs.",
         bootstrap + "\nimport json\nfrom datetime import datetime, timezone\nfrom insurance_demo import live_events\nRUN_ID = 'rehearsal-001'\nPHASE = 'baseline'\nassert PHASE in ('baseline', 'update')\nevents = live_events(build_data(), RUN_ID, datetime.now(timezone.utc))\nevent = events[0 if PHASE == 'baseline' else 1]\nevent['EventTime'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')\noutput = BASE / f'{RUN_ID}-{PHASE}.jsonl'\noutput.write_text(json.dumps(event) + '\\n', encoding='utf-8')\nprint(str(output))\nprint(event)\n"),
    ]
    directory = ROOT / "notebooks"
    directory.mkdir(exist_ok=True)
    for filename, title, instructions, code in entries:
        artifact = notebook(title, instructions, code)
        (directory / f"{filename}.ipynb").write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return len(entries)


def write_dictionary(tables):
    lines = ["# Source Data Dictionary", "", "Generated from the same schema as CSV and SQL. All data is synthetic. IDs are stable strings; all USD monetary fields are integer cents. Nullable fields are explicit. Table grains and business usage are described in the architecture document.", ""]
    for table, rows in tables.items():
        lines += [f"## {table}", f"Key: `{KEYS[table]}`. Rows: {len(rows)}.", "", "| Column | Example |", "|---|---|"]
        for column in rows[0]:
            lines.append(f"| {column} | {str(rows[0][column]).replace('|', '/')} |")
        lines.append("")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/data-dictionary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    data = build_data()
    validate(data)
    manifest = write_graph(data)
    count = write_notebook_templates()
    write_dictionary(data)
    hashes = {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in sorted((ROOT / 'data/csv').glob('*.csv'))}
    (ROOT / 'validation/data-sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps({'notebook_templates': count, 'node_types': len(manifest['nodes']), 'edge_mappings': len(manifest['edges']),
                      'nodes': sum(row['rows'] for row in manifest['nodes']), 'edges': sum(row['rows'] for row in manifest['edges']), 'status': 'PASS'}))