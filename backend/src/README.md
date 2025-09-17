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

## Runnng tests
**Activate poetry virtual environment**
```bash
    poetry shell
```
**Run tests**
```bash
    pytest
```