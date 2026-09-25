# Phase 0 AI Baseline

This document freezes the accepted StudentOS task-creation baseline before any
prompt experiments or LoRA specialization. It is an internal validation record,
not a claim that every natural-language request is supported.

## Frozen reference

- Date accepted: September 26, 2026
- Repository revision: `1bcd12f91dd2ba9427a66a21d86584906903b869`
- Provider: local Ollama at `http://127.0.0.1:11434`
- Task-action model tag: `qwen3:4b`
- Task-classification model tag: `qwen3:4b`
- Read-only chat model tag: `llama3.2:1b`
- Ollama request timeout: 300 seconds
- Task-action generation: temperature `0`, `num_predict` `512`, thinking disabled
- Classifier generation: temperature `0`, `num_predict` `512`, thinking disabled
- Read-only chat generation: temperature `0.3`, `num_predict` `512`

The task-action prompt is `TaskActionService._INSTRUCTIONS` in
`backend/ai/task_action_service.py` at the frozen revision. Its structured model
output is validated through `TaskCreateInterpretation` and converted into a
`TaskCreateProposal` in `backend/schemas/ai.py`. Schedule previews and confirmed
results use the contracts in `backend/schemas/schedule.py`.

The local Ollama model digest was not captured during this checkpoint. The model
tag and repository revision are the accepted Phase 0 identifiers. Phase 2 must
capture the model tag or digest for every controlled evaluation run.

## Representative accepted scenario

The manually tested task-creation conversation requested a two-hour physics
review for the following day, then supplied `2 pm` as the missing start time.
The accepted result was:

- scheduling mode: fixed
- estimated duration: 120 minutes
- scheduled start: September 23, 2026 at 2:00 PM local time
- scheduled end: September 23, 2026 at 4:00 PM local time
- deadline: none, because the user supplied work placement rather than a due date
- proposal: feasible and ready only after the missing start time was supplied

Confirmation persisted task `5` and exactly one linked, locked calendar event,
event `5`. The current API records preserve the 120-minute duration and the
`14:00–16:00` event interval.

The application log recorded:

- the incomplete preview returning one blocking question in about 129 seconds;
- the follow-up preview returning a feasible one-block schedule in about 84
  seconds;
- one confirmed apply request creating one calendar event in about 53 ms.

These timings describe one local-machine observation and are not performance
targets or general benchmarks.

## Phase 0 verification result

The project owner reported the following checks as passing against the frozen
revision:

- Python compilation for `backend` and `tests`;
- 102 backend tests;
- frontend ESLint;
- frontend production build;
- a real Qwen task-creation flow with the intended date, start time, duration,
  and end time;
- confirmation creating one task and exactly one linked calendar block;
- navigation away from Chat during an active request and back again without
  losing the resulting conversation or proposal.

The navigation result is intentionally recorded as text. It is regression
evidence for an internal bug fix and does not require a README screenshot or a
screen recording.

## Safety boundaries retained

- Qwen returns structured interpretation; it receives no database session or
  arbitrary application tools.
- Preview does not write records.
- Apply requires a validated proposal and explicit confirmation.
- Backend timing and scheduling services remain authoritative for conflicts,
  feasibility, and persistence.
- A task deadline remains separate from its scheduled calendar placement.

## Known baseline limitations

- Natural-language interpretation is probabilistic and has not been evaluated
  against a broad held-out dataset.
- Model response time is hardware-dependent and was slow in the accepted local
  observations.
- The narrow deterministic timing fallback covers explicit supported timing
  facts; it is not a second general natural-language parser.
- Chat history and pending proposals use browser `localStorage`, so different
  browsers and browser profiles have separate histories.
- Client-side navigation can preserve an active request, but refresh, tab
  closure, frontend restart, or backend restart cannot resume it.
- There is no authentication, per-user ownership, durable job queue, or
  cross-device synchronization.
- The accepted scenario does not prove multilingual, malformed, correction-heavy,
  or complex multi-task reliability. Those measurements belong to Phase 2.

## Change-control rule

Phase 2 experiments must treat this revision, prompt, schema, settings, and
scenario result as the control. If the prompt, model, schema, fallback logic, or
inference settings change, record a new version instead of silently replacing
this baseline.
