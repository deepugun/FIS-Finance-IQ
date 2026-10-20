from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insurance_demo import build_data, validate  # noqa: E402


EXPECTED_NOTEBOOKS = [
    "01_generate_synthetic_data.ipynb",
    "02_create_delta_tables.ipynb",
    "03_underwriting_features.ipynb",
    "04_renewal_risk_pulse.ipynb",
    "05_material_change_signals.ipynb",
    "06_graph_nodes_edges.ipynb",
    "07_live_demo_events.ipynb",
]
EXPECTED_TABLES = 31
EXPECTED_ROWS = 3731
EXPECTED_FOREIGN_KEY_CHECKS = 5475
EXPECTED_TRANSITION = [77.0, 83.0]


def validate_data_contract() -> None:
    tables = build_data()
    report = validate(tables)
    assert len(tables) == EXPECTED_TABLES
    assert sum(len(rows) for rows in tables.values()) == EXPECTED_ROWS
    assert report["foreign_key_checks"] == EXPECTED_FOREIGN_KEY_CHECKS
    assert report["transition"] == EXPECTED_TRANSITION


def validate_csv_hashes() -> None:
    expected = json.loads(
        (ROOT / "validation" / "data-sha256.json").read_text(encoding="utf-8")
    )
    actual = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / "data" / "csv").glob("*.csv"))
    }
    assert actual == expected, "Generated CSV files differ from data-sha256.json"


def validate_notebooks() -> None:
    actual = sorted(path.name for path in (ROOT / "notebooks").glob("*.ipynb"))
    assert actual == EXPECTED_NOTEBOOKS
    for name in EXPECTED_NOTEBOOKS:
        notebook = json.loads((ROOT / "notebooks" / name).read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                ast.parse("".join(cell.get("source", [])), filename=name)


def validate_python_syntax() -> None:
    for directory in ("src", "deployment", "validation"):
        for path in sorted((ROOT / directory).glob("*.py")):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_markdown_links() -> None:
    pattern = re.compile(r"\[[^\]]+\]\((?!https?://|#|mailto:)([^)]+)\)")
    failures: list[str] = []
    for path in (
        ROOT / "README.md",
        ROOT / "LAB.md",
        ROOT / "PRESENTER_GUIDE.md",
        ROOT / "Fabric-IQ-Commercial-Insurance-POC-Design.md",
    ):
        for target in pattern.findall(path.read_text(encoding="utf-8")):
            clean_target = target.split("#", 1)[0].strip("<>")
            if clean_target and not (path.parent / clean_target).exists():
                failures.append(f"{path.name}: {target}")
    assert not failures, "Broken local Markdown links:\n" + "\n".join(failures)


def validate_semantic_and_graph_artifacts() -> None:
    tmdl_tables = list((ROOT / "semantic" / "tmdl" / "definition" / "tables").glob("*.tmdl"))
    assert len(tmdl_tables) == 27, f"Expected 27 TMDL tables, found {len(tmdl_tables)}"
    manifest = json.loads((ROOT / "graph" / "mapping-manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["nodes"]) == 25
    assert len(manifest["edges"]) == 30
    gql_text = (ROOT / "gql" / "underwriting.gql").read_text(encoding="utf-8").strip()
    queries = [q.strip() for q in gql_text.split("\n\n") if q.strip()]
    assert len(queries) == 5
    assert "localPolicy:LocalPolicy" in gql_text
    assert (ROOT / "docs" / "customer-demo" / "Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx").exists()
    assert (ROOT / "Presentation.pptx").exists()


def main() -> None:
    validate_data_contract()
    validate_csv_hashes()
    validate_notebooks()
    validate_python_syntax()
    validate_markdown_links()
    validate_semantic_and_graph_artifacts()
    print(
        json.dumps(
            {
                "status": "PASS",
                "tables": EXPECTED_TABLES,
                "rows": EXPECTED_ROWS,
                "foreign_key_checks": EXPECTED_FOREIGN_KEY_CHECKS,
                "transition": EXPECTED_TRANSITION,
                "notebooks": len(EXPECTED_NOTEBOOKS),
                "semantic_tmdl_tables": 27,
                "graph_node_types": 25,
                "graph_edge_types": 30,
                "gql_queries": 5,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
