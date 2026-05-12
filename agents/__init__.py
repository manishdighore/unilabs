"""
Multi-agent engine: dual GPT-4o generation (with web search) + GPT-4o cross-validation.
Competitive Intelligence Edition — all prompts centre on Unilabs vs. competitors.
"""
import asyncio, httpx, json, logging
from datetime import datetime
from config import AGENTS, BATCH_SIZE, LANGUAGES

log = logging.getLogger("agents")

# ====================================================================
# API CALLERS
# ====================================================================

async def call_openai_search(client: httpx.AsyncClient, api_key: str,
                              system: str, user: str) -> str:
    """GPT-4o with web search enabled (used for Agent A & B research)."""
    resp = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-search-preview",
            "max_tokens": 4096,
            "web_search_options": {
                "search_context_size": "medium",
            },
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=180,
    )
    if resp.status_code != 200:
        body = resp.text[:500]
        log.error(f"OpenAI Search API {resp.status_code}: {body}")
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


async def call_openai(client: httpx.AsyncClient, api_key: str,
                      system: str, user: str) -> str:
    """Standard GPT-4o (used for validation)."""
    resp = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o",
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=120,
    )
    if resp.status_code != 200:
        body = resp.text[:500]
        log.error(f"OpenAI API {resp.status_code}: {body}")
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ====================================================================
# PROMPT BUILDERS — COMPETITIVE INTELLIGENCE FOCUSED
# ====================================================================
def _sys_prompt(agent, config, focus):
    lang = config.get("language", "en")
    lang_name = next((l["name"] for l in LANGUAGES if l["code"] == lang), "English")
    lang_note = f"\nIMPORTANT: Write the entire output in {lang_name}." if lang != "en" else ""

    competitors = config.get("competitors", []) + [c for c in config.get("custom_competitors", []) if c]
    comp_list = ", ".join(competitors) if competitors else "all major European diagnostics competitors"

    return f"""You are a senior competitive intelligence analyst writing for Unilabs executive leadership.
Unilabs operates diagnostic labs, pathology, radiology, and genetics services across NL, CH, CEE, PT, UAE, NO, SE, FI, DK, UK, FR.

YOUR PRIMARY MISSION: Every insight MUST be framed as "Unilabs vs. competitors".
Never write generic market commentary. Always position findings relative to Unilabs.

COMPETITORS TO BENCHMARK AGAINST: {comp_list}

SECTION: "{agent['title']}"
FOCUS: {focus}

RULES:
- Search the web for the LATEST competitive intelligence on Unilabs and its competitors.
- ALWAYS compare Unilabs position against specific named competitors with evidence.
- Include specific numbers: revenue, market share %, deal sizes, lab counts, contract values.
- For every competitor move, state the IMPLICATION for Unilabs.
- Flag competitive THREATS in bold and competitive OPPORTUNITIES with emphasis.
- Executive tone, third person, data-driven, concise.
- Structure with <h4>, <p>, <strong>, <ul>, <li> HTML tags.
- 400-700 words of substantive competitive analysis.
- EU/European focus aligned with Unilabs markets.
- Cite sources where possible.
- End with a "Competitive Implications for Unilabs" subsection.{lang_note}"""


def _user_prompt(agent, config):
    allc = config.get("competitors", []) + [c for c in config.get("custom_competitors", []) if c]
    geo = "All Unilabs Markets" if len(config.get("countries", [])) >= 11 else ", ".join(config.get("countries", []))
    time = f"{', '.join(str(y) for y in config.get('years', []))}"
    periods = ', '.join(config.get('periods', []))
    return f"""Search the web and write the "{agent['title']}" section for the Unilabs Competitive Intelligence Report.

CRITICAL: This is NOT a generic market report. Every finding must explicitly compare Unilabs against: {', '.join(allc)}

Period: {time} {periods}  |  Markets: {geo}
Competitors: {', '.join(allc)}

For each key finding:
1. State what the competitor did or what the market data shows
2. State how Unilabs compares (ahead, behind, at parity)
3. State the strategic implication for Unilabs

Use HTML formatting. Be specific, data-driven, and cite recent sources.
End with a "Competitive Implications for Unilabs" section with 3-5 actionable bullet points."""


def _validator_prompt(agent, out_a, out_b):
    return f"""You are a QA analyst reviewing two independent competitive intelligence analyses of "{agent['title']}".

VERSION A:
{out_a}

VERSION B:
{out_b}

TASK:
1. Compare for accuracy, completeness, and contradictions.
2. Produce ONE FINAL HTML version (500-800 words) merging the best competitive insights from both.
3. ENSURE every section explicitly compares Unilabs vs named competitors.
4. Remove any generic market commentary that lacks competitive comparison.
5. Flag unverifiable claims with [UNVERIFIED].
6. Strengthen the "Competitive Implications for Unilabs" section with specific, actionable recommendations.
7. End with <div class="validation-note"> containing:
   - Agreement score (% of consistent facts)
   - Discrepancy count and resolutions
   - Competitive data confidence rating (High/Medium/Low)"""


# ====================================================================
# SINGLE AGENT EXECUTION (dual-generate + validate)
# ====================================================================
async def run_single_agent(client, agent, config, openai_key, on_status=None):
    """Returns (agent_id, output_a, output_b, validated, status, error)."""
    aid = agent["id"]
    user_prompt = _user_prompt(agent, config)
    out_a = out_b = validated = ""
    error = None

    if on_status:
        on_status(aid, "generating")

    try:
        out_a, out_b = await asyncio.gather(
            call_openai_search(client, openai_key,
                               _sys_prompt(agent, config, agent["agentA"]), user_prompt),
            call_openai_search(client, openai_key,
                               _sys_prompt(agent, config, agent["agentB"]), user_prompt),
        )
    except Exception as e:
        log.error(f"Agent {aid} GPT search error: {e}")
        error = str(e)
        if on_status:
            on_status(aid, "error")
        return aid, out_a, out_b, out_a or out_b, "error", error

    if on_status:
        on_status(aid, "validating")

    try:
        val_sys = ("You are an expert competitive intelligence fact-checker for Unilabs executive reports. "
                   "Ensure every claim is framed as Unilabs vs. competitor comparison. Output clean HTML only.")
        validated = await call_openai(client, openai_key, val_sys,
                                      _validator_prompt(agent, out_a, out_b))
    except Exception as e:
        log.warning(f"Agent {aid} validator error: {e}")
        validated = out_a  # fallback
        error = f"Validator failed: {e}"

    if on_status:
        on_status(aid, "done")
    return aid, out_a, out_b, validated, "done", error


# ====================================================================
# FULL RUN -- ALL ENABLED AGENTS IN BATCHES
# ====================================================================
async def execute_full_run(config, openai_key, enabled_ids=None, on_status=None):
    """Run all enabled agents in batches. Returns list of result dicts."""
    agents = [a for a in AGENTS if not enabled_ids or a["id"] in enabled_ids]
    results = []

    async with httpx.AsyncClient() as client:
        for i in range(0, len(agents), BATCH_SIZE):
            batch = agents[i:i + BATCH_SIZE]
            batch_results = await asyncio.gather(*[
                run_single_agent(client, a, config, openai_key, on_status)
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
