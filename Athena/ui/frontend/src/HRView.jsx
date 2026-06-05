import { useEffect, useRef, useState } from "react";

const API = "http://localhost:8000";

const FLAG = {
  green:  { color: "#1F7A6D", bg: "#EAF7EE", label: "Healthy",  dot: "#1F7A6D" },
  yellow: { color: "#C4922A", bg: "#FDF6E3", label: "Attention", dot: "#C4922A" },
  red:    { color: "#C0392B", bg: "#FDECEA", label: "Action",    dot: "#C0392B" },
};

const LABELS = {
  content:"Content", briefing:"Briefing", iso:"ISO Coach",
  coaching:"Coaching", fda:"FDA Agent", rag:"RAG", voice_bridge:"Voice",
  consulting:"Consulting", ma_intelligence:"M&A Intelligence", eu_mdr:"EU MDR", hr:"HR/L&D",
};

function daysAgo(ts) {
  if (!ts) return null;
  return Math.floor((Date.now() - new Date(ts)) / 86400000);
}

function DaysPill({ ts, warnAt = 7, redAt = 14 }) {
  if (!ts) return <span style={{ color: "#7B90A0", fontSize: 11 }}>Never</span>;
  const d = daysAgo(ts);
  const c = d >= redAt ? "#C0392B" : d >= warnAt ? "#C4922A" : "#1F7A6D";
  const dt = new Date(ts);
  const timeStr = dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const dateStr = dt.toLocaleDateString([], { month: "short", day: "numeric" });
  const label = d === 0 ? `Today ${timeStr}` : `${d}d ago`;
  const sub   = d === 0 ? null : dateStr;
  return (
    <span style={{ color: c, fontWeight: 600, fontSize: 11 }}>
      {label}
      {sub && <span style={{ fontWeight: 400, color: "#7B90A0", marginLeft: 3 }}>{sub}</span>}
    </span>
  );
}

// Cumulative knowledge-accumulation chart (pure SVG — no chart library).
function KnowledgeGrowth({ data }) {
  if (!data || data.length < 2) {
    return (
      <div style={{
        background: "#fff", border: "1px solid #DDE4EB", borderRadius: 10,
        padding: "18px 20px", marginBottom: 16,
      }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em",
          textTransform: "uppercase", color: "#7B90A0", marginBottom: 6 }}>
          Knowledge Growth
        </div>
        <div style={{ fontSize: 12, color: "#7B90A0" }}>
          Not enough history yet — knowledge accumulation appears here as agents learn.
        </div>
      </div>
    );
  }
  const w = 860, h = 150, pad = 6;
  const vals = data.map(d => d.cumulative || 0);
  const max  = Math.max(...vals, 1);
  const min  = Math.min(...vals);
  const x = i => pad + (i / (data.length - 1)) * (w - pad * 2);
  const y = v => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2 - 4);
  const line = vals.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  const total   = vals[vals.length - 1];
  const added   = total - min;
  const peakDay = data.reduce((a, b) => (b.items > a.items ? b : a), data[0]);
  return (
    <div style={{
      background: "#fff", border: "1px solid #DDE4EB", borderRadius: 10,
      padding: "18px 20px", marginBottom: 16,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em",
          textTransform: "uppercase", color: "#7B90A0" }}>
          Knowledge Growth · cumulative items
        </div>
        <div style={{ fontSize: 11, color: "#7B90A0" }}>
          <strong style={{ color: "#1A6FA3", fontSize: 15 }}>{total.toLocaleString()}</strong> total
          {added > 0 && <span> · +{added.toLocaleString()} this window</span>}
        </div>
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: 150 }} preserveAspectRatio="none">
        <polyline points={`${pad},${h} ${line} ${w - pad},${h}`}
          fill="#1A6FA3" fillOpacity="0.10" stroke="none" />
        <polyline points={line} fill="none" stroke="#1A6FA3" strokeWidth="2" strokeLinejoin="round" />
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between",
        fontSize: 10, color: "#7B90A0", marginTop: 4 }}>
        <span>{data[0]?.date}</span>
        <span>peak day: {peakDay?.date} (+{peakDay?.items})</span>
        <span>{data[data.length - 1]?.date}</span>
      </div>
    </div>
  );
}

function AccPill({ items, chunks }) {
  if (!items && !chunks) return <span style={{ color: "#7B90A0", fontSize: 11 }}>—</span>;
  return (
    <div>
      <span style={{ fontWeight: 700, fontSize: 12, color: "#1A6FA3" }}>{(items || 0).toLocaleString()}</span>
      <span style={{ fontSize: 10, color: "#7B90A0", marginLeft: 3 }}>items</span>
      {chunks > 0 && (
        <div style={{ fontSize: 10, color: "#7B90A0" }}>{chunks.toLocaleString()} chunks</div>
      )}
    </div>
  );
}

