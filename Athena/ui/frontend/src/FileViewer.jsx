/**
 * FileViewer — opens DOCX / PPTX / PDF via Google Drive.
 *
 * On first open the backend uploads the file to the user's Google Drive and
 * returns an embed URL (Google Docs / Slides / Drive viewer).  Subsequent
 * opens for the same unchanged file are served from cache — zero re-upload.
 *
 * One-time setup: click "Connect Google Drive" → browser OAuth consent →
 * drive_token.json saved locally.  No service account needed.
 */

import { useEffect, useState } from "react";
import { authHdr } from "./api.js";

const API = "http://localhost:8000";
const F   = { sans: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" };

// App-colour header — matches real app brand colours
const TYPE_META = {
  docx: { label: "Word Document",  bg: "#2B579A", icon: "W" },
  pdf:  { label: "PDF Document",   bg: "#B30000", icon: "P" },
  pptx: { label: "Presentation",   bg: "#C43E1C", icon: "P" },
};
const DEFAULT_META = { label: "Document", bg: "#0A2540", icon: "F" };

export default function FileViewer({ folder, filename, onClose }) {
  const [embedUrl,    setEmbedUrl]    = useState("");
  const [status,      setStatus]      = useState("loading"); // loading | ready | error | unconfigured
  const [errorMsg,    setErrorMsg]    = useState("");
  const [needsAuth,   setNeedsAuth]   = useState(false);
  const [connecting,  setConnecting]  = useState(false);

  const ext      = filename?.split(".").pop().toLowerCase();
  const meta     = TYPE_META[ext] || DEFAULT_META;
  const serveUrl = `${API}/api/files/serve/${folder}/${encodeURIComponent(filename || "")}`;

  const loadView = () => {
    if (!filename || !folder) return;
    setStatus("loading"); setEmbedUrl(""); setErrorMsg(""); setNeedsAuth(false);

    fetch(`${API}/api/files/google-view/${folder}/${encodeURIComponent(filename)}`, { headers: authHdr() })
      .then(r => r.json())
      .then(data => {
        if (data.error === "not_configured") {
          setStatus("unconfigured");
          setErrorMsg(data.message);
          setNeedsAuth(!!data.needs_auth);
        } else if (data.url) {
          setEmbedUrl(data.url); setStatus("ready");
        } else {
          setStatus("error"); setErrorMsg("Unexpected response from server.");
        }
      })
      .catch(e => { setStatus("error"); setErrorMsg(e.message); });
  };

  const connectDrive = async () => {
    setConnecting(true);
    try {
      const res = await fetch(`${API}/api/google/auth`, { method: "POST", headers: authHdr() });
      const data = await res.json();
      if (data.ok) {
        // Re-attempt the view now that we have a token
        loadView();
      } else {
        setErrorMsg(data.detail || "Authorization failed.");
      }
    } catch (e) {
      setErrorMsg(e.message);
    } finally {
      setConnecting(false);
    }
  };

  useEffect(() => { loadView(); }, [folder, filename]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 1000,
        background: "rgba(0,0,0,0.60)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <div style={{
        width: "92vw", height: "90vh",
        display: "flex", flexDirection: "column",
        borderRadius: 8, overflow: "hidden",
        boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
      }}>

        {/* ── App-style title bar ───────────────────────────────────────── */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "9px 14px", flexShrink: 0,
          background: meta.bg,
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: 4,
            background: "rgba(255,255,255,0.18)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "'Georgia', serif", fontSize: 14, fontWeight: 800,
            color: "#fff", flexShrink: 0,
          }}>
            {meta.icon}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontFamily: F.sans, fontSize: 13, fontWeight: 600, color: "#fff",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              lineHeight: 1.2,
            }}>
              {filename}
            </div>
            <div style={{
              fontFamily: F.sans, fontSize: 9, color: "rgba(255,255,255,0.65)",
              letterSpacing: "0.07em", textTransform: "uppercase", marginTop: 1,
            }}>
              {meta.label}
            </div>
          </div>

          <a href={serveUrl} download={filename} style={{
            padding: "5px 12px", borderRadius: 4,
            background: "rgba(255,255,255,0.16)",
            border: "1px solid rgba(255,255,255,0.22)",
            color: "#fff", fontFamily: F.sans, fontSize: 11,
            fontWeight: 600, textDecoration: "none", flexShrink: 0,
          }}>
            ↓ Download
          </a>

          <button onClick={onClose} style={{
            width: 28, height: 28, flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            background: "rgba(255,255,255,0.12)",
            border: "1px solid rgba(255,255,255,0.20)",
            borderRadius: 4, cursor: "pointer",
            color: "#fff", fontSize: 13, lineHeight: 1, padding: 0,
          }}>✕</button>
        </div>

        {/* ── Body ─────────────────────────────────────────────────────── */}
        <div style={{ flex: 1, background: "#fff", display: "flex",
          alignItems: "center", justifyContent: "center", overflow: "hidden" }}>

          {/* Loading */}
          {status === "loading" && (
            <div style={{ fontFamily: F.sans, fontSize: 13, color: "#888" }}>
              Uploading to Google Drive…
            </div>
          )}

          {/* Ready — Google viewer iframe */}
          {status === "ready" && (
            <iframe
              src={embedUrl}
              style={{ width: "100%", height: "100%", border: "none" }}
              title={filename}
              allow="autoplay"
            />
          )}

          {/* Not configured */}
          {status === "unconfigured" && (
            <div style={{
              maxWidth: 480, padding: "32px 40px", textAlign: "center",
              fontFamily: F.sans,
            }}>
              <div style={{ fontSize: 32, marginBottom: 16 }}>☁️</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#0A2540",
                marginBottom: 10 }}>
                {needsAuth ? "Connect Google Drive" : "Google Drive not configured"}
              </div>
              <div style={{ fontSize: 12, color: "#7B90A0", lineHeight: 1.7,
                marginBottom: 20 }}>
                {errorMsg}
              </div>

              {needsAuth ? (
                <button
                  onClick={connectDrive}
                  disabled={connecting}
                  style={{
                    padding: "10px 24px", borderRadius: 6, cursor: connecting ? "default" : "pointer",
                    background: connecting ? "#ccc" : "#4285F4",
                    border: "none", color: "#fff",
                    fontFamily: F.sans, fontSize: 13, fontWeight: 600,
                    marginBottom: 16,
                  }}
                >
                  {connecting ? "Opening browser…" : "Connect Google Drive"}
                </button>
              ) : (
                <div style={{ fontSize: 11, color: "#aaa", lineHeight: 1.8,
                  background: "#F8FAFC", borderRadius: 6, padding: "12px 16px",
                  textAlign: "left" }}>
                  <strong>Setup:</strong><br />
                  1. Save <code>client_secrets.json</code> to the Athena root folder<br />
                  2. Restart the backend, then click 'Connect Google Drive'
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {status === "error" && (
            <div style={{ fontFamily: F.sans, fontSize: 13, color: "#C0392B",
              maxWidth: 420, textAlign: "center", padding: 32 }}>
              <div style={{ fontSize: 24, marginBottom: 12 }}>⚠️</div>
              {errorMsg || "Could not open file in Google Drive."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
