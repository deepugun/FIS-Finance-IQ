"""Deterministic, fictional FIS-style FP&A data. No customer data is used."""

from __future__ import annotations

import calendar
import csv
import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AS_OF = date(2026, 9, 30)
YEAR = AS_OF.year
FACTS = ("ACTUALS", "FORECAST", "PLAN")
KEYS = {
    "account": "Account",
    "cost_center": "CostCenter",
    "DIM_DATE": "DATE",
    "product": "ProductLine",
    **{name: "RecordID" for name in FACTS},
}
DIMENSIONS = (
    ("account", "ACCOUNT", "Account"),
    ("cost_center", "COSTCENTER", "CostCenter"),
    ("DIM_DATE", "DATE", "DATE"),
    ("product", "PRODUCTLINE", "ProductLine"),
)
RELATIONSHIPS = [
    {"fromTable": fact, "fromColumn": column, "toTable": dimension, "toColumn": key}
    for fact in FACTS
    for dimension, column, key in DIMENSIONS
]
Scalar = str | int
Row = dict[str, Scalar]
Tables = dict[str, list[Row]]


def month_date(year: int, month: int) -> str:
    return date(year, month, 1).isoformat()


def baseline(account: Row, product: Row, center: Row, month: int) -> int:
    return (
        int(account["MonthlyBaseCents"])
        * int(product["DemoWeight"])
        * int(center["DemoWeight"])
        * (100 + 2 * month)
        // 1_000_000
    )


def scenario_amount(
    planned: int, account: Row, product: Row, center: Row, month: int, future: bool = False
) -> int:
    if account["AccountType"] == "Revenue":
        factor = 9700
        if product["ProductLine"] == "DIGITAL" and month >= 7:
            factor = 9300 if future else 9000
    elif account["Account"] == "500100":
        factor = 10300
        if center["CostCenter"] == "300110" and product["ProductLine"] in {"DIGITAL", "PAYMENTS"}:
            factor = (13000 if future else 14500) if month >= 6 else 10500
    elif account["Account"] == "500200":
        factor = 9800 if future else 9600
    else:
        factor = 10200
    return planned * factor // 10000


def fact_row(
    scenario: str, year: int, month: int, account: Row, product: Row, center: Row, amount: int
) -> Row:
    account_id, product_id, center_id = account["Account"], product["ProductLine"], center["CostCenter"]
    versions = {"ACTUALS": "ACTUAL_FINAL_2026_09", "FORECAST": "FCST_2026_09", "PLAN": "PLAN_2026_V1"}
    return {
        "RecordID": f"{scenario}-{year}{month:02}-{account_id}-{center_id}-{product_id}",
        "ACCOUNT": account_id,
        "Amount": str(Decimal(amount).scaleb(-2)),
        "AmountCents": amount,
        "CC_PR_AC": f"{center_id}|{product_id}|{account_id}",
        "COSTCENTER": center_id,
        "COSTCENTER_PRODUCTLINE": f"{center_id}|{product_id}",
        "CURRENCY": "USD",
        "CUSTOMER": "SYNTHETIC_AGGREGATE",
        "DATASOURCE": "SYNTHETIC_FIS_DEMO",
        "DATE": month_date(year, month),
        "ENTITY": "FIS_DEMO_US",
        "ICP": "EXTERNAL",
        "LOAD_DATE": AS_OF.isoformat(),
        "LOAD_TIMESTAMP": f"{AS_OF.isoformat()}T23:00:00Z",
        "LOCATION": "US",
        "PERIOD": month,
        "PRODUCTLINE": product_id,
        "QUARTER": f"Q{(month - 1) // 3 + 1}",
        "SCENARIO": scenario,
        "VERSION": versions[scenario],
        "VIEW": "PERIODIC",
        "YEAR": year,
    }


