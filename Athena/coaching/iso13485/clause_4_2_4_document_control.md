---
clause: 4.2.4
title: Document Control
generated: 2026-06-05T12:10:14.833627
word_count: 1411
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 4.2.4: Document Control

## What This Clause Is About

Every medical device company runs on documents — procedures, work instructions, forms, specifications. Without a system to control those documents, people end up working from outdated versions, making decisions based on wrong information, and creating serious safety risks. Clause 4.2.4 establishes the rules for how documents get approved, updated, distributed, and retired so that everyone is always working from the correct, current version.

---

## What It Requires (The Essentials)

**1. Documents must be approved before use.**
Before a procedure or work instruction goes live, someone with the appropriate authority has to review and sign off on it. You can't just write a cleaning procedure and start following it — it has to go through a defined approval process first.

**2. Documents must be reviewed and updated when necessary.**
When a process changes, the document describing that process has to change too. The standard requires that you have a process for reviewing documents, making revisions, and getting those revisions approved — just like the original.

**3. The current version must be available at point of use.**
If a technician on the production floor needs to follow a work instruction, that work instruction needs to be accessible where the work actually happens. Keeping it locked in a manager's office doesn't count.

**4. Obsolete documents must be removed — or clearly marked.**
Old versions of documents cause serious problems. Your system needs to ensure that when a document gets updated, the previous version is either pulled from circulation or clearly labeled as obsolete so nobody accidentally uses it.

**5. External documents must be identified and controlled.**
This one surprises a lot of new professionals. Standards you reference (like a test method from ASTM or IEC), customer drawings, and regulatory guidance documents are all considered external documents. You need to track them and make sure you're using the current version.

---

## What This Looks Like in Practice

Imagine a 60-person Class II device company that makes surgical suction devices. They use an electronic document management system — call it their eQMS — to control all their documents.

When a **Quality Engineer** needs to update a cleaning validation procedure because the company switched chemical suppliers, here's what actually happens:

1. She initiates a **change request** in the eQMS, describing what's changing and why.
2. The system creates a new draft version of the document and locks the current version so nobody else can edit it simultaneously.
3. She makes the revisions, then routes the document for review. The **Manufacturing Supervisor** and **Regulatory Affairs Manager** are listed as required approvers for this document type.
4. Both reviewers get an email notification, log in, review the changes, and electronically sign their approval.
5. The eQMS automatically increments the document to Revision B, timestamps the approval, archives Revision A as obsolete, and pushes the new version to the controlled document library accessible on the production floor tablets.
6. If this were a paper system, someone would physically collect the old Revision A copies, stamp them "OBSOLETE," and file them separately — while distributing printed and stamped "CONTROLLED COPY" versions of Revision B.

The **Document Control Specialist** (sometimes this is a dedicated role, sometimes it rolls up to a QA Coordinator) owns the overall system — maintaining the document master list, managing access permissions, and running periodic audits to make sure no uncontrolled copies are floating around.

---

## Common Mistakes and Audit Findings

**1. Using documents that haven't been formally approved.**
This happens constantly in small companies under time pressure. Someone writes a new work instruction, everyone starts following it, and six months later during an audit it comes out that it was never signed off. Auditors call this an "unapproved document in use" — it's a straightforward nonconformance and easy to avoid.

**2. Obsolete documents still accessible at the point of use.**
A notified body auditor walks the production floor and finds a binder with a work instruction from three revisions ago sitting next to the assembly line. The current version is in the eQMS, but nobody updated the physical binder. This is one of the most common findings across all company sizes.

**3. No control over external documents.**
Companies track their own procedures carefully but forget about the external standards they reference. An audit finding might read: "The company references ASTM F2132 in their test protocol but cannot demonstrate they have verified they are using the current version of the standard." Start a simple log of every external document you reference, with the version and the date you verified it was current.

**4. Document master list is incomplete or out of date.**
Your document master list (sometimes called a document register) is supposed to be a complete inventory of all controlled documents. When it's missing documents, shows wrong revision levels, or hasn't been updated in months, it signals to auditors that your document control system isn't actually being maintained.

---

## Key Terms to Know

**Controlled Document** — A document that is managed under your document control system, meaning it has a defined approval process, revision history, and distribution control.

**Revision Level** — A label (like Rev A, Rev B, or version 1.0, 1.1) that identifies which version of a document you're looking at.

**Document Master List** — A complete index of all controlled documents in your QMS, showing the current revision level and status of each one.

**Obsolete Document** — A previous version of a document that has been superseded by a newer revision. Obsolete documents must be removed from use or clearly identified.

**Point of Use** — The physical or digital location where work is actually performed. Documents must be available here, not just somewhere in the building.

**External Document** — Any document originating outside your company that you reference in your QMS — standards, regulations, supplier specifications, customer drawings.

**Electronic Document Management System (eQMS)** — Software used to create, review, approve, store, and control documents electronically. Common examples include Veeva Vault, MasterControl, and Greenlight Guru.

---

## Check Your Understanding

**1. What is the purpose of a document master list?**
To maintain a complete inventory of all controlled documents, including their current revision levels and status, so you can verify the right version is in use at any time.

**2. Why do external documents need to be controlled?**
Because your procedures may reference specific versions of external standards or specifications. If that external document changes and you don't track it, you could be testing or designing to outdated requirements without realizing it.

**3. Scenario: A production technician shows you a laminated work instruction at their workstation. You look it up in the eQMS and discover it's two revisions old. What's the problem, and what clause does it relate to?**
The point of use has an obsolete document. This is a direct violation of Clause 4.2.4, which requires that obsolete documents be removed from use or clearly identified. The current version should be accessible where the work is performed.

**4. True or False: If a manager verbally approves a document change, that satisfies the approval requirement under 4.2.4.**
False. Approval must be documented. Verbal approvals leave no evidence and cannot be verified during an audit.

**5. Scenario: Your company just adopted a new biocompatibility test method from ISO 10993. Where should this document show up in your QMS?**
It should be added to your external documents log (part of your document master list), with the specific version identified and a note on when you verified it was current. It should be accessible to anyone who references it in your testing procedures.

---

## How This Connects to Your Career

Document control is one of the first things you'll actually touch in a QA role — initiating change requests, drafting SOPs, routing documents for approval, managing the master list. Companies that struggle with audits often struggle because their document control fundamentals are weak, and companies that hire QA professionals want people who can build and maintain a clean, audit-ready system. If you understand not just the mechanics but the *why* behind document control — preventing errors, protecting patients, creating a reliable audit trail — you'll be the person who helps the team avoid those embarrassing audit findings instead of scrambling to explain them.

---

*This lesson is educational content only and is not regulatory or legal advice. Always refer directly to ISO 13485:2016 for official requirements, and consult with qualified regulatory professionals for guidance specific to your situation.*