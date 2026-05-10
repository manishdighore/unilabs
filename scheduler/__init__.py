"""
APScheduler integration — configurable cron schedule + manual trigger.
Supports both quarterly and monthly scheduling.
"""
import asyncio, logging, json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

from config import AGENTS, DEFAULT_COMPETITORS, COUNTRIES, REPORT_FREQUENCIES, DEFAULT_REPORT_FREQUENCY
import db
from agents import execute_full_run
from agents.report_builder import build_html_report

log = logging.getLogger("scheduler")
scheduler = BackgroundScheduler(timezone="Europe/Amsterdam")


def _default_config(report_frequency="quarterly"):
    """Config used for scheduled runs."""
    current_month = datetime.now().month
    current_quarter = (current_month - 1) // 3 + 1
    
    return {
        "years": [datetime.now().year],
        "periods": [f"Q{current_quarter}"] if report_frequency in ["quarterly", "both"] else [f"M{current_month}"],
        "countries": [c["code"] for c in COUNTRIES],
        "competitors": DEFAULT_COMPETITORS,
        "custom_competitors": [],
        "language": "en",
        "report_frequency": report_frequency,
    }


def _run_scheduled(report_frequency="quarterly"):
    """Blocking wrapper for the async pipeline, called by APScheduler."""
    log.info(f"Scheduled competitive intel run triggered ({report_frequency})")
    openai_key = db.get_setting("openai_key", "")
    if not openai_key:
        log.error("Scheduled run aborted -- OpenAI API key not set.")
        return

    config = _default_config(report_frequency)
    run_id = db.create_run(config, trigger="scheduled")

    try:
        db.update_run(run_id, status="running")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            execute_full_run(config, openai_key)
        )
        loop.close()
    except Exception as e:
        log.error(f"Scheduled run error: {e}")
        db.update_run(run_id, status="error", summary=str(e))
        return

    agent_map = {a["id"]: a for a in AGENTS}
    sections = []
    for r in results:
        out_id = db.create_agent_output(run_id, r["agent_id"], agent_map[r["agent_id"]]["title"])
        db.update_agent_output(out_id,
            output_a=r["output_a"], output_b=r["output_b"],
            validated=r["validated"], status=r["status"],
            finished_at=datetime.utcnow().isoformat(),
            error_msg=r.get("error"))
        sections.append({
            "agent_id": r["agent_id"],
            "title": agent_map[r["agent_id"]]["title"],
            "content": r["validated"],
            "color": agent_map[r["agent_id"]]["color"],
        })

    html = build_html_report(sections, config)
    db.update_run(run_id, status="completed", report_html=html,
                  summary=f"{len(sections)} competitive intel sections generated and validated ({report_frequency.upper()}).")
    log.info(f"Scheduled run #{run_id} completed -- {len(sections)} sections ({report_frequency}).")


def start_scheduler():
    """Initialize both quarterly and monthly schedulers if enabled."""
    # Read frequency preference from settings
    freq_setting = db.get_setting("report_frequency", DEFAULT_REPORT_FREQUENCY)
    
    # Load quarterly schedule
    quarterly_cron = db.get_setting("scheduler_cron_quarterly")
    if quarterly_cron:
        try:
            quarterly_cron = json.loads(quarterly_cron)
        except Exception:
            quarterly_cron = {"day_of_week": "mon", "hour": 10, "minute": 0}
    else:
        quarterly_cron = {"day_of_week": "mon", "hour": 10, "minute": 0}
    
    # Load monthly schedule
    monthly_cron = db.get_setting("scheduler_cron_monthly")
    if monthly_cron:
        try:
            monthly_cron = json.loads(monthly_cron)
        except Exception:
            monthly_cron = {"day": "1", "hour": "9", "minute": "0"}
    else:
        monthly_cron = {"day": "1", "hour": "9", "minute": "0"}
    
    enabled = db.get_setting("scheduler_enabled", "true") == "true"

    # Schedule quarterly report if needed
    if freq_setting in ["quarterly", "both"]:
        scheduler.add_job(
            lambda: _run_scheduled("quarterly"),
            CronTrigger(
                day_of_week=quarterly_cron.get("day_of_week", "mon"),
                hour=int(quarterly_cron.get("hour", 10)),
                minute=int(quarterly_cron.get("minute", 0)),
                timezone="Europe/Amsterdam",
            ),
            id="quarterly_report",
            name="Quarterly Competitive Intel Report",
            replace_existing=True,
        )
        log.info("Quarterly report scheduler initialized")

    # Schedule monthly report if needed
    if freq_setting in ["monthly", "both"]:
        scheduler.add_job(
            lambda: _run_scheduled("monthly"),
            CronTrigger(
                day=int(monthly_cron.get("day", 1)),
                hour=int(monthly_cron.get("hour", 9)),
                minute=int(monthly_cron.get("minute", 0)),
                timezone="Europe/Amsterdam",
            ),
            id="monthly_report",
            name="Monthly Competitive Intel Report",
            replace_existing=True,
        )
        log.info("Monthly report scheduler initialized")

    scheduler.start()

    if not enabled:
        if freq_setting in ["quarterly", "both"]:
            scheduler.pause_job("quarterly_report")
        if freq_setting in ["monthly", "both"]:
            scheduler.pause_job("monthly_report")
        log.info("Scheduler started (paused).")
    else:
        log.info(f"Scheduler started -- {freq_setting} report(s) enabled.")


