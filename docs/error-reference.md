# StudentOS Error Reference

Use this reference when an API request fails or a named backend exception appears
in a traceback. It maps the error visible to the frontend to the layer and file
that should be inspected first.

## How to investigate an error

Record these three pieces of information before changing code:

1. The request endpoint, such as `POST /schedule/apply`.
2. The HTTP status, such as `409`.
3. The response `detail` or traceback message.

Then use the tables below to locate the error. Start at the file in **Look here
first**. If that file only converts an exception into an HTTP response, continue
to the source file listed in **Raised by**.

Do not treat every non-`200` response as a backend defect. A `404`, `409`, or
`422` can be an expected rejection of invalid or impossible input.

## Error layers

| Layer | Responsibility | Typical failure | Main location |
| --- | --- | --- | --- |
| Schema | Validates request and response shapes | Missing field, invalid enum, negative duration | `backend/schemas/` |
| API router | Converts application errors into HTTP responses | `404`, `409`, `422`, `502`, `503` | `backend/api/` |
| Service | Enforces calendar, priority, and scheduling rules | Missing relationship, completed task, impossible schedule | `backend/services/` |
| AI integration | Calls OpenAI and parses structured output | Missing key, upstream failure, invalid model output | `backend/ai/` |
| Database | Persists tasks and events | Constraint, connection, or transaction failure | `backend/database/` and migrations |

## HTTP status quick reference

| Status | Meaning in StudentOS | First place to inspect |
| --- | --- | --- |
| `404 Not Found` | The requested task or calendar event does not exist | The endpoint in `backend/api/` and the ID sent by the caller |
| `409 Conflict` | Valid input could not be applied because the requested schedule is infeasible | `backend/services/schedule_service.py` and the returned preview |
| `422 Unprocessable Content` | The request shape or domain values are invalid | `backend/schemas/`, then the relevant service |
| `502 Bad Gateway` | OpenAI did not provide a usable classification | `backend/ai/task_classifier.py` |
| `503 Service Unavailable` | The AI integration is not configured | Backend environment variables and `backend/ai/task_classifier.py` |
| `500 Internal Server Error` | An unexpected exception escaped the known handlers | Backend traceback; begin at the deepest StudentOS file in the traceback |

## Task errors

### `404` — `Task not found`

- **Seen from:** `GET`, `PUT`, or `DELETE /tasks/{task_id}`
- **Meaning:** No task exists with the requested ID.
- **Look here first:** `backend/api/tasks.py`
- **Raised by:** The router after `TaskService` returns `None`.
- **Check:** Confirm the ID, confirm the task was not deleted, and inspect the
  configured database rather than assuming the frontend and backend use the same
  database file.

### Automatic task request validation — `422`

- **Seen from:** `POST /tasks` or `PUT /tasks/{task_id}`
- **Meaning:** FastAPI/Pydantic rejected the request before the service ran.
- **Look here first:** `backend/schemas/task.py`
- **Common causes:**
  - Empty or overlong title.
  - Unknown priority, task type, or effort value.
  - `estimated_time` is not between 1 and 1440 minutes.
  - `recovery_buffer_minutes` is not between 0 and 120 minutes.
- **Check:** Read the `detail[].loc` and `detail[].msg` values in the response.
  They identify the invalid field.

## Calendar errors

### `404` — `Event not found`

- **Seen from:** `GET`, `PUT`, or `DELETE /calendar_events/{calendar_event_id}`
- **Meaning:** No calendar event exists with the requested ID.
- **Look here first:** `backend/api/calendar.py`
- **Raised by:** The router after `CalendarEventService` returns `None`.
- **Check:** Confirm the event ID and whether deleting its related task already
  removed the event through the task/calendar cascade relationship.

### `422` — `Linked task was not found`

