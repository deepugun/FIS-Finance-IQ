# Fabric IQ Commercial Insurance POC — Detailed Presenter & Facilitator Guide

**Scenario:** *Asterion Global Commercial* — Multinational Commercial Property Underwriting  
**Companion Deck:** [`docs/customer-demo/Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx`](docs/customer-demo/Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx) (also synced to [`Presentation.pptx`](Presentation.pptx))  
**Hands-On Lab Guide:** [`LAB.md`](LAB.md)  
**Design & Architecture Reference:** [`Fabric-IQ-Commercial-Insurance-POC-Design.md`](Fabric-IQ-Commercial-Insurance-POC-Design.md)  
**Deployment Receipt:** [`validation/fabric-deployment.json`](validation/fabric-deployment.json)

---

## Contents

1. [Executive Narrative & Golden Rules](#1-executive-narrative--golden-rules)
2. [Audience Persona Tailoring Matrix](#2-audience-persona-tailoring-matrix)
3. [Pre-Demo Readiness Checklist (T-30m / T-10m / T-2m)](#3-pre-demo-readiness-checklist-t-30m--t-10m--t-2m)
4. [Slide-by-Slide Verbatim Presenter Script (Slides 1–15)](#4-slide-by-slide-verbatim-presenter-script-slides-115)
5. [Live Demo Click-by-Click Runbook (5 Acts)](#5-live-demo-click-by-click-runbook-5-acts)
6. [Copy-Paste Query & Prompt Bank](#6-copy-paste-query--prompt-bank)
7. [Customer Q&A, Objection Handling & Governance FAQ](#7-customer-qa-objection-handling--governance-faq)
8. [Live Demo Recovery & Troubleshooting Playbook](#8-live-demo-recovery--troubleshooting-playbook)

---

## 1. Executive Narrative & Golden Rules

### 1.1 The Core Customer Problem We Solve

In commercial property and multinational insurance, the data needed to review a near-term renewal already exists inside the carrier—but it is trapped in separate operational silos:

- **Exposure & Statement of Values (SOV)** spreadsheets and policy administration tables
- **Catastrophe (CAT) modeling** outputs (`Windstorm`, `Flood`) at the site and zone grain
- **Claims & reserve development** snapshots across policy years
- **Risk engineering** inspection reports and open/closed critical recommendations
- **Multinational program** master-to-local policy requirements (`BI indemnity months`, local wording status)
- **Broker submission assertions** that have not yet been verified against engineering evidence

When an underwriter prepares a renewal 28 days before expiry, answering *"What changed materially on this account, why did its review priority shift, and which exact records do I need to inspect?"* requires manual reconciliation across five or six disconnected tools.

### 1.2 The Fabric IQ Value Proposition

**Microsoft Fabric IQ** turns raw medallion data into a **governed, connected business brain**:

```text
DATA (OneLake Medallion)
  -> SEMANTICS (Direct Lake measures in CommercialInsuranceIQModel)
  -> ENTITY LINKS (CommercialInsuranceOntology + Graph in Fabric)
  -> REASONING (CommercialInsuranceDataAgent grounded in semantics & tables)
  -> MONITORING (CI_Underwriting_RTI Eventhouse + KQL + RenewalRiskOperationsAgent)
  -> HUMAN DECISION & ACTION (Underwriter review with traceable evidence keys)
```

### 1.3 Five Golden Rules for Every Presenter

1. **Lead with evidence, not black-box AI.** Every number in this demo reconciles across Spark, SQL, Direct Lake DAX, KQL, and ISO GQL. Never claim the system predicts loss, sets actuarial price, or autonomously binds or declines a risk.
2. **Use `A001` (`Meridian Specialty Chemicals`) as the single red thread.** Instead of jumping across random accounts, trace `A001` from its `$1.14B` TIV and `77` baseline Renewal Risk Pulse all the way to its live `77 -> 83` Eventhouse threshold crossing and connected GQL graph evidence.
3. **Highlight the integer-cent data contract.** Source monetary columns end in `USDCents` (for example `114,000,000,000` cents = `$1,140,000,000`). Only governed semantic measures and reviewed queries divide by `100` for currency presentation—eliminating floating-point drift.
4. **Show how every score decomposes.** The `77` baseline pulse is the sum of seven bounded `[0, 1]` components multiplied by weights totaling `100` (`CAT 20 + Claims 16 + Growth 7 + Engineering 17 + Concentration 8 + Missing 6 + Proximity 3 = 77`). When the live event arrives, `CAT` (`+4`) and `Claims` (`+2`) push the pulse to `83`, crossing the `80` review threshold.
5. **Treat governance boundaries as a feature, not a footnote.** Keeping `RenewalRiskOperationsAgent` in `shouldRun = false` (`Inactive`) until human approval—and distinguishing unverified broker submission text from engineer-verified closure evidence—builds immediate credibility with regulated insurance buyers.

---

## 2. Audience Persona Tailoring Matrix

| Persona | What They Care About Most | Key Slides to Emphasize | Live Demo Moments to Highlight |
|---|---|---|---|
| **Chief Underwriting Officer (CUO) / Head of Property** | Triage speed, renewal prioritization, authority referrals, avoiding surprises inside 30 days to expiry | Slides 1, 2, 6, 7, 8, 14, 15 | `A001` baseline `77 -> 83` crossing; decomposition of the 7 pulse components; distinguishing broker assertion (`SUB001`) from open critical recs (`RECL001011`, `RECL001012`) |
| **Chief Data & Analytics Officer (CDAO) / Enterprise Architect** | Single copy of data in OneLake, Direct Lake zero-copy semantics, ontology-to-graph projection, MCP agent grounding | Slides 3, 4, 10, 11, 13, 14 | Medallion Lakehouses (`CI_Bronze_Dev`, `CI_Silver_Dev`, `CI_Gold_Dev`); 27-table Direct Lake `CommercialInsuranceIQModel`; 25-entity / 30-relationship `CommercialInsuranceOntology` |
| **CAT Modeling & Risk Engineering Leads** | Peril accumulation (`US_GULF`), site-level TIV growth, overdue critical recommendations, cross-account peril exposure | Slides 5, 6, 7, 11, 13 | GQL Query 1 (High CAT + open critical recs at `Bayport Gulf Coast Works`), GQL Query 2 (`US_GULF` broker concentration `$1.4356B`), GQL Query 5 (cross-account 2026 policy accumulation) |
| **Claims & Multinational Program Operations** | Prior vs current valuation reconciliation (`2025-09-14` vs `2026-09-14`), repeat peril patterns, local policy BI gaps | Slides 2, 6, 8, 12, 13 | DAX `Paid ($3.7M) + Outstanding ($3.3M) = Incurred ($7.0M)`; GQL Query 3 (multi-location `Machinery breakdown` claims); GQL Query 4 (`SG` `LP00103` BI months `12 vs 18` and `DE` `LP00104` `Wording outstanding`) |

---

## 3. Pre-Demo Readiness Checklist (T-30m / T-10m / T-2m)

### 3.1 T-30 Minutes: Capacity & Environment Check

1. **Confirm Fabric capacity is `Active`:**
   ```powershell
   az resource show --resource-group McapsGovernance --name nederd --resource-type Microsoft.Fabric/capacities --api-version 2023-11-01 --query "{state:properties.state,sku:sku.name}" -o json
   ```
   If `state` is `Paused`, resume it at least 15 minutes before the session:
   ```powershell
   az resource invoke-action --action resume --ids /subscriptions/722484ce-cab9-40aa-9c34-4bee6e5bfecf/resourceGroups/McapsGovernance/providers/Microsoft.Fabric/capacities/nederd --api-version 2023-11-01
   ```
2. **Run the quick automated verification check** (optional 30-second sanity check):
   ```powershell
   python .\validation\validate_repository.py
   ```
   Confirm output shows `"status": "PASS"`, `"tables": 31`, `"rows": 3731`, `"foreign_key_checks": 5475`, `"transition": [77.0, 83.0]`.

### 3.2 T-10 Minutes: Pre-Open Browser Tabs in Order

Open the workspace (`https://app.fabric.microsoft.com/groups/fef80264-9f1f-4160-b8c8-8e3bf1de7e14`) and arrange **6 clean browser tabs** from left to right (staying well under Fabric's 20-open-item tab limit):

| Tab # | Item to Open | Type | What Should Be Visible on Screen |
|---:|---|---|---|
| **Tab 1** | `Test` workspace item list | Workspace | Filtered or sorted to show the 3 Lakehouses, 7 Notebooks, `CommercialInsuranceIQModel`, `CI_Underwriting_RTI`, `CommercialInsuranceOntology`, `CI_Underwriting_Graph_Dev`, `CommercialInsuranceDataAgent`, and `RenewalRiskOperationsAgent` |
| **Tab 2** | `CI_Gold_Dev` | Lakehouse | Explorer expanded showing `Tables` (`31` `demo_*` tables + `25` `node_*` + `30` `edge_*` tables) and `Files/underwriting_demo` |
| **Tab 3** | `CommercialInsuranceIQModel` | Semantic model | Model layout view showing `Accounts` connected to `Locations`, `Policies`, `Renewals`, `UnderwritingFeatures`, `RiskPulse`, etc., plus the DAX query view ready with the `A001` query |
| **Tab 4** | `CI_Underwriting_RTI` | KQL Database | Query pane pre-populated with the `DedupedEvents()` threshold crossing query (`RunId == 'deployed-001'`) |
| **Tab 5** | `CommercialInsuranceOntology` & `CI_Underwriting_Graph_Dev` | Ontology / Graph | Ontology canvas showing the 25 entities & 30 relationships (including `Account`'s `UnderwritingEvents` time-series binding), plus the Graph **Code editor** tab ready with the 5 GQL queries from [`gql/underwriting.gql`](gql/underwriting.gql) |
| **Tab 6** | `CommercialInsuranceDataAgent` & `RenewalRiskOperationsAgent` | Agents | Data Agent chat pane showing `CommercialInsuranceIQModel` + `CI_Gold_Dev` selected; Operations Agent configuration showing `CI_Underwriting_RTI` and `shouldRun = false` (`Inactive`) |

### 3.3 T-2 Minutes: Projection & Audio/Visual Polish

- Open [`docs/customer-demo/Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx`](docs/customer-demo/Fabric-IQ-Commercial-Insurance-Customer-Demo.pptx) in PowerPoint Slide Show mode.
- Set browser zoom to **110%–125%** so table names, DAX/KQL/GQL code, and result rows are effortless to read from the back of a conference room or over Microsoft Teams screen share.
- Keep Section 6 of this guide ([Copy-Paste Query & Prompt Bank](#6-copy-paste-query--prompt-bank)) open on a second monitor so you never have to type live queries from memory.

---

## 4. Slide-by-Slide Verbatim Presenter Script (Slides 1–15)

### Standard Pacing Overview

- **Executive Overview + Concepts (Slides 1–8):** ~6 minutes
- **Run of Show + Live Demo (Slides 9–13 + Browser Tabs 1–6):** ~12 minutes (or ~25 minutes for technical deep-dive)
- **Governance + Outcomes & Next Step (Slides 14–15):** ~2 minutes

---

### Slide 1: From renewal evidence to explainable action

- **Duration:** 45 seconds
- **Visual Cue:** Dark navy executive title slide with the copper `83` badge in the top-left corner and three trust pills (`SYNTHETIC DATA`, `HUMAN-GOVERNED`, `EXPLAINABLE SIGNALS`).
- **Verbatim Talk Track:**
  > *"Welcome, everyone. Today we are going to walk through a live Microsoft Fabric IQ demonstration built specifically for commercial insurance underwriting—using our synthetic global property carrier, **Asterion Global Commercial**.*
  >
  > *Notice the number **83** in the top corner and the three principles at the bottom: **Synthetic Data**, **Human-Governed**, and **Explainable Signals**. By the end of this session, you will see how Fabric IQ takes 31 raw underwriting, exposure, catastrophe, claims, engineering, and multinational-program tables, unifies them under one governed semantic and ontology layer, and detects the exact moment our hero account crosses the renewal review threshold from **77 to 83**—while keeping every single component score and evidence key transparent for a human underwriter."*
- **Transition to Slide 2:** *"Let's start with why renewal preparation is so painful today."*

---

### Slide 2: The renewal decision is trapped across disconnected evidence

- **Duration:** 45 seconds
- **Visual Cue:** Three evidence columns (`RISK EVIDENCE`, `CONTROL EVIDENCE`, `DECISION CONTEXT`) feeding the central question card.
- **Verbatim Talk Track:**
  > *"When a commercial property account is 28 days away from renewal, the underwriter isn't suffering from a lack of data—they are suffering from disconnected evidence.*
  >
  > *On the left, **Risk Evidence** lives in statement-of-values spreadsheets, CAT model runs, and claim valuation tables. In the middle, **Control Evidence** lives in risk-engineering inspection PDFs, multinational local-policy trackers, and unverified broker submissions. On the right, **Decision Context**—expiring limits, rate changes, and underwriting authority—sits in policy administration.*
  >
  > *Because those records don't share a governed identity and semantic layer, answering a simple triage question—**'Which renewal changed, why did it change, and what exact evidence should I inspect?'**—takes hours of manual spreadsheet stitching."*
- **Transition to Slide 3:** *"Here is how Microsoft Fabric IQ changes that operating model."*

---

### Slide 3: Fabric IQ turns governed data into shared business meaning

- **Duration:** 60 seconds
- **Visual Cue:** Six numbered capability cards (`1 Data`, `2 Semantics`, `3 Entity links`, `4 Reasoning`, `5 Monitoring`, `6 Human action`) and the bottom design contract banner.
- **Verbatim Talk Track:**
  > *"Fabric IQ is not a separate database or a black-box AI wrapper. It is a six-step discipline on top of OneLake:*
  >
  > *1. **Data:** OneLake stores our Bronze, Silver, and Gold Delta tables once.*
  > *2. **Semantics:** A Direct Lake semantic model defines every financial and underwriting KPI once—converting integer cents to dollars and locking in matched valuation dates.*
  > *3. **Entity links:** Fabric IQ Ontology and Graph connect business entities—Account, Location, Policy, Claim, CAT Risk, Engineering Inspection, and Multinational Program—so we can traverse relationships across domains.*
  > *4. **Reasoning:** Data Agents answer natural-language questions by generating auditable DAX and SQL against those governed definitions.*
  > *5. **Monitoring:** Real-Time Intelligence in Eventhouse watches live underwriting events and recomputes the score in KQL.*
  > *6. **Human action:** Underwriters review the surfaced evidence keys and make the decision. Look at the contract at the bottom: **DATA -> SEMANTICS -> RELATIONSHIPS -> REASONING -> MONITORING -> DECISION -> ACTION**."*
- **Transition to Slide 4:** *"Let's look at the concrete medallion and IQ architecture we deployed in our Fabric workspace."*

---

### Slide 4: A medallion foundation powers both analytical and real-time experiences

- **Duration:** 60 seconds
- **Visual Cue:** Architecture flow from `BRONZE` (`31 source tables + audit columns`) -> `SILVER` (`features, pulse + material signals`) -> branching to `GOLD` (`graph-ready nodes + relationships`) -> `DIRECT LAKE` (`shared measures`) and `EVENTHOUSE` (`live change signals`), converging into `FABRIC IQ` (`ontology, Graph, agents, human review`).
- **Verbatim Talk Track:**
  > *"Everything in our demo runs on a clean medallion architecture in Microsoft Fabric:*
  >
  > *In **Bronze (`CI_Bronze_Dev`)**, we persist 31 source tables with ingestion audit metadata. In **Silver (`CI_Silver_Dev`)**, we compute account-grain underwriting features, the explainable Renewal Risk Pulse, and 44 material-change signals. In **Gold (`CI_Gold_Dev`)**, we publish both the curated `demo_*` tables and the 25 `node_*` and 30 `edge_*` tables.*
  >
  > *From Gold and Silver, two paths work in parallel: the **analytical path** powers our 27-table Direct Lake semantic model (`CommercialInsuranceIQModel`), our 25-entity ontology (`CommercialInsuranceOntology`), and our Graph model (`CI_Underwriting_Graph_Dev`). Meanwhile, the **real-time path** streams underwriting updates into Eventhouse (`CI_Underwriting_RTI`) and binds them directly back to the `Account` entity in our ontology. Both paths preserve the exact same identity chain: **Account -> Policy -> Location -> Claim -> Renewal -> Signal**."*
- **Transition to Slide 5:** *"Before we zoom into our hero account, let's look at the scale and determinism of the synthetic portfolio."*

---

### Slide 5: The demo is deterministic, evidence-rich, and safe to rehearse

- **Duration:** 45 seconds
- **Visual Cue:** Six metric cards (`20 commercial accounts`, `100 insured locations`, `40 policy years`, `80 claims`, `31 governed tables`, `5,475 referential checks`).
- **Verbatim Talk Track:**
  > *"We built this environment to engineering-grade reproducibility standards. Every run generates the exact same **20 commercial accounts**, **100 insured locations** across 10 countries, **40 master policy years** (`2025` and `2026`), and **80 claims** across **31 governed tables**.*
  >
  > *Before a single notebook writes to Delta, our validation suite runs **5,475 foreign-key and financial reconciliation checks**—verifying that `Paid + Outstanding = Incurred` on every claim valuation, that `Property (75%) + BI (25%)` exposures sum to location TIV, and that SHA-256 hashes match across the repository."*
- **Transition to Slide 6:** *"Within those 20 accounts, let's meet our hero account: `A001`, Meridian Specialty Chemicals."*

---

### Slide 6: A001: one renewal, one transparent evidence story

- **Duration:** 60 seconds
- **Visual Cue:** Left dark-navy card for `MERIDIAN SPECIALTY CHEMICALS` (`Global property renewal | 28 days`, `77 BASELINE PULSE`) and four KPI callout cards on the right (`$1.14B current TIV`, `$7M modeled CAT AAL`, `$7M current incurred loss`, `2 open critical recommendations`).
- **Verbatim Talk Track:**
  > *"Meet account **`A001`—Meridian Specialty Chemicals**. Meridian has a global property renewal coming up in **28 days** (`2026-10-12` as of our `2026-09-14` snapshot).*
  >
  > *At baseline, Meridian's Renewal Risk Pulse is **77**—just below our high-priority review threshold of `80`. Why is it at `77`? Look at the four governed metrics on the right:*
  > *- **Current Total Insured Value is `$1.14B`**, up **14%** from `$1.00B` last year, driven by expansion at its Bayport, Texas facility (`$729.6M` TIV).*
  > *- **Modeled CAT Average Annual Loss is `$7.0M`**, up **40%** from `$5.0M`.*
  > *- **Current Incurred Loss is `$7.0M`** (`$3.7M` paid and `$3.3M` in case reserves), also up **40%** from prior valuation.*
  > *- And **`2` critical risk-engineering recommendations remain open** past their September 1st due date at Bayport (`RECL001011` firewater pump redundancy and `RECL001012` flood barrier verification)—even though the broker submission claims flood barrier work is funded.*
  >
  > *And notice the governance rule at the bottom: **The pulse prioritizes review. It does not price, bind, decline, or infer causation.**"*
- **Transition to Slide 7:** *"How is that `77` calculated? Let's open the formula."*

---

### Slide 7: The Renewal Risk Pulse is additive, bounded, and explainable

- **Duration:** 60 seconds
- **Visual Cue:** Horizontal bar chart and 7 component cards (`CAT 20/25`, `Claims 16/20`, `Growth 7/10`, `Engineering 17/20`, `Concentration 8/10`, `Missing 6/10`, `Proximity 3/5`, `77 TOTAL`).
- **Verbatim Talk Track:**
  > *"Underwriters and regulators rightly reject opaque scores they can't explain to a broker or risk committee. So the Renewal Risk Pulse is 100% additive, bounded, and transparent.*
  >
  > *Each of the seven risk drivers is normalized to `[0, 1]` and multiplied by an explicit weight whose total is `100`:*
  > *- **CAT deterioration:** `0.80 x 25 = 20 pts` (`40%` CAT AAL growth against a `50%` cap)*
  > *- **Claims development:** `0.80 x 20 = 16 pts` (`40%` incurred growth against a `50%` cap)*
  > *- **Exposure growth:** `0.70 x 10 = 7 pts` (`14%` TIV growth against a `20%` cap)*
  > *- **Engineering deficiencies:** `0.85 x 20 = 17 pts` (`85` of `100` materiality weight points still open)*
  > *- **CAT zone concentration:** `0.80 x 10 = 8 pts` (`64%` of account TIV concentrated in `US_GULF`)*
  > *- **Missing submission items:** `0.60 x 10 = 6 pts` (`3` of `5` required renewal items still outstanding)*
  > *- **Renewal proximity:** `0.60 x 5 = 3 pts` (`28` days remaining inside a `70`-day window)*
  >
  > *Add them up: `20 + 16 + 7 + 17 + 8 + 6 + 3 = 77`. Every point links directly back to its source table and evidence key."*
- **Transition to Slide 8:** *"Now what happens when new information arrives mid-triage? Let's look at the real-time path."*

---

### Slide 8: Real-time monitoring detects the moment review priority changes

- **Duration:** 60 seconds
- **Visual Cue:** Line chart showing `A001` stepping from `77` (`Baseline`) across `80` (`Threshold`) to `83` (`Live update`), alongside three step cards (`1. Ingest`, `2. Validate`, `3. Surface`) and the bottom badge `Verified: A001 crossed 77 to 83`.
- **Verbatim Talk Track:**
  > *"Static batch reports only tell you where an account stood yesterday. With Fabric Real-Time Intelligence, Eventhouse ingests streaming underwriting events—such as a CAT model refresh at Bayport (`+$400K` AAL, moving `CAT` from `0.80` to `0.96` = `+4` pulse points) combined with a reserve increase on claim `CL00101` (`+$250K`, moving `Claims` from `0.80` to `0.90` = `+2` pulse points).*
  >
  > *In KQL, we don't blindly trust incoming event scores. Our `DedupedEvents()` function deduplicates by `EventId`, rejects future-dated timestamps, and **recomputes `ExpectedPulse` from the seven component columns** before accepting the event. That validated update moves `A001` from **77 to 83**—crossing the `80` review threshold once and surfacing the exact `EvidenceRef`."*
- **Transition to Slide 9:** *"Let's look at our four-act demo flow before we switch to the live Fabric workspace."*

---

### Slide 9: Customer demo: four acts in twelve minutes

- **Duration:** 30 seconds
- **Visual Cue:** Four timeline cards (`01 Orient - 2 min`, `02 Trace - 3 min`, `03 Explain - 3 min`, `04 Detect - 4 min`).
- **Verbatim Talk Track:**
  > *"Here is our live run of show. In **Act 1 (Orient)**, we'll inspect the three Medallion Lakehouses and seven completed notebooks. In **Act 2 (Trace)**, we'll query our 27-table Direct Lake semantic model (`CommercialInsuranceIQModel`) for `A001`. In **Act 3 (Explain)**, we'll traverse our 25-entity Ontology and run multi-hop ISO GQL queries on our Fabric Graph. And in **Act 4 (Detect)**, we'll execute the Eventhouse KQL crossing query and inspect our governed Data and Operations Agents."*
- **Transition to Slide 10:** *"Let's preview Step 1, Step 2, and Step 3 on slides 10–12, or jump straight into the live workspace after Slide 12."*

---

### Slide 10: Demo step 1: prove the governed data foundation

- **Duration:** 45 seconds
- **Visual Cue:** Seven chevron cards (`01 Generate` through `07 Stage`) and three bottom proof cards (`Show`, `Say`, `Checkpoint`).
- **Verbatim Talk Track:**
  > *"In Step 1, we show how the seven ordered notebooks build the medallion layers: notebooks 01 and 02 generate and persist the **31 Bronze Delta tables** (`3,731` rows); notebooks 03, 04, and 05 derive the **20 Silver account features**, the **77 baseline pulse**, and **44 material-change signals**; notebook 06 materializes the **25 graph node tables and 30 edge tables** in Gold; and notebook 07 stages the controlled live event pair. Remember the one-line summary: **Bronze preserves; Silver explains; Gold relates.**"*
- **Transition to Slide 11:** *"Next, Step 2 brings shared business semantics on top of Gold."*

---

### Slide 11: Demo step 2: ask once, answer with shared semantics

- **Duration:** 45 seconds
- **Visual Cue:** Left dark card (`Commercial Insurance IQ Model`, `Direct Lake`) and right 3-step verification flow (`1 Filter AccountId = A001`, `2 Read TIV, CAT AAL, incurred`, `3 Reconcile Pulse and evidence IDs`).
- **Verbatim Talk Track:**
  > *"In Step 2, we open `CommercialInsuranceIQModel`—our Direct Lake semantic model with 27 tables, 25 single-direction relationships, and 30 saved DAX measures. Because Direct Lake reads OneLake Delta files directly without import duplication, filtering `AccountId = 'A001'` immediately reconciles **$1.14B TIV**, **$7M CAT AAL**, **$7M incurred loss**, **2 critical engineering recommendations**, and **pulse 77** across the entire model."*
- **Transition to Slide 12:** *"And Step 3 proves the real-time threshold crossing in Eventhouse."*

---

### Slide 12: Demo step 3: prove the threshold crossing

- **Duration:** 45 seconds
- **Visual Cue:** Left dark KQL code card (`DedupedEvents() | where RunId == 'deployed-001' ...`) and right `PRIMARY RESULT` card (`A001 : 77 -> 83`).
- **Verbatim Talk Track:**
  > *"In Step 3, we run our seven-line KQL crossing query in `CI_Underwriting_RTI`. By sorting by `AccountId`, `EventTime`, and `Sequence` and comparing `prev(Pulse) < 80` to `Pulse >= 80`, KQL returns one deterministic row: **`A001` moving from `77` to `83`**."*
- **Transition to Slide 13 (and Live Demo Switch):** *"Let's also look at Slide 13 to see how Ontology, Graph, Data Agent, and Operations Agent extend this core foundation—and then let's switch to our live Fabric browser tabs!"*

---

### Slide 13: Extend the core proof when tenant capabilities are ready

- **Duration:** 45 seconds
- **Visual Cue:** Four 2x2 capability cards (`Ontology`, `Graph`, `Data Agent`, `Operations Agent`).
- **Verbatim Talk Track:**
  > *"On top of our Lakehouse, Direct Lake, and Eventhouse core, all four Fabric IQ experiences are deployed in our workspace:*
  > *- **`CommercialInsuranceOntology`** binds all **25 business entities** and **30 relationships** to Gold Lakehouse tables, plus a live **TimeSeries binding** from `CI_Underwriting_RTI.UnderwritingEvents` onto `Account`.*
  > *- **`CI_Underwriting_Graph_Dev`** (and the Ontology companion graph) execute multi-hop ISO **GQL** queries across locations, CAT zones, claims, and multinational local policies.*
  > *- **`CommercialInsuranceDataAgent`** is grounded in `CommercialInsuranceIQModel` and `CI_Gold_Dev` with governed instructions and validated few-shots.*
  > *- **`RenewalRiskOperationsAgent`** is configured against `CI_Underwriting_RTI` and kept safely stopped (`shouldRun = false`) until human approval.*
  >
  > *Let's switch to the live Fabric portal right now and walk through these in action."*
  *(👉 **Switch to Browser Tabs 1–6 and execute [Section 5: Live Demo Click-by-Click Runbook](#5-live-demo-click-by-click-runbook-5-acts) now. Return to Slide 14 after Act 5.**)*

---

### Slide 14: Trust comes from explicit boundaries, not polished answers

- **Duration:** 45 seconds
- **Visual Cue:** Two side-by-side governance panels (`WHAT WE PROVE` with green `OK` badges vs `WHAT WE DO NOT CLAIM` with red `NO` badges).
- **Verbatim Talk Track:**
  > *"As we wrap up the live demo, this slide is the reason risk, compliance, and actuarial leaders trust this architecture. On the left is **What We Prove**: synthetic isolated data, stable IDs and matched valuation dates (`2025-09-14` vs `2026-09-14`), integer-cent financial columns, evidence keys retained on every signal, and human review before any action.*
  >
  > *On the right is **What We Explicitly Do Not Claim**: no actuarial pricing claim, no automated bind/decline/referral, no causal inference from correlated signals, no production security waiver, and no unapproved notification."*
- **Transition to Slide 15:** *"Which brings us to our three customer outcomes and recommended next step."*

---

### Slide 15: One connected renewal story. Three customer outcomes.

- **Duration:** 45 seconds
- **Visual Cue:** Dark navy closing slide with three outcome cards (`FASTER`, `CLEARER`, `SAFER`) and the 60-minute design workshop call to action.
- **Verbatim Talk Track:**
  > *"To summarize: Fabric IQ delivers three outcomes for commercial underwriting teams:*
  > *1. **FASTER:** Prioritize the near-term renewals that materially changed before expiry.*
  > *2. **CLEARER:** Explain every score through governed DAX measures, GQL relationship paths, and row-level evidence keys.*
  > *3. **SAFER:** Keep pricing, binding, and outbound notifications 100% human-governed.*
  >
  > *Our recommended next step is a focused **60-minute design workshop** where we map one of your priority underwriting or claims journeys—using your entity vocabulary and your target KPIs—into this exact Fabric IQ blueprint. What questions can we answer?"*

---

## 5. Live Demo Click-by-Click Runbook (5 Acts)

Use this runbook when switching from Slide 13 to your pre-opened Fabric browser tabs.

### Act 1: Medallion Data Foundation (`Tab 1` & `Tab 2` — 2 Minutes)

1. **Click `Tab 1` (`Test` Workspace):**
   - Point out the three Lakehouses (`CI_Bronze_Dev`, `CI_Silver_Dev`, `CI_Gold_Dev`) and the seven ordered notebooks (`CI_01` through `CI_07`).
   - **Say:** *"Everything starts in OneLake. Seven idempotent notebooks generate our 31 tables (`3,731` rows, `5,475` referential checks), compute Silver account features and the Renewal Risk Pulse, and materialize Gold graph node and edge tables."*
2. **Click `Tab 2` (`CI_Gold_Dev` Lakehouse):**
   - In the left **Explorer**, point to `Tables`: show the `demo_*` curated tables (`demo_accounts`, `demo_underwritingfeatures`, `demo_riskpulse`, `demo_renewalsignals`) alongside the `25` `node_*` tables (`node_account`, `node_location`, `node_localpolicy`) and `30` `edge_*` tables (`edge_account_operates_location`, etc.).
   - Click `demo_riskpulse` (or `demo_underwritingfeatures`) to preview the rows and point out row `A001` (`Pulse = 77`, `TIVUSDCents = 114000000000`).
   - **Say:** *"Notice that `TIVUSDCents` is stored as an exact 64-bit integer (`114,000,000,000` cents). We never store approximate floating-point dollars in source tables."*

---

### Act 2: Shared Business Semantics in Direct Lake (`Tab 3` — 3 Minutes)

1. **Click `Tab 3` (`CommercialInsuranceIQModel`):**
   - Show the **Model layout** diagram: point to `Accounts` at the center connected via 25 single-direction relationships to `Locations -> Exposures / CATRisk / Claims / EngineeringInspections`, `Policies -> PolicyValuations / Coverages`, `Renewals -> PricingScenarios`, `MultinationalPrograms -> LocalPolicies -> ProgramRequirements`, `UnderwritingFeatures`, and `RiskPulse`.
   - Expand `Accounts` in the **Data** pane on the right to show the **25 saved measures** (including `Total Insured Value`, `Modeled CAT Loss`, `Incurred Loss`, `Paid Loss`, `Outstanding Loss`, `Loss Ratio`, `Critical Recommendations`, `TIV YoY`, `CAT Exposure Change`).
2. **Run the Saved-Measure DAX Proof:**
   - Open the **DAX query view** (or run from your query window) and execute the saved-measure query from [Section 6.1](#61-dax-queries-commercialinsuranceiqmodel).
   - Point to the single returned row for `A001`:
     - `[TIV]` = **`1,140,000,000.0`** (`$1.14B`, `[TIV_YoY]` = **`0.14`** / `+14%`)
     - `[CAT_AAL]` = **`7,000,000.0`** (`$7.0M`, `[CAT_Change]` = **`0.40`** / `+40%`)
     - `[Incurred]` = **`7,000,000.0`** (`[Paid]` = `$3.7M`, `[Outstanding]` = `$3.3M`)
     - `[WrittenPremium]` = **`$34,981,132`**, `[EarnedPremium]` = **`$33,600,310`**, `[LossRatio]` = **`20.83%`**
     - `[CriticalRecs]` = **`2`**, `[OpenRecs]` = **`3`**, `[CompletionRate]` = **`25%`**
     - `[Pulse]` = **`77.0`**
   - **Say:** *"With Direct Lake, there is zero data movement between Gold Delta tables and Power BI / Analysis Services. And because these 30 measures are saved in the model, every report, DAX query, and AI agent gets the exact same governed numbers."*

---

### Act 3: Real-Time Threshold Crossing in Eventhouse (`Tab 4` — 3 Minutes)

1. **Click `Tab 4` (`CI_Underwriting_RTI` KQL Database):**
   - In the left **Explorer**, expand **Tables** (`UnderwritingEvents`) and **Functions** (`DedupedEvents`, `LatestPulse`).
   - **Say:** *"While the semantic model holds our governed snapshot, Eventhouse monitors streaming underwriting events. Let's see what happens when Bayport's CAT model updates and claim `CL00101` takes a reserve increase."*
2. **Run the KQL Threshold Crossing Query:**
   - Highlight and run Query 1 from [Section 6.2](#62-kql-queries-ci_underwriting_rti-eventhouse):
     ```kql
     DedupedEvents()
     | where RunId == 'deployed-001'
     | sort by AccountId asc, EventTime asc, Sequence asc
     | serialize
     | extend PreviousAccount = prev(AccountId), PreviousPulse = prev(Pulse)
     | where AccountId == PreviousAccount and PreviousPulse < 80.0 and Pulse >= 80.0
     | project EventId, AccountId, PreviousPulse, Pulse, EventTime, EvidenceRef
     ```
   - Point to the single returned row:
     - `EventId`: `deployed-001-002`
     - `AccountId`: `A001`
     - `PreviousPulse`: **`77`**
     - `Pulse`: **`83`**
     - `EvidenceRef`: `CAT Bayport AAL +400000 USD; CL00101 incurred +250000 USD; synthetic live overlay`
   - **Say:** *"Look at how clean that is: one run ID, one account, one deduplicated and formula-verified crossing from **77 to 83**, and the exact evidence reference telling the underwriter why the score moved."*

---

### Act 4: Ontology & Connected-Risk Graph in GQL (`Tab 5` — 3 Minutes)

1. **Click `Tab 5` (`CommercialInsuranceOntology` & `CI_Underwriting_Graph_Dev`):**
   - First show `CommercialInsuranceOntology`: point out the **25 entity types** and **30 relationship types**, and highlight `Account` which has both its static Lakehouse binding (`node_account`) and its live Eventhouse time-series binding (`CI_Underwriting_RTI.UnderwritingEvents` on `EventTime`).
2. **Switch to the Graph Code Editor (`CI_Underwriting_Graph_Dev` or `CommercialInsuranceOntology_graph_<id>`):**
   - Run **GQL Query 1 (High CAT + Open Critical Engineering Recommendations)**:
     - Point to the **10 returned rows**, specifically `Meridian Specialty Chemicals` -> `Bayport Gulf Coast Works` -> `RECL001011` (`Firewater pump redundancy`) and `RECL001012` (`Flood barrier verification`).
     - **Say:** *"In a relational database, walking `Account -> Location -> CATRisk` AND `Location -> Inspection -> Recommendation` requires a 5-table join. In ISO GQL, it is a single visual pattern match."*
   - Run **GQL Query 4 (Multinational Program Local Policy Gaps)**:
     - Point to the **2 returned rows** for `Meridian Specialty Chemicals`:
       - `SG` (`LP00103`): `RequiredBIMonths = 18`, `BIIndemnityMonths = 12`
       - `DE` (`LP00104`): `CoverageStatus = 'Wording outstanding'`
     - **Say:** *"Here we traverse `Account -> MultinationalProgram -> ProgramRequirement -> LocalPolicy` and immediately spot that Singapore's local policy only covers 12 months of Business Interruption against an 18-month master requirement, and Germany's wording is still outstanding."*

---

### Act 5: Governed Data Agent & Operations Agent (`Tab 6` — 2 Minutes)

1. **Click `Tab 6` (`CommercialInsuranceDataAgent`):**
   - Show the **Sources** pane (`CommercialInsuranceIQModel` + `CI_Gold_Dev`), the **Agent instructions**, and the **4 few-shot examples**.
   - Ask one or two natural-language questions from [Section 6.5](#65-data-agent-prompts-commercialinsurancedataagent):
     - *"What is A001's current TIV, CAT AAL, and incurred loss?"*
     - *"Which critical engineering recommendations remain open for A001?"*
   - Expand the generated query under the answer to prove it queried the governed tables/measures and returned `RECL001011` and `RECL001012`.
2. **Show `RenewalRiskOperationsAgent`:**
   - Point out that it is bound to `CI_Underwriting_RTI`, monitors `LatestPulse()` for `Pulse >= 80.0` and `DaysToRenewal <= 45`, and is intentionally in **`Inactive` (`shouldRun = false`)** state.
   - **Say:** *"Finally, our Operations Agent is configured and ready—but kept stopped by default until an authorized underwriting manager approves the notification channel and recipient list. That is end-to-end governance in Fabric IQ."*

---

## 6. Copy-Paste Query & Prompt Bank

### 6.1 DAX Queries (`CommercialInsuranceIQModel`)

#### A. Complete Hero Account (`A001`) Saved-Measure Check (No `DEFINE` Required)

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

**Expected Output:**
- `AccountCount`: `1`
- `TIV`: `1,140,000,000.0` (`$1.14B`)
- `CAT_AAL`: `7,000,000.0` (`$7.0M`)
- `Incurred`: `7,000,000.0` (`Paid = 3,700,000.0`, `Outstanding = 3,300,000.0`)
- `WrittenPremium`: `34,981,132.0`, `EarnedPremium`: `33,600,310.0`, `LossRatio`: `0.208331` (`20.83%`)
- `ClaimCount`: `4`
- `CriticalRecs`: `2`, `OpenRecs`: `3`, `CompletionRate`: `0.25` (`25.0%`)
- `HighSignals`: `4`
- `Pulse`: `77.0`
- `TIV_YoY`: `0.14` (`+14.0%`), `CAT_Change`: `0.40` (`+40.0%`)

#### B. Portfolio Top 5 Accounts by Renewal Risk Pulse

```dax
EVALUATE
TOPN(
    5,
    SUMMARIZECOLUMNS(
        Accounts[AccountId],
        Accounts[AccountName],
        Accounts[Region],
        "Pulse", [Average Risk Pulse],
        "TIV_USD", [Total Insured Value],
        "CAT_AAL_USD", [Modeled CAT Loss],
        "Incurred_USD", [Incurred Loss],
        "OpenCritical", [Critical Recommendations]
    ),
    [Pulse], DESC,
    Accounts[AccountId], ASC
)
ORDER BY [Pulse] DESC, Accounts[AccountId] ASC
```

---

### 6.2 KQL Queries (`CI_Underwriting_RTI` Eventhouse)

#### A. Primary Demo Proof: Exact `77 -> 83` Threshold Crossing

```kql
DedupedEvents()
| where RunId == 'deployed-001'
| sort by AccountId asc, EventTime asc, Sequence asc
| serialize
| extend PreviousAccount = prev(AccountId), PreviousPulse = prev(Pulse)
| where AccountId == PreviousAccount and PreviousPulse < 80.0 and Pulse >= 80.0
| project EventId, AccountId, PreviousPulse, Pulse, EventTime, EvidenceRef
```

**Expected Output (1 row):**
- `EventId`: `deployed-001-002` | `AccountId`: `A001` | `PreviousPulse`: `77` | `Pulse`: `83` | `EvidenceRef`: `CAT Bayport AAL +400000 USD; CL00101 incurred +250000 USD; synthetic live overlay`

#### B. Latest Validated State for `A001`

```kql
LatestPulse()
| where RunId == 'deployed-001' and AccountId == 'A001'
| project EvaluationKey, AccountId, EventType, Pulse, CAT, Claims, Growth, Engineering, Concentration, Missing, Proximity, DaysToRenewal, OpenCritical, EvidenceRef
```

**Expected Output (1 row):**
- `EvaluationKey`: `A001:deployed-001:2` | `Pulse`: `83` | `CAT`: `0.96` | `Claims`: `0.9` | `DaysToRenewal`: `28` | `OpenCritical`: `2`

#### C. Data Integrity Gate Check (Zero Invalid Formula Rows)

```kql
UnderwritingEvents
| extend ExpectedPulse = round(25.0 * CAT + 20.0 * Claims + 10.0 * Growth + 20.0 * Engineering + 10.0 * Concentration + 10.0 * Missing + 5.0 * Proximity, 2)
| where abs(Pulse - ExpectedPulse) > 0.05 or EventTime > now() + 5m
```

**Expected Output:** `0 rows` (proving every event in `UnderwritingEvents` satisfies the weighted formula).

---

### 6.3 ISO GQL Queries (`CI_Underwriting_Graph_Dev` & Companion Graph)

#### Query 1: High CAT (`Score >= 80`) + Open Critical Engineering Recommendations (`10 rows`)

```gql
MATCH (account:Account)-[:OPERATES]->(location:Location)-[:HAS_CAT]->(cat:CATRisk),
      (location)-[:INSPECTED_BY]->(inspection:RiskEngineeringInspection)-[:ISSUED]->(rec:EngineeringRecommendation)
FILTER cat.Score >= 80 AND rec.Status = 'Open' AND rec.IsCritical = TRUE
RETURN DISTINCT account.AccountName, location.LocationName, cat.PerilId, rec.Title, rec.RecommendationId
LIMIT 25
```

#### Query 2: `US_GULF` Broker Concentration (`5 rows`)

```gql
MATCH (broker:Broker)-[:SERVICES]->(account:Account)-[:OPERATES]->(location:Location)
FILTER location.CATZone = 'US_GULF'
LET brokerName = broker.BrokerName
RETURN brokerName, count(DISTINCT account.AccountId) AS accounts, sum(location.TIVUSDCents) AS tivCents
GROUP BY brokerName
ORDER BY tivCents DESC
LIMIT 5
```

#### Query 3: Multi-Location Same-Peril Claims (`20 rows`)

```gql
MATCH (account:Account)-[:OPERATES]->(first:Location)-[:HAS_CLAIM]->(firstClaim:Claim)-[:FROM_EVENT]->(:LossEvent)-[:OF_PERIL]->(peril:Peril),
      (account)-[:OPERATES]->(second:Location)-[:HAS_CLAIM]->(secondClaim:Claim)-[:FROM_EVENT]->(:LossEvent)-[:OF_PERIL]->(peril)
FILTER first.LocationId < second.LocationId
RETURN DISTINCT account.AccountName, first.LocationName, second.LocationName, peril.PerilName,
       firstClaim.ClaimId, secondClaim.ClaimId
LIMIT 25
```

#### Query 4: Multinational Program Local Policy Gaps (`2 rows`)

```gql
MATCH (account:Account)-[:HAS_PROGRAM]->(program:MultinationalProgram)-[:REQUIRES]->(requirement:ProgramRequirement)-[:MATCHES_LOCAL]->(localPolicy:LocalPolicy)
FILTER localPolicy.BIIndemnityMonths < requirement.RequiredBIMonths OR localPolicy.CoverageStatus <> 'Confirmed'
RETURN account.AccountName, localPolicy.CountryId, localPolicy.LocalPolicyId, requirement.RequiredBIMonths,
       localPolicy.BIIndemnityMonths, localPolicy.CoverageStatus
LIMIT 25
```

#### Query 5: Cross-Account `US_GULF` Peril Accumulation for 2026 Policies (`25 rows`)

```gql
MATCH (first:Account)-[:OPERATES]->(firstLoc:Location)-[:HAS_CAT]->(:CATRisk)-[:FOR_PERIL]->(peril:Peril),
      (second:Account)-[:OPERATES]->(secondLoc:Location)-[:HAS_CAT]->(:CATRisk)-[:FOR_PERIL]->(peril),
      (first)-[:HOLDS]->(firstPolicy:Policy), (second)-[:HOLDS]->(secondPolicy:Policy)
FILTER first.AccountId < second.AccountId AND firstLoc.CATZone = 'US_GULF'
       AND secondLoc.CATZone = firstLoc.CATZone AND firstPolicy.PolicyYear = 2026 AND secondPolicy.PolicyYear = 2026
RETURN DISTINCT first.AccountName, second.AccountName, firstLoc.CATZone, peril.PerilName,
       firstPolicy.PolicyId, secondPolicy.PolicyId
LIMIT 25
```

---

### 6.4 SQL Endpoint Queries (`CI_Gold_Dev` SQL Analytics Endpoint)

Paste from [`sql/03_underwriting_queries.sql`](sql/03_underwriting_queries.sql) (remember to replace `Accounts`, `Exposures`, etc. with `demo_accounts`, `demo_exposures` if running directly against the Lakehouse SQL endpoint where tables are prefixed with `demo_`):

```sql
SELECT
    f.AccountId,
    a.AccountName,
    f.TIVUSDCents / 100.0 AS CurrentTIV_USD,
    f.PriorTIVUSDCents / 100.0 AS PriorTIV_USD,
    f.AALUSDCents / 100.0 AS CurrentCATAAL_USD,
    f.PriorAALUSDCents / 100.0 AS PriorCATAAL_USD,
    f.IncurredUSDCents / 100.0 AS CurrentIncurred_USD,
    f.PriorIncurredUSDCents / 100.0 AS PriorIncurred_USD,
    f.DaysToRenewal,
    f.OpenCritical,
    p.Pulse AS BaselinePulse
FROM demo_underwritingfeatures f
JOIN demo_accounts a ON f.AccountId = a.AccountId
JOIN demo_riskpulse p ON f.AccountId = p.AccountId
WHERE f.AccountId = 'A001';
```

---

### 6.5 Data Agent Prompts (`CommercialInsuranceDataAgent`)

| # | Prompt to Paste | Expected Grounded Answer & Evidence Keys |
|---:|---|---|
| 1 | `What changed for account A001 before renewal?` | TIV grew `+14%` (`$1.00B -> $1.14B`), CAT AAL grew `+40%` (`$5.0M -> $7.0M`), Incurred loss grew `+40%` (`$5.0M -> $7.0M`), `28` days to renewal, `2` open critical recommendations, baseline pulse `77`. |
| 2 | `What is A001's current TIV, CAT AAL, and incurred loss?` | Current TIV = `$1,140,000,000`, CAT AAL = `$7,000,000`, Incurred Loss = `$7,000,000` (`$3,700,000` paid, `$3,300,000` outstanding), Baseline Pulse = `77.0`. |
| 3 | `Which critical engineering recommendations remain open for A001?` | `RECL001011` (`Firewater pump redundancy`, materiality weight `35`, status `Open`, due `2026-09-01`) and `RECL001012` (`Flood barrier verification`, materiality weight `30`, status `Open`, due `2026-09-01`) at location `L00101` (`Bayport Gulf Coast Works`). |
| 4 | `Which local-program requirements are not aligned for A001?` | Program `MP001`: `REQ00103` / `LP00103` in `SG` (`BIIndemnityMonths = 12` vs `RequiredBIMonths = 18`, status `Review`) and `REQ00104` / `LP00104` in `DE` (`CoverageStatus = 'Wording outstanding'`, status `Review`). |

---

## 7. Customer Q&A, Objection Handling & Governance FAQ

### Q1: "Is the Renewal Risk Pulse an actuarial pricing model or loss-prediction model?"
**Answer:** No—and by design. Actuarial pricing models estimate expected technical loss and rate adequacy under regulatory filing constraints. The Renewal Risk Pulse is a **deterministic triage and prioritization index** (`[0, 100]`) that tells an underwriter *which* near-term renewals experienced material changes across exposure, CAT, claims, engineering, or submission completeness, and *which exact evidence records* to inspect first.

### Q2: "Why store monetary values in integer cents (`*USDCents`) instead of decimal/float?"
**Answer:** Floating-point representations (`IEEE 754`) can introduce rounding drift when aggregating across currencies, exposure layers, and claim valuations (`Paid + Outstanding = Incurred`). Storing integer cents in Bronze/Silver/Gold Delta tables guarantees exact penny reconciliation across Spark, SQL, KQL, and GQL, while our Direct Lake DAX measures divide by `100` for clean dollar presentation.

### Q3: "How do you prevent the AI agent from hallucinating financial numbers?"
**Answer:** Three layers of defense:
1. `CommercialInsuranceDataAgent` is grounded in `CommercialInsuranceIQModel` (which has `discourageImplicitMeasures` enabled and 30 saved DAX measures) and `CI_Gold_Dev` curated tables.
2. Agent instructions explicitly require referencing saved measures, using `2026-09-14` as the default valuation date, and returning primary-key evidence IDs (`AccountId`, `LocationId`, `ClaimId`, `RecommendationId`, `LocalPolicyId`).
3. Every answer includes the executed DAX/SQL query so an underwriter or auditor can verify provenance in one click.

### Q4: "Why do we need both a Semantic Model (DAX) and a Graph Model (GQL)?"
**Answer:** They solve complementary problems on the **same OneLake Gold tables**:
- **Direct Lake DAX (`CommercialInsuranceIQModel`)** excels at financial aggregations, time-intelligence (`2025-09-14` vs `2026-09-14` YoY comparisons), and portfolio KPIs (`Loss Ratio`, `Premium At Risk`).
- **Fabric Graph (`GQL`)** excels at multi-hop topological pattern matching—such as finding pairs of accounts sharing the same `US_GULF` peril zone on 2026 policies (`Query 5`), or finding accounts with multi-location claims caused by the same peril (`Query 3`), where relational self-joins become brittle.

### Q5: "How does the Ontology connect batch Lakehouse data with real-time Eventhouse streams?"
**Answer:** In `CommercialInsuranceOntology`, the 25 core entities and 30 relationships bind to static Gold Lakehouse tables (`NonTimeSeries`) so the ontology can materialize a full companion Graph. Then, on the `Account` entity, we attach a second **`TimeSeries` data binding** pointing directly to `CI_Underwriting_RTI.UnderwritingEvents` on `EventTime`. That lets `Account` carry both mastered Lakehouse properties and live Eventhouse telemetry.

### Q6: "What happens if duplicate or out-of-order events arrive in Eventhouse?"
**Answer:** Our KQL function `DedupedEvents()` applies three gates before any monitoring query or Operations Agent sees an event:
1. Rejects future timestamps (`EventTime <= now() + 5m`).
2. Deduplicates by `EventId` (`arg_max(ingestion_time(), *) by EventId`).
3. Recomputes `ExpectedPulse` from the seven component columns and drops any row where `abs(Pulse - ExpectedPulse) > 0.05`.

### Q7: "Why is `RenewalRiskOperationsAgent` stopped (`shouldRun = false`) in the workspace?"
**Answer:** In a regulated insurance environment, autonomous alerting or workflow triggers must never fire without approved identity, recipient lists, deduplication windows, and rollback procedures. We deploy the complete agent configuration and KQL evaluation contract (`EvaluationKey = AccountId:RunId:Sequence`), and keep `shouldRun = false` until governance sign-off.

### Q8: "How do you handle unverified broker statements in submissions?"
**Answer:** Look at `demo_submissions` for `A001` (`SUB001`): `BrokerStatement` says *"Bayport flood barrier funded; completion evidence pending"*, and `EvidenceClass` is tagged as **`Broker assertion`** with `Verified = false`. Meanwhile, `demo_engineeringrecommendations` (`RECL001012`) shows `ClosureEvidence = 'Not received'` and `Status = 'Open'`. The pulse and signals rely on verified engineering status, while surfacing the broker assertion side-by-side so the underwriter knows what to request from the broker.

---

## 8. Live Demo Recovery & Troubleshooting Playbook

| Symptom During Live Demo | Immediate 15-Second Recovery |
|---|---|
| **Fabric reports `Only 20 items can be opened at one time`** | Close any finished notebook tabs using the `X` on the tab bar inside Fabric, then click the target item once. Keep only the 6 core tabs from Section 3.2 open. |
| **Capacity was paused just before the meeting** | Run `az resource invoke-action --action resume --ids /subscriptions/722484ce-cab9-40aa-9c34-4bee6e5bfecf/resourceGroups/McapsGovernance/providers/Microsoft.Fabric/capacities/nederd --api-version 2023-11-01`. While it warms up (60–90 seconds), walk through Slides 1–8 in the PowerPoint deck. |
| **You want to trigger a brand-new live `77 -> 83` crossing during the call** | In `CI_Underwriting_RTI` KQL query pane, ingest a fresh `RunId` pair (for example `live-demo-002`) or run `07_live_demo_events.ipynb` with `RUN_ID = 'live-demo-002'` for `baseline` and `update`, then filter the KQL crossing query to `RunId == 'live-demo-002'`. The pre-seeded `RunId == 'deployed-001'` is always available as an instant zero-wait proof. |
| **GQL query editor is in visual builder mode instead of code mode** | In the Graph queryset toolbar, click **Query builder -> Code editor**, paste the query from Section 6.3, and click **Run query**. |
| **Need to re-verify all Fabric IQ items via CLI before a customer session** | Run `python .\deployment\deploy_iq.py --workspace-id fef80264-9f1f-4160-b8c8-8e3bf1de7e14 --gold-id 726a950f-970a-487c-a75e-555a3b2cfbff --kql-db-id 68c7a3a6-1a9a-4c40-942f-dce52d3d9205` and `python .\deployment\deploy_graph.py --workspace-id fef80264-9f1f-4160-b8c8-8e3bf1de7e14 --gold-id 726a950f-970a-487c-a75e-555a3b2cfbff --refresh --verify`. |
