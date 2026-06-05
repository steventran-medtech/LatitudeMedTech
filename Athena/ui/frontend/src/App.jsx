import { useState, useEffect, useRef, useCallback } from "react";
import SettingsView from "./SettingsView.jsx";
import VoiceView from "./VoiceView.jsx";
import HRView from "./HRView.jsx";
import ISOView from "./ISOView.jsx";
import FileViewer from "./FileViewer.jsx";
import ReviewView from "./ReviewView.jsx";
import MarketingView from "./MarketingView.jsx";
import DeckView from "./DeckView.jsx";
import { useVoiceSession } from "./useVoiceSession.js";

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
  {id:"marketing", label:"Marketing",      group:"work"},
  {id:"decks",     label:"Decks",          group:"work"},
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

function Sidebar({active,setActive,runningAgents,pendingReview,version,onAbout,taskQueue}){
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
      <nav style={{flex:1,padding:"16px 0",overflowY:"auto",minHeight:0}}>
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

      {/* Work queue */}
      <WorkQueuePanel taskQueue={taskQueue||[]} onNavigate={setActive}/>

      {/* Footer */}
      <div style={{padding:"14px 22px",borderTop:"1px solid rgba(255,255,255,0.08)"}}>
        <div style={{fontFamily:F.sans,fontSize:9,color:"rgba(255,255,255,0.3)",lineHeight:1.7}}>
          latitudemedtech.com<br/>
          steven.tran@latitudemedtech.com
        </div>
        {/* Version — click for changelog / About */}
        <button
          onClick={onAbout}
          title="View version & changelog"
          style={{
            marginTop:10,display:"flex",alignItems:"center",gap:6,
            background:"transparent",border:"none",padding:0,cursor:"pointer",
            fontFamily:F.mono,fontSize:9,letterSpacing:"0.04em",
            color:"rgba(255,255,255,0.3)",transition:"color 0.12s",
          }}
          onMouseEnter={e=>e.currentTarget.style.color="rgba(196,146,42,0.9)"}
          onMouseLeave={e=>e.currentTarget.style.color="rgba(255,255,255,0.3)"}>
          <span style={{width:5,height:5,borderRadius:"50%",background:"#1F7A6D",
            boxShadow:"0 0 5px rgba(31,122,109,0.6)",display:"inline-block"}}/>
          {version?.version ? `v${version.version}` : "v—"}
          {version?.channel && version.channel!=="stable" &&
            <span style={{opacity:0.7}}>· {version.channel}</span>}
        </button>
      </div>
      <style>{`@keyframes badgePulse{0%,100%{box-shadow:0 0 4px #1A6FA366}50%{box-shadow:0 0 10px #1A6FA3aa}}`}</style>
    </div>
  );
}

// ── McKinsey-quality Markdown renderer ────────────────────────────────────────
const LINK_STYLE = { color: C.ocean, textDecoration: "none",
  borderBottom: `1px solid ${C.ocean}55`, fontWeight: 500 };

