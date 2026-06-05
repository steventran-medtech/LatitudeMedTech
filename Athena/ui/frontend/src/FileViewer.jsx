/**
 * FileViewer — in-browser viewer for .docx, .pdf, and .md files.
 *
 * DOCX: converted to HTML via mammoth.js (runs entirely in the browser)
 * PDF:  served via /api/files/serve and rendered in an <iframe>
 * MD:   plain markdown render
 *
 * Usage:
 *   <FileViewer folder="documents" filename="2026-06-04_report.docx" />
 */

import { useEffect, useRef, useState } from "react";
import mammoth from "mammoth";

const API = "http://localhost:8000";

export default function FileViewer({ folder, filename, onClose }) {
  const [html,    setHtml]    = useState("");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");
  const iframeRef = useRef(null);

  const ext = filename?.split(".").pop().toLowerCase();

  useEffect(() => {
    if (!filename || !folder) return;
    setLoading(true); setHtml(""); setError("");

    if (ext === "docx") {
      fetch(`${API}/api/files/serve/${folder}/${encodeURIComponent(filename)}`)
        .then(r => r.arrayBuffer())
        .then(buf => mammoth.convertToHtml({ arrayBuffer: buf }))
        .then(result => { setHtml(result.value); setLoading(false); })
        .catch(e => { setError(`Could not render document: ${e.message}`); setLoading(false); });
    } else {
      // PDF and MD handled by the iframe/embed; just stop loading
      setLoading(false);
    }
  }, [folder, filename]);

  const serveUrl = `${API}/api/files/serve/${folder}/${encodeURIComponent(filename || "")}`;

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)",
      zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center",
    }}
      onClick={e => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <div style={{
        background: "#fff", borderRadius: 20, width: "90vw", height: "90vh",
        display: "flex", flexDirection: "column", overflow: "hidden",
        boxShadow: "0 8px 40px rgba(0,0,0,0.25)",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "12px 20px", borderBottom: "1px solid #E0DDD8", flexShrink: 0,
        }}>
          <div>
            <span style={{ fontFamily: "Helvetica,sans-serif", fontWeight: 700,
              fontSize: "0.9rem", color: "#1A1A1A" }}>{filename}</span>
            <span style={{ fontFamily: "Helvetica,sans-serif", fontSize: "0.75rem",
              color: "#8A8680", marginLeft: 10 }}>{ext?.toUpperCase()}</span>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <a href={serveUrl} download={filename}
              style={{ padding: "5px 12px", background: "#2C3E50", color: "#fff",
                borderRadius: 5, fontFamily: "Helvetica,sans-serif", fontSize: "0.78rem",
                fontWeight: 600, textDecoration: "none" }}>
              Download
            </a>
            <button onClick={onClose}
              style={{ padding: "5px 10px", background: "transparent", border: "1px solid #D8D4CE",
                borderRadius: 5, cursor: "pointer", fontSize: "1rem", lineHeight: 1, color: "#5A5650" }}>
              &#x2715;
            </button>
          </div>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: "auto", position: "relative" }}>
          {loading && (
            <div style={{ position: "absolute", inset: 0, display: "flex",
              alignItems: "center", justifyContent: "center",
              fontFamily: "Helvetica,sans-serif", fontSize: "0.85rem", color: "#8A8680" }}>
              Loading…
            </div>
          )}

          {error && (
            <div style={{ padding: 24, color: "#C0392B",
              fontFamily: "Helvetica,sans-serif", fontSize: "0.85rem" }}>
              {error}
            </div>
          )}

          {/* DOCX rendered as HTML */}
          {!loading && !error && ext === "docx" && (
            <div style={{ padding: "28px 40px", maxWidth: 860, margin: "0 auto" }}
              dangerouslySetInnerHTML={{ __html: html }} />
          )}

          {/* PDF in iframe */}
          {!loading && ext === "pdf" && (
            <iframe
              ref={iframeRef}
              src={serveUrl}
              style={{ width: "100%", height: "100%", border: "none" }}
              title={filename}
            />
          )}

          {/* MD as preformatted text (simple, readable) */}
          {!loading && ext === "md" && !html && (
            <iframe
              src={serveUrl}
              style={{ width: "100%", height: "100%", border: "none",
                fontFamily: "Georgia,serif", background: "#FAFAF7" }}
              title={filename}
            />
          )}
        </div>
      </div>
    </div>
  );
}
