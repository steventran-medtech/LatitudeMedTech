"use strict";
const pptxgen = require("pptxgenjs");

const OUT = "C:\\Users\\huann\\LatitudeMedTech\\Branding\\latitude_brand_sales_deck.pptx";

// ── Brand constants ──────────────────────────────────────────────────────────
const C = {
  BLACK:      "1A1A1A",
  SLATE:      "2C3E50",
  BLUE:       "5B7FA6",
  MUTED:      "8A8680",
  WHITE:      "FFFFFF",
  OFF_WHITE:  "F7F7F6",
  BLUE_TINT:  "EBF0F6",
  LIGHT_RULE: "E0E0DC",
  RED_STOP:   "C0392B",
};
const FONT = "Calibri";

// ── Helpers ──────────────────────────────────────────────────────────────────
function makeShadow() {
  return { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.12 };
}

function sectionLabel(slide, text, x, y, color) {
  slide.addText(text, {
    x, y, w: 4, h: 0.22,
    fontFace: FONT, fontSize: 9, bold: false,
    charSpacing: 4, color: color || C.MUTED,
    margin: 0,
  });
}

function darkRule(slide, x, y, w) {
  slide.addShape("rect", { x, y, w, h: 0.025, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });
}

// ── Build deck ───────────────────────────────────────────────────────────────
async function build() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10" × 5.625"
  pres.title  = "Latitude MedTech LLC — Brand & Sales Deck";
  pres.author = "Latitude MedTech LLC";

  // ==========================================================================
  // SLIDE 1 — Cover
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.BLACK };

    // Thin top accent bar
    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    // LATITUDE MEDTECH LLC wordmark
    s.addText("LATITUDE MEDTECH LLC", {
      x: 0.55, y: 1.35, w: 8.9, h: 0.85,
      fontFace: FONT, fontSize: 46, bold: true,
      charSpacing: 5, color: C.WHITE, align: "left", margin: 0,
    });

    // LM_BLUE rule below title
    s.addShape("rect", { x: 0.55, y: 2.28, w: 8.9, h: 0.03, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    // Subtitle
    s.addText("Precision Consulting for MedTech & Pharma", {
      x: 0.55, y: 2.42, w: 8.9, h: 0.55,
      fontFace: FONT, fontSize: 22, bold: false,
      color: C.BLUE, align: "left", margin: 0,
    });

    // Bottom rule
    s.addShape("rect", { x: 0.55, y: 4.35, w: 8.9, h: 0.025, fill: { color: "333333" }, line: { color: "333333", width: 0 } });

    // Contact line 1
    s.addText("Steven Tran  ·  Managing Partner & CEO", {
      x: 0.55, y: 4.5, w: 8.9, h: 0.35,
      fontFace: FONT, fontSize: 14, bold: false,
      color: C.WHITE, align: "left", margin: 0,
    });
    // Contact line 2
    s.addText("San Diego, CA  ·  latitudemedtech.com  ·  Alpha Phase · 2026", {
      x: 0.55, y: 4.85, w: 8.9, h: 0.3,
      fontFace: FONT, fontSize: 12, bold: false,
      color: C.MUTED, align: "left", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 2 — The Market Gap
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    // Title
    s.addText("The $7B Problem Nobody Solves Well", {
      x: 0.5, y: 0.3, w: 6.6, h: 0.75,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    // Rule under title
    darkRule(s, 0.5, 1.12, 6.6);

    // Bullets
    s.addText([
      { text: "6,000+ medical device companies in the US; fewer than 12% have dedicated in-house RA/QA staff", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
      { text: "Average FDA 510(k) clearance: 177 days for the least complex devices; PMA averages 3–5 years", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
      { text: "Big 4 consultancies charge $350–$600/hr with 6-month minimums — inaccessible to Series A/B startups", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
      { text: "Legacy AI tools (Lilli, GENE) answer queries; they do not reason, plan, or execute alongside the client", options: { bullet: true, breakLine: false } },
    ], {
      x: 0.5, y: 1.25, w: 6.6, h: 3.7,
      fontFace: FONT, fontSize: 14.5,
      color: C.BLACK, align: "left",
      valign: "top",
    });

    // Pull-stat callout — right side
    s.addShape("rect", {
      x: 7.5, y: 0.9, w: 2.1, h: 2.8,
      fill: { color: C.BLUE_TINT },
      line: { color: C.BLUE, width: 1.5 },
    });
    s.addText("177", {
      x: 7.5, y: 1.0, w: 2.1, h: 1.3,
      fontFace: FONT, fontSize: 72, bold: true,
      color: C.BLUE, align: "center", valign: "middle", margin: 0,
    });
    s.addText([
      { text: "DAYS", options: { bold: true, breakLine: true } },
      { text: "avg 510(k)", options: { bold: false, breakLine: true } },
      { text: "clearance", options: { bold: false } },
    ], {
      x: 7.5, y: 2.35, w: 2.1, h: 0.9,
      fontFace: FONT, fontSize: 12,
      color: C.SLATE, align: "center", valign: "top", margin: 0,
    });

    // Footnote
    s.addText("Source: FDA CDRH Device Advice, 2024 performance data. Figures are illustrative benchmarks.", {
      x: 0.5, y: 5.2, w: 9, h: 0.25,
      fontFace: FONT, fontSize: 8, italic: true,
      color: C.MUTED, align: "left", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 3 — Who We Are (split columns)
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    // Left column fill
    s.addShape("rect", { x: 0, y: 0, w: 4.8, h: 5.625, fill: { color: C.SLATE }, line: { color: C.SLATE, width: 0 } });

    // Left — section label
    sectionLabel(s, "ABOUT LATITUDE MEDTECH", 0.35, 0.5, C.BLUE);

    // Left — title
    s.addText("AI-Native MedTech\nConsulting. Built for Speed.", {
      x: 0.35, y: 0.85, w: 4.1, h: 1.4,
      fontFace: FONT, fontSize: 22, bold: true,
      color: C.WHITE, align: "left", valign: "top", margin: 0,
    });

    // Left — rule
    s.addShape("rect", { x: 0.35, y: 2.35, w: 4.1, h: 0.025, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    // Left — bullets
    s.addText([
      { text: "Latitude MedTech LLC · San Diego, CA · Biocom member", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
      { text: "E2E AI-powered management consulting — MedTech & Pharma", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
      { text: "Two lines: Coaching (active) + Consulting (scaling)", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } },
      { text: "No 6-month minimums. No junior staff. Senior expertise, AI-augmented.", options: { bullet: true } },
    ], {
      x: 0.35, y: 2.5, w: 4.1, h: 2.5,
      fontFace: FONT, fontSize: 13,
      color: C.WHITE, align: "left", valign: "top",
    });

    // Right — section label
    sectionLabel(s, "MANAGING PARTNER & CEO", 5.1, 0.5, C.MUTED);

    // Right — name
    s.addText("Steven Tran", {
      x: 5.1, y: 0.85, w: 4.5, h: 0.6,
      fontFace: FONT, fontSize: 26, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    // Right — rule
    s.addShape("rect", { x: 5.1, y: 1.52, w: 4.5, h: 0.025, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    // Right — details
    s.addText([
      { text: "Domain Expertise", options: { bold: true, color: C.SLATE, breakLine: true } },
      { text: "FDA 21 CFR 820  ·  ISO 13485  ·  EU MDR  ·  MDSAP", options: { breakLine: true, paraSpaceAfter: 12 } },
      { text: "Network & Community", options: { bold: true, color: C.SLATE, breakLine: true } },
      { text: "Biocom SoCal corridor  ·  UC San Diego  ·  RAPS", options: { breakLine: true, paraSpaceAfter: 12 } },
      { text: "Contact", options: { bold: true, color: C.SLATE, breakLine: true } },
      { text: "steven.tran@latitudemedtech.com", options: { breakLine: true, color: C.BLUE, paraSpaceAfter: 12 } },
      { text: "linkedin.com/in/huanntran100", options: { color: C.BLUE } },
    ], {
      x: 5.1, y: 1.7, w: 4.5, h: 3.5,
      fontFace: FONT, fontSize: 13,
      color: C.BLACK, align: "left", valign: "top",
    });
  }

  // ==========================================================================
  // SLIDE 4 — The Athena Advantage
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.SLATE };

    // Title
    s.addText("Your AI Consulting Backbone", {
      x: 0.5, y: 0.3, w: 6.2, h: 0.7,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.WHITE, align: "left", margin: 0,
    });
    darkRule(s, 0.5, 1.08, 6.2);

    // Bullets
    s.addText([
      { text: "Athena is Latitude's proprietary AI system — not a chatbot, an autonomous reasoning engine", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
      { text: "Voice-activated briefings: speak a regulatory question, receive a structured analysis in seconds", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
      { text: "Knowledge base: 50-year regulatory history — FDA enforcement actions back to the 1976 Medical Device Act, full ISO 13485 and EU MDR corpus", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
      { text: "Interactive reasoning vs. search: Athena synthesizes, plans, and executes — it does not return links", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
      { text: "vs. Lilli (McKinsey): client-side deployment, no vendor lock-in, auditable reasoning chain", options: { bullet: true, breakLine: true, paraSpaceAfter: 7 } },
      { text: "vs. GENE (Deloitte): transparent outputs, MedTech-specific corpus, voice-first interface", options: { bullet: true } },
    ], {
      x: 0.5, y: 1.2, w: 6.2, h: 4.0,
      fontFace: FONT, fontSize: 13.5,
      color: C.WHITE, align: "left", valign: "top",
    });

    // Pull-stat callout box
    s.addShape("rect", {
      x: 7.15, y: 1.0, w: 2.5, h: 3.2,
      fill: { color: "1A2B3C" },
      line: { color: C.BLUE, width: 1.5 },
    });
    s.addText("50", {
      x: 7.15, y: 1.1, w: 2.5, h: 1.2,
      fontFace: FONT, fontSize: 80, bold: true,
      color: C.BLUE, align: "center", valign: "middle", margin: 0,
    });
    s.addText([
      { text: "YEARS", options: { bold: true, breakLine: true } },
      { text: "regulatory", options: { breakLine: true } },
      { text: "history", options: { breakLine: true } },
      { text: "in Athena's KB", options: {} },
    ], {
      x: 7.15, y: 2.35, w: 2.5, h: 1.5,
      fontFace: FONT, fontSize: 12,
      color: C.WHITE, align: "center", valign: "top", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 5 — Coaching Line
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Coaching Line — Active", {
      x: 0.4, y: 0.25, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });
    s.addText("From QA Associate to Director in 18 Months", {
      x: 0.4, y: 0.85, w: 9.2, h: 0.35,
      fontFace: FONT, fontSize: 15, bold: false, italic: true,
      color: C.BLUE, align: "left", margin: 0,
    });

    // Three offering cards
    const cards = [
      {
        header: "Regulatory\nCareer Roadmap",
        body: "Personalized 12-month plan: skills gap analysis, target role mapping, certification sequencing (RAPS RAC, ASQ CQE/CBA). Benchmarked to SoCal device market salaries.",
        x: 0.3,
      },
      {
        header: "Interview &\nPositioning",
        body: "510(k) and EU MDR technical interview prep; regulatory portfolio review; compensation benchmarking for roles at Edwards, Masimo, Dexcom, and SoCal startups.",
        x: 3.48,
      },
      {
        header: "Strategic\nCoaching",
        body: "Monthly 1:1 sessions with Athena-generated progress reports; job search campaign management; offer negotiation strategy.",
        x: 6.66,
      },
    ];

    cards.forEach(({ header, body, x }) => {
      // Card background
      s.addShape("rect", {
        x, y: 1.35, w: 3.0, h: 3.6,
        fill: { color: C.WHITE },
        line: { color: C.LIGHT_RULE, width: 1 },
        shadow: makeShadow(),
      });
      // Header bar
      s.addShape("rect", {
        x, y: 1.35, w: 3.0, h: 0.08,
        fill: { color: C.BLUE },
        line: { color: C.BLUE, width: 0 },
      });
      // Header text
      s.addText(header, {
        x: x + 0.15, y: 1.48, w: 2.7, h: 0.75,
        fontFace: FONT, fontSize: 14, bold: true,
        color: C.SLATE, align: "left", valign: "top", margin: 0,
      });
      // Rule
      s.addShape("rect", { x: x + 0.15, y: 2.28, w: 2.7, h: 0.02, fill: { color: C.BLUE_TINT }, line: { color: C.BLUE_TINT, width: 0 } });
      // Body text
      s.addText(body, {
        x: x + 0.15, y: 2.38, w: 2.7, h: 2.35,
        fontFace: FONT, fontSize: 12,
        color: C.BLACK, align: "left", valign: "top",
      });
    });

    // Bottom note
    s.addText("Consulting line activates Q4 2026 pending regulatory clearance. All coaching engagements subject to Steven Tran's review.", {
      x: 0.3, y: 5.2, w: 9.4, h: 0.25,
      fontFace: FONT, fontSize: 9, italic: true,
      color: C.MUTED, align: "center", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 6 — Consulting Line (Coming)
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Consulting Line — Coming Q4 2026", {
      x: 0.4, y: 0.25, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });
    s.addText("FDA  ·  EU MDR  ·  ISO 13485  ·  MDSAP", {
      x: 0.4, y: 0.88, w: 9.2, h: 0.35,
      fontFace: FONT, fontSize: 15, charSpacing: 1,
      color: C.BLUE, align: "left", margin: 0,
    });
    darkRule(s, 0.4, 1.27, 9.2);

    // Two service columns
    const leftServices = [
      "510(k) & De Novo strategy",
      "PMA submission support",
      "Design controls (21 CFR Part 820)",
      "CAPA system build & training",
    ];
    const rightServices = [
      "QMS gap assessments (ISO 13485)",
      "EU MDR Article 10 compliance",
      "MDSAP audit preparation",
      "Post-market surveillance programs",
    ];

    // Left column header
    s.addText("Regulatory Submissions", {
      x: 0.5, y: 1.45, w: 4.2, h: 0.38,
      fontFace: FONT, fontSize: 14, bold: true,
      color: C.SLATE, align: "left", margin: 0,
    });
    s.addText(leftServices.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < leftServices.length - 1, paraSpaceAfter: 8 } })), {
      x: 0.5, y: 1.9, w: 4.2, h: 2.6,
      fontFace: FONT, fontSize: 14,
      color: C.BLACK, align: "left", valign: "top",
    });

    // Right column header
    s.addText("Quality Systems", {
      x: 5.3, y: 1.45, w: 4.2, h: 0.38,
      fontFace: FONT, fontSize: 14, bold: true,
      color: C.SLATE, align: "left", margin: 0,
    });
    s.addText(rightServices.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < rightServices.length - 1, paraSpaceAfter: 8 } })), {
      x: 5.3, y: 1.9, w: 4.2, h: 2.6,
      fontFace: FONT, fontSize: 14,
      color: C.BLACK, align: "left", valign: "top",
    });

    // Divider between columns
    s.addShape("rect", { x: 4.9, y: 1.4, w: 0.025, h: 3.0, fill: { color: C.LIGHT_RULE }, line: { color: C.LIGHT_RULE, width: 0 } });

    // Banner at bottom
    s.addShape("rect", {
      x: 0, y: 4.8, w: 10, h: 0.825,
      fill: { color: C.BLUE_TINT },
      line: { color: C.BLUE, width: 1 },
    });
    s.addText("Gated pending non-compete clearance + RAC credential.  Pipeline intake is open — contact to join the waitlist.", {
      x: 0.4, y: 4.88, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 13, bold: false,
      color: C.SLATE, align: "center", valign: "middle",
    });

    // Watermark "COMING Q4 2026"
    s.addText("COMING Q4 2026", {
      x: 1.5, y: 1.8, w: 7, h: 1.5,
      fontFace: FONT, fontSize: 64, bold: true,
      color: C.MUTED, align: "center", valign: "middle",
      transparency: 85, rotate: 340,
    });
  }

  // ==========================================================================
  // SLIDE 7 — Competitive Positioning
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("We Out-Execute at 1/10th the Cost", {
      x: 0.4, y: 0.25, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    const headerCell = (text) => ({
      text,
      options: { fill: { color: C.BLUE }, color: C.WHITE, bold: true, align: "center", fontFace: FONT, fontSize: 12 },
    });
    const labelCell = (text) => ({
      text,
      options: { fill: { color: C.OFF_WHITE }, color: C.BLACK, bold: true, fontFace: FONT, fontSize: 12 },
    });
    const cell = (text, highlight) => ({
      text,
      options: {
        fill: { color: highlight ? C.BLUE_TINT : C.WHITE },
        color: C.BLACK,
        align: "center",
        fontFace: FONT, fontSize: 12,
      },
    });
    const checkCell = (text, highlight) => ({
      text,
      options: {
        fill: { color: highlight ? C.BLUE_TINT : C.WHITE },
        color: highlight ? C.BLUE : C.BLACK,
        bold: highlight,
        align: "center",
        fontFace: FONT, fontSize: 12,
      },
    });

    const tableData = [
      [ headerCell(""), headerCell("Legacy Big 4"), headerCell("AI Tools (Lilli/GENE)"), headerCell("Latitude MedTech") ],
      [ labelCell("Engagement minimum"), cell("6 months"), cell("Annual subscription"), checkCell("Project-scoped", true) ],
      [ labelCell("Pricing"), cell("$350–$600/hr"), cell("$50k+ per year"), checkCell("Value-based", true) ],
      [ labelCell("Reasoning depth"), cell("Junior staff"), cell("Search-and-retrieve"), checkCell("Senior AI + human", true) ],
      [ labelCell("Regulatory depth"), cell("Generalist"), cell("Generalist"), checkCell("MedTech-specific", true) ],
      [ labelCell("Voice interface"), cell("No"), cell("No"), checkCell("Yes (Athena)", true) ],
      [ labelCell("SoCal network"), cell("Limited"), cell("None"), checkCell("Biocom-embedded", true) ],
    ];

    s.addTable(tableData, {
      x: 0.4, y: 1.05, w: 9.2,
      colW: [2.4, 2.0, 2.4, 2.4],
      rowH: 0.5,
      border: { pt: 0.5, color: C.LIGHT_RULE },
    });
  }

  // ==========================================================================
  // SLIDE 8 — Target Clients
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Ideal Client Profile", {
      x: 0.4, y: 0.25, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });
    darkRule(s, 0.4, 0.92, 9.2);

    const personas = [
      {
        label: "COACHING LINE",
        title: "QA / RA Professional",
        stat: "$95k–$130k",
        statLabel: "current comp",
        bullets: [
          "Mid-career (5–10 yrs), targeting Director/VP transition",
          "Frustrated by slow career velocity at OEM",
          "SoCal-based, open to AI-enhanced coaching",
          "Goal: RAC credential + 25%+ comp increase in 18 months",
        ],
        x: 0.25,
      },
      {
        label: "CONSULTING LINE",
        title: "MedTech Startup (Series A/B)",
        stat: "$3M–$15M",
        statLabel: "raised",
        bullets: [
          "VP Engineering or CEO at Class II device startup",
          "18–24 months to 510(k) target clearance",
          "No in-house regulatory affairs staff",
          "Needs strategy, not a 6-month consulting commitment",
        ],
        x: 3.45,
      },
      {
        label: "BOTH LINES",
        title: "MedTech OEM L&D",
        stat: "50–500",
        statLabel: "person RA/QA teams",
        bullets: [
          "HR/L&D Director at Edwards, Masimo, Dexcom",
          "Seeking scalable regulatory upskilling programs",
          "Budget: L&D line item, not consulting project code",
          "Outcome: faster cert attainment, lower attrition",
        ],
        x: 6.65,
      },
    ];

    personas.forEach(({ label, title, stat, statLabel, bullets, x }) => {
      // Card
      s.addShape("rect", {
        x, y: 1.05, w: 3.05, h: 4.3,
        fill: { color: C.BLUE_TINT },
        line: { color: C.BLUE, width: 1 },
        shadow: makeShadow(),
      });
      // Label chip
      s.addShape("rect", {
        x: x + 0.12, y: 1.18, w: 2.82, h: 0.28,
        fill: { color: C.BLUE },
        line: { color: C.BLUE, width: 0 },
      });
      s.addText(label, {
        x: x + 0.12, y: 1.18, w: 2.82, h: 0.28,
        fontFace: FONT, fontSize: 9, bold: true, charSpacing: 2,
        color: C.WHITE, align: "center", valign: "middle", margin: 0,
      });
      // Title
      s.addText(title, {
        x: x + 0.12, y: 1.55, w: 2.82, h: 0.55,
        fontFace: FONT, fontSize: 15, bold: true,
        color: C.SLATE, align: "left", valign: "top", margin: 0,
      });
      // Stat
      s.addText(stat, {
        x: x + 0.12, y: 2.1, w: 2.82, h: 0.55,
        fontFace: FONT, fontSize: 24, bold: true,
        color: C.BLUE, align: "left", margin: 0,
      });
      s.addText(statLabel, {
        x: x + 0.12, y: 2.65, w: 2.82, h: 0.3,
        fontFace: FONT, fontSize: 10,
        color: C.MUTED, align: "left", margin: 0,
      });
      // Rule
      s.addShape("rect", { x: x + 0.12, y: 3.0, w: 2.82, h: 0.02, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });
      // Bullets
      s.addText(
        bullets.map((b, i) => ({ text: b, options: { bullet: true, breakLine: i < bullets.length - 1, paraSpaceAfter: 5 } })),
        {
          x: x + 0.12, y: 3.1, w: 2.82, h: 2.0,
          fontFace: FONT, fontSize: 11.5,
          color: C.BLACK, align: "left", valign: "top",
        }
      );
    });
  }

  // ==========================================================================
  // SLIDE 9 — Go-to-Market: Guerilla Playbook
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    // Dark left sidebar
    s.addShape("rect", { x: 0, y: 0, w: 2.6, h: 5.625, fill: { color: C.BLACK }, line: { color: C.BLACK, width: 0 } });

    s.addText("How We\nWin Without\nAds", {
      x: 0.15, y: 0.5, w: 2.3, h: 2.0,
      fontFace: FONT, fontSize: 22, bold: true,
      color: C.WHITE, align: "left", valign: "top", margin: 0,
    });

    s.addText([
      { text: "Saturated channels ", options: { bold: false } },
      { text: "off-limits:", options: { bold: true, breakLine: true } },
      { text: "LinkedIn feed ads,\nInstagram, YouTube,\nGoogle Ads", options: {} },
    ], {
      x: 0.15, y: 3.4, w: 2.3, h: 1.8,
      fontFace: FONT, fontSize: 11, italic: true,
      color: C.MUTED, align: "left", valign: "top", margin: 0,
    });

    // Five channel rows
    const channels = [
      {
        num: "01",
        name: "CONFERENCE CIRCUIT",
        body: "Targeted presence at MD&M West (Feb), Biocom Annual (Q1), RAPS Convergence (Oct). Strategy: corridor conversations, not booths. Speaking abstracts submitted 6 months out.",
      },
      {
        num: "02",
        name: "PODCAST CIRCUIT",
        body: "Guest appearances on The Medical Device Podcast (Jon Speer / Greenlight Guru), MedTech Talk, RCFM. Pitch: \"AI-native consulting — what it means for your 510(k).\"",
      },
      {
        num: "03",
        name: "REGULATORY CLINIC",
        body: "Monthly free 45-min office hours at Biocom San Diego. One specific regulatory question answered live. Upsell rate target: 20% to paid engagement.",
      },
      {
        num: "04",
        name: "MEDTECH MERIDIAN",
        body: "Weekly Substack (target: 500 subscribers by Month 6). Format: one specific regulatory development + what it means for device companies. No AI fluff.",
      },
      {
        num: "05",
        name: "FDA DOCKET PARTICIPATION",
        body: "Submit comments on 2–3 open FDA guidance dockets per year as \"Latitude MedTech LLC.\" Builds public regulatory credibility with zero ad spend.",
      },
    ];

    channels.forEach(({ num, name, body }, i) => {
      const y = 0.18 + i * 1.05;
      // Number
      s.addText(num, {
        x: 2.75, y: y, w: 0.6, h: 0.45,
        fontFace: FONT, fontSize: 20, bold: true,
        color: C.BLUE, align: "left", margin: 0,
      });
      // Channel name
      s.addText(name, {
        x: 3.3, y: y, w: 6.3, h: 0.35,
        fontFace: FONT, fontSize: 13, bold: true, charSpacing: 1,
        color: C.SLATE, align: "left", margin: 0,
      });
      // Body
      s.addText(body, {
        x: 3.3, y: y + 0.38, w: 6.3, h: 0.55,
        fontFace: FONT, fontSize: 11.5,
        color: C.BLACK, align: "left", margin: 0,
      });
      // Separator (except last)
      if (i < 4) {
        s.addShape("rect", { x: 2.75, y: y + 1.0, w: 7.0, h: 0.015, fill: { color: C.LIGHT_RULE }, line: { color: C.LIGHT_RULE, width: 0 } });
      }
    });
  }

  // ==========================================================================
  // SLIDE 10 — 30-60-90 Day Plan
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.OFF_WHITE };

    s.addText("90 Days to First Revenue", {
      x: 0.4, y: 0.2, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    const columns = [
      {
        range: "DAY 1–30",
        theme: "LAUNCH",
        x: 0.3,
        items: [
          "Biocom membership activated — attend 2 chapter events",
          "Podcast pitches sent: The Medical Device Podcast + MedTech Talk",
          "Substack MedTech Meridian: first 4 issues published",
          "RAPS SoCal Chapter: joined + first meeting attended",
          "Pipeline: 20 targets identified and emailed",
        ],
        metric: "Target: 20 outreach emails sent",
      },
      {
        range: "DAY 31–60",
        theme: "BUILD",
        x: 3.45,
        items: [
          "Regulatory Clinic: first session held at Biocom SD",
          "Conference: RAPS Convergence abstract submitted",
          "Podcast: 1 confirmed recording date",
          "Substack: 200 subscribers",
          "Pipeline: 5 discovery calls completed",
        ],
        metric: "Target: 5 discovery calls",
      },
      {
        range: "DAY 61–90",
        theme: "CONVERT",
        x: 6.6,
        items: [
          "First paid coaching client: onboarded",
          "Pipeline: 3 consulting waitlist signups",
          "Podcast: 1 episode live",
          "Substack: 350 subscribers",
          "Speaking: 1 Biocom chapter talk confirmed",
        ],
        metric: "Target: 1 paid client",
      },
    ];

    columns.forEach(({ range, theme, x, items, metric }) => {
      // Card background
      s.addShape("rect", {
        x, y: 0.95, w: 3.0, h: 4.5,
        fill: { color: C.WHITE },
        line: { color: C.LIGHT_RULE, width: 1 },
        shadow: makeShadow(),
      });
      // Header bar
      s.addShape("rect", {
        x, y: 0.95, w: 3.0, h: 0.72,
        fill: { color: C.BLUE },
        line: { color: C.BLUE, width: 0 },
      });
      // Range label
      s.addText(range, {
        x: x + 0.12, y: 0.98, w: 2.76, h: 0.28,
        fontFace: FONT, fontSize: 11, bold: true, charSpacing: 2,
        color: C.WHITE, align: "left", valign: "middle", margin: 0,
      });
      // Theme label
      s.addText(theme, {
        x: x + 0.12, y: 1.28, w: 2.76, h: 0.28,
        fontFace: FONT, fontSize: 18, bold: true,
        color: "A8C4DC", align: "left", valign: "top", margin: 0,
      });
      // Items
      s.addText(
        items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } })),
        {
          x: x + 0.12, y: 1.75, w: 2.76, h: 2.9,
          fontFace: FONT, fontSize: 12,
          color: C.BLACK, align: "left", valign: "top",
        }
      );
      // Metric callout
      s.addShape("rect", {
        x, y: 5.0, w: 3.0, h: 0.45,
        fill: { color: C.BLUE_TINT },
        line: { color: C.LIGHT_RULE, width: 0 },
      });
      s.addText(metric, {
        x: x + 0.12, y: 5.02, w: 2.76, h: 0.38,
        fontFace: FONT, fontSize: 11, bold: true,
        color: C.SLATE, align: "center", valign: "middle", margin: 0,
      });
    });
  }

  // ==========================================================================
  // SLIDE 11 — Case Studies
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Early Proof Points (To Be Captured)", {
      x: 0.4, y: 0.2, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 28, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });
    darkRule(s, 0.4, 0.88, 9.2);

    const cases = [
      {
        title: "Class II Startup, San Diego",
        subtitle: "510(k) Strategy",
        situation: "Series A device company, 2 engineers, no in-house RA/QA staff, 18 months to target launch date.",
        approach: "3-month engagement: Athena-driven 510(k) gap analysis, predicate search, regulatory strategy roadmap.",
        impact: "[Outcome to be captured — Q4 2026]",
        x: 0.25,
      },
      {
        title: "QA Manager to Director",
        subtitle: "14-Month Coaching",
        situation: "8-year QA professional plateaued at $102k, targeting Director role at a Tier 1 device OEM.",
        approach: "Latitude coaching program: RAC prep, positioning strategy, technical interview coaching.",
        impact: "[Outcome to be captured]",
        x: 3.45,
      },
      {
        title: "ISO 13485 QMS Build",
        subtitle: "60-Day Engagement",
        situation: "Medical device startup needed QMS for Notified Body submission under EU MDR Article 10.",
        approach: "Athena-generated QMS framework, gap assessment against ISO 13485:2016 + MDSAP requirements.",
        impact: "[Outcome to be captured]",
        x: 6.65,
      },
    ];

    cases.forEach(({ title, subtitle, situation, approach, impact, x }) => {
      // Card
      s.addShape("rect", {
        x, y: 1.0, w: 3.0, h: 4.35,
        fill: { color: C.WHITE },
        line: { color: C.LIGHT_RULE, width: 1 },
        shadow: makeShadow(),
      });
      // Left accent bar
      s.addShape("rect", { x, y: 1.0, w: 0.08, h: 4.35, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

      // Title
      s.addText(title, {
        x: x + 0.18, y: 1.08, w: 2.72, h: 0.38,
        fontFace: FONT, fontSize: 13, bold: true,
        color: C.SLATE, align: "left", margin: 0,
      });
      s.addText(subtitle, {
        x: x + 0.18, y: 1.48, w: 2.72, h: 0.28,
        fontFace: FONT, fontSize: 11, bold: false, italic: true,
        color: C.BLUE, align: "left", margin: 0,
      });

      // SIA structure
      const sections = [
        { label: "SITUATION", text: situation },
        { label: "APPROACH", text: approach },
        { label: "IMPACT", text: impact, italic: true, color: C.MUTED },
      ];
      let ty = 1.88;
      sections.forEach(({ label, text, italic: isItalic, color }) => {
        s.addText(label, {
          x: x + 0.18, y: ty, w: 2.72, h: 0.24,
          fontFace: FONT, fontSize: 9, bold: true, charSpacing: 2,
          color: C.BLUE, align: "left", margin: 0,
        });
        s.addText(text, {
          x: x + 0.18, y: ty + 0.24, w: 2.72, h: 0.72,
          fontFace: FONT, fontSize: 11.5, italic: isItalic || false,
          color: color || C.BLACK, align: "left", valign: "top",
        });
        ty += 1.05;
      });
    });

    // Note
    s.addText("Case studies collected from paying engagements and published only with explicit client approval. Identifying details anonymised.", {
      x: 0.25, y: 5.27, w: 9.5, h: 0.22,
      fontFace: FONT, fontSize: 8.5, italic: true,
      color: C.MUTED, align: "center", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 12 — Call to Action
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.BLACK };

    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    s.addText("Let's Talk", {
      x: 0.6, y: 0.7, w: 5.8, h: 0.9,
      fontFace: FONT, fontSize: 46, bold: true,
      color: C.WHITE, align: "left", margin: 0,
    });

    s.addShape("rect", { x: 0.6, y: 1.7, w: 5.8, h: 0.03, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    s.addText([
      { text: "30-minute discovery call — no obligation, no pitch deck", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
      { text: "We will answer one specific regulatory or career question on the call", options: { bullet: true, breakLine: true, paraSpaceAfter: 8 } },
      { text: "steven.tran@latitudemedtech.com", options: { bullet: true, breakLine: true, paraSpaceAfter: 8, color: C.BLUE } },
      { text: "latitudemedtech.com", options: { bullet: true, breakLine: true, paraSpaceAfter: 8, color: C.BLUE } },
      { text: "linkedin.com/in/huanntran100", options: { bullet: true, color: C.BLUE } },
    ], {
      x: 0.6, y: 1.85, w: 5.8, h: 3.2,
      fontFace: FONT, fontSize: 14,
      color: C.WHITE, align: "left", valign: "top",
    });

    // Pull quote
    s.addText("“The best consultants don’t sell engagements.\nThey solve problems.”", {
      x: 0.6, y: 4.7, w: 5.8, h: 0.7,
      fontFace: FONT, fontSize: 13, italic: true,
      color: C.MUTED, align: "left", margin: 0,
    });

    // QR placeholder box
    s.addShape("rect", {
      x: 7.3, y: 1.4, w: 2.3, h: 2.3,
      fill: { color: "1E1E1E" },
      line: { color: C.MUTED, width: 1 },
    });
    s.addText("QR CODE\nBooking Page\n\nAdd Calendly\nlink here", {
      x: 7.3, y: 1.4, w: 2.3, h: 2.3,
      fontFace: FONT, fontSize: 11, italic: true,
      color: C.MUTED, align: "center", valign: "middle",
    });
  }

  // ==========================================================================
  // SLIDE 13 — Brand Section Divider
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.BLACK };

    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    s.addText("LATITUDE MEDTECH", {
      x: 0.6, y: 1.5, w: 8.8, h: 1.1,
      fontFace: FONT, fontSize: 52, bold: true, charSpacing: 5,
      color: C.WHITE, align: "center", margin: 0,
    });

    s.addShape("rect", { x: 2.5, y: 2.75, w: 5.0, h: 0.04, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    s.addText("Brand Identity Standards  ·  2026", {
      x: 0.6, y: 2.95, w: 8.8, h: 0.5,
      fontFace: FONT, fontSize: 18, charSpacing: 3,
      color: C.BLUE, align: "center", margin: 0,
    });

    s.addText("For internal use. Applies to all client-facing and digital outputs.", {
      x: 0.6, y: 4.9, w: 8.8, h: 0.3,
      fontFace: FONT, fontSize: 10, italic: true,
      color: C.MUTED, align: "center", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 14 — Color Palette
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Brand Colors", {
      x: 0.4, y: 0.2, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    const swatches = [
      { hex: C.BLACK,      name: "LM BLACK",     usage: "Primary Text / Headings",       textColor: C.WHITE },
      { hex: C.SLATE,      name: "LM SLATE",      usage: "Secondary Headings / Nav",      textColor: C.WHITE },
      { hex: C.BLUE,       name: "LM BLUE",       usage: "Brand Accent / Links / Rules",  textColor: C.WHITE },
      { hex: C.MUTED,      name: "LM MUTED",      usage: "Captions / Metadata",           textColor: C.WHITE },
      { hex: C.OFF_WHITE,  name: "LM OFF-WHITE",  usage: "Page Background",               textColor: C.SLATE },
      { hex: C.BLUE_TINT,  name: "LM BLUE TINT",  usage: "Highlight Backgrounds",         textColor: C.SLATE },
    ];

    swatches.forEach(({ hex, name, usage, textColor }, i) => {
      const x = 0.35 + i * 1.57;
      // Swatch rectangle
      s.addShape("rect", {
        x, y: 1.0, w: 1.42, h: 2.4,
        fill: { color: hex },
        line: { color: hex === C.WHITE || hex === C.OFF_WHITE || hex === C.BLUE_TINT ? C.LIGHT_RULE : hex, width: 1 },
      });
      // Hex on swatch
      s.addText("#" + hex, {
        x, y: 2.75, w: 1.42, h: 0.38,
        fontFace: "Consolas", fontSize: 11, bold: true,
        color: textColor, align: "center", margin: 0,
      });
      // Name below
      s.addText(name, {
        x, y: 3.5, w: 1.42, h: 0.32,
        fontFace: FONT, fontSize: 11, bold: true,
        color: C.BLACK, align: "center", margin: 0,
      });
      // Usage
      s.addText(usage, {
        x, y: 3.85, w: 1.42, h: 0.55,
        fontFace: FONT, fontSize: 10,
        color: C.MUTED, align: "center",
      });
    });
  }

  // ==========================================================================
  // SLIDE 15 — Typography
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Typography System", {
      x: 0.4, y: 0.2, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    const samples = [
      {
        label: "H1 — Calibri Bold 32pt · #1A1A1A",
        sampleText: "Regulatory Strategy for the AI Era",
        fontFace: FONT, fontSize: 32, bold: true, color: C.BLACK,
        y: 1.05,
      },
      {
        label: "H2 — Calibri Regular 22pt · #2C3E50 · Tracked",
        sampleText: "510(k) PATHWAY ANALYSIS",
        fontFace: FONT, fontSize: 22, bold: false, charSpacing: 3, color: C.SLATE,
        y: 2.2,
      },
      {
        label: "Body — Calibri Regular 15pt · #1A1A1A",
        sampleText: "Latitude MedTech delivers AI-native management consulting to MedTech and Pharma companies in the Southern California corridor. All client outputs are reviewed by Steven Tran before delivery.",
        fontFace: FONT, fontSize: 15, bold: false, color: C.BLACK,
        y: 3.1,
      },
    ];

    samples.forEach(({ label, sampleText, fontFace, fontSize, bold, charSpacing, color, y }) => {
      s.addText(label, {
        x: 0.5, y, w: 9.0, h: 0.25,
        fontFace: FONT, fontSize: 9, charSpacing: 1.5,
        color: C.MUTED, align: "left", margin: 0,
      });
      s.addText(sampleText, {
        x: 0.5, y: y + 0.28, w: 9.0, h: 0.72,
        fontFace, fontSize, bold: bold || false,
        charSpacing: charSpacing || 0,
        color, align: "left", valign: "top",
      });
    });

    // Caption sample
    s.addShape("rect", { x: 0.5, y: 4.9, w: 9.0, h: 0.02, fill: { color: C.LIGHT_RULE }, line: { color: C.LIGHT_RULE, width: 0 } });
    s.addText("Caption — Calibri 10pt · #8A8680 · All caps · Tracked", {
      x: 0.5, y: 4.98, w: 3.5, h: 0.22,
      fontFace: FONT, fontSize: 9, charSpacing: 1.5,
      color: C.MUTED, align: "left", margin: 0,
    });
    s.addText("EDUCATIONAL PURPOSES ONLY  ·  NOT REGULATORY ADVICE", {
      x: 4.5, y: 4.96, w: 5.0, h: 0.25,
      fontFace: FONT, fontSize: 10, charSpacing: 2,
      color: C.MUTED, align: "right", margin: 0,
    });
  }

  // ==========================================================================
  // SLIDE 16 — Logo Usage
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Logo Usage Guidelines", {
      x: 0.4, y: 0.2, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });

    // Divider
    s.addShape("rect", { x: 4.9, y: 0.95, w: 0.02, h: 4.0, fill: { color: C.LIGHT_RULE }, line: { color: C.LIGHT_RULE, width: 0 } });

    // DO column
    s.addShape("rect", {
      x: 0.4, y: 0.95, w: 0.55, h: 0.32,
      fill: { color: C.BLUE },
      line: { color: C.BLUE, width: 0 },
    });
    s.addText("DO", {
      x: 0.4, y: 0.95, w: 0.55, h: 0.32,
      fontFace: FONT, fontSize: 12, bold: true,
      color: C.WHITE, align: "center", valign: "middle", margin: 0,
    });
    const doRules = [
      "Use the primary wordmark (black) on white or light backgrounds",
      "Use the reversed wordmark (white) on dark or photo backgrounds",
      "Maintain clear space: 1× the height of the “L” on all sides",
      "Use the icon mark alone only when brand context is established",
      "Use Calibri as the sole typeface in all brand materials",
    ];
    s.addText(
      doRules.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < doRules.length - 1, paraSpaceAfter: 7 } })),
      {
        x: 0.4, y: 1.38, w: 4.35, h: 3.4,
        fontFace: FONT, fontSize: 13,
        color: C.BLACK, align: "left", valign: "top",
      }
    );

    // DON'T column
    s.addShape("rect", {
      x: 5.15, y: 0.95, w: 0.9, h: 0.32,
      fill: { color: C.RED_STOP },
      line: { color: C.RED_STOP, width: 0 },
    });
    s.addText("DON’T", {
      x: 5.15, y: 0.95, w: 0.9, h: 0.32,
      fontFace: FONT, fontSize: 12, bold: true,
      color: C.WHITE, align: "center", valign: "middle", margin: 0,
    });
    const dontRules = [
      "Do not stretch, skew, or rotate the mark",
      "Do not use LM BLUE (#5B7FA6) for the wordmark text — it is always black or white",
      "Do not place the mark on busy photographic backgrounds",
      "Do not use fonts other than Calibri in brand materials",
      "Do not display the mark below 0.75\" width in print, or 54px wide on screen",
    ];
    s.addText(
      dontRules.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < dontRules.length - 1, paraSpaceAfter: 7 } })),
      {
        x: 5.15, y: 1.38, w: 4.45, h: 3.4,
        fontFace: FONT, fontSize: 13,
        color: C.BLACK, align: "left", valign: "top",
      }
    );
  }

  // ==========================================================================
  // SLIDE 17 — Document Standards
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.WHITE };

    s.addText("Document Standards", {
      x: 0.4, y: 0.2, w: 9.2, h: 0.6,
      fontFace: FONT, fontSize: 30, bold: true,
      color: C.BLACK, align: "left", margin: 0,
    });
    s.addText("Applies to: Word (.docx), PDF deliverables, coaching reports, client briefs", {
      x: 0.4, y: 0.82, w: 9.2, h: 0.3,
      fontFace: FONT, fontSize: 12, italic: true,
      color: C.MUTED, align: "left", margin: 0,
    });
    darkRule(s, 0.4, 1.18, 9.2);

    const specs = [
      { label: "Page size", value: "US Letter (8.5\" × 11\")  ·  Margins: 1\" all sides" },
      { label: "Header", value: "\"LATITUDE MEDTECH LLC\" — right-aligned, 7.5pt, LM BLUE (#5B7FA6)" },
      { label: "Footer", value: "Latitude MedTech LLC  ·  San Diego, CA  ·  latitudemedtech.com  ·  Generated [date]  ·  Educational purposes only — not regulatory advice" },
      { label: "Pull stats", value: "Calibri Bold 48pt, LM BLUE — used for key numbers in briefs and reports" },
      { label: "Section rules", value: "1.5pt LM BLUE horizontal line between major sections" },
      { label: "Table headers", value: "LM BLUE fill (#5B7FA6), white bold text, Calibri 12pt" },
      { label: "Disclaimer block", value: "9pt italic LM MUTED, bottom of last page, every deliverable" },
      { label: "Review label", value: "\"Alpha Phase — Steven Tran Review Required\" on all client-facing drafts" },
    ];

    specs.forEach(({ label, value }, i) => {
      const y = 1.3 + i * 0.52;
      s.addShape("rect", {
        x: 0.4, y, w: 2.4, h: 0.42,
        fill: { color: C.BLUE_TINT },
        line: { color: C.LIGHT_RULE, width: 0.5 },
      });
      s.addText(label, {
        x: 0.5, y: y + 0.05, w: 2.2, h: 0.32,
        fontFace: FONT, fontSize: 11, bold: true,
        color: C.SLATE, align: "left", margin: 0,
      });
      s.addText(value, {
        x: 2.9, y: y + 0.04, w: 6.7, h: 0.38,
        fontFace: FONT, fontSize: 11.5,
        color: C.BLACK, align: "left", valign: "top",
      });
    });
  }

  // ==========================================================================
  // SLIDE 18 — Brand Principles
  // ==========================================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.BLACK };

    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.BLUE }, line: { color: C.BLUE, width: 0 } });

    s.addText("The Latitude Standard", {
      x: 0.5, y: 0.22, w: 9, h: 0.65,
      fontFace: FONT, fontSize: 32, bold: true,
      color: C.WHITE, align: "left", margin: 0,
    });
    s.addShape("rect", { x: 0.5, y: 0.96, w: 9, h: 0.025, fill: { color: "222222" }, line: { color: "222222", width: 0 } });

    const principles = [
      {
        num: "01",
        name: "SPECIFICITY OVER GENERALITY",
        desc: "Every deliverable contains at least one specific, verifiable claim. No unsourced numbers. No vague language.",
      },
      {
        num: "02",
        name: "PRECISION OVER VOLUME",
        desc: "One well-reasoned brief outperforms ten generic reports. Fewer pages, more value per page.",
      },
      {
        num: "03",
        name: "SOURCED, NOT FABRICATED",
        desc: "All statistics cite a regulatory filing, guidance document, company announcement, or named publication.",
      },
      {
        num: "04",
        name: "HUMAN-GATED",
        desc: "No client output ships without Steven Tran’s review and approval. AI augments; humans sign.",
      },
      {
        num: "05",
        name: "DIGNITY IN ALL COMMUNICATIONS",
        desc: "Clients are partners, not accounts. Competitors are respected, not disparaged.",
      },
    ];

    principles.forEach(({ num, name, desc }, i) => {
      const y = 1.1 + i * 0.9;
      s.addText(num, {
        x: 0.5, y, w: 0.7, h: 0.55,
        fontFace: FONT, fontSize: 22, bold: true,
        color: C.BLUE, align: "left", margin: 0,
      });
      s.addText(name, {
        x: 1.25, y, w: 7.9, h: 0.35,
        fontFace: FONT, fontSize: 14, bold: true, charSpacing: 1.5,
        color: C.WHITE, align: "left", margin: 0,
      });
      s.addText(desc, {
        x: 1.25, y: y + 0.37, w: 7.9, h: 0.42,
        fontFace: FONT, fontSize: 12,
        color: C.MUTED, align: "left", valign: "top",
      });
    });
  }

  // ── Write file ─────────────────────────────────────────────────────────────
  await pres.writeFile({ fileName: OUT });
  console.log("Deck written to:", OUT);
}

build().catch(err => { console.error(err); process.exit(1); });
