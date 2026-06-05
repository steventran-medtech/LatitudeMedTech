/**
 * Human Review Queue — Phase 1A Gate
 * Every client-facing output (briefs, articles) lands here before Steven approves it.
 */
import { useEffect, useState } from "react";

const API = "http://localhost:8000";

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
                <div style={{ fontFamily:"Inter,sans-serif", fontWeight:600,
                  fontSize:14, color:C.navy, lineHeight:1.4 }}>
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
    </div>
  );
}
