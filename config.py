"""
Central configuration — constants, agent definitions, defaults.
Competitive Intelligence Edition: Every module is centred on
Unilabs vs. named competitors.
"""
import os

# --- Paths ----------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
_db_dir = os.environ.get("UNILABS_DB_DIR", os.path.join(BASE_DIR, "db"))
os.makedirs(_db_dir, exist_ok=True)
DB_PATH = os.path.join(_db_dir, "unilabs_ci.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# --- Defaults -------------------------------------------------------------
DEFAULT_SCHEDULE_CRON = {"day_of_week": "mon", "hour": 10, "minute": 0}
BATCH_SIZE = 3  # concurrent agent pairs per batch

# --- Report Frequency Configuration -------
REPORT_FREQUENCIES = ["monthly", "quarterly", "both"]
DEFAULT_REPORT_FREQUENCY = "quarterly"

# Scheduler configurations for different frequencies
QUARTERLY_SCHEDULE = {"day_of_week": "mon", "hour": 10, "minute": 0}  # First Monday of each quarter
MONTHLY_SCHEDULE = {"day": "1", "hour": "9", "minute": "0"}  # First day of every month at 9 AM

COUNTRIES = [
    {"code": "NL", "name": "Netherlands"}, {"code": "CH", "name": "Switzerland"},
    {"code": "CEE", "name": "Central & Eastern Europe"}, {"code": "PT", "name": "Portugal"},
    {"code": "UAE", "name": "UAE"}, {"code": "NO", "name": "Norway"},
    {"code": "SE", "name": "Sweden"}, {"code": "FI", "name": "Finland"},
    {"code": "DK", "name": "Denmark"}, {"code": "UK", "name": "United Kingdom"},
    {"code": "FR", "name": "France"},
]

DEFAULT_COMPETITORS = [
    "Synlab", "Eurofins", "Sonic Healthcare Europe", "Cerba Healthcare",
    "Amedes", "Limbach Group", "Biogroup", "Affidea", "Evidea",
    "Germano de Sousa", "Unilabs Regional Rivals",
]

LANGUAGES = [
    {"code": "en", "name": "English"}, {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"}, {"code": "nl", "name": "Dutch"},
    {"code": "pt", "name": "Portuguese"}, {"code": "no", "name": "Norwegian"},
    {"code": "sv", "name": "Swedish"}, {"code": "fi", "name": "Finnish"},
    {"code": "da", "name": "Danish"}, {"code": "ar", "name": "Arabic"},
]

# --- Agent Definitions (Competitive Intelligence) -------------------------
# Every agent is rewritten to centre on Unilabs positioning vs competitors.
AGENTS = [
    # == Core Competitive Modules (10) ==
    {"id": "competitive-overview",    "title": "Competitive Landscape Overview",
     "category": "core", "color": "#003366",
     "agentA": "Map Unilabs market position vs each named competitor: revenue, lab count, geographic overlap, and growth trajectory comparison.",
     "agentB": "Identify where competitors are gaining or losing ground relative to Unilabs: new market entries, exits, and share shifts."},

    {"id": "ma-deal-tracker",         "title": "M&A & Deal Activity Tracker",
     "category": "core", "color": "#003366",
     "agentA": "Track every acquisition, divestiture, and PE deal by competitors in the last quarter and assess impact on Unilabs competitive position.",
     "agentB": "Identify potential M&A targets that competitors might pursue before Unilabs and flag white-space acquisition opportunities for Unilabs."},

    {"id": "revenue-benchmarking",    "title": "Revenue & Financial Benchmarking",
     "category": "core", "color": "#003366",
     "agentA": "Compare Unilabs revenue, EBITDA margins, and growth rates against publicly reported competitor financials (Synlab, Eurofins, Sonic, Limbach).",
     "agentB": "Analyze competitor capital allocation, capex trends, debt levels, and investor guidance that signal strategic intent against Unilabs."},

    {"id": "market-share-analysis",   "title": "Market Share & Positioning Analysis",
     "category": "core", "color": "#003366",
     "agentA": "Estimate Unilabs vs competitor market shares by country and segment (routine, specialty, pathology, radiology, genetics).",
     "agentB": "Identify market segments where Unilabs is under-indexed vs competitors and where competitors are aggressively expanding."},

    {"id": "service-portfolio",       "title": "Service Portfolio Comparison",
     "category": "core", "color": "#00A3E0",
     "agentA": "Compare Unilabs test menu, turnaround times, and service breadth vs key competitors across diagnostics, pathology, radiology, and genetics.",
     "agentB": "Identify gaps in Unilabs service offering that competitors already fill (e.g., DTC testing, at-home collection, specialty panels)."},

    {"id": "pricing-strategy",        "title": "Pricing & Contract Strategy",
     "category": "core", "color": "#00A3E0",
     "agentA": "Analyze competitor pricing visible through public tenders, DTC platforms, and published tariffs relative to Unilabs pricing.",
     "agentB": "Track competitor contract wins/losses, tender outcomes, and framework agreements that directly affect Unilabs market position."},

    {"id": "tech-capability-gap",     "title": "Technology & Capability Gap Analysis",
     "category": "core", "color": "#00A3E0",
     "agentA": "Benchmark Unilabs digital capabilities (AI, automation, LIMS, patient portal) against competitor technology investments and deployments.",
     "agentB": "Track competitor partnerships with tech vendors (Paige.AI, Tempus, Oxford Nanopore, Roche) and assess Unilabs technology gaps."},

    {"id": "geographic-battleground", "title": "Geographic Battleground Analysis",
     "category": "core", "color": "#00A3E0",
     "agentA": "Map competitor presence vs Unilabs in each of the 11 operating markets: lab density, new openings, closures, and expansion signals.",
     "agentB": "Identify geographic markets where Unilabs faces rising competitive pressure and markets where Unilabs has defensible advantages."},

    {"id": "customer-win-loss",       "title": "Customer Win/Loss Intelligence",
     "category": "core", "color": "#00A3E0",
     "agentA": "Track hospital/health system contract awards and losses involving Unilabs vs competitors from tender databases and press releases.",
     "agentB": "Analyze patterns in why customers switch to or from Unilabs: pricing, service quality, turnaround, geographic coverage."},

    {"id": "strategic-moves",         "title": "Competitor Strategic Moves & Signals",
     "category": "core", "color": "#00A3E0",
     "agentA": "Monitor competitor earnings calls, investor presentations, and press releases for strategic signals that may impact Unilabs.",
     "agentB": "Track regulatory filings, patent applications, and CE IVD submissions by competitors that reveal future competitive threats."},

    # == Intelligence Modules (12) ==
    {"id": "brand-perception",        "title": "Brand & Reputation Benchmarking",
     "category": "intelligence", "color": "#F43F5E",
     "agentA": "Compare Unilabs patient reviews (Google, Trustpilot) vs competitor ratings across all operating markets — scores, volume, trends.",
     "agentB": "Analyze healthcare professional perception of Unilabs vs competitors: referral preferences, NPS proxies, complaint themes."},

    {"id": "talent-war",              "title": "Talent & Workforce Competition",
     "category": "intelligence", "color": "#8B5CF6",
     "agentA": "Analyze competitor job postings to infer expansion plans, new capabilities, and areas where they are out-hiring Unilabs.",
     "agentB": "Track C-suite and senior leadership movements between Unilabs and competitors; monitor salary benchmarks and employer branding."},

    {"id": "digital-ecosystem",       "title": "Digital & AI Arms Race",
     "category": "intelligence", "color": "#4F46E5",
     "agentA": "Map competitor investments in diagnostic AI, digital pathology, and lab automation vs Unilabs current capabilities.",
     "agentB": "Track VC/PE funding into diagnostic startups that competitors are partnering with or acquiring, and assess threat to Unilabs."},

    {"id": "regulatory-advantage",    "title": "Regulatory & Compliance Edge",
     "category": "intelligence", "color": "#0D9488",
     "agentA": "Compare Unilabs IVDR readiness, accreditation status, and compliance posture vs competitors across EU markets.",
     "agentB": "Track competitor regulatory penalties, audit findings, or compliance advantages that could shift customer decisions away from Unilabs."},

    {"id": "payer-relationship",      "title": "Payer & Health System Relationships",
     "category": "intelligence", "color": "#EA580C",
     "agentA": "Map competitor relationships with key payers, insurers, and health systems vs Unilabs partnerships in each market.",
     "agentB": "Track hospital outsourcing decisions, lab consolidation trends, and PPP models where Unilabs competes head-to-head with rivals."},

    {"id": "esg-benchmarking",        "title": "ESG & Sustainability Comparison",
     "category": "intelligence", "color": "#10B981",
     "agentA": "Benchmark Unilabs ESG disclosures, net-zero pledges, and sustainability metrics vs competitor published reports and CSRD readiness.",
     "agentB": "Identify areas where competitors lead Unilabs on ESG (waste reduction, social impact, governance) and where Unilabs leads."},

    {"id": "supply-chain-risk",       "title": "Supply Chain & Operational Risk",
     "category": "intelligence", "color": "#F59E0B",
     "agentA": "Compare Unilabs supplier dependencies vs competitors: reagent sourcing, equipment vendors, single-source risks.",
     "agentB": "Track geopolitical risks (tariffs, FX, energy costs, Brexit) that disproportionately affect Unilabs vs competitors."},

    {"id": "clinical-pipeline",       "title": "Clinical & Scientific Pipeline Race",
     "category": "intelligence", "color": "#7DC242",
     "agentA": "Track competitor adoption of emerging tests (liquid biopsy, polygenic risk, companion diagnostics) vs Unilabs pipeline readiness.",
     "agentB": "Monitor clinical trial partnerships and guideline changes that could advantage specific competitors over Unilabs."},

    {"id": "tender-intelligence",     "title": "Tender & Procurement Battleground",
     "category": "intelligence", "color": "#EF4444",
     "agentA": "Monitor active tenders on TED/OJEU where Unilabs and competitors are likely to bid, with estimated contract values and timelines.",
     "agentB": "Analyze recent tender outcomes: who won, who lost, at what price, and what this signals about competitor pricing strategy vs Unilabs."},

    {"id": "leadership-movements",    "title": "Leadership & Board Movement Tracker",
     "category": "intelligence", "color": "#8B5CF6",
     "agentA": "Track C-suite appointments, departures, and board changes at all named competitors and assess strategic implications for Unilabs.",
     "agentB": "Monitor ex-Unilabs executives now at competitors and competitor talent that Unilabs could recruit to close capability gaps."},

    {"id": "media-share-of-voice",    "title": "Media & Share of Voice Analysis",
     "category": "intelligence", "color": "#0D9488",
     "agentA": "Measure Unilabs share of voice vs competitors in healthcare trade media, financial press, and industry conferences.",
     "agentB": "Track competitor PR campaigns, crisis events, and thought leadership positioning that affects perception relative to Unilabs."},

    {"id": "partnership-alliances",   "title": "Partnerships & Alliance Mapping",
     "category": "intelligence", "color": "#4F46E5",
     "agentA": "Map strategic alliances each competitor has (pharma co-development, tech partnerships, academic collaborations) vs Unilabs partnerships.",
     "agentB": "Identify partnership gaps where Unilabs lacks relationships that competitors leverage for competitive advantage."},
]
