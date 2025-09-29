# EcoPaths

| CI/CD | Main Coverage | Dev Coverage |
|-------|-----------------|----------------|
| [![CI/CD](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml) | [![Main Coverage](https://codecov.io/gh/OhtuProjektiSyksy25/EcoPaths/branch/main/graph/badge.svg)](https://app.codecov.io/github/OhtuProjektiSyksy25/EcoPaths) | [![Dev Coverage](https://codecov.io/gh/OhtuProjektiSyksy25/EcoPaths/branch/dev/graph/badge.svg)](https://app.codecov.io/github/OhtuProjektiSyksy25/EcoPaths) |

## Overview
EcoPaths is a project related to the course Software Engineering Project at the University of Helsinki. 

The web application aims to provide routes based on air quality for pedestrians and cyclists. The project is done in collaboration with MegaSense Oy.

## Installation

### Frontend Setup

#### Prerequisites

- Node.js
- Git



#### Install frontend

1. **Clone the repository and switch to the frontend folder**
   ```bash
   git clone https://github.com/OhtuProjektiSyksy25/EcoPaths
   cd EcoPaths/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up `.env` file for frontend**

- Copy the example file to `.env`:

```bash
cp .env_example .env
```

- Edit `.env` with your own values:
```bash 
REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
REACT_APP_API_URL=http://localhost:3000
REACT_APP_MAPBOX_STYLE=mapbox://styles/mapbox/streets-v11

```

> **Note:**
> 
> - Keep this file secret if it contains private tokens.
> - You can also set these variables as environment variables instead of using `.env`.
> - For full details and comments, see [.env_example](https://github.com/OhtuProjektiSyksy25/EcoPaths/blob/dev/frontend/.env_example)


### Backend setup

#### Prerequisites

- Poetry

#### Install backend

1. **Change directory to backend**
   ```bash
   cd ../backend
   ```

2. **Create and activate virtual environment**
   ```bash
   poetry shell
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

## Startup

### Quick Start (Full Application)
Runs both backend and frontend concurrently.

1. Activate backend virtual environment, if not already activated
```bash
cd backend
poetry shell
cd ..
```

2. Start full development environment
```bash
invoke run-all
```

> Backend: http://127.0.0.1:8000  
> Frontend: http://localhost:3000  

Press **Ctrl+C** to stop both servers.

---



### Run Backend and Frontend seperatly

> **Note:** Make sure the backend virtual environment is activated and always run `invoke` commands from the root directory. See [Notes / Tips](#notes--tips) for full instructions.

#### Start only backend
```bash
invoke run_backend
```

> Backend runs in development mode (`uvicorn src.main:app --reload`).  

---

#### Start only frontend
```bash
invoke run_frontend
```

> Frontend runs in development mode (`npm start`).  

---



## Testing

> **Note:** Make sure the backend virtual environment is activated and always run `invoke` commands from the root directory. See [Notes / Tips](#notes--tips) for full instructions.

### Backend tests
Run backend unit tests with coverage:
```bash
invoke test_backend
```

### Frontend tests
Run frontend unit tests with coverage (currently not available):
```bash
invoke test_frontend
```

### Full coverage
Run all unit tests and generate coverage reports:
```bash
invoke coverage
```

## Robot testing

### Install robot framework

```bash
npm run install-robot
```


### Running tests

1. **Start the app on terminal 1**
```bash
npm start
```

2. **Run tests on terminal 2**
```bash
npm run test:robot
```
or
```bash
npm run test:robot:headless
```

### Notes / Tips

- **Backend virtual environment:** Make sure the backend virtual environment is activated before running any `invoke` commands:
  ```bash
  cd backend
  poetry shell
  cd ..
  ```

- **Run commands from root:** Always run `invoke` commands from the root directory (`EcoPaths`), not from inside `backend/` or `frontend/`.
- **Coverage reports:** Are generated in `coverage_reports/`:
  - **Backend:** `coverage_reports/backend/`
  - **Frontend:** `coverage_reports/frontend/`

- **Port conflicts:** If ports 8000 (backend) or 3000 (frontend) are already in use, stop existing processes first. 
- **Stopping servers/tests:** Use **Ctrl+C** to stop any running processes cleanly.

## Documentation

- [Product backlog](https://github.com/orgs/OhtuProjektiSyksy25/projects/1)  
- [Sprint task board](https://github.com/orgs/OhtuProjektiSyksy25/projects/5/views/4)

## License

This project is licensed under the MIT License.