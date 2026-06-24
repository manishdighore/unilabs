"""
Central configuration — constants, agent definitions, defaults.
Market Intelligence Edition: modules focus on selected-period
competitor and market updates with implications for Unilabs.
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

# --- Month Configuration -------
MONTHS = [
    {"code": 1, "name": "January", "quarter": 1},
    {"code": 2, "name": "February", "quarter": 1},
    {"code": 3, "name": "March", "quarter": 1},
    {"code": 4, "name": "April", "quarter": 2},
    {"code": 5, "name": "May", "quarter": 2},
    {"code": 6, "name": "June", "quarter": 2},
    {"code": 7, "name": "July", "quarter": 3},
    {"code": 8, "name": "August", "quarter": 3},
    {"code": 9, "name": "September", "quarter": 3},
    {"code": 10, "name": "October", "quarter": 4},
    {"code": 11, "name": "November", "quarter": 4},
    {"code": 12, "name": "December", "quarter": 4},
]

# Month to quarter mapping for backwards compatibility
MONTH_TO_QUARTER = {m["code"]: m["quarter"] for m in MONTHS}

COUNTRIES = [
    {"code": "NL", "name": "Netherlands"}, {"code": "CH", "name": "Switzerland"},
    {"code": "CZ", "name": "Czech Republic"}, {"code": "SK", "name": "Slovakia"},
    {"code": "PT", "name": "Portugal"},
    {"code": "UAE", "name": "UAE"}, {"code": "NO", "name": "Norway"},
    {"code": "SE", "name": "Sweden"}, {"code": "FI", "name": "Finland"},
    {"code": "DK", "name": "Denmark"}, {"code": "UK", "name": "United Kingdom"},
    {"code": "FR", "name": "France"}, {"code": "US", "name": "United States"},
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

# --- Agent Definitions (Market Intelligence) ------------------------------
# Modules focus on selected-period competitor/market updates and implications.
# Sections 8 and 10 from the original UAT output are intentionally removed.
AGENTS = [
    # == Core Market Intel Modules (8) ==
    {"id": "competitive-overview", "title": "Competitive Landscape Overview",
     "category": "core", "color": "#003366",
     "agentA": "Find selected-period competitor updates only: newly published revenue figures, important news, new tests, new tools, new services, and market entries or exits.",
     "agentB": "Assess how selected-period competitor updates could impact or benefit Unilabs; avoid company descriptions and generic competitor profiles."},

    {"id": "ma-deal-tracker", "title": "M&A & Deal Activity Tracker",
     "category": "core", "color": "#003366",
     "agentA": "Track selected-period M&A deals by diagnostics competitors plus relevant PE and healthcare diagnostics deals; omit competitors with no activity.",
     "agentB": "Assess deal rationale, affected markets, transaction values where available, and implications or opportunities for Unilabs."},

    {"id": "revenue-benchmarking", "title": "Revenue & Financial Benchmarking",
     "category": "core", "color": "#003366",
     "agentA": "Find the latest selected-period competitor financial publications: revenue, EBITDA or EBITA, margin, growth, guidance, and capital allocation.",
     "agentB": "Build concise financial benchmarking with last-three-year revenue and EBITDA or EBITA data where public; include simple tables and chart-ready values."},

    {"id": "market-share-analysis", "title": "Market Share & Positioning Analysis",
     "category": "core", "color": "#003366",
     "agentA": "Estimate competitor market share percentages for Europe and selected countries; collect revenue, countries served, and growth projections.",
     "agentB": "Summarize market share in a simple table only; no company descriptions or Unilabs overview."},

    {"id": "service-portfolio", "title": "Service Portfolio Comparison",
     "category": "core", "color": "#00A3E0",
     "agentA": "Find selected-period competitor service, test-menu, pathology, radiology, genetics, digital portal, home collection, or specialty panel launches.",
     "agentB": "Explain only what changed in competitor portfolios during the period and what it means for Unilabs; omit if no real update."},

    {"id": "pricing-strategy", "title": "Pricing & Contract Strategy",
     "category": "core", "color": "#00A3E0",
     "agentA": "Analyze pricing regulation updates, reimbursement changes, tariff changes, public tender price signals, and market pricing updates in selected Unilabs markets.",
     "agentB": "Track competitor pricing updates only where public; connect price or regulation changes to risks or opportunities for Unilabs."},

    {"id": "tech-capability-gap", "title": "Technology & Capability Gap Analysis",
     "category": "core", "color": "#00A3E0",
     "agentA": "Find selected-period technology updates from European diagnostics competitors and relevant US players: AI, digital pathology, automation, LIMS, portals, genomics tools.",
     "agentB": "Assess competitor and US-player technology moves for implications to Unilabs; do not describe Unilabs capabilities upfront."},

    {"id": "customer-win-loss", "title": "Customer Win/Loss Intelligence",
     "category": "core", "color": "#00A3E0",
     "agentA": "Track selected-period customer wins and losses, hospital contracts, health-system awards, tenders, and outsourcing decisions involving competitors.",
     "agentB": "Summarize only verified wins or losses and the impact or benefit for Unilabs; omit competitors with no win/loss update."},

    # == Intelligence Modules (12) ==
    {"id": "brand-perception", "title": "Brand & Reputation Benchmarking",
     "category": "intelligence", "color": "#F43F5E",
     "agentA": "Find selected-period competitor reputation updates: review score shifts, major complaints, media reputation events, patient sentiment signals.",
     "agentB": "Return a compact table of competitor reputation signals, source/date, and implication for Unilabs."},

    {"id": "talent-war", "title": "Talent & Workforce Competition",
     "category": "intelligence", "color": "#8B5CF6",
     "agentA": "Analyze selected-period LinkedIn and company career-site hiring trends for each competitor: open roles, locations, role types, seniority, expansion signals.",
     "agentB": "Track big layoffs, hiring surges, leadership hiring, and open-position trend vs prior months where available; include chart-ready role counts."},

    {"id": "digital-ecosystem", "title": "Digital & AI Arms Race",
     "category": "intelligence", "color": "#4F46E5",
     "agentA": "Find selected-period digital and AI updates from competitors and US diagnostics or health-tech players: product launches, partnerships, funding, deployments.",
     "agentB": "Assess which updates create direct threats, partnership openings, or capability gaps for Unilabs."},

    {"id": "regulatory-advantage", "title": "Regulatory & Compliance Edge",
     "category": "intelligence", "color": "#0D9488",
     "agentA": "Find selected-period regulatory, accreditation, IVDR, reimbursement, penalty, audit, and compliance updates affecting competitors or diagnostics markets.",
     "agentB": "Explain the market impact and implication for Unilabs; omit generic IVDR background if no new update happened."},

    {"id": "payer-relationship", "title": "Payer & Health System Relationships",
     "category": "intelligence", "color": "#EA580C",
     "agentA": "Find selected-period payer, insurer, hospital, PPP, outsourcing, and health-system partnership updates involving competitors.",
     "agentB": "Summarize only real relationship or contract changes and implication for Unilabs."},

    {"id": "esg-benchmarking", "title": "ESG & Sustainability Comparison",
     "category": "intelligence", "color": "#10B981",
     "agentA": "Find selected-period ESG, CSRD, and sustainability updates from competitors: new reports, targets, waste, emissions, governance, social impact.",
     "agentB": "Return a concise update table with impact for Unilabs; no generic ESG benchmarking."},

    {"id": "supply-chain-risk", "title": "Supply Chain & Operational Risk",
     "category": "intelligence", "color": "#F59E0B",
     "agentA": "Find selected-period operational, supply chain, lab disruption, reagent or vendor, energy, logistics, tariff, FX, and resilience updates affecting competitors.",
     "agentB": "Explain whether these updates create risk, cost pressure, or opportunity for Unilabs."},

    {"id": "clinical-pipeline", "title": "Clinical & Scientific Pipeline Race",
     "category": "intelligence", "color": "#7DC242",
     "agentA": "Find selected-period clinical and scientific updates: emerging tests, clinical studies, guideline changes, liquid biopsy, companion diagnostics, genomics panels.",
     "agentB": "Assess competitor pipeline implications and practical response options for Unilabs."},

    {"id": "tender-intelligence", "title": "Tender & Procurement Battleground",
     "category": "intelligence", "color": "#EF4444",
     "agentA": "Find selected-period active tenders and tender outcomes in Unilabs markets: buyer, country, service scope, value, duration, winner, deadline.",
     "agentB": "Analyze what tender outcomes signal about pricing, service scope, and competitive pressure for Unilabs."},

    {"id": "leadership-movements", "title": "Leadership & Board Movement Tracker",
     "category": "intelligence", "color": "#8B5CF6",
     "agentA": "Find selected-period C-suite, board, country GM, senior scientific, commercial, digital, and operations leadership moves at competitors.",
     "agentB": "Explain likely strategic meaning and talent implications for Unilabs; no generic org descriptions."},

    {"id": "media-share-of-voice", "title": "Media & Share of Voice Analysis",
     "category": "intelligence", "color": "#0D9488",
     "agentA": "Find selected-period competitor media, PR, crisis, conference, campaign, award, or thought-leadership updates.",
     "agentB": "Summarize share-of-voice signals in table format and explain relevance for Unilabs communications or positioning."},

    {"id": "partnership-alliances", "title": "Partnerships & Alliance Mapping",
     "category": "intelligence", "color": "#4F46E5",
     "agentA": "Find selected-period competitor partnerships and alliances: pharma, medtech, AI, academia, hospitals, payers, startups, distributors.",
     "agentB": "Assess partnership relevance, affected markets, and implication or partnership opportunity for Unilabs."},
]
