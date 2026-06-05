---
clause: 7.3
title: Design and Development
generated: 2026-06-03T20:44:45.913602
word_count: 1413
status: DRAFT — review before sharing with clients
---

# ISO 13485:2016 — Clause 7.3: Design and Development

# ISO 13485:2016 Clause 7.3: Design and Development

*Educational content only. Always refer to the actual ISO 13485:2016 standard for official requirements.*

---

## What This Clause Is About

When a medical device company creates a new product, dozens of decisions get made — what it does, how it's built, what materials it uses, how it gets tested. Clause 7.3 exists to make sure those decisions are documented, reviewed, and traceable so you can prove the final device actually does what it was designed to do. Without it, design decisions live in someone's head or scattered emails, and when something goes wrong — or when an auditor asks why you chose that particular voltage limit — you have nothing to show.

---

## What It Requires (The Essentials)

**1. Design and Development Planning**
Before design work starts, you need a plan. This plan defines the phases of development, who's responsible, what reviews will happen, and how different teams will communicate. Think of it as a project charter with quality built in.

**2. Design Inputs**
These are the requirements the device must meet — performance specs, safety standards, regulatory requirements, intended use, and user needs. Inputs must be documented and reviewed for completeness. Vague inputs ("the device should be easy to use") are a red flag.

**3. Design Outputs**
These are the deliverables that result from the design work — drawings, specifications, software code, labeling, manufacturing procedures. Outputs must be verifiable against inputs. If an input says the device must withstand a 1-meter drop, an output somewhere must describe how that's achieved.

**4. Design Reviews, Verification, and Validation**
- **Review**: Formal meetings at defined stages to evaluate whether the design is on track.
- **Verification**: Testing that confirms the design outputs meet the design inputs ("Did we build it right?").
- **Validation**: Testing that confirms the finished device works correctly for its intended use by real users ("Did we build the right thing?").

All three must be documented. They are not the same thing, and confusing them causes real problems.

**5. Design Transfer and Design Changes**
Design transfer is the formal handoff from engineering to manufacturing — ensuring the device can actually be built consistently. Any changes made after design is finalized must go through a controlled change process, not a casual conversation between engineers.

---

## What This Looks Like in Practice

Say a 40-person company is developing a handheld wound measurement device — a Class II product. Here's how Clause 7.3 plays out:

The **Regulatory Affairs Manager** kicks off a **Design and Development Plan** (sometimes called a "D&D Plan" or project plan) in the company's document management system. It lists four development phases: Concept, Detailed Design, Verification & Validation, and Transfer to Manufacturing.

The **Product Manager** and a **Clinical Specialist** work with the engineering team to document **Design Inputs** in a formal Design Input document. These come from user interviews, the intended use statement, applicable standards (like IEC 60601-1 for electrical safety), and predicate device research.

As engineering builds the device, **Design Outputs** are generated — mechanical drawings, a software requirements spec, a labeling draft, and a bill of materials. These live in a controlled folder tied to the design history file.

At the end of each phase, the team holds a **Design Review**. The QA Engineer facilitates, takes minutes, and documents any open action items. Sign-offs are captured.

Then comes **Verification** — the test lab runs drop tests, electrical safety tests, and accuracy testing against the specs written in the design inputs. All results are documented in a Verification Report.

**Validation** happens separately — real nurses use the device on actual wound measurements in a simulated use study. The V&V Report captures that the device performs as intended by real end users.

Finally, the **Design Transfer Checklist** confirms that manufacturing can produce the device to spec before the design is "locked." Any post-lock changes go through the company's **Design Change Request** process.

All of this — every plan, review record, test report, and approval — lives in the **Design History File (DHF)**.

---

## Common Mistakes and Audit Findings

**1. Design inputs that are too vague**
"The device must be user-friendly" is not a testable input. Auditors and reviewers will flag this immediately. Inputs need to be specific and measurable enough that you can verify them.

**2. Treating verification and validation as the same activity**
Running a lab test and calling it validation is a classic early-career mistake. Validation requires involvement of intended users under conditions that simulate real use. A bench test alone doesn't satisfy validation.

**3. Incomplete or missing design reviews**
Companies sometimes skip formal reviews when schedules are tight, planning to document them later. Auditors look at review records, attendance, and action item follow-up. "We had a meeting but didn't write it up" doesn't pass.

**4. DHF that's impossible to navigate**
The DHF doesn't have to follow a specific format, but it does have to be complete and organized enough that an auditor (or you, two years from now) can follow the design history from inputs to final device. Scattered files across three systems with no index is a finding waiting to happen.

---

## Key Terms to Know

**Design History File (DHF):** The organized collection of all records that describe the design and development history of a device. The FDA specifically requires this under 21 CFR Part 820; ISO 13485 has equivalent expectations.

**Design Inputs:** The documented requirements the device must meet — regulatory, functional, safety, and user-based.

**Design Outputs:** The documented results of the design process — drawings, specs, procedures, labeling — that translate inputs into something buildable.

**Verification:** Objective testing confirming that design outputs meet design inputs. Answers: "Did we build it right?"

**Validation:** Testing confirming the finished device meets user needs and intended use under real-world conditions. Answers: "Did we build the right thing?"

**Design Transfer:** The controlled process of moving a design from development into routine manufacturing.

**Design Change Control:** The formal process for reviewing, approving, and documenting any change made to a locked design.

**Risk Management:** The ongoing process (per ISO 14971) of identifying hazards, estimating risks, and controlling them — closely linked to design inputs and outputs throughout 7.3.

---

## Check Your Understanding

**1. What is the primary purpose of design inputs?**
To document the specific, measurable requirements the device must meet — so that outputs and verification activities have something concrete to test against.

**2. A test engineer runs a bench test confirming the device meets its accuracy specification. Is this verification, validation, or both?**
Verification only. The test confirms the design output meets a design input. Validation would require testing with actual intended users under realistic use conditions.

**3. Scenario: An engineer discovers a design flaw after the design is locked and quietly updates a drawing without filing a change request. What's the problem?**
This bypasses design change control, meaning the change isn't reviewed, documented, or risk-assessed. The DHF no longer reflects the actual device, which is both a quality failure and a regulatory violation.

**4. What's the difference between a design review and verification?**
A design review is a structured meeting to evaluate whether the design is progressing correctly. Verification is objective testing (analysis, inspection, or test) that confirms outputs meet inputs. Reviews evaluate; verification confirms with evidence.

**5. Scenario: A startup skips the Design and Development Plan because the team is small and "everyone knows the plan." An auditor asks for it. What happens?**
The auditor will cite a nonconformance. Clause 7.3.2 requires a documented plan. Team knowledge doesn't substitute for a controlled document, especially when people leave, roles change, or the device is reviewed by a regulatory body.

---

## How This Connects to Your Career

Design and development is where most of the critical decisions about a medical device get made — and Clause 7.3 is the framework that makes those decisions defensible. If you understand this clause well, you can sit in a design review and know what questions to ask, catch a missing input before it becomes a failed verification, and build or audit a DHF that would hold up under FDA inspection. Companies lose FDA clearances and CE marks because their design records are incomplete. Early-career professionals who understand the difference between verification and validation, who can manage a DHF, and who know how to write a traceable design input are genuinely valuable — because a surprising number of people in this industry still confuse these things years into their careers.