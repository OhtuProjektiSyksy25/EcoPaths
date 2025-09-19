# Stage 1: Build the frontend
FROM node:20 AS frontend

WORKDIR /app

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ ./

ENV REACT_APP_API_URL=http://localhost:8000

RUN npm run build:ui

# Stage 2: Build the backend
FROM python:3.11-slim AS backend

RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY backend/pyproject.toml backend/poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY backend/ ./

COPY --from=frontend /app/build ./frontend

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