function AgentRow({ agent, skills, onLearn, running }) {
  const meta  = FLAG[agent.flag_status] || FLAG.green;
  const label = LABELS[agent.agent] || agent.agent;
  const acc   = skills?.[agent.agent];
  return (
    <tr style={{ borderBottom: "1px solid #EDF1F5" }}>
      {/* Status dot + name */}
      <td style={{ padding: "10px 12px", whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: meta.dot, flexShrink: 0,
            boxShadow: `0 0 0 2px ${meta.dot}22`,
          }}/>
          <div>
            <div style={{ fontWeight: 600, fontSize: 12, color: "#0A2540" }}>{label}</div>
            <div style={{ fontSize: 10, color: "#7B90A0", marginTop: 1 }}>{agent.tier || ""}</div>
          </div>
        </div>
      </td>
      {/* Flag */}
      <td style={{ padding: "10px 8px" }}>
        <span style={{
          display: "inline-block", padding: "2px 8px", borderRadius: 4,
          background: meta.bg, color: meta.color,
          fontSize: 10, fontWeight: 700, letterSpacing: "0.06em",
          textTransform: "uppercase",
        }}>{meta.label}</span>
      </td>
      {/* Last learning */}
      <td style={{ padding: "10px 8px" }}>
        <DaysPill ts={agent.last_learning} />
      </td>
      {/* Last run */}
      <td style={{ padding: "10px 8px" }}>
        <DaysPill ts={agent.last_run} warnAt={3} redAt={7} />
      </td>
      {/* Errors */}
      <td style={{ padding: "10px 8px", textAlign: "center" }}>
        <span style={{
          color: (agent.error_count_7d || 0) >= 5 ? "#C0392B"
               : (agent.error_count_7d || 0) >= 3 ? "#C4922A" : "#1F7A6D",
          fontWeight: 600, fontSize: 12,
        }}>{agent.error_count_7d || 0}</span>
      </td>
      {/* Items (7d) */}
      <td style={{ padding: "10px 8px", textAlign: "center" }}>
        <span style={{
          color: (agent.learning_7d || 0) === 0 ? "#C0392B" : "#0A2540",
          fontWeight: 600, fontSize: 12,
        }}>{agent.learning_7d || 0}</span>
      </td>
      {/* Accumulated (all-time) */}
      <td style={{ padding: "10px 8px" }}>
        <AccPill items={acc?.total_items} chunks={acc?.total_chunks} />
      </td>
      {/* Flag reason — sanitise legacy "9999 days" entries */}
      <td style={{ padding: "10px 8px", maxWidth: 180 }}>
        {agent.flag_status !== "green" && agent.flag_reason
          ? <span style={{ fontSize: 10, color: meta.color, lineHeight: 1.4 }}>
              {agent.flag_reason
                .split(";")[0]
                .replace(/\b9999\b/g, "never")
                .replace(/in never days/g, "— no activity on record")}
            </span>
          : <span style={{ fontSize: 10, color: "#7B90A0" }}>—</span>
        }
      </td>
      {/* Action */}
      <td style={{ padding: "10px 8px" }}>
        <button
          onClick={() => onLearn(agent.agent)}
          disabled={running}
          style={{
            padding: "4px 10px", borderRadius: 5,
            background: running ? "#E8EDF2" : "#0A2540",
            color: running ? "#7B90A0" : "#fff",
            border: "none", cursor: running ? "not-allowed" : "pointer",
            fontSize: 10, fontWeight: 600, whiteSpace: "nowrap",
          }}>
          {running ? "…" : "Learn"}
        </button>
      </td>
    </tr>
  );
}

