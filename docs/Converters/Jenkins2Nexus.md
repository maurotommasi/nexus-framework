# Jenkins2Nexus Converter - Documentation

## Overview

The Jenkins2Nexus Converter is a Python tool that transforms Jenkins pipeline definitions (both Declarative and Scripted syntax) into Nexus Enterprise Pipeline format.

## Installation

```bash
# No external dependencies required beyond standard library
# Optional: Install PyYAML for YAML output support
pip install pyyaml
```

## Quick Start

### Basic Usage

```python
from jenkins2nexus import Jenkins2Nexus

# Create converter instance
converter = Jenkins2Nexus()

# Convert from file
nexus_config = converter.convert_file('Jenkinsfile', 'nexus-pipeline.yaml')

# Or convert from string
jenkins_content = """
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
    }
}
"""
nexus_config = converter.convert_string(jenkins_content)
```

## Input/Output Examples

### Example 1: Simple Build Pipeline

**Input (Jenkinsfile):**
```groovy
pipeline {
    agent any
    
    environment {
        APP_NAME = 'myapp'
        VERSION = '1.0.0'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'npm install'
                sh 'npm run build'
            }
        }
        
        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
    }
}
```

**Output (Nexus Configuration):**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {
    "APP_NAME": "myapp",
    "VERSION": "1.0.0"
  },
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Build",
      "command": "npm install && npm run build",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    },
    {
      "name": "Test",
      "command": "npm test",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["Build"],
      "parallel": false,
      "critical": true
    }
  ]
}
```

### Example 2: Parallel Execution

**Input:**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'npm run test:unit'
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh 'npm run test:integration'
                    }
                }
                stage('E2E Tests') {
                    steps {
                        sh 'npm run test:e2e'
                    }
                }
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Unit Tests",
      "command": "npm run test:unit",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": true,
      "critical": true
    },
    {
      "name": "Integration Tests",
      "command": "npm run test:integration",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": true,
      "critical": true
    },
    {
      "name": "E2E Tests",
      "command": "npm run test:e2e",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": true,
      "critical": true
    }
  ]
}
```

### Example 3: Conditional Execution

**Input:**
```groovy
pipeline {
    agent any
    
    parameters {
        string(name: 'ENVIRONMENT', defaultValue: 'staging', description: 'Deployment environment')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run tests')
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
        
        stage('Test') {
            when {
                expression { params.RUN_TESTS == true }
            }
            steps {
                sh 'make test'
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                sh 'make deploy-prod'
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Build",
      "command": "make build",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    },
    {
      "name": "Test",
      "command": "make test",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["Build"],
      "parallel": false,
      "critical": true,
      "condition": "params.RUN_TESTS == true"
    },
    {
      "name": "Deploy to Production",
      "command": "make deploy-prod",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["Test"],
      "parallel": false,
      "critical": true,
      "condition": "$BRANCH_NAME == 'main'"
    }
  ]
}
```

### Example 4: Docker Agent Conversion

**Input:**
```groovy
pipeline {
    agent {
        docker {
            image 'node:16-alpine'
            args '-v /tmp:/tmp'
        }
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'npm install'
                sh 'npm run build'
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Build",
      "command": "npm install && npm run build",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

**Note:** Docker agent is converted to standard agent. Manual configuration required for container execution.

### Example 5: Complex When Conditions

**Input:**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Deploy') {
            when {
                allOf {
                    branch 'main'
                    environment name: 'DEPLOY_ENV', value: 'production'
                    expression { currentBuild.result == 'SUCCESS' }
                }
            }
            steps {
                sh 'make deploy'
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Deploy",
      "command": "make deploy",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true,
      "condition": "$DEPLOY_ENV == 'production'"
    }
  ]
}
```

**Note:** Complex when conditions with `allOf`, `anyOf`, or `not` require manual adjustment in Nexus.

### Example 6: Tools Configuration

