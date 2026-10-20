SET NOCOUNT ON;

CREATE TABLE dbo.[Countries] ([CountryId] varchar(250) NULL, [CountryName] varchar(250) NULL, [Region] varchar(250) NULL, [Currency] varchar(250) NULL, [FXToUSD] float NULL, [FXDate] date NULL);

CREATE TABLE dbo.[Industries] ([IndustryId] varchar(250) NULL, [IndustryName] varchar(250) NULL, [Classification] varchar(250) NULL);

CREATE TABLE dbo.[Perils] ([PerilId] varchar(250) NULL, [PerilName] varchar(250) NULL);

CREATE TABLE dbo.[Brokers] ([BrokerId] varchar(250) NULL, [BrokerName] varchar(250) NULL);

CREATE TABLE dbo.[Underwriters] ([UnderwriterId] varchar(250) NULL, [UnderwriterName] varchar(250) NULL, [Region] varchar(250) NULL, [AuthorityUSDCents] bigint NULL);

CREATE TABLE dbo.[Accounts] ([AccountId] varchar(250) NULL, [AccountName] varchar(250) NULL, [BrokerId] varchar(250) NULL, [UnderwriterId] varchar(250) NULL, [IndustryId] varchar(250) NULL, [Region] varchar(250) NULL, [DomicileCountryId] varchar(250) NULL, [RelationshipSince] bigint NULL, [Currency] varchar(250) NULL);

CREATE TABLE dbo.[Renewals] ([RenewalId] varchar(250) NULL, [AccountId] varchar(250) NULL, [RenewalDate] date NULL, [ReviewStatus] varchar(250) NULL, [MissingItems] bigint NULL, [RequiredItems] bigint NULL, [ExpiringPolicyId] varchar(250) NULL, [TargetRateChange] float NULL);

CREATE TABLE dbo.[Policies] ([PolicyId] varchar(250) NULL, [AccountId] varchar(250) NULL, [PolicyYear] bigint NULL, [EffectiveDate] date NULL, [ExpiryDate] date NULL, [WrittenUSDCents] bigint NULL, [EarnedUSDCents] bigint NULL, [LimitUSDCents] bigint NULL, [RetentionUSDCents] bigint NULL, [Currency] varchar(250) NULL, [ValuationDate] date NULL, [Placement] varchar(250) NULL);

CREATE TABLE dbo.[PolicyValuations] ([PolicyValuationId] varchar(250) NULL, [PolicyId] varchar(250) NULL, [AccountId] varchar(250) NULL, [SnapshotDate] date NULL, [WrittenUSDCents] bigint NULL, [EarnedUSDCents] bigint NULL);

CREATE TABLE dbo.[Coverages] ([CoverageId] varchar(250) NULL, [PolicyId] varchar(250) NULL, [CoverageName] varchar(250) NULL, [SublimitUSDCents] bigint NULL, [WaitingHours] bigint NULL, [SharesPolicyAggregate] bit NULL);

CREATE TABLE dbo.[MultinationalPrograms] ([ProgramId] varchar(250) NULL, [AccountId] varchar(250) NULL, [MasterPolicyId] varchar(250) NULL, [ProgramName] varchar(250) NULL, [DICDIL] varchar(250) NULL);

CREATE TABLE dbo.[Submissions] ([SubmissionId] varchar(250) NULL, [AccountId] varchar(250) NULL, [BrokerId] varchar(250) NULL, [ReceivedDate] date NULL, [DocumentRef] varchar(250) NULL, [BrokerStatement] varchar(250) NULL, [EvidenceClass] varchar(250) NULL, [Verified] bit NULL);

CREATE TABLE dbo.[Insureds] ([InsuredId] varchar(250) NULL, [AccountId] varchar(250) NULL, [LegalName] varchar(250) NULL, [CountryId] varchar(250) NULL);

CREATE TABLE dbo.[Locations] ([LocationId] varchar(250) NULL, [AccountId] varchar(250) NULL, [InsuredId] varchar(250) NULL, [LocationName] varchar(250) NULL, [CountryId] varchar(250) NULL, [Latitude] float NULL, [Longitude] float NULL, [CATZone] varchar(250) NULL, [Occupancy] varchar(250) NULL, [BIIndemnityMonths] bigint NULL, [TIVUSDCents] bigint NULL, [PriorTIVUSDCents] bigint NULL, [SnapshotDate] date NULL);

