"""
Seed the review queue with test documents for UI development / smoke testing.
Run once from the agents/ directory:  python seed_review_test_data.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pathconfig import BRIEFS_DIR, BRIEFINGS_DIR, DRAFTS_DIR, ATHENA_ROOT
from memory import Memory

DOCS_DIR = ATHENA_ROOT / "documents"

# ── Ensure output folders exist ───────────────────────────────────────────────
for d in (BRIEFS_DIR, BRIEFINGS_DIR, DRAFTS_DIR, DOCS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Test documents ─────────────────────────────────────────────────────────────
DOCS = [
    # (item_type, agent, title, folder, filename, status, notes, content)
    (
        "brief", "coaching_agent",
        "Career Transition Brief — Alex Chen, QA Manager to Director of Quality",
        BRIEFS_DIR,
        "brief_alex_chen_qa_director.md",
        "pending", "",
        """\
---
title: Career Transition Brief — Alex Chen
date: 2026-06-05
agent: coaching_agent
type: Coaching Brief
confidential: true
---

## Executive Summary

Alex Chen (8 yrs QA, currently Senior QA Manager at a $400M Class II device manufacturer) is targeting Director of Quality roles at mid-stage MedTech companies ($100–500M revenue). Principal gap: cross-functional P&L ownership and board-level regulatory communication.

## Current Profile

- **Role:** Senior QA Manager, Meridian Medical Devices
- **Scope:** 22-person QA team; FDA 21 CFR Part 820 compliance; Class II (510(k)) portfolio
- **Strengths:** CAPA closure rate 94% (industry avg 71%); led successful ISO 13485:2016 recertification in 2024
- **Gap:** No direct experience owning quality budget ($0 P&L exposure), limited executive stakeholder management

## Target Role Criteria

| Dimension | Target |
|-----------|--------|
| Company stage | Series C–D or profitable SME |
| Revenue | $100M–$500M |
| Device class | II–III |
| Regulatory scope | FDA + at least one EU MDR submission |

## 90-Day Action Plan

1. **Weeks 1–4:** Complete ASQ CQE recertification; enroll in financial literacy for quality leaders (ASQ Learning Institute, $1,200)
2. **Weeks 5–8:** Shadow CFO in two budget cycles at current employer; request line ownership for one QMS tool vendor contract
3. **Weeks 9–12:** Deliver a mock board QMS briefing to VP-level peers; document outcome metrics

## Recommended Positioning Statement

> "QA leader with a decade of Class II/III device compliance who has cut CAPA cycle time by 31% and led two successful FDA inspections without observations — now scaling into Director roles where quality is a commercial differentiator, not a cost centre."

*Drafted by Athena Coaching Agent — requires Steven's review before delivery.*
""",
    ),
    (
        "article", "content_agent",
        "FDA's QMSR Final Rule: What Small Device Makers Must Do Before July 2026",
        DRAFTS_DIR,
        "qmsr_final_rule_small_manufacturers_2026.md",
        "pending", "",
        """\
---
title: FDA's QMSR Final Rule — What Small Device Makers Must Do Before July 2026
date: 2026-06-05
agent: content_agent
type: Article
topic: QMSR / 21 CFR Part 820
---

## The Deadline Is Closer Than It Looks

The FDA's Quality Management System Regulation (QMSR), which aligns 21 CFR Part 820 with ISO 13485:2016, takes full effect **2 February 2026**. For the roughly 4,200 small device manufacturers (under 500 employees) that have not yet begun gap assessments, the window to remediate without a consent decree risk is measured in weeks, not months.

## What Changed — And What Didn't

QMSR does not replace ISO 13485 compliance; it imports it by reference. The three most operationally significant changes for small manufacturers are:

1. **Design controls are now risk-based per ISO 14971.** A documented hazard analysis tied to each design history file is no longer optional.
2. **Management review must produce measurable quality objectives** — a documented output with owners and deadlines, not a meeting summary.
3. **Supplier controls require supplier qualification evidence**, not just approved-supplier lists. Purchase orders alone will not survive an FDA inspection.

## The Remediation Sequence That Works

Based on Latitude MedTech's work with eight device firms in 2024–2025, the following sequence minimises rework:

1. Gap assessment against 21 CFR Part 820 → ISO 13485:2016 clause mapping (2–3 weeks)
2. Prioritise DHF and design-control procedures (highest FDA citation frequency in 483s)
3. Update CAPA SOP to include root-cause trending across quarters
4. Schedule an internal audit against QMSR criteria before engaging a notified body

## Cost Benchmark

A mid-size 510(k) manufacturer can expect $85,000–$140,000 in consulting and SOP remediation costs for a full QMSR transition, based on 2025 engagements. Companies that delay past July 2026 face Form 483 observations, which add an average of $220,000 in remediation costs per FDA estimate (2024 CBER/CDRH joint report).

