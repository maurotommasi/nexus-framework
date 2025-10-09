"""
Nexus Enterprise Kubernetes Git Manager
========================================
Enterprise-grade Kubernetes cluster manager with Git integration for binary deployment.

This module integrates with your existing infrastructure:
- Multi-cloud Kubernetes management (Minikube, AWS EKS, Azure AKS, GCP GKE)
- Git repository integration (GitHub/GitLab) with SSH authentication
- Binary artifact deployment from Git repositories
- Auto-route project configuration
- Centralized logging with multiple backends
- RESTful API endpoint for cluster management

Requirements:
    pip install kubernetes gitpython paramiko pyyaml requests elasticsearch \
                boto3 azure-mgmt-containerservice google-cloud-container docker

Author: Enterprise Team
Version: 2.0.0
License: Enterprise
"""

import os
import sys
import json
import yaml
import shutil
import tempfile
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import base64
import traceback

# Git and SSH
import git
from git import Repo
import paramiko

# Kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Logging backends
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


# ==================== Configuration Enums ====================

class CloudProvider(Enum):
    """Supported cloud providers"""
    MINIKUBE = "minikube"
    AWS_EKS = "aws"
    AZURE_AKS = "azure"
    GCP_GKE = "gcp"
    LOCAL = "local"


class ClusterState(Enum):
    """Cluster lifecycle states"""
    CREATING = "creating"
    ACTIVE = "active"
    UPDATING = "updating"
    DEGRADED = "degraded"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class LogBackend(Enum):
    """Logging backend types"""
    LOCAL = "local"
    ELASTICSEARCH = "elasticsearch"
    CLOUDWATCH = "cloudwatch"
    AZURE_LOGS = "azure_logs"


class GitProvider(Enum):
    """Git hosting providers"""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


# ==================== Data Classes ====================

@dataclass
class GitSourceConfig:
    """Git repository source configuration"""
    provider: GitProvider
    repo_url: str  # SSH format: git@github.com:user/repo.git
    branch: str = "main"
    tag: Optional[str] = None
    commit_hash: Optional[str] = None
    subfolder: Optional[str] = None  # e.g., "components/component-name"
    ssh_key_path: Optional[str] = None
    ssh_key_content: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "provider": self.provider.value,
            "repo_url": self.repo_url,
            "branch": self.branch,
            "tag": self.tag,
            "commit_hash": self.commit_hash,
            "subfolder": self.subfolder
        }


@dataclass
class NexusBinaryConfig:
    """Nexus binary artifact configuration"""
    name: str
    git_source: GitSourceConfig
    target_path: str = "/usr/bin/nexus"
    version_tag: Optional[str] = None
    build_command: Optional[str] = None
    binary_filename: Optional[str] = None  # If different from name
    post_install_script: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)
    
    def get_binary_name(self) -> str:
        return self.binary_filename or self.name
    
    def get_full_path(self) -> str:
        return os.path.join(self.target_path, self.get_binary_name())


@dataclass
class AutoRouteProjectConfig:
    """Auto-route project configuration"""
    name: str
    git_source: GitSourceConfig
    target_path: str = "/home/nexus/auto-route"
    config_files: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    startup_script: Optional[str] = None
    
    def get_full_path(self) -> str:
        return os.path.join(self.target_path, self.name)


@dataclass
class ClusterConfiguration:
    """Complete cluster configuration"""
    cluster_name: str
    cloud_provider: CloudProvider
    namespace: str = "default"
    
    # Binary configurations
    nexus_binaries: List[NexusBinaryConfig] = field(default_factory=list)
    
    # Auto-route projects
    auto_route_projects: List[AutoRouteProjectConfig] = field(default_factory=list)
    
    # Cluster variables
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    config_maps: Dict[str, str] = field(default_factory=dict)
    
    # Resource configuration
    replicas: int = 3
    cpu_limit: str = "1000m"
    memory_limit: str = "2Gi"
    cpu_request: str = "500m"
    memory_request: str = "1Gi"
    
    # Service configuration
    service_port: int = 8080
    service_type: str = "LoadBalancer"
    expose_external: bool = True
    
    # Health check configuration
    health_check_path: str = "/health"
    readiness_probe_path: str = "/ready"
    liveness_probe_path: str = "/health"
    
    # Docker configuration
    docker_registry: Optional[str] = None
    docker_image_tag: str = "latest"
    base_image: str = "ubuntu:22.04"
    
    # Labels and annotations
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "cluster_name": self.cluster_name,
            "cloud_provider": self.cloud_provider.value,
            "namespace": self.namespace,
            "replicas": self.replicas,
            "service_port": self.service_port,
            "environment_variables": self.environment_variables,
            "nexus_binaries": [
                {
                    "name": b.name,
                    "git_source": b.git_source.to_dict(),
                    "target_path": b.target_path
                } for b in self.nexus_binaries
            ],
            "auto_route_projects": [
                {
                    "name": p.name,
                    "git_source": p.git_source.to_dict(),
                    "target_path": p.target_path
                } for p in self.auto_route_projects
            ]
        }


@dataclass
class ClusterMetrics:
    """Cluster metrics and status"""
    cluster_name: str
    state: ClusterState
    namespace: str
    replicas: int
    ready_replicas: int
    pod_count: int
    service_count: int
    deployment_count: int
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "cluster_name": self.cluster_name,
            "state": self.state.value,
            "namespace": self.namespace,
            "replicas": self.replicas,
            "ready_replicas": self.ready_replicas,
            "pod_count": self.pod_count,
            "service_count": self.service_count,
            "deployment_count": self.deployment_count,
            "cpu_usage": self.cpu_usage_percent,
            "memory_usage": self.memory_usage_percent,
            "endpoint": self.endpoint,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    success: bool
    cluster_name: str
    deployment_id: str
    status: DeploymentStatus
    message: str
    endpoint: Optional[str] = None
    pod_names: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Optional[ClusterMetrics] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        result = {
            "success": self.success,
            "cluster_name": self.cluster_name,
            "deployment_id": self.deployment_id,
            "status": self.status.value,
            "message": self.message,
            "endpoint": self.endpoint,
            "pod_names": self.pod_names,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat()
        }
        if self.metrics:
            result["metrics"] = self.metrics.to_dict()
        return result


@dataclass
class LogConfig:
    """Logging configuration"""
    backend: LogBackend = LogBackend.LOCAL
    log_level: str = "INFO"
    local_path: str = "/var/log/nexus-k8s"
    
    # Elasticsearch
    elasticsearch_host: Optional[str] = None
    elasticsearch_port: int = 9200
    elasticsearch_index: str = "nexus-k8s-logs"
    elasticsearch_username: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    
    # CloudWatch
    cloudwatch_log_group: Optional[str] = None
    cloudwatch_stream: Optional[str] = None
    cloudwatch_region: str = "us-east-1"
    
    # Retention
    retention_days: int = 90
    max_log_size_mb: int = 1024


# ==================== SSH and Git Manager ====================

