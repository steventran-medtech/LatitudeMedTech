import { useEffect, useRef, useState } from "react";

const API     = "http://localhost:8000";
const MAX_LOG = 40;

export function useVoiceSession() {
  const [running,    setRunning]    = useState(false);
  const [state,      setState]      = useState("idle");
  const [level,      setLevel]      = useState(0);
  const [query,      setQuery]      = useState("");
  const [lastYou,      setLastYou]      = useState("");
  const [lastAthena,   setLastAthena]   = useState("");
  const [speakingLines, setSpeakingLines] = useState([]);
  const [log,        setLog]        = useState([]);
  const [status,     setStatus]     = useState(null);
  const [devices,    setDevices]    = useState([]);
  const [selDev,     setSelDev]     = useState("");
  const [elapsed,    setElapsed]    = useState(0);

  const wsRef        = useRef(null);
  const peakRef      = useRef(0);
  const sessionStart = useRef(null);
  const queryCount   = useRef(0);

  // Session elapsed timer
  useEffect(() => {
    if (!running) return;
    if (!sessionStart.current) sessionStart.current = Date.now();
    const t = setInterval(() => {
      setElapsed(Math.floor((Date.now() - sessionStart.current) / 1000));
    }, 1000);
    return () => clearInterval(t);
  }, [running]);

  // Initial load: fetch devices + auto-start voice
  useEffect(() => {
    fetch(`${API}/api/voice/devices`).then(r => r.json())
      .then(d => setDevices(d.devices ?? [])).catch(() => {});

    fetch(`${API}/api/voice/status`).then(r => r.json())
      .then(d => {
        if (d.active) {
          setRunning(true); setState(d.state ?? "idle"); setStatus(d);
          sessionStart.current = Date.now(); queryCount.current = 0;
        } else {
          // Play greeting first (blocks until TTS finishes + 1s drain),
          // then open the mic — prevents Athena from recording her own voice.
          fetch(`${API}/api/voice/greet`, { method: "POST" })
            .catch(() => {})
            .finally(() => {
              fetch(`${API}/api/voice/start`, { method: "POST" })
                .then(r => r.json()).then(s => {
                  if (s.status === "started" || s.status === "already_running") {
                    setRunning(true); setState("loading"); setStatus(s);
                    sessionStart.current = Date.now(); queryCount.current = 0;
                  }
                }).catch(() => {});
            });
        }
      }).catch(() => {});
  }, []);

  // WebSocket to voice event stream — lives for app lifetime, not just Voice tab
  useEffect(() => {
    if (!running) { wsRef.current?.close(); return; }
    const ws = new WebSocket("ws://localhost:8000/ws/voice");
    wsRef.current = ws;
    ws.onmessage = (e) => {
      const msg  = JSON.parse(e.data);
      const type = msg.type?.replace("voice_", "") ?? "";
      if (type === "level") {
        const v = msg.level ?? 0;
        setLevel(v);
        if (v > peakRef.current) peakRef.current = v;
        return;
      }
      if (type === "thinking")  { setQuery(msg.query ?? ""); setSpeakingLines([]); }
      if (type === "transcript") { setLastYou(msg.text ?? ""); setQuery(""); setSpeakingLines([]); queryCount.current += 1; }
      if (type === "speaking" && msg.response === "…") setSpeakingLines([]);
      if (type === "speaking_partial") setSpeakingLines(prev => [...prev, { id: Date.now() + Math.random(), text: msg.sentence ?? "" }]);
      if (type === "speaking" && msg.response && msg.response !== "…") { setLastAthena(msg.response ?? ""); setSpeakingLines([]); }
      if (type === "loading")   setState("loading");
      if (type === "listening") setState("listening");
      if (type === "awake")     setState("awake");
      if (type === "thinking")  setState("thinking");
      if (type === "speaking")  setState("speaking");
      if (type === "stopped")   { setState("stopped"); setRunning(false); setLevel(0); setSpeakingLines([]); }
      setLog(prev => [...prev.slice(-(MAX_LOG - 1)), { ...msg, id: Date.now() + Math.random() }]);
    };
    return () => ws.close();
  }, [running]);

  const startVoice = () => {
    const params = selDev !== "" ? `?device=${selDev}` : "";
    fetch(`${API}/api/voice/start${params}`, { method: "POST" })
      .then(r => r.json()).then(d => {
        if (d.status === "started" || d.status === "already_running") {
          setRunning(true); setState("loading"); setStatus(d);
          sessionStart.current = Date.now(); queryCount.current = 0; setElapsed(0);
        }
      }).catch(() => {});
  };

  const stopVoice = () => {
    const start = sessionStart.current;
    fetch(`${API}/api/voice/stop`, { method: "POST" })
      .then(() => {
        setRunning(false); setState("stopped"); setLevel(0);
        const ended = new Date().toISOString();
        const dur   = start ? Math.floor((Date.now() - start) / 1000) : 0;
        fetch(`${API}/api/sessions/log`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            started_at:    start ? new Date(start).toISOString() : ended,
            ended_at:      ended,
            duration_secs: dur,
            queries:       queryCount.current,
            device:        status?.device ?? "",
          }),
        }).catch(() => {});
        sessionStart.current = null; queryCount.current = 0; setElapsed(0);
      }).catch(() => {});
  };

  return {
    running, state, level, query, lastYou, lastAthena, speakingLines, log,
    status, devices, selDev, setSelDev, elapsed, peakRef,
    startVoice, stopVoice,
  };
}
