---
clause: 8.2.3
title: Process Monitoring
generated: 2026-06-03T20:50:57.147091
word_count: 1374
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 8.2.3: Process Monitoring

# ISO 13485:2016 Clause 8.2.3: Process Monitoring

*Educational content only. Always refer to the actual ISO 13485:2016 standard for official requirements.*

---

## What This Clause Is About

Manufacturing a medical device correctly once isn't enough — you need evidence that your processes stay in control over time. Clause 8.2.3 requires you to monitor and measure your manufacturing and production processes to confirm they're consistently delivering what they're supposed to deliver. Without this, you're essentially hoping your processes work rather than knowing they do.

---

## What It Requires (The Essentials)

**1. Monitor and measure your processes — not just your products.**
There's a meaningful difference between inspecting a finished catheter (product monitoring) and tracking whether your crimping machine is running within its validated parameters (process monitoring). This clause is about the latter. You need to watch the process itself.

**2. Use suitable methods.**
"Suitable" means the monitoring method actually tells you something meaningful. If your sterilization process requires a specific temperature range to achieve sterility assurance, tracking oven temperature with a calibrated sensor is suitable. Eyeballing it is not.

**3. Demonstrate that processes can achieve planned results.**
If a process can't consistently hit its targets, that's a problem that must be addressed — not just documented and filed away. The clause expects you to act when processes don't conform.

**4. Document the monitoring activities and results.**
You need records. Not just that you monitored, but what you measured, when, and what the results were.

**5. When planned results aren't achieved, take corrective action.**
This connects directly to your CAPA (Corrective and Preventive Action) system. A process drifting out of control isn't a paperwork problem — it's a quality signal that demands a response.

---

## What This Looks Like in Practice

Imagine a 60-person company making single-use surgical staplers. Their manufacturing floor runs two critical processes: laser welding of the anvil assembly and ethylene oxide (EtO) sterilization.

The **Manufacturing Engineer** worked with **Quality Engineering** during process validation to establish monitoring parameters — things like laser power output (watts), pulse duration, and weld strength pull-test results. These parameters and their acceptable ranges are documented in a **Process Monitoring Plan** (sometimes called a Control Plan), which lives as a controlled document in the QMS.

On the floor, **Production Technicians** run hourly checks on laser power output and log results on a paper traveler attached to each production lot. At the end of each shift, a **Quality Technician** pulls sample parts for pull-testing and records results in an electronic batch record. The data feeds into a simple **Statistical Process Control (SPC) chart** that the Quality Engineer reviews weekly.

For EtO sterilization, the sterilization contractor provides a **Certificate of Conformance** and a **cycle report** after each run. The **Supplier Quality Engineer** reviews these against the qualified cycle parameters before any lot is released.

When a laser power reading falls outside the control limits, the line stops. The technician flags it on the traveler, the Quality Technician initiates a **nonconformance report (NCR)**, and — depending on root cause — it may escalate to a **CAPA**. The product made during that window is quarantined pending disposition.

That entire loop — plan, monitor, record, respond — is what Clause 8.2.3 looks like when it's working.

---

## Common Mistakes and Audit Findings

**1. Monitoring the wrong thing.**
Teams sometimes track parameters that are easy to measure rather than parameters that actually indicate process health. Logging machine run time instead of weld temperature isn't process monitoring — it's activity logging. Auditors will ask: "How does this measurement tell you your process is in control?"

**2. Records that exist but aren't reviewed.**
Data sitting in a binder that no one reads is a false sense of security. A common finding: process monitoring records exist, but there's no evidence that trending or review occurred. The standard expects you to use the data, not just collect it.

**3. No clear link to corrective action.**
When out-of-control events are found in records but there's no corresponding NCR or CAPA, that's a red flag. Auditors will pull process monitoring records and cross-reference them with your NCR log. If data shows drift and there's no response, expect a finding.

**4. Confusing process monitoring with final inspection.**
Inspecting the finished device doesn't substitute for monitoring the process that made it. Both have their place, but this clause is specifically about the process. Early-career professionals often don't make this distinction clearly, which leads to gaps in the QMS.

---

## Key Terms to Know

**Process monitoring:** Ongoing measurement of how a manufacturing or production process is performing, separate from inspecting the finished product.

**Control limits:** The boundaries within which a process measurement must stay to be considered "in control." Established during validation and documented in the monitoring plan.

**Statistical Process Control (SPC):** A method of using statistical analysis to monitor process data over time and detect trends before they become failures.

**Control Plan / Process Monitoring Plan:** A documented plan that specifies what to monitor, how to monitor it, how often, and what to do when results fall outside acceptable limits.

**Nonconformance Report (NCR):** A documented record that a product or process has failed to meet a specified requirement. The formal starting point for disposition and potential corrective action.

**CAPA (Corrective and Preventive Action):** A system for identifying the root cause of nonconformances and taking action to prevent recurrence (corrective) or prevent occurrence (preventive).

**Process validation:** The documented evidence that a process consistently produces a result meeting its predetermined specifications — the foundation that makes process monitoring meaningful.

---

## Check Your Understanding

**1. What is the difference between process monitoring and product inspection?**
*Answer:* Product inspection examines the finished device to see if it meets specifications. Process monitoring watches the process itself — the parameters, conditions, and inputs — to confirm the process stays in control. Both matter, but they're not interchangeable under this clause.

**2. Why does process monitoring need to be documented?**
*Answer:* Documentation provides objective evidence that monitoring occurred and that results were reviewed. Without records, you cannot demonstrate conformance during an audit or investigation.

**3. Scenario: A production line has been logging oven temperature data for six months, but the Quality Engineer who reviews it left the company two months ago. No one has reviewed the data since. Is this a problem under Clause 8.2.3?**
*Answer:* Yes. Collecting data without reviewing it fails the intent of the clause. Monitoring exists to detect issues and trigger action. Unreviewed data offers no quality benefit and would likely generate an audit finding for lack of ongoing oversight.

**4. True or False: If a process passes final product inspection every time, you don't need to monitor the process separately.**
*Answer:* False. Clause 8.2.3 specifically requires process monitoring. Final inspection success doesn't eliminate the requirement, and it doesn't tell you whether the process is trending toward failure before a defect appears.

**5. Scenario: A quality technician notices that weld strength pull-test results have been trending downward for three weeks but still remain within control limits. What should happen?**
*Answer:* A downward trend — even within limits — is a quality signal. Good practice (and what SPC is designed to detect) calls for investigating the trend before it becomes a failure. Depending on the QMS, this might trigger a preventive action or at minimum be escalated to the Quality or Manufacturing Engineer for review. Waiting for a limit to be breached is reactive; this clause supports a proactive approach.

---

## How This Connects to Your Career

Employers value QA/RA professionals who understand the difference between checking boxes and actually controlling quality. When you understand Clause 8.2.3, you can walk onto a manufacturing floor and ask the right questions: What are we monitoring? How often? Who reviews it? What happens when something's out of range? Those questions — and knowing whether the answers are good or not — are exactly what internal auditors, quality engineers, and regulatory affairs specialists are paid to know. Early-career professionals who grasp process monitoring also tend to be better at CAPA investigations, because they understand what data should have existed before a failure occurred. That kind of systems thinking is what separates a professional who can maintain a QMS from one who can improve it.