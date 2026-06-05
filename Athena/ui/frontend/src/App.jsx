import { useState, useEffect, useRef, useCallback } from "react";
import SettingsView from "./SettingsView.jsx";
import VoiceView from "./VoiceView.jsx";
import HRView from "./HRView.jsx";
import ISOView from "./ISOView.jsx";
import FileViewer from "./FileViewer.jsx";
import ReviewView from "./ReviewView.jsx";

const API = "http://localhost:8000";
const WS  = "ws://localhost:8000/ws";

// ── Pacific Palette — San Diego consulting brand ────────────────────────────
const C = {
  // Brand
  navy:    "#0A2540",   // Deep Pacific — headings, primary
  ocean:   "#1A6FA3",   // La Jolla Cove — interactive / links
  gold:    "#C4922A",   // Coronado sunset — accent / warnings
  teal:    "#1F7A6D",   // Torrey Pines — success
  // Surfaces
  cloud:   "#F8FAFC",   // Coastal morning — app background
  sand:    "#F2EDE6",   // La Jolla sandstone — card / input background
  pearl:   "#FFFFFF",   // White
  // Text
  ink:     "#0A2540",   // Near-black headings
  slate:   "#3C5470",   // Body text
  fog:     "#7B90A0",   // Labels / muted
  // Borders
  mist:    "#DDE4EB",   // Subtle border
  // Semantic aliases for backwards compatibility with child views
  black:   "#0A2540",
  blue:    "#1A6FA3",
  warm:    "#C4922A",
  amber:   "#C4922A",
  cream:   "#F8FAFC",
  ltgray:  "#EDF1F5",
  border:  "#DDE4EB",
  muted:   "#7B90A0",
  white:   "#FFFFFF",
  red:     "#C0392B",
  green:   "#1F7A6D",
};

const F = {
  sans: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  serif: "'Lora', Georgia, serif",
  mono: "'JetBrains Mono', 'Fira Mono', monospace",
};

const S = {
  app:{minHeight:"100vh",background:C.cloud,fontFamily:F.sans,color:C.slate},
  sidebar:{width:228,background:C.navy,display:"flex",flexDirection:"column",position:"fixed",top:0,left:0,bottom:0,zIndex:10},
  main:{marginLeft:228,minHeight:"100vh",display:"flex",flexDirection:"column"},
  header:{background:C.pearl,borderBottom:`1px solid ${C.mist}`,padding:"14px 36px",display:"flex",alignItems:"center",justifyContent:"space-between",position:"sticky",top:0,zIndex:9,boxShadow:"0 1px 3px rgba(10,37,64,0.06)"},
  content:{padding:"36px",flex:1},
  card:{background:C.pearl,border:`1px solid ${C.mist}`,borderRadius:10,padding:"22px 26px",marginBottom:20,boxShadow:"0 1px 4px rgba(10,37,64,0.04)"},
  btn:(v="primary")=>({padding:"7px 18px",borderRadius:6,border:"none",cursor:"pointer",fontFamily:F.sans,fontSize:11,fontWeight:600,letterSpacing:"0.05em",textTransform:"uppercase",background:v==="primary"?C.navy:v==="teal"?C.teal:v==="warm"?C.gold:v==="red"?C.red:v==="ocean"?C.ocean:"transparent",color:v==="ghost"?C.fog:C.pearl,border:v==="ghost"?`1px solid ${C.mist}`:"none",transition:"opacity 0.15s"}),
  label:{fontFamily:F.sans,fontSize:10,fontWeight:600,letterSpacing:"0.1em",textTransform:"uppercase",color:C.fog,marginBottom:6,display:"block"},
  h2:{fontSize:17,fontWeight:600,color:C.ink,margin:"0 0 4px",letterSpacing:"-0.01em",fontFamily:F.sans},
  stat:{fontFamily:F.sans,fontSize:28,fontWeight:700,color:C.ink,lineHeight:1},
  statLabel:{fontFamily:F.sans,fontSize:10,color:C.fog,letterSpacing:"0.08em",textTransform:"uppercase",marginTop:4},
  input:{width:"100%",padding:"9px 13px",border:`1px solid ${C.mist}`,borderRadius:7,fontFamily:F.sans,fontSize:13,background:C.pearl,color:C.slate,outline:"none",boxSizing:"border-box",transition:"border-color 0.15s"},
  textarea:{width:"100%",padding:"10px 13px",border:`1px solid ${C.mist}`,borderRadius:7,fontFamily:F.mono,fontSize:12,lineHeight:1.65,background:C.pearl,color:C.slate,outline:"none",resize:"vertical",boxSizing:"border-box"},
};

// Navigation groups
const NAV = [
  // Athena Voice is the centrepiece — first item, own group
  {id:"voice",     label:"Athena Voice",   group:"athena"},
  // Work
  {id:"briefing",  label:"Daily Briefing", group:"work"},
  {id:"content",   label:"Content",        group:"work"},
  {id:"coaching",  label:"Coaching",       group:"work"},
  {id:"iso",       label:"ISO 13485",      group:"work"},
  {id:"documents", label:"Documents",      group:"work"},
  // System
  {id:"dashboard", label:"Dashboard",      group:"system"},
  {id:"review",    label:"Review Queue",    group:"work"},
  {id:"agents",    label:"Run Agents",     group:"system"},
  {id:"hr",        label:"Workforce",      group:"system"},
  {id:"tokens",    label:"Token Usage",    group:"system"},
  {id:"settings",  label:"Settings",       group:"system"},
];

const NAV_GROUPS = [
  {key:"athena",  label:""},          // Athena Voice — no group label, stands alone
  {key:"work",    label:"Work"},
  {key:"system",  label:"System"},
];

