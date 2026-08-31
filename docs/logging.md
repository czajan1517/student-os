# StudentOS Logging

StudentOS writes operational logs to the backend console and, by default, to
`logs/studentos.log`. The file rotates at 2 MB and retains five older files so
development logs cannot grow forever.

## Configuration

The following `.env` values control logging:

```env
STUDENTOS_LOG_LEVEL=INFO
STUDENTOS_LOG_FILE=logs/studentos.log
```

Use `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` for the level. An invalid
value safely falls back to `INFO`. Set `STUDENTOS_LOG_FILE` to an empty value to
disable file output while keeping console output.

## Recorded events

The initial logging system records:

- HTTP method, path, status, duration, and a generated request ID;
- Ollama model requests, completion time, and safe failure categories;
- AI task proposal readiness and confirmed application;
- successful, missing, and failed task and calendar mutations;
- schedule preview feasibility, conflicts, and applied block counts.

Every HTTP response includes `X-Request-ID`. This makes it easier to match a
frontend failure with its backend request log.

## Privacy rules

Do not add the following values to log messages:

- prompts, chat messages, task titles, or task descriptions;
- API keys, passwords, cookies, or authorization headers;
- complete request or response bodies;
- personal information that is not needed to diagnose the event.

Prefer IDs, counts, types, result states, durations, and exception categories.
Operational logs explain why the application failed; they are not a permanent
audit record of who changed data. User-linked audit history should be added only
after authentication and task ownership are implemented.
