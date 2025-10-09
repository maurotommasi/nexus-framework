#!/usr/bin/env python3
"""
Jenkins2Nexus Converter
======================
Converts Jenkins pipeline files to Nexus Enterprise Pipeline format.

Author: Conversion Tool
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
class JenkinsStage:
    """Represents a Jenkins stage"""
    name: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    when_condition: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    parallel: bool = False


@dataclass
class JenkinsAgent:
    """Represents Jenkins agent configuration"""
    type: str = "any"
    label: Optional[str] = None
    docker_image: Optional[str] = None


@dataclass
class JenkinsPipeline:
    """Represents parsed Jenkins pipeline"""
    agent: JenkinsAgent = field(default_factory=JenkinsAgent)
    environment: Dict[str, str] = field(default_factory=dict)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    stages: List[JenkinsStage] = field(default_factory=list)
    post_actions: Dict[str, List[str]] = field(default_factory=dict)
    tools: Dict[str, str] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)


class Jenkins2Nexus:
    """
    Converter class to transform Jenkins pipeline definitions into Nexus pipeline format.
    
    Supports:
    - Declarative and Scripted pipeline syntax
    - Stages and parallel stages
    - Environment variables
    - Conditional execution (when blocks)
    - Post actions (success, failure, always)
    - Agent configurations
    - Parameters
    - Triggers
    - Docker agents
    - Parallel execution
    - Timeouts and retries
    """
    
    def __init__(self):
        """Initialize the converter"""
        self.jenkins_pipeline: Optional[JenkinsPipeline] = None
        self.nexus_config: Dict[str, Any] = {}
        self.step_counter = 0
        
    def convert_file(self, jenkins_file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a Jenkinsfile to Nexus pipeline configuration.
        
        Args:
            jenkins_file_path: Path to the Jenkinsfile
            output_path: Optional path to save the converted configuration
            
        Returns:
            Dictionary containing Nexus pipeline configuration
        """
        try:
            with open(jenkins_file_path, 'r') as f:
                jenkins_content = f.read()
            
            # Parse Jenkins pipeline
            self.jenkins_pipeline = self._parse_jenkinsfile(jenkins_content)
            
            # Convert to Nexus format
            self.nexus_config = self._convert_to_nexus()
            
            # Save to file if output path provided
            if output_path:
                self._save_nexus_config(output_path)
            
            return self.nexus_config
            
        except Exception as e:
            raise Exception(f"Failed to convert Jenkinsfile: {str(e)}")
    
    def convert_string(self, jenkins_content: str) -> Dict[str, Any]:
        """
        Convert Jenkins pipeline string to Nexus configuration.
        
        Args:
            jenkins_content: Jenkins pipeline definition as string
            
        Returns:
            Dictionary containing Nexus pipeline configuration
        """
        self.jenkins_pipeline = self._parse_jenkinsfile(jenkins_content)
        self.nexus_config = self._convert_to_nexus()
        return self.nexus_config
    
    def _parse_jenkinsfile(self, content: str) -> JenkinsPipeline:
        """Parse Jenkinsfile content into structured format"""
        pipeline = JenkinsPipeline()
        
        # Detect pipeline type
        is_declarative = 'pipeline {' in content
        
        if is_declarative:
            pipeline = self._parse_declarative_pipeline(content)
        else:
            pipeline = self._parse_scripted_pipeline(content)
        
        return pipeline
    
    def _parse_declarative_pipeline(self, content: str) -> JenkinsPipeline:
        """Parse declarative pipeline syntax"""
        pipeline = JenkinsPipeline()
        
        # Parse agent
        pipeline.agent = self._parse_agent(content)
        
        # Parse environment
        pipeline.environment = self._parse_environment(content)
        
        # Parse parameters
        pipeline.parameters = self._parse_parameters(content)
        
        # Parse triggers
        pipeline.triggers = self._parse_triggers(content)
        
        # Parse options
        pipeline.options = self._parse_options(content)
        
        # Parse tools
        pipeline.tools = self._parse_tools(content)
        
        # Parse stages
        pipeline.stages = self._parse_stages(content)
        
        # Parse post actions
        pipeline.post_actions = self._parse_post_actions(content)
        
        return pipeline
    
    def _parse_scripted_pipeline(self, content: str) -> JenkinsPipeline:
        """Parse scripted pipeline syntax"""
        pipeline = JenkinsPipeline()
        
        # Extract node block
        node_match = re.search(r'node\s*\(([^)]*)\)\s*{', content)
        if node_match:
            node_label = node_match.group(1).strip().strip("'\"")
            pipeline.agent = JenkinsAgent(type="node", label=node_label if node_label else "any")
        
        # Parse stages from scripted syntax
        stage_pattern = r'stage\s*\([\'"]([^\'"]+)[\'"]\)\s*{([^}]+(?:{[^}]*}[^}]*)*?)}'
        stages = re.finditer(stage_pattern, content, re.DOTALL)
        
        for stage_match in stages:
            stage_name = stage_match.group(1)
            stage_body = stage_match.group(2)
            
            stage = JenkinsStage(name=stage_name)
            stage.steps = self._parse_steps(stage_body)
            
            pipeline.stages.append(stage)
        
        return pipeline
    
    def _parse_agent(self, content: str) -> JenkinsAgent:
        """Parse agent configuration"""
        agent = JenkinsAgent()
        
        # Parse agent block
        agent_match = re.search(r'agent\s*{([^}]+)}', content)
        if agent_match:
            agent_block = agent_match.group(1)
            
            # Check for 'any'
            if 'any' in agent_block:
                agent.type = "any"
            
            # Check for label
            label_match = re.search(r'label\s+[\'"]([^\'"]+)[\'"]', agent_block)
            if label_match:
                agent.type = "label"
                agent.label = label_match.group(1)
            
            # Check for docker
            docker_match = re.search(r'docker\s+[\'"]([^\'"]+)[\'"]', agent_block)
            if docker_match:
                agent.type = "docker"
                agent.docker_image = docker_match.group(1)
        
        # Parse simple agent syntax
        simple_match = re.search(r'agent\s+any', content)
        if simple_match:
            agent.type = "any"
        
        return agent
    
    def _parse_environment(self, content: str) -> Dict[str, str]:
        """Parse environment variables"""
        env_vars = {}
        
        env_match = re.search(r'environment\s*{([^}]+)}', content)
        if env_match:
            env_block = env_match.group(1)
            
            # Parse each environment variable
            var_pattern = r'(\w+)\s*=\s*[\'"]?([^\'"}\n]+)[\'"]?'
            for match in re.finditer(var_pattern, env_block):
                key = match.group(1).strip()
                value = match.group(2).strip()
                env_vars[key] = value
        
        return env_vars
    
    def _parse_parameters(self, content: str) -> List[Dict[str, Any]]:
        """Parse pipeline parameters"""
        parameters = []
        
        params_match = re.search(r'parameters\s*{([^}]+)}', content, re.DOTALL)
        if params_match:
            params_block = params_match.group(1)
            
            # Parse string parameters
            string_pattern = r'string\s*\(\s*name:\s*[\'"](\w+)[\'"](?:,\s*defaultValue:\s*[\'"]([^\'"]*)[\'"])?(?:,\s*description:\s*[\'"]([^\'"]*)[\'"])?\s*\)'
            for match in re.finditer(string_pattern, params_block):
                parameters.append({
                    "type": "string",
                    "name": match.group(1),
                    "default": match.group(2) or "",
                    "description": match.group(3) or ""
                })
            
            # Parse boolean parameters
            bool_pattern = r'booleanParam\s*\(\s*name:\s*[\'"](\w+)[\'"](?:,\s*defaultValue:\s*(\w+))?(?:,\s*description:\s*[\'"]([^\'"]*)[\'"])?\s*\)'
            for match in re.finditer(bool_pattern, params_block):
                parameters.append({
                    "type": "boolean",
                    "name": match.group(1),
                    "default": match.group(2) == "true" if match.group(2) else False,
                    "description": match.group(3) or ""
                })
        
        return parameters
    
    def _parse_triggers(self, content: str) -> List[str]:
        """Parse pipeline triggers"""
        triggers = []
        
        triggers_match = re.search(r'triggers\s*{([^}]+)}', content, re.DOTALL)
        if triggers_match:
            triggers_block = triggers_match.group(1)
            
            # Parse cron
            if 'cron' in triggers_block:
                cron_match = re.search(r'cron\s*\([\'"]([^\'"]+)[\'"]\)', triggers_block)
                if cron_match:
                    triggers.append(f"cron:{cron_match.group(1)}")
            
            # Parse pollSCM
            if 'pollSCM' in triggers_block:
                poll_match = re.search(r'pollSCM\s*\([\'"]([^\'"]+)[\'"]\)', triggers_block)
                if poll_match:
                    triggers.append(f"pollSCM:{poll_match.group(1)}")
            
            # Parse upstream
            if 'upstream' in triggers_block:
                triggers.append("upstream")
        
        return triggers
    
    def _parse_options(self, content: str) -> Dict[str, Any]:
        """Parse pipeline options"""
        options = {}
        
        options_match = re.search(r'options\s*{([^}]+)}', content, re.DOTALL)
        if options_match:
            options_block = options_match.group(1)
            
            # Parse timeout
            timeout_match = re.search(r'timeout\s*\(\s*time:\s*(\d+),\s*unit:\s*[\'"](\w+)[\'"]\s*\)', options_block)
            if timeout_match:
                time_value = int(timeout_match.group(1))
                time_unit = timeout_match.group(2)
                
                # Convert to seconds
                multipliers = {'SECONDS': 1, 'MINUTES': 60, 'HOURS': 3600}
                options['timeout'] = time_value * multipliers.get(time_unit, 60)
            
            # Parse retry
            if 'retry' in options_block:
                retry_match = re.search(r'retry\s*\(\s*(\d+)\s*\)', options_block)
                if retry_match:
                    options['retry'] = int(retry_match.group(1))
            
            # Parse timestamps
            if 'timestamps()' in options_block:
                options['timestamps'] = True
        
        return options
    
    def _parse_tools(self, content: str) -> Dict[str, str]:
        """Parse tools configuration"""
        tools = {}
        
        tools_match = re.search(r'tools\s*{([^}]+)}', content)
        if tools_match:
            tools_block = tools_match.group(1)
            
            # Parse tool entries
            tool_pattern = r'(\w+)\s+[\'"]([^\'"]+)[\'"]'
            for match in re.finditer(tool_pattern, tools_block):
                tool_type = match.group(1)
                tool_version = match.group(2)
                tools[tool_type] = tool_version
        
        return tools
    
    def _parse_stages(self, content: str) -> List[JenkinsStage]:
        """Parse all stages"""
        stages = []
        
        # Find stages block
        stages_match = re.search(r'stages\s*{(.*)}(?:\s*post\s*{|\s*$)', content, re.DOTALL)
        if not stages_match:
            return stages
        
        stages_block = stages_match.group(1)
        
        # Parse individual stages with nested braces support
        stage_pattern = r'stage\s*\([\'"]([^\'"]+)[\'"]\)\s*{'
        
        pos = 0
        while pos < len(stages_block):
            match = re.search(stage_pattern, stages_block[pos:])
            if not match:
                break
            
            stage_name = match.group(1)
            start_pos = pos + match.end()
            
            # Find matching closing brace
            brace_count = 1
            end_pos = start_pos
            while end_pos < len(stages_block) and brace_count > 0:
                if stages_block[end_pos] == '{':
                    brace_count += 1
                elif stages_block[end_pos] == '}':
                    brace_count -= 1
                end_pos += 1
            
            stage_body = stages_block[start_pos:end_pos-1]
            
            # Parse stage details
            stage = JenkinsStage(name=stage_name)
            
            # Check for parallel stages
            if 'parallel' in stage_body:
                stage.parallel = True
                # Parse parallel stages
                parallel_stages = self._parse_parallel_stages(stage_body)
                stages.extend(parallel_stages)
            else:
                # Parse when condition
                stage.when_condition = self._parse_when(stage_body)
                
                # Parse environment
                stage.environment = self._parse_environment(stage_body)
                
                # Parse steps
                stage.steps = self._parse_steps(stage_body)
                
                stages.append(stage)
            
            pos = pos + match.start() + (end_pos - start_pos) + match.end()
        
        return stages
    
    def _parse_parallel_stages(self, stage_body: str) -> List[JenkinsStage]:
        """Parse parallel stages"""
        parallel_stages = []
        
        # Find parallel block
        parallel_match = re.search(r'parallel\s*{(.*)}', stage_body, re.DOTALL)
        if not parallel_match:
            return parallel_stages
        
        parallel_block = parallel_match.group(1)
        
        # Parse each parallel stage
        stage_pattern = r'[\'"]([^\'"]+)[\'"]\s*:\s*{'
        
        pos = 0
        while pos < len(parallel_block):
            match = re.search(stage_pattern, parallel_block[pos:])
            if not match:
                break
            
            stage_name = match.group(1)
            start_pos = pos + match.end()
            
            # Find matching closing brace
            brace_count = 1
            end_pos = start_pos
            while end_pos < len(parallel_block) and brace_count > 0:
                if parallel_block[end_pos] == '{':
                    brace_count += 1
                elif parallel_block[end_pos] == '}':
                    brace_count -= 1
                end_pos += 1
            
            stage_body_inner = parallel_block[start_pos:end_pos-1]
            
            stage = JenkinsStage(name=stage_name, parallel=True)
            stage.steps = self._parse_steps(stage_body_inner)
            
            parallel_stages.append(stage)
            
            pos = pos + match.start() + (end_pos - start_pos) + match.end()
        
        return parallel_stages
    
    def _parse_when(self, stage_body: str) -> Optional[str]:
        """Parse when condition"""
        when_match = re.search(r'when\s*{([^}]+)}', stage_body)
        if when_match:
            when_block = when_match.group(1).strip()
            
            # Parse branch condition
            branch_match = re.search(r'branch\s+[\'"]([^\'"]+)[\'"]', when_block)
            if branch_match:
                return f"$BRANCH_NAME == '{branch_match.group(1)}'"
            
            # Parse expression
            expr_match = re.search(r'expression\s*{([^}]+)}', when_block)
            if expr_match:
                return expr_match.group(1).strip()
            
            # Parse environment
            env_match = re.search(r'environment\s+name:\s*[\'"](\w+)[\'"],\s*value:\s*[\'"]([^\'"]+)[\'"]', when_block)
            if env_match:
                return f"${env_match.group(1)} == '{env_match.group(2)}'"
        
        return None
    
    def _parse_steps(self, steps_block: str) -> List[Dict[str, Any]]:
        """Parse steps from a stage"""
        steps = []
        
        # Find steps block
        steps_match = re.search(r'steps\s*{(.*)}', steps_block, re.DOTALL)
        if not steps_match:
            # For scripted pipeline, the entire block is steps
            steps_content = steps_block
        else:
            steps_content = steps_match.group(1)
        
        # Parse sh commands
        sh_pattern = r'sh\s+[\'"]([^\'"]+)[\'"]|sh\s*\(\s*script:\s*[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(sh_pattern, steps_content, re.DOTALL):
            command = match.group(1) or match.group(2)
            if command:
                steps.append({"type": "sh", "command": command.strip()})
        
        # Parse echo commands
        echo_pattern = r'echo\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(echo_pattern, steps_content):
            steps.append({"type": "echo", "message": match.group(1)})
        
        # Parse script blocks
        script_pattern = r'script\s*{([^}]+(?:{[^}]*}[^}]*)*?)}'
        for match in re.finditer(script_pattern, steps_content, re.DOTALL):
            script_content = match.group(1).strip()
            steps.append({"type": "script", "content": script_content})
        
        # Parse git checkout
        git_pattern = r'git\s+[\'"]([^\'"]+)[\'"]|checkout\s+scm'
        for match in re.finditer(git_pattern, steps_content):
            git_url = match.group(1) if match.group(1) else "scm"
            steps.append({"type": "git", "url": git_url})
        
        # Parse docker operations
        docker_pattern = r'docker\.(\w+)\s*\([\'"]?([^\'")\s]+)[\'"]?\)'
        for match in re.finditer(docker_pattern, steps_content):
            operation = match.group(1)
            arg = match.group(2)
            steps.append({"type": "docker", "operation": operation, "argument": arg})
        
        return steps
    
    def _parse_post_actions(self, content: str) -> Dict[str, List[str]]:
        """Parse post actions"""
        post_actions = {}
        
        post_match = re.search(r'post\s*{(.*)}', content, re.DOTALL)
        if post_match:
            post_block = post_match.group(1)
            
            # Parse different post conditions
            for condition in ['always', 'success', 'failure', 'unstable', 'changed']:
                condition_match = re.search(rf'{condition}\s*{{([^}}]+)}}', post_block)
                if condition_match:
                    actions = []
                    action_block = condition_match.group(1)
                    
                    # Parse actions in the block
                    for match in re.finditer(r'(\w+)\s+[\'"]?([^\'"}\n]+)[\'"]?', action_block):
                        actions.append(f"{match.group(1)} {match.group(2)}")
                    
                    post_actions[condition] = actions
        
        return post_actions
    
    def _convert_to_nexus(self) -> Dict[str, Any]:
        """Convert parsed Jenkins pipeline to Nexus format"""
        if not self.jenkins_pipeline:
            raise Exception("No Jenkins pipeline parsed")
        
        nexus_config = {
            "name": "converted-pipeline",
            "version": "1.0.0",
            "description": "Converted from Jenkins pipeline",
            "environment": self.jenkins_pipeline.environment.copy(),
            "triggers": self._convert_triggers(),
            "max_parallel_jobs": 5,
            "artifacts_retention": 30,
            "steps": self._convert_stages()
        }
        
        # Add notifications if post actions exist
        if self.jenkins_pipeline.post_actions:
            nexus_config["notifications"] = self._convert_notifications()
        
        return nexus_config
    
    def _convert_triggers(self) -> List[str]:
        """Convert Jenkins triggers to Nexus format"""
        nexus_triggers = []
        
        for trigger in self.jenkins_pipeline.triggers:
            if trigger.startswith("cron:"):
                nexus_triggers.append(f"schedule:{trigger[5:]}")
            elif trigger.startswith("pollSCM:"):
                nexus_triggers.append("scm:poll")
            elif trigger == "upstream":
                nexus_triggers.append("upstream:success")
            else:
                nexus_triggers.append(trigger)
        
        return nexus_triggers
    
    def _convert_stages(self) -> List[Dict[str, Any]]:
        """Convert Jenkins stages to Nexus steps"""
        nexus_steps = []
        self.step_counter = 0
        
        # Build dependency map
        stage_names = [stage.name for stage in self.jenkins_pipeline.stages]
        
        for i, stage in enumerate(self.jenkins_pipeline.stages):
            nexus_step = self._convert_stage_to_step(stage, i, stage_names)
            nexus_steps.append(nexus_step)
        
        return nexus_steps
    
    def _convert_stage_to_step(self, stage: JenkinsStage, index: int, all_stages: List[str]) -> Dict[str, Any]:
        """Convert a Jenkins stage to Nexus step"""
        self.step_counter += 1
        
        # Build command from steps
        commands = []
        for step in stage.steps:
            if step["type"] == "sh":
                commands.append(step["command"])
            elif step["type"] == "echo":
                commands.append(f'echo "{step["message"]}"')
            elif step["type"] == "script":
                commands.append(step["content"])
            elif step["type"] == "git":
                if step["url"] == "scm":
                    commands.append("git checkout $GIT_BRANCH")
                else:
                    commands.append(f'git clone {step["url"]} .')
            elif step["type"] == "docker":
                commands.append(f'docker {step["operation"]} {step["argument"]}')
        
        # Join commands
        command = " && ".join(commands) if commands else "echo 'No commands'"
        
        # Determine dependencies (previous stage unless parallel)
        depends_on = []
        if index > 0 and not stage.parallel:
            # Depend on previous non-parallel stage
            for j in range(index - 1, -1, -1):
                prev_stage = self.jenkins_pipeline.stages[j]
                if not prev_stage.parallel:
                    depends_on = [prev_stage.name]
                    break
        
        # Build step configuration
        nexus_step = {
            "name": stage.name,
            "command": command,
            "working_dir": ".",
            "timeout": self.jenkins_pipeline.options.get("timeout", 300),
            "retry_count": self.jenkins_pipeline.options.get("retry", 0),
            "environment": stage.environment,
            "depends_on": depends_on,
            "parallel": stage.parallel,
            "critical": True
        }
        
        # Add condition if present
        if stage.when_condition:
            nexus_step["condition"] = stage.when_condition
        
        # Add artifacts if any (look for common artifact patterns)
        artifacts = []
        for step in stage.steps:
            if step["type"] == "sh" and ("archive" in step["command"] or "artifact" in step["command"]):
                artifacts.append("**/*.log")
                artifacts.append("**/target/**")
        
        if artifacts:
            nexus_step["artifacts"] = artifacts
        
        return nexus_step
    
    def _convert_notifications(self) -> Dict[str, Any]:
        """Convert post actions to notifications"""
        notifications = {
            "default_channels": ["console"],
            "on_failure": True,
            "on_success": False
        }
        
        if "failure" in self.jenkins_pipeline.post_actions:
            notifications["on_failure"] = True
        
        if "success" in self.jenkins_pipeline.post_actions:
            notifications["on_success"] = True
        
        return notifications
    
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
        if not self.jenkins_pipeline or not self.nexus_config:
            return "No conversion performed yet"
        
        summary = f"""
Jenkins to Nexus Conversion Summary
===================================

Jenkins Pipeline:
- Agent: {self.jenkins_pipeline.agent.type}
- Stages: {len(self.jenkins_pipeline.stages)}
- Environment Variables: {len(self.jenkins_pipeline.environment)}
- Parameters: {len(self.jenkins_pipeline.parameters)}
- Triggers: {len(self.jenkins_pipeline.triggers)}

Nexus Pipeline:
- Steps: {len(self.nexus_config.get('steps', []))}
- Environment Variables: {len(self.nexus_config.get('environment', {}))}
- Triggers: {len(self.nexus_config.get('triggers', []))}
- Parallel Steps: {len([s for s in self.nexus_config.get('steps', []) if s.get('parallel', False)])}

Conversion Complete!
"""
        return summary.strip()
    
    def validate_conversion(self) -> Tuple[bool, List[str]]:
        """
        Validate the converted Nexus configuration.
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        if not self.nexus_config:
            return False, ["No configuration generated"]
        
        # Check for required fields
        if not self.nexus_config.get('name'):
            warnings.append("Pipeline name is missing")
        
        if not self.nexus_config.get('steps'):
            warnings.append("No steps defined in pipeline")
        
        # Check for potential issues
        steps = self.nexus_config.get('steps', [])
        
        # Check for circular dependencies
        step_names = {step['name'] for step in steps}
        for step in steps:
            for dep in step.get('depends_on', []):
                if dep not in step_names:
                    warnings.append(f"Step '{step['name']}' has invalid dependency: '{dep}'")
        
        # Check for missing commands
        for step in steps:
            if not step.get('command') or step['command'].strip() == '':
                warnings.append(f"Step '{step['name']}' has no command")
        
        # Check for very long timeouts
        for step in steps:
            if step.get('timeout', 0) > 7200:
                warnings.append(f"Step '{step['name']}' has unusually long timeout: {step['timeout']}s")
        
        # Check for parallel steps without dependencies
        parallel_steps = [s for s in steps if s.get('parallel')]
        if parallel_steps and len(parallel_steps) == len(steps):
            warnings.append("All steps are parallel - this may not be intended")
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
    
    def get_unsupported_features(self) -> List[str]:
        """
        Get a list of Jenkins features that couldn't be fully converted.
        
        Returns:
            List of unsupported feature descriptions
        """
        unsupported = []
        
        if not self.jenkins_pipeline:
            return unsupported
        
        # Check for Docker agent (limited support)
        if self.jenkins_pipeline.agent.type == "docker":
            unsupported.append(f"Docker agent '{self.jenkins_pipeline.agent.docker_image}' - converted to standard agent")
        
        # Check for complex when conditions
        for stage in self.jenkins_pipeline.stages:
            if stage.when_condition and "&&" in stage.when_condition or "||" in stage.when_condition:
                unsupported.append(f"Complex when condition in stage '{stage.name}' - may need manual adjustment")
        
        # Check for tools
        if self.jenkins_pipeline.tools:
            unsupported.append(f"Tools configuration ({', '.join(self.jenkins_pipeline.tools.keys())}) - not directly supported")
        
        # Check for input steps
        for stage in self.jenkins_pipeline.stages:
            for step in stage.steps:
                if step.get('type') == 'script' and 'input' in step.get('content', ''):
                    unsupported.append(f"Input step in stage '{stage.name}' - requires manual implementation")
        
        return unsupported
    
    def add_nexus_best_practices(self):
        """
        Apply Nexus best practices to the converted configuration.
        """
        if not self.nexus_config:
            return
        
        # Add reasonable defaults
        if 'artifacts_retention' not in self.nexus_config:
            self.nexus_config['artifacts_retention'] = 30
        
        if 'max_parallel_jobs' not in self.nexus_config:
            # Count parallel steps
            parallel_count = len([s for s in self.nexus_config.get('steps', []) if s.get('parallel')])
            self.nexus_config['max_parallel_jobs'] = min(max(parallel_count, 3), 10)
        
        # Add artifacts to build steps
        for step in self.nexus_config.get('steps', []):
            if 'build' in step['name'].lower() and 'artifacts' not in step:
                step['artifacts'] = ['**/build/**', '**/dist/**', '**/*.log']
            
            if 'test' in step['name'].lower() and 'artifacts' not in step:
                step['artifacts'] = ['**/test-results/**', '**/coverage/**', '**/*.xml']
        
        # Ensure notifications are configured
        if 'notifications' not in self.nexus_config:
            self.nexus_config['notifications'] = {
                'default_channels': ['console'],
                'on_failure': True,
                'on_success': False
            }
    
    def generate_migration_guide(self) -> str:
        """
        Generate a migration guide document.
        
        Returns:
            Markdown formatted migration guide
        """
        if not self.jenkins_pipeline or not self.nexus_config:
            return "No conversion data available"
        
        unsupported = self.get_unsupported_features()
        is_valid, warnings = self.validate_conversion()
        
        guide = f"""# Jenkins to Nexus Migration Guide

