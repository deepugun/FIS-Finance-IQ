from __future__ import annotations

import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AS_OF = date(2026, 9, 14)
PRIOR = date(2025, 9, 14)
ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"CAT": 25, "Claims": 20, "Growth": 10, "Engineering": 20,
           "Concentration": 10, "Missing": 10, "Proximity": 5}


def cents(dollars: float) -> int:
    return round(dollars * 100)


def clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def pulse(components: dict) -> float:
    return round(sum(WEIGHTS[name] * clamp(components[name]) for name in WEIGHTS), 2)


def build_data() -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}

    def add(table: str, **row):
        tables.setdefault(table, []).append(row)

    countries = [
        ("US", "United States", "Americas", "USD", 1.0),
        ("NL", "Netherlands", "EMEA", "EUR", 1.10),
        ("SG", "Singapore", "APAC", "SGD", 0.75),
        ("DE", "Germany", "EMEA", "EUR", 1.10),
        ("GB", "United Kingdom", "EMEA", "GBP", 1.30),
        ("JP", "Japan", "APAC", "JPY", 0.007),
        ("AU", "Australia", "APAC", "AUD", 0.67),
        ("CA", "Canada", "Americas", "CAD", 0.74),
        ("BR", "Brazil", "Americas", "BRL", 0.20),
        ("FR", "France", "EMEA", "EUR", 1.10),
    ]
    for code, name, region, currency, rate in countries:
        add("Countries", CountryId=code, CountryName=name, Region=region,
            Currency=currency, FXToUSD=rate, FXDate=AS_OF.isoformat())
    industries = [("325", "Specialty chemicals"), ("311", "Food manufacturing"),
                  ("336", "Transport equipment"), ("493", "Warehousing"), ("334", "Electronics")]
    for code, name in industries:
        add("Industries", IndustryId=code, IndustryName=name, Classification="NAICS demo grouping")
    for position, name in enumerate(["Windstorm", "Flood", "Fire", "Machinery breakdown"], 1):
        add("Perils", PerilId=f"PER{position}", PerilName=name)
    broker_names = ["Northstar Risk Partners", "Atlas Commercial", "Pinnacle Global Risk",
                    "Harbor Insurance Advisory", "Summit Specialty"]
    for number, name in enumerate(broker_names, 1):
        add("Brokers", BrokerId=f"B{number:02}", BrokerName=name)
    for number in range(1, 9):
        add("Underwriters", UnderwriterId=f"UW{number:02}", UnderwriterName=f"Demo Underwriter {number}",
            Region=["Americas", "EMEA", "APAC"][(number - 1) % 3], AuthorityUSDCents=cents(25_000_000))
    names = ["Meridian Specialty Chemicals", "Aquila Food Systems", "Cobalt Components",
             "Crestline Logistics", "Vector Microdevices", "Orion Industrial Resins",
             "Northfield Nutrition", "Terra Mobility", "Westhaven Storage", "Helix Instruments",
             "Solstice Materials", "Juniper Foods", "Aurora Fabrication", "Keystone Distribution",
             "Lumen Circuits", "Arcadia Polymers", "Evergreen Ingredients", "Civic Rail Systems",
             "Bluewater Warehousing", "Zenith Controls"]
    hero_names = ["Bayport Gulf Coast Works", "Rotterdam Specialty Works", "Jurong Blending",
                  "Ludwigshafen Distribution", "Manchester Technical Centre"]
    hero_tiv = [729_600_000, 180_000_000, 110_000_000, 80_000_000, 40_400_000]
    hero_prior = [600_000_000, 180_000_000, 100_000_000, 80_000_000, 40_000_000]
    hero_cat = [5_800_000, 300_000, 400_000, 300_000, 200_000]
    hero_cat_prior = [3_800_000, 400_000, 350_000, 250_000, 200_000]
    coordinates = [(29.72, -95.02), (51.92, 4.48), (1.33, 103.71), (49.48, 8.44), (53.48, -2.24),
                   (35.68, 139.69), (-33.87, 151.21), (43.65, -79.38), (-23.55, -46.63), (48.86, 2.35)]
    for account_number, account_name in enumerate(names, 1):
        account_id = f"A{account_number:03}"
        broker_id = f"B{((account_number - 1) % 5) + 1:02}"
        industry_id = industries[(account_number - 1) % 5][0]
        add("Accounts", AccountId=account_id, AccountName=account_name, BrokerId=broker_id,
            UnderwriterId=f"UW{((account_number - 1) % 8) + 1:02}", IndustryId=industry_id,
            Region="Americas" if account_number == 1 else countries[account_number % 10][2],
            DomicileCountryId="US" if account_number == 1 else countries[account_number % 10][0],
            RelationshipSince=2012 + account_number % 9, Currency="USD")
        renewal_date = AS_OF + timedelta(days=28 if account_number == 1 else 10 + account_number * 3)
        add("Renewals", RenewalId=f"R{account_number:03}", AccountId=account_id,
            RenewalDate=renewal_date.isoformat(), ReviewStatus="In review", MissingItems=3 if account_number == 1 else account_number % 4,
            RequiredItems=5, ExpiringPolicyId=f"P{account_number:03}26", TargetRateChange=0.06)
        for year in (2025, 2026):
            start = date(year - 1, renewal_date.month, renewal_date.day)
            end = date(year, renewal_date.month, renewal_date.day)
            premium = 18_000_000 if account_number == 1 else 2_000_000 + account_number * 470_000
            if year == 2025:
                premium = round(premium / 1.06)
            valuation = PRIOR if year == 2025 else AS_OF
            earned = round(premium * (valuation - start).days / (end - start).days)
            policy_id = f"P{account_number:03}{str(year)[-2:]}"
            add("Policies", PolicyId=policy_id, AccountId=account_id, PolicyYear=year,
                EffectiveDate=start.isoformat(), ExpiryDate=end.isoformat(), WrittenUSDCents=cents(premium),
                EarnedUSDCents=cents(earned), LimitUSDCents=cents(250_000_000), RetentionUSDCents=cents(2_000_000),
                Currency="USD", ValuationDate=valuation.isoformat(), Placement="Master")
            add("PolicyValuations", PolicyValuationId=f"{policy_id}{valuation.year}", PolicyId=policy_id,
                AccountId=account_id, SnapshotDate=valuation.isoformat(), WrittenUSDCents=cents(premium), EarnedUSDCents=cents(earned))
            if year == 2025:
                add("PolicyValuations", PolicyValuationId=f"{policy_id}2026", PolicyId=policy_id,
                    AccountId=account_id, SnapshotDate=AS_OF.isoformat(), WrittenUSDCents=cents(premium), EarnedUSDCents=cents(premium))
            for coverage_number, coverage in enumerate(["Property damage", "Business interruption", "Machinery breakdown"], 1):
                add("Coverages", CoverageId=f"{policy_id}C{coverage_number}", PolicyId=policy_id,
                    CoverageName=coverage, SublimitUSDCents=cents([250_000_000, 100_000_000, 50_000_000][coverage_number - 1]),
                    WaitingHours=72 if coverage_number == 2 else 0, SharesPolicyAggregate=True)
        add("MultinationalPrograms", ProgramId=f"MP{account_number:03}", AccountId=account_id,
            MasterPolicyId=f"P{account_number:03}26", ProgramName=f"{account_name} Global Property", DICDIL="Subject to wording review")
        add("Submissions", SubmissionId=f"SUB{account_number:03}", AccountId=account_id, BrokerId=broker_id,
            ReceivedDate="2026-09-01", DocumentRef=f"DOC{account_number:03}",
            BrokerStatement="Bayport flood barrier funded; completion evidence pending. Rotterdam suppression upgrade verified."
            if account_number == 1 else "Statement of values and loss run received; validation in progress.",
            EvidenceClass="Broker assertion", Verified=False)
        for location_number in range(1, 6):
            location_id = f"L{account_number:03}{location_number:02}"
            country_index = location_number - 1 if account_number == 1 else (account_number + location_number) % 10
            if account_number in (6, 11, 16) and location_number == 1:
                country_index = 0
            country = countries[country_index]
            latitude, longitude = coordinates[country_index]
            current_tiv = hero_tiv[location_number - 1] if account_number == 1 else 40_000_000 + account_number * 8_000_000 + location_number * 6_000_000
            old_tiv = hero_prior[location_number - 1] if account_number == 1 else round(current_tiv / (1 + (account_number % 8) * 0.035))
            zone = "US_GULF" if country_index == 0 else f"{country[0]}_INDUSTRIAL"
            add("Insureds", InsuredId=f"I{account_number:03}{location_number:02}", AccountId=account_id,
                LegalName=f"{account_name} {country[0]} Ltd", CountryId=country[0])
            add("Locations", LocationId=location_id, AccountId=account_id, InsuredId=f"I{account_number:03}{location_number:02}",
                LocationName=hero_names[location_number - 1] if account_number == 1 else f"{account_name} Facility {location_number}",
                CountryId=country[0], Latitude=latitude, Longitude=longitude, CATZone=zone,
                Occupancy="Manufacturing" if location_number < 4 else "Distribution", BIIndemnityMonths=18,
                TIVUSDCents=cents(current_tiv), PriorTIVUSDCents=cents(old_tiv), SnapshotDate=AS_OF.isoformat())
            add("Assets", AssetId=f"AST{account_number:03}{location_number:02}", LocationId=location_id,
                AssetName="Critical production train", ReplacementUSDCents=cents(current_tiv * 0.18), LeadTimeMonths=12)
            add("LocalPolicies", LocalPolicyId=f"LP{account_number:03}{location_number:02}", ProgramId=f"MP{account_number:03}",
                CountryId=country[0], InsuredId=f"I{account_number:03}{location_number:02}",
                EffectiveDate=date(2025, renewal_date.month, renewal_date.day).isoformat(), ExpiryDate=renewal_date.isoformat(),
                Currency=country[3], LimitLocal=round(50_000_000 / country[4]), LimitUSDCents=cents(50_000_000),
                BIIndemnityMonths=12 if account_number == 1 and location_number == 3 else 18,
                CoverageStatus="Wording outstanding" if account_number == 1 and location_number == 4 else "Confirmed",
                PremiumIncludedInMaster=True)
            add("ProgramRequirements", RequirementId=f"REQ{account_number:03}{location_number:02}",
                ProgramId=f"MP{account_number:03}", CountryId=country[0], RequiredBIMonths=18,
                LocalPolicyId=f"LP{account_number:03}{location_number:02}", Status="Review" if account_number == 1 and location_number in (3, 4) else "Aligned")
            for year, tiv in [(2025, old_tiv), (2026, current_tiv)]:
                snapshot = PRIOR if year == 2025 else AS_OF
                for exposure_type, fraction in [("Property", 0.75), ("BI", 0.25)]:
                    add("Exposures", ExposureId=f"{location_id}{year}{exposure_type}", LocationId=location_id,
                        AccountId=account_id, SnapshotDate=snapshot.isoformat(), ExposureType=exposure_type,
                        ValueUSDCents=cents(tiv * fraction), ValueBasis="Declared value, USD constant FX")
                cat_total = (hero_cat if year == 2026 else hero_cat_prior)[location_number - 1] if account_number == 1 else round(tiv * (0.003 + (account_number % 6) * 0.0007))
                for peril_number, fraction in [(1, 0.7), (2, 0.3)]:
                    add("CATRisk", CATId=f"CAT{location_id}{year}{peril_number}", LocationId=location_id,
                        AccountId=account_id, PerilId=f"PER{peril_number}", SnapshotDate=snapshot.isoformat(),
                        AALUSDCents=cents(cat_total * fraction), Score=95 if zone == "US_GULF" else 25 + account_number % 40,
                        Severity="Severe" if zone == "US_GULF" else "Moderate", ModelVersion="DemoCAT-4.1",
                        FinancialBasis="Ground-up AAL; disjoint peril components", IsCurrent=year == 2026)
            inspection_id = f"INSP{account_number:03}{location_number:02}"
            add("EngineeringInspections", InspectionId=inspection_id, LocationId=location_id,
                InspectionDate="2026-07-15", Inspector="Synthetic Engineering Services", ReportRef=f"ER-{location_id}")
            if account_number == 1 and location_number == 1:
                recommendations = [("Firewater pump redundancy", 35, "Open", True),
                                   ("Flood barrier verification", 30, "Open", True),
                                   ("Roof anchorage survey", 20, "Open", False)]
            elif account_number == 1 and location_number == 2:
                recommendations = [("Suppression upgrade", 15, "Closed", False)]
            elif account_number == 1:
                recommendations = []
            else:
                recommendations = [("Protection testing", 10 + account_number % 4 * 5,
                                    "Closed" if (account_number + location_number) % 3 == 0 else "Open", account_number % 4 == 0)]
            for rec_number, (title, weight, status, critical) in enumerate(recommendations, 1):
                add("EngineeringRecommendations", RecommendationId=f"REC{location_id}{rec_number}", InspectionId=inspection_id,
                    LocationId=location_id, AccountId=account_id, Title=title, MaterialityWeight=weight,
                    Status=status, IsCritical=critical, DueDate="2026-09-01", ClosureDate="2026-08-20" if status == "Closed" else None,
                    ClosureEvidence="Engineer verified" if status == "Closed" else "Not received")
        for claim_number in range(1, 5):
            claim_id = f"CL{account_number:03}{claim_number:02}"
            location_number = [1, 1, 2, 3][claim_number - 1]
            location_id = f"L{account_number:03}{location_number:02}"
            old_loss = [2_000_000, 1_500_000, 1_000_000, 500_000][claim_number - 1] if account_number == 1 else 60_000 + account_number * claim_number * 11_000
            new_loss = [3_500_000, 2_000_000, 1_000_000, 500_000][claim_number - 1] if account_number == 1 else round(old_loss * (1 + (account_number % 7) * 0.10))
            status = "Closed" if claim_number >= 3 else "Open"
            paid = new_loss if status == "Closed" else round(new_loss * 0.4)
            peril_id = ["PER2", "PER4", "PER3", "PER4"][claim_number - 1]
            loss_event = f"LE{account_number:03}{claim_number:02}"
            add("LossEvents", LossEventId=loss_event, PerilId=peril_id,
                EventName=f"Synthetic {peril_id} incident {account_number}-{claim_number}", EventDate=f"2025-0{claim_number + 1}-15")
            add("Claims", ClaimId=claim_id, AccountId=account_id, LocationId=location_id,
                PolicyId=f"P{account_number:03}25", CoverageId=f"P{account_number:03}25C{2 if claim_number == 2 else 3 if claim_number == 4 else 1}",
                LossEventId=loss_event, LossDate=f"2025-0{claim_number + 1}-15", ReportDate=f"2025-0{claim_number + 1}-17",
                LossType="Business interruption" if claim_number == 2 else "Property", PerilId=peril_id,
                Status=status, PaidUSDCents=cents(paid), OutstandingUSDCents=cents(new_loss - paid),
                IncurredUSDCents=cents(new_loss), SnapshotDate=AS_OF.isoformat(),
                ClosureDate="2026-08-15" if status == "Closed" else None)
            for snapshot, amount in [(PRIOR, old_loss), (AS_OF, new_loss)]:
                snapshot_paid = paid if snapshot == AS_OF else round(old_loss * 0.3)
                add("ClaimValuations", ClaimValuationId=f"{claim_id}{snapshot.year}", ClaimId=claim_id,
                    AccountId=account_id, PolicyId=f"P{account_number:03}25", LocationId=location_id,
                    SnapshotDate=snapshot.isoformat(), IncurredUSDCents=cents(amount), PaidUSDCents=cents(snapshot_paid),
                    OutstandingUSDCents=cents(amount - snapshot_paid))
    features = calculate_features(tables)
    tables["UnderwritingFeatures"] = features
    tables["RiskPulse"] = [{"PulseId": f"PULSE{row['AccountId']}", "AccountId": row["AccountId"],
                             "SnapshotDate": AS_OF.isoformat(), "Pulse": pulse(row), **{name: row[name] for name in WEIGHTS}}
                            for row in features]
    for row in features:
        for kind, value, threshold, source in [
            ("CAT deterioration", row["CATGrowth"], 0.25, "CATRisk"),
            ("Claims development", row["ClaimsGrowth"], 0.25, "ClaimValuations"),
            ("Exposure growth", row["TIVGrowth"], 0.20, "Exposures"),
            ("Engineering deficiencies", row["Engineering"], 0.50, "EngineeringRecommendations"),
            ("Missing information", row["Missing"], 0.50, "Renewals")]:
            if value >= threshold:
                add("RenewalSignals", SignalId=f"SIG{row['AccountId']}{len(tables.get('RenewalSignals', [])) + 1:03}",
                    RenewalId=f"R{row['AccountId'][1:]}", AccountId=row["AccountId"], SignalType=kind,
                    Value=round(value, 6), Threshold=threshold, Materiality="High", SourceTable=source,
                    DetectedDate=AS_OF.isoformat(), EvidenceKey=row["AccountId"])
    hero = features[0]
    for index, scenario in enumerate([
        ("Base Renewal", 0.06, 0.03, 0.0, 2_000_000, 250_000_000, 1.0),
        ("CAT Tightening", 0.10, 0.08, 0.0, 5_000_000, 200_000_000, 0.83),
        ("Engineering Credit", 0.06, 0.03, 0.04, 2_000_000, 250_000_000, 0.94),
    ], 1):
        name, rate, cat_load, credit, retention, limit, loss_factor = scenario
        premium = 18_000_000 * (1 + rate + cat_load - credit)
        expected_noncat = 5_400_000 * loss_factor
        expected_cat = 4_000_000 * loss_factor
        commission = 0.15
        expenses = 0.12
        capital = 40_000_000 * (0.85 if index == 2 else 1)
        profit = premium * (1 - commission - expenses) - expected_noncat - expected_cat
        add("PricingScenarios", ScenarioId=f"SC{index}", RenewalId="R001", AccountId="A001", ScenarioName=name,
            RateChange=rate, CATLoad=cat_load, EngineeringCredit=credit, RetentionUSDCents=cents(retention),
            LimitUSDCents=cents(limit), TIVUSDCents=hero["TIVUSDCents"], BasePremiumUSDCents=cents(18_000_000),
            ExpectedNonCATUSDCents=cents(expected_noncat), ExpectedCATUSDCents=cents(expected_cat),
            Commission=commission, ExpenseRatio=expenses, CapitalUSDCents=cents(capital),
            IndicatedUSDCents=cents(premium), ExpectedLR=(expected_noncat + expected_cat) / premium,
            ExpectedMargin=profit / premium, RiskAdjustedReturn=profit / capital,
            Attractiveness=round(100 * (0.5 * clamp((profit / capital) / 0.2) + 0.5 * [0.85, 0.6, 0.9][index - 1]), 1),
            Status="Conditional - not approved" if index == 3 else "Illustrative - not approved",
            LossFactorBasis="Assumed net insurer loss factor; requires actuarial validation")
    add("UnderwritingDecisions", DecisionId="DEC001", RenewalId="R001", AccountId="A001",
        Posture="Retain subject to evidence and authority referral", Approved=False, ApprovedBy=None,
        Rationale="Compound Bayport risk; verified Rotterdam control and closed claims support differentiated terms.")
    event_types = ["CATModelUpdated", "EngineeringOpened", "EngineeringClosed", "LargeClaimCreated", "ReserveIncreased",
                   "ExposureIncreased", "NewLocationAdded", "SubmissionReceived", "RiskScoreChanged", "WeatherAlert", "RenewalApproaching"]
    for index, row in enumerate(features):
        add("UnderwritingEvents", **make_event(row, f"BASE{index:03}", "Snapshot", index + 1,
                                              datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)))
    for index, event_type in enumerate(event_types):
        row = features[1 + index]
        add("UnderwritingEvents", **make_event(row, f"HIST{index:03}", event_type, 100 + index,
                                              datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)))
    for offset in range((date(2027, 12, 31) - date(2024, 1, 1)).days + 1):
        day = date(2024, 1, 1) + timedelta(days=offset)
        add("Calendar", Date=day.isoformat(), Year=day.year, Month=day.month, MonthName=day.strftime("%b"))
    return tables


