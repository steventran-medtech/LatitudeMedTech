import { useState, useEffect, useCallback } from "react";

const API = "http://localhost:8000";

const C = {
  black: "#1A1A1A", slate: "#2C3E50", blue: "#5B7FA6",
  teal: "#4A7C6F", warm: "#C8956C", cream: "#FAFAF7",
  ltgray: "#F0EDE8", border: "#D8D4CE", muted: "#8A8680",
  white: "#FFFFFF", green: "#27AE60", red: "#C0392B",
};

const S = {
  card: {
    background: C.white, border: `1px solid ${C.border}`,
    borderRadius: 8, padding: "20px 24px", marginBottom: 20,
  },
  label: {
    fontFamily: "Helvetica, sans-serif", fontSize: 10,
    fontWeight: 700, letterSpacing: "0.12em",
    textTransform: "uppercase", color: C.muted,
    marginBottom: 6, display: "block",
  },
  input: {
    width: "100%", padding: "8px 12px",
    border: `1px solid ${C.border}`, borderRadius: 6,
    fontFamily: "Helvetica, sans-serif", fontSize: 13,
    background: C.cream, color: C.slate, outline: "none",
    boxSizing: "border-box",
  },
  textarea: {
    width: "100%", padding: "10px 12px",
    border: `1px solid ${C.border}`, borderRadius: 6,
    fontFamily: "monospace", fontSize: 12, lineHeight: 1.6,
    background: C.cream, color: C.slate, outline: "none",
    resize: "vertical", boxSizing: "border-box",
  },
  btn: (color = C.slate) => ({
    padding: "8px 18px", borderRadius: 6, border: "none",
    cursor: "pointer", fontFamily: "Helvetica, sans-serif",
    fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
    textTransform: "uppercase", background: color, color: C.white,
  }),
  tab: (active) => ({
    padding: "8px 16px", border: "none", cursor: "pointer",
    fontFamily: "Helvetica, sans-serif", fontSize: 11,
    fontWeight: active ? 700 : 400, letterSpacing: "0.06em",
    textTransform: "uppercase",
    color: active ? C.black : C.muted,
    background: "transparent",
    borderBottom: active ? `2px solid ${C.blue}` : "2px solid transparent",
  }),
};

const PROMPT_AGENTS = [
  { id: "voice_assistant", label: "Voice Assistant (Athena)" },
  { id: "content_agent",   label: "Content Agent (MedTech Meridian)" },
  { id: "coaching_brief",  label: "Coaching Brief Agent" },
  { id: "iso_coach",       label: "ISO 13485 Coach Agent" },
  { id: "briefing_agent",  label: "Daily Briefing Agent" },
];

function Field({ label, keyPath, value, type = "text", onSave }) {
  const [val, setVal] = useState(value ?? "");
  const [saved, setSaved] = useState(false);

  useEffect(() => setVal(value ?? ""), [value]);

  const save = () => {
    const parsed = type === "number" ? parseFloat(val) : type === "boolean" ? val === "true" : val;
    onSave(keyPath, parsed);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <label style={S.label}>{label}</label>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          style={S.input}
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === "Enter" && save()}
          type={type === "number" ? "number" : "text"}
          step={type === "number" ? "0.001" : undefined}
        />
        <button style={S.btn(saved ? C.green : C.slate)} onClick={save}>
          {saved ? "Saved" : "Save"}
        </button>
      </div>
    </div>
  );
}

