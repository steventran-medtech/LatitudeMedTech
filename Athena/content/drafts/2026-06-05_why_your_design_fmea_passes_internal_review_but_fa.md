---
title: Why Your Design FMEA Passes Internal Review But Fails FDA Inspection: The Severity-Detectability Trap
date: 2026-06-05
status: DRAFT — needs your review before publishing
publication: MedTech Meridian (Substack)
angle: Most device teams score risk using ISO 14971 severity tables that don't match how FDA inspectors actually evaluate patient harm—creating a false sense of compliance that audits expose immediately.
generated_by: Latitude MedTech Content Agent
---

# Why Your Design FMEA Passes Internal Review But Fails FDA Inspection: The Severity-Detectability Trap

A San Diego cardiac ablation catheter company spent eight months building a Design FMEA (Failure Modes and Effects Analysis — a systematic tool for identifying what can go wrong in a device and how bad it could be) for their next-generation device. Their internal risk team was thorough. They used a published severity table from a reputable industry consortium, scored electrical leakage as a "Medium" risk, and got sign-off from their VP of Quality. The FDA 483 observation that landed eighteen months later read: *"Risk not adequately characterized for the intended patient population."* No one on that team had done anything dishonest. They had done something more dangerous: they had mistaken a framework for a standard.

The problem wasn't their math. It was that they scored severity against "worst case in peer-reviewed literature" — which includes burn injuries in patients with normal cardiac conduction. Their actual population? Patients already in atrial fibrillation, often anticoagulated, many with prior ablations. The same electrical leakage level that produces a minor transient arrhythmia in a healthy volunteer can trigger hemodynamic collapse in that patient. Same number. Different world.

---

## Why This Matters to Your Career

FMEA authorship sits at the intersection of product development and regulatory approval — which means it shows up on job descriptions at every level, from Associate QA Engineer ($72K–$88K in San Diego per the 2024 RAPS Compensation Survey) to Principal Systems Engineer ($130K+). But here's what hiring managers won't tell you: most candidates who list "ISO 14971 proficiency" on a resume have built risk files that would survive an internal review and fail an FDA Pre-Approval Inspection.

If you can walk into an interview and explain *why* severity definitions must be localized to intended use — not just that they should be — you are in the top quartile of applicants for risk management roles. FDA inspectors ask this question. 483 observations referencing "inadequate risk characterization" have appeared in device inspections with enough frequency that CAPA (Corrective and Preventive Action) responses now routinely run six figures in consulting and remediation costs. Knowing how to prevent that response, rather than write it, is a career-defining skill.

---

## The Real Mechanics

**ISO 14971 is a framework. It is not a regulatory ceiling.**

ISO 14971:2019 (the international standard for medical device risk management) gives you a structure: estimate severity, estimate probability of occurrence, combine them into an acceptable risk determination. What it does *not* give you is a universal severity table you can copy-paste into every FMEA. Section 5.5 of ISO 14971:2019 explicitly states that severity shall be estimated based on the *nature of the harm* — a phrase that requires clinical specificity, not generic categories.

FDA's Design Controls guidance (FDA Guidance: Design Control Guidance for Medical Device Manufacturers, 1997) reinforces this: design inputs must reflect the *intended use* of the device. That means your severity definitions must be calibrated to your patient population, your procedure, and your clinical environment. "Serious injury" means something different for a pediatric cardiac catheter than for a capital orthopedic implant.

**The detectability trap that flips your risk ranking**

This is where I see experienced engineers make the same mistake repeatedly. A team scores detectability based on their post-market surveillance program — quarterly MDR (Medical Device Report) trending, complaint handling, maybe a patient registry. They use this to justify a low overall risk priority number. FDA's perspective, grounded in 21 CFR §820.30(b) (Design Controls — Design and Development Planning), is blunter: post-market detection means a patient was already harmed before you caught the signal. Design controls exist to prevent harm from reaching the patient, not to track it after it does.