function Sidebar({active,setActive,runningAgents,pendingReview}){
  const grouped = NAV_GROUPS.map(g=>({...g, items: NAV.filter(n=>n.group===g.key)}));
  const numRunning = runningAgents?.size || 0;
  return(
    <div style={S.sidebar}>
      {/* Wordmark */}
      <div style={{padding:"28px 22px 22px",borderBottom:"1px solid rgba(255,255,255,0.08)"}}>
        <div style={{fontFamily:F.sans,fontSize:10,letterSpacing:"0.22em",color:"rgba(255,255,255,0.45)",fontWeight:600,textTransform:"uppercase",marginBottom:6}}>Latitude MedTech</div>
        <div style={{fontFamily:F.serif,fontSize:20,color:"#FFFFFF",fontWeight:400,letterSpacing:"0.01em",lineHeight:1}}>Athena</div>
        <div style={{fontFamily:F.sans,fontSize:9,color:"rgba(255,255,255,0.35)",marginTop:5,letterSpacing:"0.06em"}}>AI Operating System · San Diego</div>
      </div>

      {/* Nav */}
      <nav style={{flex:1,padding:"16px 0",overflowY:"auto"}}>
        {grouped.map(g=>(
          <div key={g.key} style={{marginBottom:4}}>
            <div style={{fontFamily:F.sans,fontSize:8,fontWeight:700,letterSpacing:"0.16em",textTransform:"uppercase",color:"rgba(255,255,255,0.28)",padding:"10px 22px 5px"}}>{g.label}</div>
            {g.items.map(item=>{
              const isActive = active===item.id;
              const isAgents = item.id==="agents";
              const isReview = item.id==="review";
              const isVoice  = item.id==="voice";
              return(
                <button key={item.id} onClick={()=>setActive(item.id)} style={{
                  display:"flex",alignItems:"center",justifyContent:"space-between",
                  width:"100%",
                  padding: isVoice ? "13px 22px" : "9px 22px",
                  background: isVoice && isActive
                    ? "rgba(26,111,163,0.25)"
                    : isActive
                    ? "rgba(255,255,255,0.1)"
                    : isVoice ? "rgba(26,111,163,0.08)" : "transparent",
                  border:"none",
                  borderLeft: isActive
                    ? isVoice ? "2px solid #1A6FA3" : "2px solid #C4922A"
                    : "2px solid transparent",
                  cursor:"pointer",fontFamily:F.sans,
                  fontSize: isVoice ? 13 : 12,
                  color: isVoice
                    ? isActive ? "#FFFFFF" : "rgba(100,180,255,0.7)"
                    : isActive ? "#FFFFFF" : "rgba(255,255,255,0.55)",
                  fontWeight: isVoice ? 600 : isActive ? 500 : 400,
                  textAlign:"left",
                  transition:"all 0.12s",letterSpacing: isVoice ? "0.04em" : "0.01em",
                  boxShadow: isVoice && isActive ? "inset 0 0 20px rgba(26,111,163,0.15)" : "none",
                }}>
                  <span>{item.label}</span>
                  {/* Running agents badge on "Run Agents" nav item */}
                  {isAgents && numRunning>0 && (
                    <span style={{
                      background:"#1A6FA3",color:"#fff",
                      borderRadius:10,padding:"1px 6px",
                      fontSize:9,fontWeight:700,letterSpacing:"0.04em",
                      boxShadow:"0 0 6px #1A6FA366",
                      animation:"badgePulse 2s ease-in-out infinite",
                    }}>{numRunning}</span>
                  )}
                  {isReview && pendingReview>0 && (
                    <span style={{
                      background:"#C4922A",color:"#fff",
                      borderRadius:10,padding:"1px 6px",
                      fontSize:9,fontWeight:700,letterSpacing:"0.04em",
                      boxShadow:"0 0 6px #C4922A66",
                      animation:"badgePulse 2s ease-in-out infinite",
                    }}>{pendingReview}</span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div style={{padding:"14px 22px",borderTop:"1px solid rgba(255,255,255,0.08)"}}>
        <div style={{fontFamily:F.sans,fontSize:9,color:"rgba(255,255,255,0.3)",lineHeight:1.7}}>
          latitudemedtech.com<br/>
          steven.tran@latitudemedtech.com
        </div>
      </div>
      <style>{`@keyframes badgePulse{0%,100%{box-shadow:0 0 4px #1A6FA366}50%{box-shadow:0 0 10px #1A6FA3aa}}`}</style>
    </div>
  );
}

// ── McKinsey-quality Markdown renderer ────────────────────────────────────────
function renderInline(text) {
  // Bold, italic, inline code
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**"))
      return <strong key={i} style={{ color: C.ink, fontWeight: 700 }}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("*") && p.endsWith("*"))
      return <em key={i}>{p.slice(1, -1)}</em>;
    if (p.startsWith("`") && p.endsWith("`"))
      return <code key={i} style={{ background: "#F2EDE6", padding: "1px 5px", borderRadius: 3,
        fontFamily: F.mono, fontSize: "0.88em", color: C.navy }}>{p.slice(1, -1)}</code>;
    return p;
  });
}

// ── Frontmatter parser ─────────────────────────────────────────────────────
function parseFrontmatter(raw) {
  const trimmed = raw.trimStart();
  if (!trimmed.startsWith('---')) return { meta: {}, body: raw };
  const endIdx = trimmed.indexOf('\n---', 3);
  if (endIdx === -1) return { meta: {}, body: raw };
  const yamlBlock = trimmed.slice(3, endIdx).trim();
  const meta = {};
  yamlBlock.split('\n').forEach(line => {
    const col = line.indexOf(':');
    if (col > 0) {
      const k = line.slice(0, col).trim();
      const v = line.slice(col + 1).trim().replace(/^["']|["']$/g, '');
      meta[k] = v;
    }
  });
  const body = trimmed.slice(endIdx + 4).trimStart();
  return { meta, body };
}

// ── Frontmatter badge (shown above article, not in body) ──────────────────
function FrontmatterBadge({ meta }) {
  if (!meta || !Object.keys(meta).length) return null;
  const show = ['status','publication','date'].filter(k => meta[k]);
  if (!show.length) return null;
  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 18,
      paddingBottom: 14, borderBottom: `1px solid ${C.mist}`,
    }}>
      {show.map(k => (
        <span key={k} style={{
          fontFamily: F.sans, fontSize: 10, fontWeight: 600,
          letterSpacing: '0.06em', textTransform: 'uppercase',
          background: C.sand, color: C.fog,
          padding: '3px 8px', borderRadius: 4,
        }}>
          {k === 'status' ? meta[k].split('—')[0].trim() : meta[k]}
        </span>
      ))}
    </div>
  );
}

function MarkdownView({ content }) {
  if (!content) return null;
  const { meta, body } = parseFrontmatter(content);
  const effectiveContent = body || content;

  const lines  = effectiveContent.split('\n');
  const blocks = [];
  let paraLines = [], inBlockquote = false, inTable = false, tableRows = [];

  const flushPara = () => {
    if (!paraLines.length) return;
    const text = paraLines.join(' ').trim();
    if (text) blocks.push({ type: 'p', text });
    paraLines = [];
  };
  const flushTable = () => {
    if (!tableRows.length) return;
    blocks.push({ type: 'table', rows: tableRows });
    tableRows = []; inTable = false;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trim = line.trim();

    if (!trim) { flushPara(); flushTable(); inBlockquote = false; continue; }

    if (trim.startsWith('# '))   { flushPara(); blocks.push({ type: 'h1', text: trim.slice(2) }); continue; }
    if (trim.startsWith('## '))  { flushPara(); blocks.push({ type: 'h2', text: trim.slice(3) }); continue; }
    if (trim.startsWith('### ')) { flushPara(); blocks.push({ type: 'h3', text: trim.slice(4) }); continue; }
    if (trim.startsWith('#### ')){ flushPara(); blocks.push({ type: 'h4', text: trim.slice(5) }); continue; }
    if (trim === '---' || trim === '***') { flushPara(); blocks.push({ type: 'hr' }); continue; }
    if (trim.startsWith('- ') || trim.startsWith('* ')) {
      flushPara();
      blocks.push({ type: 'li', text: trim.slice(2) });
      continue;
    }
    if (/^\d+\. /.test(trim)) {
      flushPara();
      blocks.push({ type: 'oli', text: trim.replace(/^\d+\. /, ''), n: trim.match(/^(\d+)/)[1] });
      continue;
    }
    if (trim.startsWith('>')) {
      flushPara();
      blocks.push({ type: 'bq', text: trim.slice(1).trim() });
      continue;
    }
    // Image: ![alt](url)
    if (/^!\[.*\]\(.+\)/.test(trim)) {
      flushPara();
      const m = trim.match(/^!\[([^\]]*)\]\(([^)]+)\)/);
      if (m) blocks.push({ type: 'img', alt: m[1], url: m[2] });
      continue;
    }
    // Italic-only line → treat as image caption
    if (/^\*[^*\n]+\*$/.test(trim)) {
      flushPara();
      blocks.push({ type: 'caption', text: trim.slice(1, -1) });
      continue;
    }
    // Table row
    if (trim.startsWith('|')) {
      flushPara();
      const cells = trim.split('|').filter((_, ci) => ci > 0 && ci < trim.split('|').length - 1);
      if (cells.some(c => /^[-: ]+$/.test(c.trim()))) continue; // separator row
      tableRows.push(cells.map(c => c.trim()));
      inTable = true;
      continue;
    }
    if (inTable) { flushTable(); }

    paraLines.push(trim);
  }
  flushPara();
  flushTable();

  // Group consecutive list items
  const grouped = [];
  let i2 = 0;
  while (i2 < blocks.length) {
    if (blocks[i2].type === 'li') {
      const items = [];
      while (i2 < blocks.length && blocks[i2].type === 'li') items.push(blocks[i2++]);
      grouped.push({ type: 'ul', items });
    } else if (blocks[i2].type === 'oli') {
      const items = [];
      while (i2 < blocks.length && blocks[i2].type === 'oli') items.push(blocks[i2++]);
      grouped.push({ type: 'ol', items });
    } else {
      grouped.push(blocks[i2++]);
    }
  }

  return (
    <div style={{ fontFamily: F.serif, fontSize: 14.5, lineHeight: 1.8, color: C.slate, maxWidth: 740 }}>
      <FrontmatterBadge meta={meta} />
      {grouped.map((b, idx) => {
        switch (b.type) {
          case 'h1': return (
            <h1 key={idx} style={{ fontFamily: F.sans, fontSize: 22, color: C.ink, fontWeight: 700,
              margin: "28px 0 12px", letterSpacing: "-0.02em", lineHeight: 1.2 }}>
              {renderInline(b.text)}
            </h1>
          );
          case 'h2': return (
            <div key={idx} style={{ margin: "28px 0 10px" }}>
              <h2 style={{ fontFamily: F.sans, fontSize: 16, color: C.navy, fontWeight: 700,
                letterSpacing: "-0.01em", margin: 0, lineHeight: 1.3 }}>
                {renderInline(b.text)}
              </h2>
              <div style={{ height: 1, background: `linear-gradient(to right, ${C.ocean}66, transparent)`,
                marginTop: 6, borderRadius: 1 }}/>
            </div>
          );
          case 'h3': return (
            <h3 key={idx} style={{ fontFamily: F.sans, fontSize: 13, color: C.gold, fontWeight: 700,
              margin: "18px 0 5px", letterSpacing: "0.01em" }}>
              {renderInline(b.text)}
            </h3>
          );
          case 'h4': return (
            <h4 key={idx} style={{ fontFamily: F.sans, fontSize: 12, color: C.slate, fontWeight: 700,
              margin: "14px 0 4px", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              {renderInline(b.text)}
            </h4>
          );
          case 'hr': return (
            <hr key={idx} style={{ border: "none", borderTop: `1px solid ${C.mist}`,
              margin: "22px 0" }}/>
          );
          case 'p': return (
            <p key={idx} style={{ margin: "0 0 14px", lineHeight: 1.85 }}>
              {renderInline(b.text)}
            </p>
          );
          case 'bq': return (
            <div key={idx} style={{ margin: "14px 0", padding: "12px 18px",
              borderLeft: `3px solid ${C.gold}`, background: "#FAF7F2",
              borderRadius: "0 6px 6px 0" }}>
              <p style={{ margin: 0, fontStyle: "italic", color: C.navy, lineHeight: 1.7 }}>
                {renderInline(b.text)}
              </p>
            </div>
          );
          case 'ul': return (
            <ul key={idx} style={{ margin: "6px 0 14px", paddingLeft: 0, listStyle: "none" }}>
              {b.items.map((it, j) => (
                <li key={j} style={{ display: "flex", gap: 10, marginBottom: 6, lineHeight: 1.7 }}>
                  <span style={{ color: C.gold, fontWeight: 700, flexShrink: 0, marginTop: 1 }}>—</span>
                  <span>{renderInline(it.text)}</span>
                </li>
              ))}
            </ul>
          );
          case 'ol': return (
            <ol key={idx} style={{ margin: "6px 0 14px", paddingLeft: 0, listStyle: "none", counterReset: "mc" }}>
              {b.items.map((it, j) => (
                <li key={j} style={{ display: "flex", gap: 10, marginBottom: 6, lineHeight: 1.7 }}>
                  <span style={{ color: C.ocean, fontWeight: 700, flexShrink: 0, minWidth: 20 }}>{j + 1}.</span>
                  <span>{renderInline(it.text)}</span>
                </li>
              ))}
            </ol>
          );
          case 'table': return (
            <div key={idx} style={{ margin: "14px 0", overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse",
                fontFamily: F.sans, fontSize: 12 }}>
                <tbody>
                  {b.rows.map((row, ri) => (
                    <tr key={ri} style={{ background: ri % 2 === 0 ? "#F8FAFC" : "#fff",
                      borderBottom: "1px solid #DDE4EB" }}>
                      {row.map((cell, ci) => {
                        const Tag = ri === 0 ? "th" : "td";
                        return (
                          <Tag key={ci} style={{
                            padding: "8px 12px", textAlign: "left",
                            fontWeight: ri === 0 ? 700 : 400,
                            color: ri === 0 ? C.navy : C.slate,
                            fontSize: ri === 0 ? 10 : 12,
                            letterSpacing: ri === 0 ? "0.08em" : 0,
                            textTransform: ri === 0 ? "uppercase" : "none",
                          }}>
                            {renderInline(cell)}
                          </Tag>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
          case 'img': return (
            <div key={idx} style={{ margin: "20px 0", borderRadius: 8, overflow: "hidden",
              boxShadow: "0 2px 12px rgba(10,37,64,0.10)" }}>
              <img src={b.url} alt={b.alt}
                style={{ width: "100%", display: "block", maxHeight: 420, objectFit: "cover" }}
                onError={e => { e.currentTarget.style.display = "none"; }}/>
            </div>
          );
          case 'caption': return (
            <p key={idx} style={{ textAlign: "center", fontSize: "0.8rem", fontStyle: "italic",
              color: C.fog, margin: "-12px 0 16px", fontFamily: F.sans }}>
              {b.text}
            </p>
          );
          default: return null;
        }
      })}
    </div>
  );
}

// ── Multi-select hook ──────────────────────────────────────────────────────
function useMultiSelect() {
  const [checked, setChecked] = useState(new Set());
  const toggle   = (id) => setChecked(prev => { const s=new Set(prev); s.has(id)?s.delete(id):s.add(id); return s; });
  const clear    = ()   => setChecked(new Set());
  const selectAll= (ids)=> setChecked(new Set(ids));
  const allSelected = (ids) => ids.length > 0 && ids.every(id => checked.has(id));
  return { checked, toggle, clear, selectAll, allSelected };
}

// ── Bulk delete helper ────────────────────────────────────────────────────
async function bulkDelete(items) {
  // items: [{folder, filename}, ...]
  const res  = await fetch(`${API}/api/files/delete-bulk`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({items}),
  });
  return res.json();
}

// ── File item — hover-reveal actions (Notion/Linear style) ───────────────────
function FileItem({title, subtitle, selected, checked, onSelect, onCheck, onDelete, onEdit}){
  const [hover, setHover] = useState(false);
  const handleDelete = (e) => {
    e.stopPropagation();
    if(window.confirm(`Delete "${title}"?`)){ onDelete(); }
  };
  return(
    <div
      style={{display:"flex",alignItems:"center",gap:6,marginBottom:4,position:"relative"}}
      onMouseEnter={()=>setHover(true)}
      onMouseLeave={()=>setHover(false)}
    >
      {/* Checkbox — always visible so users know they can select */}
      <div style={{ width:16, flexShrink:0 }}>
        <input type="checkbox" checked={checked||false}
          onChange={e=>{e.stopPropagation();onCheck&&onCheck();}}
          style={{width:14,height:14,cursor:"pointer",accentColor:C.ocean,display:"block"}}/>
      </div>

      {/* Main row */}
      <div onClick={onSelect} style={{
        flex:1, padding:"9px 12px",
        background: selected ? C.sand : hover ? "#F4F7FA" : C.pearl,
        border:`1px solid ${selected?C.ocean:C.mist}`,
        borderLeft: selected?`3px solid ${C.ocean}`:`1px solid ${C.mist}`,
        borderRadius:7, cursor:"pointer",
        transition:"background 0.1s, border-color 0.1s",
      }}>
        <div style={{fontFamily:F.sans,fontSize:12,
          color:selected?C.ink:C.slate,
          fontWeight:selected?600:400,
          lineHeight:1.4,
        }}>{title?.slice(0,44)}</div>
        {subtitle&&<div style={{fontFamily:F.sans,fontSize:10,color:C.fog,marginTop:2}}>{subtitle}</div>}
      </div>

      {/* Action icons — dim by default, full on hover */}
      <div style={{
        display:"flex",gap:2,flexShrink:0,
        opacity:hover?1:0.35,transition:"opacity 0.15s",
      }}>
        {onEdit&&(
          <button onClick={e=>{e.stopPropagation();onEdit();}}
            title="Edit"
            style={{width:26,height:26,display:"flex",alignItems:"center",justifyContent:"center",
              background:"transparent",border:`1px solid ${C.mist}`,borderRadius:5,
              cursor:"pointer",color:C.fog,fontSize:11,padding:0,lineHeight:1}}>
            ✎
          </button>
        )}
        <button onClick={handleDelete} title="Delete"
          style={{width:26,height:26,display:"flex",alignItems:"center",justifyContent:"center",
            background:"transparent",border:`1px solid ${C.mist}`,borderRadius:5,
            cursor:"pointer",color:C.fog,fontSize:12,padding:0,lineHeight:1,
            transition:"color 0.12s,border-color 0.12s"}}
          onMouseEnter={e=>{e.currentTarget.style.color=C.red;e.currentTarget.style.borderColor=C.red;}}
          onMouseLeave={e=>{e.currentTarget.style.color=C.fog;e.currentTarget.style.borderColor=C.mist;}}>
          &#x2715;
        </button>
      </div>
    </div>
  );
}

// ── Bulk action bar ───────────────────────────────────────────────────────
function BulkBar({count, onDeleteSelected, onClear, onSelectAll}){
  if(count===0) return null;
  return(
    <div style={{display:"flex",alignItems:"center",gap:8,padding:"8px 12px",background:"#EBF3FB",border:`1px solid ${C.blue}33`,borderRadius:6,marginBottom:8}}>
      <span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.blue,fontWeight:600,flex:1}}>
        {count} selected
      </span>
      <button onClick={onSelectAll} style={{...S.btn("ghost"),padding:"3px 8px",fontSize:10}}>All</button>
      <button onClick={onClear}     style={{...S.btn("ghost"),padding:"3px 8px",fontSize:10}}>None</button>
      <button onClick={onDeleteSelected}
        style={{...S.btn("ghost"),padding:"3px 8px",fontSize:10,color:C.red,borderColor:C.red}}>
        Delete {count}
      </button>
    </div>
  );
}

// ── Inline editor ──────────────────────────────────────────────────────────
function InlineEditor({content, filename, endpoint, onSave, onCancel}){
  const [val, setVal] = useState(content||"");
  const [saving, setSaving] = useState(false);

  const save = async()=>{
    setSaving(true);
    try{
      await fetch(`${API}${endpoint}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename,content:val})});
      onSave(val);
    }catch(e){console.error(e);}
    setSaving(false);
  };

  return(
    <div style={{...S.card,marginBottom:0}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
        <span style={{fontFamily:"Helvetica,sans-serif",fontSize:12,fontWeight:600,color:C.black}}>Editing: {filename}</span>
        <div style={{display:"flex",gap:8}}>
          <button style={S.btn("ghost")} onClick={onCancel}>Cancel</button>
          <button style={S.btn("teal")} onClick={save} disabled={saving}>{saving?"Saving...":"Save"}</button>
        </div>
      </div>
      <textarea style={{...S.textarea,minHeight:400}} value={val} onChange={e=>setVal(e.target.value)}/>
    </div>
  );
}

// ── Sparkline chart (pure SVG — no library needed) ─────────────────────────
function Sparkline({data, valueKey, color="#5B7FA6", height=48, label=""}){
  if(!data||data.length<2) return null;
  const vals = data.map(d=>d[valueKey]||0);
  const max  = Math.max(...vals, 0.001);
  const w=480, h=height, pad=4;
  const pts = vals.map((v,i)=>`${pad+(i/(vals.length-1))*(w-pad*2)},${h-pad-(v/max)*(h-pad*2)}`).join(" ");
  return(
    <div>
      {label&&<div style={{fontFamily:"Helvetica,sans-serif",fontSize:10,color:C.muted,letterSpacing:"0.08em",textTransform:"uppercase",marginBottom:4}}>{label}</div>}
      <svg viewBox={`0 0 ${w} ${h}`} style={{width:"100%",height}} preserveAspectRatio="none">
        <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round"/>
        <polyline points={`${pad},${h} ${pts} ${w-pad},${h}`} fill={color} fillOpacity="0.08" stroke="none"/>
      </svg>
      <div style={{display:"flex",justifyContent:"space-between",fontFamily:"Helvetica,sans-serif",fontSize:10,color:C.muted,marginTop:2}}>
        <span>{data[0]?.date?.slice(5)}</span>
        <span>{data[data.length-1]?.date?.slice(5)}</span>
      </div>
    </div>
  );
}

// ── Hourly bar chart (per-hour token usage for today) ────────────────────────
function HourlyBars({data, valueKey="tokens", color=C.blue, height=120, highlightNow=true}){
  if(!data||!data.length) return null;
  const vals = data.map(d=>d[valueKey]||0);
  const max  = Math.max(...vals, 1);
  const nowHour = highlightNow?new Date().getHours():-1;
  return(
    <div>
      <div style={{display:"flex",alignItems:"flex-end",gap:2,height}}>
        {data.map((d,i)=>{
          const v=d[valueKey]||0;
          const isNow=i===nowHour;
          return(
            <div key={i} title={`${d.hour}:00 — ${v.toLocaleString()} ${valueKey} · ${d.calls} calls · $${(d.cost||0).toFixed(4)}`}
              style={{flex:1,display:"flex",flexDirection:"column",justifyContent:"flex-end",height:"100%",cursor:"default"}}>
              <div style={{height:`${Math.max((v/max)*100, v>0?3:0)}%`,
                background:isNow?C.warm:color,opacity:v>0?(isNow?1:0.75):0.12,
                borderRadius:"2px 2px 0 0",minHeight:v>0?2:1,transition:"height 0.2s"}}/>
            </div>
          );
        })}
      </div>
      <div style={{display:"flex",justifyContent:"space-between",fontFamily:"Helvetica,sans-serif",fontSize:9,color:C.muted,marginTop:4}}>
        {["00","06","12","18","23"].map(h=>(<span key={h}>{h}:00</span>))}
      </div>
    </div>
  );
}

// ── Dashboard ──────────────────────────────────────────────────────────────
function Dashboard({data}){
  const [history,setHistory]=useState([]);
  const [ts,setTs]=useState(null);
  const [hourlyDay,setHourlyDay]=useState("today");  // which day the hourly chart shows
  useEffect(()=>{
    fetch(`${API}/api/dashboard/history?days=30`).then(r=>r.json()).then(d=>setHistory(d.daily||[])).catch(()=>{});
  },[]);
  // Refetch when the hourly day toggle changes (today/yesterday totals come back unchanged).
  useEffect(()=>{
    fetch(`${API}/api/dashboard/timeseries?day=${hourlyDay}`).then(r=>r.json()).then(setTs).catch(()=>{});
  },[hourlyDay]);

  if(!data) return <div style={{color:C.muted,fontFamily:"Helvetica,sans-serif",fontSize:13}}>Loading dashboard...</div>;
  const t=data.token_report?.totals||{};
  const kb=data.kb_stats||{};
  const today=ts?.today||{}, yest=ts?.yesterday||{};
  // % change today vs yesterday; null when yesterday is 0 (avoid divide-by-zero noise)
  const delta=(a,b)=>(b>0?((a-b)/b*100):null);
  const fmtDelta=d=>d==null?"":`${d>=0?"▲":"▼"} ${Math.abs(d).toFixed(0)}% vs yest`;
  const deltaColor=d=>d==null?C.muted:d>=0?C.warm:C.green;
  const timeCards=[
    {label:"Tokens — Today", value:(today.tokens||0).toLocaleString(), sub:`${(yest.tokens||0).toLocaleString()} yesterday`, d:delta(today.tokens||0,yest.tokens||0), color:C.blue},
    {label:"Spend — Today",  value:`$${(today.cost||0).toFixed(4)}`,   sub:`$${(yest.cost||0).toFixed(4)} yesterday`, d:delta(today.cost||0,yest.cost||0), color:C.warm},
    {label:"API Calls — Today", value:today.calls||0,                  sub:`${yest.calls||0} yesterday`, d:delta(today.calls||0,yest.calls||0), color:C.slate},
  ];
  const stats=[
    {label:"API Calls (30d)",  value:t.total_calls||0,          color:C.slate},
    {label:"Total Tokens (30d)", value:(t.total_tokens||0).toLocaleString(), color:C.blue},
    {label:"Spend (30d, USD)",   value:`$${(t.total_cost||0).toFixed(4)}`, color:C.warm},
    {label:"KB Documents",     value:kb.total_docs||0,           color:C.teal},
    {label:"KB Chunks",        value:(kb.total_chunks||0).toLocaleString(), color:C.teal},
    {label:"Cache Hit Rate",   value:t.total_calls>0?`${((t.cache_hits||0)/t.total_calls*100).toFixed(1)}%`:"—", color:C.green},
  ];
  return(
    <div>
      <div style={{marginBottom:28}}>
        <h2 style={S.h2}>Dashboard</h2>
        <span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.muted}}>{new Date().toLocaleDateString("en-US",{weekday:"long",year:"numeric",month:"long",day:"numeric"})}</span>
      </div>
      {/* Today vs yesterday */}
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16,marginBottom:16}}>
        {timeCards.map(s=>(
          <div key={s.label} style={{...S.card,padding:"18px 20px",marginBottom:0}}>
            <div style={{...S.stat,color:s.color}}>{s.value}</div>
            <div style={S.statLabel}>{s.label}</div>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginTop:8}}>
              <span style={{fontFamily:"Helvetica,sans-serif",fontSize:10,color:C.muted}}>{s.sub}</span>
              <span style={{fontFamily:"Helvetica,sans-serif",fontSize:10,fontWeight:600,color:deltaColor(s.d)}}>{fmtDelta(s.d)}</span>
            </div>
          </div>
        ))}
      </div>
      {/* Per-hour breakdown — switchable between today and yesterday */}
      {ts?.hourly?.length>0&&(
        <div style={{...S.card,marginBottom:24}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <span style={S.label}>Tokens by hour{hourlyDay==="today"?" — gold bar = current hour":""}</span>
            <div style={{display:"flex",gap:4}}>
              {["today","yesterday"].map(d=>(
                <button key={d} onClick={()=>setHourlyDay(d)}
                  style={{padding:"3px 12px",borderRadius:6,cursor:"pointer",
                    fontFamily:"Helvetica,sans-serif",fontSize:10,fontWeight:600,letterSpacing:"0.04em",textTransform:"uppercase",
                    border:`1px solid ${hourlyDay===d?C.navy:C.mist}`,
                    background:hourlyDay===d?C.navy:"transparent",
                    color:hourlyDay===d?C.pearl:C.fog}}>{d}</button>
              ))}
            </div>
          </div>
          <div style={{marginTop:14}}><HourlyBars data={ts.hourly} valueKey="tokens" color={C.blue} highlightNow={hourlyDay==="today"}/></div>
        </div>
      )}
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16,marginBottom:24}}>
        {stats.map(s=>(<div key={s.label} style={{...S.card,padding:"18px 20px",marginBottom:0}}><div style={{...S.stat,color:s.color}}>{s.value}</div><div style={S.statLabel}>{s.label}</div></div>))}
      </div>
      {history.length>1&&(
        <div style={{...S.card,marginBottom:24}}>
          <span style={S.label}>Activity over time — 30 days</span>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:24,marginTop:16}}>
            <Sparkline data={history} valueKey="total_calls"  color={C.blue}  label="API Calls / day"/>
            <Sparkline data={history} valueKey="total_cost"   color={C.warm}  label="Spend (USD) / day"/>
            <Sparkline data={history} valueKey="total_tokens" color={C.teal}  label="Tokens / day"/>
            <Sparkline data={history} valueKey="cache_hits"   color={C.green} label="Cache hits / day"/>
          </div>
        </div>
      )}
      {data.token_report?.by_agent?.length>0&&(
        <div style={S.card}>
          <span style={S.label}>Token spend by agent</span>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:"Helvetica,sans-serif",fontSize:12}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>{["Agent","Calls","Tokens","Cost"].map(h=>(<th key={h} style={{padding:"6px 8px",textAlign:"left",color:C.muted,fontWeight:600,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase"}}>{h}</th>))}</tr></thead>
            <tbody>{data.token_report.by_agent.map((a,i)=>(<tr key={i} style={{borderBottom:`1px solid ${C.ltgray}`}}><td style={{padding:"8px",color:C.black,fontWeight:500}}>{a.agent}</td><td style={{padding:"8px",color:C.muted}}>{a.calls}</td><td style={{padding:"8px",color:C.muted}}>{(a.tokens||0).toLocaleString()}</td><td style={{padding:"8px",color:C.warm,fontWeight:600}}>${(a.cost||0).toFixed(4)}</td></tr>))}</tbody>
          </table>
        </div>
      )}
      {data.token_report?.by_purpose?.length>0&&(
        <div style={S.card}>
          <span style={S.label}>Token spend by purpose (30 days)</span>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:"Helvetica,sans-serif",fontSize:12}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>{["Purpose","Calls","Tokens","Cost"].map(h=>(<th key={h} style={{padding:"6px 8px",textAlign:"left",color:C.muted,fontWeight:600,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase"}}>{h}</th>))}</tr></thead>
            <tbody>{data.token_report.by_purpose.map((p,i)=>(<tr key={i} style={{borderBottom:`1px solid ${C.ltgray}`}}><td style={{padding:"8px",color:C.black,fontWeight:500}}>{p.purpose}</td><td style={{padding:"8px",color:C.muted}}>{p.calls}</td><td style={{padding:"8px",color:C.muted}}>{(p.tokens||0).toLocaleString()}</td><td style={{padding:"8px",color:C.warm,fontWeight:600}}>${(p.cost||0).toFixed(4)}</td></tr>))}</tbody>
          </table>
        </div>
      )}
      {data.recent_topics?.length>0&&(
        <div style={S.card}>
          <span style={S.label}>Recent content topics</span>
          {data.recent_topics.slice(0,8).map((t,i)=>(<div key={i} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:i<7?`1px solid ${C.ltgray}`:"none"}}><span style={{fontFamily:"Helvetica,sans-serif",fontSize:12,color:C.slate}}>{t.title}</span><span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.muted}}>{t.timestamp?.slice(0,10)}</span></div>))}
        </div>
      )}
    </div>
  );
}

// ── Briefing ───────────────────────────────────────────────────────────────
function BriefingView(){
  const [briefings,setBriefings]=useState([]);
  const [selected,setSelected]=useState(null);
  const [content,setContent]=useState("");
  const [editing,setEditing]=useState(false);
  const ms = useMultiSelect();

  const load=()=>{
    fetch(`${API}/api/briefings`).then(r=>r.json()).then(d=>{setBriefings(d.briefings||[]);if(d.briefings?.[0])setSelected(d.briefings[0].filename);}).catch(()=>{});
  };
  useEffect(()=>{load();},[]);
  useEffect(()=>{if(!selected)return;fetch(`${API}/api/briefings/${selected}`).then(r=>r.json()).then(d=>setContent(d.content||"")).catch(()=>{});},[selected]);

  const deleteFile=async(filename)=>{
    await fetch(`${API}/api/files/delete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename,folder:"briefings"})});
    if(selected===filename){setSelected(null);setContent("");setEditing(false);}
    ms.clear(); setTimeout(()=>load(), 200);
  };

  const deleteSelected=async()=>{
    if(!ms.checked.size) return;
    if(!window.confirm(`Delete ${ms.checked.size} briefing(s)?`)) return;
    await bulkDelete([...ms.checked].map(f=>({folder:"briefings",filename:f})));
    if(ms.checked.has(selected)){setSelected(null);setContent("");setEditing(false);}
    ms.clear(); setTimeout(()=>load(), 200);
  };

  const allIds = briefings.map(b=>b.filename);
  return(
    <div>
      <h2 style={{...S.h2,marginBottom:20}}>Daily Briefing</h2>
      <div style={{display:"flex",gap:20}}>
        <div style={{width:230,flexShrink:0}}>
          <BulkBar count={ms.checked.size} onDeleteSelected={deleteSelected} onClear={ms.clear} onSelectAll={()=>ms.selectAll(allIds)}/>
          {briefings.map(b=>(<FileItem key={b.filename} title={b.date} subtitle="" selected={selected===b.filename} checked={ms.checked.has(b.filename)} onCheck={()=>ms.toggle(b.filename)} onSelect={()=>{setSelected(b.filename);setEditing(false);}} onDelete={()=>deleteFile(b.filename)} onEdit={()=>{setSelected(b.filename);setEditing(true);}}/>))}
          {briefings.length===0&&<div style={{fontFamily:"Helvetica,sans-serif",fontSize:12,color:C.muted}}>No briefings yet.</div>}
        </div>
        <div style={{flex:1}}>
          {editing&&selected
            ? <InlineEditor content={content} filename={selected} endpoint="/api/files/save" onSave={v=>{setContent(v);setEditing(false);}} onCancel={()=>setEditing(false)}/>
            : <div style={S.card}>{content?<MarkdownView content={content}/>:<div style={{color:C.muted,fontFamily:"Helvetica,sans-serif",fontSize:13}}>Select a briefing</div>}</div>
          }
        </div>
      </div>
    </div>
  );
}

// ── Content ────────────────────────────────────────────────────────────────
function ContentView({onGenerate}){
  const [drafts,setDrafts]=useState([]);
  const [selected,setSelected]=useState(null);
  const [content,setContent]=useState("");
  const [editing,setEditing]=useState(false);
  const [genStatus,setGenStatus]=useState("");
  const [viewingDoc,setViewingDoc]=useState(null);  // {folder, filename} for FileViewer
  const ms = useMultiSelect();

  const load=()=>{fetch(`${API}/api/drafts`).then(r=>r.json()).then(d=>{setDrafts(d.drafts||[]);if(d.drafts?.[0]&&!selected)setSelected(d.drafts[0].filename);}).catch(()=>{});};
  useEffect(()=>{load();},[]);
  useEffect(()=>{if(!selected)return;fetch(`${API}/api/drafts/${selected}`).then(r=>r.json()).then(d=>setContent(d.content||"")).catch(()=>{});},[selected]);

  const deleteFile=async(filename)=>{
    await fetch(`${API}/api/files/delete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename,folder:"content/drafts"})});
    if(selected===filename){setSelected(null);setContent("");setEditing(false);}
    ms.clear(); setTimeout(()=>load(), 200);
  };

  const deleteSelected=async()=>{
    if(!ms.checked.size) return;
    if(!window.confirm(`Delete ${ms.checked.size} draft(s)?`)) return;
    await bulkDelete([...ms.checked].map(f=>({folder:"content/drafts",filename:f})));
    if(ms.checked.has(selected)){setSelected(null);setContent("");setEditing(false);}
    ms.clear(); setTimeout(()=>load(), 200);
  };

  const exportDoc=async(openInApp=false)=>{
    if(!content||!selected)return;
    const title=drafts.find(d=>d.filename===selected)?.title||selected;
    setGenStatus(openInApp?"Generating preview…":"Generating Word document...");
    try{
      const res=await fetch(`${API}/api/documents/generate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title,content,doc_type:"article"})});
      const data=await res.json();
      if(data.path){
        setGenStatus(`Ready: ${data.filename}`);
        if(openInApp){
          setViewingDoc({folder:"documents",filename:data.filename});
        } else {
          await fetch(`${API}/api/documents/open/${data.filename}`);
        }
      }
    }catch{setGenStatus("Error generating document");}
  };

  const allIds = drafts.map(d=>d.filename);
  return(
    <div>
      <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:20}}>
        <h2 style={S.h2}>Content Drafts</h2>
        <div style={{display:"flex",gap:10,alignItems:"center"}}>
          {genStatus&&<span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.teal}}>{genStatus}</span>}
          {content&&<button style={S.btn("ocean")} onClick={()=>exportDoc(true)}>View as Doc</button>}
          {content&&<button style={S.btn("teal")} onClick={()=>exportDoc(false)}>Open in Word</button>}
        </div>
      </div>
      <div style={{display:"flex",gap:20}}>
        <div style={{width:240,flexShrink:0}}>
          <BulkBar count={ms.checked.size} onDeleteSelected={deleteSelected} onClear={ms.clear} onSelectAll={()=>ms.selectAll(allIds)}/>
          {drafts.map(d=>(<FileItem key={d.filename} title={d.title} subtitle={d.modified?.slice(0,10)} selected={selected===d.filename} checked={ms.checked.has(d.filename)} onCheck={()=>ms.toggle(d.filename)} onSelect={()=>{setSelected(d.filename);setEditing(false);}} onDelete={()=>deleteFile(d.filename)} onEdit={()=>{setSelected(d.filename);setEditing(true);}}/>))}
          {drafts.length===0&&<div style={{fontFamily:"Helvetica,sans-serif",fontSize:12,color:C.muted}}>No drafts yet.</div>}
        </div>
        <div style={{flex:1}}>
          {editing&&selected
            ? <InlineEditor content={content} filename={selected} endpoint="/api/files/save" onSave={v=>{setContent(v);setEditing(false);}} onCancel={()=>setEditing(false)}/>
            : <div style={S.card}>{content?<MarkdownView content={content}/>:<div style={{color:C.muted,fontFamily:"Helvetica,sans-serif",fontSize:13}}>Select a draft or generate a new one</div>}</div>
          }
        </div>
      </div>
      {viewingDoc&&<FileViewer folder={viewingDoc.folder} filename={viewingDoc.filename} onClose={()=>setViewingDoc(null)}/>}
    </div>
  );
}