**Input:**
```groovy
pipeline {
    agent any
    
    tools {
        maven 'Maven 3.8.6'
        jdk 'JDK 11'
        nodejs 'NodeJS 16'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean install'
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Build",
      "command": "mvn clean install",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    }
  ]
}
```

**Note:** Tools configuration not directly supported. You need to manually configure tool paths in environment variables:
```json
{
  "environment": {
    "MAVEN_HOME": "/usr/local/maven-3.8.6",
    "JAVA_HOME": "/usr/lib/jvm/java-11",
    "PATH": "/usr/local/maven-3.8.6/bin:$PATH"
  }
}
```

### Example 7: Input Steps

**Input:**
```groovy
pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
        
        stage('Approve Deployment') {
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'make deploy'
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Build",
      "command": "make build",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    },
    {
      "name": "Approve Deployment",
      "command": "echo 'No commands'",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["Build"],
      "parallel": false,
      "critical": true
    },
    {
      "name": "Deploy",
      "command": "make deploy",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["Approve Deployment"],
      "parallel": false,
      "critical": true
    }
  ]
}
```

**Manual Implementation Required:**
```python
# Implement approval gate in Nexus
nexus_config['steps'][1] = {
    "name": "Approve Deployment",
    "command": "echo 'Waiting for approval'",
    "approval_required": True,
    "approval_config": {
        "message": "Deploy to production?",
        "approvers": ["team-lead@example.com"],
        "timeout": 86400  # 24 hours
    },
    "depends_on": ["Build"],
    "parallel": false,
    "critical": true
}
```

### Example 8: Shared Libraries

**Input:**
```groovy
@Library('my-shared-library@v1.0.0') _

pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                // Using shared library function
                buildApplication(
                    language: 'nodejs',
                    version: '16'
                )
            }
        }
        
        stage('Deploy') {
            steps {
                // Another shared library function
                deployToKubernetes(
                    environment: 'production',
                    replicas: 3
                )
            }
        }
    }
}
```

**Output:**
```json
{
  "name": "converted-pipeline",
  "version": "1.0.0",
  "description": "Converted from Jenkins pipeline",
  "environment": {},
  "triggers": [],
  "max_parallel_jobs": 5,
  "artifacts_retention": 30,
  "steps": [
    {
      "name": "Build",
      "command": "echo 'No commands'",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": [],
      "parallel": false,
      "critical": true
    },
    {
      "name": "Deploy",
      "command": "echo 'No commands'",
      "working_dir": ".",
      "timeout": 300,
      "retry_count": 0,
      "environment": {},
      "depends_on": ["Build"],
      "parallel": false,
      "critical": true
    }
  ]
}
```

**Manual Porting Required:**
```python
# Extract shared library functions and port to Nexus scripts
shared_libraries = converter.handle_shared_libraries(jenkins_content)
# Returns: ['my-shared-library@v1.0.0']

# You need to manually implement these as Nexus steps:
nexus_config['steps'][0] = {
    "name": "Build",
    "command": """
        # Port of buildApplication function
        export NODE_VERSION=16
        nvm use $NODE_VERSION
        npm install
        npm run build
    """,
    "working_dir": ".",
    "timeout": 600,
    "retry_count": 1,
    "environment": {"NODE_VERSION": "16"},
    "depends_on": [],
    "parallel": false,
    "critical": true
}

nexus_config['steps'][1] = {
    "name": "Deploy",
    "command": """
        # Port of deployToKubernetes function
        kubectl set image deployment/myapp myapp=myapp:${VERSION}
        kubectl scale deployment/myapp --replicas=3
        kubectl rollout status deployment/myapp
    """,
    "working_dir": ".",
    "timeout": 1200,
    "retry_count": 2,
    "environment": {"REPLICAS": "3", "ENVIRONMENT": "production"},
    "depends_on": ["Build"],
    "parallel": false,
    "critical": true
}
```

