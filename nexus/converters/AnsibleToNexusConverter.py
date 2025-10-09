#!/usr/bin/env python3
"""
Ansible to Nexus Pipeline Converter
===================================
Converts Ansible playbooks to Nexus Pipeline format.

This converter maps:
- Ansible plays -> Pipeline steps
- Ansible tasks -> Pipeline commands
- Ansible variables -> Pipeline environment variables
- Ansible handlers -> Pipeline post-step hooks
- Ansible roles -> Pipeline step dependencies
"""

import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class ConversionOptions:
    """Options for controlling the conversion process"""
    include_comments: bool = True
    convert_handlers: bool = True
    convert_variables: bool = True
    parallel_tasks: bool = False
    default_timeout: int = 300
    default_retry_count: int = 0
    preserve_ansible_structure: bool = True


class AnsibleToNexusConverter:
    """
    Converts Ansible playbooks to Nexus Pipeline configuration
    """
    
    def __init__(self, options: Optional[ConversionOptions] = None):
        self.options = options or ConversionOptions()
        self.conversion_log = []
        
        # Mapping of Ansible modules to shell commands
        self.module_mappings = {
            'shell': lambda args: args.get('_raw_params', args.get('cmd', '')),
            'command': lambda args: args.get('_raw_params', args.get('cmd', '')),
            'script': lambda args: f"bash {args.get('_raw_params', '')}",
            'copy': lambda args: f"cp {args.get('src', '')} {args.get('dest', '')}",
            'file': lambda args: self._convert_file_module(args),
            'template': lambda args: f"envsubst < {args.get('src', '')} > {args.get('dest', '')}",
            'git': lambda args: f"git clone {args.get('repo', '')} {args.get('dest', '.')}",
            'yum': lambda args: f"yum install -y {args.get('name', '')}",
            'apt': lambda args: f"apt-get install -y {args.get('name', '')}",
            'pip': lambda args: f"pip install {args.get('name', '')}",
            'service': lambda args: f"systemctl {args.get('state', 'started')} {args.get('name', '')}",
            'systemd': lambda args: f"systemctl {args.get('state', 'started')} {args.get('name', '')}",
            'docker_container': lambda args: self._convert_docker_container(args),
            'docker_image': lambda args: f"docker build -t {args.get('name', '')} {args.get('path', '.')}",
            'uri': lambda args: f"curl -X {args.get('method', 'GET')} {args.get('url', '')}",
            'get_url': lambda args: f"wget -O {args.get('dest', '')} {args.get('url', '')}",
            'unarchive': lambda args: f"tar -xf {args.get('src', '')} -C {args.get('dest', '')}",
            'lineinfile': lambda args: f"sed -i 's/{args.get('regexp', '')}/{args.get('line', '')}/g' {args.get('path', '')}",
            'replace': lambda args: f"sed -i 's/{args.get('regexp', '')}/{args.get('replace', '')}/g' {args.get('path', '')}",
            'wait_for': lambda args: f"sleep {args.get('timeout', 30)}",
            'debug': lambda args: f"echo '{args.get('msg', args.get('var', ''))}'",
            'fail': lambda args: f"echo '{args.get('msg', 'Task failed')}' && exit 1",
            'pause': lambda args: f"sleep {args.get('seconds', 10)}",
            'set_fact': lambda args: f"export {list(args.keys())[0] if args else ''}={list(args.values())[0] if args else ''}",
            'include_tasks': lambda args: f"# Include tasks from {args.get('file', '')}",
            'include_vars': lambda args: f"# Include variables from {args.get('file', '')}",
            'block': lambda args: "# Block start",
        }

    def convert_playbook_file(self, playbook_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Convert an Ansible playbook file to Nexus Pipeline configuration
        
        Args:
            playbook_path: Path to the Ansible playbook YAML file
            
        Returns:
            Nexus Pipeline configuration dictionary
        """
        playbook_path = Path(playbook_path)
        
        if not playbook_path.exists():
            raise FileNotFoundError(f"Playbook file not found: {playbook_path}")
        
        try:
            with open(playbook_path, 'r', encoding='utf-8') as f:
                playbook_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in playbook: {e}")
        
        return self.convert_playbook(playbook_data, playbook_path.stem)

    def convert_playbook(self, playbook_data: List[Dict[str, Any]], name: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert Ansible playbook data to Nexus Pipeline configuration
        
        Args:
            playbook_data: Parsed Ansible playbook data
            name: Optional name for the pipeline
            
        Returns:
            Nexus Pipeline configuration dictionary
        """
        if not isinstance(playbook_data, list):
            playbook_data = [playbook_data]
        
        pipeline_config = {
            "name": name or "converted-ansible-playbook",
            "version": "1.0.0",
            "description": "Converted from Ansible playbook",
            "steps": [],
            "environment": {},
            "triggers": [],
            "notifications": {},
            "artifacts_retention": 30,
            "max_parallel_jobs": 5
        }
        
        global_vars = {}
        step_counter = 1
        
        # Process each play in the playbook
        for play_index, play in enumerate(playbook_data):
            if not isinstance(play, dict):
                continue
                
            self._log(f"Processing play {play_index + 1}: {play.get('name', 'Unnamed play')}")
            
            # Extract play-level variables
            play_vars = {}
            if 'vars' in play:
                play_vars.update(play['vars'])
            if 'vars_files' in play:
                for vars_file in play['vars_files']:
                    self._log(f"Note: vars_file '{vars_file}' should be manually converted")
            
            # Process tasks
            tasks = play.get('tasks', [])
            if tasks:
                play_steps = self._convert_tasks(tasks, play_vars, f"play_{play_index + 1}")
                pipeline_config["steps"].extend(play_steps)
                step_counter += len(play_steps)
            
            # Process handlers if enabled
            if self.options.convert_handlers and 'handlers' in play:
                handler_steps = self._convert_handlers(play['handlers'], play_vars)
                pipeline_config["steps"].extend(handler_steps)
            
            # Merge environment variables
            global_vars.update(play_vars)
        
        # Set global environment
        if self.options.convert_variables:
            pipeline_config["environment"] = self._convert_variables(global_vars)
        
        # Add conversion metadata
        pipeline_config["metadata"] = {
            "converted_from": "ansible_playbook",
            "conversion_log": self.conversion_log,
            "conversion_options": self.options.__dict__
        }
        
        return pipeline_config

    def _convert_tasks(self, tasks: List[Dict[str, Any]], variables: Dict[str, Any], play_name: str) -> List[Dict[str, Any]]:
        """Convert Ansible tasks to pipeline steps"""
        steps = []
        dependencies = []
        
        for task_index, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue
            
            step_name = self._generate_step_name(task, task_index, play_name)
            
            # Handle special task structures
            if 'block' in task:
                # Handle block/rescue/always structure
                block_steps = self._convert_block_task(task, variables, step_name)
                steps.extend(block_steps)
                continue
            
            if 'include_tasks' in task or 'import_tasks' in task:
                # Handle task inclusion
                include_step = self._convert_include_task(task, variables, step_name)
                steps.append(include_step)
                continue
            
            # Convert regular task
            step = self._convert_single_task(task, variables, step_name)
            
            # Add dependencies (tasks run sequentially by default)
            if dependencies and not self.options.parallel_tasks:
                step["depends_on"] = [dependencies[-1]]
            
            steps.append(step)
            dependencies.append(step_name)
        
        return steps

    def _convert_single_task(self, task: Dict[str, Any], variables: Dict[str, Any], step_name: str) -> Dict[str, Any]:
        """Convert a single Ansible task to a pipeline step"""
        # Find the module being used
        module_name = None
        module_args = {}
        
        for key, value in task.items():
            if key not in ['name', 'when', 'tags', 'become', 'become_user', 'register', 'changed_when', 'failed_when', 'ignore_errors']:
                module_name = key
                module_args = value if isinstance(value, dict) else {'_raw_params': value}
                break
        
        if not module_name:
            self._log(f"Warning: Could not identify module in task: {task}")
            command = f"echo 'Unknown task: {task.get('name', 'Unnamed')}'"
        else:
            command = self._convert_module_to_command(module_name, module_args)
        
        # Build pipeline step
        step = {
            "name": step_name,
            "command": command,
            "working_dir": ".",
            "timeout": self.options.default_timeout,
            "retry_count": self.options.default_retry_count,
            "environment": {},
            "depends_on": [],
            "condition": None,
            "parallel": self.options.parallel_tasks,
            "critical": True,
            "artifacts": []
        }
        
        # Handle task conditions
        if 'when' in task:
            step["condition"] = self._convert_condition(task['when'])
        
        # Handle task environment
        if 'environment' in task:
            step["environment"] = self._convert_variables(task['environment'])
        
        # Handle error handling
        if task.get('ignore_errors', False):
            step["critical"] = False
        
        # Handle register (convert to artifact)
        if 'register' in task:
            step["artifacts"] = [f"{task['register']}.log"]
        
        # Add original task as comment if requested
        if self.options.include_comments:
            step["original_ansible_task"] = task
        
        return step

    def _convert_block_task(self, task: Dict[str, Any], variables: Dict[str, Any], base_name: str) -> List[Dict[str, Any]]:
        """Convert Ansible block/rescue/always structure"""
        steps = []
        
        # Convert block tasks
        if 'block' in task:
            block_steps = self._convert_tasks(task['block'], variables, f"{base_name}_block")
            steps.extend(block_steps)
        
        # Convert rescue tasks (error handling)
        if 'rescue' in task:
            rescue_steps = self._convert_tasks(task['rescue'], variables, f"{base_name}_rescue")
            for rescue_step in rescue_steps:
                rescue_step['critical'] = False  # Rescue steps shouldn't fail the pipeline
            steps.extend(rescue_steps)
        
        # Convert always tasks
        if 'always' in task:
            always_steps = self._convert_tasks(task['always'], variables, f"{base_name}_always")
            steps.extend(always_steps)
        
        return steps

    def _convert_include_task(self, task: Dict[str, Any], variables: Dict[str, Any], step_name: str) -> Dict[str, Any]:
        """Convert task inclusion to a pipeline step"""
        include_file = task.get('include_tasks') or task.get('import_tasks', '')
        
        return {
            "name": step_name,
            "command": f"# TODO: Include tasks from {include_file}",
            "working_dir": ".",
            "timeout": self.options.default_timeout,
            "retry_count": 0,
            "environment": {},
            "depends_on": [],
            "condition": None,
            "parallel": False,
            "critical": True,
            "artifacts": [],
            "note": f"Manual conversion required for included file: {include_file}"
        }

    def _convert_handlers(self, handlers: List[Dict[str, Any]], variables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Ansible handlers to pipeline steps"""
        handler_steps = []
        
        for handler_index, handler in enumerate(handlers):
            step_name = f"handler_{handler_index + 1}_{handler.get('name', 'unnamed').lower().replace(' ', '_')}"
            step = self._convert_single_task(handler, variables, step_name)
            step["parallel"] = False  # Handlers typically run sequentially
            handler_steps.append(step)
        
        return handler_steps

    def _convert_module_to_command(self, module_name: str, module_args: Dict[str, Any]) -> str:
        """Convert Ansible module call to shell command"""
        if module_name in self.module_mappings:
            try:
                command = self.module_mappings[module_name](module_args)
                self._log(f"Converted {module_name} module to: {command}")
                return command
            except Exception as e:
                self._log(f"Error converting {module_name} module: {e}")
        
        # Fallback for unknown modules
        self._log(f"Warning: Unknown module '{module_name}', creating placeholder command")
        args_str = ' '.join([f"--{k} {v}" for k, v in module_args.items() if k != '_raw_params'])
        return f"# TODO: Convert {module_name} module manually - Args: {args_str}"

    def _convert_file_module(self, args: Dict[str, Any]) -> str:
        """Convert Ansible file module to shell commands"""
        path = args.get('path', args.get('dest', ''))
        state = args.get('state', 'file')
        mode = args.get('mode', '')
        owner = args.get('owner', '')
        group = args.get('group', '')
        
        commands = []
        
        if state == 'directory':
            commands.append(f"mkdir -p {path}")
        elif state == 'absent':
            commands.append(f"rm -rf {path}")
        elif state == 'touch':
            commands.append(f"touch {path}")
        
        if mode:
            commands.append(f"chmod {mode} {path}")
        if owner:
            commands.append(f"chown {owner} {path}")
        if group:
            commands.append(f"chgrp {group} {path}")
        
        return ' && '.join(commands) if commands else f"# File operation on {path}"

    def _convert_docker_container(self, args: Dict[str, Any]) -> str:
        """Convert Ansible docker_container module to docker command"""
        name = args.get('name', '')
        image = args.get('image', '')
        state = args.get('state', 'started')
        ports = args.get('ports', [])
        volumes = args.get('volumes', [])
        environment = args.get('env', {})
        
        if state == 'absent':
            return f"docker rm -f {name}"
        
        cmd_parts = ['docker run -d']
        
        if name:
            cmd_parts.append(f"--name {name}")
        
        for port in ports:
            if isinstance(port, str) and ':' in port:
                cmd_parts.append(f"-p {port}")
        
        for volume in volumes:
            if isinstance(volume, str) and ':' in volume:
                cmd_parts.append(f"-v {volume}")
        
        for key, value in environment.items():
            cmd_parts.append(f"-e {key}={value}")
        
        cmd_parts.append(image)
        
        return ' '.join(cmd_parts)

    def _convert_condition(self, condition: Union[str, List[str]]) -> str:
        """Convert Ansible when condition to pipeline condition"""
        if isinstance(condition, list):
            condition = ' and '.join(condition)
        
        # Simple condition conversion (more complex logic may be needed)
        condition = condition.replace(' is defined', ' != ""')
        condition = condition.replace(' is not defined', ' == ""')
        condition = condition.replace(' == true', ' == "true"')
        condition = condition.replace(' == false', ' == "false"')
        
        # Convert Ansible variable syntax to shell variable syntax
        condition = re.sub(r'\b(\w+)\b(?!\s*[=!<>])', r'${\1}', condition)
        
        return condition

    def _convert_variables(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Convert Ansible variables to environment variables"""
        env_vars = {}
        
        for key, value in variables.items():
            if isinstance(value, (str, int, float, bool)):
                env_vars[key.upper()] = str(value)
            elif isinstance(value, dict):
                # Flatten nested dictionaries
                for subkey, subvalue in value.items():
                    env_vars[f"{key.upper()}_{subkey.upper()}"] = str(subvalue)
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                env_vars[key.upper()] = ','.join(str(item) for item in value)
            else:
                env_vars[key.upper()] = str(value)
        
        return env_vars

    def _generate_step_name(self, task: Dict[str, Any], index: int, play_name: str) -> str:
        """Generate a unique step name from task"""
        if 'name' in task and task['name']:
            # Clean up the task name
            name = re.sub(r'[^a-zA-Z0-9_-]', '_', task['name'].lower())
            name = re.sub(r'_{2,}', '_', name).strip('_')
            return f"{play_name}_{name}"
        else:
            return f"{play_name}_task_{index + 1}"

    def _log(self, message: str):
        """Log conversion messages"""
        self.conversion_log.append(message)
        print(f"[CONVERTER] {message}")

    def save_pipeline_config(self, config: Dict[str, Any], output_path: Union[str, Path], format: str = "yaml"):
        """Save the converted pipeline configuration to file"""
        output_path = Path(output_path)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            self._log(f"Pipeline configuration saved to: {output_path}")
        except Exception as e:
            self._log(f"Error saving configuration: {e}")
            raise

    def generate_conversion_report(self) -> str:
        """Generate a report of the conversion process"""
        report = []
        report.append("ANSIBLE TO NEXUS PIPELINE CONVERSION REPORT")
        report.append("=" * 50)
        report.append("")
        
        report.append("Conversion Log:")
        for message in self.conversion_log:
            report.append(f"  - {message}")
        
        report.append("")
        report.append("Manual Steps Required:")
        report.append("  - Review all TODO comments in the generated configuration")
        report.append("  - Convert included task files manually")
        report.append("  - Review variable substitutions")
        report.append("  - Test all converted commands")
        report.append("  - Adjust timeouts and retry counts as needed")
        
        return "\n".join(report)


def convert_ansible_playbook(playbook_path: str, 
                           output_path: str = None, 
                           options: ConversionOptions = None) -> Dict[str, Any]:
    """
    Convenience function to convert an Ansible playbook to Nexus Pipeline format
    
    Args:
        playbook_path: Path to the Ansible playbook YAML file
        output_path: Optional path to save the converted configuration
        options: Conversion options
        
    Returns:
        Converted pipeline configuration
    """
    converter = AnsibleToNexusConverter(options)
    
    try:
        # Convert the playbook
        config = converter.convert_playbook_file(playbook_path)
        
        # Save to file if output path provided
        if output_path:
            converter.save_pipeline_config(config, output_path)
        
        # Print conversion report
        print("\n" + converter.generate_conversion_report())
        
        return config
        
    except Exception as e:
        print(f"Conversion failed: {e}")
        raise


# Example usage and testing
if __name__ == "__main__":
    # Example Ansible playbook data for testing
    example_playbook = [
        {
            "name": "Deploy Web Application",
            "hosts": "webservers",
            "vars": {
                "app_name": "myapp",
                "app_version": "1.0.0",
                "deploy_dir": "/opt/myapp"
            },
            "tasks": [
                {
                    "name": "Install required packages",
                    "apt": {
                        "name": ["nginx", "nodejs", "npm"],
                        "state": "present"
                    }
                },
                {
                    "name": "Create application directory",
                    "file": {
                        "path": "{{ deploy_dir }}",
                        "state": "directory",
                        "mode": "0755"
                    }
                },
                {
                    "name": "Clone application repository",
                    "git": {
                        "repo": "https://github.com/example/myapp.git",
                        "dest": "{{ deploy_dir }}",
                        "version": "{{ app_version }}"
                    }
                },
                {
                    "name": "Install Node.js dependencies",
                    "shell": "npm install",
                    "args": {
                        "chdir": "{{ deploy_dir }}"
                    }
                },
                {
                    "name": "Build application",
                    "shell": "npm run build",
                    "args": {
                        "chdir": "{{ deploy_dir }}"
                    }
                },
                {
                    "name": "Start nginx service",
                    "service": {
                        "name": "nginx",
                        "state": "started",
                        "enabled": True
                    }
                }
            ],
            "handlers": [
                {
                    "name": "restart nginx",
                    "service": {
                        "name": "nginx",
                        "state": "restarted"
                    }
                }
            ]
        }
    ]
    
    # Test the converter
    print("Testing Ansible to Nexus Pipeline Converter...")
    
    converter = AnsibleToNexusConverter(ConversionOptions(
        include_comments=True,
        convert_handlers=True,
        convert_variables=True,
        parallel_tasks=False
    ))
    
    converted_config = converter.convert_playbook(example_playbook, "web-app-deployment")
    
    # Save the converted configuration
    converter.save_pipeline_config(converted_config, "converted_pipeline.yaml")
    
    # Print the configuration
    print("\nConverted Pipeline Configuration:")
    print(yaml.dump(converted_config, default_flow_style=False))
    
    print(converter.generate_conversion_report())