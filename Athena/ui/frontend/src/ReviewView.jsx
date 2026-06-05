/**
 * Human Review Queue — Phase 1A Gate
 * Every client-facing output (briefs, articles) lands here before Steven approves it.
 */
import { useEffect, useState } from "react";
import mammoth from "mammoth";

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
    } else {
      para.push(t);
    }
    i++;
  }
  flush();
  return out;
}

function ReviewViewer({ itemId, title, onClose }) {
  const [state, setState] = useState({ loading: true, ext: "", content: "", html: "", error: "" });
  const [instruction, setInstruction] = useState("");
  const [editing, setEditing] = useState(false);
  const [editMsg, setEditMsg] = useState("");

  const loadContent = async (signal) => {
    setState({ loading: true, ext: "", content: "", html: "", error: "" });
    try {
      const r = await fetch(`${API}/api/review/${itemId}/content`);
      if (!r.ok) throw (await r.json()).error || "Not found";
      const d = await r.json();
      if (signal?.aborted) return;
      if (d.ext === "md" || d.ext === "txt") {
        setState({ loading: false, ext: d.ext, content: d.content || "", html: "", error: "" });
      } else if (d.ext === "docx") {
        const buf = await fetch(`${API}/api/review/${itemId}/serve`).then(r => r.arrayBuffer());
        const res = await mammoth.convertToHtml({ arrayBuffer: buf });
        if (!signal?.aborted) setState({ loading: false, ext: "docx", content: "", html: res.value, error: "" });
      } else {
        setState({ loading: false, ext: d.ext, content: "", html: "", error: "" });
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

  const applyEdit = async () => {
    if (!instruction.trim() || editing) return;
    setEditing(true); setEditMsg("");
    try {
      const r = await fetch(`${API}/api/review/${itemId}/edit`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction }),
      });
      const d = await r.json();
      if (!r.ok) throw d.error || "Edit failed";
      setState({ loading: false, ext: d.ext, content: d.content || "", html: "", error: "" });
      setInstruction(""); setEditMsg("✓ Document revised and saved.");
    } catch (err) {
      setEditMsg("✕ " + (typeof err === "string" ? err : "Edit failed"));
    } finally {
      setEditing(false);
    }
  };

  const serveUrl = `${API}/api/review/${itemId}/serve`;
  const editable = state.ext === "md" || state.ext === "txt";
  return (
    <div onClick={e => { if (e.target === e.currentTarget && !editing) onClose(); }}
      style={{ position: "fixed", inset: 0, background: "rgba(10,37,64,0.45)",
        zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#fff", borderRadius: 10, width: "82vw", maxWidth: 900,
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
            <div style={{ position: "absolute", inset: 0, background: "rgba(252,253,254,0.75)",
              display: "flex", alignItems: "center", justifyContent: "center", zIndex: 5,
              fontFamily: "Inter,sans-serif", fontSize: 13, color: "#1A6FA3", fontWeight: 600 }}>
              Revising document…
            </div>
          )}
          {state.loading && <div style={{ color: "#7B90A0", fontSize: 13 }}>Loading…</div>}
          {state.error && <div style={{ color: "#C0392B", fontSize: 13 }}>{state.error}</div>}
          {!state.loading && !state.error && editable && (
            <div style={{ maxWidth: 720, margin: "0 auto" }}>{renderMarkdown(state.content)}</div>
          )}
          {!state.loading && state.ext === "docx" && (
            <div style={{ maxWidth: 760, margin: "0 auto" }}
              dangerouslySetInnerHTML={{ __html: state.html }} />
          )}
          {!state.loading && state.ext === "pdf" && (
            <iframe src={serveUrl} title={title}
              style={{ width: "100%", height: "100%", border: "none" }} />
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

export default function ReviewView() {
  const [items,  setItems]  = useState([]);
  const [stats,  setStats]  = useState({});
  const [notes,  setNotes]  = useState({});
  const [acting, setActing] = useState({});
  const [viewing, setViewing] = useState(null);   // {id, title} of item open in viewer

  const load = () => {
    fetch(`${API}/api/review/pending`).then(r => r.json())
      .then(d => { setItems(d.items || []); setStats(d.stats || {}); }).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const act = async (id, action) => {
    setActing(p => ({ ...p, [id]: true }));
    await fetch(`${API}/api/review/${id}/${action}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: notes[id] || "" }),
    });
    setActing(p => ({ ...p, [id]: false }));
    load();
  };

  const C = { navy:"#0A2540", ocean:"#1A6FA3", teal:"#1F7A6D", red:"#C0392B",
    gold:"#C4922A", fog:"#7B90A0", mist:"#DDE4EB", pearl:"#FFFFFF", cloud:"#F8FAFC" };

  return (
    <div style={{ maxWidth: 780 }}>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:20 }}>
        <div>
          <h2 style={{ fontSize:"1.15rem", fontWeight:700, color:C.navy, margin:0 }}>
            Review Queue
          </h2>
          <p style={{ fontFamily:"Inter,sans-serif", fontSize:"0.78rem", color:C.fog, margin:"4px 0 0" }}>
            All client-facing outputs require your approval before they're considered final.
          </p>
        </div>
        <div style={{ display:"flex", gap:12, fontFamily:"Inter,sans-serif", fontSize:12 }}>
          {[["pending","#C4922A"],["approved","#1F7A6D"],["rejected","#C0392B"]].map(([k,col])=>(
            <div key={k} style={{ textAlign:"center" }}>
              <div style={{ fontSize:22, fontWeight:700, color:col }}>{stats[k]||0}</div>
              <div style={{ fontSize:9, fontWeight:700, textTransform:"uppercase",
                letterSpacing:"0.1em", color:C.fog }}>{k}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Items */}
      {items.length === 0 ? (
        <div style={{ padding:"48px 0", textAlign:"center",
          border:`1px dashed ${C.mist}`, borderRadius:10,
          fontFamily:"Inter,sans-serif", fontSize:13, color:C.fog }}>
          <div style={{ fontSize:28, marginBottom:8 }}>✓</div>
          Queue is clear. No pending reviews.
        </div>
      ) : items.map(item => {
        const typeColor = TYPE_COLOR[item.item_type] || C.fog;
        const typeLabel = TYPE_LABEL[item.item_type] || item.item_type;
        const date = item.timestamp?.slice(0, 10);
        const time = item.timestamp?.slice(11, 16);
        return (
          <div key={item.id} style={{
            background: C.pearl, border:`1px solid ${C.mist}`,
            borderLeft: `3px solid ${typeColor}`,
            borderRadius:"0 10px 10px 0", padding:"16px 20px",
            marginBottom:12,
          }}>
            <div style={{ display:"flex", justifyContent:"space-between",
              alignItems:"flex-start", gap:12 }}>
              <div style={{ flex:1 }}>
                {/* Type badge + title */}
                <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:6 }}>
                  <span style={{
                    fontFamily:"Inter,sans-serif", fontSize:9, fontWeight:700,
                    letterSpacing:"0.1em", textTransform:"uppercase",
                    background: typeColor + "18", color: typeColor,
                    padding:"2px 8px", borderRadius:4,
                  }}>{typeLabel}</span>
                  <span style={{ fontFamily:"Inter,sans-serif", fontSize:9,
                    color:C.fog }}>{item.agent}</span>
                  <span style={{ fontFamily:"Inter,sans-serif", fontSize:9,
                    color:C.fog }}>{date} {time}</span>
                </div>
                <div
                  onClick={() => setViewing({ id: item.id, title: item.title })}
                  title="Open to read"
                  style={{ fontFamily:"Inter,sans-serif", fontWeight:600,
                  fontSize:14, color:C.ocean, lineHeight:1.4, cursor:"pointer",
                  textDecoration:"underline", textDecorationColor:C.mist,
                  textUnderlineOffset:3 }}>
                  {item.title}
                </div>
                {item.file_path && (
                  <div style={{ fontFamily:"monospace", fontSize:10, color:C.fog, marginTop:4 }}>
                    {item.file_path.split("\\").slice(-2).join("\\")}
                  </div>
                )}
              </div>
            </div>

            {/* Notes + actions */}
            <div style={{ marginTop:12, display:"flex", gap:8, alignItems:"flex-end" }}>
              <input
                value={notes[item.id] || ""}
                onChange={e => setNotes(p => ({ ...p, [item.id]: e.target.value }))}
                placeholder="Optional review notes…"
                style={{
                  flex:1, padding:"6px 10px", border:`1px solid ${C.mist}`,
                  borderRadius:6, fontFamily:"Inter,sans-serif", fontSize:12,
                  color:"#3C5470", background:C.cloud, outline:"none",
                }}
              />
              <button
                onClick={() => act(item.id, "approve")}
                disabled={acting[item.id]}
                style={{
                  padding:"7px 18px", background: acting[item.id] ? C.fog : C.teal,
                  color:"#fff", border:"none", borderRadius:6, cursor: acting[item.id] ? "not-allowed" : "pointer",
                  fontFamily:"Inter,sans-serif", fontSize:12, fontWeight:700, whiteSpace:"nowrap",
                }}>
                ✓ Approve
              </button>
              <button
                onClick={() => act(item.id, "reject")}
                disabled={acting[item.id]}
                style={{
                  padding:"7px 14px", background:"transparent", color:C.red,
                  border:`1px solid ${C.red}55`, borderRadius:6,
                  cursor: acting[item.id] ? "not-allowed" : "pointer",
                  fontFamily:"Inter,sans-serif", fontSize:12, fontWeight:600,
                }}>
                ✕ Reject
              </button>
            </div>
          </div>
        );
      })}

      {/* Refresh */}
      <div style={{ textAlign:"right", marginTop:16 }}>
        <button onClick={load} style={{
          padding:"5px 12px", background:"transparent",
          border:`1px solid ${C.mist}`, borderRadius:6,
          fontFamily:"Inter,sans-serif", fontSize:11, color:C.fog, cursor:"pointer",
        }}>Refresh</button>
      </div>

      {viewing && (
        <ReviewViewer itemId={viewing.id} title={viewing.title} onClose={() => setViewing(null)} />
      )}
    </div>
  );
}
