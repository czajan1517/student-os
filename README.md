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

## Project Structure

The application uses a modular architecture separating:

- React pages and reusable UI components
- Frontend API services
- FastAPI routers and services
- Database models and persistence

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

## Status

🚧 **Work in Progress**

Currently working on connecting live task and calendar data to the dashboard and building the remaining application pages.
