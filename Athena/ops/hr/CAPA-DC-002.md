# CAPA-DC-002 — Voice Stream Sharing Not Implemented (DI-033-A/B/C)

**Status:** CLOSED  
**Opened:** 2026-06-07  
**Closed:** 2026-06-07  
**Root Cause CO:** CO-010  

## Non-Conformance

`dc_verify.py` tests for DI-033-A/B/C (voice stream sharing) were deregistered
from `main()` because the implementation had not been completed. This caused a
test coverage gap where three verified-OPEN design inputs had no active
verification run.

## Root Cause

CO-008 branch work introduced `_listen_for_wake(oww_model, stream)` and
`_record_query(stream)` signatures and the shared `sd.InputStream` in
`_voice_loop`, but the dc_verify test registration was accidentally removed in
the same session.

## Correction

1. Re-registered `test_DI_033_A()`, `test_DI_033_B()`, `test_DI_033_C()` in
   `dc_verify.py` `main()` under section "UN-033 Voice Query Readiness Latency".
2. Confirmed all 3 tests pass: DI-033-A/B/C → VERIFIED.
3. Updated DC-002 DI-033 statuses from OPEN to VERIFIED.

## Preventive Action

The DC-006 co-commit rule (DI-034-A) now requires that every code commit that
introduces behavioral changes must also update at least one design control
document. This prevents silent test deregistration from occurring without a
corresponding DC-002 status change.

## Verification

`python design_control\dc_verify.py --di DI-033` exits 0, all 3 tests PASS.

---
*Filed per DC-005 CAPA protocol. Approved by Steven Tran.*
