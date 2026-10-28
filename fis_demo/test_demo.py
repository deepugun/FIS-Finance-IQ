from __future__ import annotations

import ast
import copy
import csv
import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from fis_demo.artifacts import (
    GQL_QUERIES, MEASURES, graph_files, notebook, ontology_date_keys_notebook,
    ontology_files, report_files, semantic_files,
)
from fis_demo.data import FACTS, RELATIONSHIPS, build_data, column_type, validate, write_data


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
        self.assertEqual(len(RELATIONSHIPS), 12)
        self.assertEqual(
            {
                (r["fromTable"], r["fromColumn"], r["toTable"], r["toColumn"])
                for r in RELATIONSHIPS
            },
            {
                (fact, column, dimension, key)
                for fact in ("ACTUALS", "FORECAST", "PLAN")
                for dimension, column, key in (
                    ("account", "ACCOUNT", "Account"),
                    ("cost_center", "COSTCENTER", "CostCenter"),
                    ("DIM_DATE", "DATE", "DATE"),
                    ("product", "PRODUCTLINE", "ProductLine"),
                )
            },
        )

    def test_columns_visible_in_fis_screenshots(self) -> None:
        fact_columns = set(
            "ACCOUNT Amount CC_PR_AC COSTCENTER COSTCENTER_PRODUCTLINE CURRENCY "
            "CUSTOMER DATASOURCE DATE ENTITY ICP LOAD_DATE LOAD_TIMESTAMP LOCATION "
            "PERIOD PRODUCTLINE QUARTER SCENARIO VERSION VIEW YEAR".split()
        )
        expected = {
            **{fact: fact_columns for fact in ("ACTUALS", "FORECAST", "PLAN")},
            "account": {"Account", "Description", "Description_raw"} | {
                f"L{level}{suffix}"
                for level in range(1, 9)
                for suffix in ("", "_Description")
            },
            "cost_center": {"CostCenter", "CostCenter_Cleaned"} | {
                f"CC_L{level}{suffix}"
                for level in range(1, 5)
                for suffix in ("", "_Description", "_Description_New")
            },
            "product": {"ProductLine", "ProductLine_Cleaned", "Description", "Description_New"} | {
                f"L{level}{suffix}"
                for level in range(1, 9)
                for suffix in ("", "_Description", "_Description_New")
            },
            "DIM_DATE": set(
                "DATE DATE_INTEGER DAY_NUMBER DAY_OF_WEEK DAY_OF_WEEK_LONG DAY_OF_WEEK_SHORT "
                "FIRST_DAY_MONTH FIRST_DAY_QUARTER LAST_DAY_MONTH LAST_DAY_QUARTER MONTH_ID "
                "MONTH_NAME_LONG MONTH_NAME_SHORT MONTH_YEAR MONTH_YEAR_INTEGER MONTHNUMBER "
                "PY_COMPARE_DATE QUARTER QUARTER_ID QUARTER_SEQUENCE REPORTING_MONTH SOW_MONDAY "
                "WEEK_OF_YEAR YEAR YEAR_MONTH YEAR_MONTH_SHORT YEAR_MONTH_SHORT_V1 YEAR_QUARTER".split()
            ),
        }
        for table, columns in expected.items():
            with self.subTest(table=table):
                missing = columns.difference(self.tables[table][0])
                self.assertFalse(missing, f"{table} missing screenshot columns: {sorted(missing)}")

    def test_inferred_calendar_attributes_at_period_boundaries(self) -> None:
        columns = (
            "FIRST_DAY_QUARTER", "LAST_DAY_QUARTER", "QUARTER_SEQUENCE",
            "SOW_MONDAY", "YEAR_MONTH_SHORT_V1",
        )
        expected = {
            "2025-01-01": ("2025-01-01", "2025-03-31", 1, "2024-12-30", "Jan-25"),
            "2025-03-31": ("2025-01-01", "2025-03-31", 1, "2025-03-31", "Mar-25"),
            "2025-12-31": ("2025-10-01", "2025-12-31", 4, "2025-12-29", "Dec-25"),
            "2026-01-01": ("2026-01-01", "2026-03-31", 5, "2025-12-29", "Jan-26"),
            "2026-04-01": ("2026-04-01", "2026-06-30", 6, "2026-03-30", "Apr-26"),
            "2026-07-01": ("2026-07-01", "2026-09-30", 7, "2026-06-29", "Jul-26"),
            "2026-09-30": ("2026-07-01", "2026-09-30", 7, "2026-09-28", "Sep-26"),
            "2026-12-31": ("2026-10-01", "2026-12-31", 8, "2026-12-28", "Dec-26"),
        }
        rows = {str(row["DATE"]): row for row in self.tables["DIM_DATE"]}
        for day, values in expected.items():
            with self.subTest(day=day):
                self.assertEqual(tuple(rows[day][column] for column in columns), values)
        for day, row in rows.items():
            with self.subTest(day=day):
                current = date.fromisoformat(day)
                monday = date.fromisoformat(str(row["SOW_MONDAY"]))
                self.assertEqual(monday.weekday(), 0)
                self.assertLessEqual(0, (current - monday).days)
                self.assertLess((current - monday).days, 7)
                self.assertLessEqual(str(row["FIRST_DAY_QUARTER"]), day)
                self.assertGreaterEqual(str(row["LAST_DAY_QUARTER"]), day)
        self.assertEqual({row["QUARTER_SEQUENCE"] for row in rows.values()}, set(range(1, 9)))

    def test_inferred_calendar_attributes_are_typed_on_every_model_surface(self) -> None:
        semantic = semantic_files("workspace", "gold")
        ontology = ontology_files("workspace", "gold")
        graph = graph_files("workspace", "gold")
        node = next(node for node in graph["graphType.json"]["nodeTypes"] if node["labels"] == ["DIM_DATE"])
        properties = {prop["name"]: prop["type"] for prop in node["properties"]}
        expected = {
            "FIRST_DAY_QUARTER": ("date", "dateTime", "DATETIME"),
            "LAST_DAY_QUARTER": ("date", "dateTime", "DATETIME"),
            "QUARTER_SEQUENCE": ("int64", "int64", "INT"),
            "SOW_MONDAY": ("date", "dateTime", "DATETIME"),
            "YEAR_MONTH_SHORT_V1": ("string", "string", "STRING"),
        }
        for column, (source_type, model_type, graph_type) in expected.items():
            with self.subTest(column=column):
                self.assertEqual(column_type(column, self.tables["DIM_DATE"][0][column]), source_type)
                self.assertIn(
                    f"\tcolumn '{column}'\n\t\tdataType: {model_type}\n",
                    semantic["definition/tables/DIM_DATE.tmdl"],
                )
                self.assertIn(
                    f"\tproperty '{column}'\n\t\tdataType: {model_type}\n",
                    ontology["entities/DIM_DATE.tmdl"],
                )
                self.assertEqual(properties[column], graph_type)

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
            schema = json.loads((target / "schema.json").read_text())
            self.assertEqual(schema["DIM_DATE"], {
                column: column_type(column, value)
                for column, value in self.tables["DIM_DATE"][0].items()
            })
            with (target / "data" / "DIM_DATE.csv").open(newline="", encoding="utf-8") as stream:
                self.assertEqual(list(csv.DictReader(stream)), [
                    {column: str(value) for column, value in row.items()}
                    for row in self.tables["DIM_DATE"]
                ])

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
