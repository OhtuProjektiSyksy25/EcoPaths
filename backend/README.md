# Backend setup

## Installation using Poetry

1. **Install poetry**
```bash
    curl -sSL https://install.python-poetry.org | python3 -
```

2. **Activate poetry virtual environment**
```bash
    poetry shell
```

3. **Install dependencies**
```bash
    poetry install
```

## Running backend
**Activate poetry virtual environment**
```bash
    poetry shell
```

**Run the backend**
```bash
    uvicorn src.main:app --reload
```
**Backend will open at http://127.0.0.1:8000**




## Installation using Conda



## Prerequisites

**Have conda installed**


1. **Create and activate a conda environment**
```bash
    conda create -n ecopaths-backend python=3.11
    conda activate ecopaths-backend
```

2. **Install dependencies**
```bash
    poetry install
```

3. **Run the development server**
```bash
    uvicorn src.main:app --reload
```


**Backend will open at http://127.0.0.1:8000**


## Testing

### Format code using autopep8
```bash
   poetry run invoke format
```

### Run Pylint
```bash
   poetry run invoke lint
```

### Run unit tests
```bash
   poetry run invoke test
```

### Generate coverage report
```bash
   poetry run invoke coverage
```

### Run lint and unit tests
```bash
   poetry run invoke check
```

### Run format, lint and coverage
```bash
   poetry run invoke full
```
