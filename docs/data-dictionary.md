# Source Data Dictionary

Generated from the same schema as CSV and SQL. All data is synthetic. IDs are stable strings; all USD monetary fields are integer cents. Nullable fields are explicit. Table grains and business usage are described in the architecture document.

## Countries
Key: `CountryId`. Rows: 10.

| Column | Example |
|---|---|
| CountryId | US |
| CountryName | United States |
| Region | Americas |
| Currency | USD |
| FXToUSD | 1.0 |
| FXDate | 2026-09-14 |

## Industries
Key: `IndustryId`. Rows: 5.

| Column | Example |
|---|---|
| IndustryId | 325 |
| IndustryName | Specialty chemicals |
| Classification | NAICS demo grouping |

## Perils
Key: `PerilId`. Rows: 4.

| Column | Example |
|---|---|
| PerilId | PER1 |
| PerilName | Windstorm |

## Brokers
Key: `BrokerId`. Rows: 5.

| Column | Example |
|---|---|
| BrokerId | B01 |
| BrokerName | Northstar Risk Partners |

## Underwriters
Key: `UnderwriterId`. Rows: 8.

| Column | Example |
|---|---|
| UnderwriterId | UW01 |
| UnderwriterName | Demo Underwriter 1 |
| Region | Americas |
| AuthorityUSDCents | 2500000000 |

## Accounts
Key: `AccountId`. Rows: 20.

| Column | Example |
|---|---|
| AccountId | A001 |
| AccountName | Meridian Specialty Chemicals |
| BrokerId | B01 |
| UnderwriterId | UW01 |
| IndustryId | 325 |
| Region | Americas |
| DomicileCountryId | US |
| RelationshipSince | 2013 |
| Currency | USD |

## Renewals
Key: `RenewalId`. Rows: 20.

| Column | Example |
|---|---|
| RenewalId | R001 |
| AccountId | A001 |
| RenewalDate | 2026-10-12 |
| ReviewStatus | In review |
| MissingItems | 3 |
| RequiredItems | 5 |
| ExpiringPolicyId | P00126 |
| TargetRateChange | 0.06 |

## Policies
Key: `PolicyId`. Rows: 40.

| Column | Example |
|---|---|
| PolicyId | P00125 |
| AccountId | A001 |
| PolicyYear | 2025 |
| EffectiveDate | 2024-10-12 |
| ExpiryDate | 2025-10-12 |
| WrittenUSDCents | 1698113200 |
| EarnedUSDCents | 1567847000 |
| LimitUSDCents | 25000000000 |
| RetentionUSDCents | 200000000 |
| Currency | USD |
| ValuationDate | 2025-09-14 |
| Placement | Master |

## PolicyValuations
Key: `PolicyValuationId`. Rows: 60.

| Column | Example |
|---|---|
| PolicyValuationId | P001252025 |
| PolicyId | P00125 |
| AccountId | A001 |
| SnapshotDate | 2025-09-14 |
| WrittenUSDCents | 1698113200 |
| EarnedUSDCents | 1567847000 |

## Coverages
Key: `CoverageId`. Rows: 120.

| Column | Example |
|---|---|
| CoverageId | P00125C1 |
| PolicyId | P00125 |
| CoverageName | Property damage |
| SublimitUSDCents | 25000000000 |
| WaitingHours | 0 |
| SharesPolicyAggregate | True |

## MultinationalPrograms
Key: `ProgramId`. Rows: 20.

| Column | Example |
|---|---|
| ProgramId | MP001 |
| AccountId | A001 |
| MasterPolicyId | P00126 |
| ProgramName | Meridian Specialty Chemicals Global Property |
| DICDIL | Subject to wording review |

## Submissions
Key: `SubmissionId`. Rows: 20.

| Column | Example |
|---|---|
| SubmissionId | SUB001 |
| AccountId | A001 |
| BrokerId | B01 |
| ReceivedDate | 2026-09-01 |
| DocumentRef | DOC001 |
| BrokerStatement | Bayport flood barrier funded; completion evidence pending. Rotterdam suppression upgrade verified. |
| EvidenceClass | Broker assertion |
| Verified | False |

## Insureds
Key: `InsuredId`. Rows: 100.

| Column | Example |
|---|---|
| InsuredId | I00101 |
| AccountId | A001 |
| LegalName | Meridian Specialty Chemicals US Ltd |
| CountryId | US |

## Locations
Key: `LocationId`. Rows: 100.

