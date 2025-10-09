# GitHubActions2Nexus Converter - Documentation

## Overview

The GitHubActions2Nexus Converter is a Python tool that transforms GitHub Actions workflow files (YAML format) into Nexus Enterprise Pipeline format.

## Installation

```bash
# Requires PyYAML for YAML parsing
pip install pyyaml
```

## Quick Start

### Basic Usage

```python
from nexus.converters.AnsibleToNexusConverter import GitHubActions2Nexus

# Create converter instance
converter = GitHubActions2Nexus()

# Convert from file
nexus_config = converter.convert_file('.github/workflows/ci.yml', 'nexus-pipeline.yaml')

# Or convert from string
workflow_content = """
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm test
"""
nexus_config = converter.convert_string(workflow_content)
```

## Input/Output Examples

### Example 1: Simple CI Pipeline

**Input (.github/workflows/ci.yml):**
```yaml
name: CI Pipeline

on:
  push:
    branches: [main]
  pull_request:

env:
  NODE_ENV: production

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
```

**Output (Nexus Configuration):**
```json
{
  "name": "CI Pipeline",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {
    "NODE_ENV": "production"
  },
  "triggers": [
    "git:push:main",
    "git:pull_request"
  ],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm run build",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

### Example 2: Matrix Builds (Parallel Execution)

**Input:**
```yaml
name: Test Matrix

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14, 16, 18, 20]
        os: [ubuntu-latest, windows-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

**Output:**
```json
{
  "name": "Test Matrix",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {},
  "triggers": ["git:push"],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "test_14_ubuntu-latest",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 14 && nvm use 14 && npm ci && npm test",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {
        "node-version": 14,
        "os": "ubuntu-latest"
      },
      "depends_on": [],
      "parallel": true,
      "critical": true
    },
    {
      "name": "test_14_windows-latest",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 14 && nvm use 14 && npm ci && npm test",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {
        "node-version": 14,
        "os": "windows-latest"
      },
      "depends_on": [],
      "parallel": true,
      "critical": true
    },
    {
      "name": "test_16_ubuntu-latest",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 16 && nvm use 16 && npm ci && npm test",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {
        "node-version": 16,
        "os": "ubuntu-latest"
      },
      "depends_on": [],
      "parallel": true,
      "critical": true
    }
    // ... additional combinations
  ]
}
```

### Example 3: Job Dependencies

**Input:**
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
      - uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
  
  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v3
      - run: npm test
  
  deploy:
    runs-on: ubuntu-latest
    needs: [build, test]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - run: ./deploy.sh
```

**Output:**
```json
{
  "name": "Build and Deploy",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {},
  "triggers": ["git:push:main"],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build && echo 'Artifacts uploaded'",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true,
      "artifacts": ["dist/"]
    },
    {
      "name": "test",
      "command": "git clone $GITHUB_REPOSITORY . && npm test",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["build"],
      "parallel": false,
      "critical": true
    },
    {
      "name": "deploy",
      "command": "git clone $GITHUB_REPOSITORY . && ./deploy.sh",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["build", "test"],
      "parallel": false,
      "critical": true,
      "condition": "$GITHUB_REF == 'refs/heads/main'"
    }
  ]
}
```

### Example 4: Docker Container Jobs

**Input:**
```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: node:18-alpine
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm run build
```

**Output:**
```json
{
  "name": "Docker Build",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {},
  "triggers": ["git:push"],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "build",
      "command": "docker run --rm -v $(pwd):/workspace -w /workspace node:18-alpine sh -c 'git clone $GITHUB_REPOSITORY . && npm install && npm run build'",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

### Example 5: Scheduled Workflows (Cron)

**Input:**
```yaml
name: Nightly Build

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
    - cron: '0 14 * * 5'  # 2 PM every Friday
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
      - run: npm run test
```

**Output:**
```json
{
  "name": "Nightly Build",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {},
  "triggers": [
    "schedule:0 2 * * *",
    "schedule:0 14 * * 5",
    "manual"
  ],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "build",
      "command": "git clone $GITHUB_REPOSITORY . && npm run build && npm run test",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

### Example 6: Docker Build and Push

**Input:**
```yaml
name: Docker CI/CD

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
```

**Output:**
```json
{
  "name": "Docker CI/CD",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {
    "REGISTRY": "ghcr.io",
    "IMAGE_NAME": "${{ github.repository }}"
  },
  "triggers": ["git:push:main"],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "docker",
      "command": "git clone $GITHUB_REPOSITORY . && echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin && docker build -t $IMAGE_NAME . && docker push $IMAGE_NAME",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

### Example 7: Multi-Language Setup

**Input:**
```yaml
name: Multi-Language Build

on: [push]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest
  
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test
  
  mobile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          distribution: 'temurin'
          java-version: '17'
      - run: ./gradlew build
```

**Output:**
```json
{
  "name": "Multi-Language Build",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {},
  "triggers": ["git:push"],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "backend",
      "command": "git clone $GITHUB_REPOSITORY . && pyenv install 3.11 && pyenv global 3.11 && pip install -r requirements.txt && pytest",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    },
    {
      "name": "frontend",
      "command": "git clone $GITHUB_REPOSITORY . && nvm install 18 && nvm use 18 && npm ci && npm test",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    },
    {
      "name": "mobile",
      "command": "git clone $GITHUB_REPOSITORY . && sdk install java 17 && ./gradlew build",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

### Example 8: Cloud Deployments

**Input:**
```yaml
name: Deploy to AWS

on:
  push:
    branches: [production]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to S3
        run: aws s3 sync ./dist s3://my-bucket
      
      - name: Invalidate CloudFront
        run: aws cloudfront create-invalidation --distribution-id ${{ secrets.CLOUDFRONT_ID }} --paths "/*"
```

**Output:**
```json
{
  "name": "Deploy to AWS",
  "version": "1.0.0",
  "description": "Converted from GitHub Actions workflow",
  "environment": {},
  "triggers": ["git:push:production"],
  "max_parallel_jobs": 10,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "deploy",
      "command": "git clone $GITHUB_REPOSITORY . && aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID && aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY && aws s3 sync ./dist s3://my-bucket && aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths \"/*\"",
      "working_dir": ".",
      "timeout": 21600,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

## Programmatic Usage

### Complete Conversion Workflow

```python
from github_actions_converter import GitHubActions2Nexus
import json

# Initialize converter
converter = GitHubActions2Nexus()

# Convert workflow file
try:
    nexus_config = converter.convert_file(
        '.github/workflows/ci.yml',
        'nexus-pipeline.yaml'
    )
    
    # Get conversion summary
    print(converter.get_conversion_summary())
    
    # Validate conversion
    is_valid, warnings = converter.validate_conversion()
    if not is_valid:
        print("Validation warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Generate migration guide
    guide = converter.generate_migration_guide()
    with open('migration-guide.md', 'w') as f:
        f.write(guide)
    
    print("Conversion successful!")
    
except Exception as e:
    print(f"Conversion failed: {e}")
```

### Batch Convert All Workflow Files

```python
from pathlib import Path
import yaml

def convert_all_workflows(workflows_dir: str, output_dir: str):
    """Convert all GitHub Actions workflows in a directory"""
    converter = GitHubActions2Nexus()
    
    # Find all workflow files
    workflow_files = list(Path(workflows_dir).glob('**/*.yml')) + \
                     list(Path(workflows_dir).glob('**/*.yaml'))
    
    results = []
    for workflow_file in workflow_files:
        try:
            # Create output path
            relative_path = workflow_file.relative_to(workflows_dir)
            output_path = Path(output_dir) / relative_path.parent / \
                         f"{workflow_file.stem}-nexus.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert
            converter.convert_file(str(workflow_file), str(output_path))
            
            # Validate
            is_valid, warnings = converter.validate_conversion()
            
            results.append({
                'file': str(workflow_file),
                'output': str(output_path),
                'valid': is_valid,
                'warnings': warnings
            })
            
            print(f"✓ Converted: {workflow_file.name}")
            
        except Exception as e:
            print(f"✗ Failed: {workflow_file.name} - {e}")
            results.append({
                'file': str(workflow_file),
                'error': str(e)
            })
    
    # Generate summary report
    with open(Path(output_dir) / 'conversion-report.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

# Usage
results = convert_all_workflows(
    '.github/workflows',
    './nexus-pipelines'
)

# Print summary
total = len(results)
successful = len([r for r in results if 'error' not in r])
print(f"\nConverted {successful}/{total} workflows successfully")
```

### Handle Custom Actions

```python
converter = GitHubActions2Nexus()

# Add custom action mappings
converter.action_mappings.update({
    'my-org/custom-action@v1': 'python scripts/custom_script.py',
    'my-org/deploy-action@v2': './deploy.sh production',
})

# Convert workflow
nexus_config = converter.convert_file('.github/workflows/custom.yml')

# Check for unmapped actions
for step in nexus_config['steps']:
    if '# Action:' in step['command']:
        print(f"Manual implementation needed: {step['name']}")
        print(f"  Command: {step['command']}")
```

### Advanced Customization

```python
def customize_nexus_pipeline(converter: GitHubActions2Nexus):
    """Apply custom modifications to converted pipeline"""
    config = converter.nexus_config
    
    # Add global timeout
    for step in config['steps']:
        if step['timeout'] > 7200:  # 2 hours
            step['timeout'] = 7200
    
    # Add retry logic for specific steps
    for step in config['steps']:
        if 'deploy' in step['name'].lower():
            step['retry_count'] = 3
            step['retry_delay'] = 60
    
    # Add notifications
    config['notifications'] = {
        'default_channels': ['slack', 'email'],
        'on_failure': True,
        'on_success': False,
        'slack': {
            'webhook_url': '$SLACK_WEBHOOK',
            'channel': '#deployments'
        },
        'email': {
            'recipients': ['team@example.com']
        }
    }
    
    # Add resource limits
    for step in config['steps']:
        step['resources'] = {
            'cpu': '2',
            'memory': '4Gi'
        }
    
    return config

converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')
customized = customize_nexus_pipeline(converter)
```

### Extract Secrets and Variables

```python
import re

def extract_secrets_from_workflow(workflow_path: str):
    """Extract all secrets and variables used in a workflow"""
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # Find all secrets references
    secrets = set(re.findall(r'\$\{\{\s*secrets\.(\w+)\s*\}\}', content))
    
    # Find all vars references
    variables = set(re.findall(r'\$\{\{\s*vars\.(\w+)\s*\}\}', content))
    
    # Find all env references
    env_vars = set(re.findall(r'\$\{\{\s*env\.(\w+)\s*\}\}', content))
    
    return {
        'secrets': list(secrets),
        'variables': list(variables),
        'env_vars': list(env_vars)
    }

# Extract and document
workflow_secrets = extract_secrets_from_workflow('.github/workflows/deploy.yml')

print("Secrets to configure in Nexus:")
for secret in workflow_secrets['secrets']:
    print(f"  - {secret}")

print("\nEnvironment variables to configure:")
for var in workflow_secrets['env_vars']:
    print(f"  - {var}")
```

### Handle Matrix Exclusions

```python
converter = GitHubActions2Nexus()

# Sample workflow with matrix
workflow = """
name: Test Matrix
on: [push]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [14, 16, 18]
        exclude:
          - os: macos-latest
            node: 14
          - os: windows-latest
            node: 14
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node }}
      - run: npm test
"""

nexus_config = converter.convert_string(workflow)

# Count matrix combinations
matrix_steps = [s for s in nexus_config['steps'] if s.get('parallel')]
print(f"Generated {len(matrix_steps)} parallel test combinations")
print(f"(Excluded 2 combinations as specified)")
```

### Compare Workflow Execution Times

```python
def estimate_execution_time(nexus_config: dict) -> dict:
    """Estimate pipeline execution time"""
    steps = nexus_config['steps']
    
    # Separate parallel and sequential steps
    parallel_steps = [s for s in steps if s.get('parallel')]
    sequential_steps = [s for s in steps if not s.get('parallel')]
    
    # Calculate times
    parallel_time = max([s['timeout'] for s in parallel_steps]) if parallel_steps else 0
    sequential_time = sum([s['timeout'] for s in sequential_steps])
    
    return {
        'max_parallel_time': parallel_time,
        'sequential_time': sequential_time,
        'total_estimated_time': parallel_time + sequential_time,
        'parallel_jobs': len(parallel_steps),
        'sequential_jobs': len(sequential_steps)
    }

converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')

timing = estimate_execution_time(converter.nexus_config)
print(f"Estimated execution time: {timing['total_estimated_time'] / 60:.1f} minutes")
print(f"Parallel jobs: {timing['parallel_jobs']}")
print(f"Sequential jobs: {timing['sequential_jobs']}")
```

## API Reference

### Main Methods

- `convert_file(workflow_file_path, output_path=None)` - Convert workflow file to Nexus format
- `convert_string(workflow_content)` - Convert workflow YAML string
- `get_conversion_summary()` - Get human-readable conversion summary
- `validate_conversion()` - Validate converted configuration
- `generate_migration_guide()` - Generate markdown migration guide

### Action Mappings

The converter includes built-in mappings for 40+ common GitHub Actions. Add custom mappings:

```python
converter.action_mappings['custom/action@v1'] = 'custom-command'
```

## Supported Features

- Multi-job workflows with dependencies
- Matrix strategy builds (parallel execution)
- Conditional execution (if statements)
- Environment variables (workflow and job level)
- Docker container jobs
- Scheduled triggers (cron)
- Multiple event triggers
- Artifacts upload/download
- Common GitHub Actions (checkout, setup-*, docker/*, aws-*, etc.)
- Working directories
- Timeouts
- Continue-on-error

## Limitations & Manual Steps Required

### Custom Actions
**Status:** Require manual implementation

**What happens:** Custom or unmapped actions are converted to placeholder comments.

**Manual steps:**
```python
# In converted config, you'll see:
# "command": "# Action: my-org/custom-action@v1 (manual implementation required)"

# Implement manually:
converter.action_mappings['my-org/custom-action@v1'] = """
python scripts/custom_action.py --param1 $PARAM1
"""

# Or add to Nexus config after conversion:
step['command'] = step['command'].replace(
    '# Action: my-org/custom-action@v1 (manual implementation required)',
    'python scripts/custom_action.py'
)
```

### Secrets Management
**Status:** Need to be configured in Nexus

**What happens:** Secret references (`${{ secrets.* }}`) are preserved as environment variable references.

**Manual steps:**
1. Extract all secrets from workflow:
```python
import re
secrets = set(re.findall(r'secrets\.(\w+)', workflow_content))
```

2. Configure in Nexus environment:
```python
config['environment'].update({
    'GITHUB_TOKEN': '$NEXUS_SECRET_GITHUB_TOKEN',
    'AWS_ACCESS_KEY_ID': '$NEXUS_SECRET_AWS_KEY',
    'DOCKER_PASSWORD': '$NEXUS_SECRET_DOCKER_PASS'
})
```

3. Set up secret storage in Nexus admin panel

### Reusable Workflows
**Status:** Not supported

**What happens:** Calls to reusable workflows (`uses: ./.github/workflows/reusable.yml`) are not converted.

**Manual steps:**
1. Convert each reusable workflow separately
2. Merge steps manually or reference as Nexus sub-pipelines
3. Map inputs and secrets appropriately

### Services (sidecar containers)
**Status:** Limited support

**What happens:** Service containers are not automatically configured.

**Manual steps:**
```yaml
# GitHub Actions:
services:
  postgres:
    image: postgres:14
    env:
      POSTGRES_PASSWORD: postgres

# Nexus - Add manually:
step['command'] = """
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres postgres:14
# Your actual commands
docker stop postgres && docker rm postgres
"""
```

### Caching
**Status:** Requires manual implementation

**What happens:** `actions/cache` is converted to a placeholder.

**Manual steps:**
```python
# Replace cache action with actual caching logic:
step['command'] = """
# Restore cache
if [ -f cache.tar.gz ]; then tar xzf cache.tar.gz; fi

# Your build commands
npm ci

# Save cache
tar czf cache.tar.gz node_modules/
"""

# Or use Nexus built-in caching if available:
step['cache'] = {
    'key': 'npm-${{ hashFiles(\'package-lock.json\') }}',
    'paths': ['node_modules/']
}
```

### Complex Matrix with Include
**Status:** Partial support

**What happens:** Basic matrix expansion works. Complex includes may need adjustment.

**Manual steps:**
```yaml
# GitHub Actions complex matrix:
strategy:
  matrix:
    os: [ubuntu, windows]
    node: [14, 16]
    include:
      - os: ubuntu
        node: 18
        experimental: true

# Manually add extra combinations after conversion:
extra_step = {
    "name": "test_ubuntu_18_experimental",
    "command": "...",
    "environment": {
        "os": "ubuntu",
        "node": 18,
        "experimental": "true"
    },
    "parallel": true
}
nexus_config['steps'].append(extra_step)
```

### Workflow Artifacts
**Status:** Basic support

**What happens:** Artifact paths are captured but upload/download logic needs implementation.

**Manual steps:**
```python
# Add artifact handling to steps:
for step in nexus_config['steps']:
    if step.get('artifacts'):
        step['command'] += f" && tar czf artifacts.tar.gz {' '.join(step['artifacts'])}"
        step['post_command'] = "curl -F 'file=@artifacts.tar.gz' $ARTIFACT_STORAGE_URL"
```

## Migration Checklist

- [ ] Convert all workflow files
- [ ] Add custom action implementations
- [ ] Configure all secrets in Nexus
- [ ] Test matrix builds for correct combinations
- [ ] Implement caching strategy if needed
- [ ] Set up artifact storage
- [ ] Configure notification channels
- [ ] Handle reusable workflows
- [ ] Test with actual repository
- [ ] Update team documentation
- [ ] Set up monitoring and alerting

## Common Patterns

### Pattern 1: PR Preview Deployments

```python
# Add preview deployment logic
for step in nexus_config['steps']:
    if step.get('condition') and 'pull_request' in str(step.get('condition')):
        pr_number = '$GITHUB_PR_NUMBER'
        step['command'] += f" && deploy-preview.sh {pr_number}"
        step['environment']['PREVIEW_URL'] = f"https://pr-{pr_number}.preview.example.com"
```

### Pattern 2: Conditional Deployment Gates

```python
# Add approval requirement for production
for step in nexus_config['steps']:
    if 'deploy' in step['name'].lower() and 'production' in step.get('condition', ''):
        step['approval_required'] = True
        step['approval_config'] = {
            'message': 'Approve production deployment?',
            'approvers': ['devops-team@example.com'],
            'timeout': 3600
        }
```

### Pattern 3: Multi-Environment Deployments

# GitHubActions2Nexus Converter - Documentation (Continued)

### Pattern 3: Multi-Environment Deployments (continued)

```python
environments = ['staging', 'production']
deploy_steps = []

for env in environments:
    deploy_step = {
        'name': f'deploy-{env}',
        'command': f'./deploy.sh {env}',
        'environment': {'ENVIRONMENT': env},
        'depends_on': ['test'],
        'timeout': 1800,
        'retry_count': 2 if env == 'production' else 0
    }
    
    if env == 'production':
        deploy_step['condition'] = "$GITHUB_REF == 'refs/heads/main'"
        deploy_step['approval_required'] = True
    
    deploy_steps.append(deploy_step)

nexus_config['steps'].extend(deploy_steps)
```

### Pattern 4: Rollback on Failure

```python
# Add rollback steps for each deployment
for i, step in enumerate(nexus_config['steps']):
    if 'deploy' in step['name'].lower():
        rollback_step = {
            'name': f"{step['name']}-rollback",
            'command': './rollback.sh',
            'environment': step['environment'],
            'depends_on': [step['name']],
            'condition': 'failure()',
            'timeout': 600,
            'critical': False
        }
        nexus_config['steps'].insert(i + 1, rollback_step)
```

## Advanced Usage Examples

### Example 1: Converting GitHub Action Contexts

```python
def convert_github_contexts(command: str) -> str:
    """Convert GitHub context references to Nexus equivalents"""
    conversions = {
        '${{ github.sha }}': '$GIT_COMMIT',
        '${{ github.ref }}': '$GIT_REF',
        '${{ github.ref_name }}': '$GIT_BRANCH',
        '${{ github.repository }}': '$GITHUB_REPOSITORY',
        '${{ github.actor }}': '$GITHUB_ACTOR',
        '${{ github.event_name }}': '$GITHUB_EVENT',
        '${{ github.run_id }}': '$NEXUS_RUN_ID',
        '${{ github.run_number }}': '$NEXUS_BUILD_NUMBER',
        '${{ runner.os }}': '$RUNNER_OS',
        '${{ runner.temp }}': '$RUNNER_TEMP',
        '${{ job.status }}': '$JOB_STATUS',
    }
    
    for github_ctx, nexus_var in conversions.items():
        command = command.replace(github_ctx, nexus_var)
    
    return command

# Apply to all steps after conversion
converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')

for step in converter.nexus_config['steps']:
    step['command'] = convert_github_contexts(step['command'])
```

### Example 2: Composite Actions Handling

```python
def parse_composite_action(action_path: str) -> dict:
    """Parse a composite action YAML file"""
    with open(action_path, 'r') as f:
        action_data = yaml.safe_load(f)
    
    return {
        'name': action_data.get('name'),
        'inputs': action_data.get('inputs', {}),
        'runs': action_data.get('runs', {})
    }

def expand_composite_action(step: dict, composite: dict) -> list:
    """Expand a composite action into multiple commands"""
    commands = []
    
    if composite['runs'].get('using') == 'composite':
        for sub_step in composite['runs'].get('steps', []):
            if 'run' in sub_step:
                commands.append(sub_step['run'])
    
    return commands

# Use when encountering custom composite actions
converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')

for step in converter.nexus_config['steps']:
    if './.github/actions/' in step.get('command', ''):
        # Extract action path
        action_match = re.search(r'\./.github/actions/([^@\s]+)', step['command'])
        if action_match:
            action_name = action_match.group(1)
            action_path = f'.github/actions/{action_name}/action.yml'
            
            if Path(action_path).exists():
                composite = parse_composite_action(action_path)
                expanded = expand_composite_action(step, composite)
                step['command'] = ' && '.join(expanded)
```

### Example 3: Environment-Specific Configuration

```python
def apply_environment_config(nexus_config: dict, env_name: str, env_config: dict):
    """Apply environment-specific configurations"""
    
    # Add environment variables
    nexus_config['environment'].update(env_config.get('vars', {}))
    
    # Update deployment steps
    for step in nexus_config['steps']:
        if 'deploy' in step['name'].lower():
            step['environment'].update({
                'ENVIRONMENT': env_name,
                'API_URL': env_config.get('api_url'),
                'REGION': env_config.get('region', 'us-east-1')
            })
            
            # Add environment-specific approvers
            if env_name == 'production':
                step['approval_config'] = {
                    'approvers': env_config.get('approvers', []),
                    'required_approvals': env_config.get('required_approvals', 2)
                }

# Usage
converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/deploy.yml')

environments = {
    'staging': {
        'vars': {'LOG_LEVEL': 'debug'},
        'api_url': 'https://api.staging.example.com',
        'region': 'us-west-2'
    },
    'production': {
        'vars': {'LOG_LEVEL': 'info'},
        'api_url': 'https://api.example.com',
        'region': 'us-east-1',
        'approvers': ['lead@example.com', 'ops@example.com'],
        'required_approvals': 2
    }
}

for env_name, env_config in environments.items():
    apply_environment_config(converter.nexus_config, env_name, env_config)
```

### Example 4: Monitoring and Metrics Integration

```python
def add_monitoring_to_pipeline(nexus_config: dict):
    """Add monitoring and metrics to pipeline steps"""
    
    # Add monitoring wrapper to each step
    for step in nexus_config['steps']:
        original_command = step['command']
        
        step['command'] = f"""
        # Start timing
        START_TIME=$(date +%s)
        
        # Send start event
        curl -X POST $METRICS_URL/events \
            -d '{{"pipeline": "{nexus_config["name"]}", "step": "{step["name"]}", "status": "started"}}'
        
        # Execute original command
        {original_command}
        RESULT=$?
        
        # Calculate duration
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        # Send completion event
        curl -X POST $METRICS_URL/events \
            -d '{{"pipeline": "{nexus_config["name"]}", "step": "{step["name"]}", "status": "completed", "duration": "'$DURATION'", "exit_code": "'$RESULT'"}}'
        
        exit $RESULT
        """
    
    # Add final summary step
    summary_step = {
        'name': 'pipeline-summary',
        'command': 'curl -X POST $METRICS_URL/summary -d \'{"pipeline": "' + nexus_config["name"] + '", "status": "completed"}\'',
        'depends_on': [step['name'] for step in nexus_config['steps'] if not step.get('parallel')],
        'timeout': 60,
        'retry_count': 0,
        'critical': False
    }
    
    nexus_config['steps'].append(summary_step)

converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')
add_monitoring_to_pipeline(converter.nexus_config)
```

### Example 5: Dynamic Step Generation

```python
def generate_deployment_steps(services: list, environment: str) -> list:
    """Generate deployment steps for multiple microservices"""
    steps = []
    
    # Build all services in parallel
    for service in services:
        build_step = {
            'name': f'build-{service}',
            'command': f'docker build -t {service}:latest ./{service}',
            'working_dir': f'./{service}',
            'timeout': 1200,
            'parallel': True,
            'artifacts': [f'{service}/dist/**']
        }
        steps.append(build_step)
    
    # Test all services in parallel (depends on builds)
    for service in services:
        test_step = {
            'name': f'test-{service}',
            'command': f'cd ./{service} && npm test',
            'depends_on': [f'build-{service}'],
            'timeout': 600,
            'parallel': True
        }
        steps.append(test_step)
    
    # Deploy services sequentially to avoid conflicts
    for i, service in enumerate(services):
        deploy_step = {
            'name': f'deploy-{service}',
            'command': f'kubectl apply -f ./{service}/k8s/{environment}.yaml',
            'depends_on': [f'test-{service}'] + ([f'deploy-{services[i-1]}'] if i > 0 else []),
            'environment': {'SERVICE': service, 'ENV': environment},
            'timeout': 900,
            'retry_count': 2
        }
        steps.append(deploy_step)
    
    return steps

# Usage
converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/microservices.yml')

services = ['api', 'frontend', 'worker', 'notifications']
deployment_steps = generate_deployment_steps(services, 'production')

# Replace or append to existing steps
converter.nexus_config['steps'].extend(deployment_steps)
```

## Troubleshooting Guide

### Issue 1: Matrix Builds Generate Too Many Steps

**Problem:** Matrix expansion creates hundreds of parallel steps.

**Solution:**
```python
def limit_matrix_parallelism(nexus_config: dict, max_parallel: int = 10):
    """Limit the number of parallel matrix jobs"""
    parallel_steps = [s for s in nexus_config['steps'] if s.get('parallel')]
    
    if len(parallel_steps) > max_parallel:
        # Group parallel steps into batches
        for i, step in enumerate(parallel_steps):
            batch_num = i // max_parallel
            if batch_num > 0:
                step['depends_on'] = [parallel_steps[i - max_parallel]['name']]
                step['parallel'] = False

converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/matrix.yml')
limit_matrix_parallelism(converter.nexus_config, max_parallel=5)
```

### Issue 2: Long Commands Exceed Shell Limits

**Problem:** Combined commands are too long for single execution.

**Solution:**
```python
def split_long_commands(step: dict, max_length: int = 2000):
    """Split long commands into multiple steps"""
    command = step['command']
    
    if len(command) > max_length:
        # Split on && operators
        parts = [part.strip() for part in command.split('&&')]
        
        # Create multiple steps
        new_steps = []
        for i, part in enumerate(parts):
            new_step = step.copy()
            new_step['name'] = f"{step['name']}_part_{i+1}"
            new_step['command'] = part
            new_step['depends_on'] = [f"{step['name']}_part_{i}"] if i > 0 else step.get('depends_on', [])
            new_steps.append(new_step)
        
        return new_steps
    
    return [step]

# Apply to all steps
converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')

new_steps = []
for step in converter.nexus_config['steps']:
    new_steps.extend(split_long_commands(step))

converter.nexus_config['steps'] = new_steps
```

### Issue 3: Missing Action Mappings

**Problem:** Unknown actions are converted to placeholders.

**Solution:**
```python
def analyze_unmapped_actions(nexus_config: dict) -> list:
    """Find all unmapped actions"""
    unmapped = []
    
    for step in nexus_config['steps']:
        if '# Action:' in step['command']:
            match = re.search(r'# Action: ([^\s]+)', step['command'])
            if match:
                unmapped.append({
                    'step': step['name'],
                    'action': match.group(1)
                })
    
    return unmapped

converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')

unmapped = analyze_unmapped_actions(converter.nexus_config)
if unmapped:
    print("Unmapped actions requiring manual implementation:")
    for item in unmapped:
        print(f"  Step: {item['step']}")
        print(f"  Action: {item['action']}")
        print(f"  → Implement in: converter.action_mappings['{item['action']}']")
        print()
```

## Performance Optimization

### Optimize Sequential Steps

```python
def optimize_sequential_execution(nexus_config: dict):
    """Merge compatible sequential steps"""
    optimized_steps = []
    buffer = None
    
    for step in nexus_config['steps']:
        # Skip parallel steps
        if step.get('parallel'):
            if buffer:
                optimized_steps.append(buffer)
                buffer = None
            optimized_steps.append(step)
            continue
        
        # Try to merge with buffer
        if buffer and not step.get('depends_on') and not buffer.get('condition'):
            # Merge commands
            buffer['command'] += f" && {step['command']}"
            buffer['timeout'] += step['timeout']
            
            # Merge artifacts
            if step.get('artifacts'):
                buffer.setdefault('artifacts', []).extend(step['artifacts'])
        else:
            if buffer:
                optimized_steps.append(buffer)
            buffer = step.copy()
    
    if buffer:
        optimized_steps.append(buffer)
    
    nexus_config['steps'] = optimized_steps

converter = GitHubActions2Nexus()
converter.convert_file('.github/workflows/ci.yml')
optimize_sequential_execution(converter.nexus_config)
```

## Complete Real-World Example

```python
#!/usr/bin/env python3
"""
Complete GitHub Actions to Nexus conversion script
"""

from pathlib import Path
import json
import yaml
from github_actions_converter import GitHubActions2Nexus

def main():
    # Configuration
    WORKFLOWS_DIR = Path('.github/workflows')
    OUTPUT_DIR = Path('nexus-pipelines')
    
    # Initialize converter
    converter = GitHubActions2Nexus()
    
    # Add custom action mappings
    converter.action_mappings.update({
        'company/custom-build@v1': './scripts/build.sh',
        'company/deploy-action@v2': './scripts/deploy.sh',
    })
    
    # Find all workflows
    workflows = list(WORKFLOWS_DIR.glob('*.yml')) + list(WORKFLOWS_DIR.glob('*.yaml'))
    
    print(f"Found {len(workflows)} workflow files")
    print("=" * 60)
    
    results = []
    
    for workflow_file in workflows:
        print(f"\nProcessing: {workflow_file.name}")
        
        try:
            # Convert
            output_file = OUTPUT_DIR / f"{workflow_file.stem}-nexus.yaml"
            OUTPUT_DIR.mkdir(exist_ok=True)
            
            nexus_config = converter.convert_file(str(workflow_file), str(output_file))
            
            # Validate
            is_valid, warnings = converter.validate_conversion()
            
            # Apply optimizations
            optimize_sequential_execution(nexus_config)
            
            # Add monitoring
            add_monitoring_to_pipeline(nexus_config)
            
            # Save updated config
            with open(output_file, 'w') as f:
                yaml.dump(nexus_config, f, default_flow_style=False, sort_keys=False)
            
            # Generate migration guide
            guide_file = OUTPUT_DIR / f"{workflow_file.stem}-migration.md"
            with open(guide_file, 'w') as f:
                f.write(converter.generate_migration_guide())
            
            results.append({
                'workflow': workflow_file.name,
                'output': str(output_file),
                'valid': is_valid,
                'warnings': warnings,
                'steps': len(nexus_config['steps'])
            })
            
            print(f"  ✓ Converted successfully")
            print(f"  → Output: {output_file}")
            print(f"  → Steps: {len(nexus_config['steps'])}")
            
            if warnings:
                print(f"  ⚠ Warnings: {len(warnings)}")
        
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            results.append({
                'workflow': workflow_file.name,
                'error': str(e)
            })
    
    # Generate summary report
    summary_file = OUTPUT_DIR / 'conversion-summary.json'
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"Total workflows: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"\nResults saved to: {summary_file}")

if __name__ == '__main__':
    main()
```

## License

MIT

---

## Quick Reference Card

### Convert a workflow
```python
converter = GitHubActions2Nexus()
nexus_config = converter.convert_file('workflow.yml', 'nexus.yaml')
```

### Get summary
```python
print(converter.get_conversion_summary())
```

### Validate
```python
is_valid, warnings = converter.validate_conversion()
```

### Add custom action
```python
converter.action_mappings['my-action@v1'] = 'my-command'
```

### Handle secrets
```python
config['environment']['SECRET_NAME'] = '$NEXUS_SECRET_NAME'
```

### Migration guide
```python
guide = converter.generate_migration_guide()
```