- **Seen from:** `POST /calendar_events` or `PUT /calendar_events/{id}`
- **Meaning:** The event includes a `task_id`, but that task does not exist.
- **Look here first:** `backend/services/calendar_service.py`
- **Translated by:** `backend/api/calendar.py`
- **Check:** Fetch the task first. Use `task_id: null` only when the item is an
  independent calendar event rather than a scheduled block for a task.

### `422` — `End date must be later than the start date`

- **Seen from:** Creating or updating a calendar event.
- **Meaning:** `end_date <= start_date`.
- **Look here first:**
  - Create validation: `backend/schemas/calendar.py`
  - Partial update validation: `backend/services/calendar_service.py`
- **Why there are two checks:** A create request contains both dates, while an
  update may contain only one date and must be compared with the stored value.
- **Check:** Confirm the date, time, timezone offset, and AM/PM conversion.

### Other automatic calendar validation — `422`

- **Look here first:** `backend/schemas/calendar.py`
- **Common causes:** Invalid priority, non-positive `task_id`, empty title, or a
  recovery buffer outside 0 to 240 minutes.

## Scheduling errors

### `ScheduleTaskNotFoundError` / `404` — `Task not found`

- **Seen from:** `POST /schedule/preview` or `POST /schedule/apply`
- **Meaning:** The scheduling request refers to a missing task.
- **Raised by:** `backend/services/schedule_service.py`
- **Translated by:** `backend/api/schedule.py`
- **Check:** Confirm `request.task_id` and verify the task was not deleted between
  preview and apply.

### `ScheduleValidationError` / `422` — `Completed tasks cannot be scheduled`

- **Meaning:** The requested task is already completed.
- **Raised by:** `backend/services/schedule_service.py`
- **Translated by:** `backend/api/schedule.py`
- **Check:** Reopen the task only if rescheduling a completed task is intentional;
  otherwise do not send it to the scheduler.

### `ScheduleValidationError` / `422` — timezone style mismatch

- **Visible message:** `Task deadline and schedule window must use the same timezone style`
- **Meaning:** One datetime has a timezone offset and the other is timezone-naive.
- **Raised by:** `backend/services/schedule_service.py`
- **Check:** Send all related datetimes consistently, preferably with explicit
  timezone offsets.

### Automatic schedule request validation — `422`

- **Look here first:** `backend/schemas/schedule.py`
- **Possible messages:**
  - `Window end must be later than window start`
  - `Day end must be later than day start`
  - `Maximum block length must be at least the minimum block length`
  - `Schedule window datetimes must use the same timezone style`
- **Other common causes:** Non-positive task ID or block/buffer values outside
  their declared limits.

### `ScheduleConflictError` / `409`

- **Visible message:** `The task cannot be fully scheduled in the requested window`
- **Seen from:** `POST /schedule/apply`
- **Meaning:** The request is valid, but available time is insufficient. This is
  an expected domain conflict, not necessarily a software defect.
- **Raised by:** `backend/services/schedule_service.py`
- **Translated by:** `backend/api/schedule.py`
- **Important response data:** `detail.preview` contains available time, proposed
  blocks, unscheduled minutes, and warnings.
- **Check:** Inspect `unscheduled_minutes`, the task deadline, locked events,
  working hours, recovery buffers, and minimum block size.

## Priority errors

Priority errors currently use built-in `ValueError` and are primarily visible to
backend callers and tests. If priority analysis becomes a public endpoint, give
these errors named exception classes and explicit API mappings.

### `Completed tasks are not eligible for priority analysis`

- **Raised by:** `backend/services/priority_service.py`
- **Meaning:** Priority analysis was called directly with a completed task.
- **Check:** Filter completed tasks before calling `analyze_task()`.

### `Scheduled minutes cannot be negative`

- **Raised by:** `backend/services/priority_service.py`
- **Meaning:** The caller supplied invalid allocation data.
- **Check:** Inspect the calculation that totals linked calendar block durations.

### `Priority timestamps must use the same timezone style`

