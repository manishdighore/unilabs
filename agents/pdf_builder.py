"""
PDF report builder — generates a professional market intelligence PDF
from validated agent outputs using reportlab.
"""
import io, re, html as html_mod
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate
from config import COUNTRIES
from agents.report_builder import _prepare_report_sections


# --- Colors ---------------------------------------------------------------
NAVY   = HexColor("#003366")
CYAN   = HexColor("#00A3E0")
RED    = HexColor("#EF4444")
DARK   = HexColor("#1A1A1A")
GRAY   = HexColor("#6B7280")
LGRAY  = HexColor("#F3F4F6")
AMBER  = HexColor("#F59E0B")
GREEN  = HexColor("#10B981")
PURPLE = HexColor("#8B5CF6")


def _esc(text):
    """Escape bare ampersands for reportlab XML."""
    if not text:
        return ""
    return re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', '&amp;', text)


def _strip_html(text):
    """Remove HTML tags and decode entities for plain-text extraction."""
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        r'<link href="\1" color="blue">\2</link>',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r'<tr[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<t[dh][^>]*>', ' | ', text, flags=re.IGNORECASE)
    text = re.sub(r'</t[dh]>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<li\b[^>]*>', '  - ', text)
    text = re.sub(r'</?(ul|ol|div|section|span|table|tr|td|th|thead|tbody)[^>]*>', '', text)
    text = re.sub(r'<h[1-6][^>]*>', '\n', text)
    text = re.sub(r'</h[1-6]>', '\n', text)
    text = re.sub(r'<p[^>]*>', '\n', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<strong[^>]*>', '<b>', text)
    text = re.sub(r'</strong>', '</b>', text)
    text = re.sub(r'<em[^>]*>', '<i>', text)
    text = re.sub(r'</em>', '</i>', text)
    text = re.sub(r'<(?!/?(?:b|i|link)\b)[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', '&amp;', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _source_item_to_text(item):
    """Preserve source URLs when converting appendix HTML to PDF text."""
    def replace_link(match):
        url = match.group(1)
        label = _strip_html(match.group(2))
        return f"{label} ({url})"

    text = re.sub(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        replace_link,
        item or "",
        flags=re.IGNORECASE | re.DOTALL,
    )
    return _strip_html(text)


def _make_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "PDFTitle", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=26, leading=32,
            textColor=NAVY, alignment=TA_CENTER, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "PDFSubtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=12, leading=16,
            textColor=GRAY, alignment=TA_CENTER, spaceAfter=20,
        ),
        "meta": ParagraphStyle(
            "PDFMeta", parent=base["Normal"],
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=GRAY, alignment=TA_CENTER, spaceAfter=6,
        ),
        "section_title": ParagraphStyle(
            "PDFSectionTitle", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=13, leading=18,
            textColor=NAVY, spaceBefore=18, spaceAfter=8,
            borderPadding=(0, 0, 4, 0),
        ),
        "body": ParagraphStyle(
            "PDFBody", parent=base["Normal"],
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "PDFBullet", parent=base["Normal"],
            fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=DARK, leftIndent=16, spaceAfter=4,
        ),
        "validation_note": ParagraphStyle(
            "PDFValidation", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=8, leading=11,
            textColor=HexColor("#92400E"), spaceAfter=6,
            leftIndent=8, borderPadding=(4, 4, 4, 4),
        ),
        "footer": ParagraphStyle(
            "PDFFooter", parent=base["Normal"],
            fontName="Helvetica", fontSize=7, leading=10,
            textColor=GRAY, alignment=TA_CENTER,
        ),
        "toc_item": ParagraphStyle(
            "PDFTocItem", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=16,
            textColor=NAVY, spaceAfter=4, leftIndent=8,
        ),
    }
    return styles


