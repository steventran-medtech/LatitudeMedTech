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
  const [streamingText, setStreamingText] = useState("");  // live word-by-word accumulator
  const [typedYou,      setTypedYou]      = useState("");  // character-by-character transcript
  const [log,        setLog]        = useState([]);
  const [status,     setStatus]     = useState(null);
  const [devices,    setDevices]    = useState([]);
  const [selDev,     setSelDev]     = useState("");
  const [elapsed,    setElapsed]    = useState(0);

  const typedYouRef    = useRef("");
  const animCancelRef  = useRef(0);   // increment to cancel in-flight transcript animation

  const wsRef          = useRef(null);
  const peakRef        = useRef(0);
  const sessionStart   = useRef(null);
  const queryCount     = useRef(0);
  const sessionIdRef   = useRef(null);   // UUID for the current voice session
  const sessionIsNew   = useRef(true);   // false if reconnected to an already-running session

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

    // Poll until models_ready before greeting or starting voice — guarantees
    // Athena never opens in a loading state regardless of startup script timing.
    const pollReady = (attempt) => {
      fetch(`${API}/api/voice/status`).then(r => r.json())
        .then(d => {
          if (d.active) {
            // Voice already running — resume existing session or create new tracking ID
            const existing = sessionStorage.getItem("athena_session_id");
            const sid = existing ?? crypto.randomUUID();
            const isNew = !existing;
            sessionIdRef.current = sid;
            sessionIsNew.current = isNew;
            sessionStorage.setItem("athena_session_id", sid);
            setRunning(true); setState(d.state ?? "idle"); setStatus(d);
            sessionStart.current = Date.now(); queryCount.current = 0;
            fetch(`${API}/api/sessions/start`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                session_id: sid,
                started_at: new Date().toISOString(),
                is_new: isNew,
                device: d.device ?? "",
              }),
            }).catch(() => {});
            return;
          }
          if (!d.models_ready) {
            // Models still loading — retry every 800 ms, up to ~3 minutes
            if (attempt < 225) setTimeout(() => pollReady(attempt + 1), 800);
            return;
          }
          // All models ready — greet then start
          fetch(`${API}/api/voice/greet`, { method: "POST" })
            .catch(() => {})
            .finally(() => {
              fetch(`${API}/api/voice/start`, { method: "POST" })
                .then(r => r.json()).then(s => {
                  if (s.status === "started" || s.status === "already_running") {
                    const now = Date.now();
                    const sid = crypto.randomUUID();
                    sessionIdRef.current = sid;
                    sessionIsNew.current = true;
                    sessionStorage.setItem("athena_session_id", sid);
                    setRunning(true); setState("loading"); setStatus(s);
                    sessionStart.current = now; queryCount.current = 0;
                    fetch(`${API}/api/sessions/start`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        session_id: sid,
                        started_at: new Date(now).toISOString(),
                        is_new: true,
                        device: s.device ?? "",
                      }),
                    }).catch(() => {});
                  }
                }).catch(() => {});
            });
        }).catch(() => {
          if (attempt < 225) setTimeout(() => pollReady(attempt + 1), 800);
        });
    };
    pollReady(0);
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
      if (type === "thinking")  { setQuery(msg.query ?? ""); setSpeakingLines([]); setStreamingText(""); setLastAthena(""); }
      if (type === "transcript") {
        // Animate transcript character-by-character
        const full = msg.text ?? "";
        setLastYou(full);
        setLastAthena("");
        setQuery("");
        setSpeakingLines([]);
        queryCount.current += 1;
        // Reveal characters one at a time. Cancel any prior animation via generation counter.
        const gen = ++animCancelRef.current;
        typedYouRef.current = "";
        setTypedYou("");
        let i = 0;
        const step = () => {
          if (animCancelRef.current !== gen) return;   // superseded by newer transcript
          if (i < full.length) {
            typedYouRef.current = full.slice(0, i + 1);
            setTypedYou(typedYouRef.current);
            i++;
            setTimeout(step, 18);
          }
        };
        step();
      }
      if (type === "speaking_word") setStreamingText(prev => prev + (msg.word ?? ""));
      if (type === "speaking" && msg.response === "…") { setSpeakingLines([]); setStreamingText(""); }
      if (type === "speaking_partial") setSpeakingLines(prev => [...prev, { id: Date.now() + Math.random(), text: msg.sentence ?? "" }]);
      if (type === "speaking" && msg.response && msg.response !== "…") { setLastAthena(msg.response ?? ""); setSpeakingLines([]); setStreamingText(""); }
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
          const now = Date.now();
          const sid = crypto.randomUUID();
          sessionIdRef.current = sid;
          sessionIsNew.current = true;
          sessionStorage.setItem("athena_session_id", sid);
          setRunning(true); setState("loading"); setStatus(d);
          sessionStart.current = now; queryCount.current = 0; setElapsed(0);
          fetch(`${API}/api/sessions/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              session_id: sid,
              started_at: new Date(now).toISOString(),
              is_new: true,
              device: d.device ?? "",
            }),
          }).catch(() => {});
        }
      }).catch(() => {});
  };

  const stopVoice = () => {
    const start = sessionStart.current;
    const sid   = sessionIdRef.current;
    const isNew = sessionIsNew.current;
    fetch(`${API}/api/voice/stop`, { method: "POST" })
      .then(() => {
        setRunning(false); setState("stopped"); setLevel(0);
        const ended = new Date().toISOString();
        const dur   = start ? Math.floor((Date.now() - start) / 1000) : 0;
        fetch(`${API}/api/sessions/log`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id:    sid ?? crypto.randomUUID(),
            started_at:    start ? new Date(start).toISOString() : ended,
            ended_at:      ended,
            duration_secs: dur,
            queries:       queryCount.current,
            device:        status?.device ?? "",
            is_new:        isNew,
          }),
        }).catch(() => {});
        sessionIdRef.current = null;
        sessionIsNew.current = true;
        sessionStorage.removeItem("athena_session_id");
        sessionStart.current = null; queryCount.current = 0; setElapsed(0);
      }).catch(() => {});
  };

  return {
    running, state, level, query, lastYou, lastAthena, speakingLines,
    streamingText, typedYou,
    log, status, devices, selDev, setSelDev, elapsed, peakRef,
    startVoice, stopVoice,
  };
}
