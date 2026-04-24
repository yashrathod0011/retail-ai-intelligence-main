# src/utils/pdf_generator.py
"""
Professional PDF report generator for Retail AI Intelligence.
Handles both quick_analysis and deep_analysis report formats.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime
import io
import re


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
C_PRIMARY   = colors.HexColor("#09090b")   # near-black
C_ACCENT    = colors.HexColor("#2563eb")   # blue
C_SURFACE   = colors.HexColor("#f4f4f5")   # light grey card
C_BORDER    = colors.HexColor("#d4d4d8")
C_TEXT_2    = colors.HexColor("#52525b")
C_WHITE     = colors.white
C_GREEN     = colors.HexColor("#16a34a")
C_AMBER     = colors.HexColor("#d97706")


def _strip_emoji(text: str) -> str:
    """Remove emoji / non-latin characters that confuse ReportLab."""
    if not isinstance(text, str):
        return str(text)
    # Remove emoji ranges
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"
        u"\u3030"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def _safe(text, fallback="N/A") -> str:
    if text is None or text == "":
        return fallback
    # Replace rupees symbol with INR as standard fonts may not support it
    text = str(text).replace('₹', 'INR ').replace('Rs.', 'INR ')
    return _strip_emoji(text)


class ReportPDFGenerator:
    """Generate professional PDF reports from analysis data."""

    # ------------------------------------------------------------------
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._build_styles()

    # ------------------------------------------------------------------
    def _build_styles(self):
        S = self.styles

        self.st_title = ParagraphStyle(
            "RTitle",
            parent=S["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=C_PRIMARY,
            leading=28,
            spaceAfter=4,
        )
        self.st_subtitle = ParagraphStyle(
            "RSubtitle",
            parent=S["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=C_TEXT_2,
            leading=14,
            spaceAfter=0,
        )
        self.st_section = ParagraphStyle(
            "RSection",
            parent=S["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=C_PRIMARY,
            leading=16,
            spaceBefore=14,
            spaceAfter=6,
        )
        self.st_body = ParagraphStyle(
            "RBody",
            parent=S["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=C_TEXT_2,
            leading=14,
            spaceAfter=4,
        )
        self.st_body_bold = ParagraphStyle(
            "RBodyBold",
            parent=self.st_body,
            fontName="Helvetica-Bold",
            textColor=C_PRIMARY,
        )
        self.st_bullet = ParagraphStyle(
            "RBullet",
            parent=self.st_body,
            leftIndent=14,
            bulletIndent=4,
            spaceAfter=3,
        )
        self.st_meta = ParagraphStyle(
            "RMeta",
            parent=S["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=C_TEXT_2,
            alignment=TA_RIGHT,
        )
        self.st_footer = ParagraphStyle(
            "RFooter",
            parent=S["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=C_TEXT_2,
            alignment=TA_CENTER,
        )

    # ------------------------------------------------------------------
    def _hr(self, color=C_BORDER, thickness=0.5):
        return HRFlowable(
            width="100%",
            thickness=thickness,
            color=color,
            spaceAfter=6,
            spaceBefore=6,
        )

    # ------------------------------------------------------------------
    def _kpi_table(self, rows: list[tuple]):
        """Build a simple 2-column key-value table for metrics."""
        table_data = []
        for label, value in rows:
            table_data.append([
                Paragraph(f"<b>{_safe(label)}</b>", self.st_body_bold),
                Paragraph(_safe(value), self.st_body),
            ])
        t = Table(table_data, colWidths=[2.4 * inch, 4.2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), C_SURFACE),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_WHITE, C_SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.4, C_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    # ------------------------------------------------------------------
    def _header_table(self, title: str, platform: str, report_type: str, products_analyzed: int = None):
        """Build the page header block."""
        now = datetime.now().strftime("%d %b %Y, %H:%M")
        right_info = f"Platform: {platform}\nGenerated: {now}"
        if products_analyzed:
            right_info += f"\nProducts analysed: {products_analyzed}"

        data = [[
            Paragraph(title, self.st_title),
            Paragraph(right_info.replace("\n", "<br/>"), self.st_meta),
        ]]
        t = Table(data, colWidths=[4.5 * inch, 2.2 * inch])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ]))
        return t

    # ------------------------------------------------------------------
    def generate_analysis_report(
        self,
        analysis: dict,
        platform: str = "All Platforms",
        products_analyzed: int = None,
    ) -> bytes:
        """
        Generate a PDF from analysis data.
        Handles both quick_analysis and deep_analysis structures.
        """
        # Determine which type of report this is
        is_deep = bool(analysis.get("final_report") or analysis.get("detailed_results"))
        report_label = "Deep Analysis" if is_deep else "Quick Analysis"

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
            title=f"Retail AI - {report_label} Report",
            author="Retail AI Intelligence"
        )

        story = []

        # ── Header ──────────────────────────────────────────────────────
        report_label_full = f"{report_label} Report"
        story.append(self._header_table(
            "Retail AI Intelligence",
            platform,
            report_label_full,
            products_analyzed,
        ))
        story.append(Paragraph(report_label_full, self.st_subtitle))
        story.append(Spacer(1, 4))
        story.append(self._hr(C_ACCENT, thickness=1.5))
        story.append(Spacer(1, 6))

        if is_deep:
            story += self._build_deep_sections(analysis)
        else:
            story += self._build_quick_sections(analysis)

        # ── Footer ───────────────────────────────────────────────────────
        story.append(Spacer(1, 16))
        story.append(self._hr())
        story.append(Paragraph(
            "Generated by Retail AI Intelligence  |  Powered by Gemini AI  |  Confidential",
            self.st_footer,
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # ------------------------------------------------------------------
    # Quick analysis renderer
    # ------------------------------------------------------------------
    def _build_quick_sections(self, analysis: dict) -> list:
        story = []

        # Key metrics table
        pr = analysis.get("price_range", {}) or {}
        metrics = [
            ("Total Products",  analysis.get("total_products", "N/A")),
            ("Min Price",       f"Rs {pr.get('min', 0):,.0f}"  if pr.get("min")  is not None else "N/A"),
            ("Max Price",       f"Rs {pr.get('max', 0):,.0f}"  if pr.get("max")  is not None else "N/A"),
            ("Average Price",   f"Rs {pr.get('average', 0):,.0f}" if pr.get("average") is not None else "N/A"),
        ]

        story.append(Paragraph("Key Metrics", self.st_section))
        story.append(self._kpi_table(metrics))
        story.append(Spacer(1, 8))

        # Top rated
        top = analysis.get("top_rated_product") or {}
        if top:
            story.append(KeepTogether([
                Paragraph("Top Rated Product", self.st_section),
                self._kpi_table([
                    ("Title",  top.get("title")),
                    ("Rating", top.get("rating")),
                    ("Price",  f"Rs {top.get('price', 0):,.0f}" if top.get("price") else "N/A"),
                ]),
            ]))
            story.append(Spacer(1, 8))

        # Best value
        best = analysis.get("best_value_product") or {}
        if best:
            story.append(KeepTogether([
                Paragraph("Best Value Product", self.st_section),
                self._kpi_table([
                    ("Title",  best.get("title")),
                    ("Reason", best.get("reason")),
                ]),
            ]))
            story.append(Spacer(1, 8))

        # Price insights
        insights = analysis.get("price_insights") or []
        if insights:
            story.append(Paragraph("Price Insights", self.st_section))
            for item in insights:
                story.append(Paragraph(f"- {_safe(item)}", self.st_bullet))
            story.append(Spacer(1, 8))

        # Recommendations
        recs = analysis.get("recommendations") or []
        if recs:
            story.append(Paragraph("Strategic Recommendations", self.st_section))
            for i, rec in enumerate(recs, 1):
                story.append(Paragraph(f"{i}.  {_safe(rec)}", self.st_bullet))
            story.append(Spacer(1, 8))

        # Catch-all for any other top-level text keys
        skip = {"total_products", "price_range", "top_rated_product",
                "best_value_product", "price_insights", "recommendations"}
        for key, val in analysis.items():
            if key in skip:
                continue
            if isinstance(val, str) and val.strip():
                story.append(Paragraph(key.replace("_", " ").title(), self.st_section))
                story.append(Paragraph(_safe(val), self.st_body))
            elif isinstance(val, list) and val:
                story.append(Paragraph(key.replace("_", " ").title(), self.st_section))
                for item in val:
                    story.append(Paragraph(f"- {_safe(item)}", self.st_bullet))

        return story

    # ------------------------------------------------------------------
    def _parse_md_line(self, line: str, story: list):
        """Parse a markdown line and append appropriate flowable to the story."""
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            return

        # Replace rupees
        line = line.replace('₹', 'INR ').replace('Rs.', 'INR ')

        # Process inline markdown
        # bold
        line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
        line = re.sub(r'__(.+?)__', r'<b>\1</b>', line)
        # italic
        line = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', line)
        line = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<i>\1</i>', line)
        # code inline
        line = re.sub(r'`([^`]+)`', r'<font face="Courier">\1</font>', line)

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            if level <= 2:
                story.append(Paragraph(text, self.st_title))
            else:
                story.append(Paragraph(text, self.st_section))
            return

        # Lists
        if line.startswith(("- ", "* ", "• ")):
            story.append(Paragraph(f"- {line[2:].strip()}", self.st_bullet))
        elif re.match(r"^\d+[\.\)]\s", line):
            story.append(Paragraph(line, self.st_bullet))
        elif line.endswith(":") or (len(line) < 80 and line.isupper() and not '<' in line):
            story.append(Paragraph(f"<b>{line}</b>", self.st_body_bold))
        else:
            story.append(Paragraph(line, self.st_body))

    # ------------------------------------------------------------------
    # Deep analysis renderer
    # ------------------------------------------------------------------
    def _build_deep_sections(self, analysis: dict) -> list:
        story = []

        # Detailed results from each agent
        detailed = analysis.get("detailed_results") or []
        if detailed:
            for result in detailed:
                agent_name = _safe(result.get("agent", "Agent"))
                output = _safe(result.get("output", ""))
                if not output:
                    continue

                story.append(Paragraph(agent_name, self.st_section))
                story.append(self._hr())

                # Split output into paragraphs preserving line structure
                for line in output.split("\n"):
                    self._parse_md_line(line, story)

                story.append(Spacer(1, 10))

        # Final report (executive summary by the writer agent)
        final = _safe(analysis.get("final_report", ""))
        if final and final != "N/A":
            story.append(Paragraph("Executive Summary", self.st_section))
            story.append(self._hr(C_ACCENT))
            for line in final.split("\n"):
                self._parse_md_line(line, story)

        # Metadata footer block
        meta = []
        if analysis.get("tasks_completed"):
            meta.append(("Tasks Completed", analysis["tasks_completed"]))
        if analysis.get("model_used"):
            meta.append(("Model Used", analysis["model_used"]))
        if meta:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Analysis Metadata", self.st_section))
            story.append(self._kpi_table(meta))

        return story
