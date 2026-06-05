import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

const C = {
  navy:   "#0A2540",
  ocean:  "#1A6FA3",
  teal:   "#1F7A6D",
  warm:   "#C4922A",
  slate:  "#2C3E50",
  ink:    "#0D1B2A",
  fog:    "#8A9BB0",
  muted:  "#A0AABD",
  pearl:  "#F8F9FB",
  cloud:  "#EEF1F6",
  mist:   "#DDE2EC",
  border: "#E4E8F0",
  blue:   "#5B7FA6",
  green:  "#2ECC71",
  red:    "#E74C3C",
};

const F = { sans: "'Helvetica Neue', Helvetica, Arial, sans-serif" };

const DECK_TYPES = [
  { value: "strategy",   label: "Strategy" },
  { value: "pitch",      label: "Pitch Deck" },
  { value: "regulatory", label: "Regulatory Pathway" },
  { value: "coaching",   label: "Coaching Plan" },
  { value: "ma",         label: "M&A Diligence" },
  { value: "briefing",   label: "Intelligence Briefing" },
];

function parseDeckMeta(filename) {
  // Format: YYYYMMDD_HHMMSS_slug.pptx
  const base  = filename.replace(/\.pptx$/i, "");
  const parts = base.split("_");
  let date = "", time = "", label = "";
  if (parts.length >= 2 && /^\d{8}$/.test(parts[0]) && /^\d{6}$/.test(parts[1])) {
    const d = parts[0];
    const t = parts[1];
    date  = `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`;
    time  = `${t.slice(0,2)}:${t.slice(2,4)}`;
    label = parts.slice(2).join(" ").replace(/_/g, " ");
  } else {
    label = base.replace(/_/g, " ");
  }
  return { date, time, label: label || filename };
}