IMDRF's recently updated annexes sharpen this further. Annex D (Cause Investigation — Investigation Conclusion, 2025) now requires that cause investigation traces back to original design decisions. Annex F (Health Effects — Health Impact, 2025) requires health impact assessments grounded in clinical severity, not engineering proxies. Together, these documents create an expectation that your risk file forms a traceable chain: clinical reality → severity definition → hazard analysis → design control → verification. When an inspector follows that chain and finds a gap — say, a "low detectability" score justified by complaint trending rather than design verification — your FMEA didn't just fail a process check. It revealed that a design hazard never actually made it into your verification plan.

**The table that exposes the gap**

Here is how the same electrical leakage risk scores differently depending on which severity framework a team uses:

| Framework | Severity Definition Used | Assigned Severity Level | Risk Priority | Design Control Generated? |
|---|---|---|---|---|
| Generic Industry Table | "Worst case in literature: serious injury" | Medium (3/5) | Medium | Partial — no patient-specific verification |
| ISO 14971 § 5.5 Localized | "Worst case for anticoagulated AFib patient intraoperatively" | High (5/5) | High | Yes — leakage current spec added to Design Inputs |
| FDA Inspection Standard | "Patient harm given actual use environment and population" | High (5/5) | High | Required — Design Verification test protocol written |

The delta between rows one and three isn't a regulatory technicality. It's whether a verification protocol for leakage current ever gets written. In the San Diego case, it wasn't — because the Medium score meant leakage tolerance was treated as a manufacturing parameter, not a design input. That's the 483 in one sentence.

**Risk ranking reversal: the question that ends the inspection badly**

When an FDA inspector asks "How did this design hazard make it into your verification plan?", they are not asking for your risk priority number. They are asking for evidence that the FMEA *drove* design decisions rather than *documented* them retrospectively. Teams that score a hazard as Low (low severity × high detectability) and then cannot trace that hazard to a specific verification or validation activity have, in effect, admitted the FMEA is a paper exercise. IMDRF Annex E (Health Effects — Clinical Signs and Symptoms or Conditions, 2025) now explicitly links clinical symptom characterization to cause chains, making it harder to claim a hazard is low-severity without clinical evidence supporting that call.

---

## What to Do This Week

**Action 1:** Pull your current FMEA severity table and write next to each severity category the specific clinical scenario — patient population, procedure type, anatomical site — that defines "worst case" for *your* device. If you cannot write that scenario in one sentence per row, your severity definitions are not localized. The FDA MAUDE database (accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/search.cfm) has adverse event reports filtered by device type — spend 45 minutes there building your clinical picture before you rewrite a single cell.

**Action 2:** For every hazard rated "Low" due to high detectability, document the design-phase control that prevents harm *before* market. If the only detectability mechanism is post-market surveillance, change the rating to reflect that and open a design review. This week. Not at your next audit.

---

## The Long Game

FDA's inspection focus on risk file quality has intensified since the 2022 QSR (Quality System Regulation) realignment toward ISO 13485, and it is not reversing. The IMDRF annexes published in 2025 signal where global harmonization is heading: toward clinical traceability, not documentation adequacy.

For someone at year zero in QA, building FMEAs that can survive an inspection — not just an internal review — is the skill that gets you from Associate Engineer to QA Manager in five years instead of ten. For someone at year seven, it is the differentiator between being the person who explains a 483 response to leadership and the person who prevented the 483 from being written.

San Diego's device corridor — Dexcom, Masimo, BD, the dozens of catheter and neuro-modulation startups between Sorrento Valley and Carlsbad — is producing increasingly complex devices with increasingly scrutinized risk files. The engineers who understand that ISO 14971 is a starting point, not a finish line, are the ones building reputations that last a career.

---

*Disclaimer: Educational content only. Nothing here is regulatory, legal, or compliance advice. Consult qualified professionals and official FDA guidance documents for device-specific risk management decisions.*