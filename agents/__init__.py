"""
Multi-agent engine: OpenAI Responses API with web_search_preview tool.
Competitive Intelligence Edition — Unilabs vs. named competitors.

API:   OpenAI Responses API  (client.responses.create)
Model: hardcoded constants below — change SEARCH_MODEL / VALIDATOR_MODEL as needed
"""
import asyncio, logging
import httpx
from openai import AsyncOpenAI
from config import AGENTS, BATCH_SIZE, LANGUAGES, COUNTRIES

log = logging.getLogger("agents")

# ── Model configuration (hardcoded — change here to switch models) ─────────
SEARCH_MODEL    = "gpt-5.5"   # Research agents: Responses API + web_search_preview
VALIDATOR_MODEL = "gpt-5.5"   # CI Validator:    Responses API, synthesis only
ANTHROPIC_MODEL = "claude-sonnet-4-6"
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
    """Responses API for CI Validator — synthesis and QA, no additional web search."""
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
        "temperature": 0.2,
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


# ====================================================================
# HELPERS
# ====================================================================

def _get_competitors(config):
    """Merge named competitors + any custom competitors from this run's config."""
    return (
        config.get("competitors", []) +
        [c for c in config.get("custom_competitors", []) if c]
    )


# ====================================================================
# PROMPT BUILDERS — COMPETITIVE INTELLIGENCE FOCUSED
# ====================================================================

def _sys_prompt_research(agent, config, focus):
    """System instructions for research agents (used in Responses API `instructions` field)."""
    lang      = config.get("language", "en")
    lang_name = next((l["name"] for l in LANGUAGES if l["code"] == lang), "English")
    lang_note = f"\nIMPORTANT: Write the entire output in {lang_name}." if lang != "en" else ""
    competitors = _get_competitors(config)
    comp_list   = ", ".join(competitors) if competitors else "all major European diagnostics competitors"
    market_list = ", ".join(f'{c["code"]} ({c["name"]})' for c in COUNTRIES)

    return f"""You are a senior competitive intelligence analyst writing for Unilabs executive leadership.
Unilabs operates diagnostic labs, pathology, radiology, and genetics services across these configured markets: {market_list}.

ANALYSIS SECTION: "{agent['title']}"
RESEARCH FOCUS: {focus}
COMPETITORS YOU MUST COVER: {comp_list}

MANDATORY WEB SEARCH PROTOCOL — execute ALL searches before writing:
1. Search "Unilabs {agent['title']} 2025 2026" — Unilabs' own position and announcements
2. For EACH competitor listed, search "[CompetitorName] {agent['title']} 2025 2026"
3. Search "[CompetitorName] diagnostics strategy announcement press release 2026" for each
4. Search "European diagnostics market {agent['title']} 2026 competitive"
5. Search for earnings calls, investor presentations, and trade publications for each entity

COMPETITOR SILENCE RULE (mandatory):
If you find NO verified public information for a specific competitor in this topic area, you MUST include this block:
<div class="no-activity"><strong>[CompetitorName] — No significant public activity detected</strong>:
No press releases, financial disclosures, or verified trade reports found for this period in this area.
This may indicate a strategic pause, private execution, or limited public disclosure.
<em>Recommendation: Unilabs should monitor this competitor closely for delayed announcements.</em></div>

OUTPUT REQUIREMENTS:
- Start with <div class="unilabs-summary"><h4>Unilabs Current-State Summary</h4><p>...</p></div> summarizing what is publicly known about Unilabs in this section and selected markets before comparing competitors
- 700–1000 words of substantive, specific competitive analysis
- Every paragraph must name at least one competitor and compare to Unilabs explicitly
- Include hard metrics wherever found: revenue (€M), growth %, lab counts, deal values, headcount, contract durations
- HTML structure: <h4> for subsections, <p> for body, <strong> for key data, <ul><li> for lists
- Cite EVERY claim with a clickable hyperlink — format: <a href="[URL]" target="_blank" rel="noopener">[Source Name, Month Year]</a>
  Example: <a href="https://www.synlab.com/investors/annual-report-2025" target="_blank" rel="noopener">(Synlab Annual Report, March 2026)</a>
- If the URL is not available, still cite: <em>[Source Name, Month Year — URL unavailable]</em>
- Include a REFERENCES section at the bottom listing all cited URLs as a numbered <ol> with <a href> links
- Highlight THREATS: wrap in <strong class="threat"> ... </strong>
- Highlight OPPORTUNITIES: wrap in <strong class="opportunity"> ... </strong>
- End with: <div class="ci-implications"><h4>Competitive Implications for Unilabs</h4><ul> followed by 5–6 specific, actionable bullets
- Then: <div class="references"><h4>References</h4><ol> with each source as <li><a href="[URL]" target="_blank" rel="noopener">[Full source title]</a> — [publisher, date]</li>
- Executive tone, third person, data-driven, no generic market filler{lang_note}"""


