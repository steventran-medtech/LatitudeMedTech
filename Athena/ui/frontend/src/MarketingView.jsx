import { useState, useEffect, useRef } from "react";
import { authHdr } from "./api.js";

const API = "http://localhost:8000";

// ── Brand palette (matches App.jsx) ──────────────────────────────────────────
const C = {
  navy:   "#0A2540", ocean:  "#1A6FA3", gold:   "#C4922A",
  teal:   "#1F7A6D", cloud:  "#F8FAFC", sand:   "#F2EDE6",
  pearl:  "#FFFFFF", ink:    "#0A2540", slate:  "#3C5470",
  fog:    "#7B90A0", mist:   "#DDE4EB", red:    "#C0392B",
  ltgray: "#EDF1F5", blue:   "#1A6FA3", green:  "#1F7A6D",
  // Latitude brand accents
  lmBlue: "#5B7FA6", lmTint: "#EBF0F6",
};
const F = { sans: "'Inter',-apple-system,BlinkMacSystemFont,sans-serif" };

const S = {
  card: { background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 10,
    padding: "20px 24px", marginBottom: 16,
    boxShadow: "0 1px 4px rgba(10,37,64,0.04)" },
  label: { fontFamily: F.sans, fontSize: 10, fontWeight: 600, letterSpacing: "0.1em",
    textTransform: "uppercase", color: C.fog, marginBottom: 6, display: "block" },
  btn: (v = "primary") => ({
    padding: "7px 16px", borderRadius: 6, border: "none", cursor: "pointer",
    fontFamily: F.sans, fontSize: 11, fontWeight: 600,
    letterSpacing: "0.05em", textTransform: "uppercase",
    background: v === "primary" ? C.navy : v === "teal" ? C.teal
      : v === "ocean" ? C.ocean : v === "gold" ? C.gold
      : v === "red" ? C.red : "transparent",
    color: v === "ghost" ? C.fog : C.pearl,
    border: v === "ghost" ? `1px solid ${C.mist}` : "none",
    transition: "opacity 0.15s",
  }),
  input: {
    width: "100%", padding: "8px 12px", border: `1px solid ${C.mist}`,
    borderRadius: 6, fontFamily: F.sans, fontSize: 13, background: C.pearl,
    color: C.slate, outline: "none", boxSizing: "border-box",
  },
};

// ── Channel type → colour ────────────────────────────────────────────────────
const CHANNEL_COLOR = {
  conference: C.ocean, podcast: C.teal, speaking: C.gold,
  referral: C.lmBlue, clinic: "#7B3FA6", prospect: C.navy,
};
const CHANNEL_ICON = {
  conference: "📍", podcast: "🎙", speaking: "🎤",
  referral: "🤝", clinic: "🏥", prospect: "🎯",
};

function ChannelChip({ type }) {
  const color = CHANNEL_COLOR[type] || C.fog;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      background: color + "18", color,
      padding: "2px 8px", borderRadius: 20,
      fontSize: 10, fontWeight: 600,
      border: `1px solid ${color}33`,
      letterSpacing: "0.04em",
    }}>
      {CHANNEL_ICON[type] || "·"} {type.toUpperCase()}
    </span>
  );
}

function StatusPill({ status }) {
  const map = {
    identified:   { bg: C.ltgray,         color: C.fog,       label: "Identified" },
    contacted:    { bg: "#EBF3FB",         color: C.ocean,     label: "Contacted" },
    in_discussion:{ bg: "#EAF7EE",         color: C.teal,      label: "In Discussion" },
    converted:    { bg: "#1F7A6D22",       color: C.teal,      label: "Converted ✓" },
    closed:       { bg: "#F2EDE6",         color: C.fog,       label: "Closed" },
  };
  const s = map[status] || { bg: C.ltgray, color: C.fog, label: status };
  return (
    <span style={{
      background: s.bg, color: s.color,
      padding: "2px 8px", borderRadius: 4,
      fontSize: 10, fontWeight: 700,
      letterSpacing: "0.05em",
    }}>{s.label}</span>
  );
}

