---
title: The Email That Kills Your Career: How San Diego Device Companies Hide Communication Failures Before They Become FDA 483s
date: 2026-06-05
status: DRAFT — needs your review before publishing
publication: MedTech Meridian (Substack)
angle: Most regulatory findings aren't about bad processes—they're about engineers and QA professionals who documented their thinking poorly, leaving inspectors to fill in the blanks with worst-case assumptions.
generated_by: Latitude MedTech Content Agent
---

# The Email That Kills Your Career: How Vague Technical Communication Becomes FDA Evidence Against You

In 2022, a mid-stage San Diego cardiac device company was three days into an FDA pre-approval inspection when an investigator pulled a three-line email from a design history file. The company's mechanical engineer had reviewed a supplier's proposed component substitution — a critical seal material swap — and written back: *"Looks good. Acceptable per spec. Go ahead."* The decision was correct. The engineer had mentally run through biocompatibility, dimensional tolerance, and pressure ratings. He knew the part. He'd been working with that supplier for four years. But none of that reasoning lived anywhere in writing. Two years after he hit send, that email became Exhibit A in a 483 observation (an FDA Form 483 is the written list of objectionable conditions an investigator documents during an inspection) about inadequate design controls under 21 CFR §820.30(h). The company's legal and regulatory team spent six weeks reconstructing what should have been a thirty-minute documentation exercise. The engineer wasn't negligent. He was inarticulate — on paper, at the moment that mattered.

---

## Why This Matters to Your Career

QA/RA professionals who can bridge the communication gap between engineering teams and regulatory scrutiny are among the most valuable people in any device company. This isn't soft-skills advice. The ability to translate engineering reasoning into audit-ready records is a hard, billable, hireable skill — and it's chronically undersupplied.

Regulatory Affairs Managers in San Diego earn between $110,000 and $145,000 annually (RAPS Compensation Survey, 2024). The professionals at the top of that band almost universally share one trait: they don't just enforce the quality system — they teach teams to use it. If you're interviewing at Dexcom, Masimo, or any of the 900-plus device companies clustered in the I-5 corridor, expect to be asked how you've handled a CAPA (Corrective and Preventive Action) involving cross-functional communication breakdown. If your answer is "I wrote the procedure," you're in the bottom half of candidates. If your answer is "I trained the engineering team to document their reasoning and then audited that training," you're in the room where offers get made.

---

## The Real Mechanics

The gap isn't about engineers being careless. It's about audience blindness.

When a mechanical engineer writes "acceptable per spec" to a colleague on Slack, the message is complete. Both parties share context — the test data, the conversation from Tuesday's design review, the tribal knowledge about that supplier. The message is a handshake between two people who already agree.

When an FDA investigator reads "acceptable per spec" two years later, they have none of that context. What they have is the document, the regulation, and the mandate to assume the worst if evidence of competence is absent. Under 21 CFR §820.30(b), design and development planning must ensure that design activities are assigned to qualified individuals equipped with adequate resources. "Acceptable per spec" proves nothing about qualification, nothing about the specific specification referenced, and nothing about whether a risk-informed decision was made. The investigator isn't wrong to flag it. The engineer simply wrote for the wrong audience.

Here's the distinction I ask teams to internalize: **a Slack message is a handshake; a quality record is a handshake with a notary present.** The notary doesn't know you. The notary only reads what's on the paper.

The IMDRF's recently updated Annex D (Cause Investigation – Investigation Conclusion) makes this explicit in a way that should accelerate urgency at every San Diego device company. Annex D now requires documented reasoning chains in investigation conclusions — not just the conclusion itself, but the logic that connects evidence to cause determination. Annex E (Clinical Signs and Symptoms or Conditions) echoes this by requiring that clinical documentation demonstrate how symptom patterns were interpreted, not merely catalogued. These updates signal a global regulatory consensus: *showing your work is no longer optional.*

The practical failure modes I see most often, and their regulatory exposure:

| Vague Phrase | What the Engineer Meant | What the Investigator Assumes | Relevant Regulation |
|---|---|---|---|
| "Looks good" | Passed all acceptance criteria after full review | No criteria were applied | 21 CFR §820.80(e) — Acceptance Records |
| "Acceptable per spec" | Spec #MECH-042 Rev C, all parameters in range | Unknown which spec; no evidence of comparison | 21 CFR §820.30(h) — Design Changes |
| "Verified OK" | Performed IQ/OQ verification per protocol V-2024-11 | No verification protocol referenced or executed | 21 CFR §820.75(b) — Process Validation |
| "No impact to design" | Risk assessment updated, no new hazards identified | Risk assessment was skipped | ISO 14971 §10.2 — Post-production surveillance |
| "Per previous approval" | Change falls within approved design envelope | Approval was informal or undocumented | 21 CFR §820.40 — Document Controls |

The fix is not bureaucratic. It's architectural. I train teams to use what I call the **DRI-R model** for any written technical decision: Decision, Rationale, Input referenced, Risk considered. A compliant version of that three-line email looks like this:

*"Component substitution approved. Reviewed against MECH-042 Rev C — dimensional and pressure ratings within spec. Biocompatibility equivalence confirmed per ISO 10993-1 screening (see attached). No new hazard identified per risk management file RM-2021-04. Change documented per ECO-2022-117."*

That's four sentences. It took the engineer four minutes. It would have ended the 483 observation before it started.

QA/RA's role here is not to write these records for engineers — it's to create the training and environmental conditions where engineers write them instinctively. That means embedding the DRI-R habit into design review templates, change order forms, and yes, into the informal communication channels where decisions actually get made first. Annex G (Medical Device Component documentation standards) reinforces this at the component level specifically — the days of a supplier qualification resting on a single approved vendor list entry are closing fast.

---

## What to Do This Week

**Action 1:** Pull five recent technical emails or Slack messages from your team's design history files or change control records. Score each one against the DRI-R model — Decision stated? Rationale explicit? Inputs referenced by document number? Risk considered? Bring the results to your next QA team meeting as a communication audit, not a blame session.

**Action 2:** Download IMDRF Annex D (Cause Investigation – Investigation Conclusion) directly from imdrf.org and read specifically Section 5 on documented reasoning requirements. Map one recent CAPA to its language. If your CAPA investigation conclusions don't satisfy Annex D's reasoning chain requirement, you now have the regulatory hook to update your CAPA procedure — and the credibility to bring engineering leadership into a training session to close the gap.

---

## The Long Game

The regulatory environment is moving toward demonstrated competence rather than asserted compliance. The FDA's Quality Management System Regulation (QMSR), which aligns 21 CFR Part 820 with ISO 13485:2016, will intensify this trend — inspectors will increasingly look for evidence that your team *thinks* rigorously, not just that your SOPs (Standard Operating Procedures) say they should.

For someone at zero years in QA/RA: the engineers around you are not your adversaries. They are your primary product. Teach them to write with regulatory clarity, and you become indispensable. For someone at seven years in: this is the leadership pivot. The QA professionals who will run regulatory strategy at the next generation of SoCal device companies are the ones building training infrastructure right now, not just enforcing procedures. The 483 gets issued to the company. The reputation for fixing the culture before the 483 arrives — that goes on your resume.

---

*Disclaimer: Educational content only. Nothing here is regulatory, legal, or compliance advice. Consult qualified professionals and official FDA guidance documents for compliance decisions specific to your organization.*