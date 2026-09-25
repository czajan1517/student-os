# StudentOS Development Phases

This document is the canonical development order for StudentOS. It merges the
original AI-control batches with the later portfolio and delivery plan. When a
bug-fix detour occurs, update the current phase's issue list without silently
skipping later phase gates.

## Status key

- **Completed:** implemented, reviewed, tested, and committed.
- **In progress:** active work may be uncommitted or awaiting live verification.
- **Planned:** no completion claim should be made yet.

## Required workflow for every phase

```text
Explain the design and reasoning
    -> implement only the approved phase scope
    -> explain helpers before the main coordinator
    -> review unit-test logic and real integration evidence
    -> run focused tests
    -> run the complete backend suite, frontend lint/build, and repository checks
    -> quiz and correct important misunderstandings
    -> obtain explicit approval
    -> commit the reviewed scope
    -> push only after explicit approval
```

Automated tests that use a fake model can verify deterministic orchestration,
but they do not prove that live Qwen behavior works. Any claim about the local
AI must also be supported by a real Ollama/Qwen test.

## Completed foundations

These foundations existed before the merged phase plan and should be preserved:

- Task and calendar CRUD with schemas, services, and database models.
- Task-linked calendar blocks and deterministic schedule preview/apply logic.
- Explainable deterministic priority scoring as an internal service.
- Ollama-backed chat and structured Qwen task interpretation.
- Confirmation-gated task creation and scheduling.
- Structured backend logging and an error reference.
- Dashboard and Tasks views backed by the local API.

## Phase 0 - Current AI and navigation stabilization

**Status: Completed**

This is a temporary checkpoint needed before StudentOS can produce an honest,
repeatable AI screenshot for the presentation phase. Do not add new AI action
types during this phase.

Scope:

- Prevent resolved clarification questions from repeating.
- Preserve explicit clarification facts such as date, duration, and start time
  when Qwen omits them from its revised structured output.
- Reproduce the reported `2 PM` start-time issue using the proposal payload,
  backend logs, and persisted calendar event before changing its logic.
- Preserve messages, proposal state, and an active request across client-side
  route navigation.
- Keep schedule placement separate from a task deadline.
- Verify that confirmation creates exactly one task and its intended linked
  calendar block.

Exit criteria:

- A real Qwen conversation can progress from an incomplete request through one
  blocking question at a time to a valid preview.
- Navigating away and back does not cancel or hide the active operation.
- The preview's date, start time, duration, and end time match the user's answers.
- Confirming once persists the expected task and calendar event without a
  duplicate.
- Freeze the accepted baseline model tag, canonical prompt, schema, inference
  settings, representative live-Qwen scenarios, and measured results so later
  LoRA experiments have a stable comparison point.
- Focused and complete checks pass, followed by helper-first explanation, quiz,
  explicit approval, and a dedicated baseline commit before Phase 1 or Phase 2
  work is treated as complete.

Baseline record: [`docs/validation/phase-0-ai-baseline.md`](validation/phase-0-ai-baseline.md)

## Phase 1 - StudentOS presentation

**Status: In progress**

This phase is paused at its AI screenshot checkpoint until Phase 0 is explained,
quizzed, approved, and committed. Finish this short presentation checkpoint
before beginning model-training experiments so the README documents a known
baseline rather than a moving target.

Scope:

- Finish the portfolio-focused README using only source- and test-verified claims.
- Make task creation read as a genuine back-and-forth conversation: render each
  blocking clarification as an assistant message before the user's answer, keep
  proposal and completion states visually associated with the assistant, and
  avoid a transcript made almost entirely of user messages.
- Preserve exactly one active clarification and do not duplicate questions,
  replay requests, or apply an action merely because chat history is restored.
- Add repository-tracked screenshots for the dashboard, Tasks page, and
  confirmation-ready AI task preview.
- Keep the architecture diagram, setup instructions, demonstration-data steps,
  limitations, and roadmap accurate.
- Identify placeholders and unfinished behavior instead of presenting them as
  complete features.

Exit criteria:

- Every README claim maps to current source code, tests, or observed behavior.
- Demonstration data is created through the backend rather than frontend-only
  fixtures.
- A task-creation transcript visibly alternates assistant questions and user
  answers, survives route navigation, and still creates at most one task after
  explicit confirmation.
- Backend tests, Python compilation, frontend lint/build, migrations, and
  repository checks pass.
- The user approves the completed presentation before it is committed or pushed.

## Phase 2 - Controlled AI evaluation and LoRA specialization

**Status: Planned**

Scope:

- Build a versioned evaluation harness around the frozen Phase 0 baseline. Record
  the model tag or digest, canonical prompt version, output schema, inference
  settings, backend revision, and dataset revision for every run.
- Define canonical task scenarios first, with reviewed structured outputs as the
  source of truth. Generate roughly 1,000 language variations from those
  scenarios, including incomplete requests, multi-turn clarifications,
  corrections, informal grammar, and selected multilingual or mixed-language
  examples. Do not turn these variations into new parser rules.
