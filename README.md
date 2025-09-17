# GO2-Web-App


## Frontend Setup

### Prerequisites

**Install Node.js and Git using Homebrew:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install node git
```


### Installation

1. **Clone the dev branch**
   ```bash
   git clone -b dev https://github.com/OhtuProjektiSyksy25/GO2-Web-App
   cd GO2-Web-App/frontend
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
- [Sprint task board](https://github.com/orgs/OhtuProjektiSyksy25/projects/1/views/3?filterQuery=sprint%3A%40current)
