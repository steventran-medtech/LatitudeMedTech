/**
 * FileViewer — in-browser viewers for .docx, .pdf, .pptx, and .md files.
 *
 * DOCX: mammoth.js → HTML, rendered in a Word-style A4 page layout
 * PDF:  browser native viewer via <iframe>
 * PPTX: slide-deck viewer using /api/files/slides/{folder}/{filename}
 * MD:   plain text in iframe
 */

import { useEffect, useRef, useState } from "react";
import mammoth from "mammoth";

const API = "http://localhost:8000";

const F = { sans: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" };
const C = {
  navy:  "#0A2540",
  ocean: "#1A6FA3",
  gold:  "#C4922A",
  teal:  "#1F7A6D",
  fog:   "#7B90A0",
  mist:  "#DDE4EB",
  slate: "#3C5470",
  ink:   "#0A2540",
};

// ── PPTX slide viewer ──────────────────────────────────────────────────────────
function PptxViewer({ folder, filename }) {
  const [slides,  setSlides]  = useState(null);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");
  const stripRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/api/files/slides/${folder}/${encodeURIComponent(filename)}`)
      .then(r => r.json())
      .then(d => {
        if (d.slides) setSlides(d.slides);
        else setError("No slides found.");
        setLoading(false);
      })
      .catch(e => { setError(`Could not load slides: ${e.message}`); setLoading(false); });
  }, [folder, filename]);

  useEffect(() => {
    const handler = (e) => {
      if (!slides) return;
      if (e.key === "ArrowRight") setCurrent(c => Math.min(c + 1, slides.length - 1));
      if (e.key === "ArrowLeft")  setCurrent(c => Math.max(c - 1, 0));
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [slides]);

  // Scroll active thumbnail into view
  useEffect(() => {
    if (!stripRef.current) return;
    const btn = stripRef.current.querySelector(`[data-idx="${current}"]`);
    if (btn) btn.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
  }, [current]);

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center",
      flex: 1, color: "#aaa", fontFamily: F.sans, fontSize: 13, background: "#16213E" }}>
      Loading slides…
    </div>
  );

  if (error) return (
    <div style={{ padding: 24, color: "#E74C3C", fontFamily: F.sans, fontSize: 13,
      background: "#16213E", flex: 1 }}>
      {error}
    </div>
  );

  const slide   = slides?.[current];
  const isFirst = current === 0;
  const isDark  = isFirst || (slide?.title && /^(section|appendix)/i.test(slide.title.trim()));

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, background: "#16213E", overflow: "hidden" }}>

      {/* Slide canvas */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "24px 32px", overflow: "hidden" }}>
        <div style={{ width: "100%", maxWidth: 820, position: "relative" }}>
          {/* 16:9 aspect ratio wrapper */}
          <div style={{ paddingBottom: "56.25%", position: "relative" }}>
            <div style={{
              position: "absolute", inset: 0,
              background: isDark ? "#0A2540" : "#FFFFFF",
              borderRadius: 6,
              boxShadow: "0 12px 48px rgba(0,0,0,0.6)",
              padding: "40px 52px",
              display: "flex", flexDirection: "column",
              overflow: "hidden",
            }}>
              {/* Top accent bar */}
              <div style={{
                position: "absolute", top: 0, left: 0, right: 0, height: 5,
                background: `linear-gradient(90deg, ${C.ocean} 0%, ${C.teal} 100%)`,
                borderRadius: "6px 6px 0 0",
              }} />

              {/* Slide counter */}
              <div style={{
                position: "absolute", top: 12, right: 16,
                fontSize: 9, fontFamily: F.sans, fontWeight: 600, letterSpacing: "0.06em",
                color: isDark ? "rgba(168,196,216,0.5)" : C.fog,
              }}>
                {current + 1} / {slides.length}
              </div>

              {/* Title */}
              {slide?.title && (
                <div style={{
                  fontSize: isFirst ? 26 : 18,
                  fontWeight: 700,
                  fontFamily: F.sans,
                  color: isDark ? "#FFFFFF" : C.navy,
                  lineHeight: 1.25,
                  marginBottom: isFirst ? 10 : 14,
                  marginTop: 8,
                  letterSpacing: "-0.01em",
                  maxWidth: "90%",
                }}>
                  {slide.title}
                </div>
              )}

              {/* Gold rule under non-cover titles */}
              {!isFirst && slide?.title && (
                <div style={{ width: 36, height: 2, background: C.gold, borderRadius: 1, marginBottom: 16 }} />
              )}

              {/* Body bullets */}
              <div style={{ flex: 1, overflow: "hidden" }}>
                {slide?.texts?.map((t, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 9 }}>
                    <span style={{
                      flexShrink: 0, width: 5, height: 5, borderRadius: "50%",
                      background: isDark ? C.ocean : C.gold,
                      marginTop: 7,
                    }} />
                    <div style={{
                      fontSize: 12.5, lineHeight: 1.55, fontFamily: F.sans,
                      color: isDark ? "#BDD0E0" : C.slate,
                    }}>
                      {t}
                    </div>
                  </div>
                ))}
              </div>

              {/* Brand watermark on cover */}
              {isFirst && (
                <div style={{
                  position: "absolute", bottom: 14, right: 18,
                  fontSize: 8, fontFamily: F.sans, letterSpacing: "0.14em",
                  textTransform: "uppercase",
                  color: isDark ? "rgba(168,196,216,0.35)" : C.fog,
                }}>
                  Latitude MedTech
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation bar */}
      <div style={{
        background: "#0D1528",
        borderTop: "1px solid rgba(255,255,255,0.07)",
        padding: "10px 20px",
        display: "flex", alignItems: "center", gap: 14, flexShrink: 0,
      }}>
        <button
          disabled={current === 0}
          onClick={() => setCurrent(c => c - 1)}
          style={{
            padding: "6px 14px", borderRadius: 5,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "transparent",
            color: current === 0 ? "rgba(255,255,255,0.2)" : "#fff",
            fontFamily: F.sans, fontSize: 11, fontWeight: 600,
            cursor: current === 0 ? "default" : "pointer",
            flexShrink: 0,
          }}
        >← Prev</button>

        {/* Thumbnail strip */}
        <div ref={stripRef} style={{
          flex: 1, display: "flex", gap: 4, overflowX: "auto",
          scrollbarWidth: "none", msOverflowStyle: "none",
        }}>
          {slides.map((_, i) => (
            <button
              key={i}
              data-idx={i}
              onClick={() => setCurrent(i)}
              style={{
                flexShrink: 0, width: 34, height: 22, borderRadius: 3, cursor: "pointer",
                border: `2px solid ${i === current ? C.ocean : "rgba(255,255,255,0.12)"}`,
                background: i === current ? C.ocean : "rgba(255,255,255,0.05)",
                fontSize: 8, fontFamily: F.sans,
                color: i === current ? "#fff" : "rgba(255,255,255,0.35)",
                transition: "border-color 0.12s, background 0.12s",
              }}
            >
              {i + 1}
            </button>
          ))}
        </div>

        <button
          disabled={!slides || current === slides.length - 1}
          onClick={() => setCurrent(c => c + 1)}
          style={{
            padding: "6px 14px", borderRadius: 5, border: "none",
            background: !slides || current === slides.length - 1
              ? "rgba(255,255,255,0.07)"
              : C.ocean,
            color: !slides || current === slides.length - 1
              ? "rgba(255,255,255,0.25)"
              : "#fff",
            fontFamily: F.sans, fontSize: 11, fontWeight: 700,
            cursor: !slides || current === slides.length - 1 ? "default" : "pointer",
            flexShrink: 0,
          }}
        >Next →</button>
      </div>
    </div>
  );
}

// ── Main FileViewer ────────────────────────────────────────────────────────────
export default function FileViewer({ folder, filename, onClose }) {
  const [html,    setHtml]    = useState("");
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState("");

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
      setLoading(false);
    }
  }, [folder, filename]);

  const serveUrl = `${API}/api/files/serve/${folder}/${encodeURIComponent(filename || "")}`;

  // Per-type header styling (mimics app title bars)
  const TYPE_META = {
    docx: { label: "Word Document",  headerBg: "#2B579A", icon: "W" },
    pdf:  { label: "PDF Document",   headerBg: "#B30000", icon: "P" },
    pptx: { label: "Presentation",   headerBg: "#C43E1C", icon: "P" },
    md:   { label: "Markdown",       headerBg: C.teal,    icon: "M" },
  };
  const meta = TYPE_META[ext] || { label: (ext?.toUpperCase() ?? "File"), headerBg: C.navy, icon: "F" };

  return (
    <div
      style={{
        position: "fixed", inset: 0,
        background: "rgba(0,0,0,0.60)",
        zIndex: 1000,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <div style={{
        width: "92vw", height: "90vh",
        display: "flex", flexDirection: "column",
        overflow: "hidden",
        borderRadius: 8,
        boxShadow: "0 24px 80px rgba(0,0,0,0.5)",
      }}>
        {/* ── App-style header bar ─────────────────────────────────────────── */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "9px 14px", flexShrink: 0,
          background: meta.headerBg,
        }}>
          {/* App icon */}
          <div style={{
            width: 28, height: 28, borderRadius: 4,
            background: "rgba(255,255,255,0.18)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "'Georgia', serif", fontSize: 14, fontWeight: 800,
            color: "#fff", flexShrink: 0,
          }}>
            {meta.icon}
          </div>

          {/* Filename + type */}
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

          {/* Download */}
          <a href={serveUrl} download={filename} style={{
            padding: "5px 12px", borderRadius: 4,
            background: "rgba(255,255,255,0.16)",
            border: "1px solid rgba(255,255,255,0.22)",
            color: "#fff", fontFamily: F.sans, fontSize: 11, fontWeight: 600,
            textDecoration: "none", flexShrink: 0,
          }}>
            ↓ Download
          </a>

          {/* Close */}
          <button onClick={onClose} style={{
            width: 28, height: 28, flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            background: "rgba(255,255,255,0.12)",
            border: "1px solid rgba(255,255,255,0.20)",
            borderRadius: 4, cursor: "pointer",
            color: "#fff", fontSize: 13, lineHeight: 1, padding: 0,
          }}>✕</button>
        </div>

        {/* ── Body ─────────────────────────────────────────────────────────── */}
        <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column",
          position: "relative", background: "#fff" }}>

          {/* Loading overlay */}
          {loading && (
            <div style={{
              position: "absolute", inset: 0, display: "flex",
              alignItems: "center", justifyContent: "center",
              background: "#fff", zIndex: 2,
              fontFamily: F.sans, fontSize: 13, color: C.fog,
            }}>
              Loading…
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div style={{ padding: 24, color: "#C0392B", fontFamily: F.sans, fontSize: 13 }}>
              {error}
            </div>
          )}

          {/* ── DOCX — Word-like page ──────────────────────────────────────── */}
          {!loading && !error && ext === "docx" && (
            <div style={{ flex: 1, overflow: "auto", background: "#E8E8E8", display: "flex",
              flexDirection: "column" }}>
              {/* Ribbon-style toolbar (visual only) */}
              <div style={{
                background: "#F3F3F3",
                borderBottom: "1px solid #D0D0D0",
                padding: "4px 14px",
                display: "flex", alignItems: "center", gap: 4,
                flexShrink: 0, position: "sticky", top: 0, zIndex: 2,
              }}>
                {[
                  { ch: "B", bold: true,  italic: false, under: false },
                  { ch: "I", bold: false, italic: true,  under: false },
                  { ch: "U", bold: false, italic: false, under: true  },
                ].map(({ ch, bold, italic, under }) => (
                  <button key={ch} style={{
                    width: 24, height: 22, border: "1px solid transparent",
                    borderRadius: 3, background: "transparent",
                    fontFamily: F.sans, fontSize: 12,
                    fontWeight: bold ? 700 : 400,
                    fontStyle: italic ? "italic" : "normal",
                    textDecoration: under ? "underline" : "none",
                    cursor: "default", color: "#444",
                  }}>{ch}</button>
                ))}
                <div style={{ width: 1, height: 14, background: "#C8C8C8", margin: "0 4px" }} />
                {["≡", "≣", "⊟"].map((ch, i) => (
                  <button key={i} style={{
                    width: 24, height: 22, border: "1px solid transparent",
                    borderRadius: 3, background: "transparent",
                    fontSize: 14, cursor: "default", color: "#555",
                  }}>{ch}</button>
                ))}
                <div style={{ flex: 1 }} />
                <span style={{ fontFamily: F.sans, fontSize: 10, color: "#999",
                  letterSpacing: "0.03em" }}>
                  Read-only preview
                </span>
              </div>

              {/* A4 / Letter page */}
              <div style={{ padding: "24px 24px 48px" }}>
                <div style={{
                  background: "#fff",
                  maxWidth: 816,
                  margin: "0 auto",
                  padding: "96px 96px",
                  boxShadow: "0 2px 12px rgba(0,0,0,0.15), 0 0 0 1px rgba(0,0,0,0.05)",
                  minHeight: 1056,
                }}>
                  <style>{`
                    .aw-doc { font-family: Calibri, 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #1A1A1A; line-height: 1.65; }
                    .aw-doc h1 { font-size: 22px; font-weight: 700; color: #1A1A1A; margin: 0 0 16px; line-height: 1.2; }
                    .aw-doc h2 { font-size: 16px; font-weight: 700; color: #1F497D; margin: 26px 0 10px; padding-bottom: 5px; border-bottom: 1px solid #D8D8D8; }
                    .aw-doc h3 { font-size: 13px; font-weight: 700; color: #2B579A; margin: 18px 0 6px; }
                    .aw-doc h4 { font-size: 11px; font-weight: 700; color: #444; margin: 12px 0 4px; text-transform: uppercase; letter-spacing: 0.04em; }
                    .aw-doc p  { margin: 0 0 10px; }
                    .aw-doc ul, .aw-doc ol { margin: 6px 0 12px; padding-left: 26px; }
                    .aw-doc li { margin-bottom: 4px; }
                    .aw-doc table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 10pt; }
                    .aw-doc td, .aw-doc th { border: 1px solid #BFBFBF; padding: 5px 9px; vertical-align: top; }
                    .aw-doc th { background: #2B579A; color: #fff; font-weight: 700; }
                    .aw-doc tr:nth-child(even) td { background: #F2F6FC; }
                    .aw-doc a  { color: #2B579A; }
                  `}</style>
                  <div className="aw-doc" dangerouslySetInnerHTML={{ __html: html }} />
                </div>
              </div>
            </div>
          )}

          {/* ── PDF — browser native viewer ────────────────────────────────── */}
          {!loading && ext === "pdf" && (
            <iframe
              src={serveUrl}
              style={{ flex: 1, border: "none", width: "100%", height: "100%" }}
              title={filename}
            />
          )}

          {/* ── PPTX — slide deck viewer ───────────────────────────────────── */}
          {!loading && !error && ext === "pptx" && (
            <PptxViewer folder={folder} filename={filename} />
          )}

          {/* ── MD — raw text in iframe ───────────────────────────────────── */}
          {!loading && ext === "md" && (
            <iframe
              src={serveUrl}
              style={{ flex: 1, border: "none", width: "100%", height: "100%",
                fontFamily: "Georgia,serif", background: "#FAFAF7" }}
              title={filename}
            />
          )}
        </div>
      </div>
    </div>
  );
}