def calculate_features(tables: dict) -> list[dict]:
    result = []
    for account in tables["Accounts"]:
        account_id = account["AccountId"]
        exposures = [row for row in tables["Exposures"] if row["AccountId"] == account_id]
        cats = [row for row in tables["CATRisk"] if row["AccountId"] == account_id]
        valuations = [row for row in tables["ClaimValuations"] if row["AccountId"] == account_id]
        recs = [row for row in tables["EngineeringRecommendations"] if row["AccountId"] == account_id]
        renewal = next(row for row in tables["Renewals"] if row["AccountId"] == account_id)

        def total(rows, field, snapshot):
            return sum(row[field] for row in rows if row["SnapshotDate"] == snapshot.isoformat())

        tiv = total(exposures, "ValueUSDCents", AS_OF)
        tiv_old = total(exposures, "ValueUSDCents", PRIOR)
        cat = total(cats, "AALUSDCents", AS_OF)
        cat_old = total(cats, "AALUSDCents", PRIOR)
        loss = total(valuations, "IncurredUSDCents", AS_OF)
        loss_old = total(valuations, "IncurredUSDCents", PRIOR)
        tiv_growth, cat_growth, claims_growth = tiv / tiv_old - 1, cat / cat_old - 1, loss / loss_old - 1
        zone_totals: dict[str, int] = {}
        for location in tables["Locations"]:
            if location["AccountId"] == account_id:
                zone_totals[location["CATZone"]] = zone_totals.get(location["CATZone"], 0) + location["TIVUSDCents"]
        weight = sum(row["MaterialityWeight"] for row in recs)
        open_weight = sum(row["MaterialityWeight"] for row in recs if row["Status"] != "Closed")
        days = (date.fromisoformat(renewal["RenewalDate"]) - AS_OF).days
        result.append({"AccountId": account_id, "SnapshotDate": AS_OF.isoformat(),
                       "TIVUSDCents": tiv, "PriorTIVUSDCents": tiv_old, "AALUSDCents": cat, "PriorAALUSDCents": cat_old,
                       "IncurredUSDCents": loss, "PriorIncurredUSDCents": loss_old,
                       "TIVGrowth": round(tiv_growth, 6), "CATGrowth": round(cat_growth, 6), "ClaimsGrowth": round(claims_growth, 6),
                       "DaysToRenewal": days, "OpenCritical": sum(row["IsCritical"] and row["Status"] != "Closed" for row in recs),
                       "CAT": clamp(cat_growth / 0.5), "Claims": clamp(claims_growth / 0.5),
                       "Growth": clamp(tiv_growth / 0.2), "Engineering": open_weight / weight if weight else 0.0,
                       "Concentration": clamp(max(zone_totals.values()) / tiv / 0.8),
                       "Missing": renewal["MissingItems"] / renewal["RequiredItems"], "Proximity": clamp(1 - days / 70)})
    return result