function renderInline(text) {
  // Markdown links [text](url), bare URLs, bold, italic, inline code.
  // Link alternatives come first so a URL inside [..](..) is consumed as one token.
  const parts = text.split(
    /(\[[^\]]+\]\([^)\s]+\)|https?:\/\/[^\s)\]]+|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g
  );
  return parts.map((p, i) => {
    if (!p) return null;
    const md = p.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/);
    if (md)
      return <a key={i} href={md[2]} target="_blank" rel="noopener noreferrer"
        style={LINK_STYLE}>{md[1]}</a>;
    if (/^https?:\/\//.test(p))
      return <a key={i} href={p} target="_blank" rel="noopener noreferrer"
        style={LINK_STYLE}>{p.replace(/^https?:\/\/(www\.)?/, "")}</a>;
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

// ── Title-case helper (underscore filenames → readable labels) ───────────
const UPPER_WORDS = new Set(["qa","ra","qms","iso","fda","eu","us","ivd","samd","vp","hr","md","ii","iii","iv","llc","inc"]);
function toTitleCase(str){
  return str.split(" ").map(w=>
    UPPER_WORDS.has(w.toLowerCase()) ? w.toUpperCase()
    : w.charAt(0).toUpperCase()+w.slice(1)
  ).join(" ");
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
        flex:1, minWidth:0, padding:"9px 12px",
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
        }}>{title}</div>
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
  const link = {background:"none",border:"none",cursor:"pointer",
    fontFamily:F.sans,fontSize:10,color:C.fog,padding:"2px 5px",lineHeight:1};
  return(
    <div style={{display:"flex",alignItems:"center",gap:2,padding:"5px 10px",
      background:"rgba(26,111,163,0.06)",borderRadius:6,marginBottom:8,
      borderLeft:`2px solid ${C.ocean}`}}>
      <span style={{fontFamily:F.sans,fontSize:11,color:C.ocean,fontWeight:600,flex:1}}>
        {count} selected
      </span>
      <button onClick={onSelectAll} style={link}>all</button>
      <button onClick={onClear}     style={link}>none</button>
      <span style={{color:C.mist,fontSize:10}}>·</span>
      <button onClick={onDeleteSelected}
        style={{...link,color:C.red,fontWeight:600}}>
        delete
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
function fmtDur(s){
  const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;
  if(h>0) return `${h}h ${m}m`;
  if(m>0) return `${m}m ${String(sec).padStart(2,"0")}s`;
  return `${sec}s`;
}

function Dashboard({data}){
  const [history,setHistory]=useState([]);
  const [ts,setTs]=useState(null);
  const [hourlyDay,setHourlyDay]=useState("today");  // which day the hourly chart shows
  const [kbGrowth,setKbGrowth]=useState([]);
  const [kbTotal,setKbTotal]=useState(0);
  const [companyKb,setCompanyKb]=useState(null);
  const [sessions,setSessions]=useState([]);
  const [recentDecks,setRecentDecks]=useState([]);
  useEffect(()=>{
    fetch(`${API}/api/dashboard/history?days=30`).then(r=>r.json()).then(d=>setHistory(d.daily||[])).catch(()=>{});
    fetch(`${API}/api/dashboard/knowledge-growth?days=90`).then(r=>r.json()).then(d=>{setKbGrowth(d.daily||[]);setKbTotal(d.total||0);}).catch(()=>{});
    fetch(`${API}/api/hr/skills`).then(r=>r.json()).then(d=>{
      const skills=Object.values(d.skills||{});
      const totalChunks=skills.reduce((acc,s)=>acc+(s.total_chunks||0),0);
      const domains=new Set(skills.flatMap(s=>s.domains||[]));
      setCompanyKb({totalChunks,domains:domains.size});
    }).catch(()=>{});
    fetch(`${API}/api/sessions?limit=15`).then(r=>r.json()).then(d=>setSessions(d.sessions||[])).catch(()=>{});
    fetch(`${API}/api/decks`).then(r=>r.json()).then(d=>setRecentDecks((d.decks||[]).slice(0,5))).catch(()=>{});
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
      {/* Knowledge accumulation */}
      {(kbGrowth.length>1||companyKb)&&(
        <div style={{...S.card,marginBottom:24}}>
          <span style={S.label}>Knowledge Accumulation · Company-wide · 90 days</span>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:12,marginTop:12,marginBottom:kbGrowth.length>1?20:0}}>
            {[
              {label:"Total KB Items",   value:(kbTotal||0).toLocaleString(),                                         color:C.teal},
              {label:"Total Chunks",     value:companyKb?(companyKb.totalChunks||0).toLocaleString():"—",             color:C.ocean},
              {label:"Domains Covered",  value:companyKb?(companyKb.domains||0):"—",                                  color:C.slate},
            ].map(s=>(<div key={s.label} style={{background:C.cloud,borderRadius:7,padding:"12px 14px"}}>
              <div style={{...S.stat,fontSize:22,color:s.color}}>{s.value}</div>
              <div style={S.statLabel}>{s.label}</div>
            </div>))}
          </div>
          {kbGrowth.length>1&&<Sparkline data={kbGrowth} valueKey="cumulative" color={C.teal} label="Cumulative items ingested"/>}
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
      {recentDecks.length>0&&(
        <div style={{...S.card,marginBottom:16}}>
          <span style={S.label}>Recent Decks</span>
          {recentDecks.map((d,i)=>{
            const base=d.filename.replace(/\.pptx$/i,"");
            const parts=base.split("_");
            const label=parts.length>=3?parts.slice(2).join(" ").replace(/_/g," "):base;
            const date=parts.length>=1&&/^\d{8}$/.test(parts[0])?`${parts[0].slice(0,4)}-${parts[0].slice(4,6)}-${parts[0].slice(6,8)}`:"";
            return(
              <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"8px 0",borderBottom:i<recentDecks.length-1?`1px solid ${C.ltgray}`:"none"}}>
                <div>
                  <span style={{fontFamily:"Helvetica,sans-serif",fontSize:12,color:C.slate,fontWeight:500,textTransform:"capitalize"}}>{label||d.filename}</span>
                  {date&&<span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.muted,marginLeft:8}}>{date}</span>}
                </div>
                <a href={`${API}/api/decks/download/${encodeURIComponent(d.filename)}`} download={d.filename}
                   style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.ocean,fontWeight:600,textDecoration:"none"}}>↓ pptx</a>
              </div>
            );
          })}
        </div>
      )}
      {sessions.length>0&&(
        <div style={{...S.card,marginTop:16}}>
          <span style={S.label}>Voice Sessions</span>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:"Helvetica,sans-serif",fontSize:12,marginTop:12}}>
            <thead>
              <tr style={{borderBottom:`1px solid ${C.border}`}}>
                {["Date","Started","Duration","Queries"].map(h=>(
                  <th key={h} style={{padding:"6px 8px",textAlign:"left",color:C.muted,fontWeight:600,fontSize:10,letterSpacing:"0.08em",textTransform:"uppercase"}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sessions.map((s,i)=>{
                const d=new Date(s.started_at);
                return(
                  <tr key={i} style={{borderBottom:`1px solid ${C.ltgray}`}}>
                    <td style={{padding:"8px",color:C.slate}}>{d.toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})}</td>
                    <td style={{padding:"8px",color:C.muted}}>{d.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</td>
                    <td style={{padding:"8px",color:C.blue,fontWeight:500}}>{fmtDur(s.duration_secs||0)}</td>
                    <td style={{padding:"8px",color:C.muted}}>{s.queries||0}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
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
        <div style={{width:280,flexShrink:0}}>
          <BulkBar count={ms.checked.size} onDeleteSelected={deleteSelected} onClear={ms.clear} onSelectAll={()=>ms.selectAll(allIds)}/>
          {briefings.map(b=>(<FileItem key={b.filename} title={b.title||b.date} subtitle={b.date} selected={selected===b.filename} checked={ms.checked.has(b.filename)} onCheck={()=>ms.toggle(b.filename)} onSelect={()=>{setSelected(b.filename);setEditing(false);}} onDelete={()=>deleteFile(b.filename)} onEdit={()=>{setSelected(b.filename);setEditing(true);}}/>))}
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
        <div style={{width:280,flexShrink:0}}>
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
      <h2 style={{...S.h2,marginBottom:20}}>Client Analysis</h2>
      <div style={{...S.card,display:"flex",gap:12,alignItems:"center",marginBottom:20}}>
        <input value={client} onChange={e=>setClient(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runBrief()} placeholder="Client name, LinkedIn URL, or topic" style={{...S.input,flex:1}}/>
        <button style={S.btn()} onClick={runBrief}>Generate Brief</button>
        {content&&<button style={S.btn("teal")} onClick={exportDoc}>Save as Word Doc</button>}
        {status&&<span style={{fontFamily:"Helvetica,sans-serif",fontSize:11,color:C.teal}}>{status}</span>}
      </div>
      <div style={{display:"flex",gap:20}}>
        <div style={{width:280,flexShrink:0}}>
          <BulkBar count={ms.checked.size} onDeleteSelected={deleteSelected} onClear={ms.clear} onSelectAll={()=>ms.selectAll(allIds)}/>
          {briefs.map(b=>{
            const noExt=b.filename.replace(/\.md$/,"");
            const dated=/^(\d{4}-\d{2}-\d{2})_(.+)$/.exec(noExt);
            const briefTitle=toTitleCase((dated?dated[2]:noExt.replace(/^brief_/,"")).replace(/_/g," "));
            const briefDate=dated?dated[1]:"";
            return(<FileItem key={b.filename} title={briefTitle} subtitle={briefDate} selected={selected===b.filename} checked={ms.checked.has(b.filename)} onCheck={()=>ms.toggle(b.filename)} onSelect={()=>{setSelected(b.filename);setEditing(false);}} onDelete={()=>deleteFile(b.filename)} onEdit={()=>{setSelected(b.filename);setEditing(true);}}/>);
          })}
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
  const deleteDoc=async(filename,folder)=>{
    await fetch(`${API}/api/files/delete`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filename,folder:folder||"documents"})});
    ms.clear(); load();
  };
  const deleteSelected=async()=>{
    if(!ms.checked.size) return;
    if(!window.confirm(`Delete ${ms.checked.size} document(s)?`)) return;
    const folderOf=f=>(docs.find(d=>d.filename===f)?.folder)||"documents";
    await bulkDelete([...ms.checked].map(f=>({folder:folderOf(f),filename:f})));
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
              <button style={S.btn("teal")} onClick={()=>setViewing(d)}>View</button>
              {d.filename.toLowerCase().endsWith(".docx")&&(
                <button style={{...S.btn(),background:C.slate}} onClick={()=>openDoc(d.filename)}>Open in Word</button>
              )}
              <button style={{...S.btn("ghost"),color:C.red}} onClick={()=>deleteDoc(d.filename,d.folder)}>&#x2715;</button>
            </div>
          </div>
        ))
      }
      {viewing&&<FileViewer folder={viewing.folder||"documents"} filename={viewing.filename} onClose={()=>setViewing(null)}/>}
    </div>
  );
}

