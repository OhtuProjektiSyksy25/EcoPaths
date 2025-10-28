# EcoPaths

| CI/CD | Main Coverage | Dev Coverage |
|-------|-----------------|----------------|
| [![CI/CD](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml) | [![Main Coverage](https://codecov.io/gh/OhtuProjektiSyksy25/EcoPaths/branch/main/graph/badge.svg)](https://app.codecov.io/github/OhtuProjektiSyksy25/EcoPaths) | [![Dev Coverage](https://codecov.io/gh/OhtuProjektiSyksy25/EcoPaths/branch/dev/graph/badge.svg)](https://app.codecov.io/github/OhtuProjektiSyksy25/EcoPaths) |

## Overview
EcoPaths is a project related to the course Software Engineering Project at the University of Helsinki. 

The web application aims to provide routes based on air quality for pedestrians and cyclists. 

The project is done in collaboration with MegaSense Oy.

## Installation

### Frontend Setup

#### Prerequisites

- Node.js v20 or newer

#### Install frontend

1. **Clone the repository and navigate to the frontend directory**
   ```bash
   git clone https://github.com/OhtuProjektiSyksy25/EcoPaths
   cd EcoPaths/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure enviromental variables**

   Copy the example file to `.env`:
   
   ```bash
   cp .env_example .env
   ```
   
   Edit `.env` with your own values:

   ```bash 
   REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_MAPBOX_STYLE=mapbox://styles/mapbox/streets-v11
   ```

> **Note:**
> 
> - Keep this file secret if it contains sensitive tokens.
> - You may also set these variables directly in your shell environment.
> - See [.env_example](https://github.com/OhtuProjektiSyksy25/EcoPaths/blob/dev/frontend/.env_example) for details.


### Backend setup

#### Prerequisites

- Poetry

#### Install backend

1. **Navigate to the backend directory**
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

4. **Configure enviromental variables**

   Copy the example file to `.env`:

   ```bash
     cp env_example .env
   ```

   Edit `.env` with your own values:

   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=pathplanner
   DB_PASSWORD=sekret
   DB_NAME=ecopaths
   ```

   These values must match your Docker PostgreSQL setup and any external API keys you use.

### Database Setup

   EcoPaths uses a PostgreSQL database with PostGIS extensions to store spatial data.

#### Prerequisites

- Docker and Docker Compose installed
- `.env` and `.env.test` configured in backend/

####  Docker-Based Setup

1. **Create test environment file**

   In `backend/`, create `.env.test`:
   ```env
      DB_HOST=127.0.0.1
      DB_PORT=5432
      DB_USER_TEST=pathplanner
      DB_PASSWORD_TEST=sekret
      DB_NAME_TEST=ecopaths_test
      TEST_AREA=testarea
      NETWORK_TYPE=walking
   ```


2. **Start Docker and initialize databases**

   From the project root (EcoPaths/), run:
   ```bash
   bash setup.sh
   ```
This script will:

   - Start the Docker container

   - Wait for PostgreSQL to be ready

   - Populate the development database (ecopaths) with default area berlin

   - Populate the test database (ecopaths_test) with default area testarea


### Populate the Database manually

If you want to populate a different area or rerun table setup:
   1. **Navigate to the project root directory `(EcoPaths/)`.**

   2. **Run the invoke task**

      ```bash
      invoke reset-and-populate-area --area=your_area --network-type=walking
      ```
      To target the test database:
      ```bash
      invoke reset-and-populate-area --area=your_area --network-type=walking
      ```

These commands will drop and create all tables related to given area, download and process OpenStreetMap data, generate the edge and grid layers, and store them in the configured database. You can replace `your_area` with any area defined in `AREA_SETTINGS`.


> **Note:**
> - All database operations use `DatabaseClient`
> - Test database is isolated from production
> - `testarea` is preconfigured for quick testing
> - Make sure the backend virtual environment is activated and always run `invoke` commands from the root directory. See [Notes / Tips](#notes--tips) for full instructions.

## Startup

### Quick Start (Run Full Stack)
Runs both backend and frontend concurrently.

1. Activate backend virtual environment, if not already activated
```bash
cd backend
poetry shell
cd ..
```

2. Start both frontend and backend
```bash
invoke run-all
```

> Backend: http://localhost:8000  
> Frontend: http://localhost:3000  

Press **Ctrl+C** to stop both servers.

---





### Run Backend and Frontend seperatly

> **Note:** Make sure the backend virtual environment is activated and always run `invoke` commands from the root directory. See [Notes / Tips](#notes--tips) for full instructions.

#### Start only backend
```bash
invoke run-backend
```

> Backend runs in development mode (`uvicorn src.main:app --reload`).  

---

#### Start only frontend
```bash
invoke run-frontend
```

> Frontend runs in development mode (`npm start`).  

---



## Testing

> **Note:** Make sure the backend virtual environment is activated and always run `invoke` commands from the root directory. See [Notes / Tips](#notes--tips) for full instructions.

### Backend tests
Run backend unit tests with coverage:
```bash
invoke test-backend
```

This command:

 - Automatically sets ENV=test

 - Loads .env.test from the backend/ directory

 - Runs tests against the isolated test database (ecopaths_test)

Safety check: When ENV=test is active, the backend will refuse to run if DB_NAME does not contain the word test.
   
   >If you run tests manually. Set the environment variable before running tests
   >```bash
   >export ENV=test
   >poetry run pytest
   >```


### Frontend tests
Run frontend unit tests with coverage:
```bash
invoke test-frontend
```

### Full coverage
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

- **Activate backend environment:**  
  Make sure the backend's virtual environment is activated before running development tasks.
  ```bash
  cd backend
  poetry shell
  cd ..
  ```

- **Run from project root:**  
  Always execute `invoke` tasks from the root directory of the project (`EcoPaths`), not from subfolders.

- **Coverage reports location:**  
  Test coverage reports are saved in the `coverage_reports/` directory:
  - Backend → `coverage_reports/backend/`
  - Frontend → `coverage_reports/frontend/`

- **Port conflicts:**  
  If ports `8000` (backend) or `3000` (frontend) are already in use, stop any existing processes before starting new ones.

- **Stopping servers/tests:**  
  Use standard interruption *Ctrl+C* to cleanly stop any running development servers or test processes.




## Documentation

- [Product backlog](https://github.com/orgs/OhtuProjektiSyksy25/projects/5/views/1)  
- [Sprint task board](https://github.com/orgs/OhtuProjektiSyksy25/projects/5/views/4)


## License

This project is licensed under the MIT License.
