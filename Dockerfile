# Stage 1 - build the frontend
FROM node:20 AS frontend

WORKDIR /app

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ ./

RUN npm run build:ui

# Stage 2 - build the backend
FROM python:3.11-slim AS backend

RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

ENV POETRY_HOME=/opt/poetry

ENV PATH="$POETRY_HOME/bin:$PATH"

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

RUN mkdir -p backend

COPY backend/pyproject.toml backend/poetry.lock* ./backend/

RUN cd backend && poetry install --no-interaction --no-ansi --no-root --with dev

COPY backend/ ./backend/

COPY tasks.py ./tasks.py

RUN mkdir -p backend/build

COPY --from=frontend /app/build ./backend/build

COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod a+x /app/docker-entrypoint.sh 

RUN chmod -R a+rwX /app

ENV PYTHONPATH="${PYTHONPATH}:/app:/app/backend/src"

WORKDIR /app/backend

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]