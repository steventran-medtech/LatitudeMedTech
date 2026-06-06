---
clause: 14971.9
title: Risk Management Review
standard: ISO 14971:2019
generated: 2026-06-05T17:18:42.412333
word_count: 1631
status: DRAFT — review before sharing with clients
---

# ISO 14971:2019 — Clause 9: Risk Management Review

## What This Clause Is About

By the time a device reaches the end of its design and development cycle, your risk management file contains hundreds of individual decisions made over months or years. Clause 9 exists to answer one critical question: *Taken together, does everything we know right now support the conclusion that this device's benefits outweigh its residual risks?* It's a mandatory synthesis step — a formal checkpoint where someone with the authority and knowledge to make that call actually makes it, in writing, before the device ships.

---

## What It Requires (The Essentials)

**1. Review the entire risk management file.** Before you can conclude anything, you need to verify the file is complete. That means every hazard has been identified, every risk control has been implemented and verified, and residual risks have been evaluated against your acceptance criteria.

**2. Confirm that overall residual risk is acceptable.** Individual risks can each pass your criteria and still add up to a device that a reasonable person would consider unacceptable. Clause 9 explicitly requires you to assess the *combination* of all residual risks — not just each one in isolation.

**3. Conduct a benefit-risk analysis when residual risk is otherwise unacceptable.** If your residual risks exceed your acceptance criteria, you must formally weigh them against the device's intended benefits. This isn't a loophole — it's an honest acknowledgment that some devices (like chemotherapy infusion pumps) carry serious risks that are justified by serious clinical benefit.

**4. Confirm that risk controls have not introduced new risks.** Controls solve problems and create new ones. A software interlock that prevents accidental activation might also delay a time-critical treatment. This review checks that those secondary risks were captured and addressed.

**5. Ensure the review is conducted by appropriate personnel.** ISO 14971:2019 doesn't require a specific role, but the reviewer must have the competence to evaluate the full file — which in practice usually means a cross-functional sign-off, not a solo RA analyst.

---

## Case Study 1 — Real World

**Device category:** Infusion pump software (SaMD component)

In 2010 and into the following years, the FDA issued multiple warning letters and initiated Class I recalls involving Hospira's PCA (patient-controlled analgesia) infusion pumps, specifically related to software and alarm deficiencies that contributed to medication overdose events documented in MAUDE. The core failure wasn't a single design flaw — it was that post-market data showing real-world harm was not being systematically fed back into a risk management review that reassessed overall residual risk.

**What Clause 9 element was deficient:** The benefit-risk conclusion reached at design transfer was never formally revisited as post-market surveillance data accumulated. Under ISO 14971:2019, Clause 9 is not a one-time event at the end of development — it must be repeated whenever new information (complaints, adverse events, literature) suggests that the original risk picture has changed. The risk management file showed acceptable residual risk at launch. It did not reflect what the device was actually doing in hospitals.

**What compliant practice looks like:** A compliant organization links its post-market surveillance process (Clause 10) directly to a trigger for Clause 9 re-review. Specifically: when a pre-defined threshold of adverse event type or frequency is reached, a formal risk management review is scheduled, the benefit-risk analysis is updated, and a documented conclusion is reached by authorized reviewers — not just logged in a complaint database.

---

## Case Study 2 — Hypothetical

**Company:** NovaScan Medical, a 22-person startup developing a wearable continuous glucose monitor (CGM) for Type 2 diabetes management (non-adjunctive use).

NovaScan has completed design verification and is six weeks from design transfer. The risk management file looks solid: 47 identified hazard situations, risk controls in place, individual residual risks all within acceptance criteria. The RA manager schedules the Clause 9 review, and a gap becomes visible immediately.

**The hazard:** Sensor drift causing a false "normal" glucose reading when the patient is actually hypoglycemic. Individually, this residual risk was evaluated and accepted because the probability was rated low based on bench testing.

**The problem the team finds:** When they assess *overall residual risk*, they realize three separate residual risks all share the same harm pathway — hypoglycemia going undetected — even though they were documented under different hazard categories (sensor drift, Bluetooth transmission failure, display algorithm rounding error). Individually, each was acceptable. Cumulatively, the probability of *at least one of these* causing a missed hypoglycemia event is materially higher than any single estimate.

**The analysis step:** The team needs to either aggregate these risks formally (some organizations use a fault tree or risk contribution analysis) or strengthen controls on the shared harm pathway — for example, a mandatory low-glucose alert confirmation from a secondary source.