// ── Agents ─────────────────────────────────────────────────────────────────
function AgentsView({logs,onRun,runningAgents}){
  const logRef    = useRef(null);
  const logEndRef = useRef(null);

  useEffect(()=>{
    if(logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  },[logs]);

  // Derive running state from the global runningAgents Set (stays in sync across tabs)
  const running = {};
  if(runningAgents){
    runningAgents.forEach(a=>{ running[a]=true; });
    // Also map short IDs used in the agent cards
    const MAP={rag:"rag_agent",briefing:"briefing_agent",content:"content_agent",iso:"iso_coach",consulting:"consulting_agent",ma:"ma_intelligence_agent",marketing:"marketing_agent"};
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
    {id:"marketing",   label:"Marketing Agent",        desc:"Guerilla brief, plan, outreach, events", color:"#5B7FA6"},
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
  hr_agent:"HR Review", skills_profile:"Skills Profile",
  consulting_agent:"Consulting Agent", ma_intelligence_agent:"M&A Intelligence",
  marketing_agent:"Marketing Agent",
  deck_agent:     "Deck Builder",
};

// Estimated completion times in seconds (mirrors _AGENT_ETA_SECONDS in voice_bridge.py)
const AGENT_ETA_SECONDS = {
  briefing_agent:        120,
  content_agent:         240,
  rag_agent:              60,
  iso_coach:              60,
  coaching_brief:        120,
  consulting_agent:      180,
  ma_intelligence_agent: 210,
  marketing_agent:       120,
  agent_learning:        180,
  hr_agent:               90,
  skills_profile:         60,
  deck_agent:            300,
};

// Maps agent IDs to the tab to navigate to when the task completes
const AGENT_TAB = {
  briefing_agent:        "briefing",
  content_agent:         "content",
  marketing_agent:       "marketing",
  iso_coach:             "iso",
  coaching_brief:        "review",
  consulting_agent:      "documents",
  ma_intelligence_agent: "documents",
  deck_agent:            "decks",
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
// ── About / Version panel ─────────────────────────────────────────────────────
function AboutModal({version,onClose}){
  // Strip the changelog's top "# Changelog" H1 — the modal already has a title.
  const changelog=(version?.changelog||"").replace(/^#\s+Changelog\s*\n/,"").trim();
  return(
    <div onClick={onClose} style={{
      position:"fixed",inset:0,background:"rgba(10,37,64,0.5)",
      zIndex:2000,display:"flex",alignItems:"center",justifyContent:"center",padding:24,
    }}>
      <div onClick={e=>e.stopPropagation()} style={{
        background:C.pearl,borderRadius:20,maxWidth:640,width:"100%",
        maxHeight:"82vh",display:"flex",flexDirection:"column",
        boxShadow:"0 20px 60px rgba(10,37,64,0.3)",overflow:"hidden",
      }}>
        {/* Header */}
        <div style={{padding:"24px 30px 18px",borderBottom:`1px solid ${C.mist}`,background:C.navy}}>
          <div style={{display:"flex",alignItems:"baseline",justifyContent:"space-between"}}>
            <div>
              <div style={{fontFamily:F.serif,fontSize:22,color:"#fff",fontWeight:400,lineHeight:1}}>Athena</div>
              <div style={{fontFamily:F.sans,fontSize:10,color:"rgba(255,255,255,0.5)",marginTop:5,letterSpacing:"0.06em"}}>
                Latitude MedTech · AI Operating System
              </div>
            </div>
            <div style={{textAlign:"right"}}>
              <div style={{fontFamily:F.mono,fontSize:18,color:"#fff",fontWeight:600}}>
                v{version?.version||"—"}
              </div>
              <div style={{fontFamily:F.sans,fontSize:10,color:"rgba(255,255,255,0.5)",marginTop:3}}>
                {version?.channel||""}{version?.codename?` · "${version.codename}"`:""}
              </div>
              {version?.released&&<div style={{fontFamily:F.sans,fontSize:9,color:"rgba(255,255,255,0.4)",marginTop:2}}>
                released {version.released}
              </div>}
            </div>
          </div>
        </div>
        {/* Changelog body */}
        <div style={{padding:"4px 30px 24px",overflowY:"auto",flex:1}}>
          {changelog
            ? <MarkdownView content={changelog}/>
            : <div style={{fontFamily:F.sans,fontSize:13,color:C.fog,padding:"20px 0"}}>
                Changelog unavailable.
              </div>}
        </div>
        {/* Footer */}
        <div style={{padding:"14px 30px",borderTop:`1px solid ${C.mist}`,display:"flex",justifyContent:"flex-end"}}>
          <button onClick={onClose} style={{padding:"8px 22px",background:C.navy,border:"none",
            borderRadius:7,cursor:"pointer",fontFamily:F.sans,fontSize:12,fontWeight:600,
            color:"#fff",letterSpacing:"0.02em"}}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ── Work queue timer ───────────────────────────────────────────────────────
function CountdownTimer({ startedAt, estSeconds, status }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (status !== "running") return;
    const t = setInterval(() => setNow(Date.now()), 5000);
    return () => clearInterval(t);
  }, [status]);
  if (status !== "running") return null;
  const rem = Math.max(0, estSeconds - (now - startedAt) / 1000);
  if (rem < 15) return (
    <span style={{fontFamily:F.sans,fontSize:9,color:"#1F7A6D",flexShrink:0}}>soon</span>
  );
  return (
    <span style={{fontFamily:F.sans,fontSize:9,color:"rgba(255,255,255,0.3)",flexShrink:0}}>
      ~{Math.ceil(rem / 60)}m
    </span>
  );
}

// ── Work queue sidebar panel ───────────────────────────────────────────────
function WorkQueuePanel({ taskQueue, onNavigate }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 10000);
    return () => clearInterval(t);
  }, []);
  const visible = taskQueue.filter(t =>
    t.status === "running" ||
    t.status === "awaiting_review" ||
    (t.doneAt && now - t.doneAt < 10 * 60 * 1000)
  );
  if (!visible.length) return null;

  const DOT = {
    running:          { color:"#1A6FA3", anim:"agentPing 1.2s ease-in-out infinite" },
    done:             { color:"#1F7A6D", anim:"none" },
    awaiting_review:  { color:"#C4922A", anim:"badgePulse 2s ease-in-out infinite" },
    failed:           { color:"#C0392B", anim:"none" },
  };

  return (
    <div style={{borderTop:"1px solid rgba(255,255,255,0.08)",flexShrink:0,
      maxHeight:220,overflowY:"auto",padding:"12px 16px 4px"}}>
      <div style={{fontFamily:F.sans,fontSize:8,fontWeight:700,letterSpacing:"0.16em",
        textTransform:"uppercase",color:"rgba(255,255,255,0.28)",marginBottom:8}}>
        Working On
      </div>
      {visible.map(t => {
        const dot = DOT[t.status] ?? DOT.done;
        // Items pending human review route to the Review queue; everything else
        // goes to the agent's own output tab.
        const target = t.status === "awaiting_review" ? "review" : AGENT_TAB[t.agentId];
        const clickable = t.status !== "running" && target;
        return (
          <div key={t.id}
            onClick={() => clickable && onNavigate(target)}
            style={{
              display:"flex", alignItems:"flex-start", gap:8, marginBottom:8,
              cursor: clickable ? "pointer" : "default",
              opacity: t.status === "failed" ? 0.55 : 1,
            }}>
            {/* Status dot */}
            <div style={{
              width:6, height:6, borderRadius:"50%", marginTop:3, flexShrink:0,
              background:dot.color, animation:dot.anim,
              boxShadow: t.status==="running" ? `0 0 0 2px ${dot.color}33` : "none",
            }}/>
            <div style={{flex:1,minWidth:0}}>
              <div style={{fontFamily:F.sans,fontSize:11,color:"rgba(255,255,255,0.75)",
                lineHeight:1.3,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                {t.label}
              </div>
              {t.context && (
                <div style={{fontFamily:F.sans,fontSize:9,color:"rgba(255,255,255,0.35)",
                  marginTop:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                  {t.context}
                </div>
              )}
              {t.status==="done" && (
                <div style={{fontFamily:F.sans,fontSize:9,color:"#1F7A6D",marginTop:1}}>
                  ready{clickable?" · view →":""}
                </div>
              )}
              {t.status==="awaiting_review" && (
                <div style={{fontFamily:F.sans,fontSize:9,color:"#C4922A",marginTop:1}}>
                  awaiting your review →
                </div>
              )}
            </div>
            <CountdownTimer startedAt={t.startedAt} estSeconds={t.estSeconds} status={t.status}/>
          </div>
        );
      })}
    </div>
  );
}

const VOICE_BADGE = {
  idle:      { color: "#7B90A0", pulse: false },
  loading:   { color: "#C4922A", pulse: true  },
  listening: { color: "#1A6FA3", pulse: true  },
  awake:     { color: "#C4922A", pulse: false },
  thinking:  { color: "#7B3FA6", pulse: true  },
  speaking:  { color: "#1F7A6D", pulse: false },
  stopped:   { color: "#C0392B", pulse: false },
};

function VoiceStatusBadge({ voice, onNavigate }) {
  const { running, state } = voice;
  const cfg = VOICE_BADGE[state] ?? VOICE_BADGE.idle;
  const label = running
    ? (state ? state.charAt(0).toUpperCase() + state.slice(1) : "Live")
    : "Offline";
  return (
    <div
      onClick={onNavigate}
      title="Athena Voice"
      style={{
        display:"flex", alignItems:"center", gap:5,
        padding:"3px 10px", borderRadius:20, cursor:"pointer",
        background: running ? `${cfg.color}14` : "transparent",
        border:`1px solid ${running ? cfg.color+"44" : C.mist}`,
        transition:"border-color 0.2s, background 0.2s",
      }}
    >
      <div style={{
        width:6, height:6, borderRadius:"50%",
        background: running ? cfg.color : C.fog,
        animation: (running && cfg.pulse) ? "agentPing 1.2s ease-in-out infinite" : "none",
        boxShadow: running ? `0 0 0 2px ${cfg.color}33` : "none",
      }}/>
      <span style={{
        fontFamily:F.sans, fontSize:10, fontWeight:600,
        color: running ? cfg.color : C.fog, letterSpacing:"0.03em",
      }}>
        {label}
      </span>
    </div>
  );
}

export default function App(){
  const [active,setActive]=useState("voice");
  const [data,setData]=useState(null);
  const [logs,setLogs]=useState([]);
  const [pendingReview,setPendingReview]=useState(0);
  const [wsReady,setWsReady]=useState(false);
  const [runningAgents,setRunningAgents]=useState(new Set());
  const [toasts,setToasts]=useState([]);
  const [version,setVersion]=useState(null);
  const [aboutOpen,setAboutOpen]=useState(false);
  const [shuttingDown,setShuttingDown]=useState(false);
  const wsRef=useRef(null);
  const voice=useVoiceSession();
  const [taskQueue,setTaskQueue]=useState([]);
  const voiceRunningRef=useRef(false);
  useEffect(()=>{voiceRunningRef.current=voice.running;},[voice.running]);

  const addToast=useCallback((message,type="info")=>{
    const id=Date.now()+Math.random();
    setToasts(prev=>[...prev.slice(-3),{id,message,type}]);
    setTimeout(()=>setToasts(prev=>prev.filter(t=>t.id!==id)),5000);
  },[]);

  useEffect(()=>{
    let closed=false;        // set on cleanup so onclose doesn't reconnect a dead effect
    let reconnectTimer=null; // tracked so cleanup can cancel a pending reconnect
    const connect=()=>{
      if(closed) return;
      const ws=new WebSocket(WS);
      ws.onopen=()=>setWsReady(true);
      ws.onclose=()=>{setWsReady(false);if(!closed)reconnectTimer=setTimeout(connect,3000);};
      ws.onmessage=(e)=>{
        try{
          const msg=JSON.parse(e.data);
          msg._id = `${msg.type}-${msg.agent||""}-${msg.ts||""}-${msg.line||""}`;

          // Agent lifecycle — task queue + running badge
          if(msg.type==="agent_start"){
            const label=AGENT_DISPLAY[msg.agent]||msg.agent;
            addToast(`${label} is running…`,"running");
            setRunningAgents(prev=>new Set([...prev,msg.agent]));
            const now=Date.now();
            setTaskQueue(prev=>{
              // Remove stale completed entries for this agent so they don't
              // show alongside the new running entry in the Working On panel.
              const pruned=prev.filter(t=>!(t.agentId===msg.agent&&t.status!=="running"));
              if(pruned.some(t=>t.agentId===msg.agent&&t.status==="running")) return prev;
              return [...pruned,{
                id:`${msg.agent}-${now}`,
                agentId:msg.agent,
                label,
                context:msg.context||"",
                status:"running",
                startedAt:now,
                estSeconds:AGENT_ETA_SECONDS[msg.agent]||120,
                doneAt:null,
              }];
            });
          }
          if(msg.type==="agent_done"){
            const label=AGENT_DISPLAY[msg.agent]||msg.agent;
            const finalStatus=msg.status==="awaiting_review"?"awaiting_review":msg.status==="success"?"done":"failed";
            const ok=msg.status==="success"||msg.status==="awaiting_review";
            // Enhanced toast for deck_agent: include title and slide count if available
            let toastMsg;
            if(msg.status==="awaiting_review"){
              toastMsg=`${label} awaiting your review`;
            } else if(ok && msg.agent==="deck_agent" && msg.title){
              toastMsg=`Deck ready: ${msg.title}${msg.slide_count?` (${msg.slide_count} slides)`:""}`;
            } else if(ok){
              toastMsg=`${label} ready for review`;
            } else {
              toastMsg=`${label} failed`;
            }
            addToast(toastMsg,ok?"success":"error");
            setRunningAgents(prev=>{const s=new Set(prev);s.delete(msg.agent);return s;});
            const doneAt=Date.now();
            setTaskQueue(prev=>prev.map(t=>
              t.agentId===msg.agent&&t.status==="running"
                ?{...t,status:finalStatus,doneAt}
                :t
            ));
            // Auto-remove completed tasks after 10 minutes
            setTimeout(()=>setTaskQueue(prev=>prev.filter(t=>!(t.agentId===msg.agent&&t.doneAt===doneAt))),10*60*1000);
            // Spoken notification if Athena is live
            if(voiceRunningRef.current&&ok){
              fetch(`${API}/api/voice/notify`,{
                method:"POST",headers:{"Content-Type":"application/json"},
                body:JSON.stringify({text:`Your ${label} is ready for review.`}),
              }).catch(()=>{});
            }
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
    return()=>{closed=true;if(reconnectTimer)clearTimeout(reconnectTimer);wsRef.current?.close();};
  },[addToast]);

  const loadData=useCallback(()=>{
    fetch(`${API}/api/dashboard`).then(r=>r.json()).then(setData).catch(()=>{});
  },[]);

  useEffect(()=>{loadData();},[loadData]);

  // Load app version once (for the sidebar badge + About panel)
  useEffect(()=>{
    fetch(`${API}/api/version`).then(r=>r.json()).then(setVersion).catch(()=>{});
  },[]);

  // Poll review queue count every 30s so badge stays current
  useEffect(()=>{
    const poll=()=>fetch(`${API}/api/review/pending`).then(r=>r.json())
      .then(d=>setPendingReview(d.stats?.pending||0)).catch(()=>{});
    poll();
    const t=setInterval(poll,30000);
    return()=>clearInterval(t);
  },[]);

  // Greeting moved to VoiceView — plays before mic opens to avoid self-recording

  const pendingRef = useRef(new Set());
  const activeRef  = useRef(active);
  useEffect(() => { activeRef.current = active; }, [active]);

  const runAgent=useCallback((id, override="")=>{
    const endpoints={
      rag:"/api/agents/rag", briefing:"/api/agents/briefing",
      content:"/api/agents/content", iso:"/api/agents/iso",
      consulting:"/api/agents/consulting", ma:"/api/agents/ma",
      marketing:"/api/agents/marketing",
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
  const shuttingDownRef = useRef(false);

  // Fire goodbye TTS when the Chrome window is closed via the X button.
  // sendBeacon survives page unload; the guard prevents double-fire when
  // handleExit already awaited the full /api/shutdown response.
  useEffect(() => {
    const onUnload = () => {
      if (!shuttingDownRef.current) {
        navigator.sendBeacon(`${API}/api/shutdown`);
      }
    };
    window.addEventListener("beforeunload", onUnload);
    return () => window.removeEventListener("beforeunload", onUnload);
  }, []);

  const handleExit = async () => {
    if (shuttingDown) return;   // guard: double-press of the off button
    shuttingDownRef.current = true;
    setShuttingDown(true);
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
    voice:    <VoiceView voice={voice}/>,
    content:  <ContentView onGenerate={runAgent}/>,
    coaching: <CoachingView onGenerate={runAgent}/>,
    marketing:<MarketingView runningAgents={runningAgents}/>,
    decks:    <DeckView runningAgents={runningAgents}/>,
    documents:<DocumentsView/>,
    iso:      <ISOView runningAgents={runningAgents}/>,
    review:   <ReviewView/>,
    agents:   <AgentsView logs={logs} onRun={runAgent} runningAgents={runningAgents}/>,
    hr:       <HRView runningAgents={runningAgents}/>,
    tokens:   <TokenView data={data}/>,
    settings: <SettingsView/>,
  };

  return(
    <div style={S.app}>
      <Toaster toasts={toasts}/>
      <Sidebar active={active} setActive={setActive} runningAgents={runningAgents} pendingReview={pendingReview} version={version} onAbout={()=>setAboutOpen(true)} taskQueue={taskQueue}/>
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
            <VoiceStatusBadge voice={voice} onNavigate={()=>setActive("voice")}/>
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
              onClick={()=>!shuttingDown&&setExitDialog(true)}
              title={shuttingDown?"Shutting down…":"Exit Athena"}
              disabled={shuttingDown}
              style={{
                width:28,height:28,display:"flex",alignItems:"center",justifyContent:"center",
                background:"transparent",border:`1px solid ${C.mist}`,borderRadius:6,
                cursor:shuttingDown?"not-allowed":"pointer",color:shuttingDown?C.fog:C.fog,fontSize:13,padding:0,
                opacity:shuttingDown?0.4:1,
                transition:"color 0.12s,border-color 0.12s,opacity 0.12s",
              }}
              onMouseEnter={e=>{if(!shuttingDown){e.currentTarget.style.color=C.red;e.currentTarget.style.borderColor=C.red;}}}
              onMouseLeave={e=>{e.currentTarget.style.color=C.fog;e.currentTarget.style.borderColor=C.mist;}}>
              ⏻
            </button>
          </div>
        </div>
        <div style={S.content}>{pages[active]}</div>
      </div>

      {/* About / version + changelog */}
      {aboutOpen&&<AboutModal version={version} onClose={()=>setAboutOpen(false)}/>}

      {/* Exit confirmation dialog */}
      {exitDialog&&(
        <div style={{
          position:"fixed",inset:0,background:"rgba(10,37,64,0.5)",
          zIndex:2000,display:"flex",alignItems:"center",justifyContent:"center",
        }} onClick={()=>setExitDialog(false)}>
          <div onClick={e=>e.stopPropagation()} style={{
            background:C.pearl,borderRadius:20,padding:"32px 36px",
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
