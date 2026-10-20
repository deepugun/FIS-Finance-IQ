# Fabric IQ Commercial Insurance POC — End-to-End UI & Automation Walkthrough

Build or validate the **Asterion Global Commercial** POC in Microsoft Fabric.

The deployed reference environment uses workspace **`Test`** (`fef80264-9f1f-4160-b8c8-8e3bf1de7e14`) on capacity **`nederd`** (`F16`, resource group `McapsGovernance`). When running in your own tenant, use a dedicated lab workspace such as **`Commercial_Insurance_IQ_Lab`**.

Core acceptance is the deterministic **31-table / 3,731-row** build (`5,475` foreign-key checks), the `A001` (`Meridian Specialty Chemicals`) Direct Lake semantic evidence (`$1.14B` TIV, `$7M` CAT AAL, `$7M` incurred, `2` open critical recommendations, baseline pulse `77`), and the Eventhouse pulse crossing from **77 to 83**. Ontology (`25` entity types, `30` relationship types, plus live Eventhouse time-series binding), Graph (`5` GQL investigations returning `10 / 5 / 20 / 2 / 25` rows), Data Agent, and Operations Agent extend that proof through optional branches.

Record each checkpoint only after executing it in the target workspace. Core completion is not full-lab completion.

**Audience:** facilitators, solution architects, data engineers, and underwriters  
**Presenter handbook:** see [PRESENTER_GUIDE.md](PRESENTER_GUIDE.md) for the verbatim customer talk track and live-demo runbook  
**Time:** approximately 2–3 hours for the core route; optional IQ branches add 1–2 hours  
**Data:** synthetic; do not substitute production data during the lab

Values to expect at each checkpoint (demo scale, default seed):

`31` tables · `3,731` rows · `5,475` FK checks · `20` commercial accounts · `A001` TIV **`$1.14B`** · CAT AAL **`$7M`** · incurred **`$7M`** · open critical recommendations **`2`** · baseline pulse **`77`** · live crossing **`77 -> 83`** · GQL rows **`10 / 5 / 20 / 2 / 25`**.

## Canonical Names

| Role | Canonical item name | Deployed reference ID (`Test`) |
|---|---|---|
| Workspace | `Commercial_Insurance_IQ_Lab` (or `Test`) | `fef80264-9f1f-4160-b8c8-8e3bf1de7e14` |
| Bronze Lakehouse | `CI_Bronze_Dev` | `9ca3cda1-e65a-4ddd-afae-63892c009489` |
| Silver Lakehouse | `CI_Silver_Dev` | `6852f87d-1df8-4b7c-b63e-5aa68c5d5de1` |
| Gold Lakehouse | `CI_Gold_Dev` | `726a950f-970a-487c-a75e-555a3b2cfbff` |
| Combined semantic model | `CommercialInsuranceIQModel` | `9af2fb7f-3107-444a-849f-d89800066bb8` |
| Eventhouse | `CI_Underwriting_RTI` | `d95e6f34-764f-4398-879b-28dd0686fe93` |
| KQL database | `CI_Underwriting_RTI` | `68c7a3a6-1a9a-4c40-942f-dce52d3d9205` |
| Event table | `UnderwritingEvents` | — |
| Ontology | `CommercialInsuranceOntology` | `f5d41b81-f67f-48ad-a5e6-8cea58c4382c` |
| Ontology companion graph | `CommercialInsuranceOntology_graph_<id>` | `07e16045-6a8c-4f7c-8412-d716cd04e463` |
| Standalone Graph model | `CI_Underwriting_Graph_Dev` | `7e274020-355e-43d8-9afa-7bb4c05e2313` |
| Data agent | `CommercialInsuranceDataAgent` | `e7a1a412-26eb-4195-bf5c-b05c52ab2120` |
| Operations agent | `RenewalRiskOperationsAgent` | `ce72e5ae-4509-4603-8d81-c50caf0bd11a` |

Use one workspace and these names throughout the run. If an item already exists, open and verify it rather than creating a duplicate.

> **Build order:** the sections below are ordered so you can run them **top to bottom** with no forward jumps. Notably, **Eventhouse / RTI (Module 7, Section 5)** is built **before** **Ontology (Modules 3–4, Section 6)** so the `UnderwritingEvents` time-series binding on `Account` works in place, and the **Semantic Model (Module 1, Section 3)** is built before **Data Agent (Module 8, Section 8)** so governed DAX measures are ready for natural-language Q&A.

## How to Follow This Walkthrough

### Notebook Checklist

