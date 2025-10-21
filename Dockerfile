# Stage 1 - build the frontend
FROM node:20 AS frontend

WORKDIR /app

COPY frontend/package*.json ./

RUN npm install

COPY frontend/ ./

ARG REACT_APP_MAPBOX_TOKEN=dev-default-token
ARG REACT_APP_MAPBOX_STYLE=dev-style
ARG REACT_APP_API_URL=https://ecopaths-ohtuprojekti-staging.ext.ocp-test-0.k8s.it.helsinki.fi

ENV REACT_APP_MAPBOX_TOKEN=$REACT_APP_MAPBOX_TOKEN
ENV REACT_APP_MAPBOX_STYLE=$REACT_APP_MAPBOX_STYLE
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build:ui

# Stage 2 - build the backend
FROM python:3.11-slim AS backend

RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

ENV POETRY_HOME=/opt/poetry

ENV PATH="$POETRY_HOME/bin:$PATH"

ENV POETRY_VIRTUALENVS_IN_PROJECT=true

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

ARG GOOGLE_API_KEY
ENV GOOGLE_API_KEY=$GOOGLE_API_KEY

COPY backend/pyproject.toml backend/poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY backend/ ./

COPY --from=frontend /app/build ./build

RUN chmod -R a+rwX /app

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
