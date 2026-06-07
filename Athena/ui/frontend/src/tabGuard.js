const CHANNEL_NAME = "athena-tab-singleton";
const LOCK_KEY = "athena_tab_lock";
const HEARTBEAT_MS = 1000;
const STALE_THRESHOLD_MS = 3000;

export function initTabGuard() {
  const myId = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const ch = new BroadcastChannel(CHANNEL_NAME);

  function getLock() {
    try { return JSON.parse(localStorage.getItem(LOCK_KEY)); } catch (_) { return null; }
  }
  function writeLock() {
    localStorage.setItem(LOCK_KEY, JSON.stringify({ id: myId, ts: Date.now() }));
  }
  function releaseLock() {
    const lock = getLock();
    if (lock && lock.id === myId) localStorage.removeItem(LOCK_KEY);
  }

  const existing = getLock();
  if (existing && (Date.now() - existing.ts) < STALE_THRESHOLD_MS) {
    ch.close();
    _showDuplicateOverlay();
    return false;
  }

  writeLock();

  const heartbeat = setInterval(() => {
    const lock = getLock();
    if (lock && lock.id !== myId && (Date.now() - lock.ts) < STALE_THRESHOLD_MS) {
      clearInterval(heartbeat);
      ch.close();
      _showDuplicateOverlay();
    } else {
      writeLock();
    }
  }, HEARTBEAT_MS);

  window.addEventListener("beforeunload", () => {
    clearInterval(heartbeat);
    releaseLock();
    ch.postMessage({ type: "release", from: myId });
    ch.close();
  });

  return true;
}

function _showDuplicateOverlay() {
  const overlay = document.createElement("div");
  overlay.style.cssText = [
    "position:fixed", "inset:0", "z-index:99999",
    "display:flex", "flex-direction:column", "align-items:center",
    "justify-content:center", "background:#0a0a0a", "color:#e0e0e0",
    "font-family:system-ui,sans-serif", "gap:12px", "text-align:center",
    "padding:24px",
  ].join(";");
  overlay.innerHTML = `
    <div style="font-size:2.5rem;line-height:1;">&#9888;</div>
    <div style="font-size:1.25rem;font-weight:600;">Athena is already open in another tab.</div>
    <div style="color:#888;font-size:0.875rem;">Close this tab and return to the existing session.</div>`;
  document.body.appendChild(overlay);
  const root = document.getElementById("root");
  if (root) root.style.display = "none";
}
