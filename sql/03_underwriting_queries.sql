DECLARE @AsOf date = '2026-09-14';
DECLARE @AccountId varchar(250) = 'A001';

SELECT account.AccountName, broker.BrokerName, renewal.RenewalDate, feature.*,
       pulse.Pulse, policy.WrittenUSDCents / 100.0 AS ExpiringPremiumUSD
FROM dbo.Accounts account
JOIN dbo.Brokers broker ON broker.BrokerId = account.BrokerId
JOIN dbo.Renewals renewal ON renewal.AccountId = account.AccountId
JOIN dbo.UnderwritingFeatures feature ON feature.AccountId = account.AccountId
JOIN dbo.RiskPulse pulse ON pulse.AccountId = account.AccountId
JOIN dbo.Policies policy ON policy.PolicyId = renewal.ExpiringPolicyId
WHERE account.AccountId = @AccountId;

SELECT TOP (5) account.AccountName, renewal.RenewalDate, pulse.Pulse,
       policy.WrittenUSDCents / 100.0 AS PremiumAtRiskUSD
FROM dbo.Accounts account
JOIN dbo.Renewals renewal ON renewal.AccountId = account.AccountId
JOIN dbo.RiskPulse pulse ON pulse.AccountId = account.AccountId
JOIN dbo.Policies policy ON policy.PolicyId = renewal.ExpiringPolicyId
WHERE renewal.RenewalDate >= @AsOf AND renewal.RenewalDate < DATEADD(day, 91, @AsOf)
ORDER BY pulse.Pulse DESC, policy.WrittenUSDCents DESC, account.AccountId;

SELECT claim.LocationId, location.LocationName, COUNT(*) AS ClaimCount,
       SUM(claim.IncurredUSDCents) / 100.0 AS IncurredUSD,
       SUM(claim.PaidUSDCents) / 100.0 AS PaidUSD,
       SUM(claim.OutstandingUSDCents) / 100.0 AS OutstandingUSD
FROM dbo.Claims claim
JOIN dbo.Locations location ON location.LocationId = claim.LocationId
WHERE claim.AccountId = @AccountId
GROUP BY claim.LocationId, location.LocationName
ORDER BY IncurredUSD DESC;

WITH cat AS (
    SELECT LocationId, SUM(AALUSDCents) AS AALUSDCents
    FROM dbo.CATRisk WHERE SnapshotDate = @AsOf GROUP BY LocationId
)
SELECT location.CATZone, COUNT(*) AS Locations,
       SUM(location.TIVUSDCents) / 100.0 AS TIVUSD, SUM(cat.AALUSDCents) / 100.0 AS GroundUpAALUSD
FROM dbo.Locations location JOIN cat ON cat.LocationId = location.LocationId
GROUP BY location.CATZone ORDER BY GroundUpAALUSD DESC;

SELECT location.LocationName, recommendation.RecommendationId, recommendation.Title,
       recommendation.Status, recommendation.IsCritical, recommendation.DueDate,
       recommendation.MaterialityWeight, recommendation.ClosureEvidence
FROM dbo.EngineeringRecommendations recommendation
JOIN dbo.Locations location ON location.LocationId = recommendation.LocationId
WHERE recommendation.AccountId = @AccountId
ORDER BY recommendation.MaterialityWeight DESC;

SELECT broker.BrokerName, location.CATZone, COUNT(DISTINCT account.AccountId) AS Accounts,
       SUM(location.TIVUSDCents) / 100.0 AS TIVUSD
FROM dbo.Brokers broker
JOIN dbo.Accounts account ON account.BrokerId = broker.BrokerId
JOIN dbo.Locations location ON location.AccountId = account.AccountId
GROUP BY broker.BrokerName, location.CATZone ORDER BY TIVUSD DESC;

SELECT program.ProgramName, requirement.CountryId, requirement.RequiredBIMonths,
       localpolicy.LocalPolicyId, localpolicy.BIIndemnityMonths, localpolicy.CoverageStatus,
       CASE WHEN localpolicy.LocalPolicyId IS NULL THEN 'Missing local policy'
            WHEN localpolicy.BIIndemnityMonths < requirement.RequiredBIMonths THEN 'BI mismatch'
            WHEN localpolicy.CoverageStatus <> 'Confirmed' THEN 'Wording evidence missing'
            ELSE 'Aligned' END AS Finding
FROM dbo.MultinationalPrograms program
JOIN dbo.ProgramRequirements requirement ON requirement.ProgramId = program.ProgramId
LEFT JOIN dbo.LocalPolicies localpolicy ON localpolicy.LocalPolicyId = requirement.LocalPolicyId
WHERE program.AccountId = @AccountId
ORDER BY requirement.CountryId;

SELECT AccountId, TIVUSDCents / 100.0 AS TIVUSD, PriorTIVUSDCents / 100.0 AS PriorTIVUSD,
       TIVGrowth, AALUSDCents / 100.0 AS AALUSD, CATGrowth,
       IncurredUSDCents / 100.0 AS IncurredUSD, ClaimsGrowth, OpenCritical
FROM dbo.UnderwritingFeatures WHERE AccountId = @AccountId;

WITH losses AS (
    SELECT AccountId, PolicyId, SnapshotDate, SUM(IncurredUSDCents) AS Incurred
    FROM dbo.ClaimValuations GROUP BY AccountId, PolicyId, SnapshotDate
)
SELECT premium.AccountId, policy.PolicyYear, premium.SnapshotDate,
       COALESCE(losses.Incurred, 0) / 100.0 AS IncurredUSD,
       premium.EarnedUSDCents / 100.0 AS EarnedUSD,
       COALESCE(losses.Incurred, 0) * 1.0 / NULLIF(premium.EarnedUSDCents, 0) AS LossRatio
FROM dbo.PolicyValuations premium
JOIN dbo.Policies policy ON policy.PolicyId = premium.PolicyId
LEFT JOIN losses ON losses.PolicyId = premium.PolicyId AND losses.SnapshotDate = premium.SnapshotDate
WHERE premium.AccountId = @AccountId AND policy.PolicyYear = 2025
ORDER BY premium.SnapshotDate;