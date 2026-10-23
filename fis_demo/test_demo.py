from __future__ import annotations

import ast
import copy
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from fis_demo.artifacts import (
    GQL_QUERIES, MEASURES, graph_files, notebook, ontology_date_keys_notebook,
    ontology_files, report_files, semantic_files,
)
from fis_demo.data import FACTS, RELATIONSHIPS, build_data, validate, write_data


class FinanceDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tables = build_data()
        cls.report = validate(cls.tables)

    def test_exact_seven_table_contract_and_twelve_relationships(self) -> None:
        self.assertEqual(self.report["tableRows"], {
            "account": 8, "cost_center": 6, "DIM_DATE": 730, "product": 6,
            "ACTUALS": 6048, "FORECAST": 3456, "PLAN": 3456,
        })
        self.assertEqual(self.report["foreignKeyChecks"], 51840)
        self.assertEqual(
            {(r["fromTable"], r["toTable"]) for r in RELATIONSHIPS},
            {(fact, dimension) for fact in FACTS for dimension in ("account", "cost_center", "DIM_DATE", "product")},
        )

    def test_financial_acceptance_values_and_favorable_variance(self) -> None:
        metrics = self.report["metrics"]
        self.assertEqual(metrics["ActualRevenueYTD"], 846750225.60)
        self.assertEqual(metrics["PlanRevenueYTD"], 876508875.00)
        self.assertEqual(metrics["RevenueVarianceYTD"], -29758649.40)
        self.assertEqual(metrics["ExpenseVarianceYTD"], 2360328.90)
        self.assertEqual(metrics["ProfitVarianceYTD"], -27398320.50)
        self.assertEqual(metrics["ForecastProfitFY"], 521621385.18)
        self.assertEqual(metrics["CloudDigitalActualYTD"], 4898894.00)
        self.assertEqual(metrics["CloudDigitalPlanYTD"], 3963960.00)
        self.assertNotIn("ActualRevenueFY", metrics)
        self.assertGreater(
            (Decimal(str(metrics["CloudDigitalActualYTD"])) / Decimal(str(metrics["CloudDigitalPlanYTD"]))) - 1,
            Decimal("0.10"),
        )

    def test_reject_orphan_dimension_key(self) -> None:
        tables = copy.deepcopy(self.tables)
        tables["ACTUALS"][0]["ACCOUNT"] = "NOT_AN_ACCOUNT"
        with self.assertRaisesRegex(ValueError, "Orphan foreign key"):
            validate(tables)

    def test_reject_duplicate_grain_even_with_distinct_record_id(self) -> None:
        tables = copy.deepcopy(self.tables)
        duplicate = dict(tables["PLAN"][0], RecordID="different-record-id")
        tables["PLAN"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "Duplicate finance grain"):
            validate(tables)

    def test_reject_missing_month(self) -> None:
        tables = copy.deepcopy(self.tables)
        tables["FORECAST"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete period coverage"):
            validate(tables)

    def test_reject_invalid_money_precision(self) -> None:
        tables = copy.deepcopy(self.tables)
        tables["PLAN"][0]["Amount"] = "1.001"
        with self.assertRaisesRegex(ValueError, "Amount and AmountCents disagree"):
            validate(tables)

    def test_reject_forecast_closed_month_drift(self) -> None:
        tables = copy.deepcopy(self.tables)
        row = tables["FORECAST"][0]
        row["AmountCents"] = int(row["AmountCents"]) + 100
        row["Amount"] = str(Decimal(int(row["AmountCents"])).scaleb(-2))
        with self.assertRaisesRegex(ValueError, "Closed-month forecast"):
            validate(tables)

    def test_serialized_data_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fis-finance-test-") as directory:
            target = Path(directory)
            write_data(target)
            first = json.loads((target / "data-sha256.json").read_text())
            write_data(target)
            self.assertEqual(first, json.loads((target / "data-sha256.json").read_text()))
            self.assertEqual(len(first), 7)

    def test_generated_notebook_compiles_and_guards_persisted_data(self) -> None:
        document = notebook("workspace", "bronze", "silver", "gold")
        for cell in document["cells"]:
            if cell["cell_type"] == "code":
                ast.parse("".join(cell["source"]), filename=cell["id"])
        source = "\n".join("".join(cell["source"]) for cell in document["cells"])
        self.assertIn('namespace["validate"](persisted)', source)
        self.assertIn('report["metrics"] != expected["metrics"]', source)
        self.assertIn("[36, 9, 6, 9]", source)

    def test_all_model_surfaces_preserve_the_same_twelve_edges(self) -> None:
        semantic = semantic_files("workspace", "gold")
        self.assertEqual(semantic["definition/relationships.tmdl"].count("relationship '"), 12)
        self.assertEqual(semantic["definition/relationships.tmdl"].count("oneDirection"), 12)
        self.assertEqual(sum(name.startswith("definition/tables/") for name in semantic), 7)
        self.assertNotIn("fef80264", json.dumps(semantic))
        ontology = ontology_files("workspace", "gold")
        self.assertEqual(sum(name.startswith("entities/") and name.endswith(".tmdl") for name in ontology), 7)
        self.assertEqual(ontology["entityRelationships.tmdl"].count("entityRelationship "), 12)
        self.assertEqual(ontology["relationships.tmdl"], semantic["definition/relationships.tmdl"])
        self.assertIn("compatibilityLevel: 1000000", ontology["database.tmdl"])
        graph = graph_files("workspace", "gold")
        self.assertEqual(len(graph["graphType.json"]["nodeTypes"]), 7)
        self.assertEqual(len(graph["graphType.json"]["edgeTypes"]), 12)
        self.assertEqual(
            {edge["labels"][0] for edge in graph["graphType.json"]["edgeTypes"]},
            {f"{r['fromTable']}_{r['toTable']}" for r in RELATIONSHIPS},
        )

    def test_report_binds_only_to_requested_model_and_known_measures(self) -> None:
        files = report_files("new-model-only")
        self.assertEqual(files["definition/version.json"]["version"], "2.0.0")
        self.assertEqual(files["definition/report.json"]["themeCollection"]["baseTheme"]["type"], "SharedResources")
        self.assertEqual(
            files["definition.pbir"]["datasetReference"]["byConnection"]["connectionString"],
            "semanticmodelid=new-model-only",
        )
        pages = [value for name, value in files.items() if name.endswith("/page.json")]
        self.assertEqual(len(pages), 3)
        self.assertTrue(all("SYNTHETIC" in page["displayName"] for page in pages))
        for name, value in files.items():
            if not name.endswith("/visual.json"):
                continue
            for state in value["visual"]["query"]["queryState"].values():
                for projection in state["projections"]:
                    measure = projection["field"].get("Measure")
                    if measure:
                        self.assertIn(measure["Property"], MEASURES)

    def test_gql_quotes_reserved_product_identifier(self) -> None:
        for query in GQL_QUERIES:
            self.assertIn("(p:`product`)", query)
            self.assertNotIn(":product)", query)
            self.assertNotIn("(product:", query)

    def test_ontology_uses_supported_key_types_including_integer_date_key(self) -> None:
        files = ontology_files("workspace", "gold")
        for name, rows in self.tables.items():
            text = files[f"entities/{name}.tmdl"]
            key_line = next(line for line in text.splitlines() if line.startswith("\tkeyProperty: "))
            key = key_line.split(": ", 1)[1]
            self.assertIsInstance(rows[0][key], (str, int))
            self.assertIn(f"\tbackingTable: '{name}'", text)
            self.assertEqual(text.count("valueColumn: "), len(rows[0]))
            if name == "DIM_DATE":
                self.assertEqual(key, "DATE_INTEGER")
        document = ontology_date_keys_notebook("workspace", "gold")
        for item in document["cells"]:
            if item["cell_type"] == "code":
                ast.parse("".join(item["source"]))


if __name__ == "__main__":
    unittest.main()
