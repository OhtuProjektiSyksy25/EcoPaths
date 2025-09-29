# EcoPaths

[![.github/workflows/ci-cd.yml](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/OhtuProjektiSyksy25/EcoPaths/actions/workflows/ci-cd.yml)
[![Coverage](https://codecov.io/gh/OhtuProjektiSyksy25/EcoPaths/branch/main/graph/badge.svg)](https://app.codecov.io/github/OhtuProjektiSyksy25/EcoPaths)


## Overview
EcoPaths is a project related to the course Software Engineering Project at the University of Helsinki. 

The web application aims to provide routes based on air quality for pedestrians and cyclists. The project is done in collaboration with MegaSense Oy.

## Installation

### Frontend Setup

#### Prerequisites

- Node.js
- Git



#### Install frontend

1. **Clone the main branch**
   ```bash
   git clone https://github.com/OhtuProjektiSyksy25/EcoPaths
   cd EcoPaths/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Update .env file with your mapbox token. Instructions in [.env_example](https://github.com/OhtuProjektiSyksy25/EcoPaths/blob/dev/frontend/.env_example)**

4. **Build frontend to backend**
   ```bash
   npm run build:ui
   ```

### Backend setup

#### Prerequisites

- Poetry

#### Install backend

1. **Change directory to backend**
   ```bash
   cd ../backend
   ```

2. **Create virtual environment**
   ```bash
   poetry shell
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

## Startup 

1. **Go to root directory**
   ```bash
   cd ..
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