export default function HRView({ runningAgents }) {
  const [health,   setHealth]   = useState([]);
  const [learning, setLearning] = useState([]);
  const [skills,   setSkills]   = useState({});
  const [running,  setRunning]  = useState({});
  const [last,     setLast]     = useState(null);
  const [growth,   setGrowth]   = useState([]);

  // Track previous WS state for each watched agent so we catch running→idle transitions.
  const prevLearningRef      = useRef(false);
  const prevHrRef            = useRef(false);
  const prevSkillsRef        = useRef(false);
  const fallbacksRef         = useRef({});

  const load = () => {
    fetch(`${API}/api/hr/health`).then(r => r.json()).then(d => setHealth(d.agents || [])).catch(() => {});
    fetch(`${API}/api/hr/learning?days=7`).then(r => r.json()).then(d => setLearning(d.stats || [])).catch(() => {});
    fetch(`${API}/api/hr/skills`).then(r => r.json()).then(d => setSkills(d.skills || {})).catch(() => {});
    fetch(`${API}/api/dashboard/knowledge-growth?days=90`).then(r => r.json()).then(d => setGrowth(d.daily || [])).catch(() => {});
    setLast(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
  };

  useEffect(() => { load(); }, []);

  // Clear all fallback timers on unmount.
  useEffect(() => () => {
    Object.values(fallbacksRef.current).forEach(t => clearTimeout(t));
  }, []);

  // WS-driven completion for agent_learning (covers Learn One, Bulk Learn).
  const learningRunning = runningAgents?.has?.("agent_learning") || false;
  useEffect(() => {
    const wasRunning = prevLearningRef.current;
    if (wasRunning && !learningRunning) {
      if (fallbacksRef.current.learning) { clearTimeout(fallbacksRef.current.learning); delete fallbacksRef.current.learning; }
      load();
      setRunning(p => {
        const next = { ...p };
        delete next.learn_all;
        Object.keys(next).filter(k => k.startsWith("learn_")).forEach(k => delete next[k]);
        return next;
      });
    }
    prevLearningRef.current = learningRunning;
  }, [learningRunning]);

  // WS-driven completion for hr_agent (covers HR Review button).
  const hrRunning = runningAgents?.has?.("hr_agent") || false;
  useEffect(() => {
    const wasRunning = prevHrRef.current;
    if (wasRunning && !hrRunning) {
      if (fallbacksRef.current.hr) { clearTimeout(fallbacksRef.current.hr); delete fallbacksRef.current.hr; }
      load();
      setRunning(p => { const next = { ...p }; delete next.hr; return next; });
    }
    prevHrRef.current = hrRunning;
  }, [hrRunning]);

  // WS-driven completion for skills_profile (covers Refresh Skills button).
  const skillsRunning = runningAgents?.has?.("skills_profile") || false;
  useEffect(() => {
    const wasRunning = prevSkillsRef.current;
    if (wasRunning && !skillsRunning) {
      if (fallbacksRef.current.skills_profile) { clearTimeout(fallbacksRef.current.skills_profile); delete fallbacksRef.current.skills_profile; }
      load();
      setRunning(p => { const next = { ...p }; delete next.skills_profile; return next; });
    }
    prevSkillsRef.current = skillsRunning;
  }, [skillsRunning]);

  // Fallback timeouts (used only when WS drops): generous enough for real runtimes.
  const FALLBACK_MS = { learn_all: 300000, hr: 120000, skills_profile: 120000, run_all: 300000 };

  const trigger = (endpoint, key, body = {}) => {
    setRunning(p => ({ ...p, [key]: true }));
    const fbKey = key.startsWith("learn_") ? "learning" : key;
    if (fallbacksRef.current[fbKey]) clearTimeout(fallbacksRef.current[fbKey]);
    fallbacksRef.current[fbKey] = setTimeout(() => {
      load();
      setRunning(p => { const next = { ...p }; delete next[key]; return next; });
      delete fallbacksRef.current[fbKey];
    }, FALLBACK_MS[key] || 300000);
    fetch(`${API}${endpoint}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(() => {
      setRunning(p => ({ ...p, [key]: false }));
      if (fallbacksRef.current[fbKey]) { clearTimeout(fallbacksRef.current[fbKey]); delete fallbacksRef.current[fbKey]; }
    });
  };

  const learnOne = (agent) => trigger("/api/agents/learn", `learn_${agent}`, { agent });

  // When bulk learning OR bulk run is active, all agent rows show loading state
  const allLearning = !!running.learn_all || !!running.run_all;
  const isLearning  = (agent) => allLearning || !!running[`learn_${agent}`];

  const reds    = health.filter(a => a.flag_status === "red").length;
  const yellows = health.filter(a => a.flag_status === "yellow").length;
  const greens  = health.filter(a => a.flag_status === "green").length;
  const byAgent = Object.fromEntries(learning.map(l => [l.agent, l]));

  // Sort: red first, then yellow, then green
  const sorted = [...health].sort((a, b) => {
    const order = { red: 0, yellow: 1, green: 2 };
    return (order[a.flag_status] ?? 3) - (order[b.flag_status] ?? 3);
  });

  return (
    <div style={{ maxWidth: 1100 }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#0A2540", margin: 0 }}>Workforce</h2>
          <div style={{ fontSize: 11, color: "#7B90A0", marginTop: 2 }}>
            Agent health &amp; knowledge growth · {last ? `Updated ${last}` : ""}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={load} style={gBtn}>Refresh</button>
          <button onClick={() => trigger("/api/agents/learn", "learn_all")}
            disabled={running.learn_all || running.run_all}
            style={{ ...gBtn, background: "#1A6FA3", color: "#fff", border: "none" }}>
            {running.learn_all ? "Running…" : "Bulk Learn"}
          </button>
          <button onClick={() => trigger("/api/agents/run-all", "run_all")}
            disabled={running.run_all || running.learn_all}
            style={{ ...gBtn, background: "#1F7A6D", color: "#fff", border: "none" }}>
            {running.run_all ? "Running…" : "Bulk Run"}
          </button>
          <button onClick={() => trigger("/api/agents/hr", "hr")}
            disabled={running.hr}
            style={{ ...gBtn, background: "#0A2540", color: "#fff", border: "none" }}>
            {running.hr ? "Running…" : "HR Review"}
          </button>
          <button
            onClick={() => trigger("/api/agents/skills-profile", "skills_profile")}
            disabled={running.skills_profile}
            style={{ ...gBtn, background: "#3C5470", color: "#fff", border: "none" }}>
            {running.skills_profile ? "Building…" : "Refresh Skills"}
          </button>
        </div>
      </div>

      {/* Summary strip */}
      <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
        {[
          { label: "Action Required", count: reds,    ...FLAG.red    },
          { label: "Attention",       count: yellows, ...FLAG.yellow },
          { label: "Healthy",         count: greens,  ...FLAG.green  },
          { label: "Total Agents",    count: health.length, color: "#3C5470", bg: "#F2EDE6", dot: "#7B90A0" },
        ].map(s => (
          <div key={s.label} style={{
            flex: 1, background: s.bg, border: `1px solid ${s.color}22`,
            borderRadius: 8, padding: "10px 14px",
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <div style={{ fontSize: "1.6rem", fontWeight: 700, color: s.color, lineHeight: 1 }}>{s.count}</div>
            <div style={{ fontSize: 10, color: s.color, fontWeight: 600, letterSpacing: "0.06em",
              textTransform: "uppercase", lineHeight: 1.3 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Knowledge accumulation over time */}
      <KnowledgeGrowth data={growth} />

      {/* Agent table */}
      {health.length === 0 ? (
        <div style={{ padding: "40px 0", textAlign: "center", color: "#7B90A0", fontSize: 13,
          border: "1px dashed #DDE4EB", borderRadius: 8 }}>
          No data yet — click <strong>HR Review</strong> to evaluate all agents.
        </div>
      ) : (
        <div style={{ background: "#fff", border: "1px solid #DDE4EB", borderRadius: 10, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ background: "#F8FAFC", borderBottom: "1px solid #DDE4EB" }}>
                {["Agent", "Status", "Last Learned", "Last Run", "Errors 7d", "Items 7d", "Accumulated", "Flag Reason", ""].map(h => (
                  <th key={h} style={{
                    padding: "9px 8px", textAlign: "left",
                    fontSize: 9, fontWeight: 700, letterSpacing: "0.1em",
                    textTransform: "uppercase", color: "#7B90A0",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map(a => (
                <AgentRow
                  key={a.agent}
                  agent={{ ...a, learning_7d: byAgent[a.agent]?.items || 0 }}
                  skills={skills}
                  onLearn={learnOne}
                  running={isLearning(a.agent)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Learning sparkline — compact */}
      {learning.length > 0 && (
        <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {learning.map(l => (
            <div key={l.agent} style={{
              background: "#fff", border: "1px solid #DDE4EB",
              borderRadius: 7, padding: "8px 12px", display: "flex", gap: 8, alignItems: "center",
            }}>
              <span style={{ fontSize: 11, color: "#0A2540", fontWeight: 600 }}>
                {LABELS[l.agent] || l.agent}
              </span>
              <span style={{ fontSize: 14, fontWeight: 700, color: "#1A6FA3" }}>{l.items}</span>
              <span style={{ fontSize: 10, color: "#7B90A0" }}>items</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const gBtn = {
  padding: "6px 12px", background: "transparent",
  border: "1px solid #DDE4EB", borderRadius: 6,
  cursor: "pointer", fontSize: 11, fontWeight: 500, color: "#3C5470",
};
