"""
FastAPI backend -- REST endpoints for the Competitive Intelligence dashboard.
"""
import asyncio, os, json, logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel
from typing import List, Optional

from config import AGENTS, COUNTRIES, LANGUAGES, DEFAULT_COMPETITORS, BASE_DIR, REPORTS_DIR
import db
from agents import execute_full_run
from agents.report_builder import build_html_report
from agents.pdf_builder import build_pdf_report
from scheduler import (
    start_scheduler, get_scheduler_status, _run_scheduled,
    update_schedule, set_scheduler_enabled, set_report_frequency,
)

log = logging.getLogger("api")
app = FastAPI(title="Unilabs Competitive Intelligence Platform", version="1.0.0")

# Serve static files (if directory exists)
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    log.warning(f"Static directory not found at {static_dir}, skipping mount")


# --- Models ---------------------------------------------------------------
class RunConfig(BaseModel):
    years: List[int] = [2026]
    periods: List[str] = ["Q2"]
    countries: List[str] = [c["code"] for c in COUNTRIES]
    competitors: List[str] = DEFAULT_COMPETITORS
    custom_competitors: List[str] = []
    language: str = "en"
    enabled_agents: Optional[List[str]] = None
    report_frequency: str = "quarterly"
    custom_mode_id: Optional[int] = None
    dynamic_params: Optional[dict] = None

class CustomModeCreate(BaseModel):
    mode_name: str
    description: Optional[str] = ""
    dynamic_params: dict  # {focus_area, specific_threats, analysis_angle, key_questions}

class CustomModeUpdate(BaseModel):
    mode_name: Optional[str] = None
    description: Optional[str] = None
    dynamic_params: Optional[dict] = None

class ChatMessage(BaseModel):
    message: str
    history: Optional[List[dict]] = []

class APIKeys(BaseModel):
    openai_key: Optional[str] = None

class SchedulerConfig(BaseModel):
    enabled: Optional[bool] = None
    frequency: Optional[str] = None
    day_of_week: Optional[str] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None


# --- Startup --------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    db.init_db()
    start_scheduler()
    log.info("Competitive Intelligence Platform started.")