def _user_prompt_research(agent, config, perspective_label):
    """User input for research agents."""
    competitors = _get_competitors(config)
    geo         = "All Unilabs Markets" if len(config.get("countries", [])) >= len(COUNTRIES) else ", ".join(config.get("countries", []))
    years       = ", ".join(str(y) for y in config.get("years", []))
    periods     = ", ".join(config.get("periods", []))

    search_list = "\n".join(
        f'- Search: "{c} {agent["title"]} {years}"'
        for c in competitors
    )

    return f"""Write the "{agent['title']}" section — {perspective_label} perspective — for the Unilabs Competitive Intelligence Report.

REPORT PARAMETERS:
- Period: {years} {periods}
- Markets: {geo}
- Competitors to cover: {", ".join(competitors)}

EXECUTE THESE SEARCHES FIRST (before writing):
- Search: "Unilabs {agent['title']} {years}"
{search_list}
- Search: "{agent['title']} European diagnostics {years} trends"
- Search: "Unilabs competitors Europe {years} strategy"

WRITING CHECKLIST (all items required):
☑ 2-sentence executive summary of the competitive landscape
☑ "Unilabs Current-State Summary" block at the top, describing what is known about Unilabs for this topic and market scope
☑ Dedicated paragraph or sub-section per competitor (or explicit "no activity" block)
☑ Unilabs vs. each competitor: who is ahead, behind, or at parity — with evidence
☑ Quantitative data wherever available (€, %, lab counts, deal sizes)
☑ Every claim cited with a clickable <a href> link to the source URL
☑ All source URLs collected in a numbered References list at the bottom
☑ Threats and opportunities marked with the correct HTML class
☑ "Competitive Implications for Unilabs" section with 5–6 actionable bullets
☑ References section (<div class="references">) with numbered clickable links

Period: {years} {periods} | Markets: {geo}"""


def _sys_prompt_validator(agent, config):
    """System instructions for the CI Validator."""
    competitors = _get_competitors(config)
    comp_list   = ", ".join(competitors)

    return f"""You are a senior QA analyst and competitive intelligence editor for Unilabs executive reports.
You are merging two independent research outputs for the "{agent['title']}" section.

COMPETITORS THAT MUST APPEAR IN THE FINAL OUTPUT: {comp_list}

YOUR TASKS:
1. Merge the two versions into ONE authoritative HTML section (700–900 words)
2. Resolve contradictions: keep the better-sourced claim; note unresolved discrepancies with [CONFLICTING DATA]
3. Ensure EVERY competitor in the list appears — add a "no activity detected" block for any that are missing
4. Remove all generic market commentary that lacks a specific Unilabs vs. competitor comparison
5. Strengthen quantitative claims — prefer exact figures over vague language
6. Ensure the final section starts with <div class="unilabs-summary"><h4>Unilabs Current-State Summary</h4><p>...</p></div>
7. Ensure "Competitive Implications for Unilabs" has 5–6 specific, actionable bullets
8. Preserve <strong class="threat"> and <strong class="opportunity"> markup
9. Consolidate all hyperlinked citations from both versions — keep every <a href> link that points to a real URL; remove any dead placeholder links
10. Produce a merged References section: <div class="references"><h4>References</h4><ol> with deduplicated, numbered <li><a href="[URL]" target="_blank" rel="noopener">[Title]</a> — [Publisher, Date]</li> entries
11. Append this block at the very end:
<div class="validation-note">
  <strong>Validation Summary</strong>
  <ul>
    <li>Competitors with verified data: [list]</li>
    <li>Competitors with no public activity: [list or "None"]</li>
    <li>Version agreement score: [X]%</li>
    <li>Confidence by competitor: [CompetitorName: High/Medium/Low/No Data, ...]</li>
    <li>Overall section confidence: [High/Medium/Low]</li>
    <li>Total references included: [N] links</li>
  </ul>
</div>

OUTPUT: Clean HTML only. No markdown. No explanatory text outside HTML tags."""


def _validator_user_prompt(agent, out_a, out_b):
    return f"""Merge and validate these two competitive intelligence analyses for the "{agent['title']}" section.

=== UNILABS RESEARCH VERSION (Agent A) ===
{out_a}

=== COMPETITOR INTELLIGENCE VERSION (Agent B) ===
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
                    _user_prompt_research(agent, config, "Unilabs Research"),
                    use_web_search=True,
                ),
                call_anthropic(
                    client,
                    _sys_prompt_research(agent, config, agent["agentB"]),
                    _user_prompt_research(agent, config, "Competitor Intelligence"),
                    use_web_search=True,
                ),
            )
        else:
            out_a, out_b = await asyncio.gather(
                call_responses_search(
                    client,
                    _sys_prompt_research(agent, config, agent["agentA"]),
                    _user_prompt_research(agent, config, "Unilabs Research"),
                ),
                call_responses_search(
                    client,
                    _sys_prompt_research(agent, config, agent["agentB"]),
                    _user_prompt_research(agent, config, "Competitor Intelligence"),
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
        else:
            validated = await call_responses_validate(
                client,
                _sys_prompt_validator(agent, config),
                _validator_user_prompt(agent, out_a, out_b),
            )
    except Exception as e:
        log.warning(f"Agent {aid} validator error: {e}")
        validated = out_a   # fallback to Unilabs Research version
        error = f"Validator failed: {e}"

    if on_status:
        on_status(aid, "done")
    return aid, out_a, out_b, validated, "done", error


# ====================================================================
# FULL RUN  —  ALL ENABLED AGENTS IN BATCHES
# ====================================================================

async def execute_full_run(config, api_key, provider="openai", enabled_ids=None, on_status=None, extra_agents=None):
    """Run all enabled agents in batches. Returns list of result dicts."""
    client      = api_key if provider == "anthropic" else AsyncOpenAI(api_key=api_key)
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