export default function DeckView({ runningAgents }) {
  const [decks,   setDecks]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [topic,   setTopic]   = useState("");
  const [dtype,   setDtype]   = useState("strategy");
  const [client,  setClient]  = useState("");
  const [context, setContext] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg,  setStatusMsg]  = useState("");
  const prevRunning = useRef(false);

  const loadDecks = () =>
    fetch(`${API}/api/decks`)
      .then(r => r.json())
      .then(d => { setDecks(d.decks || []); setLoading(false); })
      .catch(() => setLoading(false));

  useEffect(() => { loadDecks(); }, []);

  // Auto-refresh list when deck_agent finishes
  useEffect(() => {
    const isRunning = runningAgents?.has("deck_agent");
    if (prevRunning.current && !isRunning) {
      loadDecks();
      setStatusMsg("");
    }
    prevRunning.current = !!isRunning;
  }, [runningAgents]);

  const isGenerating = runningAgents?.has("deck_agent") || submitting;

  const handleSubmit = () => {
    if (!topic.trim()) return;
    setSubmitting(true);
    setStatusMsg("Queuing deck…");
    fetch(`${API}/api/decks/generate`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ topic: topic.trim(), deck_type: dtype, client_name: client.trim(), context: context.trim() }),
    })
      .then(r => r.json())
      .then(() => {
        setStatusMsg("Building your deck — this takes 3–5 minutes.");
        setTopic("");
        setClient("");
        setContext("");
      })
      .catch(() => setStatusMsg("Error starting deck generation."))
      .finally(() => setSubmitting(false));
  };

  return (
    <div style={{ fontFamily: F.sans }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: C.ink, margin: "0 0 4px", letterSpacing: "-0.01em" }}>
          Decks
        </h2>
        <span style={{ fontSize: 11, color: C.fog }}>
          Generate client-facing PPTX slide decks · McKinsey/PwC quality
        </span>
      </div>

      {/* ── Generate form ──────────────────────────────────────────────────── */}
      <div style={{
        background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 12,
        padding: "20px 24px", marginBottom: 24,
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: C.navy, letterSpacing: "0.06em",
                      textTransform: "uppercase", marginBottom: 14 }}>
          Generate Deck
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 160px", gap: 10, marginBottom: 10 }}>
          <input
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
            placeholder="Deck topic — e.g. Q3 Regulatory Strategy, Biocom Pitch"
            disabled={isGenerating}
            style={{
              padding: "9px 13px", border: `1px solid ${C.mist}`, borderRadius: 7,
              fontFamily: F.sans, fontSize: 13, background: isGenerating ? C.cloud : "#fff",
              color: C.ink, outline: "none", boxSizing: "border-box",
            }}
          />
          <select
            value={dtype}
            onChange={e => setDtype(e.target.value)}
            disabled={isGenerating}
            style={{
              padding: "9px 12px", border: `1px solid ${C.mist}`, borderRadius: 7,
              fontFamily: F.sans, fontSize: 13, background: isGenerating ? C.cloud : "#fff",
              color: C.ink, outline: "none", cursor: "pointer",
            }}
          >
            {DECK_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
          <input
            value={client}
            onChange={e => setClient(e.target.value)}
            placeholder="Client / audience (optional)"
            disabled={isGenerating}
            style={{
              padding: "9px 13px", border: `1px solid ${C.mist}`, borderRadius: 7,
              fontFamily: F.sans, fontSize: 13, background: isGenerating ? C.cloud : "#fff",
              color: C.ink, outline: "none", boxSizing: "border-box",
            }}
          />
          <input
            value={context}
            onChange={e => setContext(e.target.value)}
            placeholder="Additional context (optional)"
            disabled={isGenerating}
            style={{
              padding: "9px 13px", border: `1px solid ${C.mist}`, borderRadius: 7,
              fontFamily: F.sans, fontSize: 13, background: isGenerating ? C.cloud : "#fff",
              color: C.ink, outline: "none", boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button
            onClick={handleSubmit}
            disabled={isGenerating || !topic.trim()}
            style={{
              padding: "9px 22px", borderRadius: 7, cursor: isGenerating || !topic.trim() ? "default" : "pointer",
              fontFamily: F.sans, fontSize: 13, fontWeight: 600,
              background: isGenerating || !topic.trim() ? C.mist : C.navy,
              color: isGenerating || !topic.trim() ? C.fog : "#fff",
              border: "none", transition: "background 0.15s",
            }}
          >
            {isGenerating ? "Building…" : "Build Deck"}
          </button>

          {isGenerating && (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                display: "inline-block", width: 14, height: 14, borderRadius: "50%",
                border: `2px solid ${C.ocean}`, borderTopColor: "transparent",
                animation: "deckSpin 0.8s linear infinite",
              }} />
              <span style={{ fontSize: 12, color: C.ocean }}>
                {statusMsg || "Building deck — 3–5 minutes…"}
              </span>
            </div>
          )}
          {!isGenerating && statusMsg && (
            <span style={{ fontSize: 12, color: statusMsg.includes("Error") ? C.red : C.teal }}>
              {statusMsg}
            </span>
          )}
        </div>

        <style>{`@keyframes deckSpin { to { transform: rotate(360deg); } }`}</style>
      </div>

      {/* ── Deck list ──────────────────────────────────────────────────────── */}
      <div style={{ background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 12, padding: "20px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: C.navy, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Generated Decks
          </span>
          <button
            onClick={loadDecks}
            style={{ padding: "4px 12px", borderRadius: 6, border: `1px solid ${C.mist}`,
                     background: "transparent", color: C.fog, fontFamily: F.sans, fontSize: 11,
                     cursor: "pointer" }}
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <div style={{ color: C.muted, fontSize: 13, padding: "12px 0" }}>Loading…</div>
        ) : decks.length === 0 ? (
          <div style={{ color: C.muted, fontSize: 13, padding: "12px 0", fontStyle: "italic" }}>
            No decks generated yet. Use the form above or say "Athena, build me a deck on…"
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {decks.map((deck, i) => {
              const { date, time, label } = parseDeckMeta(deck.filename);
              return (
                <div key={deck.filename} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "11px 14px", borderRadius: 8,
                  background: i % 2 === 0 ? C.cloud : C.pearl,
                  transition: "background 0.1s",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0 }}>
                    {/* Slide icon */}
                    <div style={{
                      width: 32, height: 32, borderRadius: 6, flexShrink: 0,
                      background: C.navy, display: "flex", alignItems: "center",
                      justifyContent: "center",
                    }}>
                      <span style={{ fontSize: 14, lineHeight: 1 }}>📊</span>
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div style={{
                        fontSize: 13, fontWeight: 600, color: C.ink,
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                        maxWidth: 420, textTransform: "capitalize",
                      }}>
                        {label || deck.filename}
                      </div>
                      <div style={{ fontSize: 11, color: C.fog, marginTop: 2 }}>
                        {date}{time ? ` · ${time}` : ""}
                        {" · "}{deck.filename}
                      </div>
                    </div>
                  </div>

                  <a
                    href={`${API}/api/decks/download/${encodeURIComponent(deck.filename)}`}
                    download={deck.filename}
                    style={{
                      flexShrink: 0, padding: "6px 14px", borderRadius: 6,
                      background: C.ocean, color: "#fff",
                      fontFamily: F.sans, fontSize: 12, fontWeight: 600,
                      textDecoration: "none", marginLeft: 16,
                      transition: "background 0.15s",
                    }}
                  >
                    Download
                  </a>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Voice tip */}
      <div style={{ marginTop: 16, padding: "12px 16px", borderRadius: 8,
                    background: C.cloud, border: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 11, color: C.fog }}>
          <strong style={{ color: C.slate }}>Voice:</strong>
          {" "}Say <em>"Athena, build me a [strategy / pitch / regulatory] deck on [topic]"</em> to generate hands-free.
        </span>
      </div>
    </div>
  );
}
