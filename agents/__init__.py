"""
Multi-agent engine: OpenAI Responses API with web_search_preview tool.
Market Intelligence Edition - selected-period competitor and market updates.

API:   OpenAI Responses API  (client.responses.create)
Model: hardcoded constants below — change SEARCH_MODEL / VALIDATOR_MODEL as needed
"""
import asyncio, html, logging
import httpx
from openai import AsyncOpenAI
from config import AGENTS, BATCH_SIZE, LANGUAGES, COUNTRIES

log = logging.getLogger("agents")

# ── Model configuration (hardcoded — change here to switch models) ─────────
SEARCH_MODEL    = "gpt-5.2"   # Research agents: Responses API + web_search_preview
VALIDATOR_MODEL = "gpt-5.2"   # Market Intel Validator: Responses API, synthesis only
ANTHROPIC_MODEL = "claude-sonnet-4-6"
GEMINI_MODEL    = "gemini-3.5-flash"

SECTION_OUTPUT_RULES = {
    "competitive-overview": """- Include only selected-period competitor updates: published financials, important news, new tests, tools, services, market entries/exits.
- Do not describe Unilabs or profile the competitors.
- For each update, state the direct implication or benefit for Unilabs.""",
    "ma-deal-tracker": """- Focus only on competitor M&A and relevant PE/healthcare diagnostics deals.
- Do not write competitor-by-competitor if there was no deal activity.
- Include deal value, buyer/seller/target, geography, rationale, and Unilabs implication where available.""",
    "revenue-benchmarking": """- Focus only on newly published competitor financials for the selected period.
- Include a compact table with competitor, latest revenue, EBITDA/EBITA, margin/growth, publication date, and implication.
- Add a simple HTML chart block for last-three-year revenue and EBITDA/EBITA where public data is available.""",
    "market-share-analysis": """- Do not describe Unilabs.
- Output a simple table with competitor, estimated Europe market share %, revenue, countries served, and growth projection.
- Keep assumptions explicit and cite each estimate.""",
    "service-portfolio": """- Do not describe Unilabs.
- Include only selected-period competitor updates on services, new tests, tools, solutions, or portfolio changes.
- If no real update exists, omit that competitor.""",
    "pricing-strategy": """- Analyze pricing regulation updates, reimbursement/tariff changes, public tender price signals, and competitor pricing updates in selected Unilabs markets.
- Do not discuss generic contract strategy unless pricing is explicit.
- Organize by market/country where possible.""",
    "tech-capability-gap": """- Do not describe Unilabs at the beginning.
- Include selected-period technology updates from European competitors and relevant US diagnostics/health-tech players.
- Cover AI, automation, digital pathology, genomics, patient portals, LIMS, and partnerships only when a real update exists.""",
    "customer-win-loss": """- Include only selected-period customer wins/losses, hospital contracts, health-system awards, tender outcomes, and outsourcing decisions.
- Omit competitors with no verified win/loss update.
- State impact or benefit for Unilabs after each update.""",
    "brand-perception": """- Use table format.
- Include competitor, market, reputation/media/review signal, direction of change, source/date, and Unilabs implication.
- Do not include generic brand benchmarking.""",
    "talent-war": """- Analyze LinkedIn/company career-site hiring trends by competitor and market for the selected period.
- Include layoffs, hiring surges, open-position counts vs prior months where available, role families, and seniority.
- Add a compact chart-ready table for open positions by competitor/role family/month.""",
    "digital-ecosystem": """- Include only selected-period digital and AI updates from competitors and relevant US players.
- Cover launches, partnerships, funding, deployments, or regulatory milestones.
- Explain threat, partnership opening, or capability gap for Unilabs.""",
    "regulatory-advantage": """- Include only selected-period regulatory, IVDR, reimbursement, accreditation, penalty, audit, or compliance updates.
- Avoid generic regulatory background.
- Explain market impact and Unilabs implication.""",
    "payer-relationship": """- Include only selected-period payer, insurer, hospital, PPP, outsourcing, or health-system relationship updates.
- Omit generic relationship maps.
- State what changed and why it matters for Unilabs.""",
    "esg-benchmarking": """- Use table format.
- Include only selected-period ESG/CSRD/sustainability updates, reports, targets, waste/emissions, governance, or social impact.
- No generic ESG benchmarking.""",
    "supply-chain-risk": """- Include only selected-period supply chain, lab disruption, reagent/vendor, energy, logistics, tariff, FX, or operational resilience updates.
- Explain risk, cost pressure, or opportunity for Unilabs.""",
    "clinical-pipeline": """- Include only selected-period clinical/scientific updates: emerging tests, studies, guideline changes, liquid biopsy, companion diagnostics, genomics panels.
- Explain competitor pipeline implication and practical response option for Unilabs.""",
    "tender-intelligence": """- Use table format where possible.
- Include selected-period tenders and tender outcomes: buyer, country, scope, value, duration, winner, deadline/status, Unilabs implication.
- Focus on pricing and procurement signals.""",
    "leadership-movements": """- Include only selected-period C-suite, board, country GM, senior scientific, commercial, digital, and operations leadership moves.
- Explain likely strategic meaning and talent implications for Unilabs.
- No generic org descriptions.""",
    "media-share-of-voice": """- Use table format.
- Include selected-period competitor media, PR, crisis, conference, campaign, award, or thought-leadership updates.
- Explain relevance for Unilabs communications or positioning.""",
    "partnership-alliances": """- Include only selected-period competitor partnerships and alliances: pharma, medtech, AI, academia, hospitals, payers, startups, distributors.
- Explain affected markets, strategic relevance, and partnership opportunity or threat for Unilabs.""",
}

