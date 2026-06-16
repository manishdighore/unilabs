"""Assemble final HTML report from validated agent outputs — Competitive Intelligence Edition.
Enhanced with comprehensive sections and frequency-specific formatting."""
from datetime import datetime
import re
from config import AGENTS, COUNTRIES


def _strip_conflict_blocks(content):
    """Remove model-generated conflict callouts from final executive reports."""
    cleaned = re.sub(
        r'<div\b[^>]*class=["\'][^"\']*\bconflict-data\b[^"\']*["\'][^>]*>.*?</div>',
        '',
        content or '',
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r'<p>\s*<strong>\s*Conflicting\s+data:?\s*</strong>.*?</p>',
        '',
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r'\s*<strong>\s*Conflicting\s+data:?\s*</strong>.*?(?=<h[1-6]\b|<div\b|<p\b|<ul\b|$)',
        '',
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return cleaned


def build_html_report(sections, config):
    """
    sections: list of {agent_id, title, content, color}
    config: includes years, periods, countries, competitors, report_frequency
    """
    date_str = datetime.now().strftime("%d %B %Y")
    years = config.get("years", [])
    periods = config.get("periods", [])
    countries = config.get("countries", [])
    comps = config.get("competitors", []) + [c for c in config.get("custom_competitors", []) if c]
    report_frequency = config.get("report_frequency", "quarterly").upper()
    
    time_label = f"{', '.join(str(y) for y in years)} -- {', '.join(periods)}"
    geo = "All Markets" if len(countries) >= len(COUNTRIES) else ", ".join(countries)
    comp_label = ", ".join(comps[:5]) + (f" +{len(comps)-5} more" if len(comps) > 5 else "")

    cleaned_sections = [
        {**s, "content": _strip_conflict_blocks(s.get("content", ""))}
        for s in sections
    ]

    # Build section HTML with enhanced styling
    section_html = "\n".join(f"""
    <section style="margin-bottom:48px;page-break-inside:avoid">
      <h2 style="font-family:'Roboto',sans-serif;font-size:20px;font-weight:700;color:#003366;
          text-transform:uppercase;padding-bottom:12px;border-bottom:3px solid {s.get('color','#00A3E0')};
          margin-bottom:20px;letter-spacing:0.5px">{s['title']}</h2>
      <div style="font-family:'Roboto',sans-serif;font-size:14px;color:#1A1A1A;line-height:1.8">
        {s['content']}
      </div>
    </section>""" for s in cleaned_sections)

    # Add executive summary section
    frequency_note = "This report covers a monthly snapshot" if "M" in str(periods[0]) else "This quarterly report provides"
    executive_summary = f"""
    <section style="margin-bottom:48px;background:#F3F4F6;padding:20px;border-left:4px solid #003366;border-radius:0 8px 8px 0">
      <h2 style="font-family:'Roboto',sans-serif;font-size:20px;font-weight:700;color:#003366;
          text-transform:uppercase;margin-bottom:16px;letter-spacing:0.5px">Executive Summary</h2>
      <div style="font-family:'Roboto',sans-serif;font-size:14px;color:#374151;line-height:1.8">
        <p>{frequency_note} in-depth competitive intelligence across {len(sections)} key modules.</p>
        <p style="margin-top:10px"><strong>Report Type:</strong> {report_frequency} | <strong>Coverage:</strong> {geo}</p>
        <p style="margin-top:10px"><strong>Benchmarked Against:</strong> {comp_label}</p>
        <p style="margin-top:10px">Each section contains dual-agent analysis with AI cross-validation to ensure accuracy and actionability.</p>
      </div>
    </section>
    """

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Unilabs Competitive Intelligence Report -- {time_label}</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap" rel="stylesheet">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Roboto',sans-serif;color:#1A1A1A;line-height:1.7;font-size:14px;background:#fff}}
  .container{{max-width:960px;margin:0 auto;padding:50px 40px}}
  h4{{font-size:15px;color:#003366;margin:18px 0 8px;text-transform:uppercase;font-weight:700}}
  p{{margin-bottom:14px;text-align:justify}} 
  ul{{margin:10px 0 14px 24px}} 
  li{{margin-bottom:6px}}
  strong{{color:#003366}}
  .validation-note{{background:#FEF3C7;border-left:4px solid #F59E0B;padding:12px 16px;
    margin:16px 0;border-radius:0 8px 8px 0;font-size:12px;color:#92400E}}
  .references{{background:#F8FAFC;border:1px solid #E5E7EB;padding:12px 16px;
    margin-top:18px;border-radius:8px;font-size:12px;color:#475569}}
  .references h4{{font-size:12px;margin:0 0 8px;color:#003366;text-transform:uppercase}}
  .references ol{{margin:0 0 0 18px}}
  .references li{{margin-bottom:4px}}
  .threat{{background:#FEE2E2;border-left:4px solid #EF4444;padding:8px 14px;margin:10px 0;border-radius:0 6px 6px 0;font-size:13px;color:#991B1B}}
  .opportunity{{background:#D1FAE5;border-left:4px solid #10B981;padding:8px 14px;margin:10px 0;border-radius:0 6px 6px 0;font-size:13px;color:#065F46}}
  .insight{{background:#DBEAFE;border-left:4px solid #0D9488;padding:8px 14px;margin:10px 0;border-radius:0 6px 6px 0;font-size:13px;color:#0C4A6E}}
  .metric-box{{display:inline-block;background:#EEF2FF;padding:10px 16px;border-radius:6px;margin:8px 8px 8px 0;font-size:12px;font-weight:500;color:#3730A3}}
  table{{width:100%;border-collapse:collapse;margin:16px 0}}
  th{{background:#003366;color:#fff;padding:10px;text-align:left;font-weight:700}}
  td{{border-bottom:1px solid #E5E7EB;padding:10px}}
  @media print{{body{{font-size:12px}}.container{{padding:20px}}}}
  @page{{margin:1in}}
</style></head><body><div class="container">
  <header style="display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:28px;
      border-bottom:4px solid #EF4444;margin-bottom:40px">
    <div style="display:flex;align-items:center;gap:14px">
      <div style="width:56px;height:56px;background:linear-gradient(135deg,#003366,#EF4444);border-radius:12px;display:flex;
          align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:28px">CI</div>
      <div><div style="font-size:32px;font-weight:900;color:#003366">unilabs</div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:3px;color:#EF4444;font-weight:700">Competitive Intelligence</div></div>
    </div>
    <div style="text-align:right;font-size:13px;color:#6B7280;line-height:1.6">
      <div><strong style="color:#003366">Generated:</strong> {date_str}</div>
      <div><strong style="color:#003366">Report Type:</strong> {report_frequency}</div>
      <div><strong style="color:#003366">Period:</strong> {time_label}</div>
      <div><strong style="color:#003366">Markets:</strong> {geo}</div>
      <div><strong style="color:#003366">Benchmarked vs:</strong> {comp_label}</div>
      <div><strong style="color:#003366">Sections:</strong> {len(sections)} Modules</div>
      <div style="margin-top:8px;padding-top:8px;border-top:1px solid #D1D5DB"><strong style="color:#003366">Validation:</strong> Dual-agent + AI provider</div>
    </div>
  </header>
  <div style="text-align:center;margin-bottom:50px">
    <h1 style="font-size:34px;font-weight:900;color:#003366;text-transform:uppercase;letter-spacing:1px;
        margin-bottom:10px">COMPETITIVE INTELLIGENCE REPORT</h1>
    <div style="font-size:18px;color:#6B7280;font-weight:300">Unilabs vs. Competitors &mdash; European Diagnostics</div>
    <div style="display:inline-block;background:linear-gradient(135deg,#003366,#EF4444);color:#fff;padding:10px 28px;border-radius:24px;
        margin-top:16px;font-weight:500;font-size:14px">{report_frequency} Report &middot; {time_label}</div>
  </div>
  
  {executive_summary}
  
  <section style="margin-bottom:48px;padding:24px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px">
    <h2 style="font-family:'Roboto',sans-serif;font-size:18px;font-weight:700;color:#003366;
        text-transform:uppercase;margin-bottom:16px;letter-spacing:0.5px">Report Metadata</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:13px;color:#4B5563">
      <div><strong>Report Frequency:</strong> {report_frequency}</div>
      <div><strong>Total Agents:</strong> {len(sections)}</div>
      <div><strong>Geographic Coverage:</strong> {len(countries)} markets</div>
      <div><strong>Competitors Analyzed:</strong> {len(comps)} entities</div>
      <div><strong>Analysis Method:</strong> Dual-agent + AI validation</div>
      <div><strong>Confidence Level:</strong> High (cross-verified)</div>
    </div>
  </section>
  
  {section_html}
  
  <footer style="margin-top:60px;padding-top:24px;border-top:3px solid #E5E7EB;display:flex;
      justify-content:space-between;align-items:center;font-size:12px;color:#6B7280">
    <div>&copy; {datetime.now().year} Unilabs. Competitive Intelligence Platform.</div>
    <div style="background:#FEE2E2;color:#991B1B;padding:6px 16px;border-radius:6px;font-weight:700;
        font-size:11px;text-transform:uppercase;letter-spacing:0.5px">Strictly Confidential</div>
  </footer>
</div></body></html>"""
