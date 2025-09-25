# 🎓 Complete Guide to Pipeline YAML Configuration
## A Teacher's Guide for Students

Welcome, students! Today we'll learn how to configure a pipeline using YAML files. Think of YAML as a recipe card for your pipeline - it tells the system exactly what to do, step by step.

---

## 📚 Table of Contents

1. [What is YAML and Why Use It?](#what-is-yaml-and-why-use-it)
2. [Basic YAML Structure](#basic-yaml-structure)
3. [Pipeline Configuration Sections](#pipeline-configuration-sections)
4. [Step-by-Step Configuration](#step-by-step-configuration)
5. [Real Examples](#real-examples)
6. [Common Mistakes and How to Avoid Them](#common-mistakes)
7. [Advanced Configurations](#advanced-configurations)
8. [Practice Exercises](#practice-exercises)

---

## 🤔 What is YAML and Why Use It?

**YAML** stands for "YAML Ain't Markup Language" (it's recursive, like a joke within a joke!).

### Why YAML for Pipelines?

Think of YAML like writing a recipe:
- **Human-readable**: You can read it like plain English
- **Structured**: Everything has its place
- **Version-controllable**: You can track changes in Git
- **Shareable**: Easy to share with your team

### YAML vs Other Formats

```yaml
# YAML - Easy to read
name: "My Pipeline"
steps:
  - name: "build"
    command: "npm run build"
```

```json
// JSON - Harder to read
{
  "name": "My Pipeline",
  "steps": [
    {
      "name": "build", 
      "command": "npm run build"
    }
  ]
}
```

**Lesson**: YAML is cleaner and easier for humans to understand!

---

## 📝 Basic YAML Structure

### The Golden Rules of YAML

1. **Indentation matters** (like Python!)
2. **Use spaces, not tabs**
3. **Colons need a space after them**
4. **Lists start with dashes**

### Basic Syntax

```yaml
# This is a comment (starts with #)

# Key-value pairs
name: "My Pipeline"
version: "1.0.0"

# Numbers don't need quotes
timeout: 300
retry_count: 3

# Booleans
enabled: true
critical: false

# Lists (arrays)
triggers:
  - "push:main"
  - "pull_request"
  - "schedule:daily"

# Objects (nested structures)
environment:
  NODE_ENV: "production"
  DEBUG: "false"
  PORT: "3000"

# Multi-line strings
description: |
  This is a multi-line description.
  It can span several lines.
  Perfect for longer explanations.
```

### 🎯 **Student Exercise 1**: Fix the YAML

```yaml
# What's wrong with this YAML? (Find 4 errors)
name:"My Pipeline"
version: 1.0.0
enabled:true
triggers:
- push:main
  environment:
    NODE_ENV:"production"
```

<details>
<summary>Click for Answer</summary>

**Errors Found:**
1. Missing space after colon: `name: "My Pipeline"`
2. Missing space after colon: `enabled: true`  
3. Missing quotes: `- "push:main"`
4. Wrong indentation: `environment:` should align with other top-level keys

**Fixed Version:**
```yaml
name: "My Pipeline"
version: "1.0.0"
enabled: true
triggers:
  - "push:main"
environment:
  NODE_ENV: "production"
```

</details>

---

## 🏗️ Pipeline Configuration Sections

A pipeline YAML file has several main sections. Let's learn each one!

### 1. 📋 Basic Information Section

```yaml
# Pipeline Identity
name: "web-application-ci-cd"           # Required: Your pipeline name
version: "2.1.0"                        # Semantic versioning
description: "Complete CI/CD pipeline for web application"

# Pipeline Settings  
max_parallel_jobs: 3                    # How many steps can run at once
artifacts_retention: 14                 # How long to keep build outputs (days)
```

**Think of this as**: The cover page of your recipe book - it tells you what you're making and basic settings.

### 2. 🌍 Environment Variables Section

```yaml
# Global variables available to all steps
environment:
  NODE_ENV: "production"                # Environment type
  DATABASE_URL: "postgresql://localhost/app"
  API_VERSION: "v1"
  DEBUG: "false"
  MAX_CONNECTIONS: "100"
```

**Think of this as**: Ingredients that every recipe step can use.

### 3. 🔔 Triggers Section

```yaml
# When should this pipeline run?
triggers:
  - "push:main"                         # When code is pushed to main branch
  - "push:develop"                      # When code is pushed to develop branch  
  - "pull_request:*"                    # On any pull request
  - "schedule:0 2 * * *"                # Daily at 2 AM (cron format)
  - "schedule:0 0 * * 1"                # Weekly on Monday at midnight
  - "webhook:deployment"                # When webhook is called
  - "manual:release"                    # Manual trigger
```

**Think of this as**: When to start cooking - is it dinner time? Special occasion?

### 4. 📢 Notifications Section

```yaml
# How to notify people about pipeline results
notifications:
  default_channels: ["slack", "email"]  # Where to send notifications
  
  slack:
    webhook_url: "https://hooks.slack.com/services/..."
    channel: "#deployments"
    
  email:
    recipients:
      - "devops@company.com"
      - "team-lead@company.com"
    
  on_failure: true                      # Notify on failures
  on_success: false                     # Don't spam on success
```

**Think of this as**: Who to call when dinner is ready (or burned!).

---

## 👨‍🍳 Step-by-Step Configuration

The `steps` section is the heart of your pipeline - it's your cooking instructions!

### Basic Step Structure

```yaml
steps:
  - name: "step-name"                   # Required: Unique identifier
    command: "echo 'Hello World'"       # Required: What to run
    working_dir: "."                    # Where to run (default: current directory)
    timeout: 300                        # Max time in seconds (default: 300)
    retry_count: 0                      # How many times to retry if failed
    parallel: false                     # Can this run alongside other steps?
    critical: true                      # Should pipeline stop if this fails?
    depends_on: []                      # Which steps must finish first
    condition: null                     # When should this step run
    environment: {}                     # Step-specific variables
    artifacts: []                       # Files to save after step completes
```

### 🎯 **Student Exercise 2**: Create Your First Step

Create a step that:
- Is named "hello-world"
- Runs the command `echo "Hello, Pipeline!"`
- Takes maximum 60 seconds
- Creates an artifact called "hello.log"

<details>
<summary>Click for Answer</summary>

```yaml
steps:
  - name: "hello-world"
    command: "echo 'Hello, Pipeline!' > hello.log"
    timeout: 60
    artifacts:
      - "hello.log"
```

</details>

---

## 🎨 Real Examples

Let's build real pipeline configurations from simple to complex!

### 🟢 Example 1: Simple Website Build

```yaml
# simple-website.yaml
name: "simple-website-build"
version: "1.0.0"
description: "Build a simple HTML website"

environment:
  NODE_ENV: "production"

steps:
  - name: "checkout"
    command: "git clone https://github.com/mycompany/website.git ."
    timeout: 120
    artifacts:
      - "*.log"
      - "package.json"

  - name: "install-dependencies"
    command: "npm install"
    depends_on: ["checkout"]
    timeout: 300
    artifacts:
      - "node_modules.tar.gz"

  - name: "build-website"
    command: "npm run build"
    depends_on: ["install-dependencies"]
    timeout: 180
    artifacts:
      - "dist/"
      - "build.log"

  - name: "deploy-website"
    command: "aws s3 sync dist/ s3://my-website-bucket/"
    depends_on: ["build-website"]
    timeout: 120
    environment:
      AWS_REGION: "us-east-1"
```

**What this does:**
1. 📥 Downloads code from GitHub
2. 📦 Installs required packages  
3. 🔨 Builds the website
4. 🚀 Uploads to Amazon S3

### 🟡 Example 2: Advanced Application with Testing

```yaml
# advanced-app.yaml
name: "advanced-web-application"
version: "2.3.1"
description: "Full CI/CD pipeline with testing and security"

# Pipeline settings
max_parallel_jobs: 4
artifacts_retention: 30

# Global variables
environment:
  NODE_ENV: "production"
  CI: "true"
  DOCKER_REGISTRY: "registry.company.com"
  KUBERNETES_NAMESPACE: "production"

# When to run this pipeline
triggers:
  - "push:main"
  - "push:develop"
  - "pull_request:*"
  - "schedule:0 2 * * *"        # Daily at 2 AM

# Notifications
notifications:
  default_channels: ["slack", "email"]
  slack:
    webhook_url: "https://hooks.slack.com/services/ABC123/DEF456/xyz789"
  email:
    recipients: ["team@company.com"]

# Pipeline steps
steps:
  # 📥 Source Code Management
  - name: "checkout-source"
    command: "git clone https://github.com/company/webapp.git . && git checkout $BRANCH"
    timeout: 120
    retry_count: 2
    environment:
      BRANCH: "main"
    artifacts:
      - "*.log"
      - "package.json"
      - "README.md"

  # 📦 Dependencies
  - name: "install-dependencies"
    command: "npm ci --production=false"
    depends_on: ["checkout-source"]
    timeout: 600
    retry_count: 3
    environment:
      NPM_CONFIG_CACHE: "/tmp/npm-cache"
    artifacts:
      - "package-lock.json"
      - "node_modules.tar.gz"

  # 🔍 Code Quality (These run in parallel!)
  - name: "lint-code"
    command: "npm run lint -- --format=json --output-file=lint-results.json"
    depends_on: ["install-dependencies"]
    parallel: true                      # 🚀 Can run alongside other parallel steps
    timeout: 180
    artifacts:
      - "lint-results.json"

  - name: "type-check"
    command: "npm run type-check"
    depends_on: ["install-dependencies"]
    parallel: true                      # 🚀 Runs in parallel with lint-code
    timeout: 120
    critical: false                     # ⚠️ Don't stop pipeline if this fails

  # 🧪 Testing (Also parallel!)
  - name: "unit-tests"
    command: "npm run test:unit -- --coverage --ci"
    depends_on: ["install-dependencies"]
    parallel: true
    timeout: 900
    retry_count: 2
    artifacts:
      - "coverage/"
      - "test-results.xml"

  - name: "integration-tests"
    command: "npm run test:integration -- --ci"
    depends_on: ["install-dependencies"]
    parallel: true
    timeout: 1200
    environment:
      DATABASE_URL: "postgresql://test:test@localhost/test_db"
    artifacts:
      - "integration-results.xml"

  # 🔒 Security
  - name: "security-audit"
    command: "npm audit --audit-level moderate && snyk test --json > security-report.json"
    depends_on: ["install-dependencies"]
    timeout: 300
    critical: false                     # Don't stop pipeline for security warnings
    artifacts:
      - "security-report.json"

  # 🔨 Build (Waits for all tests to pass)
  - name: "build-application"
    command: "npm run build"
    depends_on: ["lint-code", "unit-tests", "integration-tests"]
    timeout: 600
    environment:
      NODE_OPTIONS: "--max-old-space-size=4096"
    artifacts:
      - "dist/"
      - "build-stats.json"
      - "webpack-bundle-analyzer.html"

  # 🐳 Container
  - name: "build-docker-image"
    command: "docker build -t $DOCKER_REGISTRY/webapp:$BUILD_NUMBER ."
    depends_on: ["build-application"]
    timeout: 1200
    environment:
      DOCKER_BUILDKIT: "1"
      BUILD_NUMBER: "#{BUILD_ID}"        # Special variable from pipeline system
    artifacts:
      - "Dockerfile"
      - "docker-build.log"

  # 🚀 Deployment (Only if on main branch)
  - name: "deploy-staging"
    command: "kubectl apply -f k8s/staging/ --namespace=staging"
    depends_on: ["build-docker-image", "security-audit"]
    timeout: 300
    condition: "$BRANCH == 'main'"      # 🎯 Conditional execution
    artifacts:
      - "k8s-staging-deployment.yaml"

  # ✅ Smoke Tests
  - name: "smoke-tests"
    command: "npm run test:smoke -- --env=staging"
    depends_on: ["deploy-staging"]
    timeout: 600
    retry_count: 3
    artifacts:
      - "smoke-test-results.json"
```

### 🎯 **Student Exercise 3**: Understanding the Flow

Looking at the advanced example above, answer these questions:

1. Which steps run first?
2. Which steps can run at the same time?
3. What happens if `type-check` fails?
4. When does `deploy-staging` run?

<details>
<summary>Click for Answers</summary>

1. **First step**: `checkout-source` (no dependencies)
2. **Parallel steps**: `lint-code`, `type-check`, `unit-tests`, `integration-tests` all run together after `install-dependencies`
3. **If type-check fails**: Pipeline continues because `critical: false`
4. **deploy-staging runs when**: 
   - `build-docker-image` AND `security-audit` are complete
   - AND the branch is 'main' (`condition: "$BRANCH == 'main'"`)

</details>

---

## ❌ Common Mistakes and How to Avoid Them

### Mistake 1: Indentation Errors

```yaml
# ❌ WRONG - Inconsistent indentation
steps:
  - name: "build"
    command: "make build"
   timeout: 300              # Wrong indentation!
```

```yaml
# ✅ CORRECT - Consistent indentation
steps:
  - name: "build"
    command: "make build"
    timeout: 300             # Properly aligned
```

### Mistake 2: Missing Dependencies

```yaml
# ❌ WRONG - deploy runs before build!
steps:
  - name: "deploy"
    command: "kubectl apply -f deployment.yaml"
    # Missing: depends_on: ["build"]
  
  - name: "build"
    command: "npm run build"
```

```yaml
# ✅ CORRECT - Proper dependency order
steps:
  - name: "build"
    command: "npm run build"
  
  - name: "deploy"
    command: "kubectl apply -f deployment.yaml"
    depends_on: ["build"]     # Now deploy waits for build
```

### Mistake 3: Circular Dependencies

```yaml
# ❌ WRONG - A depends on B, B depends on A!
steps:
  - name: "step-a"
    command: "echo a"
    depends_on: ["step-b"]    # A waits for B
  
  - name: "step-b" 
    command: "echo b"
    depends_on: ["step-a"]    # B waits for A - CIRCULAR!
```

```yaml
# ✅ CORRECT - Linear dependency
steps:
  - name: "step-a"
    command: "echo a"
    # No dependencies
  
  - name: "step-b"
    command: "echo b" 
    depends_on: ["step-a"]    # B waits for A only
```

### Mistake 4: Forgotten Quotes

```yaml
# ❌ WRONG - YAML interprets these as boolean/numbers
environment:
  PORT: 3000                 # This becomes a number!
  DEBUG: true                # This becomes boolean!
  VERSION: 1.2.3             # This becomes a number!
```

```yaml
# ✅ CORRECT - Explicit strings when needed
environment:
  PORT: "3000"               # Keep as string for environment variables
  DEBUG: "true"              # Keep as string
  VERSION: "1.2.3"           # Keep as string
```

---

## 🚀 Advanced Configurations

### 1. Conditional Execution

```yaml
steps:
  - name: "deploy-production"
    command: "kubectl apply -f prod.yaml"
    condition: "$BRANCH == 'main' and $ENVIRONMENT == 'production'"
    depends_on: ["all-tests-pass"]

  - name: "deploy-staging"
    command: "kubectl apply -f staging.yaml"
    condition: "$BRANCH != 'main'"
    depends_on: ["build"]

  - name: "send-slack-notification"
    command: "curl -X POST $SLACK_WEBHOOK -d 'Pipeline completed'"
    condition: "true"          # Always run
    critical: false            # Don't fail pipeline if notification fails
```

### 2. Complex Environment Setup

```yaml
# Different environments for different steps
environment:
  # Global variables
  COMPANY_NAME: "TechCorp"
  PROJECT_NAME: "WebApp"

steps:
  - name: "test-database"
    command: "npm run test:db"
    environment:
      # Step-specific variables (override global ones)
      DATABASE_URL: "postgresql://test:test@localhost/test_db"
      NODE_ENV: "test"
      DEBUG: "true"

  - name: "production-deploy"
    command: "npm run deploy"
    environment:
      # Production-specific variables
      DATABASE_URL: "postgresql://prod:$PROD_PASSWORD@prod-db/app"
      NODE_ENV: "production"
      DEBUG: "false"
      CACHE_ENABLED: "true"
```

### 3. Complex Artifact Management

```yaml
steps:
  - name: "build-frontend"
    command: "npm run build:frontend"
    artifacts:
      - "dist/frontend/**"     # All files in frontend dist
      - "*.map"                # Source maps
      - "build-report.html"

  - name: "build-backend"
    command: "npm run build:backend"
    artifacts:
      - "dist/backend/**"
      - "server.js"
      - "package.json"

  - name: "package-application"
    command: "tar -czf app-$BUILD_NUMBER.tar.gz dist/"
    depends_on: ["build-frontend", "build-backend"]
    environment:
      BUILD_NUMBER: "#{BUILD_ID}"
    artifacts:
      - "app-*.tar.gz"         # The packaged application
      - "packaging.log"
```

### 4. Retry and Error Handling

```yaml
steps:
  - name: "flaky-external-api-test"
    command: "npm run test:external-api"
    timeout: 300
    retry_count: 5            # Try up to 5 times
    critical: false           # Don't stop pipeline if this keeps failing

  - name: "critical-deployment"
    command: "kubectl apply -f critical-service.yaml"
    timeout: 600              # 10 minutes max
    retry_count: 2            # Try twice
    critical: true            # MUST succeed or stop everything
```

---

## 🏋️ Practice Exercises

### Exercise 4: Build a Blog Pipeline

Create a pipeline configuration for a blog application with these requirements:

**Requirements:**
- Pipeline name: "blog-deployment"
- Runs on pushes to `main` and `develop` branches
- Environment variables: `NODE_ENV=production`, `BLOG_TITLE=My Awesome Blog`
- Steps needed:
  1. **checkout**: Clone the repository (2 minutes max)
  2. **install**: Install npm dependencies (5 minutes max, retry 3 times)
  3. **test**: Run tests (must depend on install, 10 minutes max)
  4. **build**: Build the blog (depends on test, 5 minutes max)  
  5. **deploy**: Deploy only if branch is 'main' (depends on build, 3 minutes max)
- Save artifacts: `dist/`, `test-results.xml`, `*.log`

<details>
<summary>Click for Solution</summary>

```yaml
name: "blog-deployment"
version: "1.0.0"
description: "Blog application deployment pipeline"

environment:
  NODE_ENV: "production"
  BLOG_TITLE: "My Awesome Blog"

triggers:
  - "push:main"
  - "push:develop"

steps:
  - name: "checkout"
    command: "git clone https://github.com/mycompany/blog.git ."
    timeout: 120
    artifacts:
      - "*.log"

  - name: "install"
    command: "npm install"
    depends_on: ["checkout"]
    timeout: 300
    retry_count: 3
    artifacts:
      - "*.log"

  - name: "test"
    command: "npm test"
    depends_on: ["install"]
    timeout: 600
    artifacts:
      - "test-results.xml"
      - "*.log"

  - name: "build"
    command: "npm run build"
    depends_on: ["test"]
    timeout: 300
    artifacts:
      - "dist/"
      - "*.log"

  - name: "deploy"
    command: "npm run deploy"
    depends_on: ["build"]
    timeout: 180
    condition: "$BRANCH == 'main'"
    artifacts:
      - "*.log"
```

</details>

### Exercise 5: E-commerce Platform Pipeline

Create an advanced pipeline for an e-commerce platform:

**Requirements:**
- Multiple parallel test steps (unit, integration, e2e)
- Security scanning
- Database migrations
- Multi-stage deployment (staging → production)
- Notification on failures
- Docker container building

<details>
<summary>Click for Advanced Solution</summary>

```yaml
name: "ecommerce-platform-cicd"
version: "3.1.0"
description: "Complete e-commerce platform CI/CD pipeline"

max_parallel_jobs: 6
artifacts_retention: 21

environment:
  NODE_ENV: "production"
  DOCKER_REGISTRY: "registry.ecommerce.com"
  DATABASE_URL: "postgresql://app:$DB_PASSWORD@db:5432/ecommerce"

triggers:
  - "push:main"
  - "push:develop"
  - "pull_request:*"
  - "schedule:0 3 * * *"

notifications:
  default_channels: ["slack", "email"]
  slack:
    webhook_url: "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
  email:
    recipients: ["devops@ecommerce.com", "team-lead@ecommerce.com"]
  on_failure: true
  on_success: false

steps:
  # Source Code
  - name: "checkout-source"
    command: "git clone https://github.com/ecommerce/platform.git ."
    timeout: 180
    retry_count: 2
    artifacts:
      - "package.json"
      - "*.md"

  # Dependencies
  - name: "install-dependencies"
    command: "npm ci && npm run prepare"
    depends_on: ["checkout-source"]
    timeout: 900
    retry_count: 3
    artifacts:
      - "package-lock.json"

  # Parallel Testing Phase
  - name: "unit-tests"
    command: "npm run test:unit -- --coverage"
    depends_on: ["install-dependencies"]
    parallel: true
    timeout: 600
    artifacts:
      - "coverage/"
      - "unit-test-results.xml"

  - name: "integration-tests"
    command: "npm run test:integration"
    depends_on: ["install-dependencies"]
    parallel: true
    timeout: 1200
    environment:
      DATABASE_URL: "postgresql://test:test@test-db:5432/ecommerce_test"
    artifacts:
      - "integration-test-results.xml"

  - name: "e2e-tests"
    command: "npm run test:e2e"
    depends_on: ["install-dependencies"]
    parallel: true
    timeout: 1800
    critical: false
    artifacts:
      - "e2e-test-results.xml"
      - "screenshots/"

  - name: "lint-and-format"
    command: "npm run lint && npm run format:check"
    depends_on: ["install-dependencies"]
    parallel: true
    timeout: 300

  # Security
  - name: "security-scan"
    command: "npm audit && snyk test"
    depends_on: ["install-dependencies"]
    timeout: 600
    critical: false
    artifacts:
      - "security-report.json"

  # Database
  - name: "database-migrations"
    command: "npm run db:migrate"
    depends_on: ["integration-tests"]
    timeout: 300
    environment:
      DATABASE_URL: "postgresql://migrate:$MIGRATE_PASSWORD@db:5432/ecommerce"

  # Build
  - name: "build-application"
    command: "npm run build:production"
    depends_on: ["unit-tests", "integration-tests", "lint-and-format"]
    timeout: 900
    environment:
      NODE_OPTIONS: "--max-old-space-size=6144"
    artifacts:
      - "dist/"
      - "build-stats.json"

  # Container
  - name: "build-docker-image"
    command: "docker build -t $DOCKER_REGISTRY/ecommerce:$BUILD_ID ."
    depends_on: ["build-application", "database-migrations"]
    timeout: 1500
    environment:
      DOCKER_BUILDKIT: "1"
      BUILD_ID: "#{BUILD_NUMBER}"
    artifacts:
      - "Dockerfile"

  # Staging Deployment
  - name: "deploy-staging"
    command: "kubectl apply -f k8s/staging/ && kubectl rollout status deployment/ecommerce-staging"
    depends_on: ["build-docker-image", "security-scan"]
    timeout: 600
    condition: "$BRANCH == 'main' or $BRANCH == 'develop'"
    artifacts:
      - "k8s-staging-deployment.yaml"

  # Staging Tests
  - name: "staging-smoke-tests"
    command: "npm run test:smoke -- --env=staging"
    depends_on: ["deploy-staging"]
    timeout: 900
    retry_count: 3

  # Production Deployment (only main branch)
  - name: "deploy-production"
    command: "kubectl apply -f k8s/production/ && kubectl rollout status deployment/ecommerce-prod"
    depends_on: ["staging-smoke-tests"]
    timeout: 900
    condition: "$BRANCH == 'main'"
    environment:
      KUBE_NAMESPACE: "production"
    artifacts:
      - "k8s-production-deployment.yaml"

  # Production Verification
  - name: "production-health-check"
    command: "npm run health-check -- --env=production"
    depends_on: ["deploy-production"]
    timeout: 300
    retry_count: 5
    critical: true
```

</details>

---

## 🎯 Key Takeaways for Students

### The 5 Golden Rules

1. **🏗️ Structure First**: Plan your pipeline flow before writing YAML
2. **📏 Indent Correctly**: Use 2 spaces consistently  
3. **🔗 Dependencies Matter**: Think about what needs to happen first
4. **⚡ Use Parallelism**: Run independent steps together to save time
5. **🛡️ Handle Failures**: Use `critical: false`, `retry_count`, and conditions

### Common YAML Patterns

```yaml
# Pattern 1: Sequential Steps
steps:
  - name: "step1"
    command: "..."
  - name: "step2" 
    command: "..."
    depends_on: ["step1"]
  - name: "step3"
    command: "..."
    depends_on: ["step2"]

# Pattern 2: Parallel Steps
steps:
  - name: "setup"
    command: "..."
  - name: "test-unit"
    command: "..."
    depends_on: ["setup"]
    parallel: true
  - name: "test-integration"
    command: "..."
    depends_on: ["setup"]
    parallel: true
  - name: "deploy"
    command: "..."
    depends_on: ["test-unit", "test-integration"]

# Pattern 3: Conditional Steps
steps:
  - name: "deploy-prod"
    command: "..."
    condition: "$BRANCH == 'main'"
  - name: "deploy-staging"
    command: "..."
    condition: "$BRANCH != 'main'"
```

---

## ✅ Checklist for Perfect YAML

Before submitting your pipeline configuration, check:

- [ ] **Valid YAML syntax** (use online YAML validator)
- [ ] **Consistent indentation** (2 spaces everywhere)
- [ ] **All required fields** (`name`, `command` for each step)
- [ ] **No circular dependencies** 
- [ ] **Logical step order**
- [ ] **Appropriate timeouts** (not too short, not too long)
- [ ] **Environment variables quoted** when needed
- [ ] **Artifact paths are correct**
- [ ] **Conditions use proper syntax**
- [ ] **Comments explain complex parts**

---

## 📚 Additional Resources

### Quick Reference

```yaml
# Complete YAML template
name: "pipeline-name"
version: "1.0.0" 
description: "What this pipeline does"
max_parallel_jobs: 3
artifacts_retention: 30

environment:
  GLOBAL_VAR: "value"

triggers:
  - "push:main"
  - "schedule:0 2 * * *"

notifications:
  default_channels: ["slack"]
  slack:
    webhook_url: "https://..."

steps:
  - name: "step-name"
    command: "command to run"
    working_dir: "."
    timeout: 300
    retry_count: 0
    parallel: false
    critical: true
    depends_on: []
    condition: null
    environment:
      STEP_VAR: "value"
    artifacts:
      - "output.log"
```

## Example of YAML in production

```yaml
# production-pipeline-config.yaml
name: "advanced-production-pipeline"
version: "2.4.1"
description: "Advanced production CI/CD with comprehensive testing and monitoring"

# Pipeline Configuration
max_parallel_jobs: 6
artifacts_retention: 14

# Global Environment Variables
environment:
  NODE_ENV: "production"
  CI: "true"
  DOCKER_REGISTRY: "registry.company.com"
  KUBERNETES_NAMESPACE: "production"

# Pipeline Triggers
triggers:
  - "push:main"
  - "schedule:0 2 * * *"
  - "webhook:deploy"
  - "manual:release"

# Notification Configuration
notifications:
  default_channels: ["slack", "email"]
  slack:
    webhook_url: "https://hooks.slack.com/services/..."
  email:
    recipients:
      - "devops@company.com"
      - "team-lead@company.com"

# Pipeline Steps
steps:
  # Source Management
  - name: "checkout-source"
    command: "git clone https://github.com/company/webapp.git . && git checkout $BRANCH"
    working_dir: "."
    timeout: 120
    retry_count: 2
    environment:
      BRANCH: "main"
    depends_on: []
    condition: null
    parallel: false
    critical: true
    artifacts:
      - "*.log"
      - "package.json"

  # Dependency Management
  - name: "install-dependencies"
    command: "npm ci --production=false"
    working_dir: "."
    timeout: 600
    retry_count: 3
    environment: {}
    depends_on:
      - "checkout-source"
    condition: null
    parallel: false
    critical: true
    artifacts:
      - "package-lock.json"

  # Code Quality (Parallel)
  - name: "lint-code"
    command: "npm run lint -- --format=json --output-file=lint-results.json"
    working_dir: "."
    timeout: 180
    retry_count: 0
    environment: {}
    depends_on:
      - "install-dependencies"
    condition: null
    parallel: true
    critical: true
    artifacts:
      - "lint-results.json"

  - name: "type-check"
    command: "npm run type-check"
    working_dir: "."
    timeout: 120
    retry_count: 0
    environment: {}
    depends_on:
      - "install-dependencies"
    condition: null
    parallel: true
    critical: false
    artifacts: []

  # Testing (Parallel)
  - name: "unit-tests"
    command: "npm run test:unit -- --coverage --ci"
    working_dir: "."
    timeout: 900
    retry_count: 2
    environment: {}
    depends_on:
      - "install-dependencies"
    condition: null
    parallel: true
    critical: true
    artifacts:
      - "coverage/"
      - "test-results.xml"

  - name: "integration-tests"
    command: "npm run test:integration -- --ci"
    working_dir: "."
    timeout: 1200
    retry_count: 0
    environment: {}
    depends_on:
      - "install-dependencies"
    condition: null
    parallel: true
    critical: true
    artifacts:
      - "integration-results.xml"

  # Security
  - name: "security-audit"
    command: "npm audit --audit-level moderate && snyk test --json > security-report.json"
    working_dir: "."
    timeout: 300
    retry_count: 0
    environment: {}
    depends_on:
      - "install-dependencies"
    condition: null
    parallel: false
    critical: false
    artifacts:
      - "security-report.json"

  # Build
  - name: "build-application"
    command: "npm run build"
    working_dir: "."
    timeout: 600
    retry_count: 0
    environment: {}
    depends_on:
      - "lint-code"
      - "unit-tests"
      - "integration-tests"
    condition: null
    parallel: false
    critical: true
    artifacts:
      - "dist/"
      - "build-stats.json"

  # Container
  - name: "build-docker-image"
    command: "docker build -t $DOCKER_REGISTRY/webapp:$BUILD_NUMBER ."
    working_dir: "."
    timeout: 1200
    retry_count: 0
    environment:
      BUILD_NUMBER: "#{BUILD_ID}"
    depends_on:
      - "build-application"
    condition: null
    parallel: false
    critical: true
    artifacts:
      - "Dockerfile"
      - "docker-build.log"

  # Deploy
  - name: "deploy-staging"
    command: "kubectl apply -f k8s/staging/ --namespace=staging"
    working_dir: "."
    timeout: 300
    retry_count: 0
    environment: {}
    depends_on:
      - "build-docker-image"
      - "security-audit"
    condition: "$BRANCH == 'main'"
    parallel: false
    critical: true
    artifacts:
      - "k8s-staging-deployment.yaml"

# Monitoring and Hooks Configuration
monitoring:
  resource_monitoring: true
  performance_analysis: true
  health_checks: true
  
  # Hook definitions (these would be referenced in the code)
  hooks:
    pre_step:
      - name: "start_notification"
        description: "Send notification when step starts"
        enabled: true
    post_step:
      - name: "completion_notification" 
        description: "Send notification when step completes"
        enabled: true
      - name: "failure_alert"
        description: "Send alert on step failure"
        enabled: true

# Validation Settings
validation:
  configuration: true
  dependencies: true
  environment: true
  security: true

# Post-Execution Actions
post_execution:
  export_results: 
    enabled: true
    format: "json"
    filename: "production-results.json"
  
  create_dashboard:
    enabled: true
    filename: "production-dashboard.html"
  
  generate_documentation:
    enabled: true
    format: "markdown"
  
  backup_state:
    enabled: true
    path: "pipeline-backup"
  
  archive_artifacts:
    enabled: true
    filename: "production-artifacts.zip"
  
  cleanup:
    enabled: true
  
  integration_tests:
    enabled: true
  
  optimization_analysis:
    enabled: true
  
  generate_report:
    enabled: true
    type: "detailed"
```