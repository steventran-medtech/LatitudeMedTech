---
clause: 8.3
title: Control of Nonconforming Product
generated: 2026-06-03T20:52:24.926187
word_count: 1361
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 8.3: Control of Nonconforming Product

# ISO 13485:2016 Clause 8.3: Control of Nonconforming Product

*Educational content only. Always refer to the actual ISO 13485:2016 standard for official requirements.*

---

## What This Clause Is About

Sometimes things go wrong in manufacturing or receiving — a component arrives damaged, a finished device fails a test, or a label gets printed with the wrong revision. Clause 8.3 exists to make sure those problems get caught, contained, and properly resolved before a nonconforming product reaches a patient. Without a system for this, defective devices can slip through undetected, which is both a patient safety risk and a regulatory violation.

---

## What It Requires (The Essentials)

**1. Identify nonconforming product and segregate it.**
When something doesn't meet requirements, you need to identify it (usually with a physical label or tag) and move it somewhere it can't accidentally be used or shipped. A red "HOLD" tag and a locked cage in the corner of the warehouse is a classic example.

**2. Document it.**
You need a record of what was found, when, and where. This is usually called a Nonconformance Report (NCR) or Deviation Report. No verbal fixes — it has to be written down.

**3. Evaluate it and decide what to do with it.**
Someone with appropriate authority needs to review the nonconformance and determine disposition — meaning, what happens to the product. The standard gives you several options: rework it, scrap it, use it as-is (with documented justification and potentially customer or regulatory notification), or return it to the supplier.

**4. Control concessions carefully.**
A "concession" (also called "use-as-is") means accepting product that doesn't fully meet specs. This is allowed but has strict conditions under ISO 13485 — you need documented justification and, depending on the situation, may need regulatory or customer approval. This is stricter in medical devices than in many other industries.

**5. Investigate and verify reworked product.**
If you rework a nonconforming product to bring it into compliance, you have to verify it actually meets requirements after rework — and keep records. You also need to consider whether rework could have introduced new problems (think: re-sterilizing a device that was only validated for one sterilization cycle).

---

## What This Looks Like in Practice

Imagine a small surgical instrument company with about 80 employees. During incoming inspection, a quality technician notices that a batch of stainless steel forceps from a supplier has surface finish measurements outside the specification range.

Here's what happens:

1. **The technician places the parts on HOLD.** She attaches a red "NONCONFORMING — DO NOT USE" label to each box and moves them to a designated quarantine area — a separate shelf in the receiving area with a physical lock.

2. **She opens an NCR in the company's QMS software** (something like Greenlight Guru or a simple SharePoint form), documenting the part number, lot number, quantity, date received, and the specific measurement results that failed.

3. **The NCR is assigned to the Quality Engineer.** The QE reviews the data, confirms the nonconformance, and loops in the Design Engineer to evaluate whether the surface finish deviation actually affects device function or patient safety.

4. **Disposition decision is made.** In this case, the team determines the parts can't be used as-is (the deviation could affect corrosion resistance), so the disposition is "Return to Supplier." The QE documents this decision in the NCR with the technical justification.

5. **The NCR is closed with evidence.** The QE attaches the supplier return documentation, confirms the parts left the facility, and closes the record. The NCR data also feeds into the quarterly supplier performance review.

The whole process — from identification to closure — is documented. If a notified body auditor asks "show me how you handle incoming nonconformances," this is exactly the paper trail they want to see.

---

## Common Mistakes and Audit Findings

**1. No physical segregation.**
Writing an NCR but leaving the nonconforming parts in the normal stock location is one of the most common findings. Auditors will ask to see your quarantine area. If the hold label falls off and the part gets used, you have a much bigger problem than a minor finding.

**2. Dispositions signed off by whoever is available, not someone qualified.**
The standard requires that dispositions be made by authorized personnel. At smaller companies, it's tempting to let the technician who found the problem also close it out. You need defined roles — usually Quality Engineering or a Quality Manager — for disposition authority.

**3. Closing NCRs without verifying rework.**
Reworking a product and then immediately closing the NCR without re-inspection is a real finding. Rework needs its own verification step with documented evidence that the product now meets spec.

**4. Using concessions too casually.**
Accepting nonconforming product "use-as-is" without proper technical justification and authorization — especially for implantable or sterile devices — is a serious audit flag. "It's probably fine" is not a documented justification.

---

## Key Terms to Know

**Nonconformance (NC):** Failure to meet a specified requirement. Could be a dimension, a label, a functional test result — anything that doesn't meet the defined spec.

**NCR (Nonconformance Report):** The document used to record and manage a nonconformance. Sometimes called a Deviation Report depending on the company.

**Disposition:** The formal decision about what to do with nonconforming product. Options typically include: rework, scrap, use-as-is (concession), or return to supplier.

**Quarantine / Segregation:** Physically separating nonconforming product from conforming product to prevent accidental use or shipment.

**Concession (Use-As-Is):** Accepting product that doesn't fully meet specifications. Requires documented justification and sometimes regulatory or customer notification.

**Rework:** Performing additional work on a nonconforming product to bring it into compliance with requirements.

**Regrade:** Reclassifying nonconforming product for a different application where it does meet requirements. Less common in medical devices.

---

## Check Your Understanding

**1. What is the primary purpose of physically segregating nonconforming product?**
*Answer: To prevent it from being accidentally used, shipped, or mixed with conforming product while the disposition is being determined.*

**2. Which of the following is NOT typically an acceptable disposition for nonconforming product under ISO 13485?**
a) Rework and re-inspect
b) Scrap
c) Ship it and document the complaint later
d) Return to supplier

*Answer: C. Shipping known nonconforming product is not an acceptable disposition.*

**3. True or False: A verbal approval from a Quality Manager is sufficient to authorize a use-as-is concession.**
*Answer: False. Dispositions must be documented, including the justification and who authorized the decision.*

**4. Scenario: A production technician finds a cracked housing on a finished infusion pump during final inspection. He fixes it with extra adhesive and puts it back in the finished goods queue without opening an NCR because "the fix only took two minutes." What went wrong?**
*Answer: Multiple problems. The nonconformance was never documented, the rework was not authorized or verified against requirements, and the adhesive fix may not be a validated repair method. The device could fail in use.*

**5. Scenario: Your company wants to accept a batch of components that are slightly out of tolerance because the supplier lead time is 12 weeks and production is behind schedule. What does ISO 13485 require before you can do this?**
*Answer: You need a documented concession with technical justification showing the deviation doesn't compromise safety or performance, authorization from appropriate personnel, and potentially regulatory or customer notification depending on the device type and your procedures.*

---

## How This Connects to Your Career

Clause 8.3 is one of the first places auditors look and one of the first processes early-career QA professionals actually own day-to-day. Being the person who knows how to open a clean NCR, write a defensible disposition justification, and close a record correctly makes you immediately useful to your team — and immediately visible to your manager. More importantly, building the habit of treating every nonconformance as a documentation event (not just a problem to solve and forget) is foundational to everything else in quality: CAPA, supplier management, and post-market surveillance all rely on the nonconformance data you generate here. Companies that handle nonconformances well catch problems before they become recalls. Learning this clause well is learning how to protect patients and protect your