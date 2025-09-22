# EcoPaths

[![.github/workflows/ci-cd.yml](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/OhtuProjektiSyksy25/EcoPaths/branch/main/graph/badge.svg)](https://app.codecov.io/github/OhtuProjektiSyksy25/EcoPaths)


## Project Description


## Installation

### Frontend Setup

#### Prerequisites

**Install Node.js and Git using Homebrew:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install node git
```

#### Installation

1. **Clone the dev branch**
   ```bash
   git clone -b dev https://github.com/OhtuProjektiSyksy25/EcoPaths
   cd EcoPaths/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

4. **The app will open at http://localhost:3000**

## Usage

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

## Testing

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




## Documentation

- [Product backlog](https://github.com/orgs/OhtuProjektiSyksy25/projects/1)  
- [Sprint task board](https://github.com/orgs/OhtuProjektiSyksy25/projects/5/views/4)

## License

This project is licensed under the MIT License.