DEFAULT_SECTION_RULES = """- Include only selected-period verified updates.
- Avoid generic company descriptions, stale background, and competitor-by-competitor filler.
- Explain what changed and why it matters for Unilabs."""
# ──────────────────────────────────────────────────────────────────────────


# ====================================================================
# API CALLERS  —  OpenAI Responses API
# ====================================================================

async def call_responses_search(client: AsyncOpenAI, instructions: str, user_input: str) -> str:
    """Responses API with web_search_preview — explicit web search for research agents."""
    response = await client.responses.create(
        model=SEARCH_MODEL,
        tools=[{"type": "web_search_preview"}],
        instructions=instructions,
        input=user_input,
    )
    return response.output_text


async def call_responses_validate(client: AsyncOpenAI, instructions: str, user_input: str) -> str:
    """Responses API for Market Intel Validator - synthesis and QA, no additional web search."""
    response = await client.responses.create(
        model=VALIDATOR_MODEL,
        instructions=instructions,
        input=user_input,
    )
    return response.output_text


def _anthropic_text(payload: dict) -> str:
    """Collect text blocks from an Anthropic Messages API response."""
    parts = []
    for block in payload.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(p for p in parts if p).strip()


async def call_anthropic(api_key: str, instructions: str, user_input: str, use_web_search: bool) -> str:
    """Anthropic Messages API caller. Research calls can use Claude's web search tool."""
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "system": instructions,
        "messages": [{"role": "user", "content": user_input}],
    }
    if use_web_search:
        body["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 10}]

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        text = _anthropic_text(resp.json())
        return text or "<p>No content returned from Anthropic.</p>"


def _gemini_source_appendix(response) -> str:
    """Build a source appendix from Gemini grounding metadata when present."""
    try:
        grounding = response.candidates[0].grounding_metadata
        chunks = getattr(grounding, "grounding_chunks", None) or []
    except Exception:
        chunks = []

    sources = []
    seen = set()
    for chunk in chunks:
        web = getattr(chunk, "web", None)
        uri = getattr(web, "uri", None) if web else None
        if not uri or uri in seen:
            continue
        seen.add(uri)
        title = getattr(web, "title", None) or uri
        sources.append((html.escape(title), html.escape(uri, quote=True)))

    if not sources:
        return ""

    items = "\n".join(
        f'<li id="gemini-source-{i}"><a href="{uri}" target="_blank" rel="noopener">{title}</a> - Gemini Google Search grounding</li>'
        for i, (title, uri) in enumerate(sources, 1)
    )
    return f'\n<div class="references"><h4>Gemini Grounding Sources</h4><ol>{items}</ol></div>'


def _call_gemini_sync(api_key: str, instructions: str, user_input: str, use_google_search: bool) -> str:
    """Google GenAI SDK caller. Research calls use Google Search grounding."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    tools = [types.Tool(google_search=types.GoogleSearch())] if use_google_search else None
    config = types.GenerateContentConfig(
        system_instruction=instructions,
        tools=tools,
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_input,
        config=config,
    )
    text = (getattr(response, "text", None) or "").strip()
    if use_google_search:
        text += _gemini_source_appendix(response)
    return text or "<p>No content returned from Gemini.</p>"


async def call_gemini(api_key: str, instructions: str, user_input: str, use_google_search: bool) -> str:
    return await asyncio.to_thread(_call_gemini_sync, api_key, instructions, user_input, use_google_search)


# ====================================================================
# HELPERS
# ====================================================================

def _get_competitors(config):
    """Merge named competitors + any custom competitors from this run's config."""
    return (
        config.get("competitors", []) +
        [c for c in config.get("custom_competitors", []) if c]
    )


def _period_scope(config):
    years = ", ".join(str(y) for y in config.get("years", [])) or "selected year"
    periods = ", ".join(str(p) for p in config.get("periods", [])) or "selected period"
    frequency = config.get("report_frequency", "quarterly")
    return f"{years} {periods} ({frequency})"


def _section_rules(agent):
    return SECTION_OUTPUT_RULES.get(agent.get("id"), DEFAULT_SECTION_RULES)


# ====================================================================
# PROMPT BUILDERS — MARKET INTELLIGENCE FOCUSED
# ====================================================================

def _sys_prompt_research(agent, config, focus):
    """System instructions for research agents."""
    lang = config.get("language", "en")
    lang_name = next((l["name"] for l in LANGUAGES if l["code"] == lang), "English")
    lang_note = f"\nIMPORTANT: Write the entire output in {lang_name}." if lang != "en" else ""
    competitors = _get_competitors(config)
    comp_list = ", ".join(competitors) if competitors else "major diagnostics competitors and relevant market players"
    market_list = ", ".join(f'{c["code"]} ({c["name"]})' for c in COUNTRIES)
    period = _period_scope(config)
    rules = _section_rules(agent)

    return f"""You are a senior market intelligence analyst writing a concise monthly-style update for Unilabs executive leadership.
The report covers selected Unilabs markets: {market_list}.

ANALYSIS SECTION: "{agent['title']}"
SELECTED PERIOD: {period}
RESEARCH FOCUS: {focus}
COMPETITORS / PLAYERS TO CHECK: {comp_list}

SECTION-SPECIFIC BRIEF:
{rules}

WEB SEARCH PROTOCOL - execute targeted searches before writing:
1. Search each named competitor plus "{agent['title']}" plus the selected period: {period}.
2. Search selected markets plus diagnostics plus the section topic and selected period.
3. Search official press releases, investor results, annual/interim reports, tender portals, regulator pages, LinkedIn/company career pages, and credible trade press.
4. For technology sections, include relevant US diagnostics/health-tech players when they create a signal for Europe or Unilabs.
5. If no verified update exists for a competitor in the selected period, omit that competitor instead of writing filler.

GLOBAL OUTPUT REQUIREMENTS:
- Focus on real updates in the selected period, not generic company descriptions or stale background.
- Do not start by describing Unilabs unless the section-specific brief explicitly requires it.
- Do not use headings like "[Competitor] vs Unilabs"; write market-intel updates and implications.
- Target 120-220 words before references. Hard maximum: 260 words unless a required table needs more rows.
- Use 1-2 short subsections maximum, or a compact table when requested.
- Include only competitors/markets with meaningful verified signals. Omit no-update competitors.
- Include hard metrics wherever found: revenue, EBITDA/EBITA, growth %, market share %, deal values, tender values, job counts, contract durations.
- Cite material claims with compact numbered hyperlinks: <a href="[URL]" target="_blank" rel="noopener">[1]</a>.
- Include a source appendix at the bottom for consolidation: <div class="references"><h4>Source Appendix</h4><ol><li id="source-1"><a href="[URL]" target="_blank" rel="noopener">[Full source title]</a> - [publisher, date]</li></ol></div>
- Resolve source disagreements in prose using the most authoritative/latest source. Do not create discrepancy/conflict callouts.
- Highlight threats with <strong class="threat">...</strong> and opportunities with <strong class="opportunity">...</strong> only when useful.
- End with <div class="ci-implications"><h4>Implication for Unilabs</h4><ul> with 1-2 specific bullets.
- Clean HTML only. No markdown. No internal QA notes, validation summaries, confidence scores, or no-activity blocks.{lang_note}"""


def _user_prompt_research(agent, config, perspective_label):
    """User input for research agents."""
    competitors = _get_competitors(config)
    geo = "All selected Unilabs markets" if len(config.get("countries", [])) >= len(COUNTRIES) else ", ".join(config.get("countries", []))
    period = _period_scope(config)
    search_list = "\n".join(
        f'- Search: "{c} {agent["title"]} {period}"'
        for c in competitors
    )

    return f"""Write the "{agent['title']}" section for the Unilabs Market Intelligence report.

REPORT PARAMETERS:
- Period: {period}
- Markets: {geo}
- Competitors / players to check: {", ".join(competitors)}
- Research lens: {perspective_label}

EXECUTE THESE SEARCHES FIRST:
- Search: "{agent['title']} diagnostics {period} {geo}"
{search_list}
- Search official company news, filings/results, regulator pages, tender portals, LinkedIn/company career pages, and trade press for the selected period.

WRITING CHECKLIST:
- Selected-period updates only; no generic company descriptions.
- No "competitor name vs Unilabs" heading style.
- Omit competitors with no relevant update.
- Use table format when the section-specific brief requests a table.
- For financials, include latest figures and last-three-year revenue/EBITDA or EBITA table/chart-ready values where public.
- For hiring, include LinkedIn/career-page trend signals and role-family counts where public.
- Each material claim has a numbered clickable source link and an appendix entry.
- End with 1-2 practical implications for Unilabs.

Period: {period} | Markets: {geo}"""


def _sys_prompt_validator(agent, config):
    """System instructions for the Market Intel Validator."""
    competitors = _get_competitors(config)
    comp_list = ", ".join(competitors)
    period = _period_scope(config)
    rules = _section_rules(agent)

    return f"""You are a senior editor for Unilabs market intelligence reports.
You are merging two independent research outputs for the "{agent['title']}" section.

SELECTED PERIOD: {period}
COMPETITORS / PLAYERS CHECKED: {comp_list}

SECTION-SPECIFIC BRIEF:
{rules}

YOUR TASKS:
1. Merge the two versions into ONE authoritative HTML section of 160-240 words before references. Hard maximum: 300 words unless a required table needs more rows.
2. Keep only selected-period updates, latest public figures, and decision-useful implications.
3. Remove generic descriptions of Unilabs and competitors unless a sentence is necessary to understand the update.
4. Do not force every competitor into the output. Omit competitors with no meaningful update.
5. Do not use "[Competitor] vs Unilabs" headings.
6. Preserve or create compact tables when the section-specific brief requests tables, financials, market share, tenders, reputation, ESG, media, or hiring trends.
7. For Revenue & Financial Benchmarking, include a table/chart-ready block with last-three-year revenue and EBITDA/EBITA where public.
8. For Talent & Workforce Competition, include LinkedIn/career-site hiring trends, role-family counts, layoffs, or hiring surges where available.
9. For Market Share & Positioning, include market share %, Europe share, revenue, countries served, and growth projection in a simple table.
10. Resolve source disagreements in prose using the latest, official, or legally authoritative source. Do not create discrepancy/conflict callouts.
11. Convert citations to compact numbered links like <a href="[URL]" target="_blank" rel="noopener">[1]</a> and ensure each number has a matching source appendix item.
12. Produce a source appendix for the report builder to consolidate: <div class="references"><h4>Source Appendix</h4><ol><li id="source-1"><a href="[URL]" target="_blank" rel="noopener">[Title]</a> - [Publisher, Date]</li></ol></div>.
13. End with <div class="ci-implications"><h4>Implication for Unilabs</h4><ul><li>...</li></ul></div> using 1-2 specific bullets.
14. Do not include a validation summary, confidence score, internal QA note, no-activity block, or filler sentence.

OUTPUT: Clean HTML only. No markdown. No explanatory text outside HTML tags."""


def _validator_user_prompt(agent, out_a, out_b):
    return f"""Merge and validate these two market intelligence analyses for the "{agent['title']}" section.

=== UPDATE DISCOVERY VERSION (Agent A) ===
{out_a}

=== IMPACT ANALYSIS VERSION (Agent B) ===
{out_b}

Produce the single final merged HTML section following your system instructions exactly."""


# ====================================================================
# SINGLE AGENT EXECUTION  (dual-generate + validate)
# ====================================================================

async def run_single_agent(client, agent, config, provider="openai", on_status=None):
    """Returns (agent_id, output_a, output_b, validated, status, error)."""
    aid = agent["id"]
    out_a = out_b = validated = ""
    error = None

    if on_status:
        on_status(aid, "generating")

    try:
        if provider == "anthropic":
            out_a, out_b = await asyncio.gather(
                call_anthropic(
                    client,
                    _sys_prompt_research(agent, config, agent["agentA"]),
                    _user_prompt_research(agent, config, "Update discovery"),
                    use_web_search=True,
                ),
                call_anthropic(
                    client,
                    _sys_prompt_research(agent, config, agent["agentB"]),
                    _user_prompt_research(agent, config, "Impact analysis"),
                    use_web_search=True,
                ),
            )
        elif provider == "gemini":
            out_a, out_b = await asyncio.gather(
                call_gemini(
                    client,
                    _sys_prompt_research(agent, config, agent["agentA"]),
                    _user_prompt_research(agent, config, "Update discovery"),
                    use_google_search=True,
                ),
                call_gemini(
                    client,
                    _sys_prompt_research(agent, config, agent["agentB"]),
                    _user_prompt_research(agent, config, "Impact analysis"),
                    use_google_search=True,
                ),
            )
        else:
            out_a, out_b = await asyncio.gather(
                call_responses_search(
                    client,
                    _sys_prompt_research(agent, config, agent["agentA"]),
                    _user_prompt_research(agent, config, "Update discovery"),
                ),
                call_responses_search(
                    client,
                    _sys_prompt_research(agent, config, agent["agentB"]),
                    _user_prompt_research(agent, config, "Impact analysis"),
                ),
            )
    except Exception as e:
        log.error(f"Agent {aid} search error: {e}")
        error = str(e)
        if on_status:
            on_status(aid, "error")
        return aid, out_a, out_b, out_a or out_b or f"<p>Agent error: {error}</p>", "error", error

    if on_status:
        on_status(aid, "validating")

    try:
        if provider == "anthropic":
            validated = await call_anthropic(
                client,
                _sys_prompt_validator(agent, config),
                _validator_user_prompt(agent, out_a, out_b),
                use_web_search=False,
            )
        elif provider == "gemini":
            validated = await call_gemini(
                client,
                _sys_prompt_validator(agent, config),
                _validator_user_prompt(agent, out_a, out_b),
                use_google_search=False,
            )
        else:
            validated = await call_responses_validate(
                client,
                _sys_prompt_validator(agent, config),
                _validator_user_prompt(agent, out_a, out_b),
            )
    except Exception as e:
        log.warning(f"Agent {aid} validator error: {e}")
        validated = out_a   # fallback to first research version
        error = f"Validator failed: {e}"

    if on_status:
        on_status(aid, "done")
    return aid, out_a, out_b, validated, "done", error


# ====================================================================
# FULL RUN  —  ALL ENABLED AGENTS IN BATCHES
# ====================================================================

async def execute_full_run(config, api_key, provider="openai", enabled_ids=None, on_status=None, extra_agents=None):
    """Run all enabled agents in batches. Returns list of result dicts."""
    client      = api_key if provider in {"anthropic", "gemini"} else AsyncOpenAI(api_key=api_key)
    all_agents  = AGENTS + (extra_agents or [])
    agents_to_run = [a for a in all_agents if not enabled_ids or a["id"] in enabled_ids]
    results     = []

    for i in range(0, len(agents_to_run), BATCH_SIZE):
        batch = agents_to_run[i:i + BATCH_SIZE]
        batch_results = await asyncio.gather(*[
            run_single_agent(client, a, config, provider=provider, on_status=on_status)
            for a in batch
        ])
        for aid, oa, ob, val, status, err in batch_results:
            results.append({
                "agent_id": aid,
                "output_a": oa,
                "output_b": ob,
                "validated": val,
                "status": status,
                "error": err,
            })

    return results