## Original Jenkins Pipeline
- **Stages**: {len(self.jenkins_pipeline.stages)}
- **Agent Type**: {self.jenkins_pipeline.agent.type}
- **Environment Variables**: {len(self.jenkins_pipeline.environment)}

## Converted Nexus Pipeline
- **Steps**: {len(self.nexus_config.get('steps', []))}
- **Parallel Steps**: {len([s for s in self.nexus_config.get('steps', []) if s.get('parallel')])}

## Validation Status
{'✅ Configuration is valid' if is_valid else '⚠️  Configuration has warnings'}

"""
        
        if warnings:
            guide += "\n### Warnings\n"
            for warning in warnings:
                guide += f"- {warning}\n"
        
        if unsupported:
            guide += "\n### Unsupported Features\n"
            guide += "The following Jenkins features require manual implementation:\n\n"
            for feature in unsupported:
                guide += f"- {feature}\n"
        
        guide += "\n## Manual Steps Required\n\n"
        guide += "1. Review the converted configuration file\n"
        guide += "2. Test the pipeline in a development environment\n"
        guide += "3. Adjust timeouts and retry counts based on your needs\n"
        guide += "4. Configure notification channels (email, Slack, etc.)\n"
        guide += "5. Set up artifact storage locations\n"
        guide += "6. Update any credential references\n"
        
        guide += "\n## Environment Variables Mapping\n\n"
        if self.jenkins_pipeline.environment:
            guide += "| Jenkins | Nexus |\n"
            guide += "|---------|-------|\n"
            for key, value in self.jenkins_pipeline.environment.items():
                guide += f"| {key} | {value} |\n"
        else:
            guide += "No environment variables defined.\n"
        
        guide += "\n## Next Steps\n\n"
        guide += "1. Save the converted configuration to a YAML or JSON file\n"
        guide += "2. Create a Nexus Pipeline instance\n"
        guide += "3. Load the configuration using `pipeline.load_config()`\n"
        guide += "4. Validate with `pipeline.validate_config()`\n"
        guide += "5. Execute with `pipeline.execute()`\n"
        
        return guide


    def convert_with_credentials(self, credential_map: Dict[str, str]):
        """
        Apply credential mapping to the converted configuration.
        
        Args:
            credential_map: Dictionary mapping Jenkins credential IDs to Nexus environment variables
        """
        if not self.nexus_config:
            return
        
        # Replace credential references in commands
        for step in self.nexus_config.get('steps', []):
            command = step.get('command', '')
            
            for jenkins_cred_id, nexus_env_var in credential_map.items():
                # Replace common Jenkins credential patterns
                command = command.replace(f'${{credentialsId: \'{jenkins_cred_id}\'}}', f'${nexus_env_var}')
                command = command.replace(f'credentialsId: \'{jenkins_cred_id}\'', f'${nexus_env_var}')
                command = command.replace(f'credentials(\'{jenkins_cred_id}\')', f'${nexus_env_var}')
            
            step['command'] = command
    
    def handle_shared_libraries(self, content: str) -> List[str]:
        """
        Extract Jenkins shared library references.
        
        Args:
            content: Jenkinsfile content
            
        Returns:
            List of shared library references
        """
        libraries = []
        
        # Parse @Library annotation
        library_pattern = r'@Library\([\'"]([^\'"]+)[\'"]\)'
        for match in re.finditer(library_pattern, content):
            libraries.append(match.group(1))
        
        return libraries
    
    def convert_matrix_builds(self, stage_body: str) -> List[JenkinsStage]:
        """
        Convert Jenkins matrix builds to parallel Nexus steps.
        
        Args:
            stage_body: Stage body containing matrix configuration
            
        Returns:
            List of parallel stages
        """
        parallel_stages = []
        
        # Parse matrix axes
        matrix_match = re.search(r'matrix\s*{(.*?)}', stage_body, re.DOTALL)
        if not matrix_match:
            return parallel_stages
        
        matrix_block = matrix_match.group(1)
        
        # Parse axes
        axes_match = re.search(r'axes\s*{(.*?)}', matrix_block, re.DOTALL)
        if axes_match:
            axes_block = axes_match.group(1)
            
            # Parse axis values
            axis_pattern = r'axis\s*{[^}]*name\s+[\'"](\w+)[\'"][^}]*values\s+([^\n}]+)}'
            axes = {}
            
            for match in re.finditer(axis_pattern, axes_block):
                axis_name = match.group(1)
                values_str = match.group(2)
                
                # Extract values
                values = re.findall(r'[\'"]([^\'"]+)[\'"]', values_str)
                axes[axis_name] = values
            
            # Generate combinations
            if axes:
                import itertools
                
                axis_names = list(axes.keys())
                axis_values = [axes[name] for name in axis_names]
                
                for combination in itertools.product(*axis_values):
                    stage_name = "_".join(combination)
                    env_vars = dict(zip(axis_names, combination))
                    
                    stage = JenkinsStage(name=stage_name, parallel=True)
                    stage.environment = env_vars
                    
                    # Parse stages block within matrix
                    stages_in_matrix = self._parse_steps(stage_body)
                    stage.steps = stages_in_matrix
                    
                    parallel_stages.append(stage)
        
        return parallel_stages
    
    def optimize_converted_pipeline(self):
        """
        Optimize the converted Nexus pipeline for better performance.
        """
        if not self.nexus_config:
            return
        
        steps = self.nexus_config.get('steps', [])
        
        # Merge sequential shell commands
        optimized_steps = []
        for step in steps:
            if optimized_steps and not step.get('parallel') and not optimized_steps[-1].get('parallel'):
                last_step = optimized_steps[-1]
                
                # Check if both are simple shell commands
                if (not step.get('depends_on') or step.get('depends_on') == [last_step['name']]) and \
                   'echo' not in step['command'].lower()[:20] and \
                   'echo' not in last_step['command'].lower()[:20]:
                    
                    # Merge commands
                    last_step['command'] += f" && {step['command']}"
                    last_step['name'] = f"{last_step['name']}_and_{step['name']}"
                    
                    # Update timeout (use max)
                    last_step['timeout'] = max(last_step.get('timeout', 300), step.get('timeout', 300))
                    
                    # Merge artifacts
                    if step.get('artifacts'):
                        last_artifacts = last_step.get('artifacts', [])
                        last_step['artifacts'] = list(set(last_artifacts + step['artifacts']))
                    
                    continue
            
            optimized_steps.append(step)
        
        self.nexus_config['steps'] = optimized_steps
    
    def export_comparison_report(self, output_path: str):
        """
        Export a detailed comparison report between Jenkins and Nexus configurations.
        
        Args:
            output_path: Path to save the comparison report
        """
        if not self.jenkins_pipeline or not self.nexus_config:
            return
        
        report = {
            "conversion_date": __import__('datetime').datetime.now().isoformat(),
            "jenkins_pipeline": {
                "agent_type": self.jenkins_pipeline.agent.type,
                "agent_label": self.jenkins_pipeline.agent.label,
                "docker_image": self.jenkins_pipeline.agent.docker_image,
                "stages_count": len(self.jenkins_pipeline.stages),
                "stages": [
                    {
                        "name": stage.name,
                        "parallel": stage.parallel,
                        "steps_count": len(stage.steps),
                        "has_condition": stage.when_condition is not None
                    }
                    for stage in self.jenkins_pipeline.stages
                ],
                "environment_vars": self.jenkins_pipeline.environment,
                "parameters": self.jenkins_pipeline.parameters,
                "triggers": self.jenkins_pipeline.triggers,
                "tools": self.jenkins_pipeline.tools,
                "options": self.jenkins_pipeline.options,
                "post_actions": self.jenkins_pipeline.post_actions
            },
            "nexus_pipeline": self.nexus_config,
            "conversion_metrics": {
                "stages_converted": len(self.nexus_config.get('steps', [])),
                "parallel_steps": len([s for s in self.nexus_config.get('steps', []) if s.get('parallel')]),
                "total_timeout": sum(s.get('timeout', 0) for s in self.nexus_config.get('steps', [])),
                "steps_with_dependencies": len([s for s in self.nexus_config.get('steps', []) if s.get('depends_on')]),
                "steps_with_conditions": len([s for s in self.nexus_config.get('steps', []) if s.get('condition')])
            },
            "unsupported_features": self.get_unsupported_features(),
            "validation": {
                "is_valid": self.validate_conversion()[0],
                "warnings": self.validate_conversion()[1]
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    
    def convert_with_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert with custom options.
        
        Args:
            options: Dictionary with conversion options
                - merge_sequential_steps: bool - merge sequential commands
                - apply_best_practices: bool - apply Nexus best practices
                - optimize: bool - optimize the pipeline
                - add_logging: bool - add extra logging steps
                
        Returns:
            Converted Nexus configuration
        """
        if not self.nexus_config:
            raise Exception("No configuration to apply options to")
        
        # Apply options
        if options.get('merge_sequential_steps', False):
            self.optimize_converted_pipeline()
        
        if options.get('apply_best_practices', True):
            self.add_nexus_best_practices()
        
        if options.get('add_logging', False):
            self._add_logging_steps()
        
        if options.get('optimize', False):
            self.optimize_converted_pipeline()
        
        return self.nexus_config
    
    def _add_logging_steps(self):
        """Add logging steps to the pipeline"""
        if not self.nexus_config:
            return
        
        steps = self.nexus_config.get('steps', [])
        
        for step in steps:
            # Add logging to commands
            command = step.get('command', '')
            step_name = step['name']
            
            # Wrap command with logging
            wrapped_command = f'echo "Starting step: {step_name}" && {command} && echo "Completed step: {step_name}"'
            step['command'] = wrapped_command