CREATE TABLE dbo.[Assets] ([AssetId] varchar(250) NULL, [LocationId] varchar(250) NULL, [AssetName] varchar(250) NULL, [ReplacementUSDCents] bigint NULL, [LeadTimeMonths] bigint NULL);

CREATE TABLE dbo.[LocalPolicies] ([LocalPolicyId] varchar(250) NULL, [ProgramId] varchar(250) NULL, [CountryId] varchar(250) NULL, [InsuredId] varchar(250) NULL, [EffectiveDate] date NULL, [ExpiryDate] date NULL, [Currency] varchar(250) NULL, [LimitLocal] bigint NULL, [LimitUSDCents] bigint NULL, [BIIndemnityMonths] bigint NULL, [CoverageStatus] varchar(250) NULL, [PremiumIncludedInMaster] bit NULL);

CREATE TABLE dbo.[ProgramRequirements] ([RequirementId] varchar(250) NULL, [ProgramId] varchar(250) NULL, [CountryId] varchar(250) NULL, [RequiredBIMonths] bigint NULL, [LocalPolicyId] varchar(250) NULL, [Status] varchar(250) NULL);

CREATE TABLE dbo.[Exposures] ([ExposureId] varchar(250) NULL, [LocationId] varchar(250) NULL, [AccountId] varchar(250) NULL, [SnapshotDate] date NULL, [ExposureType] varchar(250) NULL, [ValueUSDCents] bigint NULL, [ValueBasis] varchar(250) NULL);

CREATE TABLE dbo.[CATRisk] ([CATId] varchar(250) NULL, [LocationId] varchar(250) NULL, [AccountId] varchar(250) NULL, [PerilId] varchar(250) NULL, [SnapshotDate] date NULL, [AALUSDCents] bigint NULL, [Score] bigint NULL, [Severity] varchar(250) NULL, [ModelVersion] varchar(250) NULL, [FinancialBasis] varchar(250) NULL, [IsCurrent] bit NULL);

CREATE TABLE dbo.[EngineeringInspections] ([InspectionId] varchar(250) NULL, [LocationId] varchar(250) NULL, [InspectionDate] date NULL, [Inspector] varchar(250) NULL, [ReportRef] varchar(250) NULL);

CREATE TABLE dbo.[EngineeringRecommendations] ([RecommendationId] varchar(250) NULL, [InspectionId] varchar(250) NULL, [LocationId] varchar(250) NULL, [AccountId] varchar(250) NULL, [Title] varchar(250) NULL, [MaterialityWeight] bigint NULL, [Status] varchar(250) NULL, [IsCritical] bit NULL, [DueDate] date NULL, [ClosureDate] date NULL, [ClosureEvidence] varchar(250) NULL);

CREATE TABLE dbo.[LossEvents] ([LossEventId] varchar(250) NULL, [PerilId] varchar(250) NULL, [EventName] varchar(250) NULL, [EventDate] date NULL);

CREATE TABLE dbo.[Claims] ([ClaimId] varchar(250) NULL, [AccountId] varchar(250) NULL, [LocationId] varchar(250) NULL, [PolicyId] varchar(250) NULL, [CoverageId] varchar(250) NULL, [LossEventId] varchar(250) NULL, [LossDate] date NULL, [ReportDate] date NULL, [LossType] varchar(250) NULL, [PerilId] varchar(250) NULL, [Status] varchar(250) NULL, [PaidUSDCents] bigint NULL, [OutstandingUSDCents] bigint NULL, [IncurredUSDCents] bigint NULL, [SnapshotDate] date NULL, [ClosureDate] date NULL);

CREATE TABLE dbo.[ClaimValuations] ([ClaimValuationId] varchar(250) NULL, [ClaimId] varchar(250) NULL, [AccountId] varchar(250) NULL, [PolicyId] varchar(250) NULL, [LocationId] varchar(250) NULL, [SnapshotDate] date NULL, [IncurredUSDCents] bigint NULL, [PaidUSDCents] bigint NULL, [OutstandingUSDCents] bigint NULL);

