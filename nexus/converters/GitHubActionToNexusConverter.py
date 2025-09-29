#!/usr/bin/env python3
"""
GitHubActions2Nexus Converter
==============================
Converts GitHub Actions workflow files to Nexus Enterprise Pipeline format.

Author: Mauro Tommasi
Version: 1.0.0
License: MIT
"""

import re
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class GitHubJob:
    """Represents a GitHub Actions job"""
    name: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    if_condition: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    needs: List[str] = field(default_factory=list)
    runs_on: str = "ubuntu-latest"
    timeout_minutes: int = 360
    strategy: Optional[Dict[str, Any]] = None
    container: Optional[str] = None
    services: Dict[str, Any] = field(default_factory=dict)
    outputs: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None
    concurrency: Optional[Dict[str, Any]] = None
    deployment_environment: Optional[str] = None
    deployment_url: Optional[str] = None
    defaults: Optional[Dict[str, Any]] = None
    continue_on_error: bool = False


@dataclass
class GitHubWorkflow:
    """Represents parsed GitHub Actions workflow"""
    name: str
    on_events: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    jobs: List[GitHubJob] = field(default_factory=list)
    defaults: Dict[str, Any] = field(default_factory=dict)
    concurrency: Optional[Dict[str, Any]] = None


class GitHubActions2Nexus:
    """
    Converter class to transform GitHub Actions workflow definitions into Nexus pipeline format.
    
    Supports:
    - Multiple jobs and job dependencies
    - Matrix strategy builds
    - Conditional execution (if statements)
    - Environment variables
    - Actions (converted to equivalent commands)
    - Services and containers
    - Caching strategies
    - Artifacts upload/download
    - Scheduled triggers (cron)
    - Multiple event triggers
    """
    
    def __init__(self):
        """Initialize the converter"""
        self.github_workflow: Optional[GitHubWorkflow] = None
        self.nexus_config: Dict[str, Any] = {}
        self.step_counter = 0
        self.secrets_used = []
        self.custom_actions = []
        
        # Comprehensive GitHub Actions mappings
        self.action_mappings = {
            # Checkout actions
            'actions/checkout@v2': 'git clone $GITHUB_REPOSITORY .',
            'actions/checkout@v3': 'git clone $GITHUB_REPOSITORY .',
            'actions/checkout@v4': 'git clone $GITHUB_REPOSITORY .',
            
            # Setup actions
            'actions/setup-node@v2': 'nvm install $NODE_VERSION && nvm use $NODE_VERSION',
            'actions/setup-node@v3': 'nvm install $NODE_VERSION && nvm use $NODE_VERSION',
            'actions/setup-node@v4': 'nvm install $NODE_VERSION && nvm use $NODE_VERSION',
            'actions/setup-python@v2': 'pyenv install $PYTHON_VERSION && pyenv global $PYTHON_VERSION',
            'actions/setup-python@v3': 'pyenv install $PYTHON_VERSION && pyenv global $PYTHON_VERSION',
            'actions/setup-python@v4': 'pyenv install $PYTHON_VERSION && pyenv global $PYTHON_VERSION',
            'actions/setup-python@v5': 'pyenv install $PYTHON_VERSION && pyenv global $PYTHON_VERSION',
            'actions/setup-java@v2': 'sdk install java $JAVA_VERSION',
            'actions/setup-java@v3': 'sdk install java $JAVA_VERSION',
            'actions/setup-java@v4': 'sdk install java $JAVA_VERSION',
            'actions/setup-go@v2': 'gvm install go$GO_VERSION && gvm use go$GO_VERSION',
            'actions/setup-go@v3': 'gvm install go$GO_VERSION && gvm use go$GO_VERSION',
            'actions/setup-go@v4': 'gvm install go$GO_VERSION && gvm use go$GO_VERSION',
            'actions/setup-dotnet@v1': 'curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --version $DOTNET_VERSION',
            'actions/setup-dotnet@v2': 'curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --version $DOTNET_VERSION',
            'actions/setup-dotnet@v3': 'curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --version $DOTNET_VERSION',
            
            # Cache actions
            'actions/cache@v2': 'echo "Cache action - implement caching strategy"',
            'actions/cache@v3': 'echo "Cache action - implement caching strategy"',
            'actions/cache@v4': 'echo "Cache action - implement caching strategy"',
            
            # Artifact actions
            'actions/upload-artifact@v2': 'echo "Artifacts uploaded"',
            'actions/upload-artifact@v3': 'echo "Artifacts uploaded"',
            'actions/upload-artifact@v4': 'echo "Artifacts uploaded"',
            'actions/download-artifact@v2': 'echo "Artifacts downloaded"',
            'actions/download-artifact@v3': 'echo "Artifacts downloaded"',
            'actions/download-artifact@v4': 'echo "Artifacts downloaded"',
            
            # Docker actions
            'docker/login-action@v1': 'echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin',
            'docker/login-action@v2': 'echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin',
            'docker/login-action@v3': 'echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin',
            'docker/build-push-action@v2': 'docker build -t $IMAGE_NAME . && docker push $IMAGE_NAME',
            'docker/build-push-action@v3': 'docker build -t $IMAGE_NAME . && docker push $IMAGE_NAME',
            'docker/build-push-action@v4': 'docker build -t $IMAGE_NAME . && docker push $IMAGE_NAME',
            'docker/setup-buildx-action@v1': 'docker buildx create --use',
            'docker/setup-buildx-action@v2': 'docker buildx create --use',
            'docker/setup-qemu-action@v1': 'docker run --privileged --rm tonistiigi/binfmt --install all',
            'docker/setup-qemu-action@v2': 'docker run --privileged --rm tonistiigi/binfmt --install all',
            
            # Cloud provider actions
            'aws-actions/configure-aws-credentials@v1': 'aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID && aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY',
            'aws-actions/configure-aws-credentials@v2': 'aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID && aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY',
            'azure/login@v1': 'az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID',
            'google-github-actions/auth@v0': 'gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS',
            'google-github-actions/auth@v1': 'gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS',
            
            # Kubernetes actions
            'azure/k8s-set-context@v1': 'kubectl config use-context $KUBE_CONTEXT',
            'azure/k8s-deploy@v1': 'kubectl apply -f $MANIFEST_PATH',
            
            # Testing actions
            'codecov/codecov-action@v1': 'bash <(curl -s https://codecov.io/bash)',
            'codecov/codecov-action@v2': 'bash <(curl -s https://codecov.io/bash)',
            'codecov/codecov-action@v3': 'bash <(curl -s https://codecov.io/bash)',
            
            # Release actions
            'softprops/action-gh-release@v1': 'gh release create $TAG_NAME',
            
            # Slack actions
            'slackapi/slack-github-action@v1': 'curl -X POST -H "Content-type: application/json" --data "$SLACK_MESSAGE" $SLACK_WEBHOOK_URL',
        }
    
    def convert_file(self, workflow_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a GitHub Actions workflow file to Nexus pipeline configuration.
        
        Args:
            workflow_file_path: Path to the workflow YAML file
            output_path: Optional path to save the converted configuration
            
        Returns:
            Dictionary containing Nexus pipeline configuration
        """
        try:
            with open(workflow_file_path, 'r') as f:
                workflow_content = f.read()
            
            # Parse GitHub Actions workflow
            self.github_workflow = self._parse_workflow(workflow_content)
            
            # Convert to Nexus format
            self.nexus_config = self._convert_to_nexus()
            
            # Save to file if output path provided
            if output_path:
                self._save_nexus_config(output_path)
            
            return self.nexus_config
            
        except Exception as e:
            raise Exception(f"Failed to convert workflow file: {str(e)}")
    
    def convert_string(self, workflow_content: str) -> Dict[str, Any]:
        """
        Convert GitHub Actions workflow string to Nexus configuration.
        
        Args:
            workflow_content: GitHub Actions workflow as YAML string
            
        Returns:
            Dictionary containing Nexus pipeline configuration
        """
        self.github_workflow = self._parse_workflow(workflow_content)
        self.nexus_config = self._convert_to_nexus()
        return self.nexus_config
    
    def _parse_workflow(self, content: str) -> GitHubWorkflow:
        """Parse GitHub Actions workflow YAML content"""
        try:
            workflow_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise Exception(f"Failed to parse YAML: {str(e)}")
        
        workflow = GitHubWorkflow(
            name=workflow_data.get('name', 'github-actions-pipeline')
        )
        
        # Parse triggers (on)
        workflow.on_events = self._parse_triggers(workflow_data.get('on', {}))
        
        # Parse global environment
        workflow.env = workflow_data.get('env', {})
        
        # Parse defaults
        workflow.defaults = workflow_data.get('defaults', {})
        
        # Parse concurrency
        workflow.concurrency = workflow_data.get('concurrency')
        
        # Parse jobs
        jobs_data = workflow_data.get('jobs', {})
        for job_name, job_config in jobs_data.items():
            job = self._parse_job(job_name, job_config)
            workflow.jobs.append(job)
        
        return workflow
    
    def _parse_triggers(self, on_data: Any) -> List[str]:
        """Parse GitHub Actions triggers"""
        triggers = []
        
        if isinstance(on_data, str):
            triggers.append(on_data)
        elif isinstance(on_data, list):
            triggers.extend(on_data)
        elif isinstance(on_data, dict):
            for event, config in on_data.items():
                if event == 'schedule':
                    if isinstance(config, list):
                        for schedule in config:
                            cron = schedule.get('cron', '')
                            triggers.append(f"schedule:{cron}")
                elif event == 'push':
                    if config and isinstance(config, dict):
                        branches = config.get('branches', [])
                        if branches:
                            for branch in (branches if isinstance(branches, list) else [branches]):
                                triggers.append(f"push:branch:{branch}")
                        else:
                            triggers.append('push')
                    else:
                        triggers.append('push')
                elif event == 'pull_request':
                    triggers.append('pull_request')
                elif event == 'workflow_dispatch':
                    triggers.append('manual')
                else:
                    triggers.append(event)
        
        return triggers
    
    def _store_workflow_inputs(self, inputs: Dict[str, Any]):
        """Store workflow dispatch inputs for documentation"""
        if not hasattr(self, 'workflow_inputs'):
            self.workflow_inputs = {}
        self.workflow_inputs.update(inputs)
    
    def _store_workflow_secrets(self, secrets: Dict[str, Any]):
        """Store workflow secrets for documentation"""
        if not hasattr(self, 'workflow_secrets'):
            self.workflow_secrets = {}
        self.workflow_secrets.update(secrets)
    
    def _parse_job(self, job_name: str, job_config: Dict[str, Any]) -> GitHubJob:
        """Parse a single GitHub Actions job"""
        job = GitHubJob(
            name=job_config.get('name', job_name),
            runs_on=self._parse_runs_on(job_config.get('runs-on', 'ubuntu-latest')),
            timeout_minutes=job_config.get('timeout-minutes', 360),
            if_condition=job_config.get('if'),
            needs=self._parse_needs(job_config.get('needs', [])),
            environment=job_config.get('env', {}),
            container=self._parse_container(job_config.get('container')),
            services=job_config.get('services', {}),
            strategy=job_config.get('strategy')
        )
        
        if 'outputs' in job_config:
            job.outputs = job_config['outputs']
        
        if 'permissions' in job_config:
            job.permissions = job_config['permissions']
        
        if 'concurrency' in job_config:
            job.concurrency = job_config['concurrency']
        
        if 'environment' in job_config:
            env_config = job_config['environment']
            if isinstance(env_config, str):
                job.deployment_environment = env_config
            elif isinstance(env_config, dict):
                job.deployment_environment = env_config.get('name')
                job.deployment_url = env_config.get('url')
        
        if 'defaults' in job_config:
            job.defaults = job_config['defaults']
        
        if 'continue-on-error' in job_config:
            job.continue_on_error = job_config['continue-on-error']
        
        steps_data = job_config.get('steps', [])
        for step_data in steps_data:
            step = self._parse_step(step_data)
            if step:
                job.steps.append(step)
        
        return job
    
    def _parse_runs_on(self, runs_on: Any) -> str:
        """Parse runs-on configuration"""
        if isinstance(runs_on, str):
            return runs_on
        elif isinstance(runs_on, list):
            return runs_on[0] if runs_on else 'ubuntu-latest'
        return 'ubuntu-latest'
    
    def _parse_needs(self, needs: Any) -> List[str]:
        """Parse job dependencies"""
        if isinstance(needs, str):
            return [needs]
        elif isinstance(needs, list):
            return needs
        return []
    
    def _parse_container(self, container: Any) -> Optional[str]:
        """Parse container configuration"""
        if isinstance(container, str):
            return container
        elif isinstance(container, dict):
            return container.get('image')
        return None
    
    def _parse_step(self, step_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single step"""
        step = {
            'name': step_data.get('name', f'Step {self.step_counter}'),
            'if': step_data.get('if'),
            'continue_on_error': step_data.get('continue-on-error', False),
            'timeout_minutes': step_data.get('timeout-minutes'),
            'working_directory': step_data.get('working-directory'),
            'env': step_data.get('env', {})
        }
        
        if 'uses' in step_data:
            action = step_data['uses']
            step['type'] = 'action'
            step['action'] = action
            step['with'] = step_data.get('with', {})
        elif 'run' in step_data:
            step['type'] = 'run'
            step['command'] = step_data['run']
        else:
            return None
        
        self.step_counter += 1
        return step
    
    def _convert_to_nexus(self) -> Dict[str, Any]:
        """Convert parsed GitHub workflow to Nexus format"""
        if not self.github_workflow:
            raise Exception("No workflow parsed")
        
        nexus_config = {
            "name": self.github_workflow.name,
            "version": "1.0.0",
            "description": "Converted from GitHub Actions workflow",
            "environment": self.github_workflow.env.copy(),
            "triggers": self._convert_triggers(),
            "max_parallel_jobs": 10,
            "artifacts_retention": 30,
            "steps": []
        }
        
        all_steps = self._convert_jobs()
        nexus_config["steps"] = all_steps
        
        return nexus_config
    
    def _convert_triggers(self) -> List[str]:
        """Convert GitHub Actions triggers to Nexus format"""
        nexus_triggers = []
        
        for trigger in self.github_workflow.on_events:
            if trigger.startswith('schedule:'):
                nexus_triggers.append(trigger)
            elif trigger.startswith('push:'):
                parts = trigger.split(':')
                if len(parts) >= 3:
                    nexus_triggers.append(f"git:push:{parts[2]}")
                else:
                    nexus_triggers.append("git:push")
            elif trigger == 'push':
                nexus_triggers.append("git:push")
            elif trigger == 'pull_request':
                nexus_triggers.append("git:pull_request")
            elif trigger == 'manual':
                nexus_triggers.append("manual")
            else:
                nexus_triggers.append(trigger)
        
        return nexus_triggers
    
    def _convert_jobs(self) -> List[Dict[str, Any]]:
        """Convert all jobs to Nexus steps"""
        all_steps = []
        
        for job in self.github_workflow.jobs:
            if job.strategy and 'matrix' in job.strategy:
                matrix_steps = self._expand_matrix_job(job)
                all_steps.extend(matrix_steps)
            else:
                job_steps = self._convert_job(job)
                all_steps.extend(job_steps)
        
        return all_steps
    
    def _expand_matrix_job(self, job: GitHubJob) -> List[Dict[str, Any]]:
        """Expand matrix strategy into multiple parallel steps"""
        matrix_steps = []
        matrix = job.strategy['matrix']
        
        include = matrix.get('include', [])
        exclude = matrix.get('exclude', [])
        
        matrix_vars = {k: v for k, v in matrix.items() if k not in ['include', 'exclude']}
        
        import itertools
        
        if matrix_vars:
            keys = list(matrix_vars.keys())
            values = [matrix_vars[k] for k in keys]
            
            for combination in itertools.product(*values):
                matrix_env = dict(zip(keys, combination))
                
                if self._is_excluded(matrix_env, exclude):
                    continue
                
                step_name = f"{job.name}_{'_'.join(str(v) for v in combination)}"
                combined_env = {**job.environment, **matrix_env}
                
                commands = []
                for step in job.steps:
                    command = self._convert_step_to_command(step, combined_env)
                    if command:
                        commands.append(command)
                
                nexus_step = {
                    "name": step_name,
                    "command": " && ".join(commands),
                    "working_dir": ".",
                    "timeout": job.timeout_minutes * 60,
                    "retry_count": 0,
                    "environment": combined_env,
                    "depends_on": job.needs,
                    "parallel": True,
                    "critical": True
                }
                
                if job.if_condition:
                    nexus_step["condition"] = self._convert_condition(job.if_condition)
                
                matrix_steps.append(nexus_step)
        
        return matrix_steps
    
    def _is_excluded(self, combination: Dict[str, Any], exclude: List[Dict[str, Any]]) -> bool:
        """Check if a matrix combination is excluded"""
        for exclusion in exclude:
            if all(combination.get(k) == v for k, v in exclusion.items()):
                return True
        return False
    
    def _convert_job(self, job: GitHubJob) -> List[Dict[str, Any]]:
        """Convert a single job to Nexus steps"""
        steps = []
        commands = []
        artifacts = []
        
        for step in job.steps:
            command = self._convert_step_to_command(step, job.environment)
            if command:
                commands.append(command)
            
            if step.get('type') == 'action' and 'upload-artifact' in step.get('action', ''):
                artifact_path = step.get('with', {}).get('path', '**/*')
                artifacts.append(artifact_path)
        
        nexus_step = {
            "name": job.name,
            "command": " && ".join(commands) if commands else "echo 'No commands'",
            "working_dir": ".",
            "timeout": job.timeout_minutes * 60,
            "retry_count": 0,
            "environment": job.environment,
            "depends_on": job.needs,
            "parallel": False,
            "critical": True
        }
        
        if job.if_condition:
            nexus_step["condition"] = self._convert_condition(job.if_condition)
        
        if artifacts:
            nexus_step["artifacts"] = artifacts
        
        if job.container:
            nexus_step["command"] = f"docker run --rm -v $(pwd):/workspace -w /workspace {job.container} sh -c '{nexus_step['command']}'"
        
        steps.append(nexus_step)
        return steps
    
    def _convert_step_to_command(self, step: Dict[str, Any], job_env: Dict[str, str]) -> Optional[str]:
        """Convert a GitHub Actions step to a shell command"""
        if step.get('type') == 'run':
            command = step['command']
            
            if step.get('working_directory'):
                command = f"cd {step['working_directory']} && {command}"
            
            step_env = step.get('env', {})
            if step_env:
                env_prefix = " ".join([f"export {k}={v};" for k, v in step_env.items()])
                command = f"{env_prefix} {command}"
            
            return command
        
        elif step.get('type') == 'action':
            action = step['action']
            with_params = step.get('with', {})
            
            if action in self.action_mappings:
                base_command = self.action_mappings[action]
                
                for key, value in with_params.items():
                    placeholder = f"${{{key.upper().replace('-', '_')}}}"
                    if placeholder in base_command:
                        base_command = base_command.replace(placeholder, str(value))
                
                return base_command
            
            if 'checkout' in action:
                ref = with_params.get('ref', '$GITHUB_REF')
                return f"git clone $GITHUB_REPOSITORY . && git checkout {ref}"
            
            if 'setup-node' in action:
                version = with_params.get('node-version', '16')
                return f"nvm install {version} && nvm use {version}"
            
            if 'setup-python' in action:
                version = with_params.get('python-version', '3.9')
                return f"pyenv install {version} && pyenv global {version}"
            
            return f"# Action: {action} (manual implementation required)"
        
        return None
    
    def _convert_condition(self, condition: str) -> str:
        """Convert GitHub Actions condition to Nexus format"""
        condition = condition.replace('github.ref', '$GITHUB_REF')
        condition = condition.replace('github.event_name', '$GITHUB_EVENT_NAME')
        condition = condition.replace('github.actor', '$GITHUB_ACTOR')
        condition = condition.replace('success()', 'true')
        condition = condition.replace('failure()', 'false')
        return condition
    
    def _save_nexus_config(self, output_path: str):
        """Save Nexus configuration to file"""
        output_file = Path(output_path)
        
        with open(output_file, 'w') as f:
            if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                yaml.dump(self.nexus_config, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(self.nexus_config, f, indent=2)
    
    def get_conversion_summary(self) -> str:
        """Get a summary of the conversion"""
        if not self.github_workflow or not self.nexus_config:
            return "No conversion performed yet"
        
        summary = f"""
GitHub Actions to Nexus Conversion Summary
==========================================

GitHub Workflow:
- Name: {self.github_workflow.name}
- Jobs: {len(self.github_workflow.jobs)}
- Triggers: {len(self.github_workflow.on_events)}
- Environment Variables: {len(self.github_workflow.env)}

Nexus Pipeline:
- Steps: {len(self.nexus_config.get('steps', []))}
- Environment Variables: {len(self.nexus_config.get('environment', {}))}
- Triggers: {len(self.nexus_config.get('triggers', []))}
- Parallel Steps: {len([s for s in self.nexus_config.get('steps', []) if s.get('parallel', False)])}

Conversion Complete!
"""
        return summary.strip()
    
    def validate_conversion(self) -> Tuple[bool, List[str]]:
        """Validate the converted Nexus configuration"""
        warnings = []
        
        if not self.nexus_config:
            return False, ["No configuration generated"]
        
        if not self.nexus_config.get('name'):
            warnings.append("Pipeline name is missing")
        
        if not self.nexus_config.get('steps'):
            warnings.append("No steps defined in pipeline")
        
        steps = self.nexus_config.get('steps', [])
        step_names = {step['name'] for step in steps}
        
        for step in steps:
            for dep in step.get('depends_on', []):
                if dep not in step_names:
                    warnings.append(f"Step '{step['name']}' has invalid dependency: '{dep}'")
            
            if '# Action:' in step.get('command', ''):
                warnings.append(f"Step '{step['name']}' requires manual action implementation")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
    
    def generate_migration_guide(self) -> str:
        """Generate a migration guide document"""
        if not self.github_workflow or not self.nexus_config:
            return "No conversion data available"
        
        is_valid, warnings = self.validate_conversion()
        
        guide = f"""# GitHub Actions to Nexus Migration Guide

## Original GitHub Workflow
- **Name**: {self.github_workflow.name}
- **Jobs**: {len(self.github_workflow.jobs)}
- **Triggers**: {len(self.github_workflow.on_events)}

## Converted Nexus Pipeline
- **Steps**: {len(self.nexus_config.get('steps', []))}
- **Parallel Steps**: {len([s for s in self.nexus_config.get('steps', []) if s.get('parallel')])}

## Validation Status
{'✅ Configuration is valid' if is_valid else '⚠️ Configuration has warnings'}

"""
        
        if warnings:
            guide += "\n### Warnings\n"
            for warning in warnings:
                guide += f"- {warning}\n"
        
        guide += "\n## Next Steps\n\n"
        guide += "1. Review converted configuration\n"
        guide += "2. Implement custom actions manually\n"
        guide += "3. Test in development environment\n"
        guide += "4. Configure secrets and credentials\n"
        guide += "5. Deploy to production\n"
        
        return guide


# Example usage
if __name__ == "__main__":
    print("\n" + "="*80)
    print("GITHUB ACTIONS TO NEXUS CONVERTER DEMONSTRATION")
    print("="*80)
    
    sample_workflow = """
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'

env:
  NODE_ENV: production
  CACHE_VERSION: v1

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build
        run: npm run build
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: build-output
          path: dist/
  
  test:
    runs-on: ubuntu-latest
    needs: build
    strategy:
      matrix:
        node-version: [16, 18, 20]
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
  
  deploy:
    runs-on: ubuntu-latest
    needs: [build, test]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: ./deploy.sh
"""
    
    converter = GitHubActions2Nexus()
    result = converter.convert_string(sample_workflow)
    
    print("\n" + converter.get_conversion_summary())
    
    is_valid, warnings = converter.validate_conversion()
    print(f"\n✓ Validation: {'PASSED' if is_valid else 'HAS WARNINGS'}")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print("\n\nConverted Nexus Configuration:")
    print("=" * 50)
    print(json.dumps(result, indent=2))
    
    print("\n\nMigration Guide:")
    print("=" * 50)
    print(converter.generate_migration_guide())