function PromptEditor({ agentId, label, prompt, onSave }) {
  const [val,   setVal]   = useState(prompt || "");
  const [saved, setSaved] = useState(false);

  useEffect(() => setVal(prompt || ""), [prompt]);

  const save = async () => {
    try {
      const res = await fetch(`${API}/api/settings/prompt/${agentId}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ prompt: val }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
        onSave(agentId, val);
      }
    } catch {}
  };

  return (
    <div style={{ ...S.card, marginBottom: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <span style={{ fontFamily: "Helvetica, sans-serif", fontSize: 13, fontWeight: 600, color: C.black }}>
          {label}
        </span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {saved && <span style={{ fontFamily: "Helvetica, sans-serif", fontSize: 11, color: C.green }}>Saved</span>}
          <button style={S.btn(saved ? C.green : C.teal)} onClick={save}>
            Save Prompt
          </button>
        </div>
      </div>
      <textarea
        style={{ ...S.textarea, minHeight: 140 }}
        value={val}
        onChange={e => setVal(e.target.value)}
        placeholder="Enter system prompt..."
      />
      <div style={{ fontFamily: "Helvetica, sans-serif", fontSize: 10, color: C.muted, marginTop: 6 }}>
        {val.length} characters · {val.split(/\s+/).filter(Boolean).length} words
      </div>
    </div>
  );
}

export default function SettingsView() {
  const [data,      setData]      = useState(null);
  const [activeTab, setActiveTab] = useState("voice");
  const [status,    setStatus]    = useState("");
  const [resetting, setResetting] = useState(false);

  const loadSettings = useCallback(() => {
    fetch(`${API}/api/settings`)
      .then(r => r.json())
      .then(setData)
      .catch(() => setData(null));
  }, []);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  const saveSetting = useCallback(async (keyPath, value) => {
    try {
      await fetch(`${API}/api/settings`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ [keyPath]: value }),
      });
      setStatus(`Saved: ${keyPath}`);
      setTimeout(() => setStatus(""), 2000);
      loadSettings();
    } catch {
      setStatus("Save failed");
    }
  }, [loadSettings]);

  const savePrompt = useCallback((agentId, prompt) => {
    loadSettings();
  }, [loadSettings]);

  const resetAll = async () => {
    if (!window.confirm("Reset all settings to defaults? This cannot be undone.")) return;
    setResetting(true);
    try {
      await fetch(`${API}/api/settings/reset`, { method: "POST" });
      loadSettings();
      setStatus("Reset to defaults");
      setTimeout(() => setStatus(""), 3000);
    } catch {}
    setResetting(false);
  };

  const TABS = [
    { id: "voice",     label: "Voice" },
    { id: "agents",    label: "Agents" },
    { id: "documents", label: "Documents" },
    { id: "prompts",   label: "Prompts" },
    { id: "coaching",  label: "Coaching" },
  ];

  if (!data) return (
    <div style={{ color: C.muted, fontFamily: "Helvetica, sans-serif", fontSize: 13 }}>
      Loading settings... Make sure settings_manager.py is in ~/Athena/agents/
    </div>
  );

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: "normal", color: C.black, margin: 0 }}>Settings</h2>
          <div style={{ fontFamily: "Helvetica, sans-serif", fontSize: 11, color: C.muted, marginTop: 3 }}>
            Changes take effect on the next agent run · Last updated: {data.meta?.updated_at?.slice(0, 16).replace("T", " ")}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {status && <span style={{ fontFamily: "Helvetica, sans-serif", fontSize: 11, color: C.teal }}>{status}</span>}
          <button style={S.btn(C.muted)} onClick={resetAll} disabled={resetting}>
            {resetting ? "Resetting..." : "Reset Defaults"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: `1px solid ${C.border}`, marginBottom: 24, display: "flex" }}>
        {TABS.map(t => (
          <button key={t.id} style={S.tab(activeTab === t.id)} onClick={() => setActiveTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Voice tab */}
      {activeTab === "voice" && (
        <div>
          <div style={S.card}>
            <span style={S.label}>Wake word & detection</span>
            <Field label="Wake word model"      keyPath="voice.wake_word"         value={data.voice?.wake_word}         onSave={saveSetting} />
            <Field label="Wake threshold (0–1)" keyPath="voice.wake_threshold"    value={data.voice?.wake_threshold}    type="number" onSave={saveSetting} />
            <Field label="Silence threshold"    keyPath="voice.silence_threshold" value={data.voice?.silence_threshold} type="number" onSave={saveSetting} />
            <Field label="Silence duration (s)" keyPath="voice.silence_duration"  value={data.voice?.silence_duration}  type="number" onSave={saveSetting} />
            <Field label="Max record (s)"       keyPath="voice.max_record_sec"    value={data.voice?.max_record_sec}    type="number" onSave={saveSetting} />
            <Field label="Whisper model"        keyPath="voice.whisper_model"     value={data.voice?.whisper_model}     onSave={saveSetting} />
          </div>
          <div style={{ ...S.card, background: C.ltgray }}>
            <span style={{ fontFamily: "Helvetica, sans-serif", fontSize: 11, color: C.muted, lineHeight: 1.7 }}>
              <strong>Whisper models:</strong> tiny.en (fastest) · base.en (default) · small.en (better) · medium.en (best)<br />
              <strong>Silence threshold:</strong> lower = more sensitive mic · higher = cuts off background noise<br />
              <strong>Wake word:</strong> "alexa" uses built-in model · set to full path for custom Hi Athena model
            </span>
          </div>
        </div>
      )}

      {/* Agents tab */}
      {activeTab === "agents" && (
        <div>
          <div style={S.card}>
            <span style={S.label}>RAG ingestion agent</span>
            <Field label="Chunk size (tokens)"   keyPath="rag.chunk_size"     value={data.rag?.chunk_size}     type="number" onSave={saveSetting} />
            <Field label="Chunk overlap"         keyPath="rag.chunk_overlap"  value={data.rag?.chunk_overlap}  type="number" onSave={saveSetting} />
            <Field label="Max RSS items"         keyPath="rag.max_rss_items"  value={data.rag?.max_rss_items}  type="number" onSave={saveSetting} />
            <Field label="Tavily results/query"  keyPath="rag.tavily_results" value={data.rag?.tavily_results} type="number" onSave={saveSetting} />
            <Field label="Schedule time (24h)"   keyPath="rag.schedule_time"  value={data.rag?.schedule_time}  onSave={saveSetting} />
          </div>
          <div style={S.card}>
            <span style={S.label}>Content agent</span>
            <Field label="Topic dedup window (days)" keyPath="content.topic_dedup_days"   value={data.content?.topic_dedup_days}   type="number" onSave={saveSetting} />
            <Field label="Max article tokens"        keyPath="content.max_article_tokens" value={data.content?.max_article_tokens} type="number" onSave={saveSetting} />
            <Field label="Word count target"         keyPath="content.word_count_target"  value={data.content?.word_count_target}  onSave={saveSetting} />
            <Field label="Schedule day"              keyPath="content.schedule_day"       value={data.content?.schedule_day}       onSave={saveSetting} />
            <Field label="Schedule time (24h)"       keyPath="content.schedule_time"      value={data.content?.schedule_time}      onSave={saveSetting} />
          </div>
          <div style={S.card}>
            <span style={S.label}>Briefing agent</span>
            <Field label="Max items per briefing"  keyPath="briefing.max_items"       value={data.briefing?.max_items}       type="number" onSave={saveSetting} />
            <Field label="Brave search queries"    keyPath="briefing.brave_queries"   value={data.briefing?.brave_queries}   type="number" onSave={saveSetting} />
            <Field label="Seen item window (days)" keyPath="briefing.seen_item_days"  value={data.briefing?.seen_item_days}  type="number" onSave={saveSetting} />
            <Field label="Schedule time (24h)"     keyPath="briefing.schedule_time"   value={data.briefing?.schedule_time}   onSave={saveSetting} />
          </div>
        </div>
      )}

      {/* Documents tab */}
      {activeTab === "documents" && (
        <div>
          <div style={S.card}>
            <span style={S.label}>Company identity</span>
            <Field label="Company name" keyPath="documents.company_name" value={data.documents?.company_name} onSave={saveSetting} />
            <Field label="Tagline"      keyPath="documents.tagline"      value={data.documents?.tagline}      onSave={saveSetting} />
            <Field label="Location"     keyPath="documents.location"     value={data.documents?.location}     onSave={saveSetting} />
            <Field label="Website"      keyPath="documents.website"      value={data.documents?.website}      onSave={saveSetting} />
            <Field label="Email"        keyPath="documents.email"        value={data.documents?.email}        onSave={saveSetting} />
          </div>
          <div style={S.card}>
            <span style={S.label}>Typography</span>
            <Field label="Font"           keyPath="documents.font"           value={data.documents?.font}           onSave={saveSetting} />
            <Field label="Body font size" keyPath="documents.font_size_body" value={data.documents?.font_size_body} type="number" onSave={saveSetting} />
            <Field label="H1 font size"   keyPath="documents.font_size_h1"   value={data.documents?.font_size_h1}   type="number" onSave={saveSetting} />
            <Field label="H2 font size"   keyPath="documents.font_size_h2"   value={data.documents?.font_size_h2}   type="number" onSave={saveSetting} />
          </div>
          <div style={S.card}>
            <span style={S.label}>Disclaimer text</span>
            <textarea
              style={{ ...S.textarea, minHeight: 100 }}
              defaultValue={data.documents?.disclaimer}
              onBlur={e => saveSetting("documents.disclaimer", e.target.value)}
            />
            <div style={{ fontFamily: "Helvetica, sans-serif", fontSize: 10, color: C.muted, marginTop: 6 }}>
              Appended to every generated document. Click outside to save.
            </div>
          </div>
          <div style={S.card}>
            <span style={S.label}>Footer text</span>
            <textarea
              style={{ ...S.textarea, minHeight: 60 }}
              defaultValue={data.documents?.footer_text}
              onBlur={e => saveSetting("documents.footer_text", e.target.value)}
            />
          </div>
        </div>
      )}

      {/* Prompts tab */}
      {activeTab === "prompts" && (
        <div>
          <div style={{ ...S.card, background: C.ltgray, marginBottom: 20 }}>
            <span style={{ fontFamily: "Helvetica, sans-serif", fontSize: 11, color: C.muted, lineHeight: 1.7 }}>
              These are the system prompts sent to Claude for each agent. Edit to change tone, scope, or output format.
              Changes take effect on the next agent run. Keep prompts focused — every extra word costs tokens.
            </span>
          </div>
          {PROMPT_AGENTS.map(agent => (
            <PromptEditor
              key={agent.id}
              agentId={agent.id}
              label={agent.label}
              prompt={data.prompts?.[agent.id]}
              onSave={savePrompt}
            />
          ))}
        </div>
      )}

      {/* Coaching tab */}
      {activeTab === "coaching" && (
        <div>
          <div style={S.card}>
            <span style={S.label}>Program pricing</span>
            {Object.entries(data.coaching?.programs || {}).map(([id, prog]) => (
              <div key={id} style={{ display: "flex", gap: 12, marginBottom: 12, alignItems: "center" }}>
                <div style={{ width: 180, fontFamily: "Helvetica, sans-serif", fontSize: 12, color: C.slate, fontWeight: 500 }}>
                  {prog.name}
                </div>
                <div style={{ flex: 1 }}>
                  <Field
                    label="Price"
                    keyPath={`coaching.programs.${id}.price`}
                    value={prog.price}
                    onSave={saveSetting}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <Field
                    label="Duration"
                    keyPath={`coaching.programs.${id}.duration`}
                    value={prog.duration}
                    onSave={saveSetting}
                  />
                </div>
              </div>
            ))}
          </div>
          <div style={S.card}>
            <span style={S.label}>A la carte pricing</span>
            {Object.entries(data.coaching?.alacarte || {}).map(([id, price]) => (
              <Field
                key={id}
                label={id.replace(/_/g, " ")}
                keyPath={`coaching.alacarte.${id}`}
                value={price}
                onSave={saveSetting}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