- Keep training, validation, and final test sets separate. Select configurations
  with validation data and reserve the final test set for the final comparison.
- Freeze the canonical prompt while comparing the base model with LoRA adapter
  candidates. After selecting a LoRA candidate, freeze that adapter before
  evaluating a small set of prompt candidates. Never change the adapter and
  prompt simultaneously when attributing an experimental result.
- Treat structured-schema validity, confirmation safety, absence of invented
  facts, and retention of previously confirmed state as hard gates rather than
  scores that stronger performance elsewhere can offset.
- Rank passing candidates with transparent weighted metrics: timing-field
  accuracy 30%, clarification accuracy 25%, proposal-state retention 20%,
  scheduling-mode accuracy 15%, and task-classification accuracy 10%. Also
  report each category separately.
- Repeat a representative reliability subset to measure intermittent success
  rates, while running the full held-out set for final comparisons.
- Use real user corrections for future training only through explicit opt-in,
  reviewable collection, data minimization and redaction, retention controls,
  and deletion support. Never silently collect prompts for training.

Exit criteria:

- The frozen baseline report is reproducible from a documented command and
  versioned dataset.
- The selected LoRA and prompt each win in a one-variable-at-a-time experiment.
- The final selected combination outperforms the baseline on the untouched test
  set, passes every safety gate, and succeeds in real Ollama/Qwen integration
  trials; fake-model orchestration tests alone are insufficient.
- If no candidate clears these gates, remain in Phase 2 and keep the Phase 0
  baseline rather than expanding AI write permissions.
- Results, limitations, helper-first implementation explanation, quiz, and
  explicit approval are completed before committing the selected AI setup.

## Phase 3 - AI update and reschedule actions

**Status: Planned; blocked by the Phase 2 quality gate**

This phase carries forward the update portion of the original Batch 5. It may
start only after the chosen AI configuration passes Phase 2.

Scope:

- Add separate preview, validation, and confirmation contracts for task updates.
- Add conflict-aware rescheduling previews.
- Recalculate immediately before apply and report stale conflicts safely.
- Replace client-trusted write proposals with server-owned proposal IDs or an
  equivalently tamper-resistant contract.
- Add idempotency so retries cannot duplicate or repeat an update.
- Never give the language model direct database-session access.

## Phase 4 - AI delete actions

**Status: Planned; blocked by Phase 3**

This phase carries forward the delete portion of the original Batch 6.

Scope:

- Add a delete preview showing the task and every linked calendar consequence.
- Require stronger, action-specific confirmation.
- Add ownership checks before enabling deletion outside the local prototype.
- Make retries idempotent and preserve an audit trail.
- Keep overdue handling recoverable and reviewable; do not silently delete
  missed tasks merely because their deadline passed.

## Phase 5 - Core workflow hardening

**Status: Planned**

This phase carries forward the remaining work from the original Batch 3.

Scope:

- Define Today's Tasks as due-today UNION scheduled-today, without duplicates.
- Display scheduled start/end separately from task deadlines in task-facing UI.
- Expand conflict, timezone, and midnight integration coverage.
- Design auditable overdue-task archival and missed-task reminders.
- Improve developer-only mutation logs so safe state changes such as
  `completed=true` and `completed=false` are distinguishable without logging
  task titles, descriptions, prompts, or other private content.

## Phase 6 - Priority-driven scheduling

**Status: Planned**

This phase carries forward the original Batch 4.

Scope:

- Connect deterministic priority ranking to multi-task scheduling order.
- Protect anchored events and explicit user-selected blocks.
- Preserve recovery buffers whenever feasible.
- Define urgent displacement rules and warnings.
- Use movable chores and then lower-priority work as explicit, reviewable
  sacrifice candidates when all available time is occupied.

## Phase 7 - GitHub Actions CI

**Status: Planned**

Scope:

- Run the backend test suite and Python compilation on supported Python versions.
- Run frontend dependency installation, ESLint, and the production build.
- Add migration and repository-integrity checks where appropriate.
- Keep CI claims out of documentation until the workflow passes on GitHub.

## Phase 8 - Reproducible Docker environment

**Status: Planned**

Scope:

- Add reviewed backend and frontend container definitions.
- Add Docker Compose for the verified local stack.
- Define health checks, persistent data behavior, startup ordering, and safe
  environment-variable examples.
- Decide explicitly how optional Ollama access works from containers.

## Phase 9 - Complete product surfaces and durable operations

**Status: Planned**

Scope:

- Finish the dedicated Calendar and Settings pages.
- Complete task creation/editing UI and remaining dashboard data wiring.
- Replace placeholder statistics, greeting, quote, and notifications with
  deliberately defined sources.
- Move chat history and pending AI operations from browser-only state to durable
  backend persistence when multi-device or reload survival is required.
- Treat different histories in separate browsers or browser profiles as an
  expected limitation until backend persistence is associated with an
  authenticated internal user ID; do not attempt to synchronize `localStorage`.
