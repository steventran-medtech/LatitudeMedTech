---
clause: 7.6
title: Control of Monitoring Equipment
generated: 2026-06-03T20:47:03.385198
word_count: 1391
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 7.6: Control of Monitoring Equipment

# ISO 13485:2016 Clause 7.6: Control of Monitoring and Measuring Equipment

*Educational content only. Always refer to the actual ISO 13485:2016 standard for official requirements.*

---

## What This Clause Is About

When you use a scale, a caliper, a pressure gauge, or a torque wrench to verify that a device meets its specifications, you're trusting that tool to give you accurate results. Clause 7.6 exists to make sure that trust is earned — that measuring equipment is calibrated, maintained, and fit for purpose before you rely on it to make quality decisions. Without this discipline, you could be releasing products based on measurements that are quietly, consistently wrong.

---

## What It Requires (The Essentials)

**1. Identify what needs to be calibrated.**
Not every tool in a facility requires formal calibration — only equipment used to monitor or verify conformance to requirements. A ruler used for rough layout work isn't the same as a micrometer used to verify a critical dimension on a catheter component.

**2. Calibrate against traceable standards.**
Your equipment must be calibrated or verified at defined intervals against measurement standards traceable to national or international standards (like NIST in the United States). If no such standard exists, you must document the basis you used for calibration.

**3. Protect calibration status.**
Equipment must be identified with its calibration status — usually a calibration sticker or label showing the last calibration date and when it's due next. Equipment that's out of calibration must be clearly identified and pulled from use.

**4. Record everything.**
You must maintain records of calibration results. This isn't optional, and "we did calibrate it" without a record is the same as not calibrating it during an audit.

**5. Assess impact when equipment is found out of tolerance.**
If you discover that equipment was out of calibration, you must evaluate whether previous measurement results were valid and what that means for product that was already released. This step is where companies often get into trouble.

---

## What This Looks Like in Practice

Imagine a 60-person Class II device company that makes surgical stapling instruments. Their QA team manages about 80 pieces of measuring equipment — calipers, torque testers, pull-force gauges, and environmental monitoring sensors in the cleanroom.

The **Quality Engineer** owns the **Calibration Master List** (sometimes called the Equipment Register), a spreadsheet or ERP record that tracks every piece of controlled equipment: asset ID, equipment type, location, calibration frequency, last calibration date, next due date, and the approved vendor or internal procedure used.

Every piece of equipment gets a **calibration label** applied after each calibration event. The label shows the asset ID, calibration date, due date, and — if applicable — any use restrictions (for example, "calibrated for use between 0–100 N only").

Calibration is either performed internally (using a validated procedure, with a traceable reference standard that itself gets sent out annually to an accredited lab) or outsourced to an **accredited calibration laboratory** (ISO/IEC 17025 accredited). The company keeps the certificates from those external labs as their objective evidence.

Thirty days before a calibration is due, the QA Coordinator pulls a **Due-for-Calibration Report** from the ERP system and contacts the equipment owner to schedule service. Equipment that misses its calibration window gets tagged **"OUT OF CALIBRATION — DO NOT USE"** and physically removed from the workstation.

When a torque tester came back from calibration 8% out of tolerance last year, the Quality Engineer initiated a **calibration deviation investigation**. They reviewed the batch records for every lot tested on that instrument over the previous six months, compared the out-of-tolerance drift against the product's acceptance criteria, and documented that the drift was within the product's engineering tolerance — meaning product integrity wasn't compromised. That investigation record became part of the product's Device History Record.

---

## Common Mistakes and Audit Findings

**1. The calibration master list isn't current.**
Equipment gets added to production lines or borrowed between departments without being logged. Auditors walk the floor, find a caliper in use, ask for its calibration record, and it doesn't exist. This is one of the most common findings in ISO 13485 audits.

**2. No traceability documented on calibration certificates.**
Companies use a vendor for calibration but never verify or document that the vendor is accredited or that their reference standards are traceable. "We've used them for years" is not objective evidence.

**3. Skipping the out-of-tolerance impact assessment.**
When equipment fails calibration, teams sometimes just send it for repair and recalibration without ever asking: "What did we measure with this while it was drifting?" That failure to assess impact is a significant nonconformance — and in some cases, a potential recall trigger.

**4. Calibration labels that don't match records.**
The sticker on the equipment says it's due in March. The calibration record says it was calibrated in October of a different year. These discrepancies create immediate audit flags and suggest records aren't being maintained carefully.

---

## Key Terms to Know

**Calibration** — Comparing a measurement instrument against a known reference standard to determine its accuracy and, if needed, adjusting it.

**Traceability** — The ability to link your calibration results back through an unbroken chain of comparisons to a national or international measurement standard (like NIST).

**ISO/IEC 17025** — The international standard for calibration and testing laboratories. A certificate from an accredited lab under this standard is strong objective evidence of traceability.

**Calibration interval** — How frequently a piece of equipment must be calibrated. Determined by risk, manufacturer recommendation, usage frequency, and historical performance.

**Out-of-tolerance** — When a calibration check reveals that equipment is reading outside its acceptable accuracy range. Triggers an impact assessment.

**Calibration Master List (Equipment Register)** — The controlled document that inventories all equipment subject to calibration requirements.

**Reference standard** — A measurement artifact or instrument of known accuracy used to calibrate other equipment. Must itself be traceable.

---

## Check Your Understanding

**1. Why does calibration equipment need to be traceable to national or international standards?**
*Answer: Traceability ensures that your measurements are meaningful and comparable to measurements made anywhere else. Without it, "5.0 mm" measured in your facility might not mean the same thing as "5.0 mm" measured by your customer or a regulatory body.*

**2. A caliper used only for rough in-process layout checks — does it need to be on the calibration master list?**
*Answer: Not necessarily. Equipment used only for monitoring or measuring that doesn't affect conformance decisions doesn't require formal calibration control. However, you should document the rationale for excluding it, and the boundary between "rough check" and "conformance decision" must be clearly defined.*

**3. Scenario: You receive a calibration certificate and notice there's no mention of traceability to NIST or any national standard. What should you do?**
*Answer: Do not accept the certificate as valid evidence. Contact the calibration vendor and request documentation of their traceability chain. If they can't provide it, find an accredited vendor.*

**4. What are the two most critical records to maintain for each piece of calibrated equipment?**
*Answer: (1) Calibration results records (showing as-found and as-left condition, reference standards used, and pass/fail determination) and (2) the calibration master list entry showing current calibration status.*

**5. Scenario: A force gauge used for final product verification has just returned from calibration and was found 12% out of tolerance. It was in service for the past four months. What must happen next?**
*Answer: An out-of-tolerance investigation must be initiated. The team must review all product tested with that gauge over the four-month period, compare the degree of drift against product acceptance limits, and document whether the drift affected the validity of any conformance decisions. If product integrity is in question, that may escalate to a nonconformance, a CAPA, or a customer notification.*

---

## How This Connects to Your Career

Calibration management looks administrative on the surface, but QA professionals who understand it deeply are genuinely valuable. When an auditor walks the production floor during a surveillance audit, calibration is one of the first places they look — and findings here can derail an otherwise clean audit. If you're the person who built a clean, current calibration program, identified gaps before the auditor did, or handled an out-of-tolerance investigation thoroughly, you demonstrate exactly the kind of systematic thinking that QA leadership looks for when deciding who to develop and promote. More practically, calibration connects directly to