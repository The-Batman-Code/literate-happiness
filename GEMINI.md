# Project Overview

This is a production-grade FastAPI boilerplate with a Google ADK multi-agent architecture. This project demonstrates best practices for building scalable AI agent systems with FastAPI, including layered services, repositories, and proper resource management.

The project uses `uv` for package management and is built with Python 3.13+.

## Building and Running

### Prerequisites

- Python 3.13+
- `uv` package manager

### Setup

1.  **Clone the repository**
2.  **Install dependencies:**
    ```bash
    uv sync
    ```
3.  **Run the application:**
    ```bash
    uv run uvicorn src.app.main:app --reload
    ```

The application will be available at `http://localhost:8000`.

### Running Tests

To run the test suite, use the following command:

```bash
uv run pytest
```

### Linting

To check for linting errors, run:

```bash
uv run ruff check .
uv run black --check .
```

To fix linting errors, run:

```bash
uv run ruff check . --fix
uv run black .
```

## Development Conventions

- **Architecture:** The project follows a layered architecture with a clear separation of concerns:
    - `api`: API routes and endpoints.
    - `services`: Business logic layer.
    - `repositories`: Data access abstraction layer.
    - `models`: SQLAlchemy ORM models.
    - `schemas`: Pydantic models for API request/response.
- **Dependency Injection:** Services are injected into the API routes using FastAPI's `Depends()` function.
- **Configuration:** Application settings are managed using Pydantic's `BaseSettings` and loaded from environment variables.
- **Logging:** Centralized logging is configured using Loguru, with different configurations for development and production environments.
- **Package Management:** Project dependencies are managed with `uv` and defined in `pyproject.toml`.
- **Agents:** The project uses a multi-agent architecture with Google ADK.
- **Database:** The project is set up to use a database, likely PostgreSQL, with SQLAlchemy as the ORM. The models are defined in `src/app/models` and the repositories in `src/app/repositories/db`.
- **Cache:** The project is set up to use Redis for caching. The cache repositories are defined in `src/app/repositories/redis`.