def build_data() -> Tables:
    accounts: list[Row] = []
    account_specs = [
        ("400100", "Platform subscriptions", "Revenue", 120_000_000),
        ("400200", "Transaction processing", "Revenue", 90_000_000),
        ("400300", "Professional services", "Revenue", 25_000_000),
        ("500100", "Cloud and infrastructure", "Operating Expense", 26_000_000),
        ("500200", "Workforce", "Operating Expense", 65_000_000),
        ("500300", "Third-party services", "Operating Expense", 19_000_000),
        ("500400", "Facilities", "Operating Expense", 6_000_000),
        ("500500", "Risk and compliance", "Operating Expense", 9_000_000),
    ]
    for code, description, category, base in account_specs:
        row: Row = {
            "Account": code, "Description": description, "Description_raw": description,
            "AccountType": category, "FavorableSign": 1 if category == "Revenue" else -1,
            "MonthlyBaseCents": base,
        }
        for level, value in enumerate(
            ["FIS demo", "Operating statement", category, category, description, description, description, code], 1
        ):
            row[f"L{level}"] = value
            row[f"L{level}_Description"] = value
        accounts.append(row)

    products: list[Row] = []
    for code, description, segment, weight in [
        ("BNK_CORE", "Core Banking Platform", "Banking", 125),
        ("DIGITAL", "Digital Banking", "Banking", 110),
        ("PAYMENTS", "Payment Processing", "Banking", 145),
        ("CAP_MKT", "Capital Markets Platform", "Capital Markets", 130),
        ("LENDING", "Lending Services", "Banking", 90),
        ("TREASURY", "Treasury Solutions", "Capital Markets", 85),
    ]:
        row = {
            "ProductLine": code, "ProductLine_Cleaned": code, "Description": description,
            "Description_New": description, "Segment": segment, "DemoWeight": weight,
        }
        for level, value in enumerate(
            ["FIS demo", segment, "Financial technology", description, "Solutions", "Global", description, code], 1
        ):
            row[f"L{level}"] = value
            row[f"L{level}_Description"] = value
            row[f"L{level}_Description_New"] = value
        products.append(row)

    centers: list[Row] = []
    for code, description, function, weight in [
        ("100110", "Banking Engineering", "Engineering", 100),
        ("100210", "Digital Operations", "Operations", 85),
        ("200110", "Markets Operations", "Operations", 110),
        ("300110", "Cloud Infrastructure", "Technology", 140),
        ("900110", "Corporate Finance", "Corporate", 55),
        ("900210", "Risk and Compliance", "Corporate", 60),
    ]:
        row = {
            "CostCenter": code, "CostCenter_Cleaned": code,
            "Description": description, "Function": function, "DemoWeight": weight,
        }
        for level, value in enumerate(["FIS demo", function, description, code], 1):
            row[f"CC_L{level}"] = value
            row[f"CC_L{level}_Description"] = value
            row[f"CC_L{level}_Description_New"] = value
        centers.append(row)

    dates: list[Row] = []
    current = date(YEAR - 1, 1, 1)
    while current <= date(YEAR, 12, 31):
        quarter = (current.month - 1) // 3 + 1
        first = current.replace(day=1)
        last = current.replace(day=calendar.monthrange(current.year, current.month)[1])
        prior = current.replace(year=current.year - 1)
        dates.append({
            "DATE": current.isoformat(), "DATE_INTEGER": int(current.strftime("%Y%m%d")),
            "DAY_NUMBER": current.day, "DAY_OF_WEEK": current.isoweekday(),
            "DAY_OF_WEEK_LONG": current.strftime("%A"), "DAY_OF_WEEK_SHORT": current.strftime("%a"),
            "FIRST_DAY_MONTH": first.isoformat(), "LAST_DAY_MONTH": last.isoformat(),
            "MONTH_ID": current.year * 100 + current.month,
            "MONTH_NAME_LONG": current.strftime("%B"), "MONTH_NAME_SHORT": current.strftime("%b"),
            "MONTH_YEAR": current.strftime("%b %Y"), "MONTH_YEAR_INTEGER": current.year * 100 + current.month,
            "MONTHNUMBER": current.month, "PY_COMPARE_DATE": prior.isoformat(),
            "QUARTER": f"Q{quarter}", "QUARTER_ID": current.year * 10 + quarter,
            "REPORTING_MONTH": AS_OF.strftime("%Y-%m"), "WEEK_OF_YEAR": current.isocalendar().week,
            "YEAR": current.year, "YEAR_MONTH": current.strftime("%Y-%m"),
            "YEAR_MONTH_SHORT": current.strftime("%b %y"), "YEAR_QUARTER": f"{current.year} Q{quarter}",
        })
        current += timedelta(days=1)

    tables: Tables = {"account": accounts, "cost_center": centers, "DIM_DATE": dates, "product": products}
    tables.update({name: [] for name in FACTS})
    for account in accounts:
        for product in products:
            for center in centers:
                for month in range(1, 13):
                    planned = baseline(account, product, center, month)
                    prior = planned * (9000 + month * 10) // 10000
                    tables["ACTUALS"].append(fact_row("ACTUALS", YEAR - 1, month, account, product, center, prior))
                    tables["PLAN"].append(fact_row("PLAN", YEAR, month, account, product, center, planned))
                    actual = scenario_amount(planned, account, product, center, month)
                    if month <= AS_OF.month:
                        tables["ACTUALS"].append(fact_row("ACTUALS", YEAR, month, account, product, center, actual))
                    outlook = scenario_amount(planned, account, product, center, month, future=month > AS_OF.month)
                    tables["FORECAST"].append(fact_row("FORECAST", YEAR, month, account, product, center, outlook))
    return tables