## Programmatic Usage

### Complete Conversion Workflow

```python
from jenkins2nexus import Jenkins2Nexus
import json

# Initialize converter
converter = Jenkins2Nexus()

# Convert Jenkinsfile
try:
    nexus_config = converter.convert_file('Jenkinsfile', 'nexus-pipeline.yaml')
    
    # Get conversion summary
    print(converter.get_conversion_summary())
    
    # Validate the conversion
    is_valid, warnings = converter.validate_conversion()
    if not is_valid:
        print("Validation warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Check for unsupported features
    unsupported = converter.get_unsupported_features()
    if unsupported:
        print("\nUnsupported features:")
        for feature in unsupported:
            print(f"  - {feature}")
    
    # Generate migration guide
    guide = converter.generate_migration_guide()
    with open('migration-guide.md', 'w') as f:
        f.write(guide)
    
    print("\nConversion successful!")
    
except Exception as e:
    print(f"Conversion failed: {e}")
```

### Advanced Options

```python
# Convert with custom options
converter = Jenkins2Nexus()
converter.convert_file('Jenkinsfile')

# Apply best practices
converter.add_nexus_best_practices()

# Optimize pipeline (merge sequential steps)
converter.optimize_converted_pipeline()

# Convert with all options
nexus_config = converter.convert_with_options({
    'merge_sequential_steps': True,
    'apply_best_practices': True,
    'optimize': True,
    'add_logging': True
})

# Save as YAML
converter._save_nexus_config('optimized-pipeline.yaml')
```

### Credential Mapping

```python
# Map Jenkins credentials to Nexus environment variables
credential_map = {
    'github-token': 'GITHUB_TOKEN',
    'docker-registry': 'DOCKER_PASSWORD',
    'aws-credentials': 'AWS_SECRET_KEY'
}

converter = Jenkins2Nexus()
converter.convert_file('Jenkinsfile')
converter.convert_with_credentials(credential_map)

nexus_config = converter.nexus_config
```

### Handling Limitations Programmatically

```python
from jenkins2nexus import Jenkins2Nexus
import json

converter = Jenkins2Nexus()
converter.convert_file('Jenkinsfile')

# Get shared libraries that need manual porting
shared_libs = converter.handle_shared_libraries(open('Jenkinsfile').read())
if shared_libs:
    print(f"Shared libraries detected: {shared_libs}")
    print("These need to be manually ported to Nexus scripts")

# Handle Docker agents
if converter.jenkins_pipeline.agent.type == "docker":
    print(f"Docker agent detected: {converter.jenkins_pipeline.agent.docker_image}")
    print("Manual configuration required:")
    print("  1. Set up container runtime in Nexus")
    print("  2. Configure image pull credentials")
    print(f"  3. Add docker image to step config: {converter.jenkins_pipeline.agent.docker_image}")
    
    # Add Docker configuration to steps
    for step in converter.nexus_config['steps']:
        step['container'] = {
            'image': converter.jenkins_pipeline.agent.docker_image,
            'pull_policy': 'Always'
        }

# Handle complex when conditions
for i, stage in enumerate(converter.jenkins_pipeline.stages):
    if stage.when_condition and ('&&' in stage.when_condition or '||' in stage.when_condition):
        print(f"Complex condition in stage '{stage.name}': {stage.when_condition}")
        print("Consider breaking into multiple steps with simpler conditions")

# Handle tools configuration
if converter.jenkins_pipeline.tools:
    print("Tools configuration detected:")
    for tool, version in converter.jenkins_pipeline.tools.items():
        print(f"  {tool}: {version}")
    print("Add these to environment variables manually")
    
    # Automatically add tool environment variables
    tool_env = {}
    for tool, version in converter.jenkins_pipeline.tools.items():
        if tool == 'maven':
            tool_env['MAVEN_HOME'] = f'/usr/local/maven-{version}'
            tool_env['PATH'] = f'/usr/local/maven-{version}/bin:$PATH'
        elif tool == 'jdk':
            tool_env['JAVA_HOME'] = f'/usr/lib/jvm/java-{version}'
        elif tool == 'nodejs':
            tool_env['NODE_VERSION'] = version
    
    converter.nexus_config['environment'].update(tool_env)

# Save updated configuration
with open('nexus-pipeline-updated.yaml', 'w') as f:
    import yaml
    yaml.dump(converter.nexus_config, f, default_flow_style=False)
```