- **Raised by:** `backend/services/priority_service.py`
- **Meaning:** The comparison mixes timezone-aware and timezone-naive datetimes.
- **Check:** Normalize the supplied `now` value and the task's `created_at` value.

## AI errors

### `AIConfigurationError` / `503`

- **Visible message:** `OPENAI_API_KEY is not configured on the backend`
- **Seen from:** `POST /ai/tasks/classify`
- **Meaning:** The key is empty, missing, or still set to the example placeholder.
- **Raised by:** `backend/ai/task_classifier.py`
- **Translated by:** `backend/api/ai.py`
- **Check:** Configure `OPENAI_API_KEY` in the backend environment. Do not place
  the key in frontend code or commit it to Git.

### `TaskClassificationError` / `502` — request failed

- **Visible message:** `The task classification request failed`
- **Meaning:** The OpenAI SDK raised `OpenAIError`, or the structured response
  failed Pydantic validation.
- **Raised by:** `backend/ai/task_classifier.py`
- **Translated by:** `backend/api/ai.py`
- **Check:** Inspect the chained backend traceback for the original exception.
  Then check network access, model access, request limits, model configuration,
  and whether the response still matches `backend/schemas/ai.py`.

### `TaskClassificationError` / `502` — no parsed classification

- **Visible message:** `The model did not return a task classification`
- **Meaning:** The API call completed without a usable `output_parsed` value.
- **Raised by:** `backend/ai/task_classifier.py`
- **Check:** Inspect the raw response during backend debugging for refusal or
  incomplete output, without exposing sensitive task content in user-facing logs.

## Warnings are not exceptions

`SchedulePreview.warnings` reports compromises or useful scheduling information.
The preview endpoint can return `200` while including warnings.

| Warning | Meaning | Suggested action |
| --- | --- | --- |
| `The task already has enough future time allocated` | Existing linked blocks already cover the estimated duration | Do not add duplicate blocks |
| `Recovery buffers were reduced to protect the deadline` | Full buffers made the task less feasible | Show the compromise to the user |
| `The scheduling window was limited by the task deadline` | Scheduling stopped at the deadline | Do not assume the full requested window was used |
| `<n> minutes could not be scheduled in this window` | Some required work remains unallocated | Expand the window, move flexible work, or ask the user |

## Unexpected `500` errors

An unexpected `500` is not intentionally produced by the current routers. It
usually means an exception escaped the documented handlers.

Investigation order:

1. Read the backend traceback from the bottom upward.
2. Find the deepest frame inside `backend/`.
3. Identify whether the failure occurred in a schema, API, service, AI, or
   database file.
4. Record the endpoint and sanitized request data needed to reproduce it.
5. Add a regression test before fixing it.
6. If the failure is an expected domain condition, introduce a named exception,
   map it to an appropriate HTTP status, and add it to this reference.

Never return raw tracebacks, API keys, database URLs, or private task content to
the frontend.

## Adding a new documented error

When adding a new expected error:

1. Name it after the domain and condition, such as `ScheduleConflictError`.
2. Raise it in the service or integration layer that detects the condition.
3. Convert it to an HTTP response in the relevant API router.
4. Add a test for the service behavior and API response.
5. Add the visible message, status, source file, and first debugging action here.

Prefer this naming pattern:

```text
<Domain><Condition>Error
```

Examples:

```text
ScheduleConflictError
ScheduleValidationError
AIConfigurationError
TaskClassificationError
```

Avoid creating a new exception when the condition is merely a preview warning or
when Pydantic already provides the correct request validation.

## Future improvement: stable API error codes

The current API primarily returns a status and human-readable `detail`. As the
frontend grows, add stable machine-readable codes so frontend behavior does not
depend on matching English sentences.

Proposed response shape:

```json
{
  "detail": {
    "code": "SCHEDULE_CONFLICT",
    "message": "The task cannot be fully scheduled in the requested window",
    "context": {
      "task_id": 42
    }
  }
}
```

This is a documented future direction and is not yet implemented.
