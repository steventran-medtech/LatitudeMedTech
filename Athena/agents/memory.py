"""
Latitude MedTech — Shared Agent Memory
========================================
SQLite-based shared memory layer used by all agents.

Every agent imports this module to:
- Log events (what happened, when, by whom)
- Track Claude API calls + token usage + cost
- Query past activity before doing work
- Check if content/docs already exist before making API calls

Single file: ~/Athena/memory/latitude_memory.db

Usage:
    from memory import Memory
    mem = Memory()

    mem.log_event("rag_agent", "ingested", "FDA guidance doc", {"chunks": 12})
    mem.log_api_call("content_agent", "claude-sonnet-4-6", input_tokens=800, output_tokens=400, purpose="draft article")

    if mem.url_ingested("https://fda.gov/..."):
        skip  # already in KB

    if mem.topic_exists(["CAPA", "corrective action"], days=30):
        skip  # already covered

    mem.print_token_report()
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from pathconfig import MEMORY_DIR
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = MEMORY_DIR / 'latitude_memory.db'

CLAUDE_PRICING = {
    'claude-sonnet-4-6': {'input': 3.00,  'output': 15.00},
    'claude-haiku-4-5':  {'input': 0.80,  'output': 4.00},
    'default':           {'input': 3.00,  'output': 15.00},
}


class Memory:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            agent       TEXT    NOT NULL,
            action      TEXT    NOT NULL,
            subject     TEXT,
            metadata    TEXT,
            hash        TEXT
        );

        CREATE TABLE IF NOT EXISTS api_calls (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            agent           TEXT    NOT NULL,
            model           TEXT    NOT NULL,
            input_tokens    INTEGER NOT NULL,
            output_tokens   INTEGER NOT NULL,
            total_tokens    INTEGER NOT NULL,
            cost_usd        REAL    NOT NULL,
            purpose         TEXT,
            cache_hit       INTEGER DEFAULT 0,
            duration_ms     INTEGER
        );

        CREATE TABLE IF NOT EXISTS knowledge_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            agent       TEXT    NOT NULL,
            item_type   TEXT    NOT NULL,
            title       TEXT    NOT NULL,
            url         TEXT    UNIQUE,
            url_hash    TEXT    UNIQUE,
            category    TEXT,
            chunks      INTEGER DEFAULT 0,
            metadata    TEXT
        );

        CREATE TABLE IF NOT EXISTS content_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            agent       TEXT    NOT NULL,
            content_type TEXT   NOT NULL,
            title       TEXT    NOT NULL,
            topic_hash  TEXT,
            status      TEXT    DEFAULT 'draft',
            file_path   TEXT,
            metadata    TEXT
        );

        CREATE TABLE IF NOT EXISTS daily_summaries (
            date        TEXT    PRIMARY KEY,
            total_calls INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            total_cost  REAL    DEFAULT 0,
            cache_hits  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS agent_learning (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            agent       TEXT    NOT NULL,
            source_name TEXT    NOT NULL,
            source_url  TEXT,
            title       TEXT,
            domain      TEXT,
            chunks_added INTEGER DEFAULT 0,
            url_hash    TEXT    UNIQUE
        );

        CREATE TABLE IF NOT EXISTS agent_health (
            agent           TEXT    PRIMARY KEY,
            last_run        TEXT,
            last_learning   TEXT,
            error_count_7d  INTEGER DEFAULT 0,
            learning_7d     INTEGER DEFAULT 0,
            flag_status     TEXT    DEFAULT 'green',
            flag_reason     TEXT,
            reviewed_at     TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_events_agent  ON events(agent, timestamp);
        CREATE INDEX IF NOT EXISTS idx_api_agent     ON api_calls(agent, timestamp);
        CREATE INDEX IF NOT EXISTS idx_api_model     ON api_calls(model, timestamp);
        CREATE INDEX IF NOT EXISTS idx_kb_url        ON knowledge_items(url_hash);
        CREATE INDEX IF NOT EXISTS idx_content_topic ON content_items(topic_hash);
        CREATE INDEX IF NOT EXISTS idx_learning_agent ON agent_learning(agent, timestamp);

        CREATE TABLE IF NOT EXISTS review_queue (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            agent       TEXT    NOT NULL,
            item_type   TEXT    NOT NULL,
            title       TEXT    NOT NULL,
            file_path   TEXT,
            status      TEXT    DEFAULT 'pending',
            reviewed_at TEXT,
            reviewer    TEXT    DEFAULT 'Steven',
            notes       TEXT,
            thread_id   TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_review_status ON review_queue(status, timestamp);
        """)
        # Migration: add thread_id to review_queue on DBs created before LangGraph
        # orchestration (Phase 1A). Links a queue item to its paused workflow thread.
        cols = [r[1] for r in self.conn.execute("PRAGMA table_info(review_queue)").fetchall()]
        if "thread_id" not in cols:
            self.conn.execute("ALTER TABLE review_queue ADD COLUMN thread_id TEXT")
        self.conn.commit()

    # ── Events ────────────────────────────────────────────────────────────────

    def log_event(self, agent, action, subject=None, metadata=None, dedup_hash=None):
        self.conn.execute(
            "INSERT INTO events (timestamp,agent,action,subject,metadata,hash) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(), agent, action, subject,
             json.dumps(metadata) if metadata else None, dedup_hash)
        )
        self.conn.commit()

    # ── API call tracking ─────────────────────────────────────────────────────

    def log_api_call(self, agent, model, input_tokens, output_tokens,
                     purpose=None, cache_hit=False, duration_ms=None):
        pricing = CLAUDE_PRICING.get(model, CLAUDE_PRICING['default'])
        cost    = (input_tokens * pricing['input'] + output_tokens * pricing['output']) / 1_000_000
        total   = input_tokens + output_tokens
        ts      = datetime.now().isoformat()
        date    = datetime.now().strftime('%Y-%m-%d')

        self.conn.execute(
            """INSERT INTO api_calls
               (timestamp,agent,model,input_tokens,output_tokens,total_tokens,
                cost_usd,purpose,cache_hit,duration_ms)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (ts, agent, model, input_tokens, output_tokens, total,
             cost, purpose, 1 if cache_hit else 0, duration_ms)
        )
        self.conn.execute("""
            INSERT INTO daily_summaries (date,total_calls,total_tokens,total_cost,cache_hits)
            VALUES (?,1,?,?,?)
            ON CONFLICT(date) DO UPDATE SET
                total_calls  = total_calls+1,
                total_tokens = total_tokens+?,
                total_cost   = total_cost+?,
                cache_hits   = cache_hits+?
        """, (date, total, cost, 1 if cache_hit else 0, total, cost, 1 if cache_hit else 0))
        self.conn.commit()
        return cost

    # ── Knowledge base ────────────────────────────────────────────────────────

    def register_document(self, agent, title, url=None, category=None,
                          chunks=0, item_type='document', metadata=None):
        url_hash = hashlib.md5((url or title).encode()).hexdigest()
        try:
            self.conn.execute(
                """INSERT INTO knowledge_items
                   (timestamp,agent,item_type,title,url,url_hash,category,chunks,metadata)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (datetime.now().isoformat(), agent, item_type, title, url,
                 url_hash, category, chunks, json.dumps(metadata) if metadata else None)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def url_ingested(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.conn.execute(
            "SELECT id FROM knowledge_items WHERE url_hash=?", (url_hash,)
        ).fetchone() is not None

    def get_kb_stats(self):
        row    = self.conn.execute(
            "SELECT COUNT(*) as docs, SUM(chunks) as chunks FROM knowledge_items"
        ).fetchone()
        by_cat = self.conn.execute(
            "SELECT category, COUNT(*) as n FROM knowledge_items GROUP BY category ORDER BY n DESC"
        ).fetchall()
        return {
            "total_docs":   row["docs"] or 0,
            "total_chunks": row["chunks"] or 0,
            "by_category":  {r["category"]: r["n"] for r in by_cat},
        }

    # ── Content dedup ─────────────────────────────────────────────────────────

    def register_content(self, agent, content_type, title,
                         topic_keywords=None, status='draft',
                         file_path=None, metadata=None):
        topic_str  = ' '.join(sorted((topic_keywords or [title]))).lower()
        topic_hash = hashlib.md5(topic_str.encode()).hexdigest()
        self.conn.execute(
            """INSERT INTO content_items
               (timestamp,agent,content_type,title,topic_hash,status,file_path,metadata)
               VALUES (?,?,?,?,?,?,?,?)""",
            (datetime.now().isoformat(), agent, content_type, title,
             topic_hash, status, file_path, json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()

    def topic_exists(self, topic_keywords, content_type=None, days=60):
        topic_str  = ' '.join(sorted(topic_keywords)).lower()
        topic_hash = hashlib.md5(topic_str.encode()).hexdigest()
        cutoff     = (datetime.now() - timedelta(days=days)).isoformat()
        q = "SELECT title FROM content_items WHERE topic_hash=? AND timestamp>?"
        p = [topic_hash, cutoff]
        if content_type:
            q += " AND content_type=?"; p.append(content_type)
        row = self.conn.execute(q, p).fetchone()
        return row["title"] if row else None

    def get_recent_topics(self, content_type=None, days=90):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        q = "SELECT title, timestamp FROM content_items WHERE timestamp>?"
        p = [cutoff]
        if content_type:
            q += " AND content_type=?"; p.append(content_type)
        q += " ORDER BY timestamp DESC"
        return [{"title": r["title"], "timestamp": r["timestamp"]}
                for r in self.conn.execute(q, p).fetchall()]

    def update_content_status(self, title, status):
        self.conn.execute(
            "UPDATE content_items SET status=? WHERE title=?", (status, title)
        )
        self.conn.commit()

    # ── Briefing dedup ────────────────────────────────────────────────────────

    def briefing_item_seen(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.conn.execute(
            "SELECT id FROM events WHERE action='briefing_item' AND hash=?",
            (url_hash,)
        ).fetchone() is not None

    def mark_briefing_items(self, agent, urls):
        for url in urls:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            try:
                self.conn.execute(
                    "INSERT INTO events (timestamp,agent,action,subject,hash) VALUES (?,?,?,?,?)",
                    (datetime.now().isoformat(), agent, 'briefing_item', url, url_hash)
                )
            except Exception:
                pass
        self.conn.commit()

    # ── Token report ──────────────────────────────────────────────────────────

    def get_token_report(self, days=30):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        totals = self.conn.execute("""
            SELECT COUNT(*) as total_calls,
                   SUM(input_tokens) as total_input,
                   SUM(output_tokens) as total_output,
                   SUM(total_tokens) as total_tokens,
                   SUM(cost_usd) as total_cost,
                   SUM(cache_hit) as cache_hits,
                   AVG(total_tokens) as avg_tokens
            FROM api_calls WHERE timestamp>?
        """, (cutoff,)).fetchone()

        by_agent = self.conn.execute("""
            SELECT agent, COUNT(*) as calls, SUM(total_tokens) as tokens, SUM(cost_usd) as cost
            FROM api_calls WHERE timestamp>? GROUP BY agent ORDER BY cost DESC
        """, (cutoff,)).fetchall()

        by_model = self.conn.execute("""
            SELECT model, COUNT(*) as calls, SUM(total_tokens) as tokens, SUM(cost_usd) as cost
            FROM api_calls WHERE timestamp>? GROUP BY model ORDER BY cost DESC
        """, (cutoff,)).fetchall()

        by_purpose = self.conn.execute("""
            SELECT purpose, COUNT(*) as calls, SUM(total_tokens) as tokens, SUM(cost_usd) as cost
            FROM api_calls WHERE timestamp>? AND purpose IS NOT NULL
            GROUP BY purpose ORDER BY cost DESC LIMIT 10
        """, (cutoff,)).fetchall()

        daily = self.conn.execute("""
            SELECT date, total_calls, total_tokens, total_cost, cache_hits
            FROM daily_summaries WHERE date >= date('now','-7 days')
            ORDER BY date DESC
        """).fetchall()

        return {
            "period_days": days,
            "totals":      dict(totals) if totals else {},
            "by_agent":    [dict(r) for r in by_agent],
            "by_model":    [dict(r) for r in by_model],
            "by_purpose":  [dict(r) for r in by_purpose],
            "daily_trend": [dict(r) for r in daily],
        }

    def print_token_report(self, days=30):
        r  = self.get_token_report(days)
        t  = r.get("totals", {})
        tc = t.get("total_cost") or 0
        tt = t.get("total_tokens") or 0
        ca = t.get("total_calls") or 0
        ch = t.get("cache_hits") or 0
        cr = (ch / ca * 100) if ca > 0 else 0
        av = t.get("avg_tokens") or 0

        print(f"""
+--------------------------------------------------+
|  Latitude MedTech Token Usage Report             |
|  Last {days} days                                  |
+--------------------------------------------------+
|  Total API calls  : {str(ca):<29}|
|  Total tokens     : {str(tt):<29}|
|  Total cost (USD) : ${tc:<28.4f}|
|  Avg tokens/call  : {str(int(av)):<29}|
|  Cache hit rate   : {f'{cr:.1f}%':<29}|
+--------------------------------------------------+""")

        if r["by_agent"]:
            print("|  By agent:                                       |")
            for a in r["by_agent"]:
                print(f"|    {a['agent']:<18} {a['calls']:>5} calls  ${a['cost']:.4f}   |")

        if r["by_model"]:
            print("+--------------------------------------------------+")
            print("|  By model:                                       |")
            for m in r["by_model"]:
                print(f"|    {m['model']:<22} ${m['cost']:.4f}         |")

        if r["daily_trend"]:
            print("+--------------------------------------------------+")
            print("|  Last 7 days:                                    |")
            for d in r["daily_trend"]:
                print(f"|    {d['date']}  {d['total_calls']:>3} calls  ${d['total_cost']:.4f}     |")

        if r["by_purpose"]:
            print("+--------------------------------------------------+")
            print("|  Top token consumers:                            |")
            for p in r["by_purpose"][:5]:
                print(f"|    {str(p['purpose'])[:28]:<28} ${p['cost']:.4f}   |")

        print("+--------------------------------------------------+")

    # ── Agent learning tracking ───────────────────────────────────────────────

    def log_learning(self, agent, source_name, title, source_url=None,
                     domain=None, chunks_added=0):
        """Record that an agent ingested a learning item."""
        url_hash = hashlib.md5((source_url or title).encode()).hexdigest()
        try:
            self.conn.execute(
                """INSERT INTO agent_learning
                   (timestamp,agent,source_name,source_url,title,domain,chunks_added,url_hash)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (datetime.now().isoformat(), agent, source_name,
                 source_url, title, domain, chunks_added, url_hash)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # already ingested

    def learning_ingested(self, url_or_title):
        h = hashlib.md5(url_or_title.encode()).hexdigest()
        return self.conn.execute(
            "SELECT id FROM agent_learning WHERE url_hash=?", (h,)
        ).fetchone() is not None

    def get_learning_stats(self, agent=None, days=7):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        q = "SELECT agent, COUNT(*) as items, SUM(chunks_added) as chunks FROM agent_learning WHERE timestamp>?"
        p = [cutoff]
        if agent:
            q += " AND agent=?"; p.append(agent)
        q += " GROUP BY agent ORDER BY items DESC"
        return [dict(r) for r in self.conn.execute(q, p).fetchall()]

    def get_skill_accumulation(self, agent):
        """
        All-time accumulation for one agent across BOTH learning streams —
        curated learning (agent_learning) + RAG ingestion (knowledge_items) —
        matching every name variant the agent may have logged under.

        Returns:
          {learn_items, learn_chunks, kb_docs, kb_chunks,
           total_items, total_chunks, domains[], last}
        Single source of truth for the dashboards and the skills profiles.
        """
        names = self._name_variants(agent)
        ph    = ",".join("?" * len(names))

        lr = self.conn.execute(
            f"SELECT COUNT(*) as items, COALESCE(SUM(chunks_added),0) as chunks, "
            f"MAX(timestamp) as last FROM agent_learning WHERE agent IN ({ph})",
            names,
        ).fetchone()
        kb = self.conn.execute(
            f"SELECT COUNT(*) as docs, COALESCE(SUM(chunks),0) as chunks, "
            f"MAX(timestamp) as last FROM knowledge_items WHERE agent IN ({ph})",
            names,
        ).fetchone()
        domains = [
            r["domain"] for r in self.conn.execute(
                f"SELECT DISTINCT domain FROM agent_learning "
                f"WHERE agent IN ({ph}) AND domain IS NOT NULL ORDER BY domain", names,
            ).fetchall()
        ]
        last = max([t for t in (lr["last"], kb["last"]) if t], default=None)
        return {
            "learn_items":  lr["items"],
            "learn_chunks": lr["chunks"],
            "kb_docs":      kb["docs"],
            "kb_chunks":    kb["chunks"],
            "total_items":  lr["items"] + kb["docs"],
            "total_chunks": lr["chunks"] + kb["chunks"],
            "domains":      domains,
            "last":         last,
        }

    # Agent names are logged inconsistently across the codebase — some modules
    # log under a short key ("content") and others under the script name
    # ("content_agent"). HR/Workforce queries use the short key, so without
    # alias expansion "Last run / Last learned" always reads "Never".
    _AGENT_ALIASES = {
        "content":         ["content", "content_agent"],
        "briefing":        ["briefing", "briefing_agent"],
        "iso":             ["iso", "iso_coach", "iso_coach_agent"],
        "coaching":        ["coaching", "coaching_brief", "coaching_brief_agent", "orchestrator"],
        "fda":             ["fda", "fda_agent"],
        "rag":             ["rag", "rag_agent"],
        "consulting":      ["consulting", "consulting_agent"],
        "ma_intelligence": ["ma_intelligence", "ma_intelligence_agent"],
        "voice_bridge":    ["voice_bridge", "voice", "athena"],
    }

    @classmethod
    def _name_variants(cls, agent):
        """All name spellings an agent may have logged activity under."""
        if agent in cls._AGENT_ALIASES:
            return cls._AGENT_ALIASES[agent]
        base = agent[:-6] if agent.endswith("_agent") else agent
        # dict.fromkeys preserves order while de-duping
        return list(dict.fromkeys([agent, base, base + "_agent"]))

    def get_last_learning(self, agent):
        """
        Check agent_learning first, then fall back to knowledge_items
        (RAG ingestion also counts as learning activity).
        Matches every name variant the agent may have logged under.
        """
        names = self._name_variants(agent)
        ph    = ",".join("?" * len(names))
        row = self.conn.execute(
            f"SELECT timestamp, title, source_name FROM agent_learning "
            f"WHERE agent IN ({ph}) ORDER BY timestamp DESC LIMIT 1", names
        ).fetchone()
        if row:
            return dict(row)
        # Fallback: check knowledge_items for this agent's ingestion activity
        row2 = self.conn.execute(
            f"SELECT timestamp, title FROM knowledge_items "
            f"WHERE agent IN ({ph}) ORDER BY timestamp DESC LIMIT 1", names
        ).fetchone()
        if row2:
            return {"timestamp": row2["timestamp"], "title": row2["title"],
                    "source_name": "knowledge_base"}
        # Fallback: any API call by this agent
        row3 = self.conn.execute(
            f"SELECT timestamp FROM api_calls WHERE agent IN ({ph}) "
            f"ORDER BY timestamp DESC LIMIT 1", names
        ).fetchone()
        if row3:
            return {"timestamp": row3["timestamp"], "title": "API activity",
                    "source_name": "api_calls"}
        return None

    # ── Agent health (HR) ─────────────────────────────────────────────────────

    def upsert_agent_health(self, agent, last_run=None, last_learning=None,
                            error_count_7d=None, learning_7d=None,
                            flag_status=None, flag_reason=None):
        existing = self.conn.execute(
            "SELECT agent FROM agent_health WHERE agent=?", (agent,)
        ).fetchone()
        if existing:
            sets, params = [], []
            for col, val in [("last_run", last_run), ("last_learning", last_learning),
                             ("error_count_7d", error_count_7d), ("learning_7d", learning_7d),
                             ("flag_status", flag_status), ("flag_reason", flag_reason)]:
                if val is not None:
                    sets.append(f"{col}=?"); params.append(val)
            if sets:
                params.append(agent)
                self.conn.execute(f"UPDATE agent_health SET {','.join(sets)} WHERE agent=?", params)
        else:
            self.conn.execute(
                """INSERT INTO agent_health
                   (agent,last_run,last_learning,error_count_7d,learning_7d,flag_status,flag_reason)
                   VALUES (?,?,?,?,?,?,?)""",
                (agent, last_run, last_learning,
                 error_count_7d or 0, learning_7d or 0,
                 flag_status or "green", flag_reason)
            )
        self.conn.commit()

    def get_all_agent_health(self):
        return [dict(r) for r in
                self.conn.execute("SELECT * FROM agent_health ORDER BY flag_status, agent").fetchall()]

    def get_agent_error_count(self, agent, days=7):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) as n FROM events WHERE agent=? AND action='error' AND timestamp>?",
            (agent, cutoff)
        ).fetchone()
        return row["n"] if row else 0

    def get_agent_last_run(self, agent):
        """
        Last time this agent did meaningful work. Checks events table,
        api_calls, and knowledge_items so past activity is reflected.
        Matches every name variant the agent may have logged under.
        """
        names = self._name_variants(agent)
        ph    = ",".join("?" * len(names))
        # Take the most recent timestamp across all three activity tables so a
        # learning run (knowledge_items) counts even if it never hit api_calls.
        row = self.conn.execute(
            f"""SELECT MAX(ts) AS ts FROM (
                    SELECT timestamp AS ts FROM events         WHERE agent IN ({ph})
                    UNION ALL
                    SELECT timestamp AS ts FROM api_calls      WHERE agent IN ({ph})
                    UNION ALL
                    SELECT timestamp AS ts FROM knowledge_items WHERE agent IN ({ph})
                    UNION ALL
                    SELECT timestamp AS ts FROM agent_learning WHERE agent IN ({ph})
                )""", names * 4
        ).fetchone()
        return row["ts"] if row and row["ts"] else None

    # ── Context summary (used by voice assistant) ─────────────────────────────

    def context_summary(self) -> str:
        """Return a short text summary of recent firm activity for voice context."""
        lines = []
        # Recent content
        recent = self.get_recent_topics(days=7)
        if recent:
            lines.append(f"Recent drafts: {', '.join(t['title'][:40] for t in recent[:3])}")
        # KB size
        kb = self.get_kb_stats()
        if kb["total_docs"]:
            lines.append(f"Knowledge base: {kb['total_docs']} docs, {kb['total_chunks']} chunks")
        # Agent health flags
        flags = [h for h in self.get_all_agent_health() if h["flag_status"] != "green"]
        if flags:
            lines.append(f"Flagged agents: {', '.join(h['agent'] for h in flags)}")
        return ". ".join(lines) if lines else ""

    # ── Human Review Queue (Phase 1A gate) ───────────────────────────────────

    def submit_for_review(self, agent: str, item_type: str, title: str,
                          file_path: str = None, thread_id: str = None):
        """Submit any agent output for Steven's review before it's considered final.

        Returns the new review_queue row id so an orchestrator can link the item
        to a paused workflow thread (thread_id) and resume it on approval.
        """
        cur = self.conn.execute(
            "INSERT INTO review_queue (timestamp,agent,item_type,title,file_path,thread_id) "
            "VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(), agent, item_type, title, file_path, thread_id)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_review(self, item_id: int):
        """Fetch a single review_queue row by id (or None)."""
        row = self.conn.execute(
            "SELECT * FROM review_queue WHERE id=?", (item_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_pending_reviews(self):
        rows = self.conn.execute(
            "SELECT * FROM review_queue WHERE status='pending' ORDER BY timestamp DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def approve_review(self, item_id: int, notes: str = ""):
        self.conn.execute(
            "UPDATE review_queue SET status='approved', reviewed_at=?, notes=? WHERE id=?",
            (datetime.now().isoformat(), notes, item_id)
        )
        self.conn.commit()

    def reject_review(self, item_id: int, notes: str = ""):
        self.conn.execute(
            "UPDATE review_queue SET status='rejected', reviewed_at=?, notes=? WHERE id=?",
            (datetime.now().isoformat(), notes, item_id)
        )
        self.conn.commit()

    def get_review_stats(self):
        row = self.conn.execute(
            "SELECT COUNT(*) FILTER(WHERE status='pending') as pending, "
            "COUNT(*) FILTER(WHERE status='approved') as approved, "
            "COUNT(*) FILTER(WHERE status='rejected') as rejected "
            "FROM review_queue"
        ).fetchone()
        return dict(row) if row else {"pending": 0, "approved": 0, "rejected": 0}

    def close(self):
        self.conn.close()
