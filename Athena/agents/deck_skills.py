"""
Latitude MedTech — Deck Skills (Phase 2A)
==========================================
python-pptx slide-type renderers for DeckAgent.
Each public method appends one slide to self.prs and returns it.

Canvas: 13.333 × 7.5 inches (16:9), all measurements in EMU.
Brand: Calibri font, Latitude palette from settings.json.
"""
from __future__ import annotations
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Brand palette (settings.json documents.colors) ───────────────────────────
_BLACK = RGBColor(0x1A, 0x1A, 0x1A)   # primary text / dark backgrounds
_SLATE = RGBColor(0x2C, 0x3E, 0x50)   # secondary text
_BLUE  = RGBColor(0x5B, 0x7F, 0xA6)   # accent / headers
_TEAL  = RGBColor(0x4A, 0x7C, 0x6F)   # section dividers
_WARM  = RGBColor(0xC8, 0x95, 0x6C)   # recommendation box / call-outs
_MUTED = RGBColor(0x8A, 0x86, 0x80)   # footnotes / captions
_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_LIGHT = RGBColor(0xF4, 0xF5, 0xF7)   # alternating table rows / light bg
_RULE  = RGBColor(0xE3, 0xE6, 0xEA)   # divider lines

FONT = "Calibri"

# Canvas constants
W    = Inches(13.333)
H    = Inches(7.5)
LM   = Inches(0.5)             # left margin
RM   = Inches(0.5)             # right margin
CW   = W - LM - RM            # usable content width ≈ 12.333"
FOOT_Y = Inches(7.05)


