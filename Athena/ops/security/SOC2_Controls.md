# SOC II & Cybersecurity Control Matrix
**Latitude MedTech LLC — Athena Platform**
**Status:** Alpha · **Date:** 2026-06-05 · **Version:** 0.5.0

---

## SOC II Trust Service Criteria — Implemented Controls

| CC | Criterion | Status | Implementation |
|----|-----------|--------|----------------|
| CC1.1 | Commitment to integrity and ethical values | ✅ | Core Values (Dignity · Stewardship · Service · Honesty · Mercy) binding on all outputs; CAPA protocol on 3+ errors |
| CC2.2 | Communication of security policies | ✅ | `compliance.md` (immutable agent rules) + `CLAUDE.md` hard rules; output labeling required on every deliverable |
| CC3.2 | Risk assessment process | ✅ | Production blockers list below; threat model documented; RBAC gate before multi-user Phase 3+ |
| CC5.6 | Logical access — no shell injection vectors | ✅ | `shell=False` enforced on all `subprocess` calls; `os.startfile()` replaces `shell=True` for document-open |
| CC6.1 | Data file protection | ✅ | `latitude_memory.db` + `.athena.key` chmod 0600 on every server start (`_harden_db_permissions()`) |
| CC6.2 | Secure credential issuance | ✅ | Session token: `secrets.token_hex(32)` (256-bit entropy); stored at `voice/.athena.key` (0600); never in git |
| CC6.6 | Authentication on all requests | ✅ | `AuthMiddleware` in `server.py` validates `X-Athena-Key` header on every non-exempt request; timing-safe comparison via `secrets.compare_digest`; auth failures audit-logged; WebSocket endpoints (`/ws`, `/ws/voice`) reject connections without valid `?token=` query param |
| CC6.7 | Transmission security | ✅ | Local-only (localhost binding); CORS restricted to `localhost:3000` + `app://`; TLS deferred to Phase 3+ cloud |
| CC7.1 | System monitoring | ✅ | Per-agent Python logs in `Athena/logs/`; voice telemetry in `voice/query_telemetry.jsonl`; voice sessions in `voice/sessions.jsonl` |
| CC7.2 | Security event logging | ✅ | `logs/audit.log` via `RotatingFileHandler` (5 MB × 5 backups = 30 MB max); logged events: `server_start`, `agent_start/done`, `auth_failure`, `ws_auth_failure`, `file_open/save/delete/delete_bulk`, `settings_update/prompt_update/reset`, `pipeline_update`, `decks_bulk_delete/accept/reject` |
| CC7.3 | Anomaly detection | ⏳ | Rate limiting (120 req/min via slowapi) provides basic DoS mitigation; full SIEM/anomaly detection deferred to Phase 3+ |
| CC7.4 | Incident response | ⏳ | **Production blocker** — runbook not yet written or tested |
| CC8.1 | Change management | ✅ | CAPA protocol (3+ errors → RCA → Steven approves); autonomous QA on every code change; Git PR flow required; CHANGELOG.md maintained |
| CC9.1 | Risk identification | ✅ | This document + `compliance.md` threat model; RBAC required before Phase 3; penetration test required before Production |
| CC9.2 | Risk mitigation | ✅ | OWASP Top 10 mitigations below; rate limiting; input sanitization; no PHI hard stop |

---

## OWASP Top 10 — Control Summary