---
*Drafted by Athena Content Agent — requires Steven's review and factual verification before publication.*
""",
    ),
    (
        "lesson", "iso_agent",
        "ISO 13485 §8.3 — Control of Nonconforming Product: Interactive Lesson",
        DOCS_DIR,
        "lesson_iso13485_8_3_nonconforming_product.md",
        "pending", "",
        """\
---
title: "ISO 13485 §8.3 — Control of Nonconforming Product"
date: 2026-06-05
agent: iso_agent
type: ISO Lesson
clause: "8.3"
duration_min: 25
---

## Learning Objectives

By the end of this lesson you will be able to:
- Identify the four required disposition options under §8.3
- Describe when a concession requires regulatory notification
- Complete a nonconformance record that meets audit requirements

## What §8.3 Requires

ISO 13485:2016 §8.3 mandates that any product that **does not conform to requirements** be identified and controlled to prevent unintended use or delivery. The standard is more prescriptive than ISO 9001 in two ways:

1. **Traceability to risk management** — each nonconformance disposition must reference the device's risk file (ISO 14971)
2. **Regulatory notification** — if a concession (use-as-is) is granted and the device is implantable or life-sustaining (Class III), the notified body or FDA may require prior notification

## The Four Disposition Paths

| Disposition | Trigger | Record Requirement |
|-------------|---------|-------------------|
| Rework | Defect correctable without design change | Before/after inspection records |
| Return to supplier | Supplier-caused nonconformance | NCR + supplier corrective action request |
| Concession (use-as-is) | Risk analysis confirms patient risk acceptable | Signed justification + risk file reference |
| Scrap/destroy | Risk unacceptable; rework not feasible | Destruction record + inventory adjustment |

## Common Audit Findings

The most frequent §8.3 finding in FDA 483s (2023–2025 CDRH data): **concessions granted without documented risk analysis**. Auditors look for a direct link between the NCR and the ISO 14971 risk file. A concession signed by a QA manager but missing the hazard reference is a Major nonconformity.

## Knowledge Check

> A batch of sterile packaging arrives with 3 of 50 pouches showing seal integrity failures. The batch has not shipped. Which disposition is most appropriate?

**Answer:** Return to supplier (supplier-caused nonconformance) and issue a supplier corrective action request. Do not concession sterile barrier failures on implantable components — this would require a risk analysis showing patient risk is acceptable, which is rarely defensible for barrier nonconformances.

---
*Drafted by Athena ISO Agent — requires Steven's review before release to learners.*
""",
    ),
    (
        "report", "consulting_agent",
        "M&A Target Scan: EU MDR-Ready Class II Cardiovascular Device Companies, Q2 2026",
        BRIEFINGS_DIR,
        "ma_scan_eu_mdr_cardiovascular_q2_2026.md",
        "approved",
        "Solid scan. Approved for client delivery — verify Ventrify valuation independently before sending.",
        """\
---
title: "M&A Target Scan: EU MDR-Ready Class II Cardiovascular Device Companies"
date: 2026-06-01
agent: consulting_agent
type: Consulting Report
quarter: Q2 2026
confidential: true
---

## Mandate

Identify Class II cardiovascular device companies with active EU MDR Article 52 QMS certifications and revenue between €20M–€80M that represent viable acquisition targets for a strategic buyer seeking EU market access without a de novo MDR submission.

## Screening Criteria

- EU MDR Article 52 QMS certificate issued or renewed 2023–2026
- Revenue €20M–€80M (2024 or most recent audited year)
- Primary product: cardiac monitoring, peripheral vascular, or structural heart (non-surgical)
- No pending competent authority investigation

## Shortlist (3 of 11 screened)

| Company | HQ | Revenue (est.) | MDR Status | Strategic Fit |
|---------|-----|---------------|------------|---------------|
| Ventrify GmbH | Munich | €34M | Article 52 cert issued Jan 2025 | Strong — cardiac monitoring overlaps buyer's US portfolio |
| CardioPath SAS | Lyon | €61M | Article 52 cert renewed Mar 2026 | Moderate — peripheral vascular, limited US synergy |
| NovaPace B.V. | Amsterdam | €28M | Article 52 cert issued Aug 2024 | Strong — structural heart, no overlap with buyer |

## Key Risk: MDR Post-Market Obligations

All three targets have ongoing PMCF (Post-Market Clinical Follow-up) obligations under EU MDR Annex XIV. Acquirer must budget for PMCF study continuation: estimated €400K–€900K annually per product line based on 2025 notified body fee schedules.

## Recommended Next Step

Proceed to NDA-gated due diligence on Ventrify GmbH and NovaPace B.V. Request 2024 audited financials and notified body surveillance audit reports before valuation modelling.