| Walkthrough section | Notebook | Deployed display name | Default Lakehouse | Destructive behavior / checkpoint |
|---|---|---|---|---|
| 2.1 | [01_generate_synthetic_data.ipynb](notebooks/01_generate_synthetic_data.ipynb) | `CI_01_Generate_Synthetic_Data_Dev` | `CI_Bronze_Dev` | Writes under `Files/underwriting_demo`; validation status `PASS`. |
| 2.2 | [02_create_delta_tables.ipynb](notebooks/02_create_delta_tables.ipynb) | `CI_02_Create_Bronze_Delta_Tables_Dev` | `CI_Bronze_Dev` | Overwrites only `demo_` tables; `31` tables / `3,731` rows. |
| 2.3 | [03_underwriting_features.ipynb](notebooks/03_underwriting_features.ipynb) | `CI_03_Bronze_To_Silver_Features_Dev` | `CI_Silver_Dev` | Overwrites `demo_UnderwritingFeatures`; `20` account rows. |
| 2.4 | [04_renewal_risk_pulse.ipynb](notebooks/04_renewal_risk_pulse.ipynb) | `CI_04_Silver_Renewal_Risk_Pulse_Dev` | `CI_Silver_Dev` | Overwrites `demo_RiskPulse`; `A001 = 77.0`. |
| 2.5 | [05_material_change_signals.ipynb](notebooks/05_material_change_signals.ipynb) | `CI_05_Silver_Material_Change_Signals_Dev` | `CI_Silver_Dev` | Overwrites `demo_RenewalSignals`; `44` rows (`4` for `A001`). |
| 2.6 | [06_graph_nodes_edges.ipynb](notebooks/06_graph_nodes_edges.ipynb) | `CI_06_Silver_To_Gold_Graph_Inputs_Dev` | `CI_Gold_Dev` | Overwrites `demo_`, `node_` (`25`), and `edge_` (`30`) tables in Gold. |
| 2.7 | [07_live_demo_events.ipynb](notebooks/07_live_demo_events.ipynb) | `CI_07_Stage_Live_Demo_Events_Dev` | `CI_Gold_Dev` | Writes one JSONL event file for `PHASE='baseline'` or `PHASE='update'`. |

### Navigation Conventions

1. Start each procedure from **Workspaces -> YOUR_WORKSPACE_NAME** unless it names a different starting screen.
2. A path such as **More options (...) -> Settings -> General** means select each control in order.
3. **Explorer** means the left pane inside an open Fabric item.
4. When two rows share a name (for example `CI_Gold_Dev` Lakehouse vs `CI_Gold_Dev` SQL analytics endpoint, or `CI_Underwriting_RTI` Eventhouse vs `CI_Underwriting_RTI` KQL database), check the **Type** column before opening.
5. Wait for each create, save, refresh, or run operation to show a completed status before continuing.
6. Confirm the attached/default Lakehouse before running a notebook.
7. Stop Fabric Spark sessions when they are no longer needed (**Run -> Stop session**).
8. If Fabric reports **Only 20 items can be opened at one time**, close finished, saved tabs using their **X** control and retry once.
9. Preserve blocked checkpoints as `BLOCKED`; do not substitute an optional result for a core checkpoint.
10. Do not enable tenant features, upgrade capacity, or activate outbound notifications without authorization.

### Core Route and Optional Branches

**Core route:** `0 -> 1 -> 2 -> 3 -> 5 -> 10`

| Label | Scope | If unavailable |
|---|---|---|
| **CORE** | deterministic data, medallion tables, semantic evidence (`CommercialInsuranceIQModel`), Eventhouse/KQL (`CI_Underwriting_RTI`) | Mark the checkpoint blocked and stop that core path. |
| **OPTIONAL** | SQL endpoint queries and Python REST deployment automation | Continue to final proof. |
| **OPTIONAL PREVIEW** | `CommercialInsuranceOntology`, Graph (`CI_Underwriting_Graph_Dev` & companion graph), `RenewalRiskOperationsAgent` | Preserve existing items and continue. |
| **OPTIONAL AI** | `CommercialInsuranceDataAgent` and external MCP grounding | Record pending/blocked and continue. |
| **EXCLUDED** | production data, autonomous pricing/binding, unapproved notifications | Do not implement in this lab. |

## Contents

