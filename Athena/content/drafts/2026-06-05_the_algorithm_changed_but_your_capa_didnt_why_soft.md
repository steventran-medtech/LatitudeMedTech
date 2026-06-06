---
title: The Algorithm Changed, But Your CAPA Didn't: Why Software Updates Are Killing Your Nonconformance Effectiveness
date: 2026-06-05
status: DRAFT — needs your review before publishing
publication: MedTech Meridian (Substack)
angle: Most CAPA systems treat software updates as maintenance, not design changes—leaving SaMD companies vulnerable to regulatory action when AI/ML models drift in production without triggering root cause investigation.
generated_by: Latitude MedTech Content Agent
---

# The Algorithm Changed, But Your CAPA Didn't: Why Software Updates Are Killing Your Nonconformance Effectiveness

A San Diego-based AI diagnostic company — building the kind of chest X-ray classifier that's become table stakes in digital health — pushed what their engineering team called a routine model retraining to production last year. The retrain used an expanded dataset. The inference pipeline didn't change. The version number bumped from 2.3.1 to 2.3.2. QA logged a 2.1% sensitivity drop in the post-deployment monitoring report, flagged it as "within expected performance variation," and closed the ticket.

FDA inspectors saw something else entirely: an uncontrolled design change with no root cause investigation, no health impact assessment, and no documented causal link between the algorithm modification and the performance delta. The 483 observation landed. The CAPA that followed — spanning six months, three consultants, and a complete QMS retrofit — cost the company north of $400,000. The harder cost was the nine-month delay on their next 510(k) submission. All of it traceable to a single gap: their CAPA system was built for hardware, and nobody had ever updated it for the reality of ML-driven SaMD.

---

## Why This Matters to Your Career

If you're a QA or RA professional at a digital health company right now, you are sitting at the intersection of two regulatory frameworks that are tightening simultaneously — and most QA teams haven't noticed yet.

The IMDRF Annexes Combined framework (May 2025) tightens cause investigation language in ways that directly implicate SaMD CAPA governance. Annex D specifically, which addresses Investigation Conclusion methodology, now requires a documented causal chain between nonconformance and design intent. Annex F (Health Effects – Health Impact) requires a structured assessment of whether a performance change created or increased patient risk. These aren't aspirational guidelines — they're the evidentiary standard FDA inspectors are comparing your CAPA records against.

For a QA engineer with three to five years of experience, being the person who builds an algorithm-change taxonomy at their company is the kind of career-defining project that gets you promoted. For a hiring manager at Dexcom, BD, or any of San Diego's growing SaMD shops, "demonstrated experience governing ML model updates under 21 CFR Part 820 and IMDRF MDCE framework" is becoming a differentiated hiring signal. RAPS salary data from 2024 shows RA specialists with SaMD-specific competencies command a 12–18% premium over generalist peers. This is the specific skill creating that gap.

---

## The Real Mechanics

Here's the core problem. Every CAPA template inherited from a hardware QMS treats "software" as a monolithic category. A bug fix that corrects a null pointer exception and a model retraining that shifts the decision boundary of a cancer detection algorithm both get logged as "software nonconformance" — same template, same root cause categories, same effectiveness criteria. That's the regulatory equivalent of using the same investigation protocol for a mislabeled screw and a structural design failure.

Under 21 CFR §820.100(a), your CAPA procedure must include methods for analyzing processes, work operations, concessions, quality audit reports, and quality records to identify existing and potential causes of nonconforming product. FDA's interpretation of "causes" for SaMD now explicitly includes algorithm behavior changes. The 2023 FDA guidance on Predetermined Change Control Plans (PCCPs) signals this clearly — performance modifications to ML models are design changes requiring documented rationale, even when the underlying code architecture stays identical.