def make_event(features: dict, event_id: str, event_type: str, sequence: int, event_time: datetime, run_id="baseline") -> dict:
    return {"EventId": event_id, "AccountId": features["AccountId"], "RunId": run_id, "Sequence": sequence,
            "EventTime": event_time.isoformat().replace("+00:00", "Z"), "EventType": event_type,
            "SourceVersion": "demo-v1", "BusinessAsOf": AS_OF.isoformat(),
            **{name: round(features[name], 6) for name in WEIGHTS}, "Pulse": pulse(features),
            "DaysToRenewal": features["DaysToRenewal"], "OpenCritical": features["OpenCritical"],
            "ReserveChangePct": 0.0, "ExposureChangePct": features["TIVGrowth"],
            "LocationId": f"L{features['AccountId'][1:]}01", "EvidenceRef": f"UnderwritingFeatures/{features['AccountId']}"}


def live_events(tables: dict, run_id: str, start: datetime) -> list[dict]:
    baseline = dict(tables["UnderwritingFeatures"][0])
    baseline_event = make_event(baseline, f"{run_id}-001", "Snapshot", 1, start, run_id)
    changed = dict(baseline, CAT=0.96, Claims=0.90)
    updated = make_event(changed, f"{run_id}-002", "CATAndReserveUpdated", 2, start + timedelta(minutes=6), run_id)
    updated["ReserveChangePct"] = round(250_000 / 2_100_000, 6)
    updated["EvidenceRef"] = "CAT Bayport AAL +400000 USD; CL00101 incurred +250000 USD; synthetic live overlay"
    return [baseline_event, updated]


