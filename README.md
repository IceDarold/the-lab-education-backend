# The Lab Academy Backend

A backend for a full-stack interactive learning platform focused on programming and technology education. It ships with a FastAPI REST API, Supabase-backed authentication and persistence, and everything needed to power hands-on lessons, quizzes, progress tracking, and administrative tooling.

## 🚀 Features

### For Students
- **Interactive Learning**: Structured courses, modules, and lessons that can be rendered by the frontend as an immersive learning flow.
- **Hands-on Coding**: Endpoints exist for submitting code, validating quizzes, and marking lessons complete, letting the frontend mirror a live coding environment.
- **Progress Tracking**: Course and lesson progress is calculated on the backend and exposed through the dashboard endpoints.
- **Quizzes and Assessments**: REST routes for validating quiz answers and reporting results in real time.
- **Personal Dashboard**: APIs expose enrolled courses with completion metrics, providing the data backbone of a dashboard experience.
- **Secure Authentication**: JWT authentication, password reset flows, and refresh token rotation are all implemented via FastAPI and Supabase.

### For Administrators
- **Content Management**: Admin APIs cover content-tree retrieval, config files, creation, updates, and deletions of courses, modules, and lessons.
- **Lesson Editor Support**: Endpoints exist for retrieving and updating raw lesson markup, giving an editor a backend to persist changes.
- **User Analytics**: Activity log endpoints track events such as lesson completions and quiz attempts for auditing and analytics.
- **Structured Content**: Courses → modules → lessons is enforced through database relations and exposed via API responses.

### Platform Features
- **Responsive-ready**: Designed to integrate with modern frontends that are optimized for desktop and mobile.
- **Real-time Analytics**: Activity events are ingestible through the `/activity-log` routes.
- **Modern UI/UX Support**: The backend is ready for any UI stack (React, Next.js, Vite, etc.) that consumes the documented schemas.
- **Robust Error Handling**: FastAPI-based validation and error responses ensure clients receive consistent status codes and payloads.

## 🛠 Tech Stack

### Backend
- **FastAPI (Python)** — High-performance async framework with automatic docs.
- **Pydantic** — Request and response validation.
- **SQLAlchemy** — ORM for PostgreSQL.
- **Alembic** — Database migrations.
- **Supabase** — Hosted PostgreSQL, Auth, and storage.
- **Poetry** — Python dependency management.

### Development Tools
- **Poetry scripts** — Manage migrations, application startup, and testing.
- **Pytest** — Unit and integration testing.
- **Ruff** — Linting.

## 📋 Prerequisites

- Python >= 3.12
- Poetry
- Git
- Supabase account (for Auth + managed PostgreSQL; optional if you run locally via Docker)

## 🛠 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd the-lab-education-backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Fill `.env` with your Supabase credentials, JWT secrets, and database URL.

## 🏃 Running the Application

### Development

1. **Apply database migrations**
   ```bash
   poetry run alembic upgrade head
   ```

2. **Start the FastAPI app**
   ```bash
   poetry run uvicorn src.main:app --reload
   ```
   API is reachable at `http://localhost:8000`.

3. **API docs**
   - Swagger UI: `http://localhost:8000/docs`
   - Redoc: `http://localhost:8000/redoc`

### Production-ready

- Use `poetry run alembic upgrade head` during deploy.
- The `vercel.json` exists for serverless deployments (e.g., Vercel, Render, Fly.io, Railway).
- Ensure environment variables listed under `.env.example` are populated on the host.

## 🧪 Testing

```bash
poetry run pytest
```

## 🔧 API Documentation

Detailed endpoint information lives in [`docs/api_endpoints.md`](docs/api_endpoints.md). Key base URL segments:

- Base URL: `/api/v1`
- Authentication: `Bearer` JWT tokens
- Content-Type: `application/json`
- Primary resources: `/auth`, `/courses`, `/dashboard`, `/lessons`, `/activity-log`, `/api/admin`

## 🚢 Deployment

### Backend Hosts
- **Vercel** — Use serverless functions together with `vercel.json`.
- **Render / Fly.io / Railway** — Run the FastAPI app in their Python runtimes or custom containers.

### Environment Variables

Set these for production:

```env
APP_NAME=the-lab-education-backend
DEBUG=false
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://example.supabase.co
SUPABASE_KEY=public-anon-key
SUPABASE_SERVICE_ROLE_KEY=service-role-key
```

## 🤝 Contributing

1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Implement your changes and run `poetry run pytest`.
4. Lint with `ruff check` if applicable.
5. Commit, push, and open a pull request.

## 📄 License

MIT License — see the [LICENSE](LICENSE) file.

## 📞 Support

- Check the [API documentation](docs/api_endpoints.md)
- Open an issue on GitHub
- Contact the maintainers via the repository channels

Happy Learning! 🎓