---
*Drafted by Athena Consulting Agent.*
""",
    ),
    (
        "brief", "coaching_agent",
        "Career Brief — Jordan Mills, Regulatory Affairs Specialist to RA Manager",
        BRIEFS_DIR,
        "brief_jordan_mills_ra_manager.md",
        "rejected",
        "Rewrite needed — the positioning statement is too generic. Needs specific submission counts and timeline.",
        """\
---
title: Career Brief — Jordan Mills, RA Specialist to RA Manager
date: 2026-05-28
agent: coaching_agent
type: Coaching Brief
confidential: true
---

## Executive Summary

Jordan Mills is a Regulatory Affairs Specialist with five years of experience seeking a step up to RA Manager. Jordan has strong technical writing skills and experience with 510(k) submissions.

## Current Profile

- **Role:** RA Specialist II, NovaMed Inc.
- **Experience:** 5 years RA; multiple 510(k) submissions; some EU MDR experience
- **Strengths:** Good documentation skills; team player; reliable
- **Gap:** Has not managed a team; limited direct FDA interaction

## Recommended Next Steps

- Work on leadership skills
- Get more experience with FDA interactions
- Consider a management course

## Positioning Statement

> "Experienced regulatory professional with a strong track record looking to take the next step in my career."

*Drafted by Athena Coaching Agent — requires Steven's review before delivery.*
""",
    ),
    (
        "article", "content_agent",
        "How MedTech Startups Should Structure Their First QMS: A Practical Guide",
        DRAFTS_DIR,
        "first_qms_medtech_startups_guide.md",
        "pending", "",
        """\
---
title: How MedTech Startups Should Structure Their First QMS — A Practical Guide
date: 2026-06-04
agent: content_agent
type: Article
topic: QMS / ISO 13485 / Startup
---

## The Mistake Most Startups Make

Most early-stage medical device companies build their quality management system the wrong way: they hire a consultant, receive 80 SOPs in a SharePoint folder, and declare themselves "ISO 13485 ready." Eighteen months later, they face a notified body audit and discover that none of the procedures reflect how the company actually operates.

The QMS that passes an audit is not the same as the QMS that prevents patient harm. The goal is to build the second one.

## The Four-Document Core

A pre-revenue Class II startup needs exactly four foundational documents before investing in procedure libraries:

1. **Quality Manual (5–8 pages):** Scope, exclusions, and the management commitment statement. This is the only document the CEO should personally sign.
2. **Risk Management Plan (per ISO 14971):** Maps every intended use scenario to hazard, probability of harm, and severity. Without this, CAPA and design controls are disconnected.
3. **Design and Development Plan:** One document per product, not a template. Captures inputs, outputs, verification methods, and the responsible engineer by name.
4. **CAPA Procedure:** The single most scrutinised document in any FDA inspection. It must include root-cause methodology (Ishikawa or 5-Why), effectiveness check cadence, and trending frequency.

## What to Defer Until Series A

- Automated document control systems (Veeva, MasterControl) — a $1,200/month tool for a 12-person team with three products is overhead without ROI
- Full supplier qualification programs — qualify your three tier-1 suppliers thoroughly; build the broader program post-Series A
- ISO 13485 third-party certification — target surveillance audit 18–24 months after your first 510(k) clearance

## The Right Hire Sequence

1. **First quality hire (pre-seed):** A regulatory writer who owns the QMS documentation
2. **Second quality hire (Seed–Series A):** A QA engineer who owns design controls and V&V
3. **Third quality hire (Series A+):** A QA/RA manager who interfaces with FDA and notified bodies

---
*Drafted by Athena Content Agent — requires Steven's review and factual verification before publication.*
""",
    ),
]


def main():
    mem = Memory()
    created = 0
    skipped = 0

    for item_type, agent, title, folder, filename, status, notes, content in DOCS:
        fpath = folder / filename

        # Write the markdown file (skip if already exists to avoid overwriting real work)
        if fpath.exists():
            print(f"  [skip file] {filename} already exists")
            skipped += 1
        else:
            fpath.write_text(content, encoding="utf-8")
            print(f"  [wrote]     {fpath.relative_to(ATHENA_ROOT)}")

        # Insert into review queue (always insert so the UI has fresh test rows)
        item_id = mem.submit_for_review(agent, item_type, title, str(fpath))

        if status == "approved":
            mem.approve_review(item_id, notes)
            print(f"  [approved]  #{item_id} — {title[:60]}")
        elif status == "rejected":
            mem.reject_review(item_id, notes)
            print(f"  [rejected]  #{item_id} — {title[:60]}")
        else:
            print(f"  [pending]   #{item_id} — {title[:60]}")

        created += 1

    stats = mem.get_review_stats()
    print(f"\nDone. {created} items seeded ({skipped} files already existed).")
    print(f"Queue stats — pending: {stats['pending']}  approved: {stats['approved']}  rejected: {stats['rejected']}")


if __name__ == "__main__":
    main()