def _header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4

    # Header accent line — gradient navy to red
    canvas_obj.setStrokeColor(RED)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(25*mm, h - 18*mm, w - 25*mm, h - 18*mm)

    canvas_obj.setFont("Helvetica-Bold", 8)
    canvas_obj.setFillColor(NAVY)
    canvas_obj.drawString(25*mm, h - 16*mm, "UNILABS MARKET INTELLIGENCE")
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(GRAY)
    canvas_obj.drawRightString(w - 25*mm, h - 16*mm, "Strictly Confidential")

    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(GRAY)
    canvas_obj.drawString(25*mm, 14*mm, f"Generated {datetime.now().strftime('%d %B %Y %H:%M')} | Strictly Confidential")
    canvas_obj.drawRightString(w - 25*mm, 14*mm, f"Page {doc.page}")

    canvas_obj.setStrokeColor(HexColor("#E5E7EB"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(25*mm, 18*mm, w - 25*mm, 18*mm)

    canvas_obj.restoreState()


def build_pdf_report(sections, config):
    buf = io.BytesIO()
    styles = _make_styles()
    cleaned_sections, source_entries = _prepare_report_sections(sections)

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm,
        topMargin=24*mm, bottomMargin=24*mm,
    )

    story = []
    years = config.get("years", [])
    periods = config.get("periods", [])
    countries = config.get("countries", [])
    comps = config.get("competitors", []) + [c for c in config.get("custom_competitors", []) if c]
    time_label = f"{', '.join(str(y) for y in years)} -- {', '.join(periods)}"
    geo = "All Markets" if len(countries) >= len(COUNTRIES) else ", ".join(countries)
    comp_label = ", ".join(comps[:5]) + (f" +{len(comps)-5} more" if len(comps) > 5 else "")
    date_str = datetime.now().strftime("%d %B %Y")

    # -- Cover / Title --
    story.append(Spacer(1, 30*mm))

    logo_data = [
        [Paragraph('<font color="#003366" size="28"><b>MI</b></font>', styles["title"]),
         Paragraph('<font color="#003366" size="26"><b>unilabs</b></font>', styles["title"])],
    ]
    logo_table = Table(logo_data, colWidths=[18*mm, 60*mm])
    logo_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(logo_table)
    story.append(Spacer(1, 8*mm))

    story.append(Paragraph("MARKET INTELLIGENCE REPORT", styles["title"]))
    story.append(Paragraph("Competitor Updates -- European Diagnostics", styles["subtitle"]))
    story.append(Spacer(1, 4*mm))

    meta_text = f"{time_label}  |  {geo}  |  {date_str}"
    story.append(Paragraph(meta_text, styles["meta"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"Benchmarked vs: {_esc(comp_label)}", styles["meta"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("Dual-Agent AI + Web Search Cross-Validation", styles["meta"]))

    story.append(Spacer(1, 12*mm))
    story.append(HRFlowable(width="80%", thickness=1, color=RED, spaceAfter=8*mm))

    # -- Table of Contents --
    story.append(Paragraph("CONTENTS", ParagraphStyle(
        "TOCHead", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY,
        spaceBefore=4, spaceAfter=12,
    )))

    for i, s in enumerate(cleaned_sections, 1):
        story.append(Paragraph(
            f'<font color="#EF4444"><b>{i}.</b></font>  {_esc(s["title"])}',
            styles["toc_item"],
        ))
    story.append(PageBreak())

    # -- Sections --
    for i, section in enumerate(cleaned_sections):
        color = section.get("color", "#003366")
        content = _strip_html(section.get("content", ""))

        header_data = [[
            Paragraph(
                f'<font color="{color}"><b>{i+1}.</b></font> '
                f'<font color="#003366"><b>{_esc(section["title"])}</b></font>',
                styles["section_title"],
            )
        ]]
        header_table = Table(header_data, colWidths=[doc.width])
        header_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 2, HexColor(color)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ]))
        story.append(header_table)

        if content:
            paragraphs = content.split('\n')
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                if para.startswith('- ') or para.startswith('* '):
                    story.append(Paragraph(
                        f'<bullet>&bull;</bullet> {para[2:]}',
                        styles["bullet"],
                    ))
                else:
                    story.append(Paragraph(para, styles["body"]))
        else:
            story.append(Paragraph(
                "<i>No content generated for this section.</i>",
                styles["body"],
            ))

        story.append(Spacer(1, 6*mm))
        if i < len(cleaned_sections) - 1 and (i + 1) % 3 == 0:
            story.append(PageBreak())

    if source_entries:
        story.append(PageBreak())
        story.append(Paragraph("SOURCE APPENDIX", styles["section_title"]))
        for i, source in enumerate(source_entries, 1):
            story.append(Paragraph(
                f'<font color="#EF4444"><b>{i}.</b></font> {_esc(_source_item_to_text(source))}',
                styles["body"],
            ))

    # -- Footer summary --
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#E5E7EB"), spaceAfter=4*mm))

    summary_data = [[
        Paragraph(f'<font color="#6B7280">{len(sections)} sections | Dual-agent validated | {date_str}</font>', styles["footer"]),
        Paragraph('<font color="#991B1B"><b>STRICTLY CONFIDENTIAL</b></font>', styles["footer"]),
    ]]
    summary_table = Table(summary_data, colWidths=[doc.width * 0.7, doc.width * 0.3])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
