import { useState, useEffect, useRef, useCallback } from "react";
import { authHdr } from "./api.js";

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

const BUILD_STAGES = [
  { label: "Cover & Title",        secs: 0   },
  { label: "Executive Summary",    secs: 30  },
  { label: "Situation / Context",  secs: 70  },
  { label: "Analysis Slides",      secs: 110 },
  { label: "Recommendations",      secs: 150 },
  { label: "Next Steps",           secs: 180 },
  { label: "Finalising & Export",  secs: 210 },
];

function parseDeckMeta(filename) {
  const base  = filename.replace(/\.pptx$/i, "");
  const parts = base.split("_");
  let date = "", time = "", label = "";
  if (parts.length >= 2 && /^\d{8}$/.test(parts[0]) && /^\d{6}$/.test(parts[1])) {
    const d = parts[0], t = parts[1];
    date  = `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`;
    time  = `${t.slice(0,2)}:${t.slice(2,4)}`;
    label = parts.slice(2).join(" ").replace(/_/g, " ");
  } else {
    label = base.replace(/_/g, " ");
  }
  return { date, time, label: label || filename };
}

// ── Slide Preview Modal ────────────────────────────────────────────────────────

function SlidePreviewModal({ filename, onClose }) {
  const [slides, setSlides] = useState(null);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const { label } = parseDeckMeta(filename);

  useEffect(() => {
    fetch(`${API}/api/decks/${encodeURIComponent(filename)}/slides`, { headers: authHdr() })
      .then(r => r.json())
      .then(d => { setSlides(d.slides || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [filename]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" && slides) setCurrent(c => Math.min(c + 1, slides.length - 1));
      if (e.key === "ArrowLeft")  setCurrent(c => Math.max(c - 1, 0));
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [slides, onClose]);

  const slide = slides?.[current];

  // Heuristic: is this a cover/section-divider slide?
  const isDark = current === 0 ||
    (slide?.title && /^(section|appendix)/i.test(slide.title.trim()));

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(10,20,35,0.80)",
      display: "flex", flexDirection: "column", alignItems: "center",
      justifyContent: "center", zIndex: 1000,
    }} onClick={onClose}>
      {/* Modal box */}
      <div style={{
        width: "min(900px, 92vw)", background: "#fff", borderRadius: 14,
        boxShadow: "0 24px 64px rgba(0,0,0,0.35)",
        display: "flex", flexDirection: "column", overflow: "hidden",
        maxHeight: "90vh",
      }} onClick={e => e.stopPropagation()}>

        {/* Header bar */}
        <div style={{
          background: C.navy, padding: "14px 20px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#fff",
                          textTransform: "capitalize", marginBottom: 2 }}>
              {label}
            </div>
            <div style={{ fontSize: 10, color: "#A8C4D8", letterSpacing: "0.05em" }}>
              ADVANCING HUMAN INTELLIGENCE — LATITUDE MEDTECH LLC
            </div>
          </div>
          <button onClick={onClose} style={{
            background: "rgba(255,255,255,0.12)", border: "none",
            color: "#fff", cursor: "pointer", borderRadius: 6,
            padding: "5px 12px", fontSize: 13, fontFamily: F.sans,
          }}>✕ Close</button>
        </div>

        {/* Slide canvas */}
        <div style={{ flex: 1, overflow: "auto", background: C.cloud, padding: "24px" }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: 40, color: C.muted, fontSize: 14 }}>
              Loading slides…
            </div>
          ) : !slides || slides.length === 0 ? (
            <div style={{ textAlign: "center", padding: 40, color: C.muted, fontSize: 14 }}>
              Could not extract slide content.
            </div>
          ) : (
            <div style={{
              background: isDark ? C.navy : "#fff",
              borderRadius: 8, minHeight: 340,
              padding: "32px 40px",
              border: `1px solid ${C.border}`,
              boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
              position: "relative",
            }}>
              {/* Slide number badge */}
              <div style={{
                position: "absolute", top: 14, right: 16,
                background: isDark ? "rgba(26,111,163,0.5)" : C.cloud,
                color: isDark ? "#A8C4D8" : C.fog,
                fontSize: 10, fontWeight: 600, padding: "3px 9px", borderRadius: 10,
                letterSpacing: "0.06em",
              }}>
                {current + 1} / {slides.length}
              </div>

              {/* Slide title */}
              {slide?.title && (
                <div style={{
                  fontSize: current === 0 ? 26 : 20,
                  fontWeight: 700,
                  color: isDark ? "#fff" : C.navy,
                  marginBottom: 18,
                  lineHeight: 1.25,
                  fontFamily: F.sans,
                  textTransform: current === 0 ? "none" : "none",
                  maxWidth: "85%",
                }}>
                  {slide.title}
                </div>
              )}

              {/* Body texts */}
              {slide?.texts?.map((t, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 10,
                }}>
                  <span style={{
                    flexShrink: 0, width: 4, height: 4,
                    borderRadius: 2, background: isDark ? "#1A6FA3" : C.blue,
                    marginTop: 8,
                  }}/>
                  <div style={{
                    fontSize: 13, color: isDark ? "#CBD8E8" : C.slate,
                    lineHeight: 1.5, fontFamily: F.sans,
                  }}>
                    {t}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div style={{
          background: "#fff", borderTop: `1px solid ${C.border}`,
          padding: "12px 20px", display: "flex",
          alignItems: "center", justifyContent: "space-between",
        }}>
          <button
            disabled={current === 0}
            onClick={() => setCurrent(c => c - 1)}
            style={{
              padding: "7px 18px", borderRadius: 6, cursor: current === 0 ? "default" : "pointer",
              border: `1px solid ${C.mist}`, background: current === 0 ? C.cloud : "#fff",
              color: current === 0 ? C.muted : C.slate, fontFamily: F.sans, fontSize: 13,
            }}
          >← Previous</button>

          {/* Thumbnail strip */}
          <div style={{ display: "flex", gap: 5, overflow: "hidden", maxWidth: 480, flexWrap: "nowrap" }}>
            {(slides || []).map((_, i) => (
              <button key={i} onClick={() => setCurrent(i)} style={{
                width: 28, height: 18, borderRadius: 3, cursor: "pointer",
                border: `2px solid ${i === current ? C.ocean : C.mist}`,
                background: i === current ? C.ocean : C.cloud,
                flexShrink: 0, fontSize: 8, color: i === current ? "#fff" : C.muted,
                fontFamily: F.sans,
              }}>{i + 1}</button>
            ))}
          </div>

          <button
            disabled={!slides || current === slides.length - 1}
            onClick={() => setCurrent(c => c + 1)}
            style={{
              padding: "7px 18px", borderRadius: 6,
              cursor: !slides || current === slides.length - 1 ? "default" : "pointer",
              border: `1px solid ${C.mist}`,
              background: !slides || current === slides.length - 1 ? C.cloud : C.navy,
              color: !slides || current === slides.length - 1 ? C.muted : "#fff",
              fontFamily: F.sans, fontSize: 13, fontWeight: 600,
            }}
          >Next →</button>
        </div>
      </div>
    </div>
  );
}

// ── Bulk Action Bar ────────────────────────────────────────────────────────────

function BulkBar({ count, total, onDeleteSelected, onAcceptSelected, onRejectSelected,
                   onSelectAll, onClear }) {
  if (count === 0) return null;
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10, padding: "10px 16px",
      background: C.navy, borderRadius: 8, marginBottom: 10,
      border: `1px solid ${C.ocean}44`,
    }}>
      <span style={{ fontSize: 12, color: "#A8C4D8", flexShrink: 0 }}>
        {count} of {total} selected
      </span>
      <div style={{ flex: 1 }}/>
      <button onClick={onSelectAll} style={_bulkBtn(C.cloud, C.slate)}>Select All</button>
      <button onClick={onClear}     style={_bulkBtn(C.cloud, C.slate)}>Clear</button>
      <div style={{ width: 1, height: 18, background: "rgba(255,255,255,0.15)" }}/>
      <button onClick={onAcceptSelected} style={_bulkBtn("#1A6FA3", "#fff", true)}>
        ✓ Accept
      </button>
      <button onClick={onRejectSelected} style={_bulkBtn("#C4922A", "#fff", true)}>
        ✕ Reject
      </button>
      <button onClick={onDeleteSelected} style={_bulkBtn(C.red, "#fff", true)}>
        Delete
      </button>
    </div>
  );
}
function _bulkBtn(bg, color, strong) {
  return {
    padding: "5px 12px", borderRadius: 5, border: "none", cursor: "pointer",
    background: bg, color, fontFamily: F.sans, fontSize: 11,
    fontWeight: strong ? 700 : 500,
  };
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function DeckView({ runningAgents }) {
  const [decks,      setDecks]      = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [topic,      setTopic]      = useState("");
  const [dtype,      setDtype]      = useState("strategy");
  const [client,     setClient]     = useState("");
  const [context,    setContext]    = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [statusMsg,  setStatusMsg]  = useState("");
  const [activeBuild, setActiveBuild] = useState(null);
  const [buildElapsed, setBuildElapsed] = useState(0);
  const [selected,   setSelected]   = useState(new Set()); // bulk selection
  const [preview,    setPreview]    = useState(null);      // filename for slide preview
  const prevRunning = useRef(false);
  const timerRef    = useRef(null);

  const loadDecks = useCallback(() =>
    fetch(`${API}/api/decks`, { headers: authHdr() })
      .then(r => r.json())
      .then(d => { setDecks(d.decks || []); setLoading(false); })
      .catch(() => setLoading(false)), []);

  useEffect(() => { loadDecks(); }, [loadDecks]);

  useEffect(() => {
    const isRunning = runningAgents?.has("deck_agent");
    if (prevRunning.current && !isRunning) {
      loadDecks();
      setStatusMsg(""); setActiveBuild(null);
      setBuildElapsed(0); clearInterval(timerRef.current);
    }
    prevRunning.current = !!isRunning;
  }, [runningAgents, loadDecks]);

  useEffect(() => {
    if (activeBuild) {
      timerRef.current = setInterval(() =>
        setBuildElapsed(Math.floor((Date.now() - activeBuild.startedAt) / 1000)), 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [activeBuild]);

  const isGenerating = runningAgents?.has("deck_agent") || submitting;

  const handleSubmit = () => {
    if (!topic.trim()) return;
    setSubmitting(true);
    setStatusMsg("Queuing deck…");
    const buildInfo = { topic: topic.trim(), dtype, client: client.trim(),
                        context: context.trim(), startedAt: Date.now() };
    fetch(`${API}/api/decks/generate`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
      body: JSON.stringify({ topic: buildInfo.topic, deck_type: dtype,
                             client_name: buildInfo.client, context: buildInfo.context }),
    })
      .then(r => r.json())
      .then(() => {
        setStatusMsg(""); setActiveBuild(buildInfo); setBuildElapsed(0);
        setTopic(""); setClient(""); setContext("");
      })
      .catch(() => setStatusMsg("Error starting deck generation."))
      .finally(() => setSubmitting(false));
  };

  const currentStage = activeBuild
    ? BUILD_STAGES.reduce((acc, s) => buildElapsed >= s.secs ? s : acc, BUILD_STAGES[0])
    : null;
  const stageIdx = currentStage ? BUILD_STAGES.indexOf(currentStage) : -1;
  const fmtElapsed = (s) => s < 60 ? `${s}s` : `${Math.floor(s/60)}m ${s%60}s`;

  // ── Selection helpers ────────────────────────────────────────────────────────
  const toggleSelect = (filename) =>
    setSelected(prev => {
      const next = new Set(prev);
      next.has(filename) ? next.delete(filename) : next.add(filename);
      return next;
    });
  const selectAll  = () => setSelected(new Set(decks.map(d => d.filename)));
  const clearAll   = () => setSelected(new Set());

  const bulkDelete = async () => {
    if (!selected.size) return;
    if (!window.confirm(`Permanently delete ${selected.size} deck(s)?`)) return;
    await fetch(`${API}/api/decks/bulk-delete`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
      body: JSON.stringify({ filenames: [...selected] }),
    });
    clearAll(); loadDecks();
  };
  const bulkAccept = async () => {
    if (!selected.size) return;
    await fetch(`${API}/api/decks/bulk-accept`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
      body: JSON.stringify({ filenames: [...selected] }),
    });
    clearAll(); loadDecks();
  };
  const bulkReject = async () => {
    if (!selected.size) return;
    if (!window.confirm(`Reject & delete ${selected.size} deck(s)?`)) return;
    await fetch(`${API}/api/decks/bulk-reject`, {
      method: "POST", headers: { "Content-Type": "application/json", ...authHdr() },
      body: JSON.stringify({ filenames: [...selected] }),
    });
    clearAll(); loadDecks();
  };

  return (
    <div style={{ fontFamily: F.sans }}>

      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 17, fontWeight: 700, color: C.ink, margin: "0 0 3px",
                     letterSpacing: "-0.01em" }}>
          Decks
        </h2>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 11, color: C.fog }}>
            Generate client-facing PPTX slide decks · McKinsey/PwC quality
          </span>
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: "0.08em",
            color: C.ocean, background: `${C.ocean}18`,
            padding: "2px 8px", borderRadius: 10, textTransform: "uppercase",
          }}>
            Advancing Human Intelligence
          </span>
        </div>
      </div>

      {/* ── Generate form ───────────────────────────────────────────────────── */}
      <div style={{
        background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 12,
        padding: "20px 24px", marginBottom: 20,
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: C.navy,
                      letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 14 }}>
          Generate Deck
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 168px", gap: 10, marginBottom: 10 }}>
          <input
            value={topic} onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSubmit()}
            placeholder="Deck topic — e.g. Q3 Regulatory Strategy, Biocom Pitch"
            disabled={isGenerating}
            style={_input(isGenerating)}
          />
          <select value={dtype} onChange={e => setDtype(e.target.value)}
            disabled={isGenerating} style={_input(isGenerating)}>
            {DECK_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
          <input value={client} onChange={e => setClient(e.target.value)}
            placeholder="Client / audience (optional)" disabled={isGenerating}
            style={_input(isGenerating)} />
          <input value={context} onChange={e => setContext(e.target.value)}
            placeholder="Additional context (optional)" disabled={isGenerating}
            style={_input(isGenerating)} />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button onClick={handleSubmit} disabled={isGenerating || !topic.trim()} style={{
            padding: "9px 22px", borderRadius: 7,
            cursor: isGenerating || !topic.trim() ? "default" : "pointer",
            fontFamily: F.sans, fontSize: 13, fontWeight: 700,
            background: isGenerating || !topic.trim() ? C.mist : C.navy,
            color: isGenerating || !topic.trim() ? C.fog : "#fff",
            border: "none", transition: "background 0.15s",
          }}>
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
      </div>

      {/* ── Active build panel ───────────────────────────────────────────────── */}
      {activeBuild && (
        <div style={{
          background: C.navy, borderRadius: 12, padding: "20px 24px",
          marginBottom: 20, border: `1px solid ${C.ocean}44`,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between",
                        alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em",
                            textTransform: "uppercase", color: C.ocean, marginBottom: 6 }}>
                Building Deck — {fmtElapsed(buildElapsed)}
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
                {activeBuild.topic}
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <span style={_pill}>{DECK_TYPES.find(t => t.value === activeBuild.dtype)?.label}</span>
                {activeBuild.client && <span style={_pill}>Client: {activeBuild.client}</span>}
              </div>
            </div>
            <div style={{ width: 20, height: 20, border: `2px solid ${C.ocean}44`,
                          borderTopColor: C.ocean, borderRadius: "50%",
                          animation: "deckSpin 0.9s linear infinite", flexShrink: 0 }}/>
          </div>
          <div style={{ display: "flex", gap: 4 }}>
            {BUILD_STAGES.map((s, i) => (
              <div key={s.label} style={{ flex: 1 }} title={s.label}>
                <div style={{
                  height: 3, borderRadius: 2,
                  background: i < stageIdx ? C.ocean : i === stageIdx ? "#fff" : "rgba(255,255,255,0.12)",
                  transition: "background 0.4s",
                }}/>
                {i === stageIdx && (
                  <div style={{ fontSize: 9, color: "#A8C4D8", marginTop: 4,
                                whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {s.label}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Deck list ────────────────────────────────────────────────────────── */}
      <div style={{ background: C.pearl, border: `1px solid ${C.mist}`, borderRadius: 12,
                    padding: "18px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between",
                      alignItems: "center", marginBottom: 12 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: C.navy,
                         letterSpacing: "0.07em", textTransform: "uppercase" }}>
            Generated Decks
          </span>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {decks.length > 0 && (
              <label style={{ display: "flex", alignItems: "center", gap: 5,
                              fontSize: 11, color: C.fog, cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={selected.size === decks.length && decks.length > 0}
                  onChange={e => e.target.checked ? selectAll() : clearAll()}
                  style={{ cursor: "pointer" }}
                />
                All
              </label>
            )}
            <button onClick={loadDecks} style={{
              padding: "4px 12px", borderRadius: 6, border: `1px solid ${C.mist}`,
              background: "transparent", color: C.fog, fontFamily: F.sans,
              fontSize: 11, cursor: "pointer",
            }}>Refresh</button>
          </div>
        </div>

        <BulkBar
          count={selected.size} total={decks.length}
          onDeleteSelected={bulkDelete}
          onAcceptSelected={bulkAccept}
          onRejectSelected={bulkReject}
          onSelectAll={selectAll}
          onClear={clearAll}
        />

        {loading ? (
          <div style={{ color: C.muted, fontSize: 13, padding: "12px 0" }}>Loading…</div>
        ) : decks.length === 0 ? (
          <div style={{ color: C.muted, fontSize: 13, padding: "12px 0", fontStyle: "italic" }}>
            No decks generated yet. Use the form above or say "Athena, build me a deck on…"
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {decks.map((deck, i) => {
              const { date, time, label } = parseDeckMeta(deck.filename);
              const isSelected = selected.has(deck.filename);
              return (
                <div key={deck.filename} style={{
                  display: "flex", alignItems: "center",
                  padding: "11px 14px", borderRadius: 8,
                  background: isSelected
                    ? `${C.ocean}14`
                    : i % 2 === 0 ? C.cloud : C.pearl,
                  border: `1px solid ${isSelected ? C.ocean + "55" : "transparent"}`,
                  transition: "background 0.12s, border 0.12s",
                }}>
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelect(deck.filename)}
                    style={{ marginRight: 12, cursor: "pointer", flexShrink: 0 }}
                  />

                  {/* Slide icon */}
                  <div style={{
                    width: 34, height: 34, borderRadius: 7, flexShrink: 0,
                    background: C.navy, display: "flex", alignItems: "center",
                    justifyContent: "center", marginRight: 12,
                  }}>
                    <svg width="18" height="14" viewBox="0 0 18 14" fill="none">
                      <rect x="0" y="0" width="18" height="14" rx="1.5" fill="#1A6FA3"/>
                      <rect x="2" y="2" width="14" height="2" rx="1" fill="rgba(255,255,255,0.8)"/>
                      <rect x="2" y="6" width="10" height="1.5" rx="0.75" fill="rgba(255,255,255,0.5)"/>
                      <rect x="2" y="9" width="7" height="1.5" rx="0.75" fill="rgba(255,255,255,0.5)"/>
                    </svg>
                  </div>

                  {/* Meta */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                      fontSize: 13, fontWeight: 700, color: C.ink,
                      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                      textTransform: "capitalize", marginBottom: 2,
                    }}>
                      {label || deck.filename}
                    </div>
                    <div style={{ fontSize: 11, color: C.fog }}>
                      {date}{time ? ` · ${time}` : ""}{" · "}{deck.filename}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", gap: 7, flexShrink: 0, marginLeft: 12 }}>
                    <button
                      onClick={() => setPreview(deck.filename)}
                      style={_actionBtn(C.cloud, C.slate)}
                      title="Preview slides in browser"
                    >
                      Preview
                    </button>
                    <a
                      href={`${API}/api/decks/download/${encodeURIComponent(deck.filename)}`}
                      download={deck.filename}
                      style={_actionBtnLink(C.ocean, "#fff")}
                      title="Download PPTX"
                    >
                      Download
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Voice tip */}
      <div style={{ marginTop: 14, padding: "10px 16px", borderRadius: 8,
                    background: C.cloud, border: `1px solid ${C.border}` }}>
        <span style={{ fontSize: 11, color: C.fog }}>
          <strong style={{ color: C.slate }}>Voice:</strong>
          {" "}Say <em>"Athena, build me a [strategy / pitch / regulatory] deck on [topic]"</em> to generate hands-free.
        </span>
      </div>

      {/* Slide Preview Modal */}
      {preview && (
        <SlidePreviewModal filename={preview} onClose={() => setPreview(null)} />
      )}

      <style>{`
        @keyframes deckSpin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

// ── Style helpers ──────────────────────────────────────────────────────────────

const _pill = {
  fontSize: 10, color: "#A8C4D8", background: "rgba(255,255,255,0.08)",
  padding: "2px 8px", borderRadius: 10,
};

function _input(disabled) {
  return {
    padding: "9px 13px", border: `1px solid ${C.mist}`, borderRadius: 7,
    fontFamily: F.sans, fontSize: 13,
    background: disabled ? C.cloud : "#fff", color: C.ink,
    outline: "none", boxSizing: "border-box", width: "100%",
  };
}
function _actionBtn(bg, color) {
  return {
    padding: "6px 13px", borderRadius: 6, border: `1px solid ${C.mist}`,
    background: bg, color, fontFamily: F.sans, fontSize: 12,
    fontWeight: 600, cursor: "pointer",
  };
}
function _actionBtnLink(bg, color) {
  return {
    padding: "6px 13px", borderRadius: 6, textDecoration: "none",
    background: bg, color, fontFamily: F.sans, fontSize: 12,
    fontWeight: 600,
  };
}