### Batch Conversion

```python
from pathlib import Path

def convert_all_jenkinsfiles(directory: str, output_dir: str):
    """Convert all Jenkinsfiles in a directory"""
    converter = Jenkins2Nexus()
    
    # Find all Jenkinsfiles
    jenkinsfiles = list(Path(directory).rglob('Jenkinsfile*'))
    
    results = []
    for jenkins_file in jenkinsfiles:
        try:
            # Create output path
            relative_path = jenkins_file.relative_to(directory)
            output_path = Path(output_dir) / relative_path.parent / 'nexus-pipeline.yaml'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert
            converter.convert_file(str(jenkins_file), str(output_path))
            
            # Validate
            is_valid, warnings = converter.validate_conversion()
            
            results.append({
                'file': str(jenkins_file),
                'output': str(output_path),
                'valid': is_valid,
                'warnings': warnings
            })
            
            print(f"Converted: {jenkins_file}")
            
        except Exception as e:
            print(f"Failed: {jenkins_file} - {e}")
            results.append({
                'file': str(jenkins_file),
                'error': str(e)
            })
    
    return results

# Usage
results = convert_all_jenkinsfiles('./jenkins-pipelines', './nexus-pipelines')
```

### Export Comparison Report

```python
converter = Jenkins2Nexus()
converter.convert_file('Jenkinsfile')

# Export detailed comparison
converter.export_comparison_report('conversion-report.json')

# The report includes:
# - Original Jenkins configuration
# - Converted Nexus configuration
# - Conversion metrics
# - Unsupported features
# - Validation results
```

### Custom Post-Processing

```python
def customize_nexus_config(converter: Jenkins2Nexus):
    """Add custom modifications to converted config"""
    config = converter.nexus_config
    
    # Add custom environment variables
    config['environment']['CUSTOM_VAR'] = 'custom_value'
    
    # Modify timeouts for all steps
    for step in config['steps']:
        if 'test' in step['name'].lower():
            step['timeout'] = 600  # 10 minutes for tests
    
    # Add notification configuration
    config['notifications'] = {
        'default_channels': ['email', 'slack'],
        'on_failure': True,
        'on_success': True,
        'email': {
            'recipients': ['team@example.com']
        },
        'slack': {
            'channel': '#ci-notifications'
        }
    }
    
    return config

converter = Jenkins2Nexus()
converter.convert_file('Jenkinsfile')
customized_config = customize_nexus_config(converter)
```

## API Reference

### Main Methods

- `convert_file(jenkins_file_path, output_path=None)` - Convert Jenkinsfile to Nexus format
- `convert_string(jenkins_content)` - Convert Jenkins pipeline string
- `get_conversion_summary()` - Get human-readable conversion summary
- `validate_conversion()` - Validate converted configuration
- `get_unsupported_features()` - List unsupported Jenkins features
- `generate_migration_guide()` - Generate markdown migration guide
- `add_nexus_best_practices()` - Apply Nexus best practices
- `optimize_converted_pipeline()` - Optimize the pipeline
- `convert_with_credentials(credential_map)` - Map credentials
- `export_comparison_report(output_path)` - Export detailed comparison
- `handle_shared_libraries(content)` - Extract shared library references

## Supported Features