- Add a durable job model if AI generation must survive browser closure or
  backend restarts.

## Phase 10 - Security, authentication, ownership, and OAuth integrations

**Status: Planned**

This is the post-MVP security-learning phase and a mandatory gate before public
deployment. Use a deliberately selected subset of OWASP ASVS as the verification
checklist, document tradeoffs, and implement one security boundary at a time.

Scope:

- Write a lightweight threat model covering assets, trust boundaries, likely
  attackers, sensitive data, and abuse cases for the browser, API, database,
  Ollama integration, and future third-party providers.
- Choose and document an authentication design before implementation. Define
  registration, login, logout, recovery, verification, session expiry,
  revocation, and optional multi-factor authentication behavior.
- Give every account a stable, non-guessable internal user ID and link tasks,
  events, proposals, chat history, provider identities, and sessions to that ID.
  Do not use an email address or an OAuth provider's display name as the database
  ownership key.
- Prefer framework-supported, backend-managed sessions with cryptographically
  random opaque session tokens. Store only a protected token verifier such as a
  hash on the server, rotate the token after authentication or privilege changes,
  and support idle expiry, absolute expiry, individual revocation, and logout of
  all sessions.
- Keep browser credentials out of ordinary JavaScript-accessible storage. Review
  secure cookie or token handling, CSRF protection, CORS allowlists, TLS-only
  production behavior, and security headers as one coordinated design.
- Deliver the session identifier through a narrowly scoped `HttpOnly`, `Secure`,
  and deliberately selected `SameSite` cookie in production; never place session
  IDs, OAuth access tokens, or refresh tokens in `localStorage` or
  `sessionStorage`.
- Add per-user ownership for tasks, events, proposals, and chat history. Enforce
  authorization in the API and service layers with deny-by-default object-level
  access checks rather than relying on hidden frontend controls.
- Add negative authorization tests proving that anonymous users and one signed-in
  user cannot read, modify, schedule, or delete another user's records.
- Add session-lifecycle and browser-isolation tests proving that separate
  anonymous browsers remain isolated, the same authenticated user can retrieve
  backend-owned history in another authorized session, and expired, logged-out,
  or revoked sessions cannot continue accessing it.
- Add abuse controls appropriate to the deployment, including request-size
  limits and rate limits for login, AI generation, and write-heavy endpoints.
- Keep secrets out of Git and logs; define development and production secret
  storage, rotation, revocation, and incident-response procedures. Never log
  passwords, session identifiers, authorization codes, access tokens, refresh
  tokens, or OAuth callback parameters.
- Add automated dependency, secret, and security-focused checks to CI, with
  findings reviewed rather than presented as proof that the application is
  secure.
- Only after StudentOS identity and ownership boundaries pass review, integrate
  Canvas, Google Calendar, or Gmail using OAuth 2.0 Authorization Code with PKCE,
  exact registered redirect URIs, transaction-bound state or nonce protection,
  and the minimum necessary scopes.
- Protect provider tokens at rest, handle refresh and revocation safely, provide
  a visible disconnect operation, and define what happens to synchronized data
  when access is revoked.

Exit criteria:

- The threat model and selected OWASP ASVS controls are documented with evidence
  for each control that StudentOS claims to satisfy.
- Authentication, logout, expiry, revocation, CSRF/CORS behavior, and cross-user
  authorization tests pass, including failure-path tests.
- OAuth callback validation rejects mismatched state, invalid redirect behavior,
  reused or invalid authorization responses, and unnecessarily broad scopes.
- A review finds no committed secrets or intentionally logged credentials, and
  documented recovery and token-revocation procedures have been exercised in a
  local or staging environment.
- Public deployment remains blocked until the security gate is explicitly
  reviewed and approved.

## Phase 11 - Project Sentinel integration

**Status: Planned**

Scope:

- Define Project Sentinel's monitoring contract against real StudentOS health
  and operational signals.
- Demonstrate local outage detection, recovery detection, and useful diagnostics.
- Document measured evidence without inventing uptime or reliability metrics.

## Phase 12 - Public deployment

**Status: Planned**

Scope:

- Deploy only after authentication, ownership, secrets handling, migrations,
  health checks, and recovery behavior have been reviewed.
- Verify the public frontend, API, database persistence, and any chosen AI
  provider boundary.
- Document costs and resource limits honestly, especially for AI inference.

## Phase 13 - Resume and LinkedIn evidence

**Status: Planned**

Scope:

- Update resume and LinkedIn descriptions only with implemented and verified
  technologies, workflows, and results.
- Link to the repository, screenshots, CI evidence, and live deployment only
  after each is genuinely available.
- Do not invent users, usage numbers, uptime, performance gains, or professional
  experience.

## Bug-fix detour rule

A discovered bug belongs to the earliest phase whose exit criteria it blocks.
Fix and verify that bug before moving forward, but do not use it as permission to
start unrelated features. Record the issue, evidence, fix, tests, and remaining
limitations under the active phase. If the bug changes architecture or expands
scope materially, revise this document with the user's approval.