def column_type(name: str, value: Scalar) -> str:
    if name == "Amount":
        return "decimal"
    if name == "LOAD_TIMESTAMP":
        return "timestamp"
    if name in {"DATE", "LOAD_DATE", "FIRST_DAY_MONTH", "LAST_DAY_MONTH", "PY_COMPARE_DATE"}:
        return "date"
    return "int64" if isinstance(value, int) else "string"


def totals(tables: Tables, fact: str, category: str, ytd: bool = False, **filters: Scalar) -> int:
    accounts = {row["Account"] for row in tables["account"] if row["AccountType"] == category}
    return sum(
        int(row["AmountCents"]) for row in tables[fact]
        if row["ACCOUNT"] in accounts and row["YEAR"] == YEAR
        and (not ytd or int(row["PERIOD"]) <= AS_OF.month)
        and all(row[key] == value for key, value in filters.items())
    )


def metrics(tables: Tables) -> dict[str, int | float]:
    result: dict[str, int | float] = {}
    for fact, prefix in (("ACTUALS", "Actual"), ("PLAN", "Plan"), ("FORECAST", "Forecast")):
        for ytd in ((True,) if fact == "ACTUALS" else (False, True)):
            suffix = "YTD" if ytd else "FY"
            revenue = totals(tables, fact, "Revenue", ytd)
            expense = totals(tables, fact, "Operating Expense", ytd)
            result[f"{prefix}Revenue{suffix}"] = revenue / 100
            result[f"{prefix}Opex{suffix}"] = expense / 100
            result[f"{prefix}Profit{suffix}"] = (revenue - expense) / 100
    result["RevenueVarianceYTD"] = round(result["ActualRevenueYTD"] - result["PlanRevenueYTD"], 2)
    result["ExpenseVarianceYTD"] = round(result["PlanOpexYTD"] - result["ActualOpexYTD"], 2)
    result["ProfitVarianceYTD"] = round(result["ActualProfitYTD"] - result["PlanProfitYTD"], 2)
    result["ForecastProfitVarianceFY"] = round(result["ForecastProfitFY"] - result["PlanProfitFY"], 2)
    hero = {"ACCOUNT": "500100", "PRODUCTLINE": "DIGITAL", "COSTCENTER": "300110"}
    result["CloudDigitalActualYTD"] = totals(tables, "ACTUALS", "Operating Expense", True, **hero) / 100
    result["CloudDigitalPlanYTD"] = totals(tables, "PLAN", "Operating Expense", True, **hero) / 100
    return result