class DeckSkills:
    """Append brand-styled slides to a python-pptx Presentation."""

    def __init__(self, prs: Presentation):
        self.prs = prs
        self._blank = self._find_blank_layout()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _find_blank_layout(self):
        for layout in self.prs.slide_layouts:
            if "blank" in layout.name.lower():
                return layout
        return self.prs.slide_layouts[-1]

    def _slide(self):
        return self.prs.slides.add_slide(self._blank)

    def _rect(self, slide, left, top, width, height, color: RGBColor):
        shape = slide.shapes.add_shape(1, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    def _tx(self, slide, text: str, left, top, width, height, *,
            bold=False, italic=False, size=16, color=_BLACK,
            align=PP_ALIGN.LEFT, wrap=True):
        box = slide.shapes.add_textbox(left, top, width, height)
        tf = box.text_frame
        tf.word_wrap = wrap
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.bold   = bold
        run.font.italic = italic
        run.font.size   = Pt(size)
        run.font.color.rgb = color
        run.font.name   = FONT
        return box

    def _bullets(self, slide, items: list[str], left, top, width, height, *,
                 size=14, color=_SLATE, space=Pt(4)):
        box = slide.shapes.add_textbox(left, top, width, height)
        tf  = box.text_frame
        tf.word_wrap = True
        for i, text in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_before = space
            run = p.add_run()
            run.text = f"• {text}"
            run.font.size  = Pt(size)
            run.font.color.rgb = color
            run.font.name  = FONT
        return box

    def _header(self, slide, title: str, subtitle: str = ""):
        """Thin blue accent bar + title on white content slides."""
        self._rect(slide, 0, 0, W, Emu(54000), _BLUE)
        self._tx(slide, title,
                 LM, Inches(0.08), CW, Inches(0.82),
                 bold=True, size=26, color=_BLACK)
        if subtitle:
            self._tx(slide, subtitle,
                     LM, Inches(0.86), CW, Inches(0.38),
                     size=13, color=_MUTED)

    def _footer(self, slide, label: str = "Alpha — Steve Review Required"):
        self._rect(slide, 0, FOOT_Y, W, Emu(18000), _RULE)
        self._tx(slide, "Latitude MedTech LLC  ·  CONFIDENTIAL",
                 LM, FOOT_Y + Emu(24000), Inches(5.5), Inches(0.35),
                 size=8, color=_MUTED)
        self._tx(slide, label,
                 W - Inches(4.8), FOOT_Y + Emu(24000), Inches(4.3), Inches(0.35),
                 size=8, color=_MUTED, align=PP_ALIGN.RIGHT)

    # ── Slide types ───────────────────────────────────────────────────────────

    def add_cover(self, title: str, subtitle: str = "",
                  date: str = "", client_name: str = "") -> object:
        """Dark full-bleed cover slide."""
        slide = self._slide()
        self._rect(slide, 0, 0, W, H, _BLACK)                       # full bg
        self._rect(slide, 0, 0, Emu(36000), H, _BLUE)               # left accent strip

        # Company name — top right
        self._tx(slide, "LATITUDE MEDTECH LLC",
                 W - Inches(3.9), Inches(0.28), Inches(3.4), Inches(0.4),
                 size=10, color=_BLUE, align=PP_ALIGN.RIGHT)

        # Title
        self._tx(slide, title,
                 Inches(0.7), Inches(2.0), Inches(10.0), Inches(2.2),
                 bold=True, size=38, color=_WHITE)

        # Subtitle
        if subtitle:
            self._tx(slide, subtitle,
                     Inches(0.7), Inches(4.25), Inches(10.0), Inches(0.7),
                     size=22, color=_MUTED)

        # Blue rule below title block
        self._rect(slide, Inches(0.7), Inches(5.1), Inches(6), Emu(16000), _BLUE)

        # Meta line
        meta = "  ·  ".join(p for p in [date, client_name] if p)
        if meta:
            self._tx(slide, meta, Inches(0.7), Inches(5.4), Inches(10), Inches(0.4),
                     size=12, color=_MUTED)

        # Tagline + confidential
        self._tx(slide, "Navigating compliance. Accelerating innovation.",
                 Inches(0.7), Inches(6.7), Inches(9), Inches(0.4),
                 size=11, italic=True, color=_MUTED)
        self._tx(slide, "CONFIDENTIAL",
                 W - Inches(2.6), Inches(6.9), Inches(2.1), Inches(0.4),
                 size=9, color=_MUTED, align=PP_ALIGN.RIGHT)
        return slide

    def add_exec_summary(self, situation: str, complication: str,
                         recommendation: str, findings: list[str]) -> object:
        """Executive summary — SCR left column, key findings right column."""
        slide = self._slide()
        self._header(slide, "Executive Summary")
        self._footer(slide)

        col_w  = Inches(5.9)
        sep_x  = LM + col_w + Inches(0.35)
        right_x = sep_x + Inches(0.2)
        right_w = W - right_x - RM
        top    = Inches(1.05)

        # SCR column
        scr = [("SITUATION",      situation,      _BLUE),
               ("COMPLICATION",   complication,   _WARM),
               ("RECOMMENDATION", recommendation, _TEAL)]
        y = top
        for label, body, accent in scr:
            self._rect(slide, LM, y, Emu(18000), Inches(0.62), accent)
            self._tx(slide, label, LM + Inches(0.22), y, col_w - Inches(0.3), Inches(0.3),
                     bold=True, size=9, color=accent)
            self._tx(slide, body, LM + Inches(0.22), y + Inches(0.28),
                     col_w - Inches(0.3), Inches(0.9),
                     size=14, color=_SLATE, wrap=True)
            y += Inches(1.15)

        # Vertical divider
        self._rect(slide, sep_x, top, Emu(9000), Inches(3.5), _RULE)

        # Findings column
        self._tx(slide, "KEY FINDINGS", right_x, top, right_w, Inches(0.35),
                 bold=True, size=10, color=_BLACK)
        y_r = top + Inches(0.45)
        for i, f in enumerate(findings[:5]):
            self._rect(slide, right_x, y_r + Emu(60000), Emu(18000), Inches(0.42), _BLUE)
            self._tx(slide, f"{i + 1:02d}  {f}",
                     right_x + Inches(0.22), y_r, right_w - Inches(0.3),
                     Inches(0.72), size=13, color=_SLATE, wrap=True)
            y_r += Inches(0.82)
        return slide

    def add_section_divider(self, section_title: str, subtitle: str = "") -> object:
        """Full-bleed dark section break."""
        slide = self._slide()
        self._rect(slide, 0, 0, W, H, _BLACK)
        self._rect(slide, 0, 0, Emu(36000), H, _TEAL)          # teal left strip

        self._tx(slide, "SECTION",
                 Inches(0.7), Inches(0.38), Inches(4), Inches(0.35),
                 size=9, color=_MUTED)
        self._tx(slide, section_title,
                 Inches(0.7), Inches(2.5), Inches(11.5), Inches(1.4),
                 bold=True, size=42, color=_WHITE)
        if subtitle:
            self._tx(slide, subtitle,
                     Inches(0.7), Inches(4.0), Inches(11), Inches(0.6),
                     size=20, color=_MUTED)
        self._rect(slide, Inches(0.7), Inches(4.85), Inches(3), Emu(16000), _TEAL)
        return slide

    def add_content_bullets(self, headline: str, bullets: list[str],
                            note: str = "") -> object:
        """Standard consulting body slide — headline + up to 5 bullets."""
        slide = self._slide()
        self._header(slide, headline)
        self._footer(slide)

        y = Inches(1.1)
        for bullet in bullets[:5]:
            self._rect(slide, LM, y + Emu(90000), Emu(14000), Inches(0.5), _BLUE)
            self._tx(slide, bullet,
                     LM + Inches(0.22), y, CW - Inches(0.3), Inches(0.78),
                     size=16, color=_SLATE, wrap=True)
            y += Inches(1.0)

        if note:
            self._tx(slide, f"Note: {note}",
                     LM, Inches(6.6), CW, Inches(0.32),
                     size=9, italic=True, color=_MUTED)
        return slide

    def add_two_column(self, headline: str,
                       left_title: str, left_bullets: list[str],
                       right_title: str, right_bullets: list[str]) -> object:
        """Side-by-side comparison slide."""
        slide = self._slide()
        self._header(slide, headline)
        self._footer(slide)

        half_w  = (CW - Inches(0.25)) / 2
        right_x = LM + half_w + Inches(0.25)
        top     = Inches(1.1)

        self._rect(slide, LM,      top, half_w, Inches(0.45), _BLUE)
        self._rect(slide, right_x, top, half_w, Inches(0.45), _SLATE)
        self._tx(slide, left_title,  LM + Inches(0.15), top + Emu(32000),
                 half_w - Inches(0.3), Inches(0.35), bold=True, size=13, color=_WHITE)
        self._tx(slide, right_title, right_x + Inches(0.15), top + Emu(32000),
                 half_w - Inches(0.3), Inches(0.35), bold=True, size=13, color=_WHITE)

        bul_y = top + Inches(0.58)
        self._bullets(slide, left_bullets[:5],  LM,      bul_y, half_w,  Inches(4.9))
        self._bullets(slide, right_bullets[:5], right_x, bul_y, half_w,  Inches(4.9))
        return slide

    def add_data_chart(self, insight_headline: str, chart_path: str,
                       data_source: str = "") -> object:
        """'So what' headline + embedded chart PNG."""
        slide = self._slide()
        self._header(slide, insight_headline)
        self._footer(slide)

        p = Path(chart_path)
        if p.exists():
            img_w = Inches(10.8)
            img_h = Inches(5.25)
            slide.shapes.add_picture(str(p), (W - img_w) / 2, Inches(1.08), img_w, img_h)
        else:
            self._tx(slide, "[ Chart visualization pending — data required ]",
                     LM, Inches(3.6), CW, Inches(0.6),
                     size=13, italic=True, color=_MUTED, align=PP_ALIGN.CENTER)

        if data_source:
            self._tx(slide, f"Source: {data_source}",
                     LM, Inches(6.55), CW, Inches(0.32),
                     size=8, italic=True, color=_MUTED)
        return slide

    def add_comparison_table(self, headline: str,
                             col_headers: list[str],
                             rows: list[list[str]]) -> object:
        """Feature/criteria comparison table."""
        slide = self._slide()
        self._header(slide, headline)
        self._footer(slide)

        n_rows = len(rows) + 1
        n_cols = len(col_headers) + 1
        tbl_h  = min(Inches(5.5), Pt(34) * n_rows)
        shape  = slide.shapes.add_table(n_rows, n_cols, LM, Inches(1.12), CW, int(tbl_h))
        tbl    = shape.table

        label_w = Inches(2.6)
        data_w  = int((CW - label_w) / max(len(col_headers), 1))
        tbl.columns[0].width = int(label_w)
        for i in range(1, n_cols):
            tbl.columns[i].width = data_w

        _cell(tbl.cell(0, 0), "", _BLACK, _WHITE, bold=True, size=11)
        for j, h in enumerate(col_headers):
            _cell(tbl.cell(0, j + 1), h, _BLUE, _WHITE, bold=True, size=11)

        for i, row in enumerate(rows):
            bg = _LIGHT if i % 2 == 0 else _WHITE
            _cell(tbl.cell(i + 1, 0), row[0] if row else "", bg, _BLACK, bold=True, size=11)
            for j, val in enumerate(row[1:], 1):
                _cell(tbl.cell(i + 1, j), str(val), bg, _SLATE, size=11)
        return slide

    def add_roadmap(self, headline: str, steps: list[dict],
                    chart_path: str = "") -> object:
        """Milestone roadmap — embeds process_steps PNG if available."""
        slide = self._slide()
        self._header(slide, headline)
        self._footer(slide)

        if chart_path and Path(chart_path).exists():
            img_w = Inches(12.0)
            img_h = Inches(4.8)
            slide.shapes.add_picture(chart_path, (W - img_w) / 2, Inches(1.2), img_w, img_h)
        else:
            # Text fallback — evenly spaced phase boxes
            n = min(len(steps), 6)
            if n:
                box_w = CW / n
                for i, s in enumerate(steps[:n]):
                    x = LM + box_w * i
                    self._rect(slide, x + Inches(0.05), Inches(1.8), box_w - Inches(0.1), Inches(0.45), _BLUE)
                    self._tx(slide, s.get("title", f"Phase {i+1}"),
                             x + Inches(0.1), Inches(1.82), box_w - Inches(0.2), Inches(0.4),
                             bold=True, size=13, color=_WHITE, align=PP_ALIGN.CENTER)
                    if s.get("detail"):
                        self._tx(slide, s["detail"],
                                 x + Inches(0.1), Inches(2.4), box_w - Inches(0.2), Inches(1.2),
                                 size=11, color=_SLATE, wrap=True)
        return slide

    def add_recommendation(self, recommendation: str,
                           rationale: list[str]) -> object:
        """Framed recommendation box + numbered rationale."""
        slide = self._slide()
        self._header(slide, "Recommendation")
        self._footer(slide)

        # Warm-coloured recommendation box
        self._rect(slide, LM, Inches(1.12), CW, Inches(1.9), _WARM)
        self._tx(slide, "WE RECOMMEND:",
                 LM + Inches(0.22), Inches(1.18), CW - Inches(0.44), Inches(0.3),
                 bold=True, size=9, color=_WHITE)
        self._tx(slide, recommendation,
                 LM + Inches(0.22), Inches(1.5), CW - Inches(0.44), Inches(1.3),
                 bold=True, size=18, color=_WHITE, wrap=True)

        # Rationale section
        self._tx(slide, "RATIONALE",
                 LM, Inches(3.2), CW, Inches(0.35),
                 bold=True, size=10, color=_BLACK)
        y = Inches(3.6)
        for r in rationale[:4]:
            self._rect(slide, LM, y + Emu(90000), Emu(14000), Inches(0.4), _BLUE)
            self._tx(slide, r, LM + Inches(0.22), y, CW - Inches(0.3), Inches(0.68),
                     size=14, color=_SLATE, wrap=True)
            y += Inches(0.82)
        return slide

    def add_next_steps(self, steps: list[dict]) -> object:
        """Numbered action items with optional owner and timeline."""
        slide = self._slide()
        self._header(slide, "Next Steps")
        self._footer(slide)

        y = Inches(1.12)
        for i, s in enumerate(steps[:5]):
            action   = s.get("action", "")
            owner    = s.get("owner", "")
            timeline = s.get("timeline", "")

            self._rect(slide, LM, y + Emu(36000), Inches(0.46), Inches(0.46), _BLUE)
            self._tx(slide, f"{i + 1:02d}",
                     LM + Emu(40000), y + Emu(30000), Inches(0.46), Inches(0.46),
                     bold=True, size=13, color=_WHITE, align=PP_ALIGN.CENTER)

            self._tx(slide, action,
                     LM + Inches(0.6), y, CW - Inches(3.8), Inches(0.58),
                     bold=True, size=15, color=_BLACK, wrap=True)

            meta = "  ·  ".join(x for x in [f"Owner: {owner}" if owner else "", timeline] if x)
            if meta:
                self._tx(slide, meta,
                         LM + Inches(0.6), y + Inches(0.58),
                         CW - Inches(3.8), Inches(0.3),
                         size=11, color=_MUTED)
            y += Inches(1.1)
        return slide

    def add_appendix_cover(self) -> object:
        return self.add_section_divider("Appendix", "Supporting detail and data")


# ── Table cell helper ─────────────────────────────────────────────────────────

def _cell(cell, text: str, bg: RGBColor, fg: RGBColor, *,
          bold: bool = False, size: int = 11):
    cell.fill.solid()
    cell.fill.fore_color.rgb = bg
    tf = cell.text_frame
    tf.word_wrap = True
    para = tf.paragraphs[0]
    para.space_before = Pt(3)
    para.space_after  = Pt(3)
    if para.runs:
        run = para.runs[0]
    else:
        run = para.add_run()
    run.text = text
    run.font.bold      = bold
    run.font.size      = Pt(size)
    run.font.color.rgb = fg
    run.font.name      = FONT
