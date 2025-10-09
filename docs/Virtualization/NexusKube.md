# Nexus Kubernetes Manager - Complete Documentation

**Version:** 2.0.0  
**Author:** Enterprise Team  
**License:** Enterprise

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Core Classes](#core-classes)
6. [API Reference](#api-reference)
7. [Configuration Guide](#configuration-guide)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Nexus Kubernetes Manager is an enterprise-grade solution for managing Kubernetes clusters with Git-integrated binary deployment across multiple cloud providers (AWS EKS, Azure AKS, GCP GKE, Minikube).

### Key Features

- **Multi-Cloud Support**: Deploy to AWS EKS, Azure AKS, GCP GKE, or Minikube
- **Git Integration**: Automatic binary and configuration deployment from GitHub/GitLab with SSH
- **Binary Management**: Deploy versioned binaries to `/usr/bin/nexus/`
- **Auto-Route Projects**: Deploy configuration projects to `/home/nexus/auto-route/`
- **Centralized Logging**: Support for local files, Elasticsearch, and CloudWatch
- **Health Monitoring**: Real-time cluster health and metrics
- **Docker Integration**: Automatic image building and deployment
- **Enterprise Security**: SSH key management, secrets, and encrypted configurations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Nexus Kubernetes Manager                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Git Repo   │  │  Git Repo    │  │   Docker     │     │
│  │   Manager    │  │   (Binary)   │  │   Builder    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                  ┌─────────▼─────────┐                      │
│                  │  Image Builder    │                      │
│                  └─────────┬─────────┘                      │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐             │
│         │                                      │             │
│  ┌──────▼───────┐                    ┌────────▼────────┐   │
│  │  Kubernetes  │                    │  Log Manager    │   │
│  │  Deployment  │◄───────────────────┤  (Local/ES/CW)  │   │
│  └──────────────┘                    └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐        ┌────▼────┐
   │  AWS    │         │  Azure  │        │  GCP    │
   │  EKS    │         │  AKS    │        │  GKE    │
   └─────────┘         └─────────┘        └─────────┘
```

---

## Installation

### Prerequisites

```bash
# Python 3.8+
python --version

# Kubernetes CLI
kubectl version --client

# Docker (for building images)
docker --version

# Git
git --version
```

### Install Dependencies

```bash
pip install kubernetes gitpython paramiko pyyaml requests elasticsearch \
            boto3 azure-mgmt-containerservice google-cloud-container docker
```

### Optional Dependencies

```bash
# For Elasticsearch logging
pip install elasticsearch

# For AWS CloudWatch logging
pip install boto3

# For Azure support
pip install azure-mgmt-containerservice azure-identity

# For GCP support
pip install google-cloud-container
```

---

## Quick Start

### Basic Example

```python
from nexus_k8s_manager import (
    NexusKubernetesManager,
    ClusterConfiguration,
    NexusBinaryConfig,
    AutoRouteProjectConfig,
    GitSourceConfig,
    GitProvider,
    CloudProvider,
    LogConfig
)

# Initialize manager
manager = NexusKubernetesManager(
    log_config=LogConfig(),
    workspace_dir="/tmp/nexus-workspace"
)

# Configure binary from Git
binary_git = GitSourceConfig(
    provider=GitProvider.GITHUB,
    repo_url="git@github.com:myorg/my-binary.git",
    branch="main",
    tag="v1.0.0",
    ssh_key_path="/path/to/ssh/key"
)

binary = NexusBinaryConfig(
    name="my-binary",
    git_source=binary_git,
    target_path="/usr/bin/nexus"
)

# Configure cluster
config = ClusterConfiguration(
    cluster_name="my-cluster",
    cloud_provider=CloudProvider.MINIKUBE,
    namespace="default",
    nexus_binaries=[binary],
    replicas=3,
    service_port=8080
)

# Deploy cluster
result = manager.create_cluster_deployment(config)

if result.success:
    print(f"Cluster deployed! Endpoint: {result.endpoint}")
else:
    print(f"Deployment failed: {result.message}")
```

---

## Core Classes

### 1. NexusKubernetesManager

**Main entry point for cluster management.**

#### Constructor

```python
NexusKubernetesManager(
    log_config: Optional[LogConfig] = None,
    docker_registry: Optional[str] = None,
    workspace_dir: str = "/tmp/nexus-k8s-workspace"
)
```

**Parameters:**
- `log_config`: Logging configuration (defaults to local logging)
- `docker_registry`: Docker registry URL (e.g., "myregistry.azurecr.io")
- `workspace_dir`: Working directory for Git operations

---

### 2. ClusterConfiguration

**Complete cluster configuration.**

#### Constructor

```python
ClusterConfiguration(
    cluster_name: str,
    cloud_provider: CloudProvider,
    namespace: str = "default",
    nexus_binaries: List[NexusBinaryConfig] = [],
    auto_route_projects: List[AutoRouteProjectConfig] = [],
    environment_variables: Dict[str, str] = {},
    secrets: Dict[str, str] = {},
    config_maps: Dict[str, str] = {},
    replicas: int = 3,
    cpu_limit: str = "1000m",
    memory_limit: str = "2Gi",
    cpu_request: str = "500m",
    memory_request: str = "1Gi",
    service_port: int = 8080,
    service_type: str = "LoadBalancer",
    health_check_path: str = "/health",
    docker_registry: Optional[str] = None,
    base_image: str = "ubuntu:22.04",
    labels: Dict[str, str] = {},
    annotations: Dict[str, str] = {}
)
```

---

### 3. GitSourceConfig

**Git repository source configuration.**

#### Constructor

```python
GitSourceConfig(
    provider: GitProvider,
    repo_url: str,
    branch: str = "main",
    tag: Optional[str] = None,
    commit_hash: Optional[str] = None,
    subfolder: Optional[str] = None,
    ssh_key_path: Optional[str] = None,
    ssh_key_content: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
)
```

**Parameters:**
- `provider`: Git provider (GitProvider.GITHUB, GitProvider.GITLAB, GitProvider.BITBUCKET)
- `repo_url`: SSH URL (e.g., "git@github.com:user/repo.git")
- `branch`: Branch name
- `tag`: Specific tag to checkout
- `commit_hash`: Specific commit to checkout
- `subfolder`: Path within repository (e.g., "components/my-component")
- `ssh_key_path`: Path to SSH private key
- `ssh_key_content`: SSH private key content as string

---

### 4. NexusBinaryConfig

**Configuration for binary artifacts.**

#### Constructor

```python
NexusBinaryConfig(
    name: str,
    git_source: GitSourceConfig,
    target_path: str = "/usr/bin/nexus",
    version_tag: Optional[str] = None,
    build_command: Optional[str] = None,
    binary_filename: Optional[str] = None,
    post_install_script: Optional[str] = None,
    environment_variables: Dict[str, str] = {}
)
```

**Parameters:**
- `name`: Binary name
- `git_source`: Git source configuration
- `target_path`: Target path in container (default: "/usr/bin/nexus")
- `build_command`: Command to build binary if source code
- `binary_filename`: Binary filename if different from name
- `environment_variables`: Binary-specific environment variables

---

### 5. AutoRouteProjectConfig

**Configuration for auto-route projects.**

#### Constructor

```python
AutoRouteProjectConfig(
    name: str,
    git_source: GitSourceConfig,
    target_path: str = "/home/nexus/auto-route",
    config_files: List[str] = [],
    environment_variables: Dict[str, str] = {},
    startup_script: Optional[str] = None
)
```

**Parameters:**
- `name`: Project name
- `git_source`: Git source configuration
- `target_path`: Target path in container (default: "/home/nexus/auto-route")
- `config_files`: List of configuration file paths
- `environment_variables`: Project-specific environment variables
- `startup_script`: Script to run on startup

---

### 6. LogConfig

**Logging backend configuration.**

#### Constructor

```python
LogConfig(
    backend: LogBackend = LogBackend.LOCAL,
    log_level: str = "INFO",
    local_path: str = "/var/log/nexus-k8s",
    elasticsearch_host: Optional[str] = None,
    elasticsearch_port: int = 9200,
    elasticsearch_index: str = "nexus-k8s-logs",
    cloudwatch_log_group: Optional[str] = None,
    cloudwatch_region: str = "us-east-1",
    retention_days: int = 90
)
```

---

## API Reference

### NexusKubernetesManager Methods

#### create_cluster_deployment()

Deploy a new Kubernetes cluster with Git-based binaries.

```python
def create_cluster_deployment(
    config: ClusterConfiguration,
    kubeconfig_path: Optional[str] = None,
    context: Optional[str] = None
) -> DeploymentResult
```

**Parameters:**
- `config`: Complete cluster configuration
- `kubeconfig_path`: Path to kubeconfig file (optional)
- `context`: Kubernetes context name (optional)

**Returns:**
- `DeploymentResult`: Deployment result with status, endpoint, and metrics

**Example:**
```python
result = manager.create_cluster_deployment(
    config=cluster_config,
    kubeconfig_path="~/.kube/config"
)

if result.success:
    print(f"Endpoint: {result.endpoint}")
    print(f"Pods: {result.pod_names}")
```

---

#### get_cluster_status()

Get current status and metrics of a cluster.

```python
def get_cluster_status(cluster_name: str) -> Optional[ClusterMetrics]
```

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:**
- `ClusterMetrics`: Current metrics or None if not found

**Example:**
```python
metrics = manager.get_cluster_status("my-cluster")
print(f"State: {metrics.state.value}")
print(f"Replicas: {metrics.ready_replicas}/{metrics.replicas}")
```

---

#### scale_cluster()

Scale cluster deployment to specified number of replicas.

```python
def scale_cluster(cluster_name: str, replicas: int) -> bool
```

**Parameters:**
- `cluster_name`: Name of the cluster
- `replicas`: New number of replicas

**Returns:**
- `bool`: Success status

**Example:**
```python
success = manager.scale_cluster("my-cluster", replicas=5)
```

---

#### delete_cluster()

Delete a cluster deployment and all associated resources.

```python
def delete_cluster(cluster_name: str) -> bool
```

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:**
- `bool`: Success status

**Example:**
```python
success = manager.delete_cluster("my-cluster")
```

---

#### list_clusters()

List all managed clusters.

```python
def list_clusters() -> List[Dict]
```

**Returns:**
- `List[Dict]`: List of cluster information dictionaries

**Example:**
```python
clusters = manager.list_clusters()
for cluster in clusters:
    print(f"{cluster['name']} - {cluster['provider']} - {cluster['endpoint']}")
```

---

#### get_pod_logs()

Retrieve logs from cluster pods.

```python
def get_pod_logs(
    cluster_name: str,
    pod_name: Optional[str] = None,
    tail_lines: int = 100
) -> Dict[str, str]
```

**Parameters:**
- `cluster_name`: Name of the cluster
- `pod_name`: Specific pod name (optional, retrieves all if not specified)
- `tail_lines`: Number of log lines to retrieve

**Returns:**
- `Dict[str, str]`: Mapping of pod names to their logs

**Example:**
```python
logs = manager.get_pod_logs("my-cluster", tail_lines=50)
for pod_name, pod_logs in logs.items():
    print(f"=== Logs from {pod_name} ===")
    print(pod_logs)
```

---

#### execute_in_pod()

Execute a command in a pod.

```python
def execute_in_pod(
    cluster_name: str,
    command: List[str],
    pod_name: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `cluster_name`: Name of the cluster
- `command`: Command to execute (list of strings)
- `pod_name`: Specific pod name (optional)

**Returns:**
- `Dict[str, Any]`: Execution result with success status and output

**Example:**
```python
result = manager.execute_in_pod(
    "my-cluster",
    command=["ls", "-la", "/usr/bin/nexus"]
)
if result['success']:
    print(result['output'])
```

---

#### health_check()

Perform health check on a cluster.

```python
def health_check(cluster_name: str) -> Dict[str, Any]
```

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:**
- `Dict[str, Any]`: Health check results

**Example:**
```python
health = manager.health_check("my-cluster")
print(f"Healthy: {health['healthy']}")
print(f"State: {health['state']}")
print(f"Replicas: {health['replicas']}")
```

---

#### get_cluster_endpoint()

Get the external endpoint URL for a cluster.

```python
def get_cluster_endpoint(cluster_name: str) -> Optional[str]
```

**Parameters:**
- `cluster_name`: Name of the cluster

**Returns:**
- `Optional[str]`: Endpoint URL or None

**Example:**
```python
endpoint = manager.get_cluster_endpoint("my-cluster")
print(f"Access cluster at: http://{endpoint}")
```

---

#### export_cluster_config()

Export cluster configuration to a YAML file.

```python
def export_cluster_config(cluster_name: str, output_file: str) -> bool
```

**Parameters:**
- `cluster_name`: Name of the cluster
- `output_file`: Output file path

**Returns:**
- `bool`: Success status

**Example:**
```python
manager.export_cluster_config("my-cluster", "my-cluster-config.yaml")
```

---

### NexusLogManager Methods

#### log_event()

Log a cluster event to all configured backends.

```python
def log_event(
    cluster_name: str,
    event_type: str,
    message: str,
    level: str = "INFO",
    metadata: Optional[Dict] = None
)
```

**Parameters:**
- `cluster_name`: Name of the cluster
- `event_type`: Type of event (e.g., "deployment_start", "scaling")
- `message`: Log message
- `level`: Log level (INFO, WARNING, ERROR, DEBUG)
- `metadata`: Additional metadata dictionary

**Example:**
```python
log_manager.log_event(
    "my-cluster",
    "custom_event",
    "Custom operation completed",
    level="INFO",
    metadata={"operation": "backup", "duration": 120}
)
```

---

#### query_logs()

Query logs with filters.

```python
def query_logs(
    cluster_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 1000
) -> List[Dict]
```

**Parameters:**
- `cluster_name`: Filter by cluster name
- `start_time`: Start time for query
- `end_time`: End time for query
- `event_type`: Filter by event type
- `level`: Filter by log level
- `limit`: Maximum number of results

**Returns:**
- `List[Dict]`: List of log entries

**Example:**
```python
from datetime import datetime, timedelta

logs = log_manager.query_logs(
    cluster_name="my-cluster",
    start_time=datetime.now() - timedelta(hours=24),
    level="ERROR",
    limit=100
)
```

---

#### export_logs()

Export logs to a file.

```python
def export_logs(
    output_file: str,
    cluster_name: Optional[str] = None,
    format: str = "json"
)
```

**Parameters:**
- `output_file`: Output file path
- `cluster_name`: Filter by cluster name
- `format`: Export format ("json" or "jsonl")

**Example:**
```python
log_manager.export_logs(
    "my-cluster-logs.json",
    cluster_name="my-cluster",
    format="json"
)
```

---

## Configuration Guide

### Complete Configuration Example

```python
from nexus_k8s_manager import *

# ==================== Git Configuration ====================

# Binary from GitHub
binary_git = GitSourceConfig(
    provider=GitProvider.GITHUB,
    repo_url="git@github.com:myorg/nexus-binaries.git",
    branch="main",
    tag="v2.1.0",
    subfolder="components/data-processor",
    ssh_key_path="/home/user/.ssh/id_rsa"
)

# Auto-route from GitLab
autoroute_git = GitSourceConfig(
    provider=GitProvider.GITLAB,
    repo_url="git@gitlab.com:myorg/route-configs.git",
    branch="production",
    ssh_key_content="""-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
...
-----END OPENSSH PRIVATE KEY-----"""
)

# ==================== Binary Configuration ====================

binary_config = NexusBinaryConfig(
    name="data-processor",
    git_source=binary_git,
    target_path="/usr/bin/nexus",
    version_tag="v2.1.0",
    binary_filename="processor",  # If different from name
    build_command="make build",  # If needs building
    environment_variables={
        "PROCESSOR_THREADS": "4",
        "BUFFER_SIZE": "1024"
    }
)

# ==================== Auto-Route Configuration ====================

autoroute_config = AutoRouteProjectConfig(
    name="route-configs",
    git_source=autoroute_git,
    target_path="/home/nexus/auto-route",
    config_files=["routes.yaml", "policies.json"],
    environment_variables={
        "ROUTE_CONFIG_PATH": "/home/nexus/auto-route/route-configs/routes.yaml"
    },
    startup_script="/home/nexus/auto-route/route-configs/init.sh"
)

# ==================== Cluster Configuration ====================

cluster_config = ClusterConfiguration(
    # Basic settings
    cluster_name="production-nexus-cluster",
    cloud_provider=CloudProvider.AWS_EKS,
    namespace="nexus-prod",
    
    # Git-based deployments
    nexus_binaries=[binary_config],
    auto_route_projects=[autoroute_config],
    
    # Environment and secrets
    environment_variables={
        "CLUSTER_ENV": "production",
        "REGION": "us-east-1",
        "LOG_LEVEL": "INFO"
    },
    secrets={
        "DB_PASSWORD": "my-secure-password",
        "API_KEY": "sk-1234567890"
    },
    config_maps={
        "app.properties": "max_connections=100\ntimeout=30",
        "features.json": '{"feature_a": true, "feature_b": false}'
    },
    
    # Resource configuration
    replicas=5,
    cpu_limit="2000m",
    memory_limit="4Gi",
    cpu_request="1000m",
    memory_request="2Gi",
    
    # Service configuration
    service_port=8080,
    service_type="LoadBalancer",
    expose_external=True,
    
    # Health checks
    health_check_path="/health",
    readiness_probe_path="/ready",
    liveness_probe_path="/health",
    
    # Docker configuration
    docker_registry="myregistry.azurecr.io",
    docker_image_tag="v2.1.0",
    base_image="ubuntu:22.04",
    
    # Labels and annotations
    labels={
        "app": "nexus",
        "env": "production",
        "team": "platform",
        "version": "v2.1.0"
    },
    annotations={
        "description": "Production Nexus cluster with data processor",
        "contact": "platform-team@company.com"
    }
)

# ==================== Logging Configuration ====================

# Local logging
local_log_config = LogConfig(
    backend=LogBackend.LOCAL,
    log_level="INFO",
    local_path="/var/log/nexus-k8s",
    retention_days=90
)

# Elasticsearch logging
es_log_config = LogConfig(
    backend=LogBackend.ELASTICSEARCH,
    log_level="DEBUG",
    elasticsearch_host="elasticsearch.company.com",
    elasticsearch_port=9200,
    elasticsearch_index="nexus-k8s-logs",
    elasticsearch_username="admin",
    elasticsearch_password="password",
    retention_days=180
)

# CloudWatch logging
cw_log_config = LogConfig(
    backend=LogBackend.CLOUDWATCH,
    log_level="INFO",
    cloudwatch_log_group="/aws/kubernetes/nexus",
    cloudwatch_stream="production-cluster",
    cloudwatch_region="us-east-1",
    retention_days=365
)

# ==================== Manager Initialization ====================

manager = NexusKubernetesManager(
    log_config=es_log_config,  # Choose logging backend
    docker_registry="myregistry.azurecr.io",
    workspace_dir="/tmp/nexus-workspace"
)

# ==================== Deploy Cluster ====================

result = manager.create_cluster_deployment(
    config=cluster_config,
    kubeconfig_path="~/.kube/config",
    context="production-cluster"
)
```

---

## Examples

### Example 1: Deploy to Minikube with GitHub Binary

```python
# Git source with SSH key
git_source = GitSourceConfig(
    provider=GitProvider.GITHUB,
    repo_url="git@github.com:mycompany/my-service.git",
    branch="main",
    tag="v1.0.0",
    ssh_key_path=os.path.expanduser("~/.ssh/id_rsa")
)

# Binary configuration
binary = NexusBinaryConfig(
    name="my-service",
    git_source=git_source,
    target_path="/usr/bin/nexus"
)

# Cluster configuration
config = ClusterConfiguration(
    cluster_name="minikube-test",
    cloud_provider=CloudProvider.MINIKUBE,
    namespace="default",
    nexus_binaries=[binary],
    replicas=2,
    service_port=8080,
    service_type="NodePort"
)

# Deploy
manager = NexusKubernetesManager()
result = manager.create_cluster_deployment(config)

if result.success:
    print(f"Success! Access at: {result.endpoint}")
```

---

### Example 2: Deploy with Multiple Binaries and Auto-Route

```python
# Binary 1: Data processor
processor_binary = NexusBinaryConfig(
    name="processor",
    git_source=GitSourceConfig(
        provider=GitProvider.GITHUB,
        repo_url="git@github.com:company/processor.git",
        branch="main",
        tag="v2.0.0",
        subfolder="build/linux",
        ssh_key_path="~/.ssh/github_key"
    ),
    environment_variables={"PROCESSOR_MODE": "production"}
)

# Binary 2: API server
api_binary = NexusBinaryConfig(
    name="api-server",
    git_source=GitSourceConfig(
        provider=GitProvider.GITLAB,
        repo_url="git@gitlab.com:company/api.git",
        branch="stable",
        ssh_key_path="~/.ssh/gitlab_key"
    ),
    build_command="go build -o api-server cmd/server/main.go",
    environment_variables={"API_PORT": "8080"}
)

# Auto-route project
autoroute = AutoRouteProjectConfig(
    name="routing-config",
    git_source=GitSourceConfig(
        provider=GitProvider.GITHUB,
        repo_url="git@github.com:company/configs.git",
        branch="production",
        ssh_key_path="~/.ssh/github_key"
    ),
    environment_variables={
        "CONFIG_PATH": "/home/nexus/auto-route/routing-config/routes.yaml"
    }
)

# Create cluster with multiple components
config = ClusterConfiguration(
    cluster_name="multi-component-cluster",
    cloud_provider=CloudProvider.AWS_EKS,
    namespace="production",
    nexus_binaries=[processor_binary, api_binary],
    auto_route_projects=[autoroute],
    environment_variables={
        "ENV": "production",
        "LOG_LEVEL": "info"
    },
    replicas=3,
    service_port=8080
)

manager = NexusKubernetesManager(
    docker_registry="123456789.dkr.ecr.us-east-1.amazonaws.com"
)
result = manager.create_cluster_deployment(config)
```

---

### Example 3: Managing Cluster Lifecycle

```python
manager = NexusKubernetesManager()

# Deploy cluster
result = manager.create_cluster_deployment(config)
cluster_name = result.cluster_name

# Check health
health = manager.health_check(cluster_name)
print(f"Healthy: {health['healthy']}")

# Scale up
manager.scale_cluster(cluster_name, replicas=10)

# Get logs
logs = manager.get_pod_logs(cluster_name, tail_lines=100)
for pod, log_content in logs.items():
    print(f"=== {pod} ===\n{log_content}\n")

# Execute command
exec_result = manager.execute_in_pod(
    cluster_name,
    command=["cat", "/usr/bin/nexus/config.yaml"]
)
print(exec_result['output'])

# Get metrics
metrics = manager.get_cluster_status(cluster_name)
print(f"Pods: {metrics.pod_count}")
print(f"Ready: {metrics.ready_replicas}/{metrics.replicas}")

# Export configuration
manager.export_cluster_config(cluster_name, "backup-config.yaml")

# Delete cluster
manager.delete_cluster(cluster_name)
```

---

### Example 4: Advanced Logging and Monitoring

```python
from datetime import datetime, timedelta

# Configure Elasticsearch logging
log_config = LogConfig(
    backend=LogBackend.ELASTICSEARCH,
    elasticsearch_host="logs.company.com",
    elasticsearch_port=9200,
    elasticsearch_index="nexus-clusters",
    retention_days=90
)

manager = NexusKubernetesManager(log_config=log_config)

# Deploy cluster
result = manager.create_cluster_deployment(config)

# Query logs
recent_errors = manager.log_manager.query_logs(
    cluster_name=result.cluster_name,
    start_time=datetime.now() - timedelta(hours=1),
    level="ERROR",
    limit=50
)

for log_entry in recent_errors:
    print(f"[{log_entry['timestamp']}] {log_entry['message']}")

# Export logs
manager.log_manager.export_logs(
    "cluster-logs.json",
    cluster_name=result.cluster_name
)

# Collect pod logs
manager.log_manager.collect_pod_logs(
    result.cluster_name,
    result.namespace,
    k8s_client=manager.clusters[result.cluster_name]['k8s_clients']['core_v1'],
    label_selector=f"app={result.cluster_name}",
    tail_lines=200
)
```

---

### Example 5: Using with FastAPI Auto-Router

```python
# Integration with your existing auto-router framework
from fastapi import FastAPI
from nexus_k8s_manager import NexusKubernetesManager, ClusterConfiguration

app = FastAPI()
manager = NexusKubernetesManager()

class KubernetesClusterManager:
    """Integrate with your framework's auto-router"""
    
    def __init__(self):
        self.k8s_manager = NexusKubernetesManager()
    
    @staticmethod
    def _is_public():
        """Decorator flag for auto-router"""
        return True
    
    def create_cluster(
        self,
        cluster_name: str,
        repo_url: str,
        binary_name: str,
        branch: str = "main",
        tag: str = None,
        subfolder: str = None,
        ssh_key_path: str = None,
        replicas: int = 3,
        service_port: int = 8080
    ):
        """Create cluster endpoint for auto-router"""
        
        # Configure from parameters
        git_source = GitSourceConfig(
            provider=GitProvider.GITHUB,
            repo_url=repo_url,
            branch=branch,
            tag=tag,
            subfolder=subfolder,
            ssh_key_path=ssh_key_path
        )
        
        binary = NexusBinaryConfig(
            name=binary_name,
            git_source=git_source
        )
        
        config = ClusterConfiguration(
            cluster_name=cluster_name,
            cloud_provider=CloudProvider.MINIKUBE,
            namespace="default",
            nexus_binaries=[binary],
            replicas=replicas,
            service_port=service_port
        )
        
        # Deploy
        result = self.k8s_manager.create_cluster_deployment(config)
        
        return {
            "success": result.success,
            "cluster_name": result.cluster_name,
            "endpoint": result.endpoint,
            "deployment_id": result.deployment_id,
            "message": result.message
        }
    
    def get_cluster_status(self, cluster_name: str):
        """Get cluster status endpoint"""
        metrics = self.k8s_manager.get_cluster_status(cluster_name)
        
        if not metrics:
            return {"error": "Cluster not found"}
        
        return metrics.to_dict()
    
    def delete_cluster(self, cluster_name: str):
        """Delete cluster endpoint"""
        success = self.k8s_manager.delete_cluster(cluster_name)
        return {"success": success, "cluster_name": cluster_name}

# Mark methods as public for auto-router
KubernetesClusterManager.create_cluster._is_public = True
KubernetesClusterManager.get_cluster_status._is_public = True
KubernetesClusterManager.delete_cluster._is_public = True
```

---

## Best Practices

### 1. SSH Key Management

```python
# ✓ GOOD: Use SSH key files
git_source = GitSourceConfig(
    repo_url="git@github.com:company/repo.git",
    ssh_key_path=os.path.expanduser("~/.ssh/id_rsa")
)

# ✓ GOOD: Use SSH key content from secure storage
ssh_key = get_from_secure_vault("github_ssh_key")
git_source = GitSourceConfig(
    repo_url="git@github.com:company/repo.git",
    ssh_key_content=ssh_key
)

# ✗ BAD: Hardcode SSH keys
git_source = GitSourceConfig(
    ssh_key_content="-----BEGIN OPENSSH PRIVATE KEY-----\n..."
)
```

### 2. Resource Management

```python
# ✓ GOOD: Specify resource limits
config = ClusterConfiguration(
    cpu_limit="2000m",
    memory_limit="4Gi",
    cpu_request="1000m",
    memory_request="2Gi"
)

# ✗ BAD: Use defaults without consideration
config = ClusterConfiguration()  # May cause resource issues
```

### 3. Error Handling

```python
# ✓ GOOD: Check deployment results
result = manager.create_cluster_deployment(config)
if result.success:
    logger.info(f"Deployed: {result.endpoint}")
else:
    logger.error(f"Failed: {result.message}")
    for error in result.errors:
        logger.error(f"  - {error}")

# ✗ BAD: Assume success
result = manager.create_cluster_deployment(config)
print(result.endpoint)  # May be None
```

### 4. Logging Configuration

```python
# ✓ GOOD: Configure appropriate retention
log_config = LogConfig(
    backend=LogBackend.ELASTICSEARCH,
    retention_days=90,
    max_log_size_mb=1024
)

# ✓ GOOD: Use structured logging
manager.log_manager.log_event(
    cluster_name="my-cluster",
    event_type="scaling",
    message="Scaled cluster",
    metadata={"old_replicas": 3, "new_replicas": 5}
)
```

### 5. Cleanup

```python
# ✓ GOOD: Always cleanup
try:
    result = manager.create_cluster_deployment(config)
finally:
    manager.cleanup()

# ✓ GOOD: Use context manager pattern
class ClusterContext:
    def __init__(self, manager, config):
        self.manager = manager
        self.config = config
        self.result = None
    
    def __enter__(self):
        self.result = self.manager.create_cluster_deployment(self.config)
        return self.result
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.cleanup()
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. SSH Authentication Failures

**Problem:** `Failed to clone repository: Permission denied (publickey)`

**Solutions:**
```python
# Check SSH key permissions
import os
os.chmod(ssh_key_path, 0o600)

# Verify SSH key format
with open(ssh_key_path) as f:
    key_content = f.read()
    assert key_content.startswith("-----BEGIN")

# Test SSH connection manually
# ssh -i ~/.ssh/id_rsa git@github.com
```

#### 2. Docker Build Failures

**Problem:** `Docker build failed: Cannot connect to Docker daemon`

**Solutions:**
```bash
# Check Docker service
sudo systemctl status docker
sudo systemctl start docker

# Check Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker installation
docker version
```

#### 3. Kubernetes Connection Issues

**Problem:** `Failed to connect to Kubernetes: Config not found`

**Solutions:**
```python
# Specify kubeconfig explicitly
result = manager.create_cluster_deployment(
    config,
    kubeconfig_path=os.path.expanduser("~/.kube/config")
)

# Check kubeconfig
kubectl config view
kubectl cluster-info

# Use specific context
result = manager.create_cluster_deployment(
    config,
    context="minikube"
)
```

#### 4. Binary Not Found

**Problem:** `Binary not found and could not be built`

**Solutions:**
```python
# Specify correct subfolder
git_source = GitSourceConfig(
    repo_url="git@github.com:company/repo.git",
    subfolder="build/linux/amd64"  # Correct path
)

# Provide build command
binary = NexusBinaryConfig(
    name="my-binary",
    git_source=git_source,
    build_command="make build && cp bin/my-binary ."
)

# Specify binary filename if different
binary = NexusBinaryConfig(
    name="my-service",
    binary_filename="my-service-linux-amd64"
)
```

#### 5. Pod Startup Failures

**Problem:** Pods are in CrashLoopBackOff

**Debug steps:**
```python
# Get pod logs
logs = manager.get_pod_logs("my-cluster")
for pod, log in logs.items():
    print(f"=== {pod} ===\n{log}")

# Check pod status
metrics = manager.get_cluster_status("my-cluster")
print(f"Ready: {metrics.ready_replicas}/{metrics.replicas}")

# Execute debug command
result = manager.execute_in_pod(
    "my-cluster",
    command=["ls", "-la", "/usr/bin/nexus"]
)

# Check health endpoint
health = manager.health_check("my-cluster")
print(health)
```

#### 6. Service Endpoint Not Available

**Problem:** `endpoint` is None after deployment

**Solutions:**
```python
# For LoadBalancer, wait longer
import time
result = manager.create_cluster_deployment(config)
if not result.endpoint:
    time.sleep(60)  # Wait for external IP
    endpoint = manager.get_cluster_endpoint(result.cluster_name)

# Use NodePort for testing
config = ClusterConfiguration(
    service_type="NodePort",  # Instead of LoadBalancer
    ...
)

# For Minikube, use minikube service
# minikube service my-cluster-service --url
```

---

## Performance Optimization

### 1. Git Clone Optimization

```python
# Use shallow clone for large repositories
git_source = GitSourceConfig(
    repo_url="git@github.com:company/large-repo.git",
    branch="main",
    # Shallow clone is automatic when no tag/commit specified
)

# Clone specific tag only
git_source = GitSourceConfig(
    repo_url="git@github.com:company/repo.git",
    tag="v1.0.0",  # Only fetches this tag
)
```

### 2. Docker Build Optimization

```python
# Use build cache
config = ClusterConfiguration(
    base_image="ubuntu:22.04",  # Use cached base image
    docker_registry="myregistry.io",  # Push for reuse
    ...
)

# Multi-stage builds (in custom Dockerfile)
# FROM golang:1.20 AS builder
# ...
# FROM ubuntu:22.04
# COPY --from=builder /app/binary /usr/bin/nexus/
```

### 3. Parallel Operations

```python
from concurrent.futures import ThreadPoolExecutor

def deploy_cluster(config):
    manager = NexusKubernetesManager()
    return manager.create_cluster_deployment(config)

# Deploy multiple clusters in parallel
configs = [config1, config2, config3]
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(deploy_cluster, configs))
```

---

## Security Considerations

### 1. Secrets Management

```python
# ✓ Use Kubernetes secrets
config = ClusterConfiguration(
    secrets={
        "DB_PASSWORD": get_from_vault("db_password"),
        "API_KEY": get_from_vault("api_key")
    }
)

# ✓ Encrypt sensitive data
from cryptography.fernet import Fernet
cipher = Fernet(encryption_key)
encrypted_password = cipher.encrypt(b"password").decode()
```

### 2. RBAC Configuration

```python
# Create service account with limited permissions
# kubectl create serviceaccount nexus-deployer
# kubectl create rolebinding nexus-deployer-binding \
#   --clusterrole=edit --serviceaccount=default:nexus-deployer
```

### 3. Network Policies

```python
# Apply network policies for pod-to-pod communication
config = ClusterConfiguration(
    annotations={
        "network-policy": "restricted"
    }
)
```

---

## API Integration Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
manager = NexusKubernetesManager()

class DeploymentRequest(BaseModel):
    cluster_name: str
    repo_url: str
    binary_name: str
    branch: str = "main"
    tag: Optional[str] = None
    replicas: int = 3
    service_port: int = 8080

@app.post("/api/v1/clusters/deploy")
async def deploy_cluster(request: DeploymentRequest):
    """Deploy a new cluster"""
    
    git_source = GitSourceConfig(
        provider=GitProvider.GITHUB,
        repo_url=request.repo_url,
        branch=request.branch,
        tag=request.tag,
        ssh_key_path=os.getenv("SSH_KEY_PATH")
    )
    
    binary = NexusBinaryConfig(
        name=request.binary_name,
        git_source=git_source
    )
    
    config = ClusterConfiguration(
        cluster_name=request.cluster_name,
        cloud_provider=CloudProvider.MINIKUBE,
        namespace="default",
        nexus_binaries=[binary],
        replicas=request.replicas,
        service_port=request.service_port
    )
    
    result = manager.create_cluster_deployment(config)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return result.to_dict()

@app.get("/api/v1/clusters/{cluster_name}/status")
async def get_status(cluster_name: str):
    """Get cluster status"""
    metrics = manager.get_cluster_status(cluster_name)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return metrics.to_dict()

@app.delete("/api/v1/clusters/{cluster_name}")
async def delete_cluster(cluster_name: str):
    """Delete a cluster"""
    success = manager.delete_cluster(cluster_name)
    
    if not success:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    return {"success": True, "cluster_name": cluster_name}
```

---

## License

Enterprise License - All Rights Reserved

---

## Support

For support and questions:
- Email: platform-team@company.com
- Documentation: https://docs.company.com/nexus-k8s
- Issues: https://github.com/company/nexus-k8s-manager/issues

---

**Last Updated:** 2024-01-08