def validate(tables: Tables) -> dict:
    if set(tables) != set(KEYS):
        raise ValueError(f"Expected exactly seven finance tables, received {sorted(tables)}")
    for name, key in KEYS.items():
        values = [row[key] for row in tables[name]]
        if not values or any(value == "" for value in values) or len(set(values)) != len(values):
            raise ValueError(f"{name}.{key} must be populated and unique")
    checks = 0
    for relationship in RELATIONSHIPS:
        keys = {row[relationship["toColumn"]] for row in tables[relationship["toTable"]]}
        rows = tables[relationship["fromTable"]]
        if any(row[relationship["fromColumn"]] not in keys for row in rows):
            raise ValueError(f"Orphan foreign key: {relationship}")
        checks += len(rows)
    grains: dict[str, dict[tuple, Row]] = {}
    for fact in FACTS:
        grains[fact] = {}
        for row in tables[fact]:
            if row["SCENARIO"] != fact or row["CURRENCY"] != "USD":
                raise ValueError(f"Invalid scenario or currency in {row['RecordID']}")
            if Decimal(str(row["Amount"])) * 100 != row["AmountCents"]:
                raise ValueError(f"Amount and AmountCents disagree in {row['RecordID']}")
            if fact == "ACTUALS" and date.fromisoformat(str(row["DATE"])) > AS_OF:
                raise ValueError("ACTUALS contains an unclosed period")
            grain = tuple(row[key] for key in ("ACCOUNT", "COSTCENTER", "PRODUCTLINE", "DATE"))
            if grain in grains[fact]:
                raise ValueError(f"Duplicate finance grain in {fact}: {grain}")
            grains[fact][grain] = row
        expected_months = (
            {month_date(YEAR - 1, month) for month in range(1, 13)}
            | {month_date(YEAR, month) for month in range(1, AS_OF.month + 1)}
        ) if fact == "ACTUALS" else {month_date(YEAR, month) for month in range(1, 13)}
        for account in tables["account"]:
            for center in tables["cost_center"]:
                for product in tables["product"]:
                    actual_months = {
                        grain[3] for grain in grains[fact]
                        if grain[:3] == (account["Account"], center["CostCenter"], product["ProductLine"])
                    }
                    if actual_months != expected_months:
                        raise ValueError(f"Incomplete period coverage in {fact}")
    for grain, row in grains["ACTUALS"].items():
        if row["YEAR"] == YEAR and grains["FORECAST"][grain]["AmountCents"] != row["AmountCents"]:
            raise ValueError(f"Closed-month forecast does not match ACTUALS: {grain}")
    values = metrics(tables)
    if round(values["RevenueVarianceYTD"] + values["ExpenseVarianceYTD"], 2) != round(values["ProfitVarianceYTD"], 2):
        raise ValueError("Revenue and favorable expense variances do not reconcile to profit variance")
    return {
        "status": "PASS", "synthetic": True, "asOf": AS_OF.isoformat(),
        "tableRows": {name: len(rows) for name, rows in tables.items()},
        "relationships": len(RELATIONSHIPS), "foreignKeyChecks": checks, "metrics": values,
    }


def write_data(target: Path = ROOT / "generated") -> dict:
    tables = build_data()
    report = validate(tables)
    csv_dir = target / "data"
    csv_dir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    schema = {}
    for name, rows in tables.items():
        path = csv_dir / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        schema[name] = {column: column_type(column, value) for column, value in rows[0].items()}
    for name, value in (
        ("validation.json", report), ("schema.json", schema),
        ("relationships.json", RELATIONSHIPS), ("data-sha256.json", hashes),
    ):
        (target / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(write_data(), indent=2))