// ── Stat card ────────────────────────────────────────────────────────────────
function KPICard({ value, label, sub, color }) {
  return (
    <div style={{
      flex: 1, background: C.pearl, border: `1px solid ${C.mist}`,
      borderRadius: 10, padding: "16px 20px",
      boxShadow: "0 1px 4px rgba(10,37,64,0.04)",
    }}>
      <div style={{ fontFamily: F.sans, fontSize: 28, fontWeight: 700,
        color: color || C.navy, lineHeight: 1 }}>
        {value ?? "—"}
      </div>
      <div style={{ fontFamily: F.sans, fontSize: 10, letterSpacing: "0.1em",
        textTransform: "uppercase", color: C.fog, marginTop: 4 }}>
        {label}
      </div>
      {sub && <div style={{ fontFamily: F.sans, fontSize: 10, color: C.fog, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

// ── Pipeline summary bar (by channel) ────────────────────────────────────────
function PipelineBar({ summary }) {
  // Group by channel type
  const byType = {};
  (summary || []).forEach(({ type, status, count }) => {
    if (!byType[type]) byType[type] = { total: 0, statuses: {} };
    byType[type].total += count;
    byType[type].statuses[status] = count;
  });

  if (!Object.keys(byType).length) {
    return (
      <div style={{ padding: "16px 0", color: C.fog, fontFamily: F.sans, fontSize: 12 }}>
        Pipeline loading…
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
      {Object.entries(byType).map(([type, data]) => {
        const color = CHANNEL_COLOR[type] || C.fog;
        return (
          <div key={type} style={{
            background: color + "12", border: `1px solid ${color}33`,
            borderRadius: 8, padding: "10px 14px", minWidth: 110,
          }}>
            <div style={{ fontFamily: F.sans, fontSize: 20, fontWeight: 700,
              color, lineHeight: 1 }}>{data.total}</div>
            <div style={{ fontFamily: F.sans, fontSize: 9, fontWeight: 700,
              letterSpacing: "0.08em", textTransform: "uppercase",
              color, marginTop: 3 }}>
              {CHANNEL_ICON[type]} {type}
            </div>
            {data.statuses.converted > 0 && (
              <div style={{ fontFamily: F.sans, fontSize: 10, color: C.teal, marginTop: 2 }}>
                ✓ {data.statuses.converted} converted
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Next-actions table ────────────────────────────────────────────────────────
function NextActions({ actions, onUpdateStatus }) {
  const [updating, setUpdating] = useState(null);

  const updateStatus = async (name, status) => {
    setUpdating(name);
    await fetch(`${API}/api/marketing/pipeline/update`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
      body: JSON.stringify({ name, status, note: `Status updated via UI` }),
    }).catch(() => {});
    setUpdating(null);
    onUpdateStatus?.();
  };

  if (!actions?.length) {
    return (
      <div style={{ padding: "12px 0", color: C.fog, fontFamily: F.sans, fontSize: 12 }}>
        No high-priority actions — run the pipeline for an update.
      </div>
    );
  }

  const NEXT_STATUS = {
    identified: "contacted", contacted: "in_discussion",
    in_discussion: "converted",
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F.sans, fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${C.mist}` }}>
            {["Target", "Channel", "Status", "Next Action", "Due", ""].map(h => (
              <th key={h} style={{
                padding: "7px 10px", textAlign: "left",
                fontSize: 9, fontWeight: 700, letterSpacing: "0.1em",
                textTransform: "uppercase", color: C.fog,
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {actions.map((a, i) => (
            <tr key={i} style={{ borderBottom: `1px solid ${C.ltgray}` }}>
              <td style={{ padding: "9px 10px", fontWeight: 600, color: C.ink, maxWidth: 180 }}>
                <div style={{ fontSize: 12 }}>{a.name}</div>
                {a.org && <div style={{ fontSize: 10, color: C.fog }}>{a.org}</div>}
              </td>
              <td style={{ padding: "9px 10px" }}><ChannelChip type={a.type} /></td>
              <td style={{ padding: "9px 10px" }}><StatusPill status={a.status} /></td>
              <td style={{ padding: "9px 10px", color: C.slate, fontSize: 11, maxWidth: 220 }}>
                {a.next_action || "—"}
              </td>
              <td style={{ padding: "9px 10px", fontFamily: F.sans, fontSize: 11,
                color: a.next_date < new Date().toISOString().slice(0, 10) ? C.red : C.fog,
                fontWeight: a.next_date < new Date().toISOString().slice(0, 10) ? 700 : 400,
              }}>
                {a.next_date || "—"}
              </td>
              <td style={{ padding: "9px 10px" }}>
                {NEXT_STATUS[a.status] && (
                  <button
                    disabled={updating === a.name}
                    onClick={() => updateStatus(a.name, NEXT_STATUS[a.status])}
                    style={{
                      ...S.btn("ghost"), fontSize: 9, padding: "3px 8px",
                      color: C.ocean, borderColor: C.ocean,
                      opacity: updating === a.name ? 0.5 : 1,
                    }}>
                    {updating === a.name ? "…" : `Mark ${NEXT_STATUS[a.status].replace("_", " ")}`}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Output file list ──────────────────────────────────────────────────────────
function OutputList({ files, selected, onSelect }) {
  if (!files?.length) {
    return (
      <div style={{ fontFamily: F.sans, fontSize: 12, color: C.fog, padding: "12px 0" }}>
        No outputs yet — run a brief or plan above.
      </div>
    );
  }
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {files.map(f => (
        <div
          key={f.filename}
          onClick={() => onSelect(f.filename)}
          style={{
            padding: "9px 12px", borderRadius: 7, cursor: "pointer",
            background: selected === f.filename ? C.sand : C.pearl,
            border: `1px solid ${selected === f.filename ? C.ocean : C.mist}`,
            borderLeft: `3px solid ${selected === f.filename ? C.ocean : C.mist}`,
            transition: "background 0.1s, border-color 0.1s",
          }}>
          <div style={{ fontFamily: F.sans, fontSize: 12,
            color: selected === f.filename ? C.ink : C.slate,
            fontWeight: selected === f.filename ? 600 : 400, lineHeight: 1.4 }}>
            {f.label || f.filename}
          </div>
          <div style={{ fontFamily: F.sans, fontSize: 10, color: C.fog, marginTop: 2 }}>
            {f.modified}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main MarketingView ────────────────────────────────────────────────────────
export default function MarketingView({ runningAgents }) {
  const [pipeline,    setPipeline]    = useState(null);
  const [outputs,     setOutputs]     = useState([]);
  const [selected,    setSelected]    = useState(null);
  const [content,     setContent]     = useState("");
  const [running,     setRunning]     = useState(null);
  const [outreach,    setOutreach]    = useState("");
  const [status,      setStatus]      = useState("");

  // ── Live progress, driven by the global WebSocket agent lifecycle ───────────
  // App.jsx tracks every active agent in `runningAgents` (updated on the
  // agent_start / agent_done WS events). We watch the marketing_agent entry so
  // this view reflects the *real* run instead of guessing with a fixed timer.
  const agentRunning   = runningAgents?.has?.("marketing_agent") || false;
  const busy           = !!running || agentRunning;
  const prevRunningRef = useRef(false);
  const fallbackRef    = useRef(null);

  const loadPipeline = () => {
    fetch(`${API}/api/marketing/pipeline`).then(r => r.json()).then(setPipeline).catch(() => {});
  };
  const loadOutputs = () => {
    fetch(`${API}/api/marketing/outputs`).then(r => r.json()).then(d => {
      const files = d.files || [];
      setOutputs(files);
      // Auto-select latest if nothing selected yet
      if (!selected && files.length) setSelected(files[0].filename);
    }).catch(() => {});
  };

  useEffect(() => { loadPipeline(); loadOutputs(); }, []);

  useEffect(() => {
    if (!selected) return;
    fetch(`${API}/api/marketing/outputs/${selected}`)
      .then(r => r.json()).then(d => setContent(d.content || "")).catch(() => setContent(""));
  }, [selected]);

  // React to the real agent lifecycle: when marketing_agent flips running → idle
  // (the agent_done WS event), pull the freshly written output and pipeline.
  // Also reflects runs started elsewhere (e.g. the Run Agents tab).
  useEffect(() => {
    const wasRunning = prevRunningRef.current;
    if (!wasRunning && agentRunning) {
      // Started — surface it even if it was triggered from another view.
      setStatus(s => s || "Marketing agent running…");
    } else if (wasRunning && !agentRunning) {
      // Finished — refresh outputs/pipeline and clear the busy state.
      if (fallbackRef.current) { clearTimeout(fallbackRef.current); fallbackRef.current = null; }
      loadOutputs();
      loadPipeline();
      setRunning(null);
      setStatus("Output ready — see the file list below.");
    }
    prevRunningRef.current = agentRunning;
  }, [agentRunning]);

  // Clear the safety-net timer if the view unmounts mid-run.
  useEffect(() => () => { if (fallbackRef.current) clearTimeout(fallbackRef.current); }, []);

  const trigger = (mode, target = "") => {
    setRunning(mode);
    setStatus(`Starting ${mode}…`);
    // Safety net only: if we somehow never observe agent_done (e.g. the WS drops),
    // refresh anyway so the view can't get stuck "running" forever. The real
    // completion path is the agentRunning effect below.
    if (fallbackRef.current) clearTimeout(fallbackRef.current);
    fallbackRef.current = setTimeout(() => {
      loadOutputs(); loadPipeline(); setRunning(null);
      setStatus("Done — refresh if your output isn't listed yet.");
      fallbackRef.current = null;
    }, 180000);
    fetch(`${API}/api/agents/marketing`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
      body: JSON.stringify({ mode, target }),
    }).then(() => {
      setStatus(`${mode} running — this can take a minute or two…`);
    }).catch(() => {
      setStatus("Error starting agent");
      setRunning(null);
      if (fallbackRef.current) { clearTimeout(fallbackRef.current); fallbackRef.current = null; }
    });
  };

  const runOutreach = () => {
    if (!outreach.trim()) return;
    trigger("outreach", outreach.trim());
  };

  const kpis = pipeline?.kpis || {};
  const phaseMeta = "Phase 1A target: 1 paid coaching client by Day 90";

  return (
    <div style={{ maxWidth: 1100 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontFamily: F.sans, fontSize: 17, fontWeight: 700,
            color: C.ink, margin: "0 0 4px", letterSpacing: "-0.01em" }}>
            Marketing
          </h2>
          <div style={{ fontFamily: F.sans, fontSize: 11, color: C.fog }}>
            Guerilla pipeline · SoCal MedTech corridor · {phaseMeta}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {[
            { mode: "brief",     label: "Weekly Brief", v: "primary" },
            { mode: "plan",      label: "30-60-90 Plan", v: "ocean" },
            { mode: "events",    label: "Events Calendar", v: "teal" },
            { mode: "scorecard", label: "Scorecard", v: "gold" },
          ].map(({ mode, label, v }) => (
            <button
              key={mode}
              disabled={busy}
              onClick={() => trigger(mode)}
              style={{ ...S.btn(v), opacity: busy ? 0.6 : 1, cursor: busy ? "not-allowed" : "pointer" }}>
              {running === mode ? "Running…" : label}
            </button>
          ))}
        </div>
      </div>

      {/* Status strip */}
      {status && (
        <div style={{
          background: busy ? "#EBF3FB" : "#EAF7EE",
          border: `1px solid ${busy ? C.ocean + "44" : C.teal + "44"}`,
          borderRadius: 7, padding: "8px 14px", marginBottom: 14,
          fontFamily: F.sans, fontSize: 12,
          color: busy ? C.ocean : C.teal,
          display: "flex", alignItems: "center", gap: 8,
        }}>
          {busy && (
            <span style={{
              width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
              background: C.ocean, animation: "mktPulse 1s ease-in-out infinite",
            }}/>
          )}
          {status}
          <style>{`@keyframes mktPulse { 0%,100%{opacity:1} 50%{opacity:0.3} }`}</style>
        </div>
      )}

      {/* KPI strip */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
        <KPICard value={kpis.total}     label="Targets in pipeline" color={C.navy} />
        <KPICard value={kpis.contacted} label="Contacted / in motion"
          sub={kpis.total > 0 ? `${Math.round(100 * (kpis.contacted || 0) / kpis.total)}% of pipeline` : ""}
          color={C.ocean} />
        <KPICard value={kpis.meetings}  label="Discovery calls / in discussion" color={C.lmBlue} />
        <KPICard value={kpis.converted} label="Converted clients" color={C.teal} />
      </div>

      {/* Pipeline by channel */}
      <div style={S.card}>
        <span style={S.label}>Pipeline by channel</span>
        <PipelineBar summary={pipeline?.summary} />
      </div>

      {/* High-priority next actions */}
      <div style={S.card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <span style={{ ...S.label, marginBottom: 0 }}>High-priority next actions</span>
          <button onClick={() => { loadPipeline(); loadOutputs(); }}
            style={{ ...S.btn("ghost"), fontSize: 10, padding: "3px 10px" }}>
            Refresh
          </button>
        </div>
        <NextActions actions={pipeline?.actions} onUpdateStatus={() => { loadPipeline(); }} />
      </div>

      {/* Outreach generator */}
      <div style={{ ...S.card, display: "flex", gap: 12, alignItems: "center" }}>
        <div style={{ flex: 1 }}>
          <span style={S.label}>Generate outreach copy</span>
          <input
            value={outreach}
            onChange={e => setOutreach(e.target.value)}
            onKeyDown={e => e.key === "Enter" && runOutreach()}
            placeholder="Target name or podcast, e.g. 'Jon Speer' or 'Medical Device Podcast'"
            style={S.input}
          />
        </div>
        <button
          disabled={busy || !outreach.trim()}
          onClick={runOutreach}
          style={{ ...S.btn("primary"), marginTop: 22, flexShrink: 0, whiteSpace: "nowrap",
            opacity: busy || !outreach.trim() ? 0.6 : 1 }}>
          {running === "outreach" ? "Generating…" : "Generate Outreach"}
        </button>
      </div>

      {/* Outputs: list + viewer */}
      <div style={{ display: "flex", gap: 20 }}>
        {/* Left: file list */}
        <div style={{ width: 260, flexShrink: 0 }}>
          <div style={{ ...S.card, padding: "16px 18px" }}>
            <span style={S.label}>Generated outputs</span>
            <OutputList files={outputs} selected={selected} onSelect={f => setSelected(f)} />
          </div>
        </div>

        {/* Right: content viewer */}
        <div style={{ flex: 1 }}>
          <div style={S.card}>
            {content ? (
              <MarkdownContent content={content} />
            ) : (
              <div style={{ fontFamily: F.sans, fontSize: 13, color: C.fog, padding: "20px 0" }}>
                {outputs.length === 0
                  ? "Run a brief, plan, or events calendar above — outputs appear here."
                  : "Select an output on the left to read it."}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Minimal markdown renderer (reuses App.jsx patterns) ──────────────────────
function MarkdownContent({ content }) {
  const lines = content.split("\n");
  const nodes = [];
  let listItems = [];

  const flushList = () => {
    if (!listItems.length) return;
    nodes.push(
      <ul key={`ul-${nodes.length}`}
        style={{ margin: "6px 0 14px", paddingLeft: 0, listStyle: "none" }}>
        {listItems.map((t, i) => (
          <li key={i} style={{ display: "flex", gap: 10, marginBottom: 5,
            fontFamily: F.sans, fontSize: 13, color: C.slate, lineHeight: 1.6 }}>
            <span style={{ color: C.gold, fontWeight: 700, flexShrink: 0 }}>—</span>
            <span>{t}</span>
          </li>
        ))}
      </ul>
    );
    listItems = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trim = line.trim();
    if (!trim) { flushList(); continue; }
    if (trim.startsWith("# ")) {
      flushList();
      nodes.push(<h2 key={i} style={{ fontFamily: F.sans, fontSize: 18, fontWeight: 700,
        color: C.ink, margin: "22px 0 8px", letterSpacing: "-0.01em" }}>
        {trim.slice(2)}
      </h2>);
    } else if (trim.startsWith("## ")) {
      flushList();
      nodes.push(<div key={i} style={{ margin: "18px 0 8px" }}>
        <h3 style={{ fontFamily: F.sans, fontSize: 14, fontWeight: 700,
          color: C.navy, margin: 0 }}>{trim.slice(3)}</h3>
        <div style={{ height: 1.5, background: C.lmBlue + "66", marginTop: 4, borderRadius: 1 }}/>
      </div>);
    } else if (trim.startsWith("### ")) {
      flushList();
      nodes.push(<h4 key={i} style={{ fontFamily: F.sans, fontSize: 12, fontWeight: 700,
        color: C.gold, margin: "14px 0 4px", textTransform: "uppercase",
        letterSpacing: "0.06em" }}>{trim.slice(4)}</h4>);
    } else if (trim.startsWith("- ") || trim.startsWith("* ")) {
      listItems.push(trim.slice(2));
    } else if (trim === "---") {
      flushList();
      nodes.push(<hr key={i} style={{ border: "none",
        borderTop: `1px solid ${C.mist}`, margin: "16px 0" }}/>);
    } else {
      flushList();
      // Strip YAML frontmatter lines
      if (trim.startsWith("---") || trim.includes(": ") && i < 8) continue;
      nodes.push(<p key={i} style={{ fontFamily: F.sans, fontSize: 13.5,
        color: C.slate, lineHeight: 1.75, margin: "0 0 10px" }}>
        {trim}
      </p>);
    }
  }
  flushList();

  return <div style={{ maxWidth: 760 }}>{nodes}</div>;
}
