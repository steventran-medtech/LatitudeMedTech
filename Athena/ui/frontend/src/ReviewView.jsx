/**
 * Human Review Queue — Phase 1A Gate
 * Every client-facing output (briefs, articles) lands here before Steven approves it.
 */
import { useEffect, useState } from "react";
import mammoth from "mammoth";

const API = "http://localhost:8000";

// Minimal, safe Markdown renderer for the review modal (headings, bold,
// bullets, rules, paragraphs). Avoids dangerouslySetInnerHTML on raw text.
function renderMarkdown(md) {
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const out = [];
  let para = [];
  const flush = (i) => {
    if (para.length) {
      out.push(<p key={`p${i}`} style={{ margin: "0 0 12px", lineHeight: 1.7,
        color: "#1A2A3A", fontSize: 14 }}>{inline(para.join(" "))}</p>);
      para = [];
    }
  };
  const inline = (s) => {
    // bold **x** → <strong>
    const parts = s.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((p, k) => p.startsWith("**") && p.endsWith("**")
      ? <strong key={k}>{p.slice(2, -2)}</strong> : <span key={k}>{p}</span>);
  };
  lines.forEach((raw, i) => {
    const t = raw.trim();
    if (!t) { flush(i); return; }
    if (/^#{1,6}\s/.test(t)) {
      flush(i);
      const level = t.match(/^#+/)[0].length;
      const text = t.replace(/^#+\s/, "");
      const size = level === 1 ? 20 : level === 2 ? 16 : 14;
      out.push(<div key={`h${i}`} style={{ fontWeight: 700, fontSize: size,
        color: "#0A2540", margin: "18px 0 8px" }}>{text}</div>);
    } else if (/^[-*]\s/.test(t)) {
      flush(i);
      out.push(<div key={`li${i}`} style={{ display: "flex", gap: 8,
        margin: "2px 0", fontSize: 14, color: "#1A2A3A", lineHeight: 1.6 }}>
        <span style={{ color: "#1A6FA3" }}>•</span>
        <span>{inline(t.replace(/^[-*]\s/, ""))}</span></div>);
    } else if (/^(-{3,}|\*{3,})$/.test(t)) {
      flush(i);
      out.push(<hr key={`hr${i}`} style={{ border: "none",
        borderTop: "1px solid #DDE4EB", margin: "16px 0" }} />);
    } else if (/^\*[^*].*\*$/.test(t)) {
      flush(i);
      out.push(<div key={`em${i}`} style={{ fontStyle: "italic", color: "#7B90A0",
        fontSize: 13, margin: "0 0 12px" }}>{t.slice(1, -1)}</div>);
    } else {
      para.push(t);
    }
  });
  flush("end");
  return out;
}

function ReviewViewer({ itemId, title, onClose }) {
  const [state, setState] = useState({ loading: true, ext: "", content: "", html: "", error: "" });

  useEffect(() => {
    let active = true;
    setState({ loading: true, ext: "", content: "", html: "", error: "" });
    fetch(`${API}/api/review/${itemId}/content`)
      .then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(e.error || "Not found")))
      .then(async d => {
        if (!active) return;
        if (d.ext === "md" || d.ext === "txt") {
          setState({ loading: false, ext: d.ext, content: d.content || "", html: "", error: "" });
        } else if (d.ext === "docx") {
          const buf = await fetch(`${API}/api/review/${itemId}/serve`).then(r => r.arrayBuffer());
          const res = await mammoth.convertToHtml({ arrayBuffer: buf });
          if (active) setState({ loading: false, ext: "docx", content: "", html: res.value, error: "" });
        } else {
          setState({ loading: false, ext: d.ext, content: "", html: "", error: "" });
        }
      })
      .catch(err => active && setState({ loading: false, ext: "", content: "", html: "",
        error: typeof err === "string" ? err : "Could not open file" }));
    return () => { active = false; };
  }, [itemId]);

  const serveUrl = `${API}/api/review/${itemId}/serve`;
  return (
    <div onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      style={{ position: "fixed", inset: 0, background: "rgba(10,37,64,0.45)",
        zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "#fff", borderRadius: 10, width: "82vw", maxWidth: 900,
        height: "88vh", display: "flex", flexDirection: "column", overflow: "hidden",
        boxShadow: "0 8px 40px rgba(10,37,64,0.3)" }}>
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
        <div style={{ flex: 1, overflow: "auto", padding: "28px 40px",
          fontFamily: "Inter,sans-serif", background: "#FCFDFE" }}>
          {state.loading && <div style={{ color: "#7B90A0", fontSize: 13 }}>Loading…</div>}
          {state.error && <div style={{ color: "#C0392B", fontSize: 13 }}>{state.error}</div>}
          {!state.loading && !state.error && (state.ext === "md" || state.ext === "txt") && (
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
