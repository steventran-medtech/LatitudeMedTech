---
clause: 4.2.3
title: Medical Device File
generated: 2026-06-03T20:33:43.179054
word_count: 1344
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 4.2.3: Medical Device File

# ISO 13485:2016 Clause 4.2.3: Medical Device File

*Educational content only. Always refer to the actual ISO 13485:2016 standard for official requirements.*

---

## What This Clause Is About

When a medical device company designs and sells a product, regulators and auditors need to be able to find all the technical information about that device in one organized place. Clause 4.2.3 requires companies to maintain a **Medical Device File (MDF)** — essentially a master reference point that either contains or points to every document that defines, governs, and supports a specific device. Without it, critical information gets scattered across departments, and nobody can confidently say they have the complete picture of a product.

---

## What It Requires (The Essentials)

**1. One file per device type (or family)**
You need a Medical Device File for each device type you manufacture. If you make three different infusion pumps with meaningfully different designs, you likely need three files. Similar devices may be grouped, but you need a defensible rationale for that grouping.

**2. It must contain or reference key technical information**
The MDF doesn't have to physically hold every document, but it must link to them. Required content includes:
- Device description and specifications
- Labeling and packaging requirements
- Manufacturing and inspection requirements
- Risk management records (your risk file)
- Clinical evaluation or performance data
- Any applicable regulatory requirements or standards the device meets

**3. It must be maintained and kept current**
This isn't a one-time task. When a device changes — new supplier, design update, labeling revision — the MDF must be updated to reflect that. A stale file is a compliance problem.

**4. It must be organized so others can navigate it**
An auditor or regulator should be able to open your MDF and find what they need without you walking them through it by hand. Structure and cross-referencing matter.

---

## What This Looks Like in Practice

Imagine a 45-person company called Cascade Medical that makes a Class II surgical stapler. Their Regulatory Affairs Specialist, Maya, owns the Medical Device File for that product.

The MDF itself is a controlled document — in their document management system it's titled **MDF-0042: AutoStaple 300 Medical Device File**. It's structured as an index document, roughly 8 pages long, that doesn't contain the actual specs and drawings but references them by document number. Here's what it links to:

- **Device Master Record (DMR)** documents: the bill of materials, manufacturing procedures, inspection and test procedures, sterilization validation records
- **Design History File (DHF)**: the full record of how the product was designed and verified — requirements, design reviews, V&V protocols and reports
- **Risk Management File**: hazard analysis, FMEA, residual risk evaluation, post-market risk review updates
- **Labeling package**: IFU, device label, packaging specifications
- **Regulatory submissions**: 510(k) clearance summary, applicable standards met (e.g., ISO 11135 for sterilization, IEC 62366 for usability)
- **Clinical/performance data**: literature review, clinical evaluation report

When Maya onboards a new QA Associate, she walks them through the MDF first. Her reasoning: "If you understand the file, you understand the product." When the company switches to a new contract sterilizer, the sterilization validation records get updated, and Maya revises the MDF index to point to the new document versions. That revision goes through document change control like anything else.

---

## Common Mistakes and Audit Findings

**1. Confusing the MDF with the DHF or DMR**
These three documents overlap but serve different purposes. The DHF captures design history. The DMR captures how to build the device. The MDF is the integrating document that ties everything together, including post-market information. Early-career professionals often assume the DHF alone satisfies this clause — it doesn't.

**2. The file is out of date after a product change**
A design change gets processed through engineering change orders, but nobody updates the MDF index to reflect the new documents. Auditors will ask you to trace from the MDF to the actual current device — if those trails don't match, you have a finding.

**3. Missing regulatory requirements section**
Companies often document their technical specifications but forget to explicitly link to applicable regulatory requirements and standards (EU MDR Annex I, specific ISO standards, etc.). This is a common notified body observation.

**4. The MDF exists but is unnavigable**
Some companies technically have an MDF but it's a disorganized folder dump. If an auditor has to ask you to help them find things because the structure is unclear, that's a problem — even if all the documents technically exist somewhere.

---

## Key Terms to Know

**Medical Device File (MDF):** The organized collection (or index) of all documents that define and support a specific medical device, required by Clause 4.2.3.

**Device Master Record (DMR):** The set of documents that describes how a device is manufactured — specs, procedures, labeling requirements. Think of it as the recipe.

**Design History File (DHF):** The record of how a device was designed — requirements, verification, validation. It shows the design process happened correctly.

**Risk Management File:** All documentation associated with risk management activities for the device, typically governed by ISO 14971.

**Controlled Document:** Any document managed under your document control system — meaning it has version history, requires approval before use, and can only be changed through a formal process.

**Clinical Evaluation Report (CER):** A document that evaluates clinical data to confirm a device's safety and performance. Required content in the MDF, particularly important under EU MDR.

**Traceability:** The ability to link one piece of information back to its source — e.g., tracing a labeling claim back to verified performance data. The MDF must support this.

---

## Check Your Understanding

**1. What is the primary purpose of a Medical Device File?**
*Answer:* To provide a single organized reference point that contains or links to all technical and regulatory documentation for a specific device — making it possible to demonstrate the device meets requirements.

**2. Does every document need to physically live inside the MDF?**
*Answer:* No. The MDF can reference documents stored elsewhere (like the DHF or risk file), as long as it clearly identifies where those documents are and what they contain.

**3. Scenario: Your company makes two versions of the same blood pressure cuff — one adult, one pediatric. Different sizes but nearly identical design. Do you need two MDFs?**
*Answer:* Possibly one, if you can justify grouping them as a device family with documented rationale. However, any differences in specifications, labeling, or risk profile must be captured. When in doubt, separate files are safer — consult your actual standard and qualified RA staff.

**4. A design change is implemented and the engineering team updates the drawings and manufacturing procedure. What else should happen?**
*Answer:* The MDF index should be updated to reference the new document versions, and that update should go through document change control. The MDF needs to reflect the current state of the device.

**5. Scenario: During an audit, a notified body auditor opens your MDF and asks where the clinical evaluation data is. You can't find a reference to it in the file. What's the finding, and what's the fix?**
*Answer:* This would likely be a nonconformity — the MDF is incomplete. The fix is to update the MDF to reference the Clinical Evaluation Report and ensure it's properly version-controlled, then implement a process so future updates stay in sync.

---

## How This Connects to Your Career

Professionals who understand the Medical Device File early develop something most junior QA/RA staff lack: a systems-level view of a product. When you know how the MDF connects the DHF, DMR, risk file, labeling, and regulatory submissions, you stop seeing those documents as isolated tasks and start seeing them as a product story you're responsible for maintaining. That perspective makes you faster during audits, more useful during product changes, and significantly more credible when working with senior engineers or notified bodies. Companies preparing for EU MDR compliance, 510(k) submissions, or surveillance audits need people who can build and maintain these files — not just file things in folders.