| Risk | Status | Control |
|------|--------|---------|
| A01 Broken Access Control | ✅ | `AuthMiddleware` on all API routes; `_safe_filename()` + resolved-path checks on all file endpoints; FOLDER_MAP allowlist prevents arbitrary path access |
| A02 Cryptographic Failures | ⚠️ Alpha | Session token stored plain-text (localhost-only; acceptable for alpha); SQLite unencrypted (local disk); Phase 3 requires TLS + AWS Secrets Manager + encrypted RDS |
| A03 Injection | ✅ | SQL: all queries parameterized (`?` placeholders); Shell: `shell=False` everywhere + `os.startfile()` for file open; Input: `_safe_filename()` (rejects `..`, `/`, `\`); `_safe_arg()` strips shell metacharacters |
| A04 Insecure Design | ✅ | No PHI until HIPAA BAA (hard stop); RBAC gate before Phase 3; output disclaimer + label on all deliverables; human gate (Steven reviews 100%) |
| A05 Security Misconfiguration | ✅ | API docs disabled (`docs_url=None`); strict CSP + security headers middleware; CORS restricted; secrets excluded from git (`.gitignore`) |
| A06 Vulnerable Components | ⏳ | No automated dependency scanning; manual review on `requirements.txt` updates — **add Dependabot for Phase 3** |
| A07 Auth/Session Failures | ✅ | `secrets.compare_digest` (timing-safe, no timing oracle); 256-bit token entropy; token not exposed in logs except WebSocket `?token=` query param |
| A08 Software Integrity | ⏳ | Code-signing cert (`StevenTran.pfx`) for Windows binaries; no SBOM yet |
| A09 Security Logging Failures | ✅ | Rotating audit log (5 MB × 5 backups); every state-mutating action logged; auth failures logged with path + IP; agent lifecycle logged |
| A10 SSRF | N/A | No server-side URL fetching based on user input; Brave/Tavily calls use hardcoded query templates only |

---

## Authentication Flow

```
Browser (localhost:3000)
  │
  ├── GET /api/auth/token     ← no auth required (returns SESSION_TOKEN)
  │
  ├── All other API calls  → X-Athena-Key: <SESSION_TOKEN>  ← AuthMiddleware validates
  │
  └── WebSocket /ws           ← ws://localhost:8000/ws?token=<SESSION_TOKEN>
      WebSocket /ws/voice     ← ws://localhost:8000/ws/voice?token=<SESSION_TOKEN>
```

Token lifecycle:
- Generated: `secrets.token_hex(32)` on server start → stored at `Athena/voice/.athena.key` (0600)
- Persists across server restarts (re-reads from file if ≥ 32 chars)
- Rotated: delete `.athena.key` and restart server
- Never in git, never in logs

---

## Audit Log Event Reference

| Event | Trigger | Detail |
|-------|---------|--------|
| `server_start` | Server startup | `version=X.Y.Z` |
| `auth_failure` | Invalid/missing token | `path=... ip=...` |
| `ws_auth_failure` | WebSocket rejected | path string |
| `agent_start` | Agent triggered | `agent=... args=...` |
| `agent_done` | Agent completed | `agent=... status=... rc=...` |
| `agent_trigger` | Specific agent triggers | `agent=... clause=...` (ISO) |
| `file_open` | Document opened in OS | `filename=... folder=...` |
| `file_save` | Document saved | `filename=... folder=...` |
| `file_delete` | Single file deleted | `filename=... folder=...` |
| `file_delete_bulk` | Bulk delete | `deleted=N failed=N` |
| `settings_update` | Settings changed | `keys=[...]` |
| `settings_prompt_update` | Agent prompt changed | `agent=...` |
| `settings_reset` | Settings reset to defaults | — |
| `pipeline_update` | Marketing pipeline target updated | `target=... status=...` |
| `decks_bulk_delete` | Decks deleted | `count=N` |
| `decks_bulk_accept` | Decks approved | `count=N` |
| `decks_bulk_reject` | Decks rejected | `count=N` |

Log location: `Athena/logs/audit.log` (rotates at 5 MB, 5 backups)

---

## Production Blockers (Before Phase 3+)

- [ ] ToS and disclaimer reviewed by licensed attorney
- [ ] RBAC fully implemented (CC6.3)
- [ ] Penetration test with no critical findings (CC9.2)
- [ ] RAC consultant engaged and under contract
- [ ] Non-compete cleared by employment attorney
- [ ] Data retention + deletion policy documented (CC9.1)
- [ ] Incident response runbook written and tested (CC7.4)
- [ ] Red-team adversarial eval completed
- [ ] Dependency vulnerability scanning automated (A06)
- [ ] TLS for all connections (A02) — Phase 3+ cloud deployment
- [ ] Secrets management via AWS Secrets Manager (A02) — Phase 3+
- [ ] HIPAA BAA signed before any PHI handled