def update_schedule(frequency="quarterly", day_of_week=None, day=None, hour=10, minute=0):
    """Update schedule for specified frequency."""
    if frequency == "quarterly" and day_of_week:
        cron = {"day_of_week": day_of_week, "hour": hour, "minute": minute}
        db.set_setting("scheduler_cron_quarterly", json.dumps(cron))
        scheduler.reschedule_job(
            "quarterly_report",
            trigger=CronTrigger(
                day_of_week=day_of_week,
                hour=int(hour),
                minute=int(minute),
                timezone="Europe/Amsterdam",
            ),
        )
        log.info(f"Quarterly schedule updated: {day_of_week} {hour}:{minute:02d} CET")
    
    elif frequency == "monthly" and day:
        cron = {"day": day, "hour": hour, "minute": minute}
        db.set_setting("scheduler_cron_monthly", json.dumps(cron))
        if scheduler.get_job("monthly_report"):
            scheduler.reschedule_job(
                "monthly_report",
                trigger=CronTrigger(
                    day=int(day),
                    hour=int(hour),
                    minute=int(minute),
                    timezone="Europe/Amsterdam",
                ),
            )
        log.info(f"Monthly schedule updated: day {day} {hour}:{minute:02d} CET")


def set_scheduler_enabled(enabled: bool):
    """Enable/disable all configured schedulers."""
    db.set_setting("scheduler_enabled", "true" if enabled else "false")
    freq = db.get_setting("report_frequency", DEFAULT_REPORT_FREQUENCY)
    
    if enabled:
        if freq in ["quarterly", "both"] and scheduler.get_job("quarterly_report"):
            scheduler.resume_job("quarterly_report")
        if freq in ["monthly", "both"] and scheduler.get_job("monthly_report"):
            scheduler.resume_job("monthly_report")
        log.info("Scheduler resumed.")
    else:
        if scheduler.get_job("quarterly_report"):
            scheduler.pause_job("quarterly_report")
        if scheduler.get_job("monthly_report"):
            scheduler.pause_job("monthly_report")
        log.info("Scheduler paused.")


def set_report_frequency(frequency: str):
    """Set report frequency (monthly, quarterly, or both)."""
    if frequency not in REPORT_FREQUENCIES:
        raise ValueError(f"Invalid frequency. Must be one of: {REPORT_FREQUENCIES}")
    
    db.set_setting("report_frequency", frequency)
    
    # Recreate jobs based on new frequency
    if scheduler.get_job("quarterly_report"):
        scheduler.remove_job("quarterly_report")
    if scheduler.get_job("monthly_report"):
        scheduler.remove_job("monthly_report")
    
    # Reinitialize with new frequency
    start_scheduler()
    log.info(f"Report frequency updated to: {frequency}")


def get_scheduler_status():
    """Get current scheduler status and configuration."""
    jobs = scheduler.get_jobs()
    enabled = db.get_setting("scheduler_enabled", "true") == "true"
    frequency = db.get_setting("report_frequency", DEFAULT_REPORT_FREQUENCY)
    
    quarterly_cron = db.get_setting("scheduler_cron_quarterly")
    if quarterly_cron:
        try:
            quarterly_cron = json.loads(quarterly_cron)
        except Exception:
            quarterly_cron = {"day_of_week": "mon", "hour": 10, "minute": 0}
    else:
        quarterly_cron = {"day_of_week": "mon", "hour": 10, "minute": 0}
    
    monthly_cron = db.get_setting("scheduler_cron_monthly")
    if monthly_cron:
        try:
            monthly_cron = json.loads(monthly_cron)
        except Exception:
            monthly_cron = {"day": "1", "hour": "9", "minute": "0"}
    else:
        monthly_cron = {"day": "1", "hour": "9", "minute": "0"}

    result = {
        "enabled": enabled,
        "frequency": frequency,
        "cron": {
            "quarterly": quarterly_cron,
            "monthly": monthly_cron,
        },
        "jobs": [],
    }
    for j in jobs:
        result["jobs"].append({
            "id": j.id,
            "name": j.name,
            "next_run": str(j.next_run_time) if j.next_run_time else None,
            "trigger": str(j.trigger),
        })
    return result