# --- Dashboard ------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def dashboard():
    path = os.path.join(BASE_DIR, "templates", "dashboard.html")
    try:
        with open(path, encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        log.warning(f"Dashboard template not found at {path}")
        # Fallback: Return a basic HTML page with API links
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Unilabs Competitive Intelligence</title></head>
        <body>
            <h1>Unilabs Competitive Intelligence Platform</h1>
            <p>Dashboard template not found. The API is running.</p>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/api/agents">Agents List</a></li>
                <li><a href="/api/runs">Runs History</a></li>
            </ul>
        </body>
        </html>
        """)


# --- API Keys -------------------------------------------------------------
@app.post("/api/keys")
def save_keys(keys: APIKeys):
    if keys.openai_key:
        db.set_setting("openai_key", keys.openai_key.strip())
    return {"status": "saved"}

@app.get("/api/keys/status")
def keys_status():
    return {
        "openai": bool(db.get_setting("openai_key")),
    }

@app.post("/api/keys/validate")
async def validate_keys(keys: APIKeys):
    """Test OpenAI key against the API before saving."""
    import httpx
    results = {"openai": None}

    async with httpx.AsyncClient() as client:
        ok = (keys.openai_key or "").strip()
        if not ok:
            ok = db.get_setting("openai_key", "")
        if ok:
            try:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {ok}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    results["openai"] = {"valid": True, "message": "Key is valid"}
                else:
                    err = resp.json().get("error", {}).get("message", resp.text[:200])
                    results["openai"] = {"valid": False, "message": f"{resp.status_code}: {err}"}
            except Exception as e:
                results["openai"] = {"valid": False, "message": str(e)[:200]}

    return results


# --- Config metadata ------------------------------------------------------
@app.get("/api/agents")
def get_agents():
    return AGENTS

@app.get("/api/countries")
def get_countries():
    return COUNTRIES

@app.get("/api/languages")
def get_languages():
    return LANGUAGES

@app.get("/api/competitors")
def get_competitors():
    return DEFAULT_COMPETITORS


# --- Trigger a run --------------------------------------------------------
@app.post("/api/runs")
async def trigger_run(config: RunConfig, background_tasks: BackgroundTasks):
    openai_key = db.get_setting("openai_key", "")
    if not openai_key:
        raise HTTPException(400, "OpenAI API key not set. Go to Admin Settings first.")

    run_id = db.create_run(config.dict(), trigger="manual")
    db.update_run(run_id, status="running")

    background_tasks.add_task(_execute_run_bg, run_id, config.dict(), openai_key)
    return {"run_id": run_id, "status": "started"}


async def _execute_run_bg(run_id, config, openai_key):
    agent_map = {a["id"]: a for a in AGENTS}
    enabled = config.get("enabled_agents")

    out_ids = {}
    for a in AGENTS:
        if enabled and a["id"] not in enabled:
            continue
        out_ids[a["id"]] = db.create_agent_output(run_id, a["id"], a["title"])

    def on_status(aid, status):
        if aid in out_ids:
            db.update_agent_output(out_ids[aid], status=status)

    try:
        results = await execute_full_run(config, openai_key,
                                         enabled_ids=enabled, on_status=on_status)
    except Exception as e:
        db.update_run(run_id, status="error", summary=str(e))
        return

    sections = []
    for r in results:
        if r["agent_id"] in out_ids:
            db.update_agent_output(out_ids[r["agent_id"]],
                output_a=r["output_a"], output_b=r["output_b"],
                validated=r["validated"], status=r["status"],
                finished_at=datetime.utcnow().isoformat(),
                error_msg=r.get("error"))
        agent = agent_map.get(r["agent_id"], {})
        sections.append({
            "agent_id": r["agent_id"],
            "title": agent.get("title", r["agent_id"]),
            "content": r["validated"],
            "color": agent.get("color", "#003366"),
        })

    html = build_html_report(sections, config)
    filename = f"ci_report_{run_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    db.update_run(run_id, status="completed", report_html=html,
                  summary=f"{len(sections)} competitive intel sections validated. File: {filename}")


# --- Runs -----------------------------------------------------------------
@app.get("/api/runs")
def list_runs():
    runs = db.list_runs()
    for r in runs:
        r["has_report"] = bool(r.get("report_html"))
        r.pop("report_html", None)
    return runs

@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    run["outputs"] = db.get_agent_outputs(run_id)
    return run

@app.get("/api/runs/{run_id}/report", response_class=HTMLResponse)
def get_report_html(run_id: int):
    run = db.get_run(run_id)
    if not run or not run.get("report_html"):
        raise HTTPException(404, "Report not found")
    return HTMLResponse(run["report_html"])

@app.get("/api/runs/{run_id}/outputs")
def get_run_outputs(run_id: int):
    return db.get_agent_outputs(run_id)


# --- PDF Download ---------------------------------------------------------
@app.get("/api/runs/{run_id}/pdf")
def download_pdf(run_id: int):
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.get("status") != "completed":
        raise HTTPException(400, "Run is not completed yet")

    outputs = db.get_agent_outputs(run_id)
    if not outputs:
        raise HTTPException(404, "No agent outputs found for this run")

    try:
        config = json.loads(run.get("config_json", "{}"))
    except Exception:
        config = {}

    agent_map = {a["id"]: a for a in AGENTS}
    sections = []
    for o in outputs:
        agent = agent_map.get(o["agent_id"], {})
        content = o.get("validated") or o.get("output_a") or ""
        if content:
            sections.append({
                "agent_id": o["agent_id"],
                "title": agent.get("title", o.get("agent_title", o["agent_id"])),
                "content": content,
                "color": agent.get("color", "#003366"),
            })

    if not sections:
        raise HTTPException(404, "No validated content to generate PDF")

    pdf_bytes = build_pdf_report(sections, config)
    filename = f"Unilabs_CI_Report_Run{run_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Scheduler ------------------------------------------------------------
@app.get("/api/scheduler")
def scheduler_status():
    return get_scheduler_status()

@app.post("/api/scheduler/trigger")
def manual_trigger(background_tasks: BackgroundTasks, frequency: str = "quarterly"):
    background_tasks.add_task(_run_scheduled, frequency)
    return {"status": "triggered", "frequency": frequency}

@app.post("/api/scheduler/config")
def update_scheduler_config(cfg: SchedulerConfig):
    if cfg.enabled is not None:
        set_scheduler_enabled(cfg.enabled)
    
    if cfg.frequency is not None:
        set_report_frequency(cfg.frequency)

    if cfg.frequency == "quarterly" and (cfg.day_of_week is not None or cfg.hour is not None or cfg.minute is not None):
        current = get_scheduler_status()
        cron = current.get("cron", {}).get("quarterly", {})
        day = cfg.day_of_week if cfg.day_of_week is not None else cron.get("day_of_week", "mon")
        hour = cfg.hour if cfg.hour is not None else cron.get("hour", 10)
        minute = cfg.minute if cfg.minute is not None else cron.get("minute", 0)
        update_schedule("quarterly", day_of_week=day, hour=hour, minute=minute)
    
    elif cfg.frequency == "monthly" and (cfg.day is not None or cfg.hour is not None or cfg.minute is not None):
        current = get_scheduler_status()
        cron = current.get("cron", {}).get("monthly", {})
        day = cfg.day if cfg.day is not None else cron.get("day", 1)
        hour = cfg.hour if cfg.hour is not None else cron.get("hour", 9)
        minute = cfg.minute if cfg.minute is not None else cron.get("minute", 0)
        update_schedule("monthly", day=day, hour=hour, minute=minute)

    return get_scheduler_status()


# --- Alerts ---------------------------------------------------------------
@app.get("/api/alerts")
def get_alerts(unread_only: bool = False):
    return db.list_alerts(unread_only=unread_only)


# --- Custom Modes ---------------------------------------------------------
@app.post("/api/custom-modes")
def create_custom_mode(req: CustomModeCreate):
    """Create a new custom analysis mode with dynamic parameters."""
    try:
        mode_id = db.create_custom_mode(
            mode_name=req.mode_name,
            description=req.description,
            dynamic_params=req.dynamic_params
        )
        return {
            "id": mode_id,
            "mode_name": req.mode_name,
            "description": req.description,
            "dynamic_params": req.dynamic_params,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to create custom mode: {str(e)}")

@app.get("/api/custom-modes")
def list_custom_modes():
    """List all custom analysis modes."""
    modes = db.list_custom_modes()
    return {"modes": modes, "count": len(modes)}

@app.get("/api/custom-modes/{mode_id}")
def get_custom_mode(mode_id: int):
    """Get a specific custom mode."""
    mode = db.get_custom_mode(mode_id)
    if not mode:
        raise HTTPException(404, "Custom mode not found")
    return mode

@app.put("/api/custom-modes/{mode_id}")
def update_custom_mode(mode_id: int, req: CustomModeUpdate):
    """Update a custom mode."""
    mode = db.get_custom_mode(mode_id)
    if not mode:
        raise HTTPException(404, "Custom mode not found")
    
    updates = {}
    if req.mode_name:
        updates["mode_name"] = req.mode_name
    if req.description:
        updates["description"] = req.description
    if req.dynamic_params:
        updates["dynamic_params"] = req.dynamic_params
    
    if updates:
        db.update_custom_mode(mode_id, **updates)
    
    return db.get_custom_mode(mode_id)

@app.delete("/api/custom-modes/{mode_id}")
def delete_custom_mode(mode_id: int):
    """Delete (disable) a custom mode."""
    mode = db.get_custom_mode(mode_id)
    if not mode:
        raise HTTPException(404, "Custom mode not found")
    
    db.delete_custom_mode(mode_id)
    return {"status": "deleted", "mode_id": mode_id}


# --- Chat Agent -----------------------------------------------------------
_CHAT_SYSTEM = """You are a Competitive Intelligence assistant for Unilabs.
You help users launch CI analysis runs by understanding their natural language requests.

AVAILABLE AGENTS (id -> title):
{agents}

AVAILABLE MARKETS: {markets}
AVAILABLE COMPETITORS: {competitors}

When the user asks to run analysis, respond with EXACTLY this JSON block (and nothing else before it):
```json
{{
  "action": "run",
  "agents": ["agent-id-1", "agent-id-2"],
  "markets": ["NL", "CH"],
  "period": "Q2",
  "year": 2026,
  "competitors": ["Synlab", "Eurofins"],
  "language": "en",
  "message": "A friendly confirmation message describing what you're launching"
}}
```

RULES for the JSON response:
- "agents": list of agent IDs to run. If user says "all" or is vague, include all agent IDs. If they mention specific topics, match to the closest agent IDs.
- "markets": list of country codes. If user says "all markets" or doesn't specify, include all market codes.
- "competitors": list of competitor names. If user doesn't specify, include all default competitors.
- "period": one of Q1,Q2,Q3,Q4,H1,H2,FY. Default to current quarter if not specified.
- "year": default to current year (2026) if not specified.
- "language": default "en" unless user specifies.
- "message": a friendly 1-2 sentence description of what will be launched.

If the user is just asking a question (not requesting a run), respond with:
```json
{{
  "action": "reply",
  "message": "Your helpful answer here"
}}
```

If the user's request is ambiguous, ask for clarification with "action": "reply".

Be concise, helpful, and knowledgeable about competitive intelligence in European diagnostics."""


@app.post("/api/chat")
async def chat_agent(msg: ChatMessage, background_tasks: BackgroundTasks):
    """GPT-powered chat agent that interprets user intent and triggers CI runs."""
    import httpx

    openai_key = db.get_setting("openai_key", "")
    if not openai_key:
        return {"action": "reply",
                "message": "Please configure your OpenAI API key in Admin Settings before using the chat agent."}

    # Build system prompt with available agents, markets, competitors
    agent_list = "\n".join(f'- {a["id"]}: {a["title"]}' for a in AGENTS)
    market_list = ", ".join(f'{c["code"]} ({c["name"]})' for c in COUNTRIES)
    comp_list = ", ".join(DEFAULT_COMPETITORS)

    system = _CHAT_SYSTEM.format(agents=agent_list, markets=market_list, competitors=comp_list)

    messages = [{"role": "system", "content": system}]
    # Add conversation history (last 10 turns)
    for h in (msg.history or [])[-10:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": msg.message})

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "max_tokens": 1024,
                    "temperature": 0.3,
                    "messages": messages,
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return {"action": "reply",
                        "message": f"API error ({resp.status_code}). Please check your OpenAI key."}
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return {"action": "reply", "message": f"Connection error: {str(e)[:200]}"}

    # Parse JSON from GPT response
    import re
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if not json_match:
        # Try bare JSON
        json_match = re.search(r'(\{[^{}]*"action"\s*:\s*"[^"]+?"[^{}]*\})', content, re.DOTALL)

    if not json_match:
        return {"action": "reply", "message": content}

    try:
        parsed = json.loads(json_match.group(1))
    except json.JSONDecodeError:
        return {"action": "reply", "message": content}

    action = parsed.get("action", "reply")

    if action == "run":
        # Validate agent IDs
        valid_ids = {a["id"] for a in AGENTS}
        agent_ids = [aid for aid in parsed.get("agents", []) if aid in valid_ids]
        if not agent_ids:
            return {"action": "reply",
                    "message": "I couldn't match any agents to your request. Could you be more specific about what competitive analysis you need?"}

        # Build run config
        run_config = {
            "years": [parsed.get("year", 2026)],
            "periods": [parsed.get("period", "Q2")],
            "countries": parsed.get("markets", [c["code"] for c in COUNTRIES]),
            "competitors": parsed.get("competitors", DEFAULT_COMPETITORS),
            "custom_competitors": [],
            "language": parsed.get("language", "en"),
            "enabled_agents": agent_ids,
        }

        # Trigger the run
        run_id = db.create_run(run_config, trigger="chat")
        db.update_run(run_id, status="running")
        background_tasks.add_task(_execute_run_bg, run_id, run_config, openai_key)

        agent_names = [a["title"] for a in AGENTS if a["id"] in agent_ids]
        friendly_msg = parsed.get("message", f"Launching {len(agent_ids)} CI agents.")

        return {
            "action": "run",
            "run_id": run_id,
            "agents": agent_ids,
            "agent_names": agent_names,
            "config": run_config,
            "message": friendly_msg,
        }
    else:
        return {"action": "reply", "message": parsed.get("message", content)}
