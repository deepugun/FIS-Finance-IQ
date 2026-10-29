# FIS Finance IQ - synthetic FP&A demo

This standalone FIS-style finance demo uses **fictional
financial technology products and synthetic financial values**, not FIS customer
data, official segment reporting, forecasts or published financial results.

## Scope and isolation

- One dedicated **FIS-Finance-IQ** Fabric workspace on the approved existing capacity.
- Only the authenticated user is assigned a workspace role, as Admin. No other
  users, groups, applications or service principals are added.
- Workspace membership is not a way to exclude tenant administrators from their
  administrative powers. Tenant governance and retention policies still apply.
- Code is maintained in [FIS-Finance-IQ](https://github.com/deepugun/FIS-Finance-IQ).
  Pushing code does not deploy Fabric items.
- No capacity resizing, recurring schedules, notifications, source-system writes,
  accounting entries or autonomous financial decisions.

The latest live state, item IDs, query results and access verification are persisted
in [the deployment receipt](deployment.json) once deployment has started. Do not
treat a generated artifact or a successful local test as proof of live deployment.
The receipt records the workspace description-marker check rather than retaining
the free-text description. This repository cleanup does not change live workspace
metadata or the historical live-check timestamp.

## Open the deployed demo

- [Private FIS-Finance-IQ workspace](https://app.fabric.microsoft.com/groups/f00e31f4-f4ab-435c-87f4-fdb5f4b06c4a/list)
- [Interactive three-page FP&A report](https://app.powerbi.com/groups/f00e31f4-f4ab-435c-87f4-fdb5f4b06c4a/reports/7a8240e8-b94b-42a3-9a5e-f0f6beb224d5)
- [Rendered report PDF](generated/FIS-Finance-IQ-Demo.pdf)

The historical deployment receipt records passing live checks for persisted data, all twelve semantic filter paths,
the three GQL investigations, seven ontology entities and twelve relationships,
and the single-user workspace role assignment. All three report pages were
rendered server-side and checked for real KPI/chart content rather than blank
pages. The Data Agent is published; conversational responses still require
review before a customer presentation.

**Local screenshot alignment:** the five additional `DIM_DATE` columns documented
below have been added to the local generated artifacts, not redeployed to Fabric.
The historical deployment receipt does not verify these new columns.

The approved existing F16 capacity is active. Standard capacity running charges
apply; no capacity size or recurring schedule was changed.

## Business story

The CFO asks: **Are we on plan, what explains the variance, and what does the
September outlook imply for the full year?**

The reproducible as-of date is **September 30, 2026**. Actuals cover January 2025
through September 2026. Plan covers all of 2026. The September forecast is a
full-year outlook: closed months equal actuals; October-December are estimates.
All values are USD. Calendar periods are used; no FIS fiscal-calendar assumption
is made.

| Synthetic checkpoint | USD |
|---|---:|
| 2026 actual revenue YTD | 846,750,225.60 |
| 2026 plan revenue YTD | 876,508,875.00 |
| Revenue variance YTD, actual minus plan | -29,758,649.40 |
| Favorable expense variance YTD, plan minus actual | 2,360,328.90 |
| Operating profit variance YTD | -27,398,320.50 |
| Full-year forecast operating profit | 521,621,385.18 |
| Full-year forecast profit versus plan | -40,338,914.82 |
| Digital Banking cloud actual YTD | 4,898,894.00 |
| Digital Banking cloud plan YTD | 3,963,960.00 |

The hero investigation is `ACCOUNT=500100`, `COSTCENTER=300110`,
`PRODUCTLINE=DIGITAL`. Cloud expense is $934,934 over plan, while workforce
savings partly offset expense pressure across the portfolio. Revenue shortfalls
still outweigh the aggregate expense savings.

Operating profit here is revenue less the modeled operating expenses. It is not
GAAP net income, EBITDA, an accounting opinion or a forecast recommendation.

## Model contract

There are exactly seven semantic tables and twelve active, many-to-one
relationships. Filters flow from each shared dimension to each fact, never
bidirectionally between facts.

| Fact | Account | Cost center | Date | Product |
|---|---|---|---|---|
| ACTUALS | `ACCOUNT -> account.Account` | `COSTCENTER -> cost_center.CostCenter` | `DATE -> DIM_DATE.DATE` | `PRODUCTLINE -> product.ProductLine` |
| FORECAST | `ACCOUNT -> account.Account` | `COSTCENTER -> cost_center.CostCenter` | `DATE -> DIM_DATE.DATE` | `PRODUCTLINE -> product.ProductLine` |
| PLAN | `ACCOUNT -> account.Account` | `COSTCENTER -> cost_center.CostCenter` | `DATE -> DIM_DATE.DATE` | `PRODUCTLINE -> product.ProductLine` |

The same seven entities and twelve relationships are used by the ontology and
standalone relationship graph. Semantic display names retain the screenshot
names; physical Delta table names are lowercase.
Ontology entity keys support only strings and integers, so its date entity uses
the existing `DATE_INTEGER` (`yyyyMMdd`) as its identity. Three date-edge tables
carry a matching `TargetDateInteger`. The semantic model and standalone graph
retain their original `DATE` relationships; no user-requested relationship is removed.
The current tenant uses the
[new TMDL ontology format](https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/ontology-definition).
Its entity relationships reuse the twelve Direct Lake table relationships.
Legacy JSON ontology definitions are not used for this deployment, because they
do not round-trip into the current ontology experience.

- **13,710 rows:** 6,048 actuals, 3,456 forecast, 3,456 plan, 8 accounts,
  6 cost centers, 6 products and 730 daily dates.
- **51,840 foreign-key checks** and **51,840 materialized graph edges**.
- Fact grain: account, cost center, product, monthly period, scenario and version.
  Each scenario has one explicitly named version.
- `Amount` is decimal USD; `AmountCents` is integer USD cents. Saved measures
  divide cents by 100 exactly once.
- Revenue and expense amounts are positive. Favorable revenue variance is
  actual minus plan; favorable expense variance is plan minus actual.
- Never sum the three fact tables together. Never compare actual YTD directly
  with full-year plan. A raw fact-to-fact join must use all four grain keys.
- Account/product hierarchies and cost-center hierarchy attributes mirror the
  shapes shown in the supplied screenshots.

### Screenshot reconstruction and assumptions

The supplied screenshots and twelve relationship pairs define the seven-table
scope. They show column names, not source rows, data types, join expressions or
business definitions. The key mappings above are inferred from matching names;
all account codes, product names, cost-center names, hierarchy values and amounts
remain fictional. Other tables visible in the screenshots' Data pane are outside
this demo's scope.

All three facts retain the visible `ACCOUNT`, `Amount`, `CC_PR_AC`, `COSTCENTER`,
`COSTCENTER_PRODUCTLINE`, `CURRENCY`, `CUSTOMER`, `DATASOURCE`, `DATE`, `ENTITY`,
`ICP`, `LOAD_DATE`, `LOAD_TIMESTAMP`, `LOCATION`, `PERIOD`, `PRODUCTLINE`,
`QUARTER`, `SCENARIO`, `VERSION`, `VIEW` and `YEAR` columns. The dimensions retain
the account/product `L1`-`L8` and cost-center `CC_L1`-`CC_L4` hierarchy shapes.
Extra fields such as `RecordID`, `AmountCents`, `AccountType` and `DemoWeight`
are synthetic demo helpers, not claims about the source schema.

The date dimension includes all 28 visible columns. The five previously missing
columns use these **inferred calendar conventions**, not verified FIS definitions:

| Column | Synthetic convention |
|---|---|
| `FIRST_DAY_QUARTER` | First calendar date of the quarter |
| `LAST_DAY_QUARTER` | Last calendar date of the quarter |
| `QUARTER_SEQUENCE` | Consecutive quarters: 2025 Q1 = 1 through 2026 Q4 = 8 |
| `SOW_MONDAY` | Monday starting the date's week, even when it falls in the prior year |
| `YEAR_MONTH_SHORT_V1` | Abbreviated month and two-digit year, for example `Jan-26` |

These columns propagate from [the data generator](data.py) into CSV/schema,
notebook, semantic-model, ontology and graph artifacts. Regression tests cover
the screenshot column names, exact twelve join-key mappings, calendar boundaries
and generated property types. Existing financial checkpoints are unchanged.

## Fabric items

| Item | Purpose |
|---|---|
| FIS_Finance_Bronze | Reproducible source ledger |
| FIS_Finance_Silver | Typed, trimmed, validated finance data |
| FIS_Finance_Gold | Seven conformed tables, variance drivers and twelve edge tables |
| FIS_01_Finance_Medallion | End-to-end build, acceptance checks and evidence display |
| FIS_02_Prepare_Ontology_Date_Keys | Validate integer date identities required by the ontology |
| FIS_Finance_IQ_Model | Direct Lake model and governed DAX finance measures |
| FIS Finance IQ - Synthetic FP&A | Executive, variance-driver and full-year outlook pages |
| FIS_Finance_Relationship_Graph | Cross-scenario relationship investigations |
| FIS_Finance_Ontology | Seven entity types with twelve bound relationship types |
| FIS_Finance_Data_Agent | Published, read-only finance investigation assistant |

Ontology, Graph and Data Agent are tenant-dependent Fabric features. Their
deployment and validation state must be read from the receipt; successful
configuration alone does not prove conversational response quality.

## Ten-minute demo

1. **Set the boundary.** "These are synthetic FIS-style FP&A figures, as of
   September 2026. They are not FIS reported results."
2. **Executive report.** Show actual versus plan YTD. Explain the $29.76M
   revenue shortfall, $2.36M favorable expense variance and $27.40M profit gap.
   The two variances reconcile to the profit gap.
3. **Variance drivers.** Select Digital Banking in the product table to
   cross-filter the page. Open the Gold `variance_drivers` table and filter
   `ReviewRequired=true`. Investigate cloud account `500100`, cost center
   `300110`, product `DIGITAL`.
4. **Evidence.** Show the nine current-year monthly actual/plan records and
   their RecordIDs, versions and dates. A review flag requires at least
   $100,000 unfavorable variance and at least 10% unfavorable variance.
   Flags do not send notifications.
5. **Outlook.** Open the FY2026 Outlook page. Explain that the forecast already
   includes closed-month actuals. Show the $40.34M forecast profit gap to
   full-year plan; do not add YTD actuals to the full-year forecast.
6. **Ontology and graph.** Show the four shared dimensions and the three facts.
   Run [the saved GQL investigations](generated/gql-queries.json): nine
   actual cloud records, six product forecast aggregates, twelve plan months.
7. **Data Agent.** Ask:
   - "What is 2026 actual revenue YTD versus plan, and how does the profit
     variance reconcile to revenue and expense variances?"
   - "Why is Digital Banking cloud expense over plan? Show monthly evidence
     for account 500100, cost center 300110, and product DIGITAL."
   - "Compare full-year forecast revenue and plan by product. Do not add
     actuals to the full-year forecast."
   Check the response against the checkpoints above. The four SQL grounding
   examples are separately executed against Gold tables; conversational
   responses must also be reviewed before a customer presentation.
8. **Governance.** Show the single workspace role assignment and the notebook's
   live validation receipt. No customer workspace or source model was modified.

## Reproduce locally

From the repository root, using Python 3.11 or later:

```powershell
python -m fis_demo.artifacts
python -m unittest discover -s .\fis_demo -p "test_*.py" -v
```

The generator and artifact tests use the Python standard library. The deployment
helper and its mocked tests require `requests` from [requirements.txt](../requirements.txt);
tests do not contact Fabric. Generated CSVs,
schemas, hashes, notebook, TMDL, PBIR, ontology, graph and SQL examples are under
[generated](generated). Initial artifact templates contain explicit placeholder
IDs; deployment replaces them with the dedicated workspace's real IDs.

## Deploy or rerun safely

Install [the deployment dependencies](../requirements.txt) if missing and
authenticate Azure CLI as the workspace owner. The workspace must have the exact
approved name and this description marker:

```text
FIS synthetic FP&A demo; dedicated single-user workspace.
```

The deployment helper checks the workspace marker and requires exactly one role
assignment matching the authenticated user's Entra object ID before changing
anything. It reuses named items only inside that workspace.

```powershell
python -m fis_demo.deploy --workspace-id "<new-workspace-id>" --phase all
```

Phases `data`, `semantic`, `iq` and `verify` allow a failed deployment to resume.
`data` overwrites only the dedicated demo Lakehouses and re-runs the notebook.
`semantic` publishes and refreshes the model, checks KPI values and all twelve
filter paths, then deploys the report. `iq` deploys and checks the graph,
ontology and Data Agent. `verify` rechecks persisted data, DAX, GQL and access.
An error is persisted and raised, never converted to a passing checkpoint.

No refresh schedule is created. Re-running compute consumes approved capacity.
Do not delete the workspace or alter capacity as part of a rehearsal.

## Source files

- [Data generator and finance validation](data.py)
- [Artifact builders](artifacts.py)
- [Deployment and live verification](deploy.py)
- [Shared Fabric REST, authentication and notebook helpers](fabric.py)
- [Targeted unit tests](test_demo.py)
- [Mocked deployment and helper tests](test_deploy.py)
