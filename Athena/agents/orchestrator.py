"""
Latitude MedTech — LangGraph Orchestrator  (Phase 1A)
=====================================================
Replaces ad-hoc subprocess invocation with an inspectable workflow graph for
the active business line: **Coaching**.

Workflow (mirrors the documented trigger chain in .claude/rules/agents.md):

    intake  ->  generate_brief  ->  [HUMAN GATE]  ->  finalize  ->  END
                                         |
                                  rejected -> END

The HUMAN GATE is a real LangGraph `interrupt()`: the graph pauses after the
brief is queued for review and does not proceed until Steven approves or rejects
it in the UI. State is persisted with a SQLite checkpointer, so a paused run
survives a backend restart and is resumed by `thread_id`.

This satisfies the Phase 1A gate: *Steve can run the full coaching workflow
end-to-end, and no output is finalized without his approval.*

CLI (headless test / manual run):
    python orchestrator.py "Jane Smith"            # start; pauses at human gate
    python orchestrator.py --resume <thread_id> --approve
    python orchestrator.py --resume <thread_id> --reject --notes "off-scope"
    python orchestrator.py --status <thread_id>
"""

import sys
import argparse
import operator
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver

# Load the API key from the code-tree .env (agents resolve it via the server's
# inherited env when launched there; this makes standalone CLI runs work too).
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / "voice" / ".env")

# Reuse existing, tested coaching-brief logic — do not reimplement.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import coaching_brief as cb          # parse_input, generate_brief, save_brief
from memory import Memory

# ── Canonical disclaimer + label (single source of truth) ────────────────────
DISCLAIMER = (
    "DISCLAIMER: This output is produced by Latitude MedTech LLC for educational "
    "and planning purposes only. It is not regulatory, legal, or compliance advice."
)
LABEL = "Alpha — Steve Review Required"

CHECKPOINT_DB = Path.home() / "Athena" / "memory" / "orchestrator_checkpoints.sqlite"


# ── Workflow state ────────────────────────────────────────────────────────────
class CoachingState(TypedDict, total=False):
    raw_input:     str
    thread_id:     str
    client:        dict
    brief:         str
    brief_path:    str
    title:         str
    review_id:     int
    review_status: str
    review_notes:  str
    delivered:     bool
    steps:         Annotated[list, operator.add]


# ── Nodes ─────────────────────────────────────────────────────────────────────
def intake(state: CoachingState) -> dict:
    client = cb.parse_input(state["raw_input"])
    return {"client": client,
            "title": f"Discovery Call Brief — {client['name']}",
            "steps": [f"intake: parsed '{client['name']}' ({client['type']})"]}


def generate_brief(state: CoachingState) -> dict:
    """Generate + save the brief, then queue it for Steven's review.

    Side effects run here (once, on first execution) — never in the node that
    contains interrupt(), which LangGraph re-executes from the top on resume.
    """
    client    = state["client"]
    brief     = cb.generate_brief(client)
    out_path  = cb.save_brief(client, brief)
    review_id = Memory().submit_for_review(
        "coaching_brief", "brief", state["title"],
        str(out_path), thread_id=state.get("thread_id"))
    return {"brief": brief, "brief_path": str(out_path), "review_id": review_id,
            "steps": [f"generate_brief: saved {out_path.name}, queued as review #{review_id}"]}


def human_review(state: CoachingState) -> dict:
    """Hard human gate. Pauses until resumed with the review decision."""
    decision = interrupt({
        "type":       "coaching_brief_review",
        "review_id":  state.get("review_id"),
        "title":      state.get("title"),
        "brief_path": state.get("brief_path"),
        "message":    "Awaiting Steven's approval before the brief is finalized.",
    })
    decision = decision or {}
    return {"review_status": decision.get("status", "rejected"),
            "review_notes":  decision.get("notes", ""),
            "steps": [f"human_review: {decision.get('status', 'rejected')}"]}


