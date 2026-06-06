import { useEffect, useRef, useState } from "react";

const API = "http://localhost:8000";

// Full ISO 13485:2016 clause list
const CLAUSES_13485 = [
  ["4.1","General QMS Requirements"],["4.2","Documentation Requirements"],
  ["4.2.3","Medical Device File"],["4.2.4","Document Control"],["4.2.5","Records Control"],
  ["5.1","Management Commitment"],["5.2","Customer Focus"],["5.3","Quality Policy"],
  ["5.4","Planning"],["5.5","Responsibility and Authority"],["5.6","Management Review"],
  ["6.1","Resource Management"],["6.2","Human Resources"],["6.3","Infrastructure"],
  ["6.4","Work Environment"],["7.1","Planning of Product Realization"],
  ["7.2","Customer-Related Processes"],["7.3","Design and Development"],
  ["7.4","Purchasing"],["7.5","Production and Service Provision"],
  ["7.6","Control of Monitoring Equipment"],["8.1","Measurement, Analysis and Improvement"],
  ["8.2","Monitoring and Measurement"],["8.2.1","Feedback"],["8.2.2","Internal Audit"],
  ["8.2.3","Process Monitoring"],["8.2.4","Product Monitoring"],
  ["8.3","Control of Nonconforming Product"],["8.4","Analysis of Data"],
  ["8.5","Improvement — CAPA"],["8.5.2","Corrective Action"],["8.5.3","Preventive Action"],
];

// ISO 14971:2019 Risk Management clause list
const CLAUSES_14971 = [
  ["14971.4",   "General Requirements for a Risk Management System"],
  ["14971.5",   "Risk Analysis"],
  ["14971.5.2", "Intended Use and Reasonably Foreseeable Misuse"],
  ["14971.5.3", "Hazard Identification"],
  ["14971.5.4", "Estimation of Risk"],
  ["14971.6",   "Risk Evaluation"],
  ["14971.7",   "Risk Control"],
  ["14971.7.1", "Risk Control Option Analysis"],
  ["14971.7.2", "Implementation of Risk Control Measures"],
  ["14971.7.3", "Residual Risk Evaluation After Risk Control"],
  ["14971.7.4", "Benefit-Risk Analysis"],
  ["14971.7.5", "Risks Arising from Risk Control Measures"],
  ["14971.7.6", "Completeness of Risk Control"],
  ["14971.8",   "Evaluation of Overall Residual Risk"],
  ["14971.9",   "Risk Management Review"],
  ["14971.10",  "Production and Post-Production Activities"],
];

// Combined for datalist autocomplete
const CLAUSES = [...CLAUSES_13485, ...CLAUSES_14971];

const C = {
  navy:   "#0A2540", ocean:  "#1A6FA3", gold:   "#C4922A",
  teal:   "#1F7A6D", cloud:  "#F8FAFC", sand:   "#F2EDE6",
  pearl:  "#FFFFFF", mist:   "#DDE4EB", fog:    "#7B90A0",
  slate:  "#3C5470", ink:    "#0A2540", red:    "#C0392B",
  // legacy aliases used in MarkdownView
  black: "#0A2540", blue: "#1A6FA3", border: "#DDE4EB",
  muted: "#7B90A0", white: "#FFFFFF", ltgray: "#EDF1F5", cream: "#F8FAFC",
};

// ── Simple multiselect hook ───────────────────────────────────────────────
function useSelect() {
  const [checked, setChecked] = useState(new Set());
  return {
    checked,
    toggle:    (id)  => setChecked(p => { const s = new Set(p); s.has(id) ? s.delete(id) : s.add(id); return s; }),
    clear:     ()    => setChecked(new Set()),
    selectAll: (ids) => setChecked(new Set(ids)),
    has:       (id)  => checked.has(id),
    size:      checked.size,
  };
}

// ── Bulk action bar ───────────────────────────────────────────────────────
function BulkBar({ count, total, onDeleteSelected, onSelectAll, onClear }) {
  if (count === 0) return null;
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      padding: "8px 12px", marginBottom: 8,
      background: "#EEF5FB", border: `1px solid ${C.ocean}33`, borderRadius: 6,
    }}>
      <span style={{ fontFamily: "Inter,sans-serif", fontSize: 11,
        fontWeight: 600, color: C.ocean, flex: 1 }}>
        {count} selected
      </span>
      <button onClick={onSelectAll} style={actionBtn(C.fog)}>All ({total})</button>
      <button onClick={onClear}     style={actionBtn(C.fog)}>None</button>
      <button onClick={onDeleteSelected} style={actionBtn(C.red)}>
        Delete {count}
      </button>
    </div>
  );
}

