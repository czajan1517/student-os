# StudentOS

StudentOS is a full-stack student productivity application I'm building to combine task management, scheduling, progress tracking, and AI-assisted study tools into one workspace.

The project is currently under active development.

## Tech Stack

**Frontend**
- React
- Tailwind CSS
- React Router
- Vite

**Backend**
- Python
- FastAPI
- SQLAlchemy
- SQLite

## Current Features

- Task CRUD system
- Calendar event CRUD system
- Dashboard interface
- Sidebar navigation and page routing
- Reusable React component architecture
- Frontend and backend API integration
- Local AI chat, task classification, and confirmed task creation through Ollama

## Project Structure

The application uses a modular architecture separating:

- React pages and reusable UI components
- Frontend API services
- FastAPI routers and services
- Database models and persistence

## Developer References

- [Error reference](docs/error-reference.md) — maps API errors and backend
  exceptions to their source, meaning, and first debugging steps.
- [Logging reference](docs/logging.md) — explains the operational events,
  configuration, request IDs, and privacy rules used by backend logs.

## Database Setup

StudentOS uses Alembic for database migrations. After installing the Python
dependencies, prepare a new database with:

```bash
python -m alembic upgrade head
```

Existing databases created before Alembic was introduced must be stamped at
the initial schema once before upgrading:

```bash
python -m alembic stamp 25b9c5e2c8ce
python -m alembic upgrade head
```

## Local AI Setup

StudentOS uses Ollama for local AI. The task, calendar, priority, and scheduling
features do not depend on Ollama and continue to work when it is stopped.

1. Install [Ollama for Windows](https://ollama.com/download/windows).
2. Download the local models. StudentOS uses the lightweight Llama model for
   responsive chat and keeps Qwen for structured task analysis:

```powershell
ollama pull llama3.2:1b
ollama pull qwen3:4b
```

3. Copy `.env.example` to `.env` if a local `.env` does not already exist.
4. Start the backend after Ollama is running.

The backend connects to `http://127.0.0.1:11434` by default. No API key is
required. Chat and classification remain read-only. AI task creation uses two
separate requests so interpretation cannot write by itself:

1. `POST /ai/actions/tasks/preview` returns a validated task proposal without
   changing the database.
2. `POST /ai/actions/tasks/apply` accepts that proposal only with
   `confirmed: true`, then delegates creation to `TaskService`.

Update, delete, and scheduling actions are not enabled for AI. Authentication
and per-user ownership must be added before this confirmation flow is exposed
outside the local single-user development environment.

## Status

🚧 **Work in Progress**

Currently working on connecting live task and calendar data to the dashboard and building the remaining application pages.
