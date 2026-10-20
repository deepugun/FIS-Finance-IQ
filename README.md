# Fabric IQ Commercial Insurance POC

A synthetic commercial-insurance lab for Microsoft Fabric IQ: governed source data,
medallion Lakehouses, a Direct Lake semantic model, renewal-risk signals, Eventhouse
monitoring, ontology, Graph, and agent-ready business context.

The fictional carrier is **Asterion Global Commercial**. All data is synthetic. The
sample supports human underwriting review; it is not an actuarial indication, legal
opinion, binder, or autonomous underwriting decision.

## Start Here

- **Hands-on execution:** follow **[the lab instructions](LAB.md)** for prerequisites, canonical item names, ordered execution, checkpoints, optional preview branches, and troubleshooting.
- **Customer presentation & live demo script:** follow **[the detailed presenter guide](PRESENTER_GUIDE.md)** and open **[the 15-slide customer deck](docs/customer-demo/Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx)** (also synced to **[Presentation.pptx](Presentation.pptx)**).
- **Architecture & scope:** read **[the current lab design](Fabric-IQ-Commercial-Insurance-POC-Design.md)**.

```text
fabric-iq-commercial-insurance/
|-- README.md
|-- LAB.md                                       # end-to-end UI + automation walkthrough
|-- PRESENTER_GUIDE.md                           # verbatim talk tracks, click-by-click demo runbook, Q&A
|-- Fabric-IQ-Commercial-Insurance-POC-Design.md # use case, architecture, roadmap, and governance
|-- Presentation.pptx                            # synced 15-slide customer-facing PowerPoint deck
|-- notebooks/                                   # seven ordered Fabric notebooks
|-- data/                                        # generated synthetic CSV/JSON data and schema
|-- semantic/                                    # 27-table Direct Lake TMDL and 30 saved DAX measures
|-- kql/                                         # Eventhouse setup and monitoring queries
|-- gql/                                         # five ISO GQL graph investigation queries
|-- graph/                                       # generated 25 node / 30 edge files and manifest
|-- deployment/                                  # Fabric REST deployment & verification helpers
|-- src/                                         # deterministic data and artifact generators
|-- validation/                                  # validation suite, hashes, and deployment receipt
`-- docs/                                        # data dictionary and deck generator (generate-deck.js)
```

## Notebook Order

| # | Notebook | Layer | Purpose |
|---|---|---|---|
| 1 | [Generate synthetic data](notebooks/01_generate_synthetic_data.ipynb) | Bronze | Create the deterministic portfolio under `Files/underwriting_demo`. |
| 2 | [Create Delta tables](notebooks/02_create_delta_tables.ipynb) | Bronze | Build the 31 managed `demo_` source tables. |
| 3 | [Derive underwriting features](notebooks/03_underwriting_features.ipynb) | Silver | Recompute explainable, account-grain features. |
| 4 | [Calculate Renewal Risk Pulse](notebooks/04_renewal_risk_pulse.ipynb) | Silver | Apply the transparent weighted score. |
| 5 | [Identify material changes](notebooks/05_material_change_signals.ipynb) | Silver | Produce evidence-linked triage signals. |
| 6 | [Materialize Graph inputs](notebooks/06_graph_nodes_edges.ipynb) | Gold | Build graph node and edge tables. |
| 7 | [Stage live demo events](notebooks/07_live_demo_events.ipynb) | Gold/RTI | Create the controlled 77-to-83 pulse crossing. |

Run the notebooks in order. Notebooks 2 through 6 overwrite only their documented
demo tables. Notebook 7 writes a JSONL event file; it does not claim automatic
Eventhouse ingestion.

## Reference Checkpoints

The default seed must produce:

- **31 tables** and **3,731 rows** across Bronze, Silver, and Gold
- **5,475** foreign-key and financial reconciliation checks
- **27 Direct Lake tables**, **25 relationships**, and **30 saved DAX measures** in `CommercialInsuranceIQModel`
- hero account `A001` (`Meridian Specialty Chemicals`) with **$1.14B TIV** (`+14% YoY`), **$7M CAT AAL** (`+40% YoY`), **$7M incurred** (`$3.7M` paid / `$3.3M` reserve), and **2 open critical engineering recommendations** (`RECL001011`, `RECL001012`)
- transparent Renewal Risk Pulse **77** (`20 + 16 + 7 + 17 + 8 + 6 + 3`)
- staged Eventhouse transition **77 -> 83** (`1` crossing row in `DedupedEvents()`)
- **25 entity types**, **30 relationship types**, and an Eventhouse `UnderwritingEvents` time-series binding in `CommercialInsuranceOntology`
- **5 ISO GQL investigations** returning **10 / 5 / 20 / 2 / 25** rows (`status = 00000`) on `CI_Underwriting_Graph_Dev` and the Ontology companion graph
- published `CommercialInsuranceDataAgent` (with `4` validated few-shots) and governed `RenewalRiskOperationsAgent` (`shouldRun = false`)

Reference values are checkpoints, not proof that a Fabric tenant has been validated.
Spark, DAX, KQL, GQL, permissions, preview features, and agent responses require
execution in the target workspace.

## Before Running

- Use a disposable or dedicated lab workspace.
- Review every overwrite and replacement step in [LAB.md](LAB.md).
- Keep monetary source values as integer USD cents; convert explicitly in measures.
- Replace environment identifiers with your own values. Do not commit tokens or secrets.
- Ontology, Graph, Operations Agent, and external grounding capabilities may be preview
  or unavailable in a given tenant/capacity. A blocked optional branch is not a failed
  core checkpoint.
- Do not enable tenant features, upgrade capacity, or send notifications without
  authorization.

## Design Reference

[Current lab design](Fabric-IQ-Commercial-Insurance-POC-Design.md) explains the
business problem, architecture, feature scope, evidence boundaries, and acceptance
limits. Use [LAB.md](LAB.md) for execution.

## Local Reproducibility

The core generator uses only the Python standard library:

```powershell
python .\src\insurance_demo.py
python .\src\build_artifacts.py
python .\validation\validate_repository.py
```

The optional deployment helper also requires the packages in
[`requirements.txt`](requirements.txt) and an authenticated Azure CLI session.

The latest environment-specific deployment result is recorded in
[`validation/fabric-deployment.json`](validation/fabric-deployment.json).