CREATE TABLE dbo.[UnderwritingFeatures] ([AccountId] varchar(250) NULL, [SnapshotDate] date NULL, [TIVUSDCents] bigint NULL, [PriorTIVUSDCents] bigint NULL, [AALUSDCents] bigint NULL, [PriorAALUSDCents] bigint NULL, [IncurredUSDCents] bigint NULL, [PriorIncurredUSDCents] bigint NULL, [TIVGrowth] float NULL, [CATGrowth] float NULL, [ClaimsGrowth] float NULL, [DaysToRenewal] bigint NULL, [OpenCritical] bigint NULL, [CAT] float NULL, [Claims] float NULL, [Growth] float NULL, [Engineering] float NULL, [Concentration] float NULL, [Missing] float NULL, [Proximity] float NULL);

CREATE TABLE dbo.[RiskPulse] ([PulseId] varchar(250) NULL, [AccountId] varchar(250) NULL, [SnapshotDate] date NULL, [Pulse] float NULL, [CAT] float NULL, [Claims] float NULL, [Growth] float NULL, [Engineering] float NULL, [Concentration] float NULL, [Missing] float NULL, [Proximity] float NULL);

CREATE TABLE dbo.[RenewalSignals] ([SignalId] varchar(250) NULL, [RenewalId] varchar(250) NULL, [AccountId] varchar(250) NULL, [SignalType] varchar(250) NULL, [Value] float NULL, [Threshold] float NULL, [Materiality] varchar(250) NULL, [SourceTable] varchar(250) NULL, [DetectedDate] date NULL, [EvidenceKey] varchar(250) NULL);

CREATE TABLE dbo.[PricingScenarios] ([ScenarioId] varchar(250) NULL, [RenewalId] varchar(250) NULL, [AccountId] varchar(250) NULL, [ScenarioName] varchar(250) NULL, [RateChange] float NULL, [CATLoad] float NULL, [EngineeringCredit] float NULL, [RetentionUSDCents] bigint NULL, [LimitUSDCents] bigint NULL, [TIVUSDCents] bigint NULL, [BasePremiumUSDCents] bigint NULL, [ExpectedNonCATUSDCents] bigint NULL, [ExpectedCATUSDCents] bigint NULL, [Commission] float NULL, [ExpenseRatio] float NULL, [CapitalUSDCents] bigint NULL, [IndicatedUSDCents] bigint NULL, [ExpectedLR] float NULL, [ExpectedMargin] float NULL, [RiskAdjustedReturn] float NULL, [Attractiveness] float NULL, [Status] varchar(250) NULL, [LossFactorBasis] varchar(250) NULL);

CREATE TABLE dbo.[UnderwritingDecisions] ([DecisionId] varchar(250) NULL, [RenewalId] varchar(250) NULL, [AccountId] varchar(250) NULL, [Posture] varchar(250) NULL, [Approved] bit NULL, [ApprovedBy] varchar(250) NULL, [Rationale] varchar(250) NULL);

CREATE TABLE dbo.[UnderwritingEvents] ([EventId] varchar(250) NULL, [AccountId] varchar(250) NULL, [RunId] varchar(250) NULL, [Sequence] bigint NULL, [EventTime] datetime2(6) NULL, [EventType] varchar(250) NULL, [SourceVersion] varchar(250) NULL, [BusinessAsOf] date NULL, [CAT] float NULL, [Claims] float NULL, [Growth] float NULL, [Engineering] float NULL, [Concentration] float NULL, [Missing] float NULL, [Proximity] float NULL, [Pulse] float NULL, [DaysToRenewal] bigint NULL, [OpenCritical] bigint NULL, [ReserveChangePct] float NULL, [ExposureChangePct] float NULL, [LocationId] varchar(250) NULL, [EvidenceRef] varchar(250) NULL);

CREATE TABLE dbo.[Calendar] ([Date] date NULL, [Year] bigint NULL, [Month] bigint NULL, [MonthName] varchar(250) NULL);