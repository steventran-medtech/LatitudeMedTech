/**
 * Athena Voice — Jarvis × McKinsey × Pacific UI
 *
 * Design brief:
 *   — Dark navy HUD panel (Pacific deep, not pure black)
 *   — Ocean blue (#1A6FA3) primary glow  →  La Jolla Cove
 *   — Gold (#C4922A) accent arcs          →  Coronado sunset
 *   — Teal (#1F7A6D) success / speaking   →  Torrey Pines
 *   — Clean Inter typography (McKinsey restraint)
 *   — Concentric animated rings (Jarvis energy)
 *   — No log clutter; just the orb + last exchange
 */

const API    = "http://localhost:8000";
const NAVY   = "#0A2540";
const OCEAN  = "#1A6FA3";
const GOLD   = "#C4922A";
const TEAL   = "#1F7A6D";
const PURPLE = "#7B3FA6";
const RED    = "#C0392B";
const FOG    = "#7B90A0";

// State configuration: what the orb looks like in each state
const ORB = {
  idle:      { ring1: "#1C3352", ring2: "#1C3352", glow: "transparent", spin: false, label: "Idle",       sub: "Start Athena to begin" },
  loading:   { ring1: GOLD,      ring2: "#2A4A6A",  glow: `${GOLD}22`,   spin: true,  label: "Loading",   sub: "Initialising models…" },
  listening: { ring1: OCEAN,     ring2: "#1C3352",  glow: `${OCEAN}33`,  spin: false, label: "Listening", sub: "Say 'Hi Athena' to activate" },
  awake:     { ring1: GOLD,      ring2: OCEAN,      glow: `${GOLD}44`,   spin: false, label: "Recording", sub: "Speak your query…" },
  thinking:  { ring1: PURPLE,    ring2: OCEAN,      glow: `${PURPLE}44`, spin: true,  label: "Thinking",  sub: "Athena is processing…" },
  speaking:  { ring1: TEAL,      ring2: OCEAN,      glow: `${TEAL}44`,   spin: false, label: "Speaking",  sub: "Athena is responding" },
  stopped:   { ring1: RED,       ring2: "#1C3352",  glow: `${RED}22`,    spin: false, label: "Stopped",   sub: "Voice assistant offline" },
};

const MAX_LOG = 40;

// ── Animated Orb ─────────────────────────────────────────────────────────────
function AthenaOrb({ state, level }) {
  const cfg = ORB[state] ?? ORB.idle;
  const isActive = !["idle", "stopped"].includes(state);

  return (
    <div style={{ position: "relative", width: 200, height: 200, margin: "0 auto" }}>

      {/* Outer slow-pulse ring */}
      <div style={{
        position: "absolute", inset: 0, borderRadius: "50%",
        border: `1px solid ${cfg.ring1}`,
        opacity: isActive ? 0.6 : 0.2,
        animation: isActive ? "orbBreath 3s ease-in-out infinite" : "none",
      }}/>

      {/* Scanning arc ring (rotates when thinking/loading) */}
      <div style={{
        position: "absolute", inset: 8, borderRadius: "50%",
        border: `2px solid transparent`,
        borderTopColor: cfg.ring1,
        borderRightColor: cfg.ring1,
        opacity: isActive ? 0.9 : 0.15,
        animation: cfg.spin ? "orbSpin 1.2s linear infinite" : "none",
        transition: "border-color 0.4s",
      }}/>

      {/* Middle ring — mic level driven */}
      <div style={{
        position: "absolute", inset: 20, borderRadius: "50%",
        border: `1px solid ${cfg.ring2}`,
        opacity: 0.4 + level * 0.5,
        transform: `scale(${1 + level * 0.08})`,
        transition: "transform 0.06s, opacity 0.06s",
      }}/>

      {/* Inner accent ring */}
      <div style={{
        position: "absolute", inset: 36, borderRadius: "50%",
        border: `2px solid ${cfg.ring1}`,
        opacity: isActive ? 0.7 : 0.1,
        boxShadow: `inset 0 0 20px ${cfg.glow}, 0 0 20px ${cfg.glow}`,
        transition: "border-color 0.4s, box-shadow 0.4s",
      }}/>

      {/* Center glow core */}
      <div style={{
        position: "absolute", inset: 52, borderRadius: "50%",
        background: `radial-gradient(circle, ${cfg.ring1}66 0%, ${NAVY} 70%)`,
        boxShadow: `0 0 24px ${cfg.glow}, 0 0 48px ${cfg.glow}`,
        transition: "background 0.4s, box-shadow 0.4s",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        {/* State icon */}
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: isActive ? cfg.ring1 : "#1C3352",
          boxShadow: isActive ? `0 0 12px ${cfg.ring1}` : "none",
          transition: "background 0.3s",
        }}/>
      </div>

      {/* Tick marks around the outer ring */}
      {[0,45,90,135,180,225,270,315].map(deg => (
        <div key={deg} style={{
          position: "absolute",
          width: 2, height: deg % 90 === 0 ? 6 : 3,
          background: cfg.ring1,
          opacity: isActive ? 0.5 : 0.1,
          left: "50%", top: 0,
          transformOrigin: "50% 100px",
          transform: `translateX(-50%) rotate(${deg}deg)`,
          transition: "opacity 0.4s",
        }}/>
      ))}

      {/* Inner only — no absolute overflow */}
    </div>
  );
}

