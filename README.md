# Kariko — Backend

Django REST API for the Kariko to-do application.

## Tech Stack

- **Python** 3.11+ / **Django** 5.0
- **Django REST Framework** — API layer
- **SimpleJWT** — access + refresh token authentication with OTP login
- **PostgreSQL** 16 — primary database
- **Docker / Docker Compose** — containerized development and production

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose

### Run with Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Run locally

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/development.txt

# Configure environment
cp .env.example .env  # then edit .env

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for development |
| `DATABASE_URL` | PostgreSQL connection string |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |

## Project Structure

```
apps/
  accounts/   # User model, OTP + password auth, JWT tokens
  tasks/      # Task and Step models, CRUD endpoints
  lists/      # Task list management
  sync/       # WatermelonDB sync endpoint (pull/push)
common/       # Shared utilities and base classes
config/       # Django settings (base, dev, prod)
requirements/ # Pinned dependencies (base, development, production)
tests/        # Project-level tests
```

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/otp/request/` | Request OTP |
| `POST` | `/api/v1/auth/otp/verify/` | Verify OTP → tokens |
| `POST` | `/api/v1/auth/password/login/` | Password login → tokens |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh access token |
| `DELETE` | `/api/v1/auth/logout/` | Revoke refresh token |
| `GET/PATCH` | `/api/v1/users/me/` | Current user profile |
| `GET` | `/api/v1/sync/` | Pull changes |
| `POST` | `/api/v1/sync/` | Push changes |

## Running Tests

```bash
pytest
```