- [0. Prerequisites and Workspace](#0-prerequisites-and-workspace)
- [1. Understand the Data Before Building](#1-understand-the-data-before-building)
- [2. Build Bronze, Silver, and Gold Tables (Module 0)](#2-build-bronze-silver-and-gold-tables-module-0)
- [3. Build the Direct Lake Semantic Model (Module 1)](#3-build-the-direct-lake-semantic-model-module-1)
- [4. Validate the SQL Evidence Path (Module 2)](#4-validate-the-sql-evidence-path-module-2)
- [5. Configure Eventhouse and Prove the Pulse Crossing (Module 7)](#5-configure-eventhouse-and-prove-the-pulse-crossing-module-7)
- [6. Configure the Ontology and Time-Series Binding (Modules 3-4)](#6-configure-the-ontology-and-time-series-binding-modules-3-4)
- [7. Build and Query the Graph (Module 6)](#7-build-and-query-the-graph-module-6)
- [8. Configure the Data Agent (Module 8)](#8-configure-the-data-agent-module-8)
- [9. Configure the Operations Agent (Module 9)](#9-configure-the-operations-agent-module-9)
- [10. Final Proof](#10-final-proof)
- [11. Troubleshooting](#11-troubleshooting)

## 0. Prerequisites and Workspace

### 0.1 Required Access and Tenant Settings

- A Microsoft Fabric workspace attached to an active Fabric capacity (`F2+` required for Fabric IQ experiences; reference deployment uses `F16`).
- Permission to create and run Lakehouses, notebooks, semantic models, and Eventhouse items used by the core route.
- Fabric Admin tenant settings enabled for optional branches:
  - **Ontology item (preview)** and **Graph in Fabric (preview)** for Sections 6 and 7.
  - **Fabric Data Agent** and **Copilot and Azure OpenAI Service** for Section 8.
  - **Operations Agent (preview)** for Section 9.
- For optional REST automation (`deployment/fabric_deploy.py`, `deployment/deploy_graph.py`, `deployment/deploy_iq.py`): Python 3.10+, `requests` (`pip install -r requirements.txt`), and an authenticated Azure CLI session (`az login`).

### 0.2 Create or Select the Workspace

1. Open `https://app.fabric.microsoft.com`.
2. Create or select `Commercial_Insurance_IQ_Lab` (or `Test`, workspace ID `fef80264-9f1f-4160-b8c8-8e3bf1de7e14`).
3. Confirm in **Workspace settings -> License info** that the workspace is assigned to an active Fabric capacity.
4. Confirm that it is isolated from production data and production automation.
5. Record the workspace GUID from the browser URL if you will use deployment automation.

**Checkpoint 0.2:** correct workspace selected on active capacity; no production sources or actions attached.

### 0.3 Create the Lakehouses

Create three non-schema-enabled Lakehouses in the workspace:

1. `CI_Bronze_Dev`
2. `CI_Silver_Dev`
3. `CI_Gold_Dev`

The deployment helper expects exactly one Lakehouse with each name.

**Checkpoint 0.3:** three uniquely named Lakehouses exist (`CI_Bronze_Dev`, `CI_Silver_Dev`, `CI_Gold_Dev`).

## 1. Understand the Data Before Building

Read [the current design](Fabric-IQ-Commercial-Insurance-POC-Design.md) and the [generated data dictionary](docs/data-dictionary.md).

### 1.1 The Business Scenario — "Asterion Global Commercial"

Asterion Global Commercial underwrites multinational property programs across 20 commercial accounts and 100 insured locations. Hero account **`A001` (`Meridian Specialty Chemicals`)** is a US-domiciled chemical manufacturer (`BrokerId = B01` Northstar Risk Partners, `UnderwriterId = UW01`, `IndustryId = 325`) renewing in **28 days** (`RenewalId = R001`, expiring master policy `P00126`). Its five facilities span the US Gulf Coast (`L00101` Bayport Gulf Coast Works), Netherlands (`L00102` Rotterdam Specialty Works), Singapore (`L00103` Jurong Blending), Germany (`L00104` Ludwigshafen Distribution), and the UK (`L00105` Manchester Technical Centre).

### 1.2 Entity Types by Subject Area (25 Entities, 30 Relationships)

| Subject Area | Entities | Primary Purpose |
|---|---|---|
| **Core Account & Placement** | `Account`, `Insured`, `Broker`, `Underwriter`, `Industry`, `Country`, `Policy`, `Coverage`, `Submission` | Mastered commercial identity, broker/underwriter ownership, and policy terms |
| **Locations, Exposure & CAT** | `Location`, `Exposure`, `Asset`, `CATRisk`, `Peril` | Site-level TIV (`Property` 75% + `BI` 25%), critical equipment, and peril-specific CAT AAL |
| **Risk Engineering** | `RiskEngineeringInspection`, `EngineeringRecommendation` | Site inspections and open/closed critical recommendations (`RECL001011`, `RECL001012`) |
| **Claims & Loss Events** | `Claim`, `LossEvent`, `ClaimValuation` (table) | Paid, outstanding, and incurred loss development across matched `2025-09-14` and `2026-09-14` snapshots |
| **Multinational Program** | `MultinationalProgram`, `LocalPolicy`, `ProgramRequirement` | Master-to-local policy alignment (`LP00103` SG BI period gap; `LP00104` DE wording gap) |
| **Renewal Triage & Decision** | `Renewal`, `RenewalSignal`, `PricingScenario`, `UnderwritingDecision` | Explainable Renewal Risk Pulse (`77`), material-change flags (`4` for `A001`), illustrative scenarios, and human-governed posture |

### 1.3 Important Table Grains

| Table | Grain | Rows |
|---|---|---:|
| `Accounts` | one commercial account | 20 |
| `Locations` | one insured location (5 per account) | 100 |
| `Policies` | one master policy year (2025 and 2026 per account) | 40 |
| `PolicyValuations` | one policy at one valuation snapshot (`2025-09-14` / `2026-09-14`) | 60 |
| `Exposures` | one location + exposure type (`Property`/`BI`) + snapshot | 400 |
| `CATRisk` | one location + peril (`PER1`/`PER2`) + snapshot | 400 |
| `Claims` | one claim (4 per account) | 80 |
| `ClaimValuations` | one claim at one valuation snapshot | 160 |
| `EngineeringRecommendations` | one risk engineering recommendation | 99 |
| `LocalPolicies` / `ProgramRequirements` | one local policy / requirement per location | 100 / 100 |
| `UnderwritingFeatures` | one account at current snapshot (`2026-09-14`) | 20 |
| `RiskPulse` | one account Renewal Risk Pulse breakdown | 20 |
| `RenewalSignals` | one material-change signal (`Value >= Threshold`) | 44 |
| `UnderwritingEvents` | one baseline or historical RTI event | 31 |

Currency fields ending in `USDCents` are **integer cents**, not dollars.

**Checkpoint 1:** reviewer can explain why `A001` is evidence for prioritization, not an automated underwriting recommendation.

## 2. Build Bronze, Silver, and Gold Tables (Module 0)

You can execute this module either **in the Fabric UI** (importing and running the seven notebooks in order) or via **automated REST deployment**:

```powershell
python .\deployment\fabric_deploy.py --workspace-id <WORKSPACE_ID> --workspace-name <WORKSPACE_NAME> --phase all
```

| Step | Notebook | Default Lakehouse | Destructive behavior / checkpoint |
|---|---|---|---|
| 2.1 | `01_generate_synthetic_data.ipynb` | `CI_Bronze_Dev` | Writes under `Files/underwriting_demo`; validation status `PASS`. |
| 2.2 | `02_create_delta_tables.ipynb` | `CI_Bronze_Dev` | Overwrites only `demo_` tables; `31` tables / `3,731` rows with audit columns. |
| 2.3 | `03_underwriting_features.ipynb` | `CI_Silver_Dev` | Overwrites `demo_UnderwritingFeatures`; `20` account rows. |
| 2.4 | `04_renewal_risk_pulse.ipynb` | `CI_Silver_Dev` | Overwrites `demo_RiskPulse`; `A001 = 77.0` (`20+16+7+17+8+6+3`). |
| 2.5 | `05_material_change_signals.ipynb` | `CI_Silver_Dev` | Overwrites `demo_RenewalSignals`; `44` rows (`4` high-materiality signals for `A001`). |
| 2.6 | `06_graph_nodes_edges.ipynb` | `CI_Gold_Dev` | Copies `31` `demo_` tables and materializes `25` `node_` and `30` `edge_` tables in Gold. |
| 2.7 | `07_live_demo_events.ipynb` | `CI_Gold_Dev` | Writes one JSONL event file (`<RUN_ID>-<PHASE>.jsonl`) under `Files/underwriting_demo`. |

For notebook 7, use a unique `RUN_ID`. Run `PHASE='baseline'` first and retain the same `RUN_ID` when later running `PHASE='update'`.

**Checkpoint 2:** the generated report matches [`validation/data-validation.json`](validation/data-validation.json):

- status `PASS`
- `31` tables
- `3,731` total rows
- `5,475` foreign-key checks
- transition `[77.0, 83.0]`

## 3. Build the Direct Lake Semantic Model (Module 1)

### 3.1 Deploy or Configure `CommercialInsuranceIQModel`

The repository includes a complete 27-table Direct Lake TMDL definition under [`semantic/tmdl/`](semantic/tmdl) with 25 single-direction relationships and 30 saved DAX measures.

- **Automated path:** run [`deployment/deploy_iq.py`](deployment/deploy_iq.py), which deploys all 32 TMDL parts to `CommercialInsuranceIQModel`, triggers a full Direct Lake refresh, and executes the verification DAX query.
- **UI path:**
  1. Open `CI_Gold_Dev` and select **New semantic model**, or create `CommercialInsuranceIQModel` in the workspace.
  2. Include the 27 curated `demo_*` tables defined in [`semantic/tmdl/definition/model.tmdl`](semantic/tmdl/definition/model.tmdl).
  3. Configure the 25 single-direction relationships in [`semantic/tmdl/definition/relationships.tmdl`](semantic/tmdl/definition/relationships.tmdl).
  4. Add the saved measures from [`semantic/tmdl/definition/tables/Accounts.tmdl`](semantic/tmdl/definition/tables/Accounts.tmdl), [`RiskPulse.tmdl`](semantic/tmdl/definition/tables/RiskPulse.tmdl), and [`UnderwritingFeatures.tmdl`](semantic/tmdl/definition/tables/UnderwritingFeatures.tmdl) (also listed in [`semantic/measures.dax`](semantic/measures.dax)).
  5. Run a **Full refresh** so Direct Lake builds relationship indexes.

### 3.2 Verify the Semantic Measures

Run [`semantic/measures.dax`](semantic/measures.dax) or execute the saved-measure query directly (without `DEFINE`):

```dax
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
```

**Checkpoint 3:** for `A001`, the semantic engine returns:

- `Total Insured Value` = **`$1,140,000,000`** (`TIV YoY = 14.00%`)
- `Modeled CAT Loss` = **`$7,000,000`** (`CAT Exposure Change = 40.00%`)
- `Incurred Loss` = **`$7,000,000`** (`Paid Loss = $3,700,000`, `Outstanding Loss = $3,300,000`)
- `Written Premium` = **`$34,981,132`**, `Earned Premium` = **`$33,600,310`**, `Loss Ratio` = **`20.83%`**
- `Critical Recommendations` = **`2`** (`Open Recommendations = 3`, `Engineering Completion Rate = 25.00%`)
- `High Materiality Signals` = **`4`**
- `Average Risk Pulse` = **`77.00`**

## 4. Validate the SQL Evidence Path (Module 2)

Optional but recommended:

1. Open the **SQL analytics endpoint** for `CI_Gold_Dev` (or `CI_Bronze_Dev`).
2. Run the six queries in [`sql/03_underwriting_queries.sql`](sql/03_underwriting_queries.sql).
3. Confirm that `@AsOf` remains `2026-09-14` and `@AccountId` remains `A001` for the reference proof.

**Checkpoint 4:** the account summary, claims development, CAT-zone concentration (`US_GULF` = `$729.6M` for `A001`), open critical engineering recommendations (`RECL001011`, `RECL001012`), multinational program gaps (`LP00103`, `LP00104`), and pricing scenarios (`SC1`, `SC2`, `SC3`) reconcile to the semantic model.

## 5. Configure Eventhouse and Prove the Pulse Crossing (Module 7)

### 5.1 Create the Eventhouse

Create `CI_Underwriting_RTI`, open its KQL database (`CI_Underwriting_RTI`), and run [`kql/01_eventhouse_setup.kql`](kql/01_eventhouse_setup.kql).

This creates:

- `UnderwritingEvents`
- `DedupedEvents()` (deduplicates by `EventId`, filters out future-dated events, recomputes `ExpectedPulse`, and requires `abs(Pulse - ExpectedPulse) <= 0.05`)
- `LatestPulse()` (projects `EvaluationKey = strcat(AccountId, ':', RunId, ':', tostring(Sequence))` and returns the latest valid event per `AccountId` and `RunId`)

### 5.2 Ingest the Baseline and Update

1. Run notebook 7 with a unique `RUN_ID` (for example `deployed-001` or `rehearsal-001`) and `PHASE='baseline'`.
2. Ingest the baseline JSONL row into `UnderwritingEvents` (via **Get data -> Local file** or KQL `.ingest inline`).
3. Confirm one row with `Pulse = 77.0`.
4. Run notebook 7 with the **same** `RUN_ID` and `PHASE='update'`.
5. Ingest the second JSONL row (`EventType = 'CATAndReserveUpdated'`, `CAT = 0.96`, `Claims = 0.90`, `Pulse = 83.0`).
6. Do not repeatedly upload the same phase as a substitute for validation.

### 5.3 Run the Monitoring Queries

Run [`kql/02_monitoring_queries.kql`](kql/02_monitoring_queries.kql) (using `deployed-001` for the pre-seeded reference run or your own `RUN_ID`):

```kql
DedupedEvents()
| where RunId == 'deployed-001'
| sort by AccountId asc, EventTime asc, Sequence asc
| serialize
| extend PreviousAccount = prev(AccountId), PreviousPulse = prev(Pulse)
| where AccountId == PreviousAccount and PreviousPulse < 80.0 and Pulse >= 80.0
| project EventId, AccountId, PreviousPulse, Pulse, EventTime, EvidenceRef
```

**Checkpoint 5:** the crossing query returns **1 row** for `A001` with `PreviousPulse = 77` and `Pulse = 83` (`EvidenceRef = 'CAT Bayport AAL +400000 USD; CL00101 incurred +250000 USD; synthetic live overlay'`). `LatestPulse()` returns the `83` update as the latest state for that account and run.

## 6. Configure the Ontology and Time-Series Binding (Modules 3-4)

**Optional preview**

### 6.1 Create `CommercialInsuranceOntology` and Bind Static Entities & Relationships

- **Automated path:** run [`deployment/deploy_iq.py`](deployment/deploy_iq.py), which deploys all 25 entity types, 25 Lakehouse data bindings (`CI_Gold_Dev`), 30 relationship types, 30 relationship contextualizations, and the `UnderwritingEvents` Eventhouse time-series binding on `Account` (`113` total definition parts), and normalizes the companion graph data source paths.
- **UI path:**
  1. Create `CommercialInsuranceOntology` in the workspace.
  2. Bind entity types to the managed `node_*` tables in `CI_Gold_Dev` described in [`graph/mapping-manifest.json`](graph/mapping-manifest.json).
  3. Bind the 30 relationship types to the `edge_*` mapping tables in `CI_Gold_Dev` using `SourceId` and `TargetId`.
  4. Select **Manage graph -> Materialize** to project the static Lakehouse graph (`CommercialInsuranceOntology_graph_<id>`) **before** adding multi-source bindings.

### 6.2 Add the Eventhouse Time-Series Binding on `Account`

Bind `UnderwritingEvents` from `CI_Underwriting_RTI` as a `TimeSeries` data binding on `Account`:

- Join key: `AccountId -> AccountId`
- Timestamp column: `EventTime`
- Time-series properties: `EventTime` (`DateTime`), `Pulse` (`Double`), `EventType` (`String`), `RunId` (`String`), `EvidenceRef` (`String`)

Do not disable production security or change production Delta settings to satisfy a preview restriction. Use only the dedicated lab tables.

**Checkpoint 6:** `CommercialInsuranceOntology` contains 25 entity types, 30 relationship types, and the `Account` time-series binding to `CI_Underwriting_RTI.UnderwritingEvents`.

## 7. Build and Query the Graph (Module 6)

**Optional preview**

You can query either the standalone Graph model (`CI_Underwriting_Graph_Dev`) deployed by [`deployment/deploy_graph.py`](deployment/deploy_graph.py) or the Ontology companion graph (`CommercialInsuranceOntology_graph_<id>`):

```powershell
python .\deployment\deploy_graph.py --workspace-id fef80264-9f1f-4160-b8c8-8e3bf1de7e14 --gold-id 726a950f-970a-487c-a75e-555a3b2cfbff --refresh --verify
```

In the Fabric UI, open the Graph model, select **Query -> Query now**, switch **Query builder -> Code editor**, and run the five GQL investigations in [`gql/underwriting.gql`](gql/underwriting.gql) one at a time:

| # | Investigation | Expected Row Count | Key Evidence Returned |
|---|---|---:|---|
| 7.1 | High CAT (`Score >= 80`) + Open Critical Engineering Recommendations | **10 rows** | `Meridian Specialty Chemicals` (`Bayport Gulf Coast Works`) -> `RECL001011` (`Firewater pump redundancy`), `RECL001012` (`Flood barrier verification`) |
| 7.2 | `US_GULF` Broker Concentration (`GROUP BY brokerName`) | **5 rows** | Ranked #1: `Northstar Risk Partners` (`4` accounts, `143,560,000,000` cents = `$1.4356B`) |
| 7.3 | Multi-Location Same-Peril Claims (`first.LocationId < second.LocationId`) | **20 rows** | Repeat `Machinery breakdown` (`PER4`) claims across facility pairs (`CL00102` & `CL00104` for `A001`) |
| 7.4 | Multinational Program Local Policy Gaps (`localPolicy:LocalPolicy`) | **2 rows** | `Meridian Specialty Chemicals`: `SG` (`LP00103`, BI indemnity `12` vs `18` required months) and `DE` (`LP00104`, `Wording outstanding`) |
| 7.5 | Cross-Account `US_GULF` Peril Accumulation (`PolicyYear = 2026`) | **25 rows** | Shared `Windstorm` (`PER1`) and `Flood` (`PER2`) exposure across 2026 policies (`P00126`, `P00626`, `P01626`, `P01826`, etc.) |

> **GQL identifier note:** `LOCAL` is a reserved keyword in ISO GQL. Query 7.4 uses `localPolicy:LocalPolicy` (or backticked `` `local` ``) rather than unquoted `local`.

**Checkpoint 7:** all five GQL queries execute with status `00000` and return `10`, `5`, `20`, `2`, and `25` rows respectively on both `CI_Underwriting_Graph_Dev` and `CommercialInsuranceOntology_graph_<id>`.

## 8. Configure the Data Agent (Module 8)

**Optional AI**

1. Create or open `CommercialInsuranceDataAgent` (deployed and published automatically by [`deployment/deploy_iq.py`](deployment/deploy_iq.py)).
2. Ground it in `CommercialInsuranceIQModel` (for governed DAX measures) and `CI_Gold_Dev` (`demo_*` tables for row-level evidence keys).
3. Add these governed instructions in **Agent instructions**:

```text
Use CommercialInsuranceIQModel and CI_Gold_Dev for commercial insurance underwriting questions.
Use AccountId (for example A001 for Meridian Specialty Chemicals) as the mastered account identity.
Keep monetary source values in integer cents (*USDCents) and convert to USD by dividing by 100 or referencing saved semantic measures.
Default snapshot date is 2026-09-14 and prior comparison snapshot date is 2025-09-14 unless another date is explicitly requested.
For A001 KPIs, reference saved measures [Total Insured Value], [Modeled CAT Loss], [Incurred Loss], [Paid Loss], [Outstanding Loss], [Written Premium], [Earned Premium], [Loss Ratio], [Critical Recommendations], [Open Recommendations], [Engineering Completion Rate], [High Materiality Signals], [Average Risk Pulse], [TIV YoY], and [CAT Exposure Change].
Always include evidence IDs (AccountId, LocationId, PolicyId, ClaimId, RecommendationId, LocalPolicyId, RequirementId, SignalId) and state that results support human underwriting review rather than automated pricing, binding, or declination.
```

4. Test the four core underwriting prompts:
   - *What changed for account A001 before renewal?* -> TIV `$1.00B -> $1.14B` (`+14%`), CAT AAL `$5.0M -> $7.0M` (`+40%`), Incurred `$5.0M -> $7.0M` (`+40%`), `28` days to renewal, `2` open critical recommendations, baseline pulse `77`.
   - *What is A001's current TIV, CAT AAL, and incurred loss?* -> `$1,140,000,000` TIV, `$7,000,000` CAT AAL, `$7,000,000` incurred loss (`$3.7M` paid, `$3.3M` outstanding).
   - *Which critical engineering recommendations remain open for A001?* -> `RECL001011` (`Firewater pump redundancy`, weight `35`) and `RECL001012` (`Flood barrier verification`, weight `30`) at location `L00101` (`Bayport Gulf Coast Works`).
   - *Which local-program requirements are not aligned for A001?* -> `REQ00103` / `LP00103` (`SG`, BI indemnity `12` months vs `18` required) and `REQ00104` / `LP00104` (`DE`, `Wording outstanding`).
5. Inspect the executed DAX/SQL query, filters, and raw result for every answer.

**Checkpoint 8:** numeric answers and evidence IDs reconcile to the semantic, SQL, and GQL proofs. Fluent text without a reconciling query is not a pass.

## 9. Configure the Operations Agent (Module 9)

### 9.1 `RenewalRiskOperationsAgent` in Fabric

**Optional preview**

1. Create or open `RenewalRiskOperationsAgent` (created and configured with `shouldRun = false` by [`deployment/deploy_iq.py`](deployment/deploy_iq.py)).
2. Connect `CI_Underwriting_RTI` (`KustoDatabase`) as the single knowledge source.
3. Configure instructions to monitor `LatestPulse()` using `EvaluationKey` (`AccountId:RunId:Sequence`) for fresh deduplicated events where `Pulse >= 80.0` and `DaysToRenewal <= 45`.
4. Keep the agent **stopped (`shouldRun = false`, state `Inactive`)** until identity, recipients, cadence, deduplication, and rollback are approved by an authorized reviewer.

**Checkpoint 9:** `RenewalRiskOperationsAgent` is configured against `CI_Underwriting_RTI` and remains safely stopped (`shouldRun = false`); baseline `77` does not cross `80`, while the `83` update matches once.

### 9.2 External Agent Grounding (Foundry and Copilot Studio - Module 10)

**Optional integration**

Because `CommercialInsuranceDataAgent` is published in the workspace, external assistants in **Microsoft Foundry** (`https://ai.azure.com` -> **Build -> New agent -> Tools -> Add -> Fabric IQ (OneLake Catalog)**) or **Copilot Studio** can attach `CommercialInsuranceDataAgent` over MCP in the same tenant and reuse the same governed semantic and Lakehouse answers without duplicating business logic.

## 10. Final Proof

| Proof | Expected | Verified in `Test` (`2026-10-20`) | Status |
|---|---:|---:|---|
| Generated tables | 31 | 31 | `PASS` (Spark + Local) |
| Generated rows | 3,731 | 3,731 | `PASS` (Spark + Local) |
| Referential checks | 5,475 | 5,475 | `PASS` (Spark + Local) |
| Ordered notebooks executed | 7 / 7 | 7 Completed, 0 Failed | `PASS` (Fabric Spark) |
| `CommercialInsuranceIQModel` refresh | Completed (27 tables, 25 rels, 30 measures) | Completed | `PASS` (Direct Lake DAX) |
| `A001` baseline pulse | 77 | 77.0 | `PASS` (Spark + DAX + KQL) |
| `A001` updated pulse | 83 | 83.0 (1 crossing row, `deployed-001`) | `PASS` (Eventhouse KQL) |
| `A001` TIV | $1.14B | $1,140,000,000 (`+14.0% YoY`) | `PASS` (Direct Lake DAX) |
| `A001` CAT AAL | $7M | $7,000,000 (`+40.0% YoY`) | `PASS` (Direct Lake DAX) |
| `A001` incurred | $7M | $7,000,000 (`$3.7M` paid / `$3.3M` reserve) | `PASS` (Direct Lake DAX) |
| `A001` open critical recommendations | 2 | 2 (`RECL001011`, `RECL001012`) | `PASS` (DAX + SQL + GQL) |
| `CommercialInsuranceOntology` | 25 entities, 30 rels + RTI time-series | Deployed (`113` parts) | `PASS` (Fabric Ontology) |
| Graph refresh & 5 GQL queries (`CI_Underwriting_Graph_Dev` & companion graph) | `10 / 5 / 20 / 2 / 25` rows | `10 / 5 / 20 / 2 / 25` rows (`status = 00000`) | `PASS` (Fabric GQL) |
| `CommercialInsuranceDataAgent` | Grounded in Model + Gold LH + 4 few-shots | Published | `PASS` (Fabric Data Agent) |
| `RenewalRiskOperationsAgent` | Configured against `CI_Underwriting_RTI`, stopped | `shouldRun = false` (`Inactive`) | `PASS` (Governed Setup) |

Full deployment metadata and item GUIDs are recorded in [`validation/fabric-deployment.json`](validation/fabric-deployment.json).

## 11. Troubleshooting

### A notebook is attached to the wrong Lakehouse

Stop before running. Change the default Lakehouse (`CI_Bronze_Dev` for 01–02, `CI_Silver_Dev` for 03–05, `CI_Gold_Dev` for 06–07), restart the session, and confirm the target in the notebook metadata.

### A demo table already exists

The notebooks intentionally overwrite only documented `demo_`, `node_`, or `edge_` tables. If the table is not a disposable lab table, use a new Lakehouse.

### Ontology companion graph fails refresh with `PathNotFound` on `/Tables/dbo/`

Non-schema Lakehouses store tables under `/Tables/<table_name>` rather than `/Tables/dbo/<table_name>`. Run [`deployment/deploy_iq.py`](deployment/deploy_iq.py), which automatically normalizes `/Tables/dbo/` to `/Tables/` in the companion graph's `dataSources.json`.

### Standalone Graph refresh cancels immediately

Confirm that `definition.parts` uses `.json` filenames (`dataSources.json`, `graphDefinition.json`, `graphType.json`, `stylingConfiguration.json`) and `"format": "json"`. [`deployment/deploy_graph.py`](deployment/deploy_graph.py) sets these automatically.

### GQL query fails with syntax error `42000` on `local`

`LOCAL` is a reserved keyword in ISO GQL. Use `localPolicy:LocalPolicy` (as updated in [`gql/underwriting.gql`](gql/underwriting.gql)) or enclose the identifier in backticks (`` `local` ``).

### The KQL crossing query returns zero rows

Confirm both phases use the same `RUN_ID`, baseline was ingested before update, event times are not in the future, and both rows pass `DedupedEvents()`.

### The KQL crossing query returns duplicates

Use a new `RUN_ID`, inspect duplicate uploads by `EventId`, and verify `DedupedEvents()` before rerunning. Do not repeatedly send events to force a desired result.

### The Data Agent answer differs from the checkpoint

Inspect its executed query, as-of filter (`2026-09-14`), source, and measure. Reconcile against the saved DAX/SQL proof before changing instructions.

### REST deployment fails

Confirm Azure CLI authentication (`az account show`), active capacity state, workspace permission, canonical Lakehouse names, and the exact workspace ID. The helpers discover Lakehouse IDs by name and never store a token.