| Column | Example |
|---|---|
| LocationId | L00101 |
| AccountId | A001 |
| InsuredId | I00101 |
| LocationName | Bayport Gulf Coast Works |
| CountryId | US |
| Latitude | 29.72 |
| Longitude | -95.02 |
| CATZone | US_GULF |
| Occupancy | Manufacturing |
| BIIndemnityMonths | 18 |
| TIVUSDCents | 72960000000 |
| PriorTIVUSDCents | 60000000000 |
| SnapshotDate | 2026-09-14 |

## Assets
Key: `AssetId`. Rows: 100.

| Column | Example |
|---|---|
| AssetId | AST00101 |
| LocationId | L00101 |
| AssetName | Critical production train |
| ReplacementUSDCents | 13132800000 |
| LeadTimeMonths | 12 |

## LocalPolicies
Key: `LocalPolicyId`. Rows: 100.

| Column | Example |
|---|---|
| LocalPolicyId | LP00101 |
| ProgramId | MP001 |
| CountryId | US |
| InsuredId | I00101 |
| EffectiveDate | 2025-10-12 |
| ExpiryDate | 2026-10-12 |
| Currency | USD |
| LimitLocal | 50000000 |
| LimitUSDCents | 5000000000 |
| BIIndemnityMonths | 18 |
| CoverageStatus | Confirmed |
| PremiumIncludedInMaster | True |

## ProgramRequirements
Key: `RequirementId`. Rows: 100.

| Column | Example |
|---|---|
| RequirementId | REQ00101 |
| ProgramId | MP001 |
| CountryId | US |
| RequiredBIMonths | 18 |
| LocalPolicyId | LP00101 |
| Status | Aligned |

## Exposures
Key: `ExposureId`. Rows: 400.

| Column | Example |
|---|---|
| ExposureId | L001012025Property |
| LocationId | L00101 |
| AccountId | A001 |
| SnapshotDate | 2025-09-14 |
| ExposureType | Property |
| ValueUSDCents | 45000000000 |
| ValueBasis | Declared value, USD constant FX |

## CATRisk
Key: `CATId`. Rows: 400.

| Column | Example |
|---|---|
| CATId | CATL0010120251 |
| LocationId | L00101 |
| AccountId | A001 |
| PerilId | PER1 |
| SnapshotDate | 2025-09-14 |
| AALUSDCents | 266000000 |
| Score | 95 |
| Severity | Severe |
| ModelVersion | DemoCAT-4.1 |
| FinancialBasis | Ground-up AAL; disjoint peril components |
| IsCurrent | False |

## EngineeringInspections
Key: `InspectionId`. Rows: 100.

| Column | Example |
|---|---|
| InspectionId | INSP00101 |
| LocationId | L00101 |
| InspectionDate | 2026-07-15 |
| Inspector | Synthetic Engineering Services |
| ReportRef | ER-L00101 |

## EngineeringRecommendations
Key: `RecommendationId`. Rows: 99.

| Column | Example |
|---|---|
| RecommendationId | RECL001011 |
| InspectionId | INSP00101 |
| LocationId | L00101 |
| AccountId | A001 |
| Title | Firewater pump redundancy |
| MaterialityWeight | 35 |
| Status | Open |
| IsCritical | True |
| DueDate | 2026-09-01 |
| ClosureDate | None |
| ClosureEvidence | Not received |

## LossEvents
Key: `LossEventId`. Rows: 80.

| Column | Example |
|---|---|
| LossEventId | LE00101 |
| PerilId | PER2 |
| EventName | Synthetic PER2 incident 1-1 |
| EventDate | 2025-02-15 |

## Claims
Key: `ClaimId`. Rows: 80.

| Column | Example |
|---|---|
| ClaimId | CL00101 |
| AccountId | A001 |
| LocationId | L00101 |
| PolicyId | P00125 |
| CoverageId | P00125C1 |
| LossEventId | LE00101 |
| LossDate | 2025-02-15 |
| ReportDate | 2025-02-17 |
| LossType | Property |
| PerilId | PER2 |
| Status | Open |
| PaidUSDCents | 140000000 |
| OutstandingUSDCents | 210000000 |
| IncurredUSDCents | 350000000 |
| SnapshotDate | 2026-09-14 |
| ClosureDate | None |

## ClaimValuations
Key: `ClaimValuationId`. Rows: 160.

| Column | Example |
|---|---|
| ClaimValuationId | CL001012025 |
| ClaimId | CL00101 |
| AccountId | A001 |
| PolicyId | P00125 |
| LocationId | L00101 |
| SnapshotDate | 2025-09-14 |
| IncurredUSDCents | 200000000 |
| PaidUSDCents | 60000000 |
| OutstandingUSDCents | 140000000 |