# Example usage and demonstration
if __name__ == "__main__":
    """
    Demonstration of Jenkins2Nexus converter
    """
    
    # Sample Jenkinsfile content
    sample_jenkinsfile = """
    pipeline {
        agent any
        
        environment {
            NODE_ENV = 'production'
            VERSION = '1.0.0'
        }
        
        parameters {
            string(name: 'BRANCH', defaultValue: 'main', description: 'Branch to build')
            booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run tests')
        }
        
        triggers {
            cron('H 2 * * *')
            pollSCM('H/15 * * * *')
        }
        
        options {
            timeout(time: 1, unit: 'HOURS')
            retry(2)
            timestamps()
        }
        
        stages {
            stage('Checkout') {
                steps {
                    git 'https://github.com/example/repo.git'
                }
            }
            
            stage('Build') {
                steps {
                    sh 'npm install'
                    sh 'npm run build'
                }
            }
            
            stage('Test') {
                when {
                    expression { params.RUN_TESTS == true }
                }
                steps {
                    sh 'npm test'
                }
            }
            
            stage('Parallel Tests') {
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
                }
            }
            
            stage('Deploy') {
                when {
                    branch 'main'
                }
                steps {
                    sh 'npm run deploy'
                }
            }
        }
        
        post {
            success {
                echo 'Build succeeded!'
            }
            failure {
                echo 'Build failed!'
            }
            always {
                echo 'Build complete'
            }
        }
    }
    """
    
    # Create converter
    converter = Jenkins2Nexus()
    
    # Convert
    print("Converting Jenkins pipeline to Nexus format...\n")
    nexus_config = converter.convert_string(sample_jenkinsfile)
    
    # Print summary
    print(converter.get_conversion_summary())
    
    # Print converted configuration
    print("\n\nConverted Nexus Configuration:")
    print("=" * 50)
    print(json.dumps(nexus_config, indent=2))