// ── Coaching ───────────────────────────────────────────────────────────────
function CoachingView({onGenerate}){
  const [client,setClient]=useState("");
  const [status,setStatus]=useState("");
  const [briefs,setBriefs]=useState([]);
  const [selected,setSelected]=useState(null);
  const [content,setContent]=useState("");
  const [editing,setEditing]=useState(false);
  const ms = useMultiSelect();

  const load=()=>{fetch(`${API}/api/coaching/briefs`).then(r=>r.json()).then(d=>{setBriefs(d.briefs||[]);}).catch(()=>{});};
  useEffect(()=>{load();},[]);
  useEffect(()=>{if(!selected)return;fetch(`${API}/api/coaching/briefs/${selected}`).then(r=>r.json()).then(d=>setContent(d.content||"")).catch(()=>{});},[selected]);

  const runBrief=()=>{
    if(!client.trim())return;
    setStatus(`Generating brief for ${client}...`);
    fetch(`${API}/api/orchestrate/coaching`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({client})}).then(()=>setStatus("Brief generating — will appear in Review queue for your approval")).catch(()=>setStatus("Error"));
  };

  const deleteFile=async(filename)=>{
    await fetch(`${API}/api/files/delete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename,folder:"coaching/briefs"})});
    if(selected===filename){setSelected(null);setContent("");setEditing(false);}
    ms.clear(); setTimeout(()=>load(), 200);
  };

  const deleteSelected=async()=>{
    if(!ms.checked.size) return;
    if(!window.confirm(`Delete ${ms.checked.size} brief(s)?`)) return;
    await bulkDelete([...ms.checked].map(f=>({folder:"coaching/briefs",filename:f})));
    if(ms.checked.has(selected)){setSelected(null);setContent("");setEditing(false);}
    ms.clear(); setTimeout(()=>load(), 200);
  };

  const exportDoc=async()=>{
    if(!content)return;
    setStatus("Generating Word document...");
    try{
      const res=await fetch(`${API}/api/documents/generate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:`Discovery Call Brief — ${client||selected}`,content,doc_type:"brief"})});
      const data=await res.json();
      if(data.path){setStatus(`Saved: ${data.filename}`);await fetch(`${API}/api/documents/open/${data.filename}`);}
    }catch{setStatus("Error");}
  };

  const allIds=briefs.map(b=>b.filename);
  return(
    <div>
      <h2 style={{...S.h2,marginBottom:20}}>Coaching Briefs</h2>
      <div style={{...S.card,display:"flex",gap:12,alignItems:"center",marginBottom:20}}>
        <input value={client} onChange={e=>setClient(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runBrief()} placeholder="Client name or LinkedIn URL" style={{...S.input,flex:1}}/>
        <button style={S.btn()} onClick={runBrief}>Generate Brief</button>
        {content&&<button style={S.btn("teal")} onClick={exportDoc}>Save as Word Doc</button>}
        {status&&<span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.teal}}>{status}</span>}
      </div>
      <div style={{display:"flex",gap:20}}>
        <div style={{width:240,flexShrink:0}}>
          <BulkBar count={ms.checked.size} onDeleteSelected={deleteSelected} onClear={ms.clear} onSelectAll={()=>ms.selectAll(allIds)}/>
          {briefs.map(b=>(<FileItem key={b.filename} title={b.filename.replace('.md','').slice(11)} subtitle={b.filename.slice(0,10)} selected={selected===b.filename} checked={ms.checked.has(b.filename)} onCheck={()=>ms.toggle(b.filename)} onSelect={()=>{setSelected(b.filename);setEditing(false);}} onDelete={()=>deleteFile(b.filename)} onEdit={()=>{setSelected(b.filename);setEditing(true);}}/>))}
          {briefs.length===0&&<div style={{fontFamily:"Helvetica,sans-serif",fontSize:12,color:C.muted}}>No briefs yet.</div>}
        </div>
        <div style={{flex:1}}>
          {editing&&selected
            ? <InlineEditor content={content} filename={selected} endpoint="/api/files/save" onSave={v=>{setContent(v);setEditing(false);}} onCancel={()=>setEditing(false)}/>
            : <div style={S.card}>{content?<MarkdownView content={content}/>:<div style={{color:C.muted,fontFamily:"Helvetica,sans-serif",fontSize:13}}>Enter a client name and generate a brief</div>}</div>
          }
        </div>
      </div>
    </div>
  );
}