// ── HUD data panel ────────────────────────────────────────────────────────────
function HUDPanel({ label, children, accent = OCEAN }) {
  return (
    <div style={{
      background: "rgba(10,37,64,0.6)",
      border: `1px solid ${accent}33`,
      borderLeft: `2px solid ${accent}`,
      borderRadius: "0 6px 6px 0",
      padding: "10px 14px",
      backdropFilter: "blur(4px)",
    }}>
      <div style={{
        fontFamily: "Inter, sans-serif", fontSize: 9, fontWeight: 700,
        letterSpacing: "0.14em", textTransform: "uppercase",
        color: accent, marginBottom: 6,
      }}>{label}</div>
      {children}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
function fmtElapsed(s) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}:${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;
  return `${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;
}

export default function VoiceView({ voice }) {
  const { running, state, level, query, lastYou, lastAthena, speakingLines,
          streamingText, typedYou,
          log, status, devices, selDev, setSelDev, elapsed,
          startVoice, stopVoice, triggerListen, pttRejected } = voice;
  const cfg = ORB[state] ?? ORB.idle;

  return (
    <div style={{
      background: `linear-gradient(160deg, ${NAVY} 0%, #061928 100%)`,
      borderRadius: 12,
      minHeight: "calc(100vh - 100px)",
      display: "flex", flexDirection: "column", alignItems: "center",
      padding: "40px 24px",
      position: "relative",
      overflow: "hidden",
    }}>

      {/* Grid overlay — subtle Jarvis HUD grid */}
      <div style={{
        position: "absolute", inset: 0, opacity: 0.03,
        backgroundImage: `
          linear-gradient(${OCEAN} 1px, transparent 1px),
          linear-gradient(90deg, ${OCEAN} 1px, transparent 1px)
        `,
        backgroundSize: "40px 40px",
        pointerEvents: "none",
      }}/>

      {/* Corner accent lines — Jarvis HUD frame */}
      {[["0 0","top left"],["0 auto 0 auto","top right"],
        ["auto 0 0","bottom left"],["auto auto 0 auto","bottom right"]].map(([margin, pos], i) => (
        <div key={i} style={{
          position: "absolute", width: 40, height: 40,
          [pos.includes("top") ? "top" : "bottom"]: 20,
          [pos.includes("left") ? "left" : "right"]: 20,
          borderTop:    pos.includes("top")    ? `1px solid ${OCEAN}66` : "none",
          borderBottom: pos.includes("bottom") ? `1px solid ${OCEAN}66` : "none",
          borderLeft:   pos.includes("left")   ? `1px solid ${OCEAN}66` : "none",
          borderRight:  pos.includes("right")  ? `1px solid ${OCEAN}66` : "none",
          pointerEvents: "none",
        }}/>
      ))}

      {/* Header */}
      <div style={{ width: "100%", maxWidth: 560, marginBottom: 32, display: "flex",
        justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: "Inter, sans-serif", fontSize: 10, fontWeight: 700,
            letterSpacing: "0.2em", color: `${OCEAN}99`, textTransform: "uppercase" }}>
            Latitude MedTech
          </div>
          <div style={{ fontFamily: "Inter, sans-serif", fontSize: 22, fontWeight: 300,
            color: "#fff", letterSpacing: "0.08em", marginTop: 2 }}>
            ATHENA
          </div>
        </div>
        {/* On/Off toggle — action labels, not status labels */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Status badge (actual current state) */}
          <div style={{
            display: "flex", alignItems: "center", gap: 5,
            padding: "3px 10px", borderRadius: 12,
            border: `1px solid ${running ? TEAL + "55" : RED + "44"}`,
            background: running ? TEAL + "11" : "transparent",
          }}>
            <div style={{
              width: 6, height: 6, borderRadius: "50%",
              background: running ? TEAL : RED,
              animation: running ? "statusPulse 2s ease-in-out infinite" : "none",
            }}/>
            <span style={{ fontFamily: "Inter, sans-serif", fontSize: 9, fontWeight: 700,
              letterSpacing: "0.1em", textTransform: "uppercase",
              color: running ? TEAL : RED }}>
              {running ? "Live" : "Offline"}
            </span>
          </div>
          {/* Session elapsed timer — only shown while running */}
          {running && elapsed > 0 && (
            <div style={{
              display: "flex", alignItems: "center", gap: 5,
              padding: "3px 10px", borderRadius: 12,
              border: `1px solid ${GOLD}44`,
              background: `${GOLD}0D`,
            }}>
              <span style={{ fontFamily: "Inter, sans-serif", fontSize: 9, fontWeight: 700,
                letterSpacing: "0.1em", textTransform: "uppercase", color: GOLD }}>
                {fmtElapsed(elapsed)}
              </span>
            </div>
          )}
          {/* Action button */}
          {!running ? (
            <button onClick={startVoice} style={orbBtn(OCEAN)}>Turn On</button>
          ) : (
            <button onClick={stopVoice} style={orbBtn(RED)}>Turn Off</button>
          )}
        </div>
      </div>

      {/* Central orb */}
      <div style={{ marginBottom: 20, position: "relative" }}>
        <AthenaOrb state={state} level={level} />
        {/* Waveform bars — inline, below orb, no overflow */}
        {(state === "speaking" || state === "awake") && (
          <div style={{ display:"flex", gap:3, alignItems:"flex-end",
            justifyContent:"center", height:24, marginTop:12 }}>
            {Array.from({length: 13}, (_, i) => (
              <div key={i} style={{
                width: 3, borderRadius: 2,
                background: state === "speaking" ? TEAL : GOLD,
                animation: `wave${(i % 4) + 1} ${0.4 + i * 0.06}s ease-in-out infinite alternate`,
                opacity: 0.85,
              }}/>
            ))}
          </div>
        )}
        {/* State label below orb */}
        <div style={{ textAlign: "center", marginTop: 12 }}>
          <div style={{ fontFamily: "Inter, sans-serif", fontWeight: 700, fontSize: 13,
            color: cfg.ring1, letterSpacing: "0.12em", textTransform: "uppercase",
            textShadow: `0 0 10px ${cfg.ring1}` }}>
            {cfg.label}
          </div>
          <div style={{ fontFamily: "Inter, sans-serif", fontSize: 11, color: FOG, marginTop: 4 }}>
            {query ? `"${query.slice(0, 50)}${query.length > 50 ? "…" : ""}"` : cfg.sub}
          </div>
        </div>
      </div>

      {/* Press to Listen — manual PTT trigger */}
      {running && state === "listening" && (
        <div style={{ marginBottom: 24 }}>
          <button
            onClick={triggerListen}
            style={{
              padding: "10px 28px",
              background: "transparent",
              border: `1px solid ${OCEAN}88`,
              borderRadius: 24,
              color: OCEAN,
              fontFamily: "Inter, sans-serif",
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              cursor: "pointer",
              boxShadow: `0 0 14px ${OCEAN}22`,
              transition: "border-color 0.2s, box-shadow 0.2s",
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = OCEAN;
              e.currentTarget.style.boxShadow = `0 0 20px ${OCEAN}44`;
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = `${OCEAN}88`;
              e.currentTarget.style.boxShadow = `0 0 14px ${OCEAN}22`;
            }}
          >
            Press to Listen
          </button>
          {pttRejected && (
            <div style={{
              marginTop: 8,
              fontFamily: "Inter, sans-serif", fontSize: 10, fontWeight: 600,
              letterSpacing: "0.08em", textTransform: "uppercase",
              color: `${RED}cc`,
              animation: "cursorBlink 0.6s ease-in-out 2",
            }}>
              Busy — try again
            </div>
          )}
        </div>
      )}

      {/* HUD panels — last exchange */}
      <div style={{ width: "100%", maxWidth: 560, display: "flex", flexDirection: "column", gap: 10 }}>

        {(lastYou || typedYou) && (
          <HUDPanel label="You said" accent={GOLD}>
            <div style={{ fontFamily: "Inter, sans-serif", fontSize: 13, color: "#fff",
              lineHeight: 1.6, fontWeight: 400 }}>
              {typedYou || lastYou}
              {typedYou && typedYou.length < (lastYou || "").length && (
                <span style={{
                  display: "inline-block", width: 2, height: "0.85em",
                  background: GOLD, marginLeft: 2, verticalAlign: "middle",
                  animation: "cursorBlink 0.9s step-end infinite",
                }}/>
              )}
            </div>
          </HUDPanel>
        )}

        {(streamingText || speakingLines.length > 0 || lastAthena) && (
          <HUDPanel label="Athena" accent={TEAL}>
            <div style={{ fontFamily: "Inter, sans-serif", fontSize: 13, color: "#e0eaf2",
              lineHeight: 1.8, fontWeight: 300 }}>
              {streamingText
                ? (
                  <>
                    {streamingText}
                    <span style={{
                      display: "inline-block", width: 2, height: "0.85em",
                      background: TEAL, marginLeft: 3, verticalAlign: "middle",
                      animation: "cursorBlink 0.9s step-end infinite",
                    }}/>
                  </>
                )
                : speakingLines.length > 0
                  ? speakingLines.map((line, i) => (
                      <span key={line.id} style={{
                        display: "inline",
                        animation: "lineIn 0.35s ease forwards",
                        opacity: 0,
                      }}>
                        {i > 0 ? " " : ""}{line.text}
                      </span>
                    ))
                  : lastAthena
              }
            </div>
          </HUDPanel>
        )}

        {!lastYou && !lastAthena && running && (
          <HUDPanel label="Status" accent={OCEAN}>
            <div style={{ fontFamily: "Inter, sans-serif", fontSize: 12, color: FOG }}>
              {status?.device ?? "Awaiting activation"} · {status?.tts_backend?.toUpperCase() ?? ""} TTS
            </div>
          </HUDPanel>
        )}
      </div>

      {/* Mic level — thin HUD bar */}
      {running && (
        <div style={{ width: "100%", maxWidth: 560, marginTop: 20 }}>
          <div style={{ display: "flex", gap: 2, height: 20, alignItems: "flex-end" }}>
            {Array.from({ length: 32 }, (_, i) => (
              <div key={i} style={{
                flex: 1, borderRadius: 1,
                background: level >= i / 32
                  ? (i < 20 ? TEAL : i < 28 ? GOLD : RED)
                  : "rgba(255,255,255,0.05)",
                height: `${40 + (i / 32) * 60}%`,
                transition: "background 0.04s",
              }}/>
            ))}
          </div>
        </div>
      )}

      {/* Device selector — minimal, only when stopped */}
      {!running && devices.length > 0 && (
        <div style={{ width: "100%", maxWidth: 560, marginTop: 20 }}>
          <select value={selDev} onChange={e => setSelDev(e.target.value)}
            style={{
              width: "100%", padding: "8px 12px", borderRadius: 6,
              background: "rgba(255,255,255,0.05)", border: `1px solid ${OCEAN}44`,
              color: FOG, fontSize: 11, fontFamily: "Inter, sans-serif", cursor: "pointer",
            }}>
            <option value="">Auto-select (follows VOICE_INPUT_DEVICE in .env)</option>
            {devices.map(d => {
              const isArray = d.name.toLowerCase().includes("array");
              const isLine  = d.name.toLowerCase().includes("line") && !d.name.toLowerCase().includes("microphone");
              const hint    = isArray ? " ✓ Best without earbuds" : isLine ? " (audio interface)" : "";
              return (
                <option key={d.index} value={d.index} style={{ background: NAVY }}>
                  [{d.index}] {d.name}{hint}
                </option>
              );
            })}
          </select>
        </div>
      )}

      {/* Collapsible log */}
      {log.length > 0 && (
        <div style={{ width: "100%", maxWidth: 560, marginTop: 20 }}>
          <details>
            <summary style={{ fontFamily: "Inter, sans-serif", fontSize: 9,
              letterSpacing: "0.14em", textTransform: "uppercase",
              color: `${OCEAN}77`, cursor: "pointer", userSelect: "none" }}>
              Activity log ({log.length})
            </summary>
            <div style={{
              marginTop: 8, maxHeight: 160, overflowY: "auto",
              background: "rgba(0,0,0,0.3)", borderRadius: 6,
              padding: "8px 12px", fontFamily: "monospace", fontSize: 10, lineHeight: 1.8,
            }}>
              {log.map(e => {
                const t = e.type?.replace("voice_", "") ?? "";
                const c = t === "transcript" ? "#fff" : t === "speaking" ? TEAL
                  : t === "thinking" ? PURPLE : t === "error" ? RED : FOG;
                const tx = t === "transcript" ? `▶ ${e.text}`
                  : t === "speaking" ? `◀ ${(e.response||"").slice(0,80)}`
                  : t === "thinking" ? `⟳ ${e.query||""}`
                  : e.message ?? t;
                return (
                  <div key={e.id} style={{ color: c, marginBottom: 1 }}>
                    <span style={{ color: "#2A4A6A", marginRight: 8 }}>
                      {e.ts ? new Date(e.ts).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit",second:"2-digit"}) : ""}
                    </span>
                    {tx}
                  </div>
                );
              })}
            </div>
          </details>
        </div>
      )}

      {/* CSS keyframes */}
      <style>{`
        @keyframes orbBreath {
          0%,100% { transform: scale(1);    opacity: 0.5; }
          50%      { transform: scale(1.04); opacity: 0.8; }
        }
        @keyframes orbSpin {
          to { transform: rotate(360deg); }
        }
        @keyframes wave1 { 0%{height:4px} 100%{height:20px} }
        @keyframes wave2 { 0%{height:6px} 100%{height:14px} }
        @keyframes wave3 { 0%{height:3px} 100%{height:18px} }
        @keyframes wave4 { 0%{height:8px} 100%{height:12px} }
        @keyframes statusPulse {
          0%,100% { opacity: 1; }
          50%      { opacity: 0.4; }
        }
        @keyframes cursorBlink {
          0%,100% { opacity: 1; }
          50%      { opacity: 0; }
        }
        @keyframes lineIn {
          from { opacity: 0; transform: translateY(5px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function orbBtn(color) {
  return {
    padding: "7px 18px",
    background: "transparent",
    border: `1px solid ${color}66`,
    borderRadius: 4,
    color: color,
    fontFamily: "Inter, sans-serif",
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    cursor: "pointer",
    transition: "border-color 0.2s, color 0.2s, box-shadow 0.2s",
    boxShadow: `0 0 8px ${color}22`,
  };
}
