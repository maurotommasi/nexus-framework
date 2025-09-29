# GitHub Actions to Nexus Pipeline Migration Guide

**Comprehensive Guide with 100+ Real-World Examples**

**Version:** 2.0.0  
**Last Updated:** 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Basic Workflows (10 examples)](#basic-workflows)
3. [Node.js & JavaScript (15 examples)](#nodejs--javascript)
4. [Python Projects (15 examples)](#python-projects)
5. [Java & JVM (12 examples)](#java--jvm)
6. [Go Projects (10 examples)](#go-projects)
7. [Ruby Projects (8 examples)](#ruby-projects)
8. [PHP Projects (8 examples)](#php-projects)
9. [.NET & C# (8 examples)](#net--c)
10. [Rust Projects (6 examples)](#rust-projects)
11. [Docker & Containers (12 examples)](#docker--containers)
12. [Cloud Deployments (18 examples)](#cloud-deployments)
13. [Kubernetes (10 examples)](#kubernetes)
14. [Database Operations (10 examples)](#database-operations)
15. [Testing & Quality (15 examples)](#testing--quality)
16. [Security & Compliance (12 examples)](#security--compliance)
17. [Monorepo Strategies (8 examples)](#monorepo-strategies)
18. [Mobile Development (10 examples)](#mobile-development)
19. [Infrastructure as Code (10 examples)](#infrastructure-as-code)
20. [CI/CD Patterns (15 examples)](#cicd-patterns)
21. [Notification & Monitoring (8 examples)](#notification--monitoring)
22. [Caching & Optimization (8 examples)](#caching--optimization)
23. [Migration Best Practices](#migration-best-practices)

---

## Introduction

This comprehensive guide provides 100+ real-world examples for migrating from GitHub Actions to Nexus Enterprise Pipeline, covering virtually every common use case and technology stack.

---

## Basic Workflows

### Example 1: Simple CI Pipeline

**GitHub Actions:**
```yaml
name: Simple CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm test
```

**Nexus Pipeline:**
```json
{
  "name": "Simple CI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm install && npm test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 2: Multi-Step Build

**GitHub Actions:**
```yaml
name: Multi-Step Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

**Nexus Pipeline:**
```json
{
  "name": "Multi-Step Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm ci && npm run lint && npm test && npm run build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 3: PR Validation

**GitHub Actions:**
```yaml
name: PR Validation
on:
  pull_request:
    branches: [main, develop]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci
      - run: npm run validate
```

**Nexus Pipeline:**
```json
{
  "name": "PR Validation",
  "version": "1.0.0",
  "triggers": ["git:pull_request"],
  "steps": [
    {
      "name": "validate",
      "command": "git clone $GITHUB_REPOSITORY . && npm ci && npm run validate",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 4: Branch-Specific Workflow

**GitHub Actions:**
```yaml
name: Branch Build
on:
  push:
    branches:
      - main
      - develop
      - 'release/*'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: make build
```

**Nexus Pipeline:**
```json
{
  "name": "Branch Build",
  "version": "1.0.0",
  "triggers": ["git:push:main", "git:push:develop", "git:push:release/*"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && make build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 5: Path-Based Triggers

**GitHub Actions:**
```yaml
name: Backend Only
on:
  push:
    paths:
      - 'backend/**'
      - 'api/**'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: cd backend && npm test
```

**Nexus Pipeline:**
```json
{
  "name": "Backend Only",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && if git diff --name-only HEAD~1 | grep -E '^(backend|api)/'; then cd backend && npm test; fi",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 6: Scheduled Workflow

**GitHub Actions:**
```yaml
name: Nightly Build
on:
  schedule:
    - cron: '0 2 * * *'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
```

**Nexus Pipeline:**
```json
{
  "name": "Nightly Build",
  "version": "1.0.0",
  "triggers": ["schedule:0 2 * * *"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 7: Manual Trigger

**GitHub Actions:**
```yaml
name: Manual Deploy
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment'
        required: true
        default: 'staging'
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: ./deploy.sh ${{ github.event.inputs.environment }}
```

**Nexus Pipeline:**
```json
{
  "name": "Manual Deploy",
  "version": "1.0.0",
  "triggers": ["manual"],
  "steps": [
    {
      "name": "deploy",
      "command": "git clone $GITHUB_REPOSITORY . && ./deploy.sh $ENVIRONMENT",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "ENVIRONMENT": "$INPUTS_ENVIRONMENT"
      }
    }
  ]
}
```

### Example 8: Tag-Based Release

**GitHub Actions:**
```yaml
name: Release
on:
  push:
    tags:
      - 'v*'
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: make release
```

**Nexus Pipeline:**
```json
{
  "name": "Release",
  "version": "1.0.0",
  "triggers": ["git:tag:v*"],
  "steps": [
    {
      "name": "release",
      "command": "git clone $GITHUB_REPOSITORY . && make release",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 9: Multiple Jobs Sequential

**GitHub Actions:**
```yaml
name: Sequential Pipeline
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
  
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm test
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run deploy
```

**Nexus Pipeline:**
```json
{
  "name": "Sequential Pipeline",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build",
      "working_dir": ".",
      "timeout": 21600
    },
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && npm test",
      "working_dir": ".",
      "timeout": 21600,
      "depends_on": ["build"]
    },
    {
      "name": "deploy",
      "command": "git clone $GITHUB_REPOSITORY . && npm run deploy",
      "working_dir": ".",
      "timeout": 21600,
      "depends_on": ["test"]
    }
  ]
}
```

### Example 10: Environment-Specific Builds

**GitHub Actions:**
```yaml
name: Multi-Environment
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, staging, prod]
    steps:
      - uses: actions/checkout@v3
      - run: npm run build:${{ matrix.environment }}
```

**Nexus Pipeline:**
```json
{
  "name": "Multi-Environment",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "build_dev",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build:dev",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "build_staging",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build:staging",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "build_prod",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build:prod",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

---

## Node.js & JavaScript

### Example 11: Node.js Matrix Testing

**GitHub Actions:**
```yaml
name: Node.js CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14, 16, 18, 20]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

**Nexus Pipeline:**
```json
{
  "name": "Node.js CI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 4,
  "steps": [
    {
      "name": "test_14",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 14 && nvm use 14 && npm ci && npm test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_16",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 16 && nvm use 16 && npm ci && npm test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_18",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_20",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 20 && nvm use 20 && npm ci && npm test",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

### Example 12: React Application

**GitHub Actions:**
```yaml
name: React Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v3
        with:
          name: build
          path: build/
```

**Nexus Pipeline:**
```json
{
  "name": "React Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["build/**"]
    }
  ]
}
```

### Example 13: Vue.js Application

**GitHub Actions:**
```yaml
name: Vue Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - run: npm run test:unit
```

**Nexus Pipeline:**
```json
{
  "name": "Vue Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm run test:unit",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 14: Angular Application

**GitHub Actions:**
```yaml
name: Angular Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run lint
      - run: npm run test -- --watch=false --browsers=ChromeHeadless
      - run: npm run build -- --configuration production
```

**Nexus Pipeline:**
```json
{
  "name": "Angular Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run lint && npm run test -- --watch=false --browsers=ChromeHeadless && npm run build -- --configuration production",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 15: Next.js Application

**GitHub Actions:**
```yaml
name: Next.js Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - run: npm start &
      - run: sleep 10
      - run: curl http://localhost:3000
```

**Nexus Pipeline:**
```json
{
  "name": "Next.js Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm start & sleep 10 && curl http://localhost:3000",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 16: TypeScript Library

**GitHub Actions:**
```yaml
name: TypeScript Lib
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run type-check
      - run: npm run build
      - run: npm test
      - run: npm pack
```

**Nexus Pipeline:**
```json
{
  "name": "TypeScript Lib",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run type-check && npm run build && npm test && npm pack",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["*.tgz"]
    }
  ]
}
```

### Example 17: Electron App

**GitHub Actions:**
```yaml
name: Electron Build
on: [push]
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - run: npm run package
```

**Nexus Pipeline:**
```json
{
  "name": "Electron Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "build_ubuntu",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm run package",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "build_macos",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm run package",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "build_windows",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm run package",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

### Example 18: Express API

**GitHub Actions:**
```yaml
name: Express API
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis
      mongodb:
        image: mongo
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test
```

**Nexus Pipeline:**
```json
{
  "name": "Express API",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "docker run -d --name redis redis && docker run -d --name mongodb mongo && git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 19: NestJS Application

**GitHub Actions:**
```yaml
name: NestJS
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run test:e2e
      - run: npm run build
```

**Nexus Pipeline:**
```json
{
  "name": "NestJS",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run lint && npm run test && npm run test:e2e && npm run build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 20: Gatsby Site

**GitHub Actions:**
```yaml
name: Gatsby Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - run: npm run serve &
      - run: sleep 10
      - run: curl http://localhost:9000
```

**Nexus Pipeline:**
```json
{
  "name": "Gatsby Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm run serve & sleep 10 && curl http://localhost:9000",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["public/**"]
    }
  ]
}
```

### Example 21: Svelte Application

**GitHub Actions:**
```yaml
name: Svelte Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run check
      - run: npm run build
      - run: npm test
```

**Nexus Pipeline:**
```json
{
  "name": "Svelte Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run check && npm run build && npm test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 22: Webpack Bundle

**GitHub Actions:**
```yaml
name: Webpack Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - run: npm run analyze
```

**Nexus Pipeline:**
```json
{
  "name": "Webpack Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && npm run analyze",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["dist/**", "stats.json"]
    }
  ]
}
```

### Example 23: Yarn Workspaces

**GitHub Actions:**
```yaml
name: Yarn Workspaces
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: yarn install --frozen-lockfile
      - run: yarn workspaces run test
      - run: yarn workspaces run build
```

**Nexus Pipeline:**
```json
{
  "name": "Yarn Workspaces",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && yarn install --frozen-lockfile && yarn workspaces run test && yarn workspaces run build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 24: pnpm Monorepo

**GitHub Actions:**
```yaml
name: pnpm Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm run -r build
      - run: pnpm run -r test
```

**Nexus Pipeline:**
```json
{
  "name": "pnpm Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm install -g pnpm@8 && nvm install 18 && nvm use 18 && pnpm install && pnpm run -r build && pnpm run -r test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 25: Deno Application

**GitHub Actions:**
```yaml
name: Deno
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: denoland/setup-deno@v1
        with:
          deno-version: v1.x
      - run: deno lint
      - run: deno test
      - run: deno task build
```

**Nexus Pipeline:**
```json
{
  "name": "Deno",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && curl -fsSL https://deno.land/install.sh | sh && export PATH=\"$HOME/.deno/bin:$PATH\" && deno lint && deno test && deno task build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

---

## Python Projects

### Example 26: Python Multi-Version Testing

**GitHub Actions:**
```yaml
name: Python Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pytest
```

**Nexus Pipeline:**
```json
{
  "name": "Python Tests",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 5,
  "steps": [
    {
      "name": "test_3_8",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.8 && pyenv global 3.8 && pip install -r requirements.txt && pytest",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_9",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.9 && pyenv global 3.9 && pip install -r requirements.txt && pytest",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_10",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install -r requirements.txt && pytest",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_11",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install -r requirements.txt && pytest",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_12",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.12 && pyenv global 3.12 && pip install -r requirements.txt && pytest",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

### Example 27: Django Application

**GitHub Actions:**
```yaml
name: Django CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python manage.py migrate
      - run: python manage.py test
```

**Nexus Pipeline:**
```json
{
  "name": "Django CI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "docker run -d --name postgres -e POSTGRES_PASSWORD=postgres postgres:14 && git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install -r requirements.txt && python manage.py migrate && python manage.py test",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/test"
      }
    }
  ]
}
```

### Example 28: Flask API

**GitHub Actions:**
```yaml
name: Flask API
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest-cov
      - run: pytest --cov=app --cov-report=xml
```

**Nexus Pipeline:**
```json
{
  "name": "Flask API",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install -r requirements.txt && pip install pytest-cov && pytest --cov=app --cov-report=xml",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["coverage.xml"]
    }
  ]
}
```

### Example 29: FastAPI Application

**GitHub Actions:**
```yaml
name: FastAPI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
      - run: uvicorn main:app --host 0.0.0.0 --port 8000 &
      - run: sleep 5
      - run: curl http://localhost:8000/health
```

**Nexus Pipeline:**
```json
{
  "name": "FastAPI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install -r requirements.txt && pytest && uvicorn main:app --host 0.0.0.0 --port 8000 & sleep 5 && curl http://localhost:8000/health",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 30: Poetry Project

**GitHub Actions:**
```yaml
name: Poetry Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest
      - run: poetry build
```

**Nexus Pipeline:**
```json
{
  "name": "Poetry Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install poetry && poetry install && poetry run pytest && poetry build",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["dist/**"]
    }
  ]
}
```

### Example 31: Pipenv Project

**GitHub Actions:**
```yaml
name: Pipenv Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install pipenv
      - run: pipenv install --dev
      - run: pipenv run pytest
```

**Nexus Pipeline:**
```json
{
  "name": "Pipenv Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install pipenv && pipenv install --dev && pipenv run pytest",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 32: Pylint & Black

**GitHub Actions:**
```yaml
name: Python Linting
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pylint black flake8 mypy
      - run: black --check .
      - run: flake8 .
      - run: pylint **/*.py
      - run: mypy .
```

**Nexus Pipeline:**
```json
{
  "name": "Python Linting",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "lint",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install pylint black flake8 mypy && black --check . && flake8 . && pylint **/*.py && mypy .",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 33: Sphinx Documentation

**GitHub Actions:**
```yaml
name: Build Docs
on: [push]
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install sphinx sphinx_rtd_theme
      - run: cd docs && make html
```

**Nexus Pipeline:**
```json
{
  "name": "Build Docs",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "docs",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install sphinx sphinx_rtd_theme && cd docs && make html",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["docs/_build/html/**"]
    }
  ]
}
```

### Example 34: Celery Worker

**GitHub Actions:**
```yaml
name: Celery Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis
      rabbitmq:
        image: rabbitmq
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: celery -A myapp worker --loglevel=info &
      - run: pytest tests/celery_tests.py
```

**Nexus Pipeline:**
```json
{
  "name": "Celery Test",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "docker run -d --name redis redis && docker run -d --name rabbitmq rabbitmq && git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install -r requirements.txt && celery -A myapp worker --loglevel=info & pytest tests/celery_tests.py",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 35: Scrapy Spider

**GitHub Actions:**
```yaml
name: Scrapy Spider
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install scrapy
      - run: scrapy check
      - run: scrapy crawl myspider -o output.json
```

**Nexus Pipeline:**
```json
{
  "name": "Scrapy Spider",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install scrapy && scrapy check && scrapy crawl myspider -o output.json",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["output.json"]
    }
  ]
}
```

### Example 36: Jupyter Notebooks

**GitHub Actions:**
```yaml
name: Test Notebooks
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install jupyter nbconvert
      - run: jupyter nbconvert --to notebook --execute notebooks/*.ipynb
```

**Nexus Pipeline:**
```json
{
  "name": "Test Notebooks",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install jupyter nbconvert && jupyter nbconvert --to notebook --execute notebooks/*.ipynb",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 37: PyInstaller Build

**GitHub Actions:**
```yaml
name: PyInstaller
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install pyinstaller
      - run: pyinstaller --onefile main.py
```

**Nexus Pipeline:**
```json
{
  "name": "PyInstaller",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install pyinstaller && pyinstaller --onefile main.py",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["dist/**"]
    }
  ]
}
```

### Example 38: Behave BDD Tests

**GitHub Actions:**
```yaml
name: BDD Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install behave
      - run: behave
```

**Nexus Pipeline:**
```json
{
  "name": "BDD Tests",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install behave && behave",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 39: NumPy/SciPy Project

**GitHub Actions:**
```yaml
name: Scientific Python
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install numpy scipy pandas matplotlib
      - run: pytest tests/
```

**Nexus Pipeline:**
```json
{
  "name": "Scientific Python",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install numpy scipy pandas matplotlib && pytest tests/",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 40: Machine Learning Pipeline

**GitHub Actions:**
```yaml
name: ML Pipeline
on: [push]
jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install scikit-learn tensorflow
      - run: python train.py
      - run: python evaluate.py
```

**Nexus Pipeline:**
```json
{
  "name": "ML Pipeline",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "train",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.10 && pyenv global 3.10 && pip install scikit-learn tensorflow && python train.py && python evaluate.py",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["models/**", "metrics.json"]
    }
  ]
}
```

---

## Java & JVM

### Example 41: Maven Build

**GitHub Actions:**
```yaml
name: Maven Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: mvn clean install
```

**Nexus Pipeline:**
```json
{
  "name": "Maven Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && mvn clean install",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 42: Gradle Multi-Module

**GitHub Actions:**
```yaml
name: Gradle Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: ./gradlew build
      - run: ./gradlew test
```

**Nexus Pipeline:**
```json
{
  "name": "Gradle Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && ./gradlew build && ./gradlew test",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["build/reports/**"]
    }
  ]
}
```

### Example 43: Spring Boot Application

**GitHub Actions:**
```yaml
name: Spring Boot
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: mvn clean package
      - run: mvn spring-boot:run &
      - run: sleep 30
      - run: curl http://localhost:8080/actuator/health
```

**Nexus Pipeline:**
```json
{
  "name": "Spring Boot",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && mvn clean package && mvn spring-boot:run & sleep 30 && curl http://localhost:8080/actuator/health",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 44: Quarkus Application

**GitHub Actions:**
```yaml
name: Quarkus
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: ./mvnw clean package -Pnative
```

**Nexus Pipeline:**
```json
{
  "name": "Quarkus",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && ./mvnw clean package -Pnative",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 45: Micronaut Application

**GitHub Actions:**
```yaml
name: Micronaut
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: ./gradlew test
      - run: ./gradlew build
```

**Nexus Pipeline:**
```json
{
  "name": "Micronaut",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && ./gradlew test && ./gradlew build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 46: Kotlin Project

**GitHub Actions:**
```yaml
name: Kotlin Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: ./gradlew ktlintCheck
      - run: ./gradlew test
      - run: ./gradlew build
```

**Nexus Pipeline:**
```json
{
  "name": "Kotlin Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && ./gradlew ktlintCheck && ./gradlew test && ./gradlew build",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 47: Scala SBT Project

**GitHub Actions:**
```yaml
name: Scala Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '11'
          distribution: 'temurin'
      - run: sbt clean compile
      - run: sbt test
```

**Nexus Pipeline:**
```json
{
  "name": "Scala Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 11-tem && sdk use java 11-tem && sdk install sbt && sbt clean compile && sbt test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 48: Groovy Project

**GitHub Actions:**
```yaml
name: Groovy Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '11'
          distribution: 'temurin'
      - run: ./gradlew test
```

**Nexus Pipeline:**
```json
{
  "name": "Groovy Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 11-tem && sdk use java 11-tem && ./gradlew test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 49: Apache Camel

**GitHub Actions:**
```yaml
name: Camel Routes
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '11'
          distribution: 'temurin'
      - run: mvn test
      - run: mvn camel:run &
      - run: sleep 10
```

**Nexus Pipeline:**
```json
{
  "name": "Camel Routes",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 11-tem && sdk use java 11-tem && mvn test && mvn camel:run & sleep 10",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 50: Vert.x Application

**GitHub Actions:**
```yaml
name: Vert.x
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: mvn clean package
      - run: java -jar target/*.jar &
      - run: sleep 10
```

**Nexus Pipeline:**
```json
{
  "name": "Vert.x",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && mvn clean package && java -jar target/*.jar & sleep 10",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 51: JUnit 5 Tests

**GitHub Actions:**
```yaml
name: JUnit Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: '17'
          distribution: 'temurin'
      - run: mvn test
      - run: mvn surefire-report:report
```

**Nexus Pipeline:**
```json
{
  "name": "JUnit Tests",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && mvn test && mvn surefire-report:report",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["target/surefire-reports/**"]
    }
  ]
}
```

### Example 52: Java Multi-Version

**GitHub Actions:**
```yaml
name: Java Matrix
on: [push]
jobs:
  build:
    strategy:
      matrix:
        java: [11, 17, 21]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          java-version: ${{ matrix.java }}
          distribution: 'temurin'
      - run: mvn test
```

**Nexus Pipeline:**
```json
{
  "name": "Java Matrix",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "test_java_11",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 11-tem && sdk use java 11-tem && mvn test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_java_17",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17-tem && sdk use java 17-tem && mvn test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_java_21",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 21-tem && sdk use java 21-tem && mvn test",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

---

## Go Projects

### Example 53: Go Build and Test

**GitHub Actions:**
```yaml
name: Go Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go build -o mycli
```

**Nexus Pipeline:**
```json
{
  "name": "Go CLI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "build_ubuntu",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && GOOS=linux GOARCH=amd64 go build -o mycli-linux",
      "parallel": true,
      "timeout": 21600,
      "artifacts": ["mycli-linux"]
    },
    {
      "name": "build_macos",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && GOOS=darwin GOARCH=amd64 go build -o mycli-darwin",
      "parallel": true,
      "timeout": 21600,
      "artifacts": ["mycli-darwin"]
    },
    {
      "name": "build_windows",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && GOOS=windows GOARCH=amd64 go build -o mycli.exe",
      "parallel": true,
      "timeout": 21600,
      "artifacts": ["mycli.exe"]
    }
  ]
}
```
### Example 54: Go Microservice

**GitHub Actions:**
```yaml
name: Go Microservice
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go install golang.org/x/lint/golint@latest
      - run: golint ./...
  
  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test -race -coverprofile=coverage.txt ./...
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go build -o bin/server ./cmd/server
```

**Nexus Pipeline:**
```json
{
  "name": "Go Microservice",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "lint",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go install golang.org/x/lint/golint@latest && golint ./...",
      "working_dir": ".",
      "timeout": 21600
    },
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go test -race -coverprofile=coverage.txt ./...",
      "working_dir": ".",
      "timeout": 21600,
      "depends_on": ["lint"],
      "artifacts": ["coverage.txt"]
    },
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go build -o bin/server ./cmd/server",
      "working_dir": ".",
      "timeout": 21600,
      "depends_on": ["test"],
      "artifacts": ["bin/server"]
    }
  ]
}
```

### Example 56: Go with Protobuf

**GitHub Actions:**
```yaml
name: Go Protobuf
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
      - run: protoc --go_out=. proto/*.proto
      - run: go build ./...
```

**Nexus Pipeline:**
```json
{
  "name": "Go Protobuf",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go install google.golang.org/protobuf/cmd/protoc-gen-go@latest && protoc --go_out=. proto/*.proto && go build ./...",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 57: Go gRPC Service

**GitHub Actions:**
```yaml
name: gRPC Service
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test ./...
      - run: go run server/main.go &
      - run: sleep 5
      - run: grpcurl -plaintext localhost:50051 list
```

**Nexus Pipeline:**
```json
{
  "name": "gRPC Service",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go test ./... && go run server/main.go & sleep 5 && grpcurl -plaintext localhost:50051 list",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 58: Go Benchmarks

**GitHub Actions:**
```yaml
name: Go Benchmarks
on: [push]
jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test -bench=. -benchmem ./...
```

**Nexus Pipeline:**
```json
{
  "name": "Go Benchmarks",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "benchmark",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go test -bench=. -benchmem ./...",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 59: Go Cobra CLI

**GitHub Actions:**
```yaml
name: Cobra CLI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go mod download
      - run: go build -o mycli
      - run: ./mycli version
```

**Nexus Pipeline:**
```json
{
  "name": "Cobra CLI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go mod download && go build -o mycli && ./mycli version",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 60: Go Module Update

**GitHub Actions:**
```yaml
name: Go Mod Update
on:
  schedule:
    - cron: '0 0 * * 1'
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go get -u ./...
      - run: go mod tidy
      - run: go test ./...
```

**Nexus Pipeline:**
```json
{
  "name": "Go Mod Update",
  "version": "1.0.0",
  "triggers": ["schedule:0 0 * * 1"],
  "steps": [
    {
      "name": "update",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && go get -u ./... && go mod tidy && go test ./...",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 61: Go with Docker

**GitHub Actions:**
```yaml
name: Go Docker
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t myapp:latest .
      - run: docker run --rm myapp:latest go test ./...
```

**Nexus Pipeline:**
```json
{
  "name": "Go Docker",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -t myapp:latest . && docker run --rm myapp:latest go test ./...",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 62: GoReleaser

**GitHub Actions:**
```yaml
name: GoReleaser
on:
  push:
    tags:
      - 'v*'
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: curl -sfL https://goreleaser.com/static/run | bash
```

**Nexus Pipeline:**
```json
{
  "name": "GoReleaser",
  "version": "1.0.0",
  "triggers": ["git:tag:v*"],
  "steps": [
    {
      "name": "release",
      "command": "git clone $GITHUB_REPOSITORY . && gvm install go1.21 && gvm use go1.21 && curl -sfL https://goreleaser.com/static/run | bash",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

---

## Ruby Projects

### Example 63: Ruby on Rails

**GitHub Actions:**
```yaml
name: Rails CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: rails db:create db:migrate
      - run: rails test
```

**Nexus Pipeline:**
```json
{
  "name": "Rails CI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "docker run -d --name postgres -e POSTGRES_PASSWORD=postgres postgres:14 && git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && rails db:create db:migrate && rails test",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/test"
      }
    }
  ]
}
```

### Example 64: RSpec Tests

**GitHub Actions:**
```yaml
name: RSpec
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: rspec
```

**Nexus Pipeline:**
```json
{
  "name": "RSpec",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && rspec",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 65: Sinatra App

**GitHub Actions:**
```yaml
name: Sinatra
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: ruby app.rb &
      - run: sleep 5
      - run: curl http://localhost:4567
```

**Nexus Pipeline:**
```json
{
  "name": "Sinatra",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && ruby app.rb & sleep 5 && curl http://localhost:4567",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 66: Jekyll Site

**GitHub Actions:**
```yaml
name: Jekyll Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: bundle exec jekyll build
```

**Nexus Pipeline:**
```json
{
  "name": "Jekyll Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && bundle exec jekyll build",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["_site/**"]
    }
  ]
}
```

### Example 67: Ruby Gem Build

**GitHub Actions:**
```yaml
name: Gem Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: gem build *.gemspec
      - run: gem install *.gem
```

**Nexus Pipeline:**
```json
{
  "name": "Gem Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && gem build *.gemspec && gem install *.gem",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["*.gem"]
    }
  ]
}
```

### Example 68: RuboCop Linting

**GitHub Actions:**
```yaml
name: RuboCop
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: rubocop
```

**Nexus Pipeline:**
```json
{
  "name": "RuboCop",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "lint",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && rubocop",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 69: Cucumber Tests

**GitHub Actions:**
```yaml
name: Cucumber
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: cucumber
```

**Nexus Pipeline:**
```json
{
  "name": "Cucumber",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && cucumber",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 70: Ruby Matrix Testing

**GitHub Actions:**
```yaml
name: Ruby Matrix
on: [push]
jobs:
  test:
    strategy:
      matrix:
        ruby: ['2.7', '3.0', '3.1', '3.2']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: ${{ matrix.ruby }}
      - run: bundle install
      - run: rspec
```

**Nexus Pipeline:**
```json
{
  "name": "Ruby Matrix",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 4,
  "steps": [
    {
      "name": "test_2_7",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 2.7.0 && rbenv global 2.7.0 && bundle install && rspec",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_0",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.0.0 && rbenv global 3.0.0 && bundle install && rspec",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_1",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.1.0 && rbenv global 3.1.0 && bundle install && rspec",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_3_2",
      "command": "git clone $GITHUB_REPOSITORY . && rbenv install 3.2.0 && rbenv global 3.2.0 && bundle install && rspec",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

---

## PHP Projects

### Example 71: PHP Composer

**GitHub Actions:**
```yaml
name: PHP Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: vendor/bin/phpunit
```

**Nexus Pipeline:**
```json
{
  "name": "PHP Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && vendor/bin/phpunit",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 72: Laravel Application

**GitHub Actions:**
```yaml
name: Laravel
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: php artisan test
```

**Nexus Pipeline:**
```json
{
  "name": "Laravel",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && php artisan test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 73: Symfony Application

**GitHub Actions:**
```yaml
name: Symfony
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: php bin/phpunit
```

**Nexus Pipeline:**
```json
{
  "name": "Symfony",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && php bin/phpunit",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 74: WordPress Plugin

**GitHub Actions:**
```yaml
name: WordPress Plugin
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.1'
      - run: composer install
      - run: vendor/bin/phpcs
      - run: vendor/bin/phpunit
```

**Nexus Pipeline:**
```json
{
  "name": "WordPress Plugin",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.1.0 && phpenv global 8.1.0 && composer install && vendor/bin/phpcs && vendor/bin/phpunit",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 75: PHP CS Fixer

**GitHub Actions:**
```yaml
name: PHP CS
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: vendor/bin/php-cs-fixer fix --dry-run --diff
```

**Nexus Pipeline:**
```json
{
  "name": "PHP CS",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "lint",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && vendor/bin/php-cs-fixer fix --dry-run --diff",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 76: PHPStan Analysis

**GitHub Actions:**
```yaml
name: PHPStan
on: [push]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: vendor/bin/phpstan analyse
```

**Nexus Pipeline:**
```json
{
  "name": "PHPStan",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "analyze",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && vendor/bin/phpstan analyse",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 77: Pest Testing

**GitHub Actions:**
```yaml
name: Pest Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: vendor/bin/pest
```

**Nexus Pipeline:**
```json
{
  "name": "Pest Tests",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && vendor/bin/pest",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 78: PHP Multi-Version

**GitHub Actions:**
```yaml
name: PHP Matrix
on: [push]
jobs:
  test:
    strategy:
      matrix:
        php: ['8.0', '8.1', '8.2']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
      - run: composer install
      - run: vendor/bin/phpunit
```

**Nexus Pipeline:**
```json
{
  "name": "PHP Matrix",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "test_8_0",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.0.0 && phpenv global 8.0.0 && composer install && vendor/bin/phpunit",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_8_1",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.1.0 && phpenv global 8.1.0 && composer install && vendor/bin/phpunit",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_8_2",
      "command": "git clone $GITHUB_REPOSITORY . && phpenv install 8.2.0 && phpenv global 8.2.0 && composer install && vendor/bin/phpunit",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

---

## .NET & C#

### Example 79: .NET Build

**GitHub Actions:**
```yaml
name: .NET Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '7.0.x'
      - run: dotnet restore
      - run: dotnet build
      - run: dotnet test
```

**Nexus Pipeline:**
```json
{
  "name": ".NET Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet restore && dotnet build && dotnet test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 80: ASP.NET Core

**GitHub Actions:**
```yaml
name: ASP.NET Core
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '7.0.x'
      - run: dotnet build
      - run: dotnet run &
      - run: sleep 10
      - run: curl http://localhost:5000/health
```

**Nexus Pipeline:**
```json
{
  "name": "ASP.NET Core",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet build && dotnet run & sleep 10 && curl http://localhost:5000/health",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 81: Blazor Application

**GitHub Actions:**
```yaml
name: Blazor
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '7.0.x'
      - run: dotnet restore
      - run: dotnet build --configuration Release
      - run: dotnet publish --configuration Release
```

**Nexus Pipeline:**
```json
{
  "name": "Blazor",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet restore && dotnet build --configuration Release && dotnet publish --configuration Release",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["bin/Release/**"]
    }
  ]
}
```

### Example 82: NuGet Package

**GitHub Actions:**
```yaml
name: NuGet Package
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '7.0.x'
      - run: dotnet pack --configuration Release
```

**Nexus Pipeline:**
```json
{
  "name": "NuGet Package",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet pack --configuration Release",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["**/*.nupkg"]
    }
  ]
}
```

### Example 83: xUnit Tests

**GitHub Actions:**
```yaml
name: xUnit Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '7.0.x'
      - run: dotnet test --logger "trx;LogFileName=test-results.trx"
```

**Nexus Pipeline:**
```json
{
  "name": "xUnit Tests",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet test --logger \"trx;LogFileName=test-results.trx\"",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["**/test-results.trx"]
    }
  ]
}
```

### Example 84: Entity Framework Migrations

**GitHub Actions:**
```yaml
name: EF Migrations
on: [push]
jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '7.0.x'
      - run: dotnet ef migrations add NewMigration
      - run: dotnet ef database update
```

**Nexus Pipeline:**
```json
{
  "name": "EF Migrations",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "migrate",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet ef migrations add NewMigration && dotnet ef database update",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 85: .NET Multi-Version

**GitHub Actions:**
```yaml
name: .NET Matrix
on: [push]
jobs:
  build:
    strategy:
      matrix:
        dotnet: ['6.0.x', '7.0.x', '8.0.x']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: ${{ matrix.dotnet }}
      - run: dotnet test
```

**Nexus Pipeline:**
```json
{
  "name": ".NET Matrix",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "test_6_0",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 6.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_7_0",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 7.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet test",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "test_8_0",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 8.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet test",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

### Example 86: MAUI Application

**GitHub Actions:**
```yaml
name: .NET MAUI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-dotnet@v3
        with:
          dotnet-version: '8.0.x'
      - run: dotnet workload install maui
      - run: dotnet build -f net8.0-android
```

**Nexus Pipeline:**
```json
{
  "name": ".NET MAUI",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && wget https://dot.net/v1/dotnet-install.sh && bash dotnet-install.sh --version 8.0 && export PATH=\"$HOME/.dotnet:$PATH\" && dotnet workload install maui && dotnet build -f net8.0-android",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

---

## Rust Projects

### Example 87: Rust Build

**GitHub Actions:**
```yaml
name: Rust Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - run: cargo build --release
      - run: cargo test
```

**Nexus Pipeline:**
```json
{
  "name": "Rust Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && cargo build --release && cargo test",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["target/release/**"]
    }
  ]
}
```

### Example 88: Rust Clippy

**GitHub Actions:**
```yaml
name: Rust Clippy
on: [push]
jobs:
  clippy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          components: clippy
      - run: cargo clippy -- -D warnings
```

**Nexus Pipeline:**
```json
{
  "name": "Rust Clippy",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "clippy",
      "command": "git clone $GITHUB_REPOSITORY . && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && rustup component add clippy && cargo clippy -- -D warnings",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 89: Rust Format Check

**GitHub Actions:**
```yaml
name: Rust Format
on: [push]
jobs:
  format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          components: rustfmt
      - run: cargo fmt -- --check
```

**Nexus Pipeline:**
```json
{
  "name": "Rust Format",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "format",
      "command": "git clone $GITHUB_REPOSITORY . && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && rustup component add rustfmt && cargo fmt -- --check",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 90: Rust WebAssembly

**GitHub Actions:**
```yaml
name: Rust WASM
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - run: cargo install wasm-pack
      - run: wasm-pack build --target web
```

**Nexus Pipeline:**
```json
{
  "name": "Rust WASM",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && cargo install wasm-pack && wasm-pack build --target web",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["pkg/**"]
    }
  ]
}
```

### Example 91: Rust Cross-Compile

**GitHub Actions:**
```yaml
name: Rust Cross
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - run: rustup target add x86_64-unknown-linux-musl
      - run: cargo build --release --target x86_64-unknown-linux-musl
```

**Nexus Pipeline:**
```json
{
  "name": "Rust Cross",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && rustup target add x86_64-unknown-linux-musl && cargo build --release --target x86_64-unknown-linux-musl",
      "working_dir": ".",
      "timeout": 21600,
      "artifacts": ["target/x86_64-unknown-linux-musl/release/**"]
    }
  ]
}
```

### Example 92: Rust Benchmark

**GitHub Actions:**
```yaml
name: Rust Bench
on: [push]
jobs:
  bench:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: nightly
      - run: cargo +nightly bench
```

**Nexus Pipeline:**
```json
{
  "name": "Rust Bench",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "bench",
      "command": "git clone $GITHUB_REPOSITORY . && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source $HOME/.cargo/env && rustup toolchain install nightly && cargo +nightly bench",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

---

## Docker & Containers

### Example 93: Docker Build and Push

**GitHub Actions:**
```yaml
name: Docker Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: myapp:latest
```

**Nexus Pipeline:**
```json
{
  "name": "Docker Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin && docker build -t myapp:latest . && docker push myapp:latest",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "DOCKER_USERNAME": "$DOCKER_USERNAME",
        "DOCKER_PASSWORD": "$DOCKER_PASSWORD"
      }
    }
  ]
}
```

### Example 94: Multi-Stage Docker Build

**GitHub Actions:**
```yaml
name: Multi-Stage Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

**Nexus Pipeline:**
```json
{
  "name": "Multi-Stage Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && docker buildx create --use && echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin && docker build -t ghcr.io/$GITHUB_REPOSITORY:$GITHUB_SHA . && docker push ghcr.io/$GITHUB_REPOSITORY:$GITHUB_SHA",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "GITHUB_TOKEN": "$GITHUB_TOKEN",
        "GITHUB_ACTOR": "$GITHUB_ACTOR",
        "GITHUB_REPOSITORY": "$GITHUB_REPOSITORY",
        "GITHUB_SHA": "$GITHUB_SHA"
      }
    }
  ]
}
```

### Example 95: Docker Compose Testing

**GitHub Actions:**
```yaml
name: Docker Compose Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose up -d
      - run: docker-compose exec -T app npm test
      - run: docker-compose down
```

**Nexus Pipeline:**
```json
{
  "name": "Docker Compose Test",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && docker-compose up -d && docker-compose exec -T app npm test && docker-compose down",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 96: Docker Multi-Platform Build

**GitHub Actions:**
```yaml
name: Multi-Platform
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-qemu-action@v2
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          platforms: linux/amd64,linux/arm64
          push: true
          tags: myapp:latest
```

**Nexus Pipeline:**
```json
{
  "name": "Multi-Platform",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && docker run --rm --privileged multiarch/qemu-user-static --reset -p yes && docker buildx create --use && docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest --push .",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 97: Docker Layer Caching

**GitHub Actions:**
```yaml
name: Docker Cache
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/build-push-action@v4
        with:
          context: .
          cache-from: type=gha
          cache-to: type=gha,mode=max
          push: true
          tags: myapp:latest
```

**Nexus Pipeline:**
```json
{
  "name": "Docker Cache",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && docker buildx create --use && docker buildx build --cache-from type=local,src=/tmp/.buildx-cache --cache-to type=local,dest=/tmp/.buildx-cache -t myapp:latest --push .",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 98: Dockerfile Linting

**GitHub Actions:**
```yaml
name: Dockerfile Lint
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker run --rm -i hadolint/hadolint < Dockerfile
```

**Nexus Pipeline:**
```json
{
  "name": "Dockerfile Lint",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "lint",
      "command": "git clone $GITHUB_REPOSITORY . && docker run --rm -i hadolint/hadolint < Dockerfile",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 99: Container Security Scan

**GitHub Actions:**
```yaml
name: Container Scan
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t myapp:test .
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:test'
```

**Nexus Pipeline:**
```json
{
  "name": "Container Scan",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "scan",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -t myapp:test . && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image myapp:test",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 100: Docker Build Matrix

**GitHub Actions:**
```yaml
name: Docker Matrix
on: [push]
jobs:
  build:
    strategy:
      matrix:
        version: ['alpine', 'ubuntu', 'debian']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -f Dockerfile.${{ matrix.version }} -t myapp:${{ matrix.version }} .
```

**Nexus Pipeline:**
```json
{
  "name": "Docker Matrix",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "max_parallel_jobs": 3,
  "steps": [
    {
      "name": "build_alpine",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -f Dockerfile.alpine -t myapp:alpine .",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "build_ubuntu",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -f Dockerfile.ubuntu -t myapp:ubuntu .",
      "parallel": true,
      "timeout": 21600
    },
    {
      "name": "build_debian",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -f Dockerfile.debian -t myapp:debian .",
      "parallel": true,
      "timeout": 21600
    }
  ]
}
```

### Example 101: Docker Registry Push

**GitHub Actions:**
```yaml
name: Registry Push
on: [push]
jobs:
  push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t registry.example.com/myapp:${{ github.sha }} .
      - run: docker login registry.example.com -u ${{ secrets.REGISTRY_USER }} -p ${{ secrets.REGISTRY_PASS }}
      - run: docker push registry.example.com/myapp:${{ github.sha }}
```

**Nexus Pipeline:**
```json
{
  "name": "Registry Push",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "push",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -t registry.example.com/myapp:$GITHUB_SHA . && echo $REGISTRY_PASS | docker login registry.example.com -u $REGISTRY_USER --password-stdin && docker push registry.example.com/myapp:$GITHUB_SHA",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "REGISTRY_USER": "$REGISTRY_USER",
        "REGISTRY_PASS": "$REGISTRY_PASS",
        "GITHUB_SHA": "$GITHUB_SHA"
      }
    }
  ]
}
```

### Example 102: Podman Build

**GitHub Actions:**
```yaml
name: Podman Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: sudo apt-get install -y podman
      - run: podman build -t myapp:latest .
      - run: podman push myapp:latest
```

**Nexus Pipeline:**
```json
{
  "name": "Podman Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && sudo apt-get update && sudo apt-get install -y podman && podman build -t myapp:latest . && podman push myapp:latest",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 103: Kaniko Build

**GitHub Actions:**
```yaml
name: Kaniko Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          docker run \
            -v $(pwd):/workspace \
            gcr.io/kaniko-project/executor:latest \
            --dockerfile=Dockerfile \
            --context=dir:///workspace \
            --destination=myapp:latest
```

**Nexus Pipeline:**
```json
{
  "name": "Kaniko Build",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && docker run -v $(pwd):/workspace gcr.io/kaniko-project/executor:latest --dockerfile=Dockerfile --context=dir:///workspace --destination=myapp:latest",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

### Example 104: Docker Healthcheck

**GitHub Actions:**
```yaml
name: Docker Health
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker build -t myapp:test .
      - run: docker run -d --name test-container myapp:test
      - run: sleep 10
      - run: docker inspect --format='{{.State.Health.Status}}' test-container
```

**Nexus Pipeline:**
```json
{
  "name": "Docker Health",
  "version": "1.0.0",
  "triggers": ["git:push"],
  "steps": [
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && docker build -t myapp:test . && docker run -d --name test-container myapp:test && sleep 10 && docker inspect --format='{{.State.Health.Status}}' test-container",
      "working_dir": ".",
      "timeout": 21600
    }
  ]
}
```

---

## Cloud Deployments

### Example 105: AWS S3 Deployment

**GitHub Actions:**
```yaml
name: Deploy to S3
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: aws s3 sync ./build s3://my-bucket --delete
```

**Nexus Pipeline:**
```json
{
  "name": "Deploy to S3",
  "version": "1.0.0",
  "triggers": ["git:push:main"],
  "steps": [
    {
      "name": "deploy",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=us-east-1 && aws s3 sync ./build s3://my-bucket --delete",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY"
      }
    }
  ]
}
```

### Example 106: AWS Lambda Deployment

**GitHub Actions:**
```yaml
name: Deploy Lambda
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci --production
      - run: zip -r function.zip .
      - uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip
```

**Nexus Pipeline:**
```json
{
  "name": "Deploy Lambda",
  "version": "1.0.0",
  "triggers": ["git:push:main"],
  "steps": [
    {
      "name": "deploy",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci --production && zip -r function.zip . && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=us-east-1 && aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip",
      "working_dir": ".",
      "timeout": 21600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY"
      }
    }
  ]
}
```

### Example 107: Microservices Multi-Region Deployment with Canary Release

**GitHub Actions:**
```yaml
name: Microservices Canary Deployment
on:
  push:
    branches: [main]

env:
  ECR_REGISTRY: 123456789.dkr.ecr.us-east-1.amazonaws.com
  REGIONS: us-east-1,eu-west-1,ap-southeast-1

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [auth-service, payment-service, user-service, notification-service]
    outputs:
      image-tags: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.ECR_REGISTRY }}/${{ matrix.service }}
          tags: |
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./services/${{ matrix.service }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Run integration tests
        run: |
          docker run --rm ${{ env.ECR_REGISTRY }}/${{ matrix.service }}:${{ github.sha }} \
            npm run test:integration
      
      - name: Run security scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.ECR_REGISTRY }}/${{ matrix.service }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results-${{ matrix.service }}.sarif'
      
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results-${{ matrix.service }}.sarif'

  deploy-canary:
    needs: build-and-test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        region: [us-east-1, eu-west-1, ap-southeast-1]
        service: [auth-service, payment-service, user-service, notification-service]
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ matrix.region }}
      
      - name: Update ECS task definition
        run: |
          TASK_DEFINITION=$(aws ecs describe-task-definition \
            --task-definition ${{ matrix.service }}-${{ matrix.region }} \
            --query taskDefinition)
          
          NEW_TASK_DEF=$(echo $TASK_DEFINITION | jq --arg IMAGE "${{ env.ECR_REGISTRY }}/${{ matrix.service }}:${{ github.sha }}" \
            '.containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
          
          aws ecs register-task-definition --cli-input-json "$NEW_TASK_DEF"
      
      - name: Deploy canary (10% traffic)
        run: |
          aws ecs update-service \
            --cluster production-${{ matrix.region }} \
            --service ${{ matrix.service }} \
            --task-definition ${{ matrix.service }}-${{ matrix.region }} \
            --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
            --desired-count 10
          
          # Wait for canary deployment
          aws ecs wait services-stable \
            --cluster production-${{ matrix.region }} \
            --services ${{ matrix.service }}
      
      - name: Monitor canary metrics
        run: |
          python3 scripts/monitor_canary.py \
            --service ${{ matrix.service }} \
            --region ${{ matrix.region }} \
            --duration 600 \
            --error-threshold 1.0 \
            --latency-threshold-p99 500
      
      - name: Rollback on failure
        if: failure()
        run: |
          aws ecs update-service \
            --cluster production-${{ matrix.region }} \
            --service ${{ matrix.service }} \
            --force-new-deployment \
            --task-definition ${{ matrix.service }}-${{ matrix.region }}:$(($REVISION - 1))

  promote-production:
    needs: deploy-canary
    runs-on: ubuntu-latest
    strategy:
      matrix:
        region: [us-east-1, eu-west-1, ap-southeast-1]
        service: [auth-service, payment-service, user-service, notification-service]
    steps:
      - name: Scale to 100% traffic
        run: |
          aws ecs update-service \
            --cluster production-${{ matrix.region }} \
            --service ${{ matrix.service }} \
            --desired-count 50

  notify:
    needs: [build-and-test, deploy-canary, promote-production]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Deployment ${{ job.status }}: ${{ github.repository }}@${{ github.sha }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Status:* ${{ job.status }}\n*Repository:* ${{ github.repository }}\n*Commit:* ${{ github.sha }}\n*Author:* ${{ github.actor }}"
                  }
                }
              ]
            }
```

**Nexus Pipeline:**
```json
{
  "name": "Microservices Canary Deployment",
  "version": "1.0.0",
  "triggers": ["git:push:main"],
  "max_parallel_jobs": 12,
  "steps": [
    {
      "name": "build_auth_service",
      "command": "git clone $GITHUB_REPOSITORY . && docker buildx create --use && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com && docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/auth-service:$GITHUB_SHA ./services/auth-service --cache-from type=gha --cache-to type=gha,mode=max && docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/auth-service:$GITHUB_SHA && docker run --rm 123456789.dkr.ecr.us-east-1.amazonaws.com/auth-service:$GITHUB_SHA npm run test:integration && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --format sarif --output trivy-auth.sarif 123456789.dkr.ecr.us-east-1.amazonaws.com/auth-service:$GITHUB_SHA",
      "parallel": true,
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      },
      "artifacts": ["trivy-auth.sarif"]
    },
    {
      "name": "build_payment_service",
      "command": "git clone $GITHUB_REPOSITORY . && docker buildx create --use && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com && docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/payment-service:$GITHUB_SHA ./services/payment-service && docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/payment-service:$GITHUB_SHA && docker run --rm 123456789.dkr.ecr.us-east-1.amazonaws.com/payment-service:$GITHUB_SHA npm run test:integration && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --format sarif --output trivy-payment.sarif 123456789.dkr.ecr.us-east-1.amazonaws.com/payment-service:$GITHUB_SHA",
      "parallel": true,
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      },
      "artifacts": ["trivy-payment.sarif"]
    },
    {
      "name": "build_user_service",
      "command": "git clone $GITHUB_REPOSITORY . && docker buildx create --use && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com && docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/user-service:$GITHUB_SHA ./services/user-service && docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/user-service:$GITHUB_SHA && docker run --rm 123456789.dkr.ecr.us-east-1.amazonaws.com/user-service:$GITHUB_SHA npm run test:integration && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --format sarif --output trivy-user.sarif 123456789.dkr.ecr.us-east-1.amazonaws.com/user-service:$GITHUB_SHA",
      "parallel": true,
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      },
      "artifacts": ["trivy-user.sarif"]
    },
    {
      "name": "build_notification_service",
      "command": "git clone $GITHUB_REPOSITORY . && docker buildx create --use && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com && docker build -t 123456789.dkr.ecr.us-east-1.amazonaws.com/notification-service:$GITHUB_SHA ./services/notification-service && docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/notification-service:$GITHUB_SHA && docker run --rm 123456789.dkr.ecr.us-east-1.amazonaws.com/notification-service:$GITHUB_SHA npm run test:integration && docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --format sarif --output trivy-notification.sarif 123456789.dkr.ecr.us-east-1.amazonaws.com/notification-service:$GITHUB_SHA",
      "parallel": true,
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      },
      "artifacts": ["trivy-notification.sarif"]
    },
    {
      "name": "deploy_canary_us_east_1",
      "command": "git clone $GITHUB_REPOSITORY . && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=us-east-1 && for service in auth-service payment-service user-service notification-service; do TASK_DEF=$(aws ecs describe-task-definition --task-definition $service-us-east-1 --query taskDefinition) && NEW_TASK=$(echo $TASK_DEF | jq --arg IMG \"123456789.dkr.ecr.us-east-1.amazonaws.com/$service:$GITHUB_SHA\" '.containerDefinitions[0].image = $IMG | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)') && aws ecs register-task-definition --cli-input-json \"$NEW_TASK\" && aws ecs update-service --cluster production-us-east-1 --service $service --task-definition $service-us-east-1 --deployment-configuration 'maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}' --desired-count 10 && aws ecs wait services-stable --cluster production-us-east-1 --services $service && python3 scripts/monitor_canary.py --service $service --region us-east-1 --duration 600 --error-threshold 1.0 --latency-threshold-p99 500; done",
      "depends_on": ["build_auth_service", "build_payment_service", "build_user_service", "build_notification_service"],
      "timeout": 7200,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      },
      "retry_count": 0
    },
    {
      "name": "deploy_canary_eu_west_1",
      "command": "git clone $GITHUB_REPOSITORY . && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=eu-west-1 && for service in auth-service payment-service user-service notification-service; do TASK_DEF=$(aws ecs describe-task-definition --task-definition $service-eu-west-1 --query taskDefinition) && NEW_TASK=$(echo $TASK_DEF | jq --arg IMG \"123456789.dkr.ecr.us-east-1.amazonaws.com/$service:$GITHUB_SHA\" '.containerDefinitions[0].image = $IMG | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)') && aws ecs register-task-definition --cli-input-json \"$NEW_TASK\" && aws ecs update-service --cluster production-eu-west-1 --service $service --task-definition $service-eu-west-1 --deployment-configuration 'maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}' --desired-count 10 && aws ecs wait services-stable --cluster production-eu-west-1 --services $service && python3 scripts/monitor_canary.py --service $service --region eu-west-1 --duration 600 --error-threshold 1.0 --latency-threshold-p99 500; done",
      "depends_on": ["build_auth_service", "build_payment_service", "build_user_service", "build_notification_service"],
      "parallel": true,
      "timeout": 7200,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      }
    },
    {
      "name": "deploy_canary_ap_southeast_1",
      "command": "git clone $GITHUB_REPOSITORY . && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=ap-southeast-1 && for service in auth-service payment-service user-service notification-service; do TASK_DEF=$(aws ecs describe-task-definition --task-definition $service-ap-southeast-1 --query taskDefinition) && NEW_TASK=$(echo $TASK_DEF | jq --arg IMG \"123456789.dkr.ecr.us-east-1.amazonaws.com/$service:$GITHUB_SHA\" '.containerDefinitions[0].image = $IMG | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)') && aws ecs register-task-definition --cli-input-json \"$NEW_TASK\" && aws ecs update-service --cluster production-ap-southeast-1 --service $service --task-definition $service-ap-southeast-1 --deployment-configuration 'maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}' --desired-count 10 && aws ecs wait services-stable --cluster production-ap-southeast-1 --services $service && python3 scripts/monitor_canary.py --service $service --region ap-southeast-1 --duration 600 --error-threshold 1.0 --latency-threshold-p99 500; done",
      "depends_on": ["build_auth_service", "build_payment_service", "build_user_service", "build_notification_service"],
      "parallel": true,
      "timeout": 7200,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "GITHUB_SHA": "$GITHUB_SHA"
      }
    },
    {
      "name": "promote_production_all_regions",
      "command": "export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && for region in us-east-1 eu-west-1 ap-southeast-1; do export AWS_DEFAULT_REGION=$region && for service in auth-service payment-service user-service notification-service; do aws ecs update-service --cluster production-$region --service $service --desired-count 50; done; done",
      "depends_on": ["deploy_canary_us_east_1", "deploy_canary_eu_west_1", "deploy_canary_ap_southeast_1"],
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY"
      }
    },
    {
      "name": "notify_slack",
      "command": "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Deployment completed: $GITHUB_REPOSITORY@$GITHUB_SHA by $GITHUB_ACTOR\",\"blocks\":[{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"*Deployment Status:* Success\\n*Repository:* $GITHUB_REPOSITORY\\n*Commit:* $GITHUB_SHA\\n*Author:* $GITHUB_ACTOR\"}}]}' $SLACK_WEBHOOK",
      "depends_on": ["promote_production_all_regions"],
      "condition": "success",
      "timeout": 300,
      "environment": {
        "SLACK_WEBHOOK": "$SLACK_WEBHOOK",
        "GITHUB_REPOSITORY": "$GITHUB_REPOSITORY",
        "GITHUB_SHA": "$GITHUB_SHA",
        "GITHUB_ACTOR": "$GITHUB_ACTOR"
      }
    },
    {
      "name": "notify_slack_failure",
      "command": "curl -X POST -H 'Content-type: application/json' --data '{\"text\":\"Deployment FAILED: $GITHUB_REPOSITORY@$GITHUB_SHA by $GITHUB_ACTOR\",\"blocks\":[{\"type\":\"section\",\"text\":{\"type\":\"mrkdwn\",\"text\":\"*Deployment Status:* FAILED\\n*Repository:* $GITHUB_REPOSITORY\\n*Commit:* $GITHUB_SHA\\n*Author:* $GITHUB_ACTOR\"}}]}' $SLACK_WEBHOOK",
      "depends_on": ["promote_production_all_regions"],
      "condition": "failure",
      "timeout": 300,
      "environment": {
        "SLACK_WEBHOOK": "$SLACK_WEBHOOK",
        "GITHUB_REPOSITORY": "$GITHUB_REPOSITORY",
        "GITHUB_SHA": "$GITHUB_SHA",
        "GITHUB_ACTOR": "$GITHUB_ACTOR"
      }
    }
  ]
}
```

### Example 108: Full-Stack Monorepo with E2E Testing

**GitHub Actions:**
```yaml
name: Full-Stack Monorepo CI/CD
on:
  push:
    branches: [main, develop, staging]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'
  POSTGRES_VERSION: '14'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      database: ${{ steps.filter.outputs.database }}
    steps:
      - uses: actions/checkout@v3
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            frontend:
              - 'packages/frontend/**'
            backend:
              - 'packages/backend/**'
            database:
              - 'packages/database/**'

  frontend-build:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint:frontend
      
      - name: Type check
        run: npm run type-check:frontend
      
      - name: Unit tests
        run: npm run test:frontend -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./packages/frontend/coverage/coverage-final.json
          flags: frontend
      
      - name: Build
        run: npm run build:frontend
        env:
          REACT_APP_API_URL: ${{ secrets.API_URL }}
          REACT_APP_ENV: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
      
      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: frontend-build
          path: packages/frontend/build
          retention-days: 7

  backend-build:
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint:backend
      
      - name: Type check
        run: npm run type-check:backend
      
      - name: Run migrations
        run: npm run migrate:test
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
      
      - name: Unit tests
        run: npm run test:backend -- --coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
      
      - name: Integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./packages/backend/coverage/coverage-final.json
          flags: backend
      
      - name: Build
        run: npm run build:backend

  e2e-tests:
    needs: [frontend-build, backend-build]
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: e2edb
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install dependencies
        run: npm ci
      
      - name: Download frontend build
        uses: actions/download-artifact@v3
        with:
          name: frontend-build
          path: packages/frontend/build
      
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      
      - name: Run migrations
        run: npm run migrate:test
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/e2edb
      
      - name: Seed database
        run: npm run seed:e2e
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/e2edb
      
      - name: Start backend
        run: npm run start:backend &
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/e2edb
          REDIS_URL: redis://localhost:6379
          PORT: 3001
      
      - name: Start frontend
        run: npx serve -s packages/frontend/build -l 3000 &
      
      - name: Wait for services
        run: |
          npx wait-on http://localhost:3000 http://localhost:3001/health --timeout 120000
      
      - name: Run E2E tests
        run: npm run test:e2e
        env:
          BASE_URL: http://localhost:3000
          API_URL: http://localhost:3001
      
      - name: Upload E2E artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7

  database-migration-check:
    needs: detect-changes
    if: needs.detect-changes.outputs.database == 'true'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
      
      - name: Install dependencies
        run: npm ci
      
      - name: Check migration rollback
        run: |
          npm run migrate:up
          npm run migrate:down
          npm run migrate:up
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres
      
      - name: Generate migration SQL
        run: npm run migrate:sql > migration.sql
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/postgres
      
      - name: Upload migration SQL
        uses: actions/upload-artifact@v3
        with:
          name: migration-sql
          path: migration.sql

  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    needs: [frontend-build, backend-build, e2e-tests]
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Download frontend build
        uses: actions/download-artifact@v3
        with:
          name: frontend-build
          path: packages/frontend/build
      
      - name: Deploy frontend to S3
        run: |
          aws s3 sync packages/frontend/build s3://staging-frontend-bucket --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.STAGING_CF_DIST_ID }} --paths "/*"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
      
      - name: Run database migrations
        run: npm run migrate:up
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
      
- name: Deploy backend to ECS
        run: |
          aws ecs update-service \
            --cluster staging-cluster \
            --service backend-service \
            --force-new-deployment
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: us-east-1
      
      - name: Run smoke tests
        run: npm run test:smoke
        env:
          BASE_URL: https://staging.example.com

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: [frontend-build, backend-build, e2e-tests, database-migration-check]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v3
      
      - name: Create backup
        run: |
          TIMESTAMP=$(date +%Y%m%d_%H%M%S)
          aws rds create-db-snapshot \
            --db-instance-identifier production-db \
            --db-snapshot-identifier backup-$TIMESTAMP
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Download frontend build
        uses: actions/download-artifact@v3
        with:
          name: frontend-build
          path: packages/frontend/build
      
      - name: Deploy frontend
        run: |
          aws s3 sync packages/frontend/build s3://production-frontend-bucket --delete
          aws cloudfront create-invalidation --distribution-id ${{ secrets.PROD_CF_DIST_ID }} --paths "/*"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Run migrations with monitoring
        run: |
          npm run migrate:up 2>&1 | tee migration.log
          if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "Migration failed!"
            npm run migrate:down
            exit 1
          fi
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
      
      - name: Deploy backend
        run: |
          aws ecs update-service \
            --cluster production-cluster \
            --service backend-service \
            --force-new-deployment
          aws ecs wait services-stable \
            --cluster production-cluster \
            --services backend-service
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      
      - name: Run production smoke tests
        run: npm run test:smoke
        env:
          BASE_URL: https://example.com
      
      - name: Create GitHub release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: v${{ github.run_number }}
          release_name: Release ${{ github.run_number }}
          body: |
            Automated release from commit ${{ github.sha }}
            
            Changes: ${{ github.event.head_commit.message }}
```

**Nexus Pipeline:**
```json
{
  "name": "Full-Stack Monorepo CI/CD",
  "version": "1.0.0",
  "triggers": ["git:push:main", "git:push:develop", "git:push:staging", "git:pull_request"],
  "max_parallel_jobs": 4,
  "steps": [
    {
      "name": "frontend_build",
      "command": "git clone $GITHUB_REPOSITORY . && git diff --name-only HEAD~1 > changed_files.txt && if grep -q '^packages/frontend/' changed_files.txt; then nvm install 18 && nvm use 18 && npm ci && npm run lint:frontend && npm run type-check:frontend && npm run test:frontend -- --coverage && npm run build:frontend && curl -s https://codecov.io/bash | bash -s -- -f ./packages/frontend/coverage/coverage-final.json -F frontend; else echo 'No frontend changes'; fi",
      "working_dir": ".",
      "timeout": 3600,
      "environment": {
        "REACT_APP_API_URL": "$API_URL",
        "REACT_APP_ENV": "$ENVIRONMENT"
      },
      "artifacts": ["packages/frontend/build/**"]
    },
    {
      "name": "backend_build",
      "command": "git clone $GITHUB_REPOSITORY . && git diff --name-only HEAD~1 > changed_files.txt && if grep -q '^packages/backend/' changed_files.txt; then docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=testdb -p 5432:5432 postgres:14 && docker run -d --name redis -p 6379:6379 redis:7 && sleep 10 && nvm install 18 && nvm use 18 && npm ci && npm run lint:backend && npm run type-check:backend && export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/testdb && export REDIS_URL=redis://localhost:6379 && npm run migrate:test && npm run test:backend -- --coverage && npm run test:integration && npm run build:backend && curl -s https://codecov.io/bash | bash -s -- -f ./packages/backend/coverage/coverage-final.json -F backend; else echo 'No backend changes'; fi",
      "working_dir": ".",
      "timeout": 3600,
      "parallel": true,
      "artifacts": ["packages/backend/dist/**"]
    },
    {
      "name": "e2e_tests",
      "command": "git clone $GITHUB_REPOSITORY . && docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=e2edb -p 5432:5432 postgres:14 && docker run -d --name redis -p 6379:6379 redis:7 && sleep 10 && nvm install 18 && nvm use 18 && npm ci && npx playwright install --with-deps chromium && export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/e2edb && export REDIS_URL=redis://localhost:6379 && npm run migrate:test && npm run seed:e2e && npm run start:backend & sleep 5 && npx serve -s packages/frontend/build -l 3000 & npx wait-on http://localhost:3000 http://localhost:3001/health --timeout 120000 && npm run test:e2e",
      "depends_on": ["frontend_build", "backend_build"],
      "timeout": 3600,
      "environment": {
        "BASE_URL": "http://localhost:3000",
        "API_URL": "http://localhost:3001"
      },
      "artifacts": ["playwright-report/**"]
    },
    {
      "name": "database_migration_check",
      "command": "git clone $GITHUB_REPOSITORY . && git diff --name-only HEAD~1 > changed_files.txt && if grep -q '^packages/database/' changed_files.txt; then docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:14 && sleep 10 && nvm install 18 && nvm use 18 && npm ci && export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres && npm run migrate:up && npm run migrate:down && npm run migrate:up && npm run migrate:sql > migration.sql; else echo 'No database changes'; fi",
      "working_dir": ".",
      "timeout": 1800,
      "artifacts": ["migration.sql"]
    },
    {
      "name": "deploy_staging",
      "command": "git clone $GITHUB_REPOSITORY . && if [ \"$GITHUB_REF\" = \"refs/heads/develop\" ]; then export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=us-east-1 && aws s3 sync packages/frontend/build s3://staging-frontend-bucket --delete && aws cloudfront create-invalidation --distribution-id $STAGING_CF_DIST_ID --paths '/*' && npm run migrate:up && aws ecs update-service --cluster staging-cluster --service backend-service --force-new-deployment && sleep 60 && npm run test:smoke; fi",
      "depends_on": ["frontend_build", "backend_build", "e2e_tests"],
      "condition": "$GITHUB_REF == 'refs/heads/develop'",
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "STAGING_CF_DIST_ID": "$STAGING_CF_DIST_ID",
        "DATABASE_URL": "$STAGING_DATABASE_URL",
        "BASE_URL": "https://staging.example.com"
      }
    },
    {
      "name": "deploy_production",
      "command": "git clone $GITHUB_REPOSITORY . && if [ \"$GITHUB_REF\" = \"refs/heads/main\" ]; then export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=us-east-1 && TIMESTAMP=$(date +%Y%m%d_%H%M%S) && aws rds create-db-snapshot --db-instance-identifier production-db --db-snapshot-identifier backup-$TIMESTAMP && aws s3 sync packages/frontend/build s3://production-frontend-bucket --delete && aws cloudfront create-invalidation --distribution-id $PROD_CF_DIST_ID --paths '/*' && npm run migrate:up 2>&1 | tee migration.log && if [ ${PIPESTATUS[0]} -ne 0 ]; then npm run migrate:down && exit 1; fi && aws ecs update-service --cluster production-cluster --service backend-service --force-new-deployment && aws ecs wait services-stable --cluster production-cluster --services backend-service && npm run test:smoke && curl -X POST -H 'Authorization: token $GITHUB_TOKEN' -d '{\"tag_name\":\"v$GITHUB_RUN_NUMBER\",\"name\":\"Release $GITHUB_RUN_NUMBER\",\"body\":\"Automated release from commit $GITHUB_SHA\"}' https://api.github.com/repos/$GITHUB_REPOSITORY/releases; fi",
      "depends_on": ["frontend_build", "backend_build", "e2e_tests", "database_migration_check"],
      "condition": "$GITHUB_REF == 'refs/heads/main'",
      "requires_approval": true,
      "timeout": 3600,
      "environment": {
        "AWS_ACCESS_KEY_ID": "$AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "$AWS_SECRET_ACCESS_KEY",
        "PROD_CF_DIST_ID": "$PROD_CF_DIST_ID",
        "DATABASE_URL": "$PROD_DATABASE_URL",
        "BASE_URL": "https://example.com",
        "GITHUB_TOKEN": "$GITHUB_TOKEN",
        "GITHUB_RUN_NUMBER": "$GITHUB_RUN_NUMBER",
        "GITHUB_SHA": "$GITHUB_SHA"
      }
    }
  ]
}
```