// ── Lesson list item with checkbox + edit + delete ────────────────────────
function LessonItem({ clause, title, date, active, checked, onSelect, onCheck, onEdit, onDelete }) {
  const [hover, setHover] = useState(false);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}>

      {/* Always-visible checkbox */}
      <input type="checkbox" checked={checked} onChange={e => { e.stopPropagation(); onCheck(); }}
        style={{ width: 14, height: 14, cursor: "pointer", accentColor: C.ocean, flexShrink: 0 }}/>

      {/* Main card */}
      <div onClick={onSelect} style={{
        flex: 1, padding: "9px 12px", cursor: "pointer",
        background: active ? "#EEF6F5" : hover ? "#F4F7FA" : C.pearl,
        border: `1px solid ${active ? C.teal : C.mist}`,
        borderLeft: active ? `3px solid ${C.teal}` : `1px solid ${C.mist}`,
        borderRadius: 7, transition: "background 0.1s",
      }}>
        <div style={{ fontFamily: "Inter,sans-serif", fontSize: 12,
          fontWeight: active ? 700 : 500, color: active ? C.navy : C.slate }}>
          §{clause}
        </div>
        <div style={{ fontFamily: "Inter,sans-serif", fontSize: 10, color: C.fog, marginTop: 2 }}>
          {title || "—"}
        </div>
        <div style={{ fontFamily: "Inter,sans-serif", fontSize: 9, color: C.fog, marginTop: 1 }}>
          {date}
        </div>
      </div>

      {/* Edit + Delete — dim at rest, full on hover */}
      <div style={{ display: "flex", gap: 3, opacity: hover ? 1 : 0.25, transition: "opacity 0.12s" }}>
        <button onClick={e => { e.stopPropagation(); onEdit(); }} title="Edit"
          style={iconBtn(C.fog)}>✎</button>
        <button onClick={e => { e.stopPropagation(); if (window.confirm(`Delete §${clause}?`)) onDelete(); }}
          title="Delete" style={iconBtn(C.fog)}
          onMouseEnter={e => e.currentTarget.style.color = C.red}
          onMouseLeave={e => e.currentTarget.style.color = C.fog}>
          &#x2715;
        </button>
      </div>
    </div>
  );
}