def finalize(state: CoachingState) -> dict:
    """Apply the disclaimer layer and mark the brief delivery-ready."""
    path = Path(state["brief_path"])
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if DISCLAIMER not in text:
            notes = state.get("review_notes", "")
            footer = (f"\n\n---\n\n*{LABEL} · Approved by Steven "
                      f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                      f"{(' · Notes: ' + notes) if notes else ''}*\n\n"
                      f"> {DISCLAIMER}\n")
            path.write_text(text + footer, encoding="utf-8")
    return {"delivered": True,
            "steps": ["finalize: disclaimer + label applied, brief delivery-ready"]}


def route_after_review(state: CoachingState) -> str:
    return "finalize" if state.get("review_status") == "approved" else "rejected"


# ── Graph factory (module-level, persistent checkpointer) ─────────────────────
def _build_graph():
    builder = StateGraph(CoachingState)
    builder.add_node("intake", intake)
    builder.add_node("generate_brief", generate_brief)
    builder.add_node("human_review", human_review)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "generate_brief")
    builder.add_edge("generate_brief", "human_review")
    builder.add_conditional_edges("human_review", route_after_review,
                                  {"finalize": "finalize", "rejected": END})
    builder.add_edge("finalize", END)

    CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
    return builder.compile(checkpointer=SqliteSaver(conn))


_GRAPH = None
def graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


# ── Public API (used by the backend + CLI) ────────────────────────────────────
def _slug(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "client"


def start_coaching(raw_input: str, thread_id: str = None) -> dict:
    """Run the workflow up to the human gate. Returns the pause payload."""
    client    = cb.parse_input(raw_input)
    thread_id = thread_id or f"coaching-{_slug(client['name'])}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    config    = {"configurable": {"thread_id": thread_id}}
    graph().invoke({"raw_input": raw_input, "thread_id": thread_id}, config)
    values = graph().get_state(config).values
    return {"status": "awaiting_review", "thread_id": thread_id,
            "review_id": values.get("review_id"), "title": values.get("title"),
            "brief_path": values.get("brief_path"), "steps": values.get("steps", [])}


def resume_coaching(thread_id: str, status: str, notes: str = "") -> dict:
    """Resume a paused workflow with Steven's decision ('approved'|'rejected')."""
    config = {"configurable": {"thread_id": thread_id}}
    snap = graph().get_state(config)
    if not snap.values:
        return {"status": "unknown_thread", "thread_id": thread_id}
    graph().invoke(Command(resume={"status": status, "notes": notes}), config)
    values = graph().get_state(config).values
    return {"status": "finalized" if values.get("delivered") else status,
            "thread_id": thread_id, "review_status": values.get("review_status"),
            "delivered": values.get("delivered", False), "steps": values.get("steps", [])}


def get_status(thread_id: str) -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    snap = graph().get_state(config)
    return {"thread_id": thread_id, "next": list(snap.next),
            "values": {k: v for k, v in snap.values.items() if k != "brief"}}


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Latitude MedTech coaching orchestrator")
    ap.add_argument("client", nargs="?", help="Client name or LinkedIn URL")
    ap.add_argument("--resume", metavar="THREAD_ID")
    ap.add_argument("--approve", action="store_true")
    ap.add_argument("--reject", action="store_true")
    ap.add_argument("--notes", default="")
    ap.add_argument("--status", metavar="THREAD_ID")
    args = ap.parse_args()

    if args.status:
        import json; print(json.dumps(get_status(args.status), indent=2)); return

    if args.resume:
        status = "approved" if args.approve else "rejected"
        result = resume_coaching(args.resume, status, args.notes)
        print(f"\n[RESUME] thread={args.resume} -> {result['status']}")
        for s in result.get("steps", []): print(f"  - {s}")
        return

    if not args.client:
        ap.error("Provide a client name/URL to start, or --resume <thread_id>.")

    print(f"\n[START] Coaching workflow for: {args.client}")
    result = start_coaching(args.client)
    print(f"  thread_id : {result['thread_id']}")
    print(f"  review #  : {result['review_id']}  (PAUSED at human gate)")
    for s in result.get("steps", []): print(f"  - {s}")
    print(f"\nApprove:  python orchestrator.py --resume {result['thread_id']} --approve")
    print(f"Reject :  python orchestrator.py --resume {result['thread_id']} --reject --notes \"...\"")


if __name__ == "__main__":
    main()
