"""
Latitude MedTech — Agent Base
================================
Shared utilities for all agents:
- Load agent context from .claude/agents/<name>.md
- KB-first query helper (search before calling Claude API)
- Standardised system prompt builder
- Memory logging

Usage:
    from agent_base import AgentBase
    base = AgentBase("content")
    system = base.system_prompt("Write a draft about CAPA")
    kb_ctx = base.kb_context("CAPA corrective action")
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ATHENA     = Path.home() / "Athena"
RULES_DIR  = Path(r"C:\Users\huann\LatitudeMedTech\.claude\agents")
CLAUDE_MD  = Path(r"C:\Users\huann\LatitudeMedTech\CLAUDE.md")

load_dotenv(ATHENA / "voice" / ".env")
sys.path.insert(0, str(ATHENA / "agents"))

# Shared memory + KB
try:
    from memory import Memory
    _mem = Memory()
except Exception:
    _mem = None

try:
    from kb_query import KBQuery
    _kb = KBQuery()
except Exception:
    _kb = None


class AgentBase:
    def __init__(self, agent_name: str):
        self.name    = agent_name
        self._ctx    = None   # lazy-loaded context file
        self._claude = None   # lazy anthropic client

    # ── Context file ──────────────────────────────────────────────────────────

    def context_file(self) -> str:
        """Load agent persona from .claude/agents/<name>[-agent].md."""
        if self._ctx is not None:
            return self._ctx
        for fname in [f"{self.name}.md", f"{self.name}-agent.md"]:
            f = RULES_DIR / fname
            if f.exists():
                self._ctx = f.read_text(encoding="utf-8")
                return self._ctx
        self._ctx = ""
        return self._ctx

    def firm_context(self, sections=("## Core Values", "## North Star")) -> str:
        """Extract relevant sections from CLAUDE.md for prompt grounding."""
        if not CLAUDE_MD.exists():
            return ""
        raw = CLAUDE_MD.read_text(encoding="utf-8")
        parts = []
        for section in sections:
            start = raw.find(section)
            if start != -1:
                end = raw.find("\n## ", start + 1)
                parts.append(raw[start: end if end != -1 else start + 500])
        return "\n".join(parts)

    # ── KB context ────────────────────────────────────────────────────────────

    def kb_context(self, query: str, top_k: int = 4, max_chars: int = 2500) -> str:
        """Search local KB. Returns formatted context string or empty string."""
        if not _kb or not _kb.has_content():
            return ""
        chunks = _kb.search(query, top_k=top_k)
        return _kb.format_context(chunks, max_chars=max_chars)

    def has_kb(self) -> bool:
        return _kb is not None and _kb.has_content()

    def central_kb_context(self, query: str, top_k: int = 8, max_chars: int = 4000) -> str:
        """
        Query the CENTRAL KB across ALL agent categories.
        Use this for complex tasks that benefit from multi-domain knowledge:
        consulting frameworks + regulatory knowledge + M&A patterns + industry data.
        """
        if not _kb or not _kb.has_content():
            return ""
        chunks = _kb.search(query, top_k=top_k)   # searches all categories
        return _kb.format_context(chunks, max_chars=max_chars)

    # ── System prompt builder ─────────────────────────────────────────────────

    def system_prompt(self, task_context: str = "", include_kb: str = "") -> str:
        """
        Build a complete system prompt:
          firm values + agent persona + task context + KB grounding
        """
        parts = [
            "You are an AI agent for Latitude MedTech LLC, a MedTech and Pharma "
            "management consulting firm in San Diego, CA. "
            "You serve Steven Tran, Managing Partner and CEO.\n",
            self.firm_context(),
            "\n## Your Role\n",
            self.context_file(),
        ]
        if task_context:
            parts.append(f"\n## Current Task\n{task_context}")
        if include_kb:
            parts.append(f"\n## Knowledge Base Context\n{include_kb}")
        parts.append(
            "\n\nALWAYS append this disclaimer to any client-facing output:\n"
            "\"DISCLAIMER: This output is produced by Latitude MedTech LLC for "
            "educational and planning purposes only. Not regulatory or legal advice.\"\n"
            "Label all outputs: Alpha — Steve Review Required."
        )
        return "\n".join(parts)

    # ── Claude API helper ─────────────────────────────────────────────────────

    def _get_client(self):
        if self._claude is None:
            import anthropic
            self._claude = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        return self._claude

    def ask(self, prompt: str, system: str = "", model: str = "claude-haiku-4-5",
            max_tokens: int = 1000) -> str:
        """
        Call Claude with KB-grounded system prompt.
        Uses haiku for speed/cost unless explicitly overridden.
        """
        client = self._get_client()
        if not system:
            system = self.system_prompt()
        resp = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = resp.content[0].text.strip()
        if _mem:
            _mem.log_api_call(
                self.name, model,
                resp.usage.input_tokens, resp.usage.output_tokens,
                purpose=f"{self.name}_ask",
            )
        return answer

    # ── Memory helpers ────────────────────────────────────────────────────────

    def log(self, action: str, subject: str = "", metadata: dict = None):
        if _mem:
            _mem.log_event(self.name, action, subject=subject, metadata=metadata)

    def log_api(self, model, input_tok, output_tok, purpose=""):
        if _mem:
            _mem.log_api_call(self.name, model, input_tok, output_tok, purpose=purpose)