// ── Documents ──────────────────────────────────────────────────────────────
function DocumentsView(){
  const [docs,setDocs]=useState([]);
  const [viewing,setViewing]=useState(null);
  const ms=useMultiSelect();
  const load=()=>{fetch(`${API}/api/documents`).then(r=>r.json()).then(d=>setDocs(d.documents||[])).catch(()=>{});};
  useEffect(()=>{load();},[]);
  const openDoc=(filename)=>{fetch(`${API}/api/documents/open/${filename}`).catch(()=>{});};
  const deleteDoc=async(filename)=>{
    await fetch(`${API}/api/files/delete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename,folder:"documents"})});
    ms.clear(); load();
  };
  const deleteSelected=async()=>{
    if(!ms.checked.size) return;
    if(!window.confirm(`Delete ${ms.checked.size} document(s)?`)) return;
    await bulkDelete([...ms.checked].map(f=>({folder:"documents",filename:f})));
    ms.clear(); setTimeout(()=>load(), 200);
  };
  const allIds=docs.map(d=>d.filename);
  return(
    <div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20}}>
        <h2 style={S.h2}>Generated Documents</h2>
        {ms.checked.size>0&&(
          <div style={{display:"flex",gap:8}}>
            <button onClick={ms.clear} style={{...S.btn("ghost"),fontSize:11}}>None</button>
            <button onClick={()=>ms.selectAll(allIds)} style={{...S.btn("ghost"),fontSize:11}}>All</button>
            <button onClick={deleteSelected} style={{...S.btn("ghost"),fontSize:11,color:C.red,borderColor:C.red}}>Delete {ms.checked.size}</button>
          </div>
        )}
      </div>
      {docs.length===0
        ? <div style={{...S.card,color:C.muted,fontFamily:"Helvetica,sans-serif",fontSize:13}}>No documents yet. Export a draft or brief to Word.</div>
        : docs.map(d=>(
          <div key={d.filename} style={{...S.card,display:"flex",justifyContent:"space-between",alignItems:"center",padding:"14px 20px",marginBottom:10,background:ms.checked.has(d.filename)?"#EBF3FB":undefined,border:ms.checked.has(d.filename)?`1px solid ${C.blue}44`:undefined}}>
            <div style={{display:"flex",alignItems:"center",gap:10}}>
              <input type="checkbox" checked={ms.checked.has(d.filename)} onChange={()=>ms.toggle(d.filename)} style={{width:14,height:14,accentColor:C.blue}}/>
              <div><div style={{fontFamily:"Helvetica,sans-serif",fontSize:13,color:C.black,fontWeight:500}}>{d.filename}</div><div style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.muted,marginTop:3}}>{d.modified?.slice(0,10)}</div></div>
            </div>
            <div style={{display:"flex",gap:8}}>
              <button style={S.btn("teal")} onClick={()=>setViewing(d.filename)}>View</button>
              <button style={{...S.btn(),background:C.slate}} onClick={()=>openDoc(d.filename)}>Open in Word</button>
              <button style={{...S.btn("ghost"),color:C.red}} onClick={()=>deleteDoc(d.filename)}>&#x2715;</button>
            </div>
          </div>
        ))
      }
      {viewing&&<FileViewer folder="documents" filename={viewing} onClose={()=>setViewing(null)}/>}
    </div>
  );
}

// ── Agents ─────────────────────────────────────────────────────────────────
function AgentsView({logs,onRun,runningAgents}){
  const logRef    = useRef(null);
  const logEndRef = useRef(null);

  useEffect(()=>{
    if(logEndRef.current) logEndRef.current.scrollIntoView({behavior:"smooth"});
  },[logs]);

  // Derive running state from the global runningAgents Set (stays in sync across tabs)
  const running = {};
  if(runningAgents){
    runningAgents.forEach(a=>{ running[a]=true; });
    // Also map short IDs used in the agent cards
    const MAP={rag:"rag_agent",briefing:"briefing_agent",content:"content_agent",iso:"iso_coach",consulting:"consulting_agent",ma:"ma_intelligence_agent"};
    Object.entries(MAP).forEach(([short,full])=>{if(runningAgents.has(full)) running[short]=true;});
  }

  const handleRun = (id, override) => { onRun(id, override); };

  const AGENTS=[
    {id:"rag",         label:"RAG Ingestion",         desc:"FDA, EU MDR, IMDRF + Tavily",         color:C.blue},
    {id:"briefing",    label:"Daily Briefing",         desc:"RSS + Brave real-time search",         color:C.teal},
    {id:"content",     label:"Content Draft",          desc:"MedTech Meridian article",             color:C.warm},
    {id:"iso",         label:"ISO 13485 Coach",        desc:"Generate clause lesson content",       color:C.slate},
    {id:"consulting",  label:"Consulting Agent",       desc:"Frameworks, methodologies, case studies", color:"#7B3FA6"},
    {id:"ma",          label:"M&A Intelligence",       desc:"MedTech/Pharma deals, QARA analysis",  color:"#1A6FA3"},
  ];
  const [overrides,setOverrides]=useState({});
  const [showOverride,setShowOverride]=useState(null);

  const runWithOverride=(id)=>{
    handleRun(id, overrides[id]||"");
    setShowOverride(null);
  };

  return(
    <div>
      <h2 style={{...S.h2,marginBottom:8}}>Run Agents</h2>
      <div style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.muted,marginBottom:20}}>Optionally add a focus prompt before running. Agents grey out while in progress.</div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:24}}>
        {AGENTS.map(a=>{
          const isRunning = !!running[a.id];
          return(
            <div key={a.id} style={{...S.card,marginBottom:0,opacity:isRunning?0.7:1,transition:"opacity 0.3s"}}>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:showOverride===a.id?12:0}}>
                <div>
                  <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:3}}>
                    <div style={{fontFamily:"Helvetica,sans-serif",fontSize:13,fontWeight:600,color:C.black}}>{a.label}</div>
                    {isRunning&&(
                      <div style={{display:"flex",alignItems:"center",gap:4}}>
                        <div style={{width:6,height:6,borderRadius:"50%",background:a.color,animation:"pulse 1s ease-in-out infinite"}}/>
                        <span style={{fontFamily:"Helvetica,sans-serif",fontSize:10,color:a.color,letterSpacing:"0.08em",textTransform:"uppercase"}}>Running</span>
                      </div>
                    )}
                  </div>
                  <div style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.muted}}>{a.desc}</div>
                </div>
                <div style={{display:"flex",gap:6,flexShrink:0,marginLeft:12}}>
                  {!isRunning&&<button style={{...S.btn("ghost"),color:C.blue,background:C.ltgray}} onClick={()=>setShowOverride(showOverride===a.id?null:a.id)}>
                    {showOverride===a.id?"Cancel":"+ Focus"}
                  </button>}
                  <button
                    style={{...S.btn(),background:isRunning?C.muted:a.color,cursor:isRunning?"not-allowed":"pointer"}}
                    onClick={()=>!isRunning&&runWithOverride(a.id)}
                    disabled={isRunning}
                  >
                    {isRunning?"Running...":"Run"}
                  </button>
                </div>
              </div>
              {showOverride===a.id&&!isRunning&&(
                <div style={{marginTop:10}}>
                  <textarea
                    placeholder={`Focus this run on a specific topic or instruction… (Ctrl+Enter to run)`}
                    value={overrides[a.id]||""}
                    onChange={e=>setOverrides(prev=>({...prev,[a.id]:e.target.value}))}
                    onKeyDown={e=>{if(e.key==="Enter"&&(e.ctrlKey||e.metaKey)){e.preventDefault();runWithOverride(a.id);}}}
                    style={{...S.textarea,minHeight:80}}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div style={S.card}>
        <span style={S.label}>Agent log</span>
        <div ref={logRef} style={{background:C.black,borderRadius:6,padding:"14px 16px",height:280,overflowY:"auto",fontFamily:"monospace",fontSize:11,color:"#C5C8C6",lineHeight:1.6}}>
          {logs.length===0
            ? <span style={{color:"#666"}}>No output yet. Run an agent above.</span>
            : logs.map((l)=>(
              <div key={l._id||Math.random()} style={{color:l.type==="agent_start"?"#81A2BE":l.type==="agent_done"?(l.status==="success"?"#B5BD68":"#CC6666"):"#C5C8C6"}}>
                {l.type==="agent_start"?`> ${l.agent} started`:l.type==="agent_done"?`${l.status==="success"?"OK":"XX"} ${l.agent} ${l.status}`:l.line}
              </div>
            ))
          }
          <div ref={logEndRef} />
        </div>
      </div>
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
    </div>
  );
}


// ── Token view ─────────────────────────────────────────────────────────────
function TokenView({data}){
  if(!data) return <div style={{color:C.muted,fontFamily:"Helvetica,sans-serif",fontSize:13}}>Loading...</div>;
  const r=data.token_report||{};
  return(
    <div>
      <h2 style={{...S.h2,marginBottom:20}}>Token Usage</h2>
      {r.daily_trend?.length>0&&(
        <div style={S.card}>
          <span style={S.label}>Last 7 days</span>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:"Helvetica,sans-serif",fontSize:12}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>{["Date","Calls","Tokens","Cost","Cache"].map(h=>(<th key={h} style={{padding:"6px 8px",textAlign:"left",color:C.muted,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase"}}>{h}</th>))}</tr></thead>
            <tbody>{r.daily_trend.map((d,i)=>(<tr key={i} style={{borderBottom:`1px solid ${C.ltgray}`}}><td style={{padding:"8px",fontWeight:500}}>{d.date}</td><td style={{padding:"8px",color:C.muted}}>{d.total_calls}</td><td style={{padding:"8px",color:C.muted}}>{(d.total_tokens||0).toLocaleString()}</td><td style={{padding:"8px",color:C.warm,fontWeight:600}}>${(d.total_cost||0).toFixed(4)}</td><td style={{padding:"8px",color:C.green}}>{d.cache_hits||0}</td></tr>))}</tbody>
          </table>
        </div>
      )}
      {r.by_purpose?.length>0&&(
        <div style={S.card}>
          <span style={S.label}>Top consumers by purpose</span>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:"Helvetica,sans-serif",fontSize:12}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>{["Purpose","Calls","Tokens","Cost"].map(h=>(<th key={h} style={{padding:"6px 8px",textAlign:"left",color:C.muted,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase"}}>{h}</th>))}</tr></thead>
            <tbody>{r.by_purpose.map((p,i)=>(<tr key={i} style={{borderBottom:`1px solid ${C.ltgray}`}}><td style={{padding:"8px",fontWeight:500}}>{p.purpose}</td><td style={{padding:"8px",color:C.muted}}>{p.calls}</td><td style={{padding:"8px",color:C.muted}}>{(p.tokens||0).toLocaleString()}</td><td style={{padding:"8px",color:C.warm,fontWeight:600}}>${(p.cost||0).toFixed(4)}</td></tr>))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Agent label map ────────────────────────────────────────────────────────
const AGENT_DISPLAY = {
  rag_agent:"RAG Ingestion", briefing_agent:"Daily Briefing",
  content_agent:"Content Draft", iso_coach:"ISO 13485 Coach",
  coaching_brief:"Coaching Brief", agent_learning:"Agent Learning",
  hr_agent:"HR Review",
  consulting_agent:"Consulting Agent", ma_intelligence_agent:"M&A Intelligence",
};

// ── Toast notification system ──────────────────────────────────────────────
function Toaster({toasts}){
  return(
    <div style={{position:"fixed",bottom:24,right:24,zIndex:9999,
      display:"flex",flexDirection:"column",gap:8,pointerEvents:"none"}}>
      {toasts.map(t=>{
        const colors={
          running:{bg:"#0A2540",border:"#1A6FA3",icon:"⟳",spin:true},
          success:{bg:"#1F7A6D",border:"#27AE60",icon:"✓",spin:false},
          error:  {bg:"#7B2020",border:"#C0392B",icon:"✕",spin:false},
          info:   {bg:"#0A2540",border:"#3C5470",icon:"·",spin:false},
        }[t.type]||{bg:"#0A2540",border:"#3C5470",icon:"·",spin:false};
        return(
          <div key={t.id} style={{
            background:colors.bg,
            border:`1px solid ${colors.border}`,
            boxShadow:`0 4px 24px rgba(0,0,0,0.4), 0 0 12px ${colors.border}33`,
            borderRadius:8,padding:"10px 16px",
            fontFamily:F.sans,fontSize:12,fontWeight:500,color:"#fff",
            display:"flex",alignItems:"center",gap:10,maxWidth:300,
            animation:"toastSlide 0.25s ease",
          }}>
            <span style={{
              fontSize:14,lineHeight:1,flexShrink:0,
              display:"inline-block",
              animation:colors.spin?"toastSpin 1s linear infinite":"none",
            }}>{colors.icon}</span>
            <span>{t.message}</span>
          </div>
        );
      })}
      <style>{`
        @keyframes toastSlide { from{opacity:0;transform:translateX(20px)} to{opacity:1;transform:none} }
        @keyframes toastSpin  { to{transform:rotate(360deg)} }
      `}</style>
    </div>
  );
}

// ── Main app ───────────────────────────────────────────────────────────────
export default function App(){
  const [active,setActive]=useState("voice");
  const [data,setData]=useState(null);
  const [logs,setLogs]=useState([]);
  const [pendingReview,setPendingReview]=useState(0);
  const [wsReady,setWsReady]=useState(false);
  const [runningAgents,setRunningAgents]=useState(new Set());
  const [toasts,setToasts]=useState([]);
  const wsRef=useRef(null);

  const addToast=useCallback((message,type="info")=>{
    const id=Date.now()+Math.random();
    setToasts(prev=>[...prev.slice(-3),{id,message,type}]);
    setTimeout(()=>setToasts(prev=>prev.filter(t=>t.id!==id)),5000);
  },[]);

  useEffect(()=>{
    const connect=()=>{
      const ws=new WebSocket(WS);
      ws.onopen=()=>setWsReady(true);
      ws.onclose=()=>{setWsReady(false);setTimeout(connect,3000);};
      ws.onmessage=(e)=>{
        try{
          const msg=JSON.parse(e.data);
          msg._id = `${msg.type}-${msg.agent||""}-${msg.ts||""}-${msg.line||""}`;

          // Agent lifecycle notifications
          if(msg.type==="agent_start"){
            const label=AGENT_DISPLAY[msg.agent]||msg.agent;
            addToast(`${label} is running…`,"running");
            setRunningAgents(prev=>new Set([...prev,msg.agent]));
          }
          if(msg.type==="agent_done"){
            const label=AGENT_DISPLAY[msg.agent]||msg.agent;
            const ok=msg.status==="success";
            addToast(`${label} ${ok?"complete":"failed"}`,ok?"success":"error");
            setRunningAgents(prev=>{const s=new Set(prev);s.delete(msg.agent);return s;});
          }

          setLogs(prev=>{
            const tail=prev.slice(-20);
            if(tail.some(m=>m._id===msg._id)) return prev;
            return [...prev.slice(-199),msg];
          });
          if(msg.type==="agent_done") loadData();
        }catch{}
      };
      wsRef.current=ws;
    };
    connect();
    return()=>wsRef.current?.close();
  },[addToast]);

  const loadData=useCallback(()=>{
    fetch(`${API}/api/dashboard`).then(r=>r.json()).then(setData).catch(()=>{});
  },[]);

  useEffect(()=>{loadData();},[loadData]);

  // Poll review queue count every 30s so badge stays current
  useEffect(()=>{
    const poll=()=>fetch(`${API}/api/review/pending`).then(r=>r.json())
      .then(d=>setPendingReview(d.stats?.pending||0)).catch(()=>{});
    poll();
    const t=setInterval(poll,30000);
    return()=>clearInterval(t);
  },[]);

  // Play startup greeting once on first load
  useEffect(()=>{
    fetch(`${API}/api/voice/greet`,{method:"POST"}).catch(()=>{});
  },[]);

  const pendingRef = useRef(new Set());
  const activeRef  = useRef(active);
  useEffect(() => { activeRef.current = active; }, [active]);

  const runAgent=useCallback((id, override="")=>{
    const endpoints={
      rag:"/api/agents/rag", briefing:"/api/agents/briefing",
      content:"/api/agents/content", iso:"/api/agents/iso",
      consulting:"/api/agents/consulting", ma:"/api/agents/ma",
    };
    if(endpoints[id] && !pendingRef.current.has(id)){
      pendingRef.current.add(id);
      fetch(`${API}${endpoints[id]}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({override})})
        .finally(()=>{ setTimeout(()=>pendingRef.current.delete(id), 2000); })
        .catch(()=>{ pendingRef.current.delete(id); });
      // Don't navigate away if voice is active — user is mid-conversation.
      if(activeRef.current !== "voice") setActive("agents");
    }
  },[]);

  const [exitDialog, setExitDialog] = useState(false);

  const handleExit = async () => {
    setExitDialog(false);
    try {
      // Await the response — the backend blocks until TTS finishes before replying.
      await fetch(`${API}/api/shutdown`, { method: "POST" });
    } catch {}
    // TTS is complete by now; close immediately.
    window.athena?.quit?.();
    window.close();
    window.location.replace("about:blank");
  };

  const pages={
    dashboard:<Dashboard data={data}/>,
    briefing: <BriefingView/>,
    voice:    <VoiceView/>,
    content:  <ContentView onGenerate={runAgent}/>,
    coaching: <CoachingView onGenerate={runAgent}/>,
    documents:<DocumentsView/>,
    iso:      <ISOView/>,
    review:   <ReviewView/>,
    agents:   <AgentsView logs={logs} onRun={runAgent} runningAgents={runningAgents}/>,
    hr:       <HRView/>,
    tokens:   <TokenView data={data}/>,
    settings: <SettingsView/>,
  };

  return(
    <div style={S.app}>
      <Toaster toasts={toasts}/>
      <Sidebar active={active} setActive={setActive} runningAgents={runningAgents} pendingReview={pendingReview}/>
      <div style={S.main}>
        {/* Top bar */}
        <div style={S.header}>
          <div>
            <div style={{fontFamily:F.sans,fontSize:14,color:C.ink,fontWeight:600,letterSpacing:"-0.01em"}}>
              {NAV.find(n=>n.id===active)?.label}
            </div>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            {/* Running agents indicator */}
            {runningAgents.size>0&&(
              <div style={{display:"flex",alignItems:"center",gap:6,padding:"3px 10px",
                background:"rgba(26,111,163,0.08)",borderRadius:20,
                border:"1px solid rgba(26,111,163,0.25)",cursor:"pointer"}}
                onClick={()=>setActive("agents")}>
                <div style={{width:6,height:6,borderRadius:"50%",background:C.ocean,
                  animation:"agentPing 1.2s ease-in-out infinite",
                  boxShadow:"0 0 0 2px rgba(26,111,163,0.3)"}}/>
                <span style={{fontFamily:F.sans,fontSize:10,fontWeight:600,color:C.ocean,letterSpacing:"0.03em"}}>
                  {runningAgents.size} running
                </span>
              </div>
            )}
            {/* WS status pill */}
            <div style={{display:"flex",alignItems:"center",gap:5,padding:"3px 10px",
              background:wsReady?"rgba(31,122,109,0.08)":"rgba(192,57,43,0.08)",
              borderRadius:20,border:`1px solid ${wsReady?"rgba(31,122,109,0.2)":"rgba(192,57,43,0.2)"}`}}>
              <div style={{width:6,height:6,borderRadius:"50%",
                background:wsReady?C.teal:C.red,
                boxShadow:wsReady?`0 0 0 2px rgba(31,122,109,0.3)`:"none"}}/>
              <span style={{fontFamily:F.sans,fontSize:10,fontWeight:500,
                color:wsReady?C.teal:C.red,letterSpacing:"0.03em"}}>
                {wsReady?"Live":"Offline"}
              </span>
            </div>
            <style>{`@keyframes agentPing{0%,100%{box-shadow:0 0 0 0px rgba(26,111,163,0.4)}50%{box-shadow:0 0 0 4px rgba(26,111,163,0.1)}}`}</style>
            <button style={{...S.btn("ghost"),padding:"5px 12px",fontSize:10}}
              onClick={loadData}>Refresh</button>
            <button
              onClick={()=>setExitDialog(true)}
              title="Exit Athena"
              style={{
                width:28,height:28,display:"flex",alignItems:"center",justifyContent:"center",
                background:"transparent",border:`1px solid ${C.mist}`,borderRadius:6,
                cursor:"pointer",color:C.fog,fontSize:13,padding:0,
                transition:"color 0.12s,border-color 0.12s",
              }}
              onMouseEnter={e=>{e.currentTarget.style.color=C.red;e.currentTarget.style.borderColor=C.red;}}
              onMouseLeave={e=>{e.currentTarget.style.color=C.fog;e.currentTarget.style.borderColor=C.mist;}}>
              ⏻
            </button>
          </div>
        </div>
        <div style={S.content}>{pages[active]}</div>
      </div>

      {/* Exit confirmation dialog */}
      {exitDialog&&(
        <div style={{
          position:"fixed",inset:0,background:"rgba(10,37,64,0.5)",
          zIndex:2000,display:"flex",alignItems:"center",justifyContent:"center",
        }} onClick={()=>setExitDialog(false)}>
          <div onClick={e=>e.stopPropagation()} style={{
            background:C.pearl,borderRadius:12,padding:"32px 36px",
            maxWidth:380,width:"90%",boxShadow:"0 20px 60px rgba(10,37,64,0.3)",
          }}>
            <div style={{fontFamily:F.sans,fontSize:17,fontWeight:700,color:C.ink,marginBottom:8}}>
              Exit Athena?
            </div>
            <div style={{fontFamily:F.sans,fontSize:13,color:C.fog,marginBottom:24,lineHeight:1.6}}>
              All voice sessions and agent processes will be closed.
            </div>
            <div style={{display:"flex",gap:10,justifyContent:"flex-end"}}>
              <button
                onClick={()=>setExitDialog(false)}
                style={{padding:"8px 20px",background:"transparent",border:`1px solid ${C.mist}`,
                  borderRadius:7,cursor:"pointer",fontFamily:F.sans,fontSize:12,
                  fontWeight:500,color:C.slate}}>
                Cancel
              </button>
              <button
                onClick={handleExit}
                style={{padding:"8px 20px",background:C.navy,border:"none",
                  borderRadius:7,cursor:"pointer",fontFamily:F.sans,fontSize:12,
                  fontWeight:600,color:"#fff",letterSpacing:"0.02em"}}>
                Exit Athena
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