class SSHKeyManager:
    """Manage SSH keys for Git authentication"""
    
    def __init__(self):
        self.logger = logging.getLogger("SSHKeyManager")
        self.temp_key_files: List[str] = []
    
    def create_temp_key_file(self, key_content: str) -> str:
        """Create temporary SSH key file with proper permissions"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(key_content)
                if not key_content.endswith('\n'):
                    f.write('\n')
                key_path = f.name
            
            # Set proper permissions (readable only by owner)
            os.chmod(key_path, 0o600)
            self.temp_key_files.append(key_path)
            self.logger.info(f"Created temporary SSH key: {key_path}")
            return key_path
        except Exception as e:
            self.logger.error(f"Failed to create SSH key file: {e}")
            raise
    
    def cleanup(self):
        """Remove all temporary key files"""
        for key_file in self.temp_key_files:
            try:
                if os.path.exists(key_file):
                    os.remove(key_file)
                    self.logger.debug(f"Removed temporary key: {key_file}")
            except Exception as e:
                self.logger.warning(f"Failed to remove key file {key_file}: {e}")
    
    def __del__(self):
        self.cleanup()


class GitRepositoryManager:
    """Manage Git repository operations with SSH/HTTPS support"""
    
    def __init__(self, workspace_dir: str = "/tmp/nexus-k8s-workspace"):
        self.workspace_dir = workspace_dir
        self.logger = logging.getLogger("GitRepositoryManager")
        self.ssh_manager = SSHKeyManager()
        os.makedirs(workspace_dir, exist_ok=True)
        self.logger.info(f"Git workspace initialized: {workspace_dir}")
    
    def clone_repository(self, git_config: GitSourceConfig) -> str:
        """
        Clone a Git repository with SSH or HTTPS authentication
        
        Args:
            git_config: Git source configuration
            
        Returns:
            str: Path to cloned repository
        """
        repo_name = git_config.repo_url.split('/')[-1].replace('.git', '')
        clone_path = os.path.join(self.workspace_dir, repo_name)
        
        # Remove existing directory
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)
            self.logger.info(f"Removed existing repository: {clone_path}")
        
        try:
            # Setup authentication
            env_vars = os.environ.copy()
            
            if git_config.ssh_key_content or git_config.ssh_key_path:
                # SSH authentication
                ssh_key_path = git_config.ssh_key_path
                if git_config.ssh_key_content and not ssh_key_path:
                    ssh_key_path = self.ssh_manager.create_temp_key_file(
                        git_config.ssh_key_content
                    )
                
                git_ssh_cmd = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
                env_vars['GIT_SSH_COMMAND'] = git_ssh_cmd
                self.logger.info(f"Using SSH authentication for {git_config.repo_url}")
            
            # Clone repository
            self.logger.info(f"Cloning repository: {git_config.repo_url}")
            
            with git.Git().custom_environment(**env_vars):
                repo = Repo.clone_from(
                    git_config.repo_url,
                    clone_path,
                    branch=git_config.branch,
                    depth=1 if not git_config.tag and not git_config.commit_hash else None
                )
            
            # Checkout specific version
            if git_config.tag:
                self.logger.info(f"Checking out tag: {git_config.tag}")
                repo.git.checkout(git_config.tag)
            elif git_config.commit_hash:
                self.logger.info(f"Checking out commit: {git_config.commit_hash}")
                repo.git.checkout(git_config.commit_hash)
            
            self.logger.info(f"Successfully cloned to: {clone_path}")
            return clone_path
            
        except Exception as e:
            self.logger.error(f"Failed to clone repository {git_config.repo_url}: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def get_subfolder_path(self, clone_path: str, subfolder: Optional[str]) -> str:
        """Get full path to subfolder within repository"""
        if subfolder:
            full_path = os.path.join(clone_path, subfolder)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Subfolder not found: {subfolder} in {clone_path}")
            return full_path
        return clone_path
    
    def find_binary(self, search_path: str, binary_name: str) -> Optional[str]:
        """Find binary file in directory tree"""
        for root, dirs, files in os.walk(search_path):
            if binary_name in files:
                binary_path = os.path.join(root, binary_name)
                self.logger.info(f"Found binary: {binary_path}")
                return binary_path
        
        self.logger.warning(f"Binary '{binary_name}' not found in {search_path}")
        return None
    
    def build_binary(self, source_path: str, build_command: str, binary_name: str) -> Optional[str]:
        """Build binary from source code"""
        try:
            original_dir = os.getcwd()
            os.chdir(source_path)
            
            self.logger.info(f"Executing build command: {build_command}")
            result = subprocess.run(
                build_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                self.logger.error(f"Build failed: {result.stderr}")
                os.chdir(original_dir)
                return None
            
            self.logger.info(f"Build output: {result.stdout}")
            
            # Find the built binary
            binary_path = self.find_binary(source_path, binary_name)
            os.chdir(original_dir)
            return binary_path
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Build timeout exceeded (600s)")
            os.chdir(original_dir)
            return None
        except Exception as e:
            self.logger.error(f"Build failed: {e}")
            os.chdir(original_dir)
            return None
    
    def cleanup_workspace(self):
        """Clean up workspace directory"""
        try:
            if os.path.exists(self.workspace_dir):
                shutil.rmtree(self.workspace_dir)
                self.logger.info(f"Cleaned workspace: {self.workspace_dir}")
        except Exception as e:
            self.logger.error(f"Workspace cleanup failed: {e}")
        
        self.ssh_manager.cleanup()


# ==================== Centralized Log Manager ====================

class NexusLogManager:
    """Enterprise logging system for Kubernetes clusters"""
    
    def __init__(self, config: LogConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.es_client = None
        self.cloudwatch_client = None
        
        # Setup local logging
        if config.backend == LogBackend.LOCAL or True:  # Always enable local as fallback
            os.makedirs(config.local_path, exist_ok=True)
        
        # Setup Elasticsearch
        if config.backend == LogBackend.ELASTICSEARCH:
            self._setup_elasticsearch()
        
        # Setup CloudWatch
        if config.backend == LogBackend.CLOUDWATCH:
            self._setup_cloudwatch()
    
    def _setup_logger(self) -> logging.Logger:
        """Configure logger"""
        logger = logging.getLogger("NexusLogManager")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = os.path.join(self.config.local_path, "nexus-k8s-manager.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _setup_elasticsearch(self):
        """Initialize Elasticsearch client"""
        if not ELASTICSEARCH_AVAILABLE:
            self.logger.warning("Elasticsearch not available, falling back to local logging")
            return
        
        try:
            if self.config.elasticsearch_username and self.config.elasticsearch_password:
                self.es_client = Elasticsearch(
                    [f"http://{self.config.elasticsearch_host}:{self.config.elasticsearch_port}"],
                    basic_auth=(self.config.elasticsearch_username, self.config.elasticsearch_password)
                )
            else:
                self.es_client = Elasticsearch(
                    [f"http://{self.config.elasticsearch_host}:{self.config.elasticsearch_port}"]
                )
            self.logger.info("Connected to Elasticsearch")
        except Exception as e:
            self.logger.error(f"Failed to connect to Elasticsearch: {e}")
            self.es_client = None
    
    def _setup_cloudwatch(self):
        """Initialize CloudWatch client"""
        if not AWS_AVAILABLE:
            self.logger.warning("boto3 not available, falling back to local logging")
            return
        
        try:
            self.cloudwatch_client = boto3.client(
                'logs',
                region_name=self.config.cloudwatch_region
            )
            self.logger.info("Connected to CloudWatch")
        except Exception as e:
            self.logger.error(f"Failed to connect to CloudWatch: {e}")
            self.cloudwatch_client = None
    
    def log_event(
        self,
        cluster_name: str,
        event_type: str,
        message: str,
        level: str = "INFO",
        metadata: Optional[Dict] = None
    ):
        """Log a cluster event to all configured backends"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cluster_name": cluster_name,
            "event_type": event_type,
            "level": level,
            "message": message,
            "metadata": metadata or {}
        }
        
        # Log to local file
        self._log_to_file(cluster_name, log_entry)
        
        # Log to Elasticsearch
        if self.es_client:
            self._log_to_elasticsearch(log_entry)
        
        # Log to CloudWatch
        if self.cloudwatch_client:
            self._log_to_cloudwatch(log_entry)
        
        # Standard logging
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{cluster_name}] {event_type}: {message}")
    
    def _log_to_file(self, cluster_name: str, log_entry: Dict):
        """Write log entry to local JSON Lines file"""
        log_file = os.path.join(
            self.config.local_path,
            f"{cluster_name}.jsonl"
        )
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
    
    def _log_to_elasticsearch(self, log_entry: Dict):
        """Send log entry to Elasticsearch"""
        try:
            self.es_client.index(
                index=self.config.elasticsearch_index,
                document=log_entry
            )
        except Exception as e:
            self.logger.error(f"Failed to log to Elasticsearch: {e}")
    
    def _log_to_cloudwatch(self, log_entry: Dict):
        """Send log entry to CloudWatch"""
        try:
            stream_name = self.config.cloudwatch_stream or f"nexus-k8s-{log_entry['cluster_name']}"
            
            # Create log stream if it doesn't exist
            try:
                self.cloudwatch_client.create_log_stream(
                    logGroupName=self.config.cloudwatch_log_group,
                    logStreamName=stream_name
                )
            except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Send log
            self.cloudwatch_client.put_log_events(
                logGroupName=self.config.cloudwatch_log_group,
                logStreamName=stream_name,
                logEvents=[{
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'message': json.dumps(log_entry)
                }]
            )
        except Exception as e:
            self.logger.error(f"Failed to log to CloudWatch: {e}")
    
    def collect_pod_logs(
        self,
        cluster_name: str,
        namespace: str,
        k8s_client: client.CoreV1Api,
        pod_name: Optional[str] = None,
        label_selector: Optional[str] = None,
        tail_lines: int = 100
    ):
        """Collect logs from Kubernetes pods"""
        try:
            if pod_name:
                pods = [k8s_client.read_namespaced_pod(pod_name, namespace)]
            else:
                pods = k8s_client.list_namespaced_pod(
                    namespace,
                    label_selector=label_selector
                ).items
            
            for pod in pods:
                try:
                    logs = k8s_client.read_namespaced_pod_log(
                        pod.metadata.name,
                        namespace,
                        tail_lines=tail_lines
                    )
                    
                    self.log_event(
                        cluster_name=cluster_name,
                        event_type="pod_logs",
                        message=f"Collected logs from pod {pod.metadata.name}",
                        level="INFO",
                        metadata={
                            "pod_name": pod.metadata.name,
                            "namespace": namespace,
                            "logs": logs
                        }
                    )
                except Exception as e:
                    self.logger.error(f"Failed to collect logs from pod {pod.metadata.name}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to collect pod logs: {e}")
    
    def query_logs(
        self,
        cluster_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Query logs with filters"""
        if self.config.backend == LogBackend.ELASTICSEARCH and self.es_client:
            return self._query_elasticsearch_logs(
                cluster_name, start_time, end_time, event_type, level, limit
            )
        else:
            return self._query_local_logs(
                cluster_name, start_time, end_time, event_type, level, limit
            )
    
    def _query_local_logs(
        self,
        cluster_name: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        event_type: Optional[str],
        level: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Query logs from local files"""
        results = []
        
        # Determine files to read
        if cluster_name:
            log_files = [os.path.join(self.config.local_path, f"{cluster_name}.jsonl")]
        else:
            log_files = [
                os.path.join(self.config.local_path, f)
                for f in os.listdir(self.config.local_path)
                if f.endswith('.jsonl')
            ]
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            with open(log_file, 'r') as f:
                for line in f:
                    if len(results) >= limit:
                        break
                    
                    try:
                        entry = json.loads(line)
                        
                        # Apply filters
                        if start_time and datetime.fromisoformat(entry['timestamp']) < start_time:
                            continue
                        if end_time and datetime.fromisoformat(entry['timestamp']) > end_time:
                            continue
                        if event_type and entry.get('event_type') != event_type:
                            continue
                        if level and entry.get('level') != level:
                            continue
                        
                        results.append(entry)
                    except json.JSONDecodeError:
                        continue
        
        return results[:limit]
    
    def _query_elasticsearch_logs(
        self,
        cluster_name: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        event_type: Optional[str],
        level: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Query logs from Elasticsearch"""
        query = {"bool": {"must": []}}
        
        if cluster_name:
            query["bool"]["must"].append({"term": {"cluster_name": cluster_name}})
        if event_type:
            query["bool"]["must"].append({"term": {"event_type": event_type}})
        if level:
            query["bool"]["must"].append({"term": {"level": level}})
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            query["bool"]["must"].append({"range": {"timestamp": time_range}})
        
        try:
            response = self.es_client.search(
                index=self.config.elasticsearch_index,
                query=query,
                size=limit,
                sort=[{"timestamp": {"order": "desc"}}]
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            self.logger.error(f"Failed to query Elasticsearch: {e}")
            return []
    
    def export_logs(self, output_file: str, cluster_name: Optional[str] = None, format: str = "json"):
        """Export logs to file"""
        logs = self.query_logs(cluster_name=cluster_name, limit=100000)
        
        with open(output_file, 'w') as f:
            if format == "json":
                json.dump(logs, f, indent=2)
            elif format == "jsonl":
                for log in logs:
                    f.write(json.dumps(log) + '\n')
        
        self.logger.info(f"Exported {len(logs)} logs to {output_file}")
    
    def cleanup_old_logs(self):
        """Remove logs older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        # Clean local logs
        for log_file in os.listdir(self.config.local_path):
            if not log_file.endswith('.jsonl'):
                continue
            
            file_path = os.path.join(self.config.local_path, log_file)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < cutoff_date:
                    os.remove(file_path)
                    self.logger.info(f"Removed old log file: {log_file}")
            except Exception as e:
                self.logger.error(f"Failed to clean log file {log_file}: {e}")


# ==================== Docker Image Builder ====================

class DockerImageBuilder:
    """Build Docker images with Git artifacts and binaries"""
    
    def __init__(self, registry: Optional[str] = None):
        self.registry = registry
        self.logger = logging.getLogger("DockerImageBuilder")
    
    def generate_dockerfile(
        self,
        config: ClusterConfiguration,
        binary_paths: Dict[str, str],
        auto_route_paths: Dict[str, str]
    ) -> str:
        """Generate Dockerfile for deployment"""
        
        dockerfile = f"""FROM {config.base_image}

# Install dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    wget \\
    git \\
    ca-certificates \\
    openssh-client \\
    && rm -rf /var/lib/apt/lists/*

# Create nexus user and directories
RUN useradd -m -s /bin/bash nexus && \\
    mkdir -p /usr/bin/nexus /home/nexus/auto-route && \\
    chown -R nexus:nexus /home/nexus

# Copy nexus binaries
"""
        
        # Add binary copies
        for binary_config in config.nexus_binaries:
            binary_name = binary_config.get_binary_name()
            target_path = binary_config.get_full_path()
            
            if binary_name in binary_paths:
                dockerfile += f"COPY --chown=nexus:nexus {binary_name} {target_path}\n"
                dockerfile += f"RUN chmod +x {target_path}\n"
        
        dockerfile += "\n# Copy auto-route projects\n"
        
        # Add auto-route project copies
        for project_config in config.auto_route_projects:
            project_name = project_config.name
            target_path = project_config.get_full_path()
            
            if project_name in auto_route_paths:
                dockerfile += f"COPY --chown=nexus:nexus {project_name}/ {target_path}/\n"
        
        # Environment variables
        dockerfile += "\n# Set environment variables\n"
        all_env_vars = {**config.environment_variables}
        
        # Add binary-specific env vars
        for binary_config in config.nexus_binaries:
            all_env_vars.update(binary_config.environment_variables)
        
        # Add auto-route project env vars
        for project_config in config.auto_route_projects:
            all_env_vars.update(project_config.environment_variables)
        
        for key, value in all_env_vars.items():
            dockerfile += f'ENV {key}="{value}"\n'
        
        # Add PATH
        dockerfile += f'ENV PATH="/usr/bin/nexus:$PATH"\n'
        
        dockerfile += f"""
# Expose service port
EXPOSE {config.service_port}

# Switch to nexus user
USER nexus
WORKDIR /home/nexus

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \\
    CMD curl -f http://localhost:{config.service_port}{config.health_check_path} || exit 1

# Default command
CMD ["/bin/bash", "-c", "tail -f /dev/null"]
"""
        
        return dockerfile
    
    def build_image(
        self,
        dockerfile_content: str,
        context_dir: str,
        image_name: str,
        tag: str = "latest"
    ) -> str:
        """Build Docker image"""
        full_image_name = f"{self.registry}/{image_name}:{tag}" if self.registry else f"{image_name}:{tag}"
        
        # Write Dockerfile
        dockerfile_path = os.path.join(context_dir, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        try:
            # Build image
            cmd = ["docker", "build", "-t", full_image_name, context_dir]
            self.logger.info(f"Building Docker image: {full_image_name}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Docker build successful")
            self.logger.debug(result.stdout)
            return full_image_name
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Docker build failed: {e.stderr}")
            raise
    
    def push_image(self, image_name: str):
        """Push Docker image to registry"""
        if not self.registry:
            self.logger.warning("No registry configured, skipping push")
            return
        
        try:
            cmd = ["docker", "push", image_name]
            self.logger.info(f"Pushing image: {image_name}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info("Docker push successful")
            self.logger.debug(result.stdout)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Docker push failed: {e.stderr}")
            raise


# ==================== Kubernetes Deployment Manager ====================

class KubernetesDeploymentManager:
    """Manage Kubernetes deployments and services"""
    
    def __init__(self, log_manager: NexusLogManager):
        self.logger = logging.getLogger("K8sDeploymentManager")
        self.log_manager = log_manager
    
    def create_namespace(self, k8s_client: client.CoreV1Api, namespace: str) -> bool:
        """Create namespace if it doesn't exist"""
        try:
            k8s_client.read_namespace(namespace)
            self.logger.info(f"Namespace {namespace} already exists")
            return True
        except ApiException as e:
            if e.status == 404:
                # Create namespace
                ns_manifest = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=namespace)
                )
                k8s_client.create_namespace(ns_manifest)
                self.logger.info(f"Created namespace: {namespace}")
                return True
            else:
                self.logger.error(f"Failed to check namespace: {e}")
                return False
    
    def create_config_map(
        self,
        k8s_client: client.CoreV1Api,
        config: ClusterConfiguration
    ) -> bool:
        """Create ConfigMap for environment variables"""
        try:
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=f"{config.cluster_name}-config",
                    namespace=config.namespace
                ),
                data=config.config_maps
            )
            
            try:
                k8s_client.create_namespaced_config_map(config.namespace, configmap)
                self.logger.info(f"Created ConfigMap: {config.cluster_name}-config")
            except ApiException as e:
                if e.status == 409:  # Already exists
                    k8s_client.replace_namespaced_config_map(
                        f"{config.cluster_name}-config",
                        config.namespace,
                        configmap
                    )
                    self.logger.info(f"Updated ConfigMap: {config.cluster_name}-config")
                else:
                    raise
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create ConfigMap: {e}")
            return False
    
    def create_secret(
        self,
        k8s_client: client.CoreV1Api,
        config: ClusterConfiguration
    ) -> bool:
        """Create Secret for sensitive data"""
        try:
            # Encode secrets
            encoded_secrets = {
                k: base64.b64encode(v.encode()).decode()
                for k, v in config.secrets.items()
            }
            
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=f"{config.cluster_name}-secret",
                    namespace=config.namespace
                ),
                type="Opaque",
                data=encoded_secrets
            )
            
            try:
                k8s_client.create_namespaced_secret(config.namespace, secret)
                self.logger.info(f"Created Secret: {config.cluster_name}-secret")
            except ApiException as e:
                if e.status == 409:  # Already exists
                    k8s_client.replace_namespaced_secret(
                        f"{config.cluster_name}-secret",
                        config.namespace,
                        secret
                    )
                    self.logger.info(f"Updated Secret: {config.cluster_name}-secret")
                else:
                    raise
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create Secret: {e}")
            return False
    
    def create_deployment(
        self,
        k8s_client: client.AppsV1Api,
        config: ClusterConfiguration,
        image_name: str
    ) -> bool:
        """Create Kubernetes Deployment"""
        try:
            # Container specification
            container = client.V1Container(
                name=config.cluster_name,
                image=image_name,
                image_pull_policy="Always",
                ports=[client.V1ContainerPort(container_port=config.service_port)],
                env=[
                    client.V1EnvVar(name=k, value=v)
                    for k, v in config.environment_variables.items()
                ],
                resources=client.V1ResourceRequirements(
                    requests={
                        "cpu": config.cpu_request,
                        "memory": config.memory_request
                    },
                    limits={
                        "cpu": config.cpu_limit,
                        "memory": config.memory_limit
                    }
                ),
                liveness_probe=client.V1Probe(
                    http_get=client.V1HTTPGetAction(
                        path=config.liveness_probe_path,
                        port=config.service_port
                    ),
                    initial_delay_seconds=30,
                    period_seconds=10
                ),
                readiness_probe=client.V1Probe(
                    http_get=client.V1HTTPGetAction(
                        path=config.readiness_probe_path,
                        port=config.service_port
                    ),
                    initial_delay_seconds=5,
                    period_seconds=5
                )
            )
            
            # Pod template
            template = client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": config.cluster_name,
                        **config.labels
                    }
                ),
                spec=client.V1PodSpec(containers=[container])
            )
            
            # Deployment spec
            spec = client.V1DeploymentSpec(
                replicas=config.replicas,
                selector=client.V1LabelSelector(
                    match_labels={"app": config.cluster_name}
                ),
                template=template
            )
            
            # Deployment
            deployment = client.V1Deployment(
                api_version="apps/v1",
                kind="Deployment",
                metadata=client.V1ObjectMeta(
                    name=config.cluster_name,
                    namespace=config.namespace,
                    annotations=config.annotations
                ),
                spec=spec
            )
            
            try:
                k8s_client.create_namespaced_deployment(config.namespace, deployment)
                self.logger.info(f"Created Deployment: {config.cluster_name}")
            except ApiException as e:
                if e.status == 409:  # Already exists
                    k8s_client.replace_namespaced_deployment(
                        config.cluster_name,
                        config.namespace,
                        deployment
                    )
                    self.logger.info(f"Updated Deployment: {config.cluster_name}")
                else:
                    raise
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create Deployment: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def create_service(
        self,
        k8s_client: client.CoreV1Api,
        config: ClusterConfiguration
    ) -> Optional[str]:
        """Create Kubernetes Service"""
        try:
            service = client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=client.V1ObjectMeta(
                    name=f"{config.cluster_name}-service",
                    namespace=config.namespace
                ),
                spec=client.V1ServiceSpec(
                    type=config.service_type,
                    selector={"app": config.cluster_name},
                    ports=[client.V1ServicePort(
                        port=config.service_port,
                        target_port=config.service_port,
                        protocol="TCP"
                    )]
                )
            )
            
            try:
                result = k8s_client.create_namespaced_service(config.namespace, service)
                self.logger.info(f"Created Service: {config.cluster_name}-service")
            except ApiException as e:
                if e.status == 409:  # Already exists
                    result = k8s_client.replace_namespaced_service(
                        f"{config.cluster_name}-service",
                        config.namespace,
                        service
                    )
                    self.logger.info(f"Updated Service: {config.cluster_name}-service")
                else:
                    raise
            
            # Get service endpoint
            endpoint = self._get_service_endpoint(k8s_client, config)
            return endpoint
            
        except Exception as e:
            self.logger.error(f"Failed to create Service: {e}")
            return None
    
    def _get_service_endpoint(
        self,
        k8s_client: client.CoreV1Api,
        config: ClusterConfiguration,
        timeout: int = 60
    ) -> Optional[str]:
        """Get service endpoint (waits for LoadBalancer IP if needed)"""
        import time
        
        service_name = f"{config.cluster_name}-service"
        
        if config.service_type == "ClusterIP":
            service = k8s_client.read_namespaced_service(service_name, config.namespace)
            return f"{service.spec.cluster_ip}:{config.service_port}"
        
        elif config.service_type == "NodePort":
            service = k8s_client.read_namespaced_service(service_name, config.namespace)
            node_port = service.spec.ports[0].node_port
            # Get first node's IP
            nodes = k8s_client.list_node()
            if nodes.items:
                node_ip = nodes.items[0].status.addresses[0].address
                return f"{node_ip}:{node_port}"
        
        elif config.service_type == "LoadBalancer":
            # Wait for LoadBalancer IP
            start_time = time.time()
            while time.time() - start_time < timeout:
                service = k8s_client.read_namespaced_service(service_name, config.namespace)
                if service.status.load_balancer.ingress:
                    ingress = service.status.load_balancer.ingress[0]
                    ip = ingress.ip or ingress.hostname
                    return f"{ip}:{config.service_port}"
                time.sleep(2)
            
            self.logger.warning("LoadBalancer IP not available within timeout")
        
        return None
    
    def get_pod_names(
        self,
        k8s_client: client.CoreV1Api,
        config: ClusterConfiguration
    ) -> List[str]:
        """Get list of pod names for deployment"""
        try:
            pods = k8s_client.list_namespaced_pod(
                config.namespace,
                label_selector=f"app={config.cluster_name}"
            )
            return [pod.metadata.name for pod in pods.items]
        except Exception as e:
            self.logger.error(f"Failed to get pod names: {e}")
            return []
    
    def wait_for_deployment(
        self,
        k8s_client: client.AppsV1Api,
        config: ClusterConfiguration,
        timeout: int = 300
    ) -> bool:
        """Wait for deployment to be ready"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                deployment = k8s_client.read_namespaced_deployment(
                    config.cluster_name,
                    config.namespace
                )
                
                if (deployment.status.ready_replicas and 
                    deployment.status.ready_replicas == config.replicas):
                    self.logger.info(f"Deployment {config.cluster_name} is ready")
                    return True
                
                self.logger.info(f"Waiting for deployment... ({deployment.status.ready_replicas}/{config.replicas} ready)")
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error checking deployment status: {e}")
                time.sleep(5)
        
        self.logger.error(f"Deployment timeout after {timeout}s")
        return False


# ==================== Main Enterprise Manager ====================

class NexusKubernetesManager:
    """
    Enterprise Nexus Kubernetes Manager
    
    Comprehensive cluster management with Git integration for binary deployment,
    multi-cloud support, and centralized logging.
    """
    
    def __init__(
        self,
        log_config: Optional[LogConfig] = None,
        docker_registry: Optional[str] = None,
        workspace_dir: str = "/tmp/nexus-k8s-workspace"
    ):
        """
        Initialize Nexus Kubernetes Manager
        
        Args:
            log_config: Logging configuration
            docker_registry: Docker registry URL (e.g., "myregistry.azurecr.io")
            workspace_dir: Working directory for Git operations
        """
        self.logger = self._setup_logging()
        self.log_manager = NexusLogManager(log_config or LogConfig())
        self.git_manager = GitRepositoryManager(workspace_dir)
        self.image_builder = DockerImageBuilder(docker_registry)
        self.k8s_deployment_manager = KubernetesDeploymentManager(self.log_manager)
        
        self.clusters: Dict[str, Dict] = {}
        self.deployments: Dict[str, DeploymentResult] = {}
        
        self.logger.info("Nexus Kubernetes Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger("NexusK8sManager")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def create_cluster_deployment(
        self,
        config: ClusterConfiguration,
        kubeconfig_path: Optional[str] = None,
        context: Optional[str] = None
    ) -> DeploymentResult:
        """
        Create and deploy a Kubernetes cluster with Git-based binaries
        
        Args:
            config: Complete cluster configuration
            kubeconfig_path: Path to kubeconfig file
            context: Kubernetes context to use
            
        Returns:
            DeploymentResult: Deployment result with status and metrics
        """
        deployment_id = str(uuid.uuid4())
        cluster_name = config.cluster_name
        
        self.log_manager.log_event(
            cluster_name,
            "deployment_start",
            f"Starting cluster deployment: {cluster_name}",
            metadata={"deployment_id": deployment_id, "config": config.to_dict()}
        )
        
        try:
            # Step 1: Clone repositories and prepare binaries
            self.logger.info(f"[{cluster_name}] Step 1/7: Cloning Git repositories...")
            binary_paths, auto_route_paths = self._prepare_artifacts(config)
            
            # Step 2: Build Docker image
            self.logger.info(f"[{cluster_name}] Step 2/7: Building Docker image...")
            image_name = self._build_deployment_image(config, binary_paths, auto_route_paths)
            
            # Step 3: Connect to Kubernetes cluster
            self.logger.info(f"[{cluster_name}] Step 3/7: Connecting to Kubernetes...")
            k8s_clients = self._connect_to_kubernetes(config, kubeconfig_path, context)
            
            # Step 4: Create namespace and resources
            self.logger.info(f"[{cluster_name}] Step 4/7: Creating Kubernetes resources...")
            self._create_kubernetes_resources(config, k8s_clients)
            
            # Step 5: Deploy application
            self.logger.info(f"[{cluster_name}] Step 5/7: Deploying application...")
            endpoint = self._deploy_application(config, k8s_clients, image_name)
            
            # Step 6: Wait for deployment to be ready
            self.logger.info(f"[{cluster_name}] Step 6/7: Waiting for deployment...")
            ready = self.k8s_deployment_manager.wait_for_deployment(
                k8s_clients['apps_v1'],
                config,
                timeout=300
            )
            
            if not ready:
                raise Exception("Deployment did not become ready within timeout")
            
            # Step 7: Collect metrics and logs
            self.logger.info(f"[{cluster_name}] Step 7/7: Collecting metrics...")
            metrics = self._collect_metrics(config, k8s_clients, endpoint)
            pod_names = self.k8s_deployment_manager.get_pod_names(k8s_clients['core_v1'], config)
            
            # Setup log collection
            self.log_manager.collect_pod_logs(
                cluster_name,
                config.namespace,
                k8s_clients['core_v1'],
                label_selector=f"app={cluster_name}"
            )
            
            # Store cluster info
            self.clusters[cluster_name] = {
                "config": config,
                "k8s_clients": k8s_clients,
                "image_name": image_name,
                "endpoint": endpoint,
                "deployment_id": deployment_id
            }
            
            # Create success result
            result = DeploymentResult(
                success=True,
                cluster_name=cluster_name,
                deployment_id=deployment_id,
                status=DeploymentStatus.COMPLETED,
                message=f"Deployment successful. Endpoint: {endpoint}",
                endpoint=endpoint,
                pod_names=pod_names,
                metrics=metrics
            )
            
            self.deployments[deployment_id] = result
            
            self.log_manager.log_event(
                cluster_name,
                "deployment_complete",
                f"Deployment completed successfully",
                metadata=result.to_dict()
            )
            
            self.logger.info(f"✓ Cluster {cluster_name} deployed successfully!")
            self.logger.info(f"  Endpoint: {endpoint}")
            self.logger.info(f"  Pods: {', '.join(pod_names)}")
            
            return result
            
        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            self.logger.error(f"[{cluster_name}] {error_msg}")
            self.logger.error(traceback.format_exc())
            
            result = DeploymentResult(
                success=False,
                cluster_name=cluster_name,
                deployment_id=deployment_id,
                status=DeploymentStatus.FAILED,
                message=error_msg,
                errors=[str(e), traceback.format_exc()]
            )
            
            self.deployments[deployment_id] = result
            
            self.log_manager.log_event(
                cluster_name,
                "deployment_failed",
                error_msg,
                level="ERROR",
                metadata={"deployment_id": deployment_id, "error": str(e)}
            )
            
            return result
        
        finally:
            # Cleanup Git workspace
            self.git_manager.cleanup_workspace()
    
    def _prepare_artifacts(
        self,
        config: ClusterConfiguration
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Clone repositories and prepare binary artifacts"""
        binary_paths = {}
        auto_route_paths = {}
        
        # Process nexus binaries
        for binary_config in config.nexus_binaries:
            self.logger.info(f"Processing binary: {binary_config.name}")
            
            try:
                # Clone repository
                clone_path = self.git_manager.clone_repository(binary_config.git_source)
                
                # Get subfolder if specified
                search_path = self.git_manager.get_subfolder_path(
                    clone_path,
                    binary_config.git_source.subfolder
                )
                
                binary_name = binary_config.get_binary_name()
                
                # Find binary
                binary_path = self.git_manager.find_binary(search_path, binary_name)
                
                if not binary_path and binary_config.build_command:
                    # Build binary
                    self.logger.info(f"Binary not found, building from source...")
                    binary_path = self.git_manager.build_binary(
                        search_path,
                        binary_config.build_command,
                        binary_name
                    )
                
                if binary_path:
                    binary_paths[binary_name] = binary_path
                    self.logger.info(f"✓ Prepared binary: {binary_name}")
                else:
                    raise FileNotFoundError(f"Binary {binary_name} not found and could not be built")
                    
            except Exception as e:
                self.logger.error(f"Failed to prepare binary {binary_config.name}: {e}")
                raise
        
        # Process auto-route projects
        for project_config in config.auto_route_projects:
            self.logger.info(f"Processing auto-route project: {project_config.name}")
            
            try:
                # Clone repository
                clone_path = self.git_manager.clone_repository(project_config.git_source)
                
                # Get subfolder if specified
                project_path = self.git_manager.get_subfolder_path(
                    clone_path,
                    project_config.git_source.subfolder
                )
                
                auto_route_paths[project_config.name] = project_path
                self.logger.info(f"✓ Prepared auto-route project: {project_config.name}")
                
            except Exception as e:
                self.logger.error(f"Failed to prepare auto-route project {project_config.name}: {e}")
                raise
        
        return binary_paths, auto_route_paths
    
    def _build_deployment_image(
        self,
        config: ClusterConfiguration,
        binary_paths: Dict[str, str],
        auto_route_paths: Dict[str, str]
    ) -> str:
        """Build Docker image with all artifacts"""
        context_dir = tempfile.mkdtemp(prefix="nexus-k8s-build-")
        
        try:
            # Copy binaries to context
            for binary_name, source_path in binary_paths.items():
                dest_path = os.path.join(context_dir, binary_name)
                shutil.copy2(source_path, dest_path)
                os.chmod(dest_path, 0o755)
            
            # Copy auto-route projects to context
            for project_name, source_path in auto_route_paths.items():
                dest_path = os.path.join(context_dir, project_name)
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path)
                else:
                    os.makedirs(dest_path)
                    shutil.copy2(source_path, dest_path)
            
            # Generate Dockerfile
            dockerfile_content = self.image_builder.generate_dockerfile(
                config,
                binary_paths,
                auto_route_paths
            )
            
            # Build image
            image_name = self.image_builder.build_image(
                dockerfile_content,
                context_dir,
                config.cluster_name,
                config.docker_image_tag
            )
            
            # Push to registry if configured
            if self.image_builder.registry:
                self.image_builder.push_image(image_name)
            
            return image_name
            
        finally:
            # Cleanup build context
            shutil.rmtree(context_dir, ignore_errors=True)
    
    def _connect_to_kubernetes(
        self,
        config: ClusterConfiguration,
        kubeconfig_path: Optional[str],
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Connect to Kubernetes cluster"""
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path, context=context)
            else:
                try:
                    config.load_kube_config(context=context)
                except:
                    # Try in-cluster config
                    config.load_incluster_config()
            
            return {
                "core_v1": client.CoreV1Api(),
                "apps_v1": client.AppsV1Api(),
                "batch_v1": client.BatchV1Api()
            }
        except Exception as e:
            self.logger.error(f"Failed to connect to Kubernetes: {e}")
            raise
    
    def _create_kubernetes_resources(
        self,
        config: ClusterConfiguration,
        k8s_clients: Dict[str, Any]
    ):
        """Create Kubernetes resources (namespace, configmap, secret)"""
        # Create namespace
        self.k8s_deployment_manager.create_namespace(k8s_clients['core_v1'], config.namespace)
        
        # Create ConfigMap if needed
        if config.config_maps:
            self.k8s_deployment_manager.create_config_map(k8s_clients['core_v1'], config)
        
        # Create Secret if needed
        if config.secrets:
            self.k8s_deployment_manager.create_secret(k8s_clients['core_v1'], config)
    
    def _deploy_application(
        self,
        config: ClusterConfiguration,
        k8s_clients: Dict[str, Any],
        image_name: str
    ) -> Optional[str]:
        """Deploy application to Kubernetes"""
        # Create deployment
        success = self.k8s_deployment_manager.create_deployment(
            k8s_clients['apps_v1'],
            config,
            image_name
        )
        
        if not success:
            raise Exception("Failed to create deployment")
        
        # Create service
        endpoint = self.k8s_deployment_manager.create_service(
            k8s_clients['core_v1'],
            config
        )
        
        return endpoint
    
    def _collect_metrics(
        self,
        config: ClusterConfiguration,
        k8s_clients: Dict[str, Any],
        endpoint: Optional[str]
    ) -> ClusterMetrics:
        """Collect cluster metrics"""
        try:
            # Get deployment
            deployment = k8s_clients['apps_v1'].read_namespaced_deployment(
                config.cluster_name,
                config.namespace
            )
            
            # Get pods
            pods = k8s_clients['core_v1'].list_namespaced_pod(
                config.namespace,
                label_selector=f"app={config.cluster_name}"
            )
            
            # Get services
            services = k8s_clients['core_v1'].list_namespaced_service(config.namespace)
            
            # Get all deployments in namespace
            deployments = k8s_clients['apps_v1'].list_namespaced_deployment(config.namespace)
            
            metrics = ClusterMetrics(
                cluster_name=config.cluster_name,
                state=ClusterState.ACTIVE,
                namespace=config.namespace,
                replicas=deployment.spec.replicas,
                ready_replicas=deployment.status.ready_replicas or 0,
                pod_count=len(pods.items),
                service_count=len(services.items),
                deployment_count=len(deployments.items),
                endpoint=endpoint
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return ClusterMetrics(
                cluster_name=config.cluster_name,
                state=ClusterState.DEGRADED,
                namespace=config.namespace,
                replicas=0,
                ready_replicas=0,
                pod_count=0,
                service_count=0,
                deployment_count=0
            )
    
    def get_cluster_status(self, cluster_name: str) -> Optional[ClusterMetrics]:
        """
        Get current status of a cluster
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            ClusterMetrics: Current cluster metrics or None if not found
        """
        if cluster_name not in self.clusters:
            self.logger.warning(f"Cluster {cluster_name} not found")
            return None
        
        cluster_info = self.clusters[cluster_name]
        config = cluster_info['config']
        k8s_clients = cluster_info['k8s_clients']
        endpoint = cluster_info.get('endpoint')
        
        return self._collect_metrics(config, k8s_clients, endpoint)
    
    def scale_cluster(
        self,
        cluster_name: str,
        replicas: int
    ) -> bool:
        """
        Scale cluster deployment
        
        Args:
            cluster_name: Name of the cluster
            replicas: New number of replicas
            
        Returns:
            bool: Success status
        """
        if cluster_name not in self.clusters:
            self.logger.error(f"Cluster {cluster_name} not found")
            return False
        
        try:
            cluster_info = self.clusters[cluster_name]
            config = cluster_info['config']
            k8s_clients = cluster_info['k8s_clients']
            
            # Scale deployment
            k8s_clients['apps_v1'].patch_namespaced_deployment_scale(
                cluster_name,
                config.namespace,
                {"spec": {"replicas": replicas}}
            )
            
            self.logger.info(f"Scaled {cluster_name} to {replicas} replicas")
            
            self.log_manager.log_event(
                cluster_name,
                "cluster_scaled",
                f"Cluster scaled to {replicas} replicas"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to scale cluster: {e}")
            return False
    
    def delete_cluster(self, cluster_name: str) -> bool:
        """
        Delete a cluster deployment
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            bool: Success status
        """
        if cluster_name not in self.clusters:
            self.logger.error(f"Cluster {cluster_name} not found")
            return False
        
        try:
            cluster_info = self.clusters[cluster_name]
            config = cluster_info['config']
            k8s_clients = cluster_info['k8s_clients']
            
            # Delete service
            try:
                k8s_clients['core_v1'].delete_namespaced_service(
                    f"{cluster_name}-service",
                    config.namespace
                )
                self.logger.info(f"Deleted service: {cluster_name}-service")
            except ApiException:
                pass
            
            # Delete deployment
            try:
                k8s_clients['apps_v1'].delete_namespaced_deployment(
                    cluster_name,
                    config.namespace
                )
                self.logger.info(f"Deleted deployment: {cluster_name}")
            except ApiException:
                pass
            
            # Delete configmap
            try:
                k8s_clients['core_v1'].delete_namespaced_config_map(
                    f"{cluster_name}-config",
                    config.namespace
                )
            except ApiException:
                pass
            
            # Delete secret
            try:
                k8s_clients['core_v1'].delete_namespaced_secret(
                    f"{cluster_name}-secret",
                    config.namespace
                )
            except ApiException:
                pass
            
            # Remove from registry
            del self.clusters[cluster_name]
            
            self.log_manager.log_event(
                cluster_name,
                "cluster_deleted",
                f"Cluster deleted successfully"
            )
            
            self.logger.info(f"✓ Cluster {cluster_name} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete cluster: {e}")
            return False
    
    def list_clusters(self) -> List[Dict]:
        """
        List all managed clusters
        
        Returns:
            List[Dict]: List of cluster information
        """
        return [
            {
                "name": name,
                "provider": info['config'].cloud_provider.value,
                "namespace": info['config'].namespace,
                "endpoint": info.get('endpoint'),
                "deployment_id": info.get('deployment_id')
            }
            for name, info in self.clusters.items()
        ]
    
    def get_deployment_result(self, deployment_id: str) -> Optional[DeploymentResult]:
        """
        Get deployment result by ID
        
        Args:
            deployment_id: Deployment ID
            
        Returns:
            DeploymentResult: Deployment result or None if not found
        """
        return self.deployments.get(deployment_id)
    
    def get_pod_logs(
        self,
        cluster_name: str,
        pod_name: Optional[str] = None,
        tail_lines: int = 100
    ) -> Dict[str, str]:
        """
        Get logs from cluster pods
        
        Args:
            cluster_name: Name of the cluster
            pod_name: Specific pod name (optional)
            tail_lines: Number of lines to retrieve
            
        Returns:
            Dict[str, str]: Pod name to logs mapping
        """
        if cluster_name not in self.clusters:
            self.logger.error(f"Cluster {cluster_name} not found")
            return {}
        
        cluster_info = self.clusters[cluster_name]
        config = cluster_info['config']
        k8s_clients = cluster_info['k8s_clients']
        
        logs_dict = {}
        
        try:
            if pod_name:
                pods = [k8s_clients['core_v1'].read_namespaced_pod(pod_name, config.namespace)]
            else:
                pods = k8s_clients['core_v1'].list_namespaced_pod(
                    config.namespace,
                    label_selector=f"app={cluster_name}"
                ).items
            
            for pod in pods:
                try:
                    logs = k8s_clients['core_v1'].read_namespaced_pod_log(
                        pod.metadata.name,
                        config.namespace,
                        tail_lines=tail_lines
                    )
                    logs_dict[pod.metadata.name] = logs
                except Exception as e:
                    self.logger.error(f"Failed to get logs for pod {pod.metadata.name}: {e}")
            
            return logs_dict
            
        except Exception as e:
            self.logger.error(f"Failed to get pod logs: {e}")
            return {}
    
    def execute_in_pod(
        self,
        cluster_name: str,
        command: List[str],
        pod_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute command in a pod
        
        Args:
            cluster_name: Name of the cluster
            command: Command to execute
            pod_name: Specific pod name (optional, uses first pod if not specified)
            
        Returns:
            Dict[str, Any]: Execution result
        """
        if cluster_name not in self.clusters:
            return {"success": False, "error": f"Cluster {cluster_name} not found"}
        
        cluster_info = self.clusters[cluster_name]
        config = cluster_info['config']
        k8s_clients = cluster_info['k8s_clients']
        
        try:
            if not pod_name:
                # Get first pod
                pods = k8s_clients['core_v1'].list_namespaced_pod(
                    config.namespace,
                    label_selector=f"app={cluster_name}"
                ).items
                
                if not pods:
                    return {"success": False, "error": "No pods found"}
                
                pod_name = pods[0].metadata.name
            
            # Execute command
            from kubernetes.stream import stream
            
            resp = stream(
                k8s_clients['core_v1'].connect_get_namespaced_pod_exec,
                pod_name,
                config.namespace,
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            
            return {
                "success": True,
                "pod_name": pod_name,
                "output": resp
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute command in pod: {e}")
            return {"success": False, "error": str(e)}
    
    def export_cluster_config(self, cluster_name: str, output_file: str) -> bool:
        """
        Export cluster configuration to file
        
        Args:
            cluster_name: Name of the cluster
            output_file: Output file path
            
        Returns:
            bool: Success status
        """
        if cluster_name not in self.clusters:
            self.logger.error(f"Cluster {cluster_name} not found")
            return False
        
        try:
            cluster_info = self.clusters[cluster_name]
            config_dict = cluster_info['config'].to_dict()
            
            with open(output_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
            
            self.logger.info(f"Exported cluster config to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export config: {e}")
            return False
    
    def get_cluster_endpoint(self, cluster_name: str) -> Optional[str]:
        """
        Get cluster endpoint URL
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            Optional[str]: Endpoint URL or None if not found
        """
        if cluster_name in self.clusters:
            return self.clusters[cluster_name].get('endpoint')
        return None
    
    def health_check(self, cluster_name: str) -> Dict[str, Any]:
        """
        Perform health check on cluster
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            Dict[str, Any]: Health check results
        """
        if cluster_name not in self.clusters:
            return {"healthy": False, "error": f"Cluster {cluster_name} not found"}
        
        try:
            metrics = self.get_cluster_status(cluster_name)
            
            if not metrics:
                return {"healthy": False, "error": "Failed to get metrics"}
            
            healthy = (
                metrics.state == ClusterState.ACTIVE and
                metrics.ready_replicas == metrics.replicas and
                metrics.replicas > 0
            )
            
            return {
                "healthy": healthy,
                "state": metrics.state.value,
                "replicas": f"{metrics.ready_replicas}/{metrics.replicas}",
                "pods": metrics.pod_count,
                "endpoint": metrics.endpoint
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"healthy": False, "error": str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        self.git_manager.cleanup_workspace()
        self.log_manager.cleanup_old_logs()
        self.logger.info("Cleanup completed")


# ==================== Example Usage ====================

def example_usage():
    """Example usage of the Nexus Kubernetes Manager"""
    
    # Configure logging
    log_config = LogConfig(
        backend=LogBackend.LOCAL,
        local_path="/var/log/nexus-k8s",
        retention_days=90
    )
    
    # Initialize manager
    manager = NexusKubernetesManager(
        log_config=log_config,
        docker_registry=None,  # Use local registry or specify: "myregistry.azurecr.io"
        workspace_dir="/tmp/nexus-k8s-workspace"
    )
    
    # Configure Git source for binary
    binary_git_source = GitSourceConfig(
        provider=GitProvider.GITHUB,
        repo_url="git@github.com:myorg/my-nexus-binary.git",
        branch="main",
        tag="v1.0.0",
        subfolder="components/my-component",
        ssh_key_path="/path/to/ssh/key"
    )
    
    # Configure binary
    nexus_binary = NexusBinaryConfig(
        name="my-component",
        git_source=binary_git_source,
        target_path="/usr/bin/nexus",
        version_tag="v1.0.0",
        environment_variables={
            "COMPONENT_MODE": "production",
            "LOG_LEVEL": "INFO"
        }
    )
    
    # Configure Git source for auto-route project
    autoroute_git_source = GitSourceConfig(
        provider=GitProvider.GITLAB,
        repo_url="git@gitlab.com:myorg/auto-route-config.git",
        branch="main",
        ssh_key_path="/path/to/ssh/key"
    )
    
    # Configure auto-route project
    autoroute_project = AutoRouteProjectConfig(
        name="auto-route-config",
        git_source=autoroute_git_source,
        target_path="/home/nexus/auto-route",
        environment_variables={
            "ROUTE_CONFIG": "/home/nexus/auto-route/auto-route-config/config.yaml"
        }
    )
    
    # Create cluster configuration
    cluster_config = ClusterConfiguration(
        cluster_name="my-nexus-cluster",
        cloud_provider=CloudProvider.MINIKUBE,
        namespace="nexus-production",
        nexus_binaries=[nexus_binary],
        auto_route_projects=[autoroute_project],
        environment_variables={
            "CLUSTER_ENV": "production",
            "REGION": "us-east-1"
        },
        replicas=3,
        service_port=8080,
        service_type="LoadBalancer",
        cpu_limit="2000m",
        memory_limit="4Gi",
        labels={
            "app": "nexus",
            "env": "production"
        }
    )
    
    # Deploy cluster
    result = manager.create_cluster_deployment(
        config=cluster_config,
        kubeconfig_path="~/.kube/config"
    )
    
    # Check result
    if result.success:
        print(f"✓ Deployment successful!")
        print(f"  Cluster: {result.cluster_name}")
        print(f"  Endpoint: {result.endpoint}")
        print(f"  Pods: {', '.join(result.pod_names)}")
        
        # Get cluster status
        status = manager.get_cluster_status(result.cluster_name)
        print(f"\nCluster Status:")
        print(f"  State: {status.state.value}")
        print(f"  Replicas: {status.ready_replicas}/{status.replicas}")
        print(f"  Pods: {status.pod_count}")
        
        # Get pod logs
        logs = manager.get_pod_logs(result.cluster_name, tail_lines=50)
        for pod_name, pod_logs in logs.items():
            print(f"\nLogs from {pod_name}:")
            print(pod_logs[:500])  # First 500 chars
        
    else:
        print(f"✗ Deployment failed: {result.message}")
        for error in result.errors:
            print(f"  Error: {error}")


if __name__ == "__main__":
    example_usage()