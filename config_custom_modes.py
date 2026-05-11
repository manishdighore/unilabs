"""
Custom Mode Presets - Pre-configured agent combinations for specific analysis types
"""

# --- CUSTOM MODE PRESETS -------
# Users can select these presets or create their own
CUSTOM_MODE_PRESETS = {
    "all_agents": {
        "id": "all_agents",
        "name": "All 22 Agents",
        "description": "Full comprehensive competitive intelligence report (all agents)",
        "agent_ids": [
            # Core (10)
            "competitive-overview", "ma-deal-tracker", "revenue-benchmarking", 
            "market-share-analysis", "service-portfolio", "pricing-strategy",
            "tech-capability-gap", "geographic-battleground", "customer-win-loss",
            "strategic-moves",
            # Intelligence (12)
            "brand-perception", "talent-war", "digital-ecosystem", "regulatory-advantage",
            "payer-relationship", "esg-benchmarking", "supply-chain-risk", "clinical-pipeline",
            "tender-intelligence", "leadership-movements", "media-share-of-voice", "partnership-alliances"
        ],
        "is_editable": False  # System preset
    },
    
    "ma_focus": {
        "id": "ma_focus",
        "name": "M&A Focus",
        "description": "Monitor acquisition, divestiture, and strategic deal activity",
        "agent_ids": ["ma-deal-tracker", "strategic-moves", "market-share-analysis", "leadership-movements"],
        "is_editable": False
    },
    
    "market_health": {
        "id": "market_health",
        "name": "Market Health Check",
        "description": "Monthly snapshot of market position and key shifts",
        "agent_ids": ["competitive-overview", "market-share-analysis", "pricing-strategy", 
                      "customer-win-loss", "revenue-benchmarking"],
        "is_editable": False
    },
    
    "executive_summary": {
        "id": "executive_summary",
        "name": "Executive Summary",
        "description": "5-module briefing for C-suite (strategic level)",
        "agent_ids": ["competitive-overview", "revenue-benchmarking", "strategic-moves", 
                      "talent-war", "market-share-analysis"],
        "is_editable": False
    },
    
    "tech_innovation": {
        "id": "tech_innovation",
        "name": "Tech & Innovation",
        "description": "Digital, AI, and clinical pipeline developments",
        "agent_ids": ["tech-capability-gap", "digital-ecosystem", "clinical-pipeline", 
                      "partnership-alliances"],
        "is_editable": False
    },
    
    "compliance_risk": {
        "id": "compliance_risk",
        "name": "Compliance & Risk",
        "description": "Regulatory, ESG, and operational risk monitoring",
        "agent_ids": ["regulatory-advantage", "esg-benchmarking", "supply-chain-risk"],
        "is_editable": False
    },
}

# --- CUSTOM MODE CONFIG -------
# Structure for database/config storage
CUSTOM_MODE_CONFIG_TEMPLATE = {
    "id": "user_mode_1",              # Unique identifier
    "name": "My Custom Analysis",      # User-friendly name
    "description": "Description...",   # What this mode does
    "agent_ids": ["agent-1", "agent-2"],  # Array of agent IDs to run
    "is_editable": True,              # Can user edit/delete?
    "created_at": "2026-05-11T10:00:00",
    "updated_at": "2026-05-11T10:00:00",
}
