"""
Unilabs Competitive Intelligence Platform
Entry point — starts FastAPI + APScheduler.

Usage:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:8001 in your browser.
"""
import sys, os, logging, uvicorn

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from api import app  # noqa — imports the FastAPI app

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Unilabs Competitive Intelligence Platform")
    print("  22 CI Agents | OpenAI/Anthropic + Web Search | Cross-Validation")
    print("="*60)
    print("  Dashboard:  http://localhost:8001")
    print("  API docs:   http://localhost:8001/docs")
    print("  Scheduler:  Monday 10:00 CET (auto)")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