- Declarative and Scripted pipelines
- Sequential and parallel stages
- Environment variables
- Parameters (string, boolean)
- Triggers (cron, pollSCM, upstream)
- Conditional execution (when blocks)
- Post actions (success, failure, always)
- Timeouts and retries
- Shell commands
- Docker operations
- Git checkout

## Limitations & Manual Steps Required

### Docker Agents
**Status:** Converted to standard agents

**What happens:** The Docker image reference is removed and converted to a standard agent.

**Manual steps:**
1. Configure container runtime in Nexus execution environment
2. Add container configuration to each step:
```python
step['container'] = {
    'image': 'node:16-alpine',
    'pull_policy': 'Always',
    'volumes': ['/tmp:/tmp']
}
```
3. Set up image pull credentials if using private registries

### Complex When Conditions
**Status:** Simplified or may need adjustment

**What happens:** Conditions with `allOf`, `anyOf`, `not`, or complex logical operators are simplified to basic expressions.

**Manual steps:**
1. Review all converted conditions
2. For complex logic, break into multiple steps:
```python
# Instead of: allOf { branch 'main'; environment name: 'ENV', value: 'prod' }
# Use multiple conditional steps:
{
    "name": "Check Branch",
    "condition": "$BRANCH_NAME == 'main'",
    "command": "echo 'Branch check passed'"
},
{
    "name": "Deploy",
    "condition": "$ENV == 'prod'",
    "depends_on": ["Check Branch"],
    "command": "make deploy"
}
```

### Tools Configuration
**Status:** Not directly supported

**What happens:** Tools declarations are removed from the converted configuration.

**Manual steps:**
1. Add tool paths to environment variables:
```python
config['environment'].update({
    'MAVEN_HOME': '/usr/local/maven-3.8.6',
    'JAVA_HOME': '/usr/lib/jvm/java-11',
    'NODE_VERSION': '16',
    'PATH': '/usr/local/maven-3.8.6/bin:$JAVA_HOME/bin:$PATH'
})
```
2. Install required tools on Nexus agents
3. Configure tool version management in Nexus

### Input Steps
**Status:** Require manual implementation

**What happens:** Input steps are converted to empty echo commands.

**Manual steps:**
1. Implement approval gates using Nexus approval mechanism:
```python
step['approval_required'] = True
step['approval_config'] = {
    'message': 'Deploy to production?',
    'approvers': ['team-lead@example.com', 'devops@example.com'],
    'timeout': 86400,  # 24 hours
    'required_approvals': 2
}
```
2. Or implement external approval via API call:
```python
step['command'] = """
curl -X POST https://approval-service/api/request \
    -d '{"message":"Deploy to production?","pipeline":"${PIPELINE_ID}"}' &&
while [ $(curl https://approval-service/api/status/${APPROVAL_ID}) != "approved" ]; do
    sleep 30
done
"""
```

### Shared Libraries
**Status:** Need manual porting

**What happens:** Shared library calls are removed. Steps using library functions become empty.

**Manual steps:**
1. Extract shared library code from Jenkins
2. Port functions to standalone scripts:
```bash
# Create shared scripts directory
mkdir -p nexus-scripts/

# Port each library function
# Example: vars/buildApplication.groovy -> nexus-scripts/build-application.sh
```
3. Update Nexus configuration to call scripts:
```python
step['command'] = """
source ./nexus-scripts/common.sh
build_application "nodejs" "16"
"""
```
4. Or convert to Nexus step templates
5. Maintain scripts in version control separately

## Migration Checklist

After conversion, verify these items:

- [ ] Review all converted steps for accuracy
- [ ] Add container configurations if using Docker agents
- [ ] Simplify or split complex when conditions
- [ ] Add tool paths to environment variables
- [ ] Implement approval gates for input steps
- [ ] Port shared library functions to scripts
- [ ] Update credential references
- [ ] Configure notification channels
- [ ] Set artifact storage locations
- [ ] Test in non-production environment
- [ ] Update documentation for team

## License

MIT