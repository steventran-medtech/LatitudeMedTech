---
clause: 4.2
title: Documentation Requirements
generated: 2026-06-05T11:45:00.318713
word_count: 1451
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 4.2: Documentation Requirements

## What This Clause Is About

Every medical device company runs on documents — procedures, records, forms, specifications. Clause 4.2 sets the rules for how your Quality Management System (QMS) documentation must be structured and controlled. Without these rules, you end up with outdated procedures people ignore, missing records that can't prove compliance, and audits that go sideways fast.

---

## What It Requires (The Essentials)

**1. You must have a documented Quality Manual.**
ISO 13485 requires a Quality Manual that describes the scope of your QMS, references your procedures, and explains how your processes interact. Think of it as the map of your entire quality system. If your company makes orthopedic implants but not software, your Quality Manual documents that scope and explains why certain clauses may not apply.

**2. Your QMS needs documented procedures — some are mandatory.**
The standard requires written procedures for specific activities (like document control, record control, and corrective action). Beyond the mandatory ones, your company decides what else needs a documented procedure based on the complexity of your processes and the competency of your people. A three-person startup handles this differently than a 200-person manufacturer.

**3. Records are a separate category — and they need special protection.**
A *document* tells people what to do. A *record* is evidence that they did it. Both need to be controlled, but records have extra requirements: you can't alter them improperly, they must be legible, and you must retain them for defined periods. A Device History Record (DHR) proving a lot of catheters was built to spec is a record. The work instruction explaining how to build it is a document.

**4. Documents must be controlled — the right version, in the right hands, at the right time.**
This means approved before use, reviewed and updated when needed, and protected from accidental use of outdated versions. If a technician on the production floor is working from a procedure that was revised six months ago, that's a Clause 4.2 problem.

**5. You must control documents of external origin.**
This catches people off guard. If you use a customer drawing, a supplier specification, or a recognized standard (like IEC 60601 for electrical safety) as part of your process, those documents need to be identified and controlled too — not just floating around in someone's email inbox.

---

## What This Looks Like in Practice

Imagine a 50-person company in Minnesota that makes powered surgical handpieces. Their QMS looks something like this:

The **Quality Manager** owns the document control procedure (SOP-001) and the Quality Manual. When an engineer wants to revise a work instruction for handpiece assembly, she submits a change request through their document control software (something like Greenlight Guru, MasterControl, or even a well-structured SharePoint). The **Document Control Coordinator** — often a junior QA role — reviews the request for completeness and routes it to the appropriate approvers.

Before the revision goes live, it gets reviewed by Engineering for technical accuracy and by QA for compliance impact. Once approved, the system automatically archives the old version and publishes the new one. The coordinator then notifies the production supervisor, who confirms that floor personnel have been trained on the change before using the updated procedure.

Records from that process — the training acknowledgment forms, the approval signatures, the change history — all get stored and retained per the company's record retention schedule. For a Class II device, that might mean retaining manufacturing records for the expected device lifetime plus two years, or longer depending on regulatory requirements in their markets.

A new QA associate in this company spends their first few weeks learning this system — understanding how documents are numbered, where approved versions live, and why you never, ever print and use a document without checking that it's the current approved version.

---

## Common Mistakes and Audit Findings

**1. Confusing documents with records.**
Early-career professionals frequently mix these up. An auditor asks for your "calibration records" and you hand them the calibration procedure. These are not the same thing. Know the difference cold.

**2. Uncontrolled documents on the production floor.**
Printed copies of SOPs or work instructions sitting in binders with no revision date, no indication they're controlled copies, and no system to pull them when procedures change. Notified bodies find this constantly.

**3. Missing control of external documents.**
A team is using a customer-supplied drawing or a specific ASTM standard in their test method but it's not listed in their controlled document system. When the customer updates their drawing, nobody knows. This creates both a quality risk and a compliance finding.

**4. Quality Manual that doesn't match reality.**
The Quality Manual says the company uses a risk-based approach to supplier qualification and documents all critical processes — but the actual procedures and records don't support that. Auditors read your Quality Manual and then go looking for evidence. If the two don't align, you have a problem.

---

## Key Terms to Know

**Quality Manual** — The top-level document describing your QMS scope, structure, and how your processes connect. Required by ISO 13485.

**Documented Procedure** — A written procedure that describes how to carry out a specific activity. Some are explicitly required by the standard; others are determined by your company's needs.

**Record** — Objective evidence that something happened or a result was achieved. Records can't be revised the way procedures can — they document what actually occurred.

**Document Control** — The system for managing the creation, review, approval, distribution, and retirement of documents to ensure only current, approved versions are in use.

**Quality Management System (QMS)** — The complete set of processes, procedures, and records a company uses to consistently meet quality and regulatory requirements.

**Device History Record (DHR)** — A collection of records proving that a specific device lot or unit was manufactured according to the Device Master Record (specifications and procedures).

**Retention Period** — The minimum length of time a record must be kept. Varies by document type and applicable regulations.

**External Document** — A document created outside your company (customer drawings, supplier specs, industry standards) that you use in your processes and must therefore control.

---

## Check Your Understanding

**1. What is the primary purpose of the Quality Manual?**
*Answer: It describes the scope of the QMS, references key procedures, and explains how processes interact — essentially a map of the quality system.*

**2. What is the difference between a document and a record?**
*Answer: A document tells people what to do (procedure, work instruction, specification). A record is evidence that something was done (test result, training log, inspection form). Records cannot be revised the way procedures can.*

**3. Why does ISO 13485 require control of external documents?**
*Answer: Because if you're using external documents in your processes, outdated or incorrect external documents can cause the same quality and compliance failures as outdated internal ones.*

**4. Scenario: During an audit, an inspector finds a technician using a printed assembly procedure. The header shows Revision B, but the document control system shows Revision C was approved three months ago. Which clause is implicated and what's the core problem?**
*Answer: Clause 4.2, specifically document control. The core problem is that an obsolete document version was in use — meaning either the old copy wasn't removed when the revision went live, or the technician retrieved an uncontrolled copy.*

**5. Scenario: Your company's Quality Manual states that all suppliers are evaluated annually. An auditor asks to see the supplier evaluation records and finds that three critical suppliers haven't been evaluated in 18 months. What's the issue beyond just the supplier management clause?**
*Answer: There's also a Clause 4.2 issue — the Quality Manual doesn't reflect actual practice. Documentation must describe what the system actually does, not an idealized version of it.*

---

## How This Connects to Your Career

Document control is often the first real responsibility handed to an early-career QA professional — and it's where a lot of people either build credibility or lose it quickly. Companies need people who understand not just how to file documents, but *why* the system is structured the way it is. When you understand Clause 4.2, you can catch problems before they become audit findings, train colleagues on why version control matters, and contribute meaningfully to QMS improvement projects. Hiring managers notice candidates who can speak to document hierarchy, controlled distribution, and record retention with confidence — because it signals that you understand the foundation the entire QMS is built on.

---

*This lesson is educational content only and is not regulatory or legal advice. Always refer to the official ISO 13485:2016 standard for actual requirements, and consult qualified regulatory professionals for guidance specific to your company and products.*