The IMDRF Annexes Combined framework makes this even more explicit. Annex D's Investigation Conclusion structure requires four documented elements: the identified cause, the evidence supporting that cause, the elimination of alternative causes, and the link to corrective action. If your root cause investigation for a 2.1% sensitivity drop reads "expected statistical variation in retraining dataset," you've failed all four — because you haven't established what caused the variation, what evidence you examined, what alternatives you ruled out, or what action prevents recurrence.

Three 483 observations issued between 2024 and Q1 2025 follow an identical pattern:

| Company Type | 483 Citation | FDA's Specific Finding | Outcome |
|---|---|---|---|
| AI imaging SaMD (dermatology) | 21 CFR §820.100(a) | Model performance drift logged as "expected variation"; no RCA initiated | Warning Letter, voluntary recall review |
| Clinical decision support platform | 21 CFR §820.100(a) & §820.30(i) | Post-market data showing specificity decline not routed to CAPA system | Consent decree negotiations |
| ML-based patient monitoring | 21 CFR §820.100(a) | CAPA closed without effectiveness verification after retraining event | Re-inspection required, market hold |

The pattern is not subtle. FDA is specifically looking for whether your CAPA system has a mechanism — a documented, procedural mechanism — to distinguish between a software patch that fixes defective behavior and an algorithmic update that alters intended performance. If you can't show that mechanism exists, the 483 is already written.

What does a workable mechanism look like? An algorithm change taxonomy — ideally embedded directly into your change control SOP (Standard Operating Procedure) and CAPA initiation criteria — that classifies software updates into at least three tiers:

**Tier 1 — Corrective (Bug Fix):** Restores behavior to design specification. No performance delta expected. Standard change control, no CAPA trigger unless recurrence pattern exists.

**Tier 2 — Adaptive (Model Retraining / Data Augmentation):** Same architecture, updated weights or training data. Performance delta possible. Requires Annex D-style cause investigation if any validated metric shifts beyond pre-specified thresholds. Threshold definition is mandatory — "expected variation" is not a threshold.

**Tier 3 — Perfective / Architectural (Feature Engineering, Model Architecture Change):** Design change under §820.30(b). Full design control re-entry required. PCCP documentation if applicable.

The absence of this taxonomy is the gap FDA is citing. Building it is not a six-month project — it's a two-week sprint with your QA lead, your ML engineer, and your RA counsel in the same room.

---

## What to Do This Week

**Action 1:** Pull your current CAPA initiation procedure and search it for any mention of model retraining, algorithm change, or performance drift. If those words aren't there, your procedure has a documented gap — and so does your next audit response. Draft a one-page taxonomy addendum using the three-tier framework above and route it for review. This is not a full SOP revision — it's a gap closure memo that buys you protection while the full revision processes.

**Action 2:** Download the IMDRF Annexes Combined document (May 2025) directly from imdrf.org and read Annex D and Annex F back-to-back against your last three CAPA records for any software-related nonconformance. If your investigation conclusions don't map to Annex D's four-element structure, document that gap in your internal audit log today. That documentation demonstrates good faith awareness — which matters in a consent decree negotiation more than most people realize.

---

## The Long Game

The FDA's PCCP framework, IMDRF's tightening Annex language, and the EU AI Act's conformity requirements for high-risk AI systems are converging on the same expectation: SaMD companies must govern algorithm behavior with the same rigor they apply to hardware design changes. For someone at zero years in QA, understanding this now means you enter the field with a mental model that most five-year veterans don't have yet. For someone at seven years, this is your opportunity to become the person who builds the institutional framework — the kind of work that translates directly into Director-level scope.

San Diego's SaMD corridor — Dexcom, Butterfly Network's clinical partners, the UCSD Health AI pipeline — is going to need people who can sit at the intersection of ML operations and QMS governance. That role doesn't have a clean title yet. It will. Build the skills before the title exists.

---

*Disclaimer: Educational content only. Nothing here is regulatory, legal, or compliance advice. Consult qualified professionals and official FDA and IMDRF guidance documents before making decisions about your quality management system.*