"""
Latitude MedTech — Deck Agent (Phase 2A)
=========================================
Builds client-facing management consulting slide decks (PPTX) on demand.

Workflow:
  1. Claude Sonnet plans the deck structure as a JSON slide manifest
  2. For slides requiring charts, figures.py generates branded PNGs
  3. DeckSkills renders each slide into a python-pptx Presentation
  4. Saved to documents/decks/YYYYMMDD_HHMMSS_<slug>.pptx

Usage (CLI):
    python deck_agent.py --topic "Q3 Regulatory Strategy" --type strategy
    python deck_agent.py --topic "Pitch: Latitude Coaching" --type pitch --client "Biocom Summit"

Usage (module):
    from deck_agent import DeckAgent
    result = DeckAgent().generate("Regulatory Pathway Analysis", deck_type="regulatory")
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from pathconfig import ENV_FILE, ATHENA_ROOT, LOGS_DIR
load_dotenv(ENV_FILE)

DECKS_DIR   = ATHENA_ROOT / "documents" / "decks"
FIGURES_DIR = ATHENA_ROOT / "documents" / "figures"
BACKEND_DIR = ATHENA_ROOT / "ui" / "backend"

DECKS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# figures.py lives in ui/backend
sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "deck_agent.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("deck_agent")

# ── Deck type → slide count guidance ─────────────────────────────────────────
_DECK_GUIDES = {
    "strategy": (
        "Full strategy deck using SCQA structure. Slides: cover, exec_summary, "
        "section_divider (Context), 2 content_bullets or two_column, 1 data_chart, "
        "section_divider (Findings), comparison_table or data_chart, "
        "section_divider (Recommendations), recommendation, roadmap, next_steps. "
        "Total: 10-12 slides."
    ),
    "pitch": (
        "Investor/client pitch deck following McKinsey bottom-line-up-front structure. "
        "Slides: cover, exec_summary (BLUF: what you're asking for and why — one crisp recommendation), "
        "content_bullets (Problem), content_bullets (Solution), data_chart (Market Size), "
        "two_column (Product/Service), content_bullets (Business Model), "
        "data_chart (Traction/Proof), comparison_table (Team or Competitive), "
        "next_steps (The Ask). Total: 10-11 slides."
    ),
    "regulatory": (
        "Regulatory pathway analysis. Slides: cover, exec_summary, "
        "content_bullets (Device Overview & Classification), two_column (US vs EU Pathway), "
        "comparison_table (Predicate/Evidence Analysis), roadmap (Regulatory Timeline), "
        "content_bullets (Resource Requirements), recommendation, next_steps. "
        "Total: 8-9 slides."
    ),
    "coaching": (
        "Career coaching engagement plan. Slides: cover, exec_summary, "
        "content_bullets (Current State Assessment), two_column (Gap Analysis), "
        "roadmap (90-Day Coaching Plan), content_bullets (Program Deliverables), "
        "comparison_table (Program Options), next_steps. Total: 7-8 slides."
    ),
    "ma": (
        "M&A diligence summary. Slides: cover, exec_summary, "
        "content_bullets (Transaction Overview), two_column (Target Profile), "
        "comparison_table (Quality & Regulatory Assessment), data_chart (Financial Snapshot), "
        "content_bullets (Risk Matrix), recommendation, next_steps. Total: 8-9 slides."
    ),
    "briefing": (
        "Daily/weekly intelligence briefing. Slides: cover, exec_summary, "
        "content_bullets (Breaking / Need to Know), content_bullets (Industry Pulse), "
        "data_chart (Market Snapshot if data available), next_steps (Action Items). "
        "Total: 5-6 slides."
    ),
}

_SLIDE_SCHEMA = """
Each slide is a JSON object with a "type" field plus type-specific fields:

cover:
  {type, title, subtitle, date}

exec_summary:
  {type, situation, complication, recommendation, findings: [str×3-5]}

section_divider:
  {type, section_title, subtitle?}

content_bullets:
  {type, headline, bullets: [str×3-5], note?}