**The mistake the team makes:** They add a note in the risk file saying "combined pathway reviewed — acceptable" without actually documenting the aggregated probability estimate or the rationale. An auditor will find that note unconvincing. The Clause 9 review conclusion must be traceable: show the inputs, show the logic, show the authorization signature. A sentence is not a benefit-risk analysis.

---

## Common Mistakes and Audit Findings

**1. Treating Clause 9 as a one-time signature page.** Notified bodies regularly observe risk management files where the review section is a single sign-off dated at design transfer with no evidence of re-review after post-market data was collected. Clause 9 requires re-review when new information warrants it.

**2. No documented overall residual risk conclusion.** FDA 483 observations frequently cite risk files that evaluate individual risks thoroughly but contain no explicit statement that *overall* residual risk has been evaluated and found acceptable. The conclusion must be stated — not implied.

**3. Benefit-risk analysis that's purely qualitative and undocumented.** When residual risk exceeds acceptance criteria and a benefit-risk argument is invoked, reviewers sometimes write "clinical benefit outweighs risk" with no supporting evidence. A defensible analysis references clinical data, published literature, or equivalent device comparison.

**4. Risk controls not verified before the Clause 9 review.** The review is supposed to confirm that implemented controls actually work. Audit findings frequently surface cases where a control was listed as "implemented" but verification testing was still outstanding at the time of sign-off.

---

## Key Terms to Know

- **Risk Management File:** The complete set of records produced by the risk management process. Not a single document — a linked collection of plans, analyses, control records, and reviews.
- **Residual Risk:** The risk remaining after risk controls have been applied. Example: a needlestick guard on a lancet device reduces injury risk, but some residual risk of improper disposal still remains.
- **Overall Residual Risk:** The aggregate risk picture across *all* residual risks for a device. Example: a surgical robot may have ten individually acceptable residual risks that together affect the same harm pathway.
- **Benefit-Risk Analysis:** A formal comparison of a device's clinical or health benefits against its residual risks. Example: the risk of internal bleeding from a cardiac stent is weighed against the benefit of preventing a fatal MI.
- **Risk Acceptance Criteria:** The pre-defined thresholds your organization established in the risk management plan for what is and isn't acceptable. Example: probability × severity matrix with a red/yellow/green decision boundary.
- **Authorized Reviewer:** A person with documented competence and organizational authority to sign the Clause 9 conclusion. Example: a Chief Medical Officer co-signing with the VP of Quality for a Class III implant.

---

## Check Your Understanding

**1. What is the difference between individual residual risk acceptability and overall residual risk acceptability?**
Individual residual risk evaluates each hazardous situation in isolation. Overall residual risk asks whether the *sum* of all residual risks — especially those sharing a common harm pathway — remains acceptable. A device can pass the first test and still fail the second.

**2. When does a benefit-risk analysis become required under Clause 9?**
When overall residual risk, after all controls, still exceeds the manufacturer's acceptance criteria. It is the documented basis for proceeding despite elevated risk, and must be supported by evidence of clinical benefit — not just a statement.

**3. *(Scenario — Case Study 2):* NovaScan's team writes "combined pathway reviewed — acceptable" in the risk file. Why isn't this sufficient?**
It provides no traceable logic. A reviewer cannot determine what data were examined, what aggregated probability was estimated, or who made the determination. Clause 9 requires a documented conclusion with substantiated rationale, not an assertion.

**4. How often must a Clause 9 review be conducted?**
At minimum before design transfer. Additionally, whenever post-market surveillance, adverse events, or new scientific information suggests the original risk-benefit conclusion may no longer be valid.

**5. *(Scenario — Case Study 1):* What system would have prevented the infusion pump compliance failure?**
A formal linkage between post-market surveillance data (complaint rates, MAUDE trending) and a defined threshold that triggers a mandatory Clause 9 re-review. The trigger, the review process, and the re-authorization requirement must all be documented in the risk management plan.

---

## How This Connects to Your Career

Clause 9 is the clause where risk management stops being paperwork and becomes a professional judgment you put your name on. Auditors and regulators can tell immediately whether a Clause 9 review was a genuine synthesis of the risk picture or a formality to close out a design file. Early in your career, being the person who can actually *read* a complete risk management file, identify gaps in the overall residual risk picture, and articulate a defensible benefit-risk rationale — in writing, in plain language — makes you genuinely valuable. It also keeps patients safer, which is the whole point.

---

*This lesson is educational content produced by Latitude MedTech LLC. It is not regulatory advice. Always consult the ISO 14971:2019 standard directly and work with qualified regulatory professionals for your specific device and market.*