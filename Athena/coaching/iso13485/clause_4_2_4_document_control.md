---
clause: 4.2.4
title: Document Control
generated: 2026-06-03T20:34:28.375476
word_count: 1411
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 4.2.4: Document Control

# ISO 13485:2016 Clause 4.2.4: Document Control

*Educational content only. Always refer to the actual ISO 13485:2016 standard for official requirements.*

---

## What This Clause Is About

Document control solves a simple but critical problem: making sure everyone in your company is working from the right version of the right document. In medical devices, using an outdated procedure or the wrong form can lead to product defects, patient harm, or a failed audit. This clause sets up the rules for how documents get approved, updated, distributed, and retired.

---

## What It Requires (The Essentials)

**1. Documents must be approved before use.**
Before anyone follows a procedure or uses a form, someone with the authority to do so must formally approve it. You can't just write a work instruction and start using it — there has to be a documented sign-off.

**2. Documents must be reviewed and updated when necessary.**
When a process changes, the document describing that process has to change too. The clause requires a system for reviewing documents and re-approving them after changes are made.

**3. The current version must be available where it's needed.**
If your production team runs a sterilization process, the current sterilization procedure needs to be accessible on the production floor — not sitting in a binder in the QA manager's office. Availability at the point of use is a real requirement.

**4. Obsolete documents must be controlled.**
Old versions of documents can cause serious problems if someone accidentally follows them. The clause requires that you either remove obsolete documents from circulation or clearly mark them so no one mistakes them for current versions.

**5. External documents must be identified and controlled.**
This catches a lot of people off guard. Standards, customer specifications, supplier requirements — any external document your QMS relies on — must be identified and controlled, just like your internal documents.

---

## What This Looks Like in Practice

Picture a 45-person Class II device company making infusion pumps. Their QMS lives in a cloud-based document management system called Veeva Vault (a common choice at this size).

When a **Process Engineer** needs to update the assembly work instruction for the pump housing, here's what actually happens:

1. She initiates a **change request** in Vault, which automatically notifies the document owner.
2. She drafts the revision, explaining in the change justification field *why* the change is needed — maybe a supplier switched a component material.
3. The draft routes electronically for review to the **Manufacturing Supervisor** and **Quality Engineer** assigned to that product line.
4. After their comments are resolved, it routes to the **QA Manager** for final approval. She reviews it, confirms it's technically accurate and compliant, and approves it with an electronic signature.
5. Vault automatically increments the document to Rev B, timestamps the approval, archives Rev A as "obsolete," and notifies the production floor that a new version is available.
6. The Manufacturing Supervisor confirms that printed copies of Rev A (there were two laminated copies on the line) are pulled and replaced — that physical step gets documented in the training record.

The whole process takes about a week for a routine change. Nothing goes live without that approval chain completing.

If there's a supplier specification that your company references — say, a biocompatibility test report format from your contract lab — that external document gets logged in a **master document list** with its version number. When the lab updates their format, someone owns the task of catching that and updating the log.

---

## Common Mistakes and Audit Findings

**1. Uncontrolled documents in use.**
Auditors walk the production floor and find a laminated work instruction with no revision number, no approval signature, and no indication of when it was created. The team swears it's current — but there's no way to verify that. This is one of the most common findings in manufacturing audits.

**2. Obsolete documents not removed.**
Rev C of a cleaning procedure is approved and live, but Rev B is still sitting in a shared drive folder that technicians also have access to. If someone follows Rev B, you have a nonconformance. If they do it during an audit, you have a finding.

**3. External documents not identified in the QMS.**
A Regulatory Affairs Specialist references IEC 60601-1 (a major electrical safety standard) in multiple design documents, but it's never been added to the controlled external documents list. Auditors ask for evidence that the company tracks external standards — and there isn't any.

**4. No evidence of training after document revisions.**
A new procedure is approved and goes live. But there's no record that the people who actually perform that procedure were trained on the new version. Approval doesn't equal implementation. Training records need to close that loop.

---

## Key Terms to Know

**Controlled document:** Any document that falls under your document control system — meaning it has an approval process, version history, and defined distribution.

**Revision level (or version number):** A label (Rev A, Rev B, Rev 1.0, etc.) that identifies which iteration of a document you're looking at. Critical for knowing whether you have the current version.

**Obsolete document:** A previous version of a document that has been superseded. It must either be destroyed or clearly marked so it can't be accidentally used.

**Point of use:** The physical or digital location where a task is performed. Documents need to be available *there*, not just somewhere in the building.

**Master document list (or document register):** A log of all controlled documents, their current revision levels, and their status. This is often how an auditor starts — asking to see your master list.

**Document owner:** The person responsible for keeping a specific document accurate and current. This isn't the same as the person who approves it.

**Electronic signature:** A legally and technically defined method of signing a document digitally. In regulated industries, this has specific requirements (audit trails, identity verification) — it's not just typing your name.

**Change control:** The formal process for making, reviewing, approving, and implementing changes to controlled documents (and other QMS elements).

---

## Check Your Understanding

**1. Why does ISO 13485 require documents to be approved before use?**
*Answer:* To ensure that only technically accurate and officially sanctioned documents are being followed. Unapproved documents haven't been reviewed for accuracy, compliance, or safety implications.

**2. A technician finds two versions of a cleaning procedure in the work area — Rev C and Rev D. Rev D is the approved current version. What should happen?**
*Answer:* Rev C should be immediately removed from the work area and either destroyed or marked as obsolete per your document control procedure. This situation should also be investigated as a potential nonconformance.

**3. What's the difference between a document owner and the person who approves a document?**
*Answer:* The document owner is responsible for maintaining the document's accuracy over time — initiating updates when changes are needed. The approver has the authority to formally authorize the document for use. These can be the same person, but often aren't.

**4. Your company references ASTM F2132 (a material standard) in a design specification. Does that standard need to be in your document control system?**
*Answer:* Yes. External documents that your QMS relies on must be identified and controlled. That means logging the standard, its version, and having a process to check when it's updated.

**5. A new work instruction is approved on Monday. Production starts using it on Tuesday with no training records created. Is this acceptable under ISO 13485?**
*Answer:* No. Approval means the document is authorized — it doesn't mean personnel are qualified to use it. Training (and records of that training) are required before personnel perform the task.

---

## How This Connects to Your Career

Document control is the infrastructure of a QMS — almost every other clause depends on it working correctly. Early-career professionals who understand it deeply become the people their teams trust with document change requests, audit prep, and onboarding new employees. When you walk into an audit and you can pull your master document list, show clean revision histories, and demonstrate a controlled obsolete document archive, you look competent and prepared. Employers notice that. More practically: QA coordinators and specialists who can manage a document control system — especially electronic systems like Veeva, MasterControl, or Greenlight Guru — are consistently in demand. This clause isn't glamorous, but getting it right makes everything else in quality work better.