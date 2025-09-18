# Backend setup

## Installation

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

## Testing

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

### Run format, lint and coverage
```bash
   poetry run invoke all
```