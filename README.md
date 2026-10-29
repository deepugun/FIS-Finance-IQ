# FIS Finance IQ

A standalone, synthetic FP&A demo for Microsoft Fabric IQ. It brings ACTUALS,
FORECAST and PLAN together through shared account, cost-center, date and product
dimensions for governed finance analysis.

**All figures, account codes, product names and cost centers are fictional.**
They are not FIS customer data, published results or official forecasts.

## Start here

- [Finance runbook, business story and acceptance values](fis_demo/README.md)
- [Generated finance datasets](fis_demo/generated/data)
- [Seven-table schema](fis_demo/generated/schema.json) and
  [twelve relationships](fis_demo/generated/relationships.json)
- [Finance report PDF](fis_demo/generated/FIS-Finance-IQ-Demo.pdf)
- [Historical Fabric deployment receipt](fis_demo/deployment.json)

## Finance model

| Tables | Purpose |
|---|---|
| `ACTUALS` | January 2025 through September 2026 closed-period actuals |
| `FORECAST` | September 2026 full-year outlook, including closed-month actuals |
| `PLAN` | Full-year 2026 plan |
| `account` | Account classification and hierarchy |
| `cost_center` | Cost-center hierarchy and attributes |
| `DIM_DATE` | Daily calendar with all 28 screenshot columns |
| `product` | Product-line hierarchy and attributes |

Each fact has four active, many-to-one relationships:

- `ACCOUNT -> account.Account`
- `COSTCENTER -> cost_center.CostCenter`
- `DATE -> DIM_DATE.DATE`
- `PRODUCTLINE -> product.ProductLine`

The same seven entities and twelve relationships are represented in the Direct
Lake semantic model, ontology and graph. The reproducible dataset has **13,710
rows** and **51,840 foreign-key checks**.

Screenshots establish the table and column shapes, not source values or business
definitions. Inferred calendar conventions and synthetic helper columns are
documented in the [model contract](fis_demo/README.md#model-contract).

## Repository layout

```text
FIS-Finance-IQ/
|-- README.md
|-- requirements.txt
`-- fis_demo/
    |-- README.md
    |-- data.py
    |-- artifacts.py
    |-- fabric.py
    |-- deploy.py
    |-- deployment.json
    |-- test_demo.py
    |-- test_deploy.py
    `-- generated/
        |-- data/
        |-- semantic/
        |-- ontology/
        |-- graph/
        |-- report/
        |-- agent/
        |-- FIS_01_Finance_Medallion.ipynb
        `-- FIS_02_Prepare_Ontology_Date_Keys.ipynb
```

## Local reproduction

Use Python 3.11 or later from the repository root. Deployment and mocked
deployment tests require the dependency in [requirements.txt](requirements.txt).

```powershell
python -m pip install -r .\requirements.txt
python -m fis_demo.artifacts
python -m unittest discover -s .\fis_demo -p "test_*.py" -v
python -m fis_demo.deploy --help
```

The generator runs locally without Fabric access. Its default artifact IDs are
placeholders; supply `--workspace`, `--bronze`, `--silver`, `--gold` and `--model`
when generating artifacts with environment-specific bindings. Unit tests do not
contact Fabric.

## Deployment and boundaries

Follow the [deployment runbook](fis_demo/README.md#deploy-or-rerun-safely) before
running [the deployment helper](fis_demo/deploy.py). It requires an authenticated
Azure CLI session and checks the dedicated FIS workspace identity and single-user
role assignment before making changes.

Code generation, tests and Git pushes do **not** deploy or refresh live Fabric
items. Historical deployment evidence is not proof that the latest local schema
has been deployed. No capacity changes, schedules, notifications or source-system
writes are performed by local reproduction.