two_column:
  {type, headline, left_title, left_bullets: [str×3-4], right_title, right_bullets: [str×3-4]}

data_chart:
  {type, insight_headline,
   chart_type: "bar"|"grouped_bar"|"trend_line",
   chart_data: {
     bar:          {labels:[str], values:[num], ylabel?, highlight_index?},
     grouped_bar:  {categories:[str], series:{name:[num]}, ylabel?},
     trend_line:   {x:[str], series:{name:[num]}, ylabel?}
   },
   data_source?}

comparison_table:
  {type, headline, col_headers: [str×2-5], rows: [[label, val, val, ...]×2-6]}

roadmap:
  {type, headline, steps: [{title, detail?}×3-6]}

recommendation:
  {type, recommendation, rationale: [str×3-4]}

next_steps:
  {type, steps: [{action, owner?, timeline?}×3-5]}

appendix_cover:
  {type}
"""


class DeckAgent:
    def __init__(self):
        from agent_base import AgentBase
        self._base = AgentBase("deck")
        self._client = None

    def _claude(self):
        if not self._client:
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        return self._client

    # ── Client brief lookup ───────────────────────────────────────────────────

    def _find_client_brief(self, client_name: str) -> str:
        """Fuzzy-match client_name against coaching/briefs/ filenames.
        Returns the brief content (stripped of frontmatter) or empty string."""
        from pathconfig import BRIEFS_DIR
        if not client_name or not BRIEFS_DIR.exists():
            return ""

        # Normalise: "Maya Patel" → "maya_patel"
        slug = re.sub(r"[^a-z0-9]+", "_", client_name.lower()).strip("_")
        # Individual tokens for partial matching: ["maya", "patel"]
        tokens = [t for t in slug.split("_") if len(t) > 1]

        candidates = []
        for f in BRIEFS_DIR.glob("*.md"):
            # Filename: "2026-06-05_maya_patel.md" → name_slug = "maya_patel"
            name_slug = f.stem.split("_", 1)[1] if "_" in f.stem else f.stem
            if slug == name_slug:                              # exact
                candidates.append((2, f.stat().st_mtime, f))
            elif tokens and all(t in name_slug for t in tokens):  # partial
                candidates.append((1, f.stat().st_mtime, f))

        if not candidates:
            return ""

        best = sorted(candidates, key=lambda x: (x[0], x[1]), reverse=True)[0][2]
        try:
            raw = best.read_text(encoding="utf-8")
            # Strip YAML frontmatter
            if raw.startswith("---"):
                end = raw.find("\n---", 3)
                raw = raw[end + 4:].strip() if end != -1 else raw
            log.info(f"Client brief matched: {best.name}")
            return raw[:4000]   # cap at 4k chars — enough context, won't blow the prompt
        except Exception as e:
            log.warning(f"Brief read error: {e}")
            return ""

    # ── Planning ──────────────────────────────────────────────────────────────

    def _plan(self, topic: str, deck_type: str, context: str,
              data: dict, client_name: str) -> dict:
        """Ask Claude Sonnet to plan the full slide manifest as JSON."""
        kb = self._base.central_kb_context(
            f"{deck_type} consulting deck {topic}", top_k=8, max_chars=4000
        )
        guide = _DECK_GUIDES.get(deck_type, _DECK_GUIDES["strategy"])
        today = datetime.now().strftime("%B %d, %Y")

        system = (
            "You are a McKinsey/PwC-calibre consulting deck architect for "
            "Latitude MedTech LLC — an AI-powered management consulting firm "
            "whose mission is 'Advancing Human Intelligence'.\n\n"
            "Produce client-facing, Big 4-quality slide structures: "
            "Pyramid Principle, MECE logic, 'so what' headlines on every "
            "data slide, max 5 bullets per slide, concrete outcomes over "
            "vague language. Every recommendation must be defensible and "
            "specific. The 'Advancing Human Intelligence' theme should subtly "
            "inform framing — we use AI and expertise to reduce complexity "
            "and elevate human decision-making, never to replace judgment.\n\n"
            f"{self._base.firm_context()}\n\n"
            f"## Knowledge Base\n{kb}"
        )

        meta = [f"Topic: {topic}", f"Deck type: {deck_type}", f"Date: {today}"]
        if client_name:
            meta.append(f"Client / audience: {client_name}")
            brief = self._find_client_brief(client_name)
            if brief:
                meta.append(
                    f"## Existing client file for {client_name}\n"
                    f"Use this to tailor slide content, framing, and recommendations "
                    f"specifically to this client's background, goals, and program match:\n\n"
                    f"{brief}"
                )
            else:
                log.info(f"No existing brief found for client: {client_name!r}")
        if context:
            meta.append(f"Additional context: {context}")
        if data:
            meta.append(f"Pre-loaded data: {json.dumps(data)}")

        prompt = (
            "\n".join(meta) + "\n\n"
            f"## Deck type guidance\n{guide}\n\n"
            f"## Slide JSON schema\n{_SLIDE_SCHEMA}\n\n"
            "Return ONLY a valid JSON object — no markdown fences, no explanation:\n"
            '{"deck_title": "...", "deck_subtitle": "...", "slides": [...]}'
        )

        log.info("Planning deck with Claude Sonnet…")
        resp = self._claude().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        self._base.log_api("claude-sonnet-4-6",
                           resp.usage.input_tokens, resp.usage.output_tokens,
                           purpose="deck_plan")
        return _parse_json(raw)

    # ── Figure generation ─────────────────────────────────────────────────────

    def _make_chart(self, slide_def: dict) -> str:
        """Generate a branded PNG for a data_chart slide. Returns PNG path."""
        try:
            from figures import bar_chart, grouped_bar, trend_line
        except ImportError as e:
            log.warning(f"figures.py unavailable: {e}")
            return ""

        ctype = slide_def.get("chart_type", "bar")
        cdata = slide_def.get("chart_data", {})
        title = slide_def.get("insight_headline", "Data")

        try:
            if ctype == "bar":
                return bar_chart(
                    title,
                    cdata.get("labels", []),
                    cdata.get("values", []),
                    ylabel=cdata.get("ylabel", ""),
                    highlight=cdata.get("highlight_index"),
                )
            elif ctype == "grouped_bar":
                return grouped_bar(
                    title,
                    cdata.get("categories", []),
                    cdata.get("series", {}),
                    ylabel=cdata.get("ylabel", ""),
                )
            elif ctype == "trend_line":
                return trend_line(
                    title,
                    cdata.get("x", []),
                    cdata.get("series", {}),
                    ylabel=cdata.get("ylabel", ""),
                )
        except Exception as e:
            log.warning(f"Chart generation failed ({ctype}): {e}")
        return ""

    def _make_roadmap_chart(self, headline: str, steps: list) -> str:
        """Generate a process_steps PNG for roadmap slides."""
        try:
            from figures import process_steps
            tuples = [(s.get("title", ""), s.get("detail", "")) for s in steps[:6]]
            return process_steps(headline, tuples)
        except Exception as e:
            log.warning(f"Roadmap chart failed: {e}")
            return ""

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render(self, plan: dict, client_name: str) -> "Presentation":
        from pptx import Presentation as PPT
        from pptx.util import Inches as _Inches
        from deck_skills import DeckSkills

        prs = PPT()
        prs.slide_width  = _Inches(13.333)
        prs.slide_height = _Inches(7.5)
        skills = DeckSkills(prs)

        for s in plan.get("slides", []):
            stype = s.get("type", "")
            log.info(f"  Rendering slide: {stype}")

            if stype == "cover":
                skills.add_cover(
                    s.get("title", plan.get("deck_title", "")),
                    subtitle=s.get("subtitle", plan.get("deck_subtitle", "")),
                    date=s.get("date", datetime.now().strftime("%B %Y")),
                    client_name=client_name,
                )
            elif stype == "exec_summary":
                skills.add_exec_summary(
                    s.get("situation", ""),
                    s.get("complication", ""),
                    s.get("recommendation", ""),
                    s.get("findings", []),
                )
            elif stype == "section_divider":
                skills.add_section_divider(
                    s.get("section_title", ""),
                    s.get("subtitle", ""),
                )
            elif stype == "content_bullets":
                skills.add_content_bullets(
                    s.get("headline", ""),
                    s.get("bullets", []),
                    note=s.get("note", ""),
                )
            elif stype == "two_column":
                skills.add_two_column(
                    s.get("headline", ""),
                    s.get("left_title", ""),  s.get("left_bullets", []),
                    s.get("right_title", ""), s.get("right_bullets", []),
                )
            elif stype == "data_chart":
                png = self._make_chart(s)
                skills.add_data_chart(
                    s.get("insight_headline", ""),
                    png,
                    data_source=s.get("data_source", ""),
                )
            elif stype == "comparison_table":
                skills.add_comparison_table(
                    s.get("headline", ""),
                    s.get("col_headers", []),
                    s.get("rows", []),
                )
            elif stype == "roadmap":
                steps = s.get("steps", [])
                png = self._make_roadmap_chart(s.get("headline", ""), steps)
                skills.add_roadmap(s.get("headline", ""), steps, chart_path=png)
            elif stype == "recommendation":
                skills.add_recommendation(
                    s.get("recommendation", ""),
                    s.get("rationale", []),
                )
            elif stype == "next_steps":
                skills.add_next_steps(s.get("steps", []))
            elif stype == "appendix_cover":
                skills.add_appendix_cover()
            else:
                log.warning(f"Unknown slide type '{stype}' — skipped")

        return prs

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(self, topic: str, deck_type: str = "strategy",
                 context: str = "", data: dict = None,
                 client_name: str = "") -> dict:
        """
        Plan and render a PPTX deck. Returns:
          {status, path, title, slide_count, deck_type}
        """
        data = data or {}
        log.info(f"Deck agent starting: type={deck_type!r}, topic={topic!r}")

        plan = self._plan(topic, deck_type, context, data, client_name)

        title      = plan.get("deck_title", topic)
        slide_list = plan.get("slides", [])
        n_slides   = len(slide_list)
        log.info(f"Plan: {n_slides} slides — '{title}'")

        prs = self._render(plan, client_name)

        slug     = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:50]
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ts}_{slug}.pptx"
        out_path = DECKS_DIR / filename
        prs.save(str(out_path))

        # Gate 10 — submit for Steven's review before treating as final
        try:
            from memory import Memory as _Mem
            review_id = _Mem().submit_for_review("deck_agent", "deck", title, str(out_path))
            log.info(f"Submitted for review: id={review_id}")
        except Exception as _re:
            log.warning(f"Review queue submit failed: {_re!r}")
            review_id = None

        result = {
            "status":      "ok",
            "path":        str(out_path),
            "filename":    filename,
            "title":       title,
            "subtitle":    plan.get("deck_subtitle", ""),
            "slide_count": n_slides,
            "deck_type":   deck_type,
            "review_id":   review_id,
        }
        log.info(f"Deck saved: {out_path} ({n_slides} slides)")
        self._base.log("generate", subject=title,
                       metadata={"deck_type": deck_type, "slides": n_slides, "path": str(out_path)})
        return result


# ── JSON extraction ───────────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    """Extract JSON from Claude's response, tolerating markdown fences."""
    # Strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract the first {...} block
        m = re.search(r"\{[\s\S]+\}", cleaned)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    log.error("JSON parse failed; returning empty plan")
    return {"deck_title": "Untitled Deck", "deck_subtitle": "", "slides": []}


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli():
    ap = argparse.ArgumentParser(description="Latitude MedTech Deck Agent")
    ap.add_argument("--topic",  required=True, help="Deck topic / title")
    ap.add_argument("--type",   default="strategy",
                    choices=list(_DECK_GUIDES.keys()),
                    help="Deck template")
    ap.add_argument("--client", default="", help="Client name or audience")
    ap.add_argument("--context", default="", help="Extra context for the planner")
    args = ap.parse_args()

    result = DeckAgent().generate(
        args.topic, deck_type=args.type,
        context=args.context, client_name=args.client,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli()