## UnderwritingFeatures
Key: `AccountId`. Rows: 20.

| Column | Example |
|---|---|
| AccountId | A001 |
| SnapshotDate | 2026-09-14 |
| TIVUSDCents | 114000000000 |
| PriorTIVUSDCents | 100000000000 |
| AALUSDCents | 700000000 |
| PriorAALUSDCents | 500000000 |
| IncurredUSDCents | 700000000 |
| PriorIncurredUSDCents | 500000000 |
| TIVGrowth | 0.14 |
| CATGrowth | 0.4 |
| ClaimsGrowth | 0.4 |
| DaysToRenewal | 28 |
| OpenCritical | 2 |
| CAT | 0.7999999999999998 |
| Claims | 0.7999999999999998 |
| Growth | 0.6999999999999995 |
| Engineering | 0.85 |
| Concentration | 0.7999999999999999 |
| Missing | 0.6 |
| Proximity | 0.6 |

## RiskPulse
Key: `PulseId`. Rows: 20.

| Column | Example |
|---|---|
| PulseId | PULSEA001 |
| AccountId | A001 |
| SnapshotDate | 2026-09-14 |
| Pulse | 77.0 |
| CAT | 0.7999999999999998 |
| Claims | 0.7999999999999998 |
| Growth | 0.6999999999999995 |
| Engineering | 0.85 |
| Concentration | 0.7999999999999999 |
| Missing | 0.6 |
| Proximity | 0.6 |

## RenewalSignals
Key: `SignalId`. Rows: 44.

| Column | Example |
|---|---|
| SignalId | SIGA001001 |
| RenewalId | R001 |
| AccountId | A001 |
| SignalType | CAT deterioration |
| Value | 0.4 |
| Threshold | 0.25 |
| Materiality | High |
| SourceTable | CATRisk |
| DetectedDate | 2026-09-14 |
| EvidenceKey | A001 |

## PricingScenarios
Key: `ScenarioId`. Rows: 3.

| Column | Example |
|---|---|
| ScenarioId | SC1 |
| RenewalId | R001 |
| AccountId | A001 |
| ScenarioName | Base Renewal |
| RateChange | 0.06 |
| CATLoad | 0.03 |
| EngineeringCredit | 0.0 |
| RetentionUSDCents | 200000000 |
| LimitUSDCents | 25000000000 |
| TIVUSDCents | 114000000000 |
| BasePremiumUSDCents | 1800000000 |
| ExpectedNonCATUSDCents | 540000000 |
| ExpectedCATUSDCents | 400000000 |
| Commission | 0.15 |
| ExpenseRatio | 0.12 |
| CapitalUSDCents | 4000000000 |
| IndicatedUSDCents | 1962000000 |
| ExpectedLR | 0.47910295616717635 |
| ExpectedMargin | 0.25089704383282363 |
| RiskAdjustedReturn | 0.123065 |
| Attractiveness | 73.3 |
| Status | Illustrative - not approved |
| LossFactorBasis | Assumed net insurer loss factor; requires actuarial validation |

## UnderwritingDecisions
Key: `DecisionId`. Rows: 1.

| Column | Example |
|---|---|
| DecisionId | DEC001 |
| RenewalId | R001 |
| AccountId | A001 |
| Posture | Retain subject to evidence and authority referral |
| Approved | False |
| ApprovedBy | None |
| Rationale | Compound Bayport risk; verified Rotterdam control and closed claims support differentiated terms. |

## UnderwritingEvents
Key: `EventId`. Rows: 31.

| Column | Example |
|---|---|
| EventId | BASE000 |
| AccountId | A001 |
| RunId | baseline |
| Sequence | 1 |
| EventTime | 2026-09-14T09:00:00Z |
| EventType | Snapshot |
| SourceVersion | demo-v1 |
| BusinessAsOf | 2026-09-14 |
| CAT | 0.8 |
| Claims | 0.8 |
| Growth | 0.7 |
| Engineering | 0.85 |
| Concentration | 0.8 |
| Missing | 0.6 |
| Proximity | 0.6 |
| Pulse | 77.0 |
| DaysToRenewal | 28 |
| OpenCritical | 2 |
| ReserveChangePct | 0.0 |
| ExposureChangePct | 0.14 |
| LocationId | L00101 |
| EvidenceRef | UnderwritingFeatures/A001 |

## Calendar
Key: `Date`. Rows: 1461.

| Column | Example |
|---|---|
| Date | 2024-01-01 |
| Year | 2024 |
| Month | 1 |
| MonthName | Jan |