KEYS = {"Countries": "CountryId", "Industries": "IndustryId", "Perils": "PerilId", "Brokers": "BrokerId",
        "Underwriters": "UnderwriterId", "Accounts": "AccountId", "Renewals": "RenewalId", "Policies": "PolicyId",
        "Coverages": "CoverageId", "PolicyValuations": "PolicyValuationId", "MultinationalPrograms": "ProgramId", "Submissions": "SubmissionId",
        "Insureds": "InsuredId", "Locations": "LocationId", "Assets": "AssetId", "LocalPolicies": "LocalPolicyId",
        "ProgramRequirements": "RequirementId", "Exposures": "ExposureId", "CATRisk": "CATId",
        "EngineeringInspections": "InspectionId", "EngineeringRecommendations": "RecommendationId",
        "LossEvents": "LossEventId", "Claims": "ClaimId", "ClaimValuations": "ClaimValuationId",
        "UnderwritingFeatures": "AccountId", "RiskPulse": "PulseId", "RenewalSignals": "SignalId",
        "PricingScenarios": "ScenarioId", "UnderwritingDecisions": "DecisionId", "UnderwritingEvents": "EventId", "Calendar": "Date"}


def validate(tables: dict) -> dict:
    for table, key in KEYS.items():
        values = [row[key] for row in tables[table]]
        assert len(values) == len(set(values)) and all(value is not None for value in values), table
    references = {value: table for table, value in KEYS.items() if table not in ("UnderwritingFeatures", "Calendar")}
    references.update({"DomicileCountryId": "Countries", "ExpiringPolicyId": "Policies", "MasterPolicyId": "Policies"})
    checks = 0
    for table, rows in tables.items():
        for row in rows:
            for field, target in references.items():
                if field in row and row[field] is not None and not (target == table and field == KEYS[table]):
                    assert row[field] in {item[KEYS[target]] for item in tables[target]}, (table, field, row[field])
                    checks += 1
    policies = {row["PolicyId"]: row for row in tables["Policies"]}
    locations = {row["LocationId"]: row for row in tables["Locations"]}
    coverages = {row["CoverageId"]: row for row in tables["Coverages"]}
    for claim in tables["Claims"]:
        assert claim["PaidUSDCents"] + claim["OutstandingUSDCents"] == claim["IncurredUSDCents"]
        assert claim["AccountId"] == policies[claim["PolicyId"]]["AccountId"] == locations[claim["LocationId"]]["AccountId"]
        assert coverages[claim["CoverageId"]]["PolicyId"] == claim["PolicyId"]
        assert policies[claim["PolicyId"]]["EffectiveDate"] <= claim["LossDate"] < policies[claim["PolicyId"]]["ExpiryDate"]
        assert claim["LossDate"] <= claim["ReportDate"] <= claim["SnapshotDate"]
        if claim["Status"] == "Closed":
            assert claim["OutstandingUSDCents"] == 0 and claim["ClosureDate"] is not None
    for row in tables["ClaimValuations"]:
        assert row["PaidUSDCents"] + row["OutstandingUSDCents"] == row["IncurredUSDCents"]
    for location in tables["Locations"]:
        for snapshot, field in [(AS_OF.isoformat(), "TIVUSDCents"), (PRIOR.isoformat(), "PriorTIVUSDCents")]:
            assert sum(row["ValueUSDCents"] for row in tables["Exposures"] if row["LocationId"] == location["LocationId"] and row["SnapshotDate"] == snapshot) == location[field]
    hero = tables["UnderwritingFeatures"][0]
    assert hero["TIVUSDCents"] == cents(1_140_000_000)
    assert hero["AALUSDCents"] == cents(7_000_000)
    assert hero["IncurredUSDCents"] == cents(7_000_000)
    assert hero["OpenCritical"] == 2 and pulse(hero) == 77.0
    events = live_events(tables, "test", datetime(2026, 9, 14, 12, tzinfo=timezone.utc))
    assert [row["Pulse"] for row in events] == [77.0, 83.0]
    for row in tables["PricingScenarios"]:
        assert row["ExpectedLR"] < 1 and row["RiskAdjustedReturn"] > 0
    return {"status": "PASS", "foreign_key_checks": checks, "table_counts": {table: len(rows) for table, rows in tables.items()},
            "hero": hero, "transition": [row["Pulse"] for row in events],
            "not_verified": ["Fabric Spark execution", "DAX engine", "GQL engine", "KQL engine", "tenant permissions", "agent responses"]}


