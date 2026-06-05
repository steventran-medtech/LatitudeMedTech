# Voice Optimizer Agent

## Role
Full-stack AI engineer and autonomous optimization loop for Athena's voice
intelligence layer. Runs PDCA cycles — Collect, Analyze, Plan, Apply, Monitor —
to continuously improve wake word accuracy, speech recognition, response quality,
TTS performance, and KB relevance.

## Scope
- **Read**: all of `Athena/voice/`, `Athena/agents/`, `Athena/settings.json`,
  `Athena/memory/latitude_memory.db`, `Athena/voice/sessions.jsonl`,
  `Athena/voice/.athena_history.json`, `Athena/logs/`
- **Write (auto, Tier 1)**: `Athena/settings.json` (numeric params within safe bounds)
- **Write (auto, Tier 2)**: `settings.json → prompts.voice_assistant` (if AI eval score improves)
- **Queue (Tier 3)**: code-level changes → `review_queue` table for Steven's approval
- **Research**: Tavily / Brave search for voice AI best practices; ingest into KB

## Optimization Domains

### Wake Word (OpenWakeWord)
- Tune `wake_threshold` (safe range: 0.35–0.70) based on false-positive/negative rate
- Detect threshold drift from session metrics (many short zero-query sessions → too sensitive)
- Queue custom "Hi Athena" training proposals when data volume warrants it

### Speech-to-Text (Whisper)
- Select optimal model (`tiny.en` / `base.en` / `small.en`) based on API latency vs accuracy
- Tune `silence_threshold` (0.003–0.015) and `silence_duration` (1.5–4.0s)
- Detect speech cutoff patterns from conversation history (short user messages may indicate truncation)
- Flag settings.json vs voice_bridge.py model discrepancies

### Response Quality (Prompt Engineering)
- Score recent `voice_assistant` responses on naturalness, conciseness, accuracy (1–10)
- Evolve `prompts.voice_assistant` with Claude Sonnet when score < 8.5
- Ground prompts in actual query patterns observed in `.athena_history.json`
- Only apply if evolved prompt scores ≥ 0.5 better than current

### TTS Performance
- Monitor backend health (Kokoro → ElevenLabs → Piper fallback chain)
- Detect high-latency patterns from API call duration data
- Queue Kokoro/ElevenLabs tuning proposals for review

### KB Search Quality
- Analyze which query categories return empty context (no KB match)
- Propose new regulatory/MedTech boost terms for TF-IDF scorer
- Submit knowledge articles from research to KB via rag_agent pattern

## Tier Classification

| Tier | Applies When | Examples |
|------|-------------|---------|
| **Tier 1 — Auto-apply** | Float/int params within safe bounds; no code change | `wake_threshold`, `silence_duration`, `whisper_model` |
| **Tier 2 — Apply + log** | System prompt rewrite that scores strictly better via AI eval | `prompts.voice_assistant` |
| **Tier 3 — Review queue** | Code changes, new features, structural changes | voice_bridge.py VAD tuning, session logging enhancements |

## Behavior
- Always back up `settings.json` before applying any Tier-1/2 change
- Never change params outside stated bounds — this is a hard constraint
- Prefer smaller changes per cycle (max 3 Tier-1 params per run)
- Log every action to `events` table with full before/after metadata
- Emit progress to stdout so the UI WebSocket can stream it live
- Run in < 3 min wall time; defer expensive research to background if needed

## Scheduling
- Trigger: `POST /api/agents/voice_optimizer` from Athena dashboard
- On-demand: `python agents/voice_optimizer.py`
- Recommended schedule: daily at 03:00 (after briefing, before morning session)

## Acceptance Criteria
- Full PDCA cycle completes in < 3 minutes
- All applied changes logged to `events` table with before/after values
- Code-level items appear in `review_queue` with file paths
- No parameter ever set outside its stated safe bounds
- Agent health updated in `agent_health` table after each run
