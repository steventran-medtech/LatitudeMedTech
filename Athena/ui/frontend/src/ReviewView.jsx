/**
 * Human Review Queue — Phase 1A Gate
 * Every client-facing output (briefs, articles) lands here before Steven approves it.
 */
import { useEffect, useRef, useState } from "react";
import { authHdr } from "./api.js";
import FileViewer from "./FileViewer.jsx";

const API = "http://localhost:8000";

// Inline Markdown: **bold**, *italic*, `code`. Safe (no dangerouslySetInnerHTML).
function inlineMd(s, keyBase = "") {
  const parts = s.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g).filter(Boolean);
  return parts.map((p, k) => {
    const key = `${keyBase}-${k}`;
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={key}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("*") && p.endsWith("*"))   return <em key={key}>{p.slice(1, -1)}</em>;
    if (p.startsWith("`") && p.endsWith("`"))
      return <code key={key} style={{ background: "#EEF2F6", padding: "1px 5px",
        borderRadius: 4, fontSize: "0.9em", fontFamily: "ui-monospace,monospace" }}>{p.slice(1, -1)}</code>;
    return <span key={key}>{p}</span>;
  });
}

// Strip leading YAML frontmatter; return { meta: [[k,v]...], body }.
function stripFrontmatter(md) {
  const text = md.replace(/\r\n/g, "\n");
  if (!text.startsWith("---\n")) return { meta: [], body: text };
  const end = text.indexOf("\n---", 3);
  if (end === -1) return { meta: [], body: text };
  const block = text.slice(4, end);
  const rest  = text.slice(text.indexOf("\n", end + 1) + 1);
  const meta  = block.split("\n").map(l => {
    const m = l.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    return m ? [m[1], m[2].replace(/^["']|["']$/g, "")] : null;
  }).filter(Boolean);
  return { meta, body: rest };
}

// Consulting-clean Markdown renderer: frontmatter → metadata strip, proper
// heading hierarchy, serif body, lists, tables, blockquotes, rules.
function renderMarkdown(md) {
  const { meta, body } = stripFrontmatter(md);
  const lines = body.split("\n");
  const out = [];
  let para = [], i = 0;
  const SERIF = "Georgia, 'Times New Roman', serif";

  const flush = () => {
    if (para.length) {
      out.push(<p key={`p${i}-${out.length}`} style={{ margin: "0 0 14px",
        lineHeight: 1.75, color: "#26333F", fontSize: 15, fontFamily: SERIF }}>
        {inlineMd(para.join(" "), `p${i}`)}</p>);
      para = [];
    }
  };

  // Metadata strip (badges) from frontmatter
  if (meta.length) {
    out.push(
      <div key="meta" style={{ display: "flex", flexWrap: "wrap", gap: 8,
        padding: "0 0 16px", marginBottom: 18, borderBottom: "1px solid #EDF1F5" }}>
        {meta.filter(([k]) => !/^title$/i.test(k)).map(([k, v], n) => (
          <span key={n} style={{ fontFamily: "Inter,sans-serif", fontSize: 10.5,
            color: "#5A6B7B", background: "#F4F7FA", border: "1px solid #E3EAF1",
            padding: "3px 9px", borderRadius: 5 }}>
            <span style={{ color: "#9AAAB8", textTransform: "uppercase",
              letterSpacing: "0.06em", fontSize: 9 }}>{k} </span>{v}
          </span>
        ))}
      </div>
    );
  }

  while (i < lines.length) {
    const t = lines[i].trim();

    // Table: a line with pipes followed by a separator row
    if (t.includes("|") && /^\|?.*\|.*$/.test(t) && i + 1 < lines.length &&
        /^\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i + 1].trim())) {
      flush();
      const parseRow = r => r.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
      const head = parseRow(t);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].includes("|")) { rows.push(parseRow(lines[i].trim())); i++; }
      out.push(
        <table key={`tbl${i}`} style={{ width: "100%", borderCollapse: "collapse",
          margin: "8px 0 18px", fontFamily: "Inter,sans-serif", fontSize: 13 }}>
          <thead><tr>{head.map((h, n) => (
            <th key={n} style={{ textAlign: "left", padding: "8px 10px",
              borderBottom: "2px solid #0A2540", color: "#0A2540", fontWeight: 700 }}>
              {inlineMd(h, `th${n}`)}</th>))}</tr></thead>
          <tbody>{rows.map((r, ri) => (
            <tr key={ri}>{r.map((c, ci) => (
              <td key={ci} style={{ padding: "7px 10px", borderBottom: "1px solid #EDF1F5",
                color: "#26333F" }}>{inlineMd(c, `td${ri}${ci}`)}</td>))}</tr>))}</tbody>
        </table>
      );
      continue;
    }

    if (!t) { flush(); i++; continue; }

    if (/^#{1,6}\s/.test(t)) {
      flush();
      const level = t.match(/^#+/)[0].length;
      const text = t.replace(/^#+\s/, "");
      const sizes = { 1: 24, 2: 18, 3: 15.5, 4: 14 };
      out.push(<div key={`h${i}`} style={{ fontFamily: "Inter,sans-serif",
        fontWeight: 700, fontSize: sizes[level] || 14, color: "#0A2540",
        margin: level <= 2 ? "26px 0 10px" : "18px 0 6px",
        lineHeight: 1.3, letterSpacing: level === 1 ? "-0.01em" : 0 }}>{inlineMd(text, `h${i}`)}</div>);
    } else if (/^>\s?/.test(t)) {
      flush();
      out.push(<blockquote key={`bq${i}`} style={{ margin: "0 0 14px",
        padding: "8px 16px", borderLeft: "3px solid #1A6FA3", background: "#F4F8FB",
        color: "#3C5470", fontStyle: "italic", fontFamily: SERIF, fontSize: 14.5 }}>
        {inlineMd(t.replace(/^>\s?/, ""), `bq${i}`)}</blockquote>);
    } else if (/^(\d+)\.\s/.test(t)) {
      flush();
      const num = t.match(/^(\d+)\./)[1];
      out.push(<div key={`ol${i}`} style={{ display: "flex", gap: 10,
        margin: "3px 0", fontFamily: SERIF, fontSize: 15, color: "#26333F", lineHeight: 1.65 }}>
        <span style={{ color: "#1A6FA3", fontWeight: 700, minWidth: 18 }}>{num}.</span>
        <span>{inlineMd(t.replace(/^\d+\.\s/, ""), `ol${i}`)}</span></div>);
    } else if (/^[-*]\s/.test(t)) {
      flush();
      out.push(<div key={`li${i}`} style={{ display: "flex", gap: 10,
        margin: "3px 0", fontFamily: SERIF, fontSize: 15, color: "#26333F", lineHeight: 1.65 }}>
        <span style={{ color: "#1A6FA3" }}>•</span>
        <span>{inlineMd(t.replace(/^[-*]\s/, ""), `li${i}`)}</span></div>);
    } else if (/^(-{3,}|\*{3,}|_{3,})$/.test(t)) {
      flush();
      out.push(<hr key={`hr${i}`} style={{ border: "none",
        borderTop: "1px solid #DDE4EB", margin: "20px 0" }} />);
    } else if (/^\*[^*].*\*$/.test(t) && !t.includes(" ** ")) {
      flush();
      out.push(<div key={`em${i}`} style={{ fontStyle: "italic", color: "#7B90A0",
        fontSize: 13, fontFamily: SERIF, margin: "0 0 14px" }}>{t.slice(1, -1)}</div>);
    } else if (/^!\[.*\]\(.+\)/.test(t)) {
      flush();
      const m = t.match(/^!\[([^\]]*)\]\(([^)]+)\)/);
      if (m) {
        out.push(
          <div key={`img${i}`} style={{ margin: "16px 0", borderRadius: 8, overflow: "hidden",
            boxShadow: "0 2px 10px rgba(10,37,64,0.08)" }}>
            <img src={m[2]} alt={m[1]}
              style={{ width: "100%", maxHeight: 420, objectFit: "cover", display: "block" }}
              onError={e => { e.currentTarget.parentElement.style.display = "none"; }} />
          </div>
        );
      }
    } else {
      para.push(t);
    }
    i++;
  }
  flush();
  return out;
}