def column_type(field: str, rows: list[dict]) -> str:
    values = [row[field] for row in rows if row[field] is not None]
    if field.endswith("Date") or field in ("Date", "BusinessAsOf"):
        return "date"
    if field == "EventTime":
        return "datetime2(6)"
    if values and isinstance(values[0], bool):
        return "bit"
    if values and isinstance(values[0], int):
        return "bigint"
    if values and isinstance(values[0], float):
        return "float"
    return "varchar(8000)" if any(len(str(value)) > 250 for value in values) else "varchar(250)"


def write_outputs(tables: dict, root: Path = ROOT) -> None:
    for directory in ["data/csv", "sql", "validation"]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    schema = {}
    ddl = ["SET NOCOUNT ON;"]
    inserts = ["SET NOCOUNT ON;"]
    for table, rows in tables.items():
        fields = list(rows[0])
        schema[table] = {"key": KEYS[table], "columns": {field: column_type(field, rows) for field in fields}}
        with (root / "data/csv" / f"{table}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        columns = ", ".join(f"[{field}] {schema[table]['columns'][field]} NULL" for field in fields)
        ddl.append(f"CREATE TABLE dbo.[{table}] ({columns});")

        def literal(value):
            if value is None:
                return "NULL"
            if isinstance(value, bool):
                return "1" if value else "0"
            if isinstance(value, (int, float)):
                return str(value)
            return "'" + str(value).replace("'", "''") + "'"

        field_sql = ", ".join(f"[{field}]" for field in fields)
        for start in range(0, len(rows), 100):
            values = ",\n".join("(" + ", ".join(literal(row[field]) for field in fields) + ")" for row in rows[start:start + 100])
            inserts.append(f"INSERT INTO dbo.[{table}] ({field_sql}) VALUES\n{values};")
    (root / "sql/01_create_tables.sql").write_text("\n\n".join(ddl), encoding="utf-8")
    (root / "sql/02_insert_data.sql").write_text("\n\n".join(inserts), encoding="utf-8")
    (root / "data/schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (root / "data/demo.json").write_text(json.dumps(tables, indent=2), encoding="utf-8")
    (root / "validation/data-validation.json").write_text(json.dumps(validate(tables), indent=2), encoding="utf-8")


if __name__ == "__main__":
    data = build_data()
    report = validate(data)
    write_outputs(data)
    print(json.dumps({"status": report["status"], "tables": len(data), "rows": sum(map(len, data.values())),
                      "foreign_key_checks": report["foreign_key_checks"], "hero_pulse": report["transition"]}, indent=2))