// ── Inline editor ─────────────────────────────────────────────────────────
function LessonEditor({ filename, content, onSave, onCancel }) {
  const [val, setVal]       = useState(content || "");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/api/files/save`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, content: val }),
      });
      onSave(val);
    } catch (e) { console.error(e); }
    setSaving(false);
  };

  return (
    <div style={{ background: C.pearl, border: `1px solid ${C.mist}`,
      borderRadius: 10, padding: "18px 22px" }}>
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "center", marginBottom: 12 }}>
        <span style={{ fontFamily: "Inter,sans-serif", fontSize: 12,
          fontWeight: 600, color: C.ink }}>Editing: {filename}</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={onCancel} style={actionBtn(C.fog)}>Cancel</button>
          <button onClick={save} disabled={saving}
            style={{ ...actionBtn(C.teal), background: C.teal, color: "#fff", border: "none" }}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
      <textarea value={val} onChange={e => setVal(e.target.value)}
        style={{ width: "100%", minHeight: 420, padding: "10px 12px",
          border: `1px solid ${C.mist}`, borderRadius: 7,
          fontFamily: "monospace", fontSize: 12, lineHeight: 1.65,
          color: C.slate, background: C.cloud, resize: "vertical",
          boxSizing: "border-box", outline: "none" }}/>
    </div>
  );
}

// ── Strip YAML frontmatter before rendering ───────────────────────────────
function stripFrontmatter(raw) {
  const t = raw.trimStart();
  if (!t.startsWith('---')) return raw;
  const end = t.indexOf('\n---', 3);
  if (end === -1) return raw;
  return t.slice(end + 4).trimStart();
}

// ── Local Markdown renderer ───────────────────────────────────────────────
function MarkdownView({ content: rawContent }) {
  const content = stripFrontmatter(rawContent);
  const html = content
    .replace(/^# (.+)$/gm,  '<h1 style="font-size:1.25rem;font-weight:700;margin:1.2rem 0 0.5rem;color:#0A2540;letter-spacing:-0.01em">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:1rem;font-weight:700;margin:1rem 0 0.4rem;color:#1A6FA3">$1</h2>')
    .replace(/^### (.+)$/gm,'<h3 style="font-size:0.9rem;font-weight:700;margin:0.8rem 0 0.3rem;color:#1F7A6D">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm,  '<div style="display:flex;gap:8px;margin:0.25rem 0 0.25rem 0.5rem"><span style="color:#C4922A;font-weight:700;flex-shrink:0">—</span><span>$1</span></div>')
    .replace(/^---$/gm,     '<hr style="border:none;border-top:1px solid #DDE4EB;margin:1rem 0"/>')
    .replace(/\n\n/g, '</p><p style="margin:0.6rem 0">')
    .replace(/\n/g, '<br/>');
  return (
    <div style={{ fontFamily: "Georgia,serif", fontSize: 14, lineHeight: 1.8, color: "#3C5470" }}
      dangerouslySetInnerHTML={{ __html: `<p style="margin:0">${html}</p>` }} />
  );
}

// ── Main view ─────────────────────────────────────────────────────────────
export default function ISOView({ runningAgents }) {
  const [lessons,  setLessons]  = useState([]);
  const [selected, setSelected] = useState(null);
  const [content,  setContent]  = useState("");
  const [editing,  setEditing]  = useState(false);
  const [running,  setRunning]  = useState(false);
  const [clause,   setClause]   = useState("");
  const [status,   setStatus]   = useState("");
  const ms = useSelect();

  const prevIsoRef  = useRef(false);
  const fallbackRef = useRef(null);

  const load = () =>
    fetch(`${API}/api/iso/lessons`).then(r => r.json())
      .then(d => setLessons(d.lessons || [])).catch(() => {});

  useEffect(() => { load(); }, []);

  useEffect(() => {
    if (!selected) return;
    fetch(`${API}/api/iso/lessons/${selected}`).then(r => r.json())
      .then(d => setContent(d.content || "")).catch(() => {});
  }, [selected]);

  // WS-driven completion: react when iso_coach flips running → idle.
  const isoRunning = runningAgents?.has?.("iso_coach") || false;
  useEffect(() => {
    const wasRunning = prevIsoRef.current;
    if (wasRunning && !isoRunning) {
      if (fallbackRef.current) { clearTimeout(fallbackRef.current); fallbackRef.current = null; }
      load();
      setRunning(false);
      setStatus("Lesson ready — see the list on the left.");
    }
    prevIsoRef.current = isoRunning;
  }, [isoRunning]);

  // Clear safety-net timer on unmount.
  useEffect(() => () => { if (fallbackRef.current) clearTimeout(fallbackRef.current); }, []);

  const selectLesson = (filename) => {
    setSelected(filename);
    setEditing(false);
  };

  const generateLesson = () => {
    setRunning(true);
    setStatus("Generating lesson…");
    if (fallbackRef.current) clearTimeout(fallbackRef.current);
    fallbackRef.current = setTimeout(() => {
      load(); setRunning(false); fallbackRef.current = null;
      setStatus("Done — refresh if your lesson isn't listed yet.");
    }, 120000);
    fetch(`${API}/api/agents/iso`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clause: clause.trim() || null }),
    }).then(() => {
      setStatus("Generating — check Run Agents log");
    }).catch(() => {
      setStatus("Error");
      setRunning(false);
      if (fallbackRef.current) { clearTimeout(fallbackRef.current); fallbackRef.current = null; }
    });
  };

  const folderOf = (filename) => filename.startsWith("14971_") ? "iso14971" : "iso13485";

  const deleteOne = async (filename) => {
    await fetch(`${API}/api/files/delete`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, folder: folderOf(filename) }),
    });
    if (selected === filename) { setSelected(null); setContent(""); setEditing(false); }
    ms.clear(); load();
  };

  const deleteSelected = async () => {
    if (!ms.size) return;
    if (!window.confirm(`Delete ${ms.size} lesson(s)?`)) return;
    await fetch(`${API}/api/files/delete-bulk`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: [...ms.checked].map(f => ({ folder: folderOf(f), filename: f })) }),
    });
    if (ms.has(selected)) { setSelected(null); setContent(""); setEditing(false); }
    ms.clear(); load();
  };

  const allIds = lessons.map(l => l.filename);

  return (
    <div>
      <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: C.ink, margin: "0 0 4px" }}>
        ISO Case Studies
      </h2>
      <div style={{ fontFamily: "Inter,sans-serif", fontSize: 11, color: C.fog, marginBottom: 20 }}>
        ISO 13485:2016 Quality Management · ISO 14971:2019 Risk Management
      </div>

      {/* Generate — clause selector dropdown */}
      <div style={{ background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 8,
        padding: "14px 20px", marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select value={clause} onChange={e => setClause(e.target.value)}
            style={{ flex: 1, padding: "8px 12px", border: `1px solid ${C.mist}`,
              borderRadius: 6, fontFamily: "Inter,sans-serif", fontSize: 13,
              background: C.cloud, color: C.slate, outline: "none", cursor: "pointer" }}>
            <option value="">— Generate next missing clause —</option>
            <optgroup label="ISO 13485:2016 — Quality Management System">
              {CLAUSES_13485.map(([num, name]) => {
                const done = lessons.some(l => l.clause === num);
                return (
                  <option key={num} value={num}>
                    {done ? "✓ " : ""}§{num} — {name}
                  </option>
                );
              })}
            </optgroup>
            <optgroup label="ISO 14971:2019 — Risk Management">
              {CLAUSES_14971.map(([num, name]) => {
                const dispNum = num.replace("14971.", "");
                const done = lessons.some(l => l.clause === num);
                return (
                  <option key={num} value={num}>
                    {done ? "✓ " : ""}§{dispNum} — {name}
                  </option>
                );
              })}
            </optgroup>
          </select>
          <button onClick={generateLesson} disabled={running}
            style={{ padding: "8px 18px", background: running ? C.fog : C.navy, flexShrink: 0,
              color: "#fff", border: "none", borderRadius: 6, fontWeight: 700,
              fontSize: 12, cursor: running ? "not-allowed" : "pointer", whiteSpace: "nowrap" }}>
            {running ? "Running…" : clause.trim()
              ? `Generate §${clause.startsWith("14971.") ? clause.replace("14971.","") : clause}`
              : "Generate Next"}
          </button>
        </div>
        {status && <div style={{ marginTop: 8, fontFamily: "Inter,sans-serif", fontSize: 11, color: C.teal }}>{status}</div>}
      </div>

      <div style={{ display: "flex", gap: 20 }}>

        {/* Sidebar */}
        <div style={{ width: 240, flexShrink: 0 }}>
          <BulkBar count={ms.size} total={lessons.length}
            onDeleteSelected={deleteSelected}
            onSelectAll={() => ms.selectAll(allIds)}
            onClear={ms.clear}/>

          {lessons.length === 0 && (
            <div style={{ fontFamily: "Inter,sans-serif", fontSize: 12, color: C.fog }}>
              No lessons yet. Generate one above.
            </div>
          )}

          {lessons.map(l => {
            const std = l.standard || (l.clause?.startsWith("14971.") ? "ISO 14971" : "ISO 13485");
            const dispClause = l.clause?.startsWith("14971.") ? l.clause.replace("14971.", "") : l.clause;
            return (
              <LessonItem
                key={l.filename}
                clause={dispClause}
                title={l.standard ? `[${std.replace("ISO ","")}] ${l.title}` : l.title}
                date={l.modified?.slice(0, 10)}
                active={selected === l.filename}
                checked={ms.has(l.filename)}
                onCheck={() => ms.toggle(l.filename)}
                onSelect={() => selectLesson(l.filename)}
                onEdit={() => { setSelected(l.filename); setEditing(true); }}
                onDelete={() => deleteOne(l.filename)}
              />
            );
          })}
        </div>

        {/* Content / Editor */}
        <div style={{ flex: 1, minHeight: 300 }}>
          {editing && selected ? (
            <LessonEditor
              filename={selected}
              content={content}
              onSave={v => { setContent(v); setEditing(false); }}
              onCancel={() => setEditing(false)}
            />
          ) : (
            <div style={{ background: C.pearl, border: `1px solid ${C.mist}`,
              borderRadius: 10, padding: "20px 24px", minHeight: 300 }}>
              {content
                ? <MarkdownView content={content}/>
                : <div style={{ color: C.fog, fontFamily: "Inter,sans-serif", fontSize: 13 }}>
                    Select a lesson or generate a new one.
                  </div>
              }
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Shared micro styles ───────────────────────────────────────────────────
function actionBtn(color) {
  return {
    padding: "4px 10px", borderRadius: 5, cursor: "pointer",
    background: "transparent", border: `1px solid ${color}66`,
    color, fontSize: 11, fontWeight: 600, fontFamily: "Inter,sans-serif",
  };
}

function iconBtn(color) {
  return {
    width: 26, height: 26, display: "flex", alignItems: "center",
    justifyContent: "center", background: "transparent",
    border: `1px solid ${C.mist}`, borderRadius: 5,
    cursor: "pointer", color, fontSize: 12, padding: 0, lineHeight: 1,
    transition: "color 0.12s",
  };
}