function ReviewViewer({ itemId, title, onClose, editState, onEdit, readOnly = false }) {
  const [state, setState] = useState({ loading: true, ext: "", content: "", html: "", error: "", embedUrl: "" });
  const [instruction, setInstruction] = useState("");
  // Edit lifecycle is owned by the parent (ReviewView) so it survives closing the
  // modal. We derive the in-flight flag and status message from the parent's state.
  const editing = editState?.status === "editing";
  const editMsg = editState?.msg || "";

  const loadContent = async (signal) => {
    setState({ loading: true, ext: "", content: "", html: "", error: "" });
    try {
      const r = await fetch(`${API}/api/review/${itemId}/content`, { headers: authHdr() });
      if (!r.ok) throw (await r.json()).error || "Not found";
      const d = await r.json();
      if (signal?.aborted) return;
      if (d.ext === "md" || d.ext === "txt") {
        setState({ loading: false, ext: d.ext, content: d.content || "", html: "", error: "", embedUrl: "" });
      } else if (d.ext === "docx" || d.ext === "pptx" || d.ext === "pdf") {
        const gv = await fetch(`${API}/api/review/${itemId}/google-view`, { headers: authHdr() }).then(r => r.json());
        if (signal?.aborted) return;
        const url = gv.url || `${API}/api/review/${itemId}/serve`;
        setState({ loading: false, ext: d.ext, content: "", html: "", error: "", embedUrl: url });
      } else {
        setState({ loading: false, ext: d.ext, content: "", html: "", error: "", embedUrl: "" });
      }
    } catch (err) {
      if (!signal?.aborted) setState({ loading: false, ext: "", content: "", html: "",
        error: typeof err === "string" ? err : "Could not open file" });
    }
  };

  useEffect(() => {
    const ctrl = new AbortController();
    loadContent(ctrl.signal);
    return () => ctrl.abort();
  }, [itemId]);

  // When an edit owned by the parent finishes while this viewer is open, fold the
  // revised content into the view. Keyed on the completion timestamp so it applies
  // exactly once per edit (and not again on unrelated re-renders).
  const lastAppliedAt = useRef(0);
  useEffect(() => {
    if (editState?.status === "done" && editState.at && editState.at !== lastAppliedAt.current) {
      lastAppliedAt.current = editState.at;
      setState({ loading: false, ext: editState.ext || "md",
        content: editState.content || "", html: "", error: "" });
    }
  }, [editState]);

  const applyEdit = () => {
    if (!instruction.trim() || editing) return;
    const instr = instruction.trim();
    setInstruction("");
    // Fire-and-forget: the parent tracks status, so progress persists even if the
    // user closes this modal before the revision returns.
    onEdit(instr);
  };

  const serveUrl = `${API}/api/review/${itemId}/serve`;
  const editable = !readOnly && (state.ext === "md" || state.ext === "txt");
  return (
    <div onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      style={{ position: "fixed", inset: 0, background: "rgba(10,37,64,0.45)",
        zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#fff", borderRadius: 20, width: "82vw", maxWidth: 900,
        height: "90vh", display: "flex", flexDirection: "column", overflow: "hidden",
        boxShadow: "0 8px 40px rgba(10,37,64,0.3)" }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "12px 20px", borderBottom: "1px solid #DDE4EB", flexShrink: 0 }}>
          <span style={{ fontFamily: "Inter,sans-serif", fontWeight: 700, fontSize: 14,
            color: "#0A2540", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{title}</span>
          <div style={{ display: "flex", gap: 8 }}>
            <a href={serveUrl} target="_blank" rel="noreferrer"
              style={{ padding: "5px 12px", background: "#0A2540", color: "#fff", borderRadius: 5,
                fontFamily: "Inter,sans-serif", fontSize: 12, fontWeight: 600, textDecoration: "none" }}>
              Download
            </a>
            <button onClick={onClose} style={{ padding: "5px 10px", background: "transparent",
              border: "1px solid #DDE4EB", borderRadius: 5, cursor: "pointer", fontSize: 14, color: "#5A5650" }}>
              ✕
            </button>
          </div>
        </div>
        {/* Body */}
        <div style={{ flex: 1, overflow: "auto", padding: "32px 48px",
          fontFamily: "Inter,sans-serif", background: "#FCFDFE", position: "relative" }}>
          {editing && (
            <div style={{ position: "absolute", inset: 0, background: "rgba(252,253,254,0.78)",
              display: "flex", flexDirection: "column", gap: 6, alignItems: "center",
              justifyContent: "center", zIndex: 5, fontFamily: "Inter,sans-serif" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8,
                fontSize: 13, color: "#1A6FA3", fontWeight: 600 }}>
                <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#1A6FA3",
                  animation: "revPulse 1s ease-in-out infinite" }} />
                Revising document…
              </div>
              <div style={{ fontSize: 11, color: "#7B90A0" }}>
                You can close this preview — progress continues in the Review Queue.
              </div>
            </div>
          )}
          {state.loading && <div style={{ color: "#7B90A0", fontSize: 13 }}>Loading…</div>}
          {state.error && <div style={{ color: "#C0392B", fontSize: 13 }}>{state.error}</div>}
          {!state.loading && !state.error && editable && (
            <div style={{ maxWidth: 720, margin: "0 auto" }}>{renderMarkdown(state.content)}</div>
          )}
          {!state.loading && state.embedUrl && (
            <iframe src={state.embedUrl} title={title}
              style={{ width: "100%", height: "100%", border: "none" }}
              allow="autoplay" />
          )}
        </div>
        {/* Edit-with-prompt footer (markdown/text only) */}
        {editable && (
          <div style={{ flexShrink: 0, borderTop: "1px solid #DDE4EB",
            padding: "12px 20px", background: "#F8FAFC" }}>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: "Inter,sans-serif", fontSize: 10, fontWeight: 700,
                  letterSpacing: "0.08em", textTransform: "uppercase", color: "#7B90A0", marginBottom: 4 }}>
                  Edit with a prompt
                </div>
                <textarea
                  value={instruction}
                  onChange={e => setInstruction(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); applyEdit(); } }}
                  placeholder="e.g. Tighten the opening, add a 21 CFR citation in section 2, cut the conclusion… (Ctrl+Enter)"
                  rows={2}
                  style={{ width: "100%", boxSizing: "border-box", resize: "vertical",
                    padding: "8px 10px", border: "1px solid #DDE4EB", borderRadius: 6,
                    fontFamily: "Inter,sans-serif", fontSize: 12.5, color: "#26333F",
                    background: "#fff", outline: "none", lineHeight: 1.5 }}
                />
              </div>
              <button onClick={applyEdit} disabled={editing || !instruction.trim()}
                style={{ padding: "9px 18px", background: editing || !instruction.trim() ? "#9AAAB8" : "#1A6FA3",
                  color: "#fff", border: "none", borderRadius: 6,
                  cursor: editing || !instruction.trim() ? "not-allowed" : "pointer",
                  fontFamily: "Inter,sans-serif", fontSize: 12, fontWeight: 700, whiteSpace: "nowrap" }}>
                {editing ? "Revising…" : "Apply Edit"}
              </button>
            </div>
            {editMsg && (
              <div style={{ marginTop: 6, fontFamily: "Inter,sans-serif", fontSize: 11,
                color: editMsg.startsWith("✓") ? "#1F7A6D" : "#C0392B" }}>{editMsg}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const TYPE_COLOR = {
  article: "#1A6FA3",
  brief:   "#1F7A6D",
  report:  "#C4922A",
  lesson:  "#7B3FA6",
};

const TYPE_LABEL = {
  article: "Article",
  brief:   "Coaching Brief",
  report:  "Report",
  lesson:  "ISO Lesson",
};

const AGENT_LABEL = {
  coaching_brief:  "Coaching Agent",
  coaching_agent:  "Coaching Agent",
  content_agent:   "Content Agent",
  iso_agent:       "ISO Agent",
  consulting_agent:"Consulting Agent",
  rag_agent:       "Knowledge Agent",
  fda_agent:       "FDA Monitor",
};

function friendlyDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso.slice(0, 16).replace("T", " ");
  const now  = new Date();
  const diff = (now - d) / 1000;   // seconds
  if (diff < 60)              return "Just now";
  if (diff < 3600)            return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400)           return `Today at ${d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
  if (diff < 172800)          return `Yesterday at ${d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
  return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
}

export default function ReviewView({ reviewRefreshToken = 0 }) {
  const [items,  setItems]  = useState([]);
  const [stats,  setStats]  = useState({});
  const [notes,  setNotes]  = useState({});
  const [acting, setActing] = useState({});
  const [viewing, setViewing] = useState(null);   // {id, title, readOnly} of item open in viewer
  // In-flight / recently-finished edits, keyed by item id. Lives here (not in the
  // modal) so a revision keeps showing progress in the queue after the preview closes.
  const [edits, setEdits] = useState({});          // id -> { status, msg, content, ext, at }

  const [tab,       setTab]       = useState("pending");  // "pending" | "approved" | "rejected"
  const [histItems, setHistItems] = useState([]);
  const [reopening, setReopening] = useState({});         // id -> true while in-flight
  const [approvedDocs,    setApprovedDocs]    = useState([]);
  const [viewingApproved, setViewingApproved] = useState(null);

  const load = () => {
    fetch(`${API}/api/review/pending`, { headers: authHdr() }).then(r => r.json())
      .then(d => { setItems(d.items || []); setStats(d.stats || {}); }).catch(() => {});
  };

  const loadHistory = () => {
    fetch(`${API}/api/review/history`, { headers: authHdr() }).then(r => r.json())
      .then(d => setHistItems(d.items || [])).catch(() => {});
  };

  useEffect(() => { load(); }, []);
  const loadApproved = () => {
    fetch(`${API}/api/documents`, { headers: authHdr() }).then(r => r.json())
      .then(d => setApprovedDocs(d.documents || [])).catch(() => {});
  };

  const openDoc = (filename, folder) => {
    fetch(`${API}/api/documents/open/${encodeURIComponent(filename)}?folder=${folder || "documents"}`, { headers: authHdr() }).catch(() => {});
  };

  useEffect(() => {
    if (tab === "rejected") loadHistory();
    if (tab === "approved") loadApproved();
  }, [tab]);
  // Reload queue whenever a new agent delivers review items (token increments on agent_done).
  useEffect(() => { if (reviewRefreshToken > 0) load(); }, [reviewRefreshToken]);

  const runEdit = async (id, instruction) => {
    setEdits(p => ({ ...p, [id]: { status: "editing", msg: "" } }));
    try {
      const r = await fetch(`${API}/api/review/${id}/edit`, {
        method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
        body: JSON.stringify({ instruction }),
      });
      const d = await r.json();
      if (!r.ok) throw d.error || "Edit failed";
      setEdits(p => ({ ...p, [id]: { status: "done", msg: "✓ Document revised and saved.",
        content: d.content || "", ext: d.ext || "md", at: Date.now() } }));
      load();   // title/content may have changed
      setTimeout(() => setEdits(p => p[id]?.status === "done"
        ? (({ [id]: _drop, ...rest }) => rest)(p) : p), 8000);
    } catch (err) {
      setEdits(p => ({ ...p, [id]: { status: "error",
        msg: "✕ " + (typeof err === "string" ? err : "Edit failed") } }));
    }
  };

  const act = async (id, action) => {
    setActing(p => ({ ...p, [id]: true }));
    try {
      await fetch(`${API}/api/review/${id}/${action}`, {
        method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
        body: JSON.stringify({ notes: notes[id] || "" }),
      });
    } finally {
      setActing(p => ({ ...p, [id]: false }));
      load();
    }
  };

  const reopen = async (id) => {
    setReopening(p => ({ ...p, [id]: true }));
    try {
      await fetch(`${API}/api/review/${id}/reopen`, { method: "POST", headers: authHdr() });
    } finally {
      setReopening(p => ({ ...p, [id]: false }));
      load();
      loadHistory();
    }
  };

  const C = { navy:"#0A2540", ocean:"#1A6FA3", teal:"#1F7A6D", red:"#C0392B",
    gold:"#C4922A", fog:"#7B90A0", mist:"#DDE4EB", pearl:"#FFFFFF", cloud:"#F8FAFC" };

  return (
    <div style={{ maxWidth: 780 }}>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
        <div>
          <h2 style={{ fontSize:"1.15rem", fontWeight:700, color:C.navy, margin:0 }}>
            Document Queue
          </h2>
          <p style={{ fontFamily:"Inter,sans-serif", fontSize:"0.78rem", color:C.fog, margin:"4px 0 0" }}>
            Review pending outputs and browse approved and rejected documents.
          </p>
        </div>
        <div style={{ display:"flex", gap:8, fontFamily:"Inter,sans-serif" }}>
          {[
            { key:"pending",  label:"Awaiting",  col:"#C4922A", bg:"#FDF6EC" },
            { key:"approved", label:"Approved",  col:"#1F7A6D", bg:"#EDF7F4" },
            { key:"rejected", label:"Rejected",  col:"#C0392B", bg:"#FBEAEA" },
          ].map(({ key, label, col, bg }) => (
            <div key={key} style={{ textAlign:"center", background:bg, borderRadius:8,
              padding:"8px 14px", minWidth:60 }}>
              <div style={{ fontSize:20, fontWeight:700, color:col, lineHeight:1.1 }}>{stats[key]||0}</div>
              <div style={{ fontSize:10, color:col, opacity:0.8, marginTop:2 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display:"flex", gap:0, marginBottom:20, borderBottom:`1px solid ${C.mist}` }}>
        {[["pending","Pending"], ["approved","Approved"], ["rejected","Rejected"]].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{
            padding:"7px 20px", background:"transparent", border:"none",
            borderBottom: tab === key ? `2px solid ${C.ocean}` : "2px solid transparent",
            fontFamily:"Inter,sans-serif", fontSize:12.5, fontWeight: tab === key ? 700 : 500,
            color: tab === key ? C.ocean : C.fog,
            cursor:"pointer", marginBottom:-1, transition:"color 0.15s",
          }}>{label}{key === "pending" && (stats.pending||0) > 0 &&
            <span style={{ marginLeft:6, background:C.gold, color:"#fff", fontSize:9,
              fontWeight:700, padding:"1px 6px", borderRadius:8 }}>{stats.pending}</span>}
          </button>
        ))}
      </div>

      {/* ── Pending Queue ── */}
      {tab === "pending" && (items.length === 0 ? (
        <div style={{ padding:"52px 0", textAlign:"center",
          border:`1px dashed ${C.mist}`, borderRadius:10,
          fontFamily:"Inter,sans-serif", color:C.fog }}>
          <div style={{ fontSize:32, marginBottom:10 }}>✓</div>
          <div style={{ fontSize:14, fontWeight:600, color:C.navy, marginBottom:4 }}>All caught up</div>
          <div style={{ fontSize:12 }}>No documents are waiting for your review.</div>
        </div>
      ) : items.map(item => {
        const typeColor = TYPE_COLOR[item.item_type] || C.fog;
        const typeLabel = TYPE_LABEL[item.item_type] || item.item_type;
        const agentLabel = AGENT_LABEL[item.agent] || item.agent;
        const whenLabel  = friendlyDate(item.timestamp);
        return (
          <div key={item.id} style={{
            background: C.pearl, border:`1px solid ${C.mist}`,
            borderLeft: `3px solid ${typeColor}`,
            borderRadius:"0 10px 10px 0", padding:"18px 22px",
            marginBottom:12,
          }}>
            <div style={{ display:"flex", justifyContent:"space-between",
              alignItems:"flex-start", gap:12 }}>
              <div style={{ flex:1 }}>
                {/* Type badge + meta */}
                <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:8, flexWrap:"wrap" }}>
                  <span style={{
                    fontFamily:"Inter,sans-serif", fontSize:10, fontWeight:600,
                    background: typeColor + "18", color: typeColor,
                    padding:"3px 9px", borderRadius:5,
                  }}>{typeLabel}</span>
                  <span style={{ fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog }}>
                    {agentLabel}
                  </span>
                  <span style={{ fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog, opacity:0.7 }}>
                    · Submitted {whenLabel}
                  </span>
                  {edits[item.id]?.status === "editing" && (
                    <span style={{ display:"inline-flex", alignItems:"center", gap:5,
                      fontFamily:"Inter,sans-serif", fontSize:10, fontWeight:600,
                      background:C.ocean+"18", color:C.ocean, padding:"3px 9px", borderRadius:5 }}>
                      <span style={{ width:6, height:6, borderRadius:"50%", background:C.ocean,
                        animation:"revPulse 1s ease-in-out infinite" }} />
                      Revising…
                    </span>
                  )}
                  {edits[item.id]?.status === "done" && (
                    <span style={{ fontFamily:"Inter,sans-serif", fontSize:10, fontWeight:600,
                      background:C.teal+"18", color:C.teal, padding:"3px 9px", borderRadius:5 }}>
                      ✓ Revised
                    </span>
                  )}
                  {edits[item.id]?.status === "error" && (
                    <span title={edits[item.id]?.msg} style={{ fontFamily:"Inter,sans-serif",
                      fontSize:10, fontWeight:600,
                      background:C.red+"18", color:C.red, padding:"3px 9px", borderRadius:5 }}>
                      Edit failed
                    </span>
                  )}
                </div>
                <div
                  onClick={() => setViewing({ id: item.id, title: item.title })}
                  title="Click to read"
                  style={{ fontFamily:"Inter,sans-serif", fontWeight:600,
                  fontSize:15, color:C.ocean, lineHeight:1.4, cursor:"pointer",
                  textDecoration:"underline", textDecorationColor:C.mist,
                  textUnderlineOffset:3 }}>
                  {item.title}
                </div>
              </div>
            </div>

            {/* Notes + actions */}
            {(() => { const busy = acting[item.id] || edits[item.id]?.status === "editing"; return (
            <div style={{ marginTop:14, borderTop:`1px solid ${C.mist}`, paddingTop:12,
              display:"flex", gap:8, alignItems:"center" }}>
              <input
                value={notes[item.id] || ""}
                onChange={e => setNotes(p => ({ ...p, [item.id]: e.target.value }))}
                placeholder="Add a review note (optional)…"
                style={{
                  flex:1, padding:"7px 12px", border:`1px solid ${C.mist}`,
                  borderRadius:7, fontFamily:"Inter,sans-serif", fontSize:12.5,
                  color:"#3C5470", background:C.cloud, outline:"none",
                }}
              />
              <button
                onClick={() => act(item.id, "approve")}
                disabled={busy}
                title={edits[item.id]?.status === "editing" ? "Wait for the revision to finish" : ""}
                style={{
                  padding:"8px 20px", background: busy ? C.fog : C.teal,
                  color:"#fff", border:"none", borderRadius:7, cursor: busy ? "not-allowed" : "pointer",
                  fontFamily:"Inter,sans-serif", fontSize:12.5, fontWeight:700, whiteSpace:"nowrap",
                  boxShadow: busy ? "none" : "0 1px 4px rgba(31,122,109,0.25)",
                }}>
                ✓ Approve
              </button>
              <button
                onClick={() => act(item.id, "reject")}
                disabled={busy}
                style={{
                  padding:"8px 16px", background:"transparent", color:C.red,
                  border:`1px solid ${C.red}55`, borderRadius:7,
                  cursor: busy ? "not-allowed" : "pointer",
                  fontFamily:"Inter,sans-serif", fontSize:12.5, fontWeight:600,
                }}>
                Reject
              </button>
            </div>
          ); })()}
          </div>
        );
      }))}

      {/* -- Approved -- */}
      {tab === "approved" && (approvedDocs.length === 0 ? (
        <div style={{ padding:"52px 0", textAlign:"center",
          border:`1px dashed ${C.mist}`, borderRadius:10,
          fontFamily:"Inter,sans-serif", color:C.fog }}>
          <div style={{ fontSize:14, fontWeight:600, color:C.navy, marginBottom:4 }}>No approved documents</div>
          <div style={{ fontSize:12 }}>Approved outputs will appear here once you review pending items.</div>
        </div>
      ) : approvedDocs.map(doc => (
        <div key={doc.filename} style={{
          background: C.pearl, border:`1px solid ${C.mist}`,
          borderLeft:`3px solid ${C.teal}`,
          borderRadius:"0 10px 10px 0", padding:"14px 22px",
          marginBottom:10, display:"flex", justifyContent:"space-between", alignItems:"center", gap:12,
        }}>
          <div style={{ flex:1 }}>
            <div style={{ fontFamily:"Inter,sans-serif", fontWeight:600, fontSize:14, color:C.navy, marginBottom:4 }}>
              {doc.title || doc.filename}
            </div>
            <div style={{ fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog }}>
              {doc.filename}
            </div>
          </div>
          <div style={{ display:"flex", gap:8, flexShrink:0 }}>
            <button
              onClick={() => setViewingApproved({ folder: doc.folder || "documents", filename: doc.filename })}
              style={{
                padding:"6px 14px", background:"transparent",
                border:`1px solid ${C.ocean}55`, borderRadius:6,
                color:C.ocean, cursor:"pointer",
                fontFamily:"Inter,sans-serif", fontSize:11, fontWeight:600,
              }}>
              View
            </button>
            {doc.filename.endsWith(".docx") && (
              <button
                onClick={() => openDoc(doc.filename, doc.folder || "documents")}
                style={{
                  padding:"6px 14px", background:"transparent",
                  border:`1px solid ${C.fog}44`, borderRadius:6,
                  color:C.fog, cursor:"pointer",
                  fontFamily:"Inter,sans-serif", fontSize:11, fontWeight:600,
                }}>
                Open
              </button>
            )}
          </div>
        </div>
      )))}

      {/* -- Rejected -- */}
      {tab === "rejected" && (() => {
        const rejected = histItems.filter(i => i.status === "rejected");
        return rejected.length === 0 ? (
          <div style={{ padding:"52px 0", textAlign:"center",
            border:`1px dashed ${C.mist}`, borderRadius:10,
            fontFamily:"Inter,sans-serif", color:C.fog }}>
            <div style={{ fontSize:14, fontWeight:600, color:C.navy, marginBottom:4 }}>No rejected documents</div>
            <div style={{ fontSize:12 }}>Rejected outputs will appear here.</div>
          </div>
        ) : rejected.map(item => {
          const typeColor  = TYPE_COLOR[item.item_type] || C.fog;
          const typeLabel  = TYPE_LABEL[item.item_type] || item.item_type;
          const agentLabel = AGENT_LABEL[item.agent] || item.agent;
          const whenLabel  = friendlyDate(item.reviewed_at || item.timestamp);
          return (
            <div key={item.id} style={{
              background: C.pearl, border:`1px solid ${C.mist}`,
              borderLeft:`3px solid ${C.red}`,
              borderRadius:"0 10px 10px 0", padding:"16px 22px",
              marginBottom:10, opacity: reopening[item.id] ? 0.5 : 1,
              transition:"opacity 0.2s",
            }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12 }}>
                <div style={{ flex:1 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:8, flexWrap:"wrap" }}>
                    <span style={{ fontFamily:"Inter,sans-serif", fontSize:10, fontWeight:600,
                      background:C.red+"18", color:C.red,
                      padding:"3px 9px", borderRadius:5 }}>Rejected</span>
                    <span style={{ fontFamily:"Inter,sans-serif", fontSize:10, fontWeight:600,
                      background: typeColor + "18", color: typeColor,
                      padding:"3px 9px", borderRadius:5 }}>{typeLabel}</span>
                    <span style={{ fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog }}>
                      {agentLabel}
                    </span>
                    <span style={{ fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog, opacity:0.7 }}>
                      Reviewed {whenLabel}
                    </span>
                  </div>
                  <div
                    onClick={() => setViewing({ id: item.id, title: item.title, readOnly: true })}
                    title="Click to read"
                    style={{ fontFamily:"Inter,sans-serif", fontWeight:600, fontSize:15,
                      color:C.ocean, lineHeight:1.4, cursor:"pointer",
                      textDecoration:"underline", textDecorationColor:C.mist, textUnderlineOffset:3 }}>
                    {item.title}
                  </div>
                  {item.notes && (
                    <div style={{ fontFamily:"Inter,sans-serif", fontSize:11.5, color:C.fog,
                      marginTop:6, fontStyle:"italic", borderLeft:`2px solid ${C.mist}`,
                      paddingLeft:10 }}>
                      {item.notes}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => reopen(item.id)}
                  disabled={!!reopening[item.id]}
                  title="Move back to pending queue"
                  style={{
                    flexShrink:0, padding:"6px 14px", background:"transparent",
                    border:`1px solid ${C.ocean}55`, borderRadius:6,
                    color:C.ocean, cursor: reopening[item.id] ? "not-allowed" : "pointer",
                    fontFamily:"Inter,sans-serif", fontSize:11, fontWeight:600, whiteSpace:"nowrap",
                  }}>
                  {reopening[item.id] ? "Moving..." : "Reopen"}
                </button>
              </div>
            </div>
          );
        });
      })()}

            {/* Refresh */}
      <div style={{ textAlign:"right", marginTop:16 }}>
        <button onClick={tab==="pending" ? load : tab==="approved" ? loadApproved : loadHistory} style={{
          padding:"5px 12px", background:"transparent",
          border:`1px solid ${C.mist}`, borderRadius:6,
          fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog, cursor:"pointer",
        }}>Refresh</button>
      </div>

      {viewingApproved && (
        <FileViewer folder={viewingApproved.folder} filename={viewingApproved.filename}
          onClose={() => setViewingApproved(null)} />
      )}

      {viewing && (
        <ReviewViewer itemId={viewing.id} title={viewing.title} onClose={() => setViewing(null)}
          readOnly={!!viewing.readOnly}
          editState={edits[viewing.id]} onEdit={instr => runEdit(viewing.id, instr)} />
      )}

      <style>{`@keyframes revPulse { 0%,100%{opacity:1} 50%{opacity:0.25} }`}</style>
    </div>
  );
}
