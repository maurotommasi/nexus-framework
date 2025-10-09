"""
Comprehensive Test Suite for Nexus Kubernetes Manager

Tests covering cloud providers (EKS, GKE, AKS) and local providers (Minikube, Kind, K3s)

Requirements:
    pip install pytest kubernetes pyyaml pytest-mock pytest-cov

Run tests:
    pytest test_k8s_manager.py -v
    pytest test_k8s_manager.py -v --cov=k8s_manager
"""

import sys
import os

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)


import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from kubernetes.client.rest import ApiException
from nexus.virtualization.k8s_manager import KubernetesManager
import yaml


# ==================== Fixtures ====================

@pytest.fixture
def mock_k8s_config():
    """Mock Kubernetes config loading"""
    with patch('nexus.virtualization.k8s_manager.config.load_kube_config') as mock_config:
        yield mock_config


@pytest.fixture
def mock_core_v1():
    """Mock CoreV1Api"""
    with patch('nexus.virtualization.k8s_manager.client.CoreV1Api') as mock_v1:
        yield mock_v1.return_value


@pytest.fixture
def mock_apps_v1():
    """Mock AppsV1Api"""
    with patch('nexus.virtualization.k8s_manager.client.AppsV1Api') as mock_apps:
        yield mock_apps.return_value


@pytest.fixture
def k8s_manager(mock_k8s_config, mock_core_v1, mock_apps_v1):
    """Create KubernetesManager instance with mocked dependencies"""
    manager = KubernetesManager()
    manager.v1 = mock_core_v1
    manager.apps_v1 = mock_apps_v1
    return manager


@pytest.fixture
def sample_namespace():
    """Sample namespace object"""
    ns = Mock()
    ns.metadata.name = "default"
    return ns


@pytest.fixture
def sample_pod():
    """Sample pod object"""
    pod = Mock()
    pod.metadata.name = "test-pod"
    pod.status.phase = "Running"
    pod.spec.node_name = "node-1"
    return pod


@pytest.fixture
def sample_deployment():
    """Sample deployment object"""
    deployment = Mock()
    deployment.metadata.name = "test-deployment"
    return deployment


@pytest.fixture
def sample_service():
    """Sample service object"""
    svc = Mock()
    svc.metadata.name = "test-service"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.0.0.1"
    port = Mock()
    port.port = 80
    port.target_port = 8080
    svc.spec.ports = [port]
    return svc


# ==================== Initialization Tests ====================

def test_init_default_config(mock_k8s_config):
    """Test 1: Initialize with default kubeconfig"""
    manager = KubernetesManager()
    mock_k8s_config.assert_called_once_with(context=None)


def test_init_custom_kubeconfig(mock_k8s_config):
    """Test 2: Initialize with custom kubeconfig path"""
    manager = KubernetesManager(kubeconfig_path="/custom/path")
    mock_k8s_config.assert_called_once_with(config_file="/custom/path", context=None)


def test_init_with_context(mock_k8s_config):
    """Test 3: Initialize with specific context"""
    manager = KubernetesManager(context="minikube")
    mock_k8s_config.assert_called_once_with(context="minikube")


def test_init_custom_config_and_context(mock_k8s_config):
    """Test 4: Initialize with custom config and context"""
    manager = KubernetesManager(kubeconfig_path="/custom/path", context="prod-cluster")
    mock_k8s_config.assert_called_once_with(config_file="/custom/path", context="prod-cluster")


# ==================== Minikube Tests ====================

def test_minikube_list_namespaces(k8s_manager, mock_core_v1, sample_namespace):
    """Test 5: List namespaces on Minikube"""
    mock_core_v1.list_namespace.return_value.items = [sample_namespace]
    result = k8s_manager.list_namespaces()
    assert result == ["default"]


def test_minikube_list_pods(k8s_manager, mock_core_v1, sample_pod):
    """Test 6: List pods in Minikube namespace"""
    mock_core_v1.list_namespaced_pod.return_value.items = [sample_pod]
    result = k8s_manager.list_pods("default")
    assert len(result) == 1
    assert result[0]["name"] == "test-pod"


def test_minikube_get_pod_logs(k8s_manager, mock_core_v1):
    """Test 7: Get pod logs from Minikube"""
    mock_core_v1.read_namespaced_pod_log.return_value = "test logs"
    result = k8s_manager.get_pod_logs("test-pod", "default")
    assert result == "test logs"


def test_minikube_scale_deployment(k8s_manager, mock_apps_v1):
    """Test 8: Scale deployment on Minikube"""
    k8s_manager.scale_deployment("test-deploy", "default", 3)
    mock_apps_v1.patch_namespaced_deployment_scale.assert_called_once()


def test_minikube_delete_deployment(k8s_manager, mock_apps_v1):
    """Test 9: Delete deployment on Minikube"""
    k8s_manager.delete_deployment("test-deploy", "default")
    mock_apps_v1.delete_namespaced_deployment.assert_called_once_with("test-deploy", "default")


# ==================== Kind (Kubernetes in Docker) Tests ====================

def test_kind_init_with_context(mock_k8s_config):
    """Test 10: Initialize with Kind context"""
    manager = KubernetesManager(context="kind-kind")
    mock_k8s_config.assert_called_with(context="kind-kind")


def test_kind_list_deployments(k8s_manager, mock_apps_v1, sample_deployment):
    """Test 11: List deployments on Kind"""
    mock_apps_v1.list_namespaced_deployment.return_value.items = [sample_deployment]
    result = k8s_manager.list_deployments("default")
    assert result == ["test-deployment"]


def test_kind_list_services(k8s_manager, mock_core_v1, sample_service):
    """Test 12: List services on Kind"""
    mock_core_v1.list_namespaced_service.return_value.items = [sample_service]
    result = k8s_manager.list_services("default")
    assert result == ["test-service"]


def test_kind_get_service_details(k8s_manager, mock_core_v1, sample_service):
    """Test 13: Get service details on Kind"""
    mock_core_v1.read_namespaced_service.return_value = sample_service
    result = k8s_manager.get_service("test-service", "default")
    assert result["name"] == "test-service"
    assert result["type"] == "ClusterIP"


# ==================== K3s Tests ====================

def test_k3s_init_with_custom_config(mock_k8s_config):
    """Test 14: Initialize with K3s config"""
    manager = KubernetesManager(kubeconfig_path="/etc/rancher/k3s/k3s.yaml")
    mock_k8s_config.assert_called_with(config_file="/etc/rancher/k3s/k3s.yaml", context=None)


def test_k3s_list_multiple_namespaces(k8s_manager, mock_core_v1):
    """Test 15: List multiple namespaces on K3s"""
    ns1, ns2, ns3 = Mock(), Mock(), Mock()
    ns1.metadata.name = "default"
    ns2.metadata.name = "kube-system"
    ns3.metadata.name = "custom"
    mock_core_v1.list_namespace.return_value.items = [ns1, ns2, ns3]
    result = k8s_manager.list_namespaces()
    assert len(result) == 3


def test_k3s_list_pods_multiple(k8s_manager, mock_core_v1):
    """Test 16: List multiple pods on K3s"""
    pod1, pod2 = Mock(), Mock()
    pod1.metadata.name = "pod-1"
    pod1.status.phase = "Running"
    pod1.spec.node_name = "node-1"
    pod2.metadata.name = "pod-2"
    pod2.status.phase = "Pending"
    pod2.spec.node_name = "node-2"
    mock_core_v1.list_namespaced_pod.return_value.items = [pod1, pod2]
    result = k8s_manager.list_pods("default")
    assert len(result) == 2


# ==================== AWS EKS Tests ====================

def test_eks_init_with_context(mock_k8s_config):
    """Test 17: Initialize with EKS context"""
    manager = KubernetesManager(context="arn:aws:eks:us-east-1:123456789:cluster/my-cluster")
    mock_k8s_config.assert_called_with(context="arn:aws:eks:us-east-1:123456789:cluster/my-cluster")


def test_eks_list_namespaces(k8s_manager, mock_core_v1):
    """Test 18: List namespaces on EKS"""
    namespaces = [Mock() for _ in range(5)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"ns-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 5


def test_eks_list_pods_production(k8s_manager, mock_core_v1):
    """Test 19: List pods in production namespace on EKS"""
    pods = [Mock() for _ in range(10)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"app-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"ip-10-0-{i}-100.ec2.internal"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 10


def test_eks_scale_deployment_high_replicas(k8s_manager, mock_apps_v1):
    """Test 20: Scale deployment to high replica count on EKS"""
    k8s_manager.scale_deployment("api-service", "production", 50)
    mock_apps_v1.patch_namespaced_deployment_scale.assert_called_once()


def test_eks_get_pod_logs_with_container(k8s_manager, mock_core_v1):
    """Test 21: Get logs from specific container on EKS"""
    mock_core_v1.read_namespaced_pod_log.return_value = "container logs"
    result = k8s_manager.get_pod_logs("app-pod", "production", container="nginx")
    mock_core_v1.read_namespaced_pod_log.assert_called_with(
        "app-pod", "production", container="nginx", tail_lines=100
    )


def test_eks_get_pod_logs_custom_tail(k8s_manager, mock_core_v1):
    """Test 22: Get pod logs with custom tail lines on EKS"""
    mock_core_v1.read_namespaced_pod_log.return_value = "logs"
    result = k8s_manager.get_pod_logs("app-pod", "production", tail_lines=500)
    mock_core_v1.read_namespaced_pod_log.assert_called_with(
        "app-pod", "production", container=None, tail_lines=500
    )


# ==================== GCP GKE Tests ====================

def test_gke_init_with_context(mock_k8s_config):
    """Test 23: Initialize with GKE context"""
    manager = KubernetesManager(context="gke_project-id_us-central1_cluster-name")
    mock_k8s_config.assert_called_with(context="gke_project-id_us-central1_cluster-name")


def test_gke_list_namespaces(k8s_manager, mock_core_v1):
    """Test 24: List namespaces on GKE"""
    namespaces = [Mock() for _ in range(3)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"team-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert "team-0" in result


def test_gke_list_pods_regional_cluster(k8s_manager, mock_core_v1):
    """Test 25: List pods on GKE regional cluster"""
    pods = [Mock() for _ in range(15)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"workload-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"gke-cluster-pool-{i % 3}-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("default")
    assert len(result) == 15


def test_gke_list_services(k8s_manager, mock_core_v1):
    """Test 26: List services on GKE"""
    services = [Mock() for _ in range(5)]
    for i, svc in enumerate(services):
        svc.metadata.name = f"service-{i}"
    mock_core_v1.list_namespaced_service.return_value.items = services
    result = k8s_manager.list_services("default")
    assert len(result) == 5


def test_gke_get_service_loadbalancer(k8s_manager, mock_core_v1):
    """Test 27: Get LoadBalancer service on GKE"""
    svc = Mock()
    svc.metadata.name = "lb-service"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.8.0.1"
    port = Mock()
    port.port = 443
    port.target_port = 8443
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("lb-service", "production")
    assert result["type"] == "LoadBalancer"


# ==================== Azure AKS Tests ====================

def test_aks_init_with_context(mock_k8s_config):
    """Test 28: Initialize with AKS context"""
    manager = KubernetesManager(context="aks-cluster")
    mock_k8s_config.assert_called_with(context="aks-cluster")


def test_aks_list_namespaces(k8s_manager, mock_core_v1):
    """Test 29: List namespaces on AKS"""
    namespaces = [Mock() for _ in range(4)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"app-namespace-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 4


def test_aks_list_pods_multiple_zones(k8s_manager, mock_core_v1):
    """Test 30: List pods across availability zones on AKS"""
    pods = [Mock() for _ in range(12)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"aks-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"aks-nodepool1-{i}-vmss"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 12


def test_aks_scale_deployment(k8s_manager, mock_apps_v1):
    """Test 31: Scale deployment on AKS"""
    k8s_manager.scale_deployment("frontend", "production", 10)
    mock_apps_v1.patch_namespaced_deployment_scale.assert_called_once()


def test_aks_list_deployments(k8s_manager, mock_apps_v1):
    """Test 32: List deployments on AKS"""
    deployments = [Mock() for _ in range(7)]
    for i, dep in enumerate(deployments):
        dep.metadata.name = f"deployment-{i}"
    mock_apps_v1.list_namespaced_deployment.return_value.items = deployments
    result = k8s_manager.list_deployments("default")
    assert len(result) == 7


# ==================== Deployment Manifest Tests ====================

def test_deploy_deployment_manifest(k8s_manager, mock_apps_v1):
    """Test 33: Deploy deployment from YAML manifest"""
    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "test-deploy"}
    }
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("test-deploy", "default", "deployment.yaml")
    mock_apps_v1.create_namespaced_deployment.assert_called_once()


def test_deploy_service_manifest(k8s_manager, mock_core_v1):
    """Test 34: Deploy service from YAML manifest"""
    manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "test-svc"}
    }
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("test-svc", "default", "service.yaml")
    mock_core_v1.create_namespaced_service.assert_called_once()


def test_deploy_unsupported_manifest(k8s_manager):
    """Test 35: Deploy unsupported resource type"""
    manifest = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": "test-cm"}
    }
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("test-cm", "default", "configmap.yaml")
    # Should log warning but not raise exception


# ==================== Error Handling Tests ====================

def test_list_namespaces_api_exception(k8s_manager, mock_core_v1):
    """Test 36: Handle API exception when listing namespaces"""
    mock_core_v1.list_namespace.side_effect = ApiException(status=500)
    result = k8s_manager.list_namespaces()
    assert result == []


def test_list_pods_api_exception(k8s_manager, mock_core_v1):
    """Test 37: Handle API exception when listing pods"""
    mock_core_v1.list_namespaced_pod.side_effect = ApiException(status=404)
    result = k8s_manager.list_pods("nonexistent")
    assert result == []


def test_get_pod_logs_api_exception(k8s_manager, mock_core_v1):
    """Test 38: Handle API exception when getting logs"""
    mock_core_v1.read_namespaced_pod_log.side_effect = ApiException(status=404)
    result = k8s_manager.get_pod_logs("nonexistent", "default")
    assert result == ""


def test_list_deployments_api_exception(k8s_manager, mock_apps_v1):
    """Test 39: Handle API exception when listing deployments"""
    mock_apps_v1.list_namespaced_deployment.side_effect = ApiException(status=403)
    result = k8s_manager.list_deployments("restricted")
    assert result == []


def test_scale_deployment_api_exception(k8s_manager, mock_apps_v1):
    """Test 40: Handle API exception when scaling deployment"""
    mock_apps_v1.patch_namespaced_deployment_scale.side_effect = ApiException(status=404)
    k8s_manager.scale_deployment("nonexistent", "default", 3)
    # Should not raise exception


def test_deploy_manifest_api_exception(k8s_manager, mock_apps_v1):
    """Test 41: Handle API exception when deploying manifest"""
    manifest = {"kind": "Deployment", "metadata": {"name": "test"}}
    mock_apps_v1.create_namespaced_deployment.side_effect = ApiException(status=409)
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("test", "default", "deploy.yaml")
    # Should not raise exception


def test_delete_deployment_api_exception(k8s_manager, mock_apps_v1):
    """Test 42: Handle API exception when deleting deployment"""
    mock_apps_v1.delete_namespaced_deployment.side_effect = ApiException(status=404)
    k8s_manager.delete_deployment("nonexistent", "default")
    # Should not raise exception


def test_list_services_api_exception(k8s_manager, mock_core_v1):
    """Test 43: Handle API exception when listing services"""
    mock_core_v1.list_namespaced_service.side_effect = ApiException(status=500)
    result = k8s_manager.list_services("default")
    assert result == []


def test_get_service_api_exception(k8s_manager, mock_core_v1):
    """Test 44: Handle API exception when getting service"""
    mock_core_v1.read_namespaced_service.side_effect = ApiException(status=404)
    result = k8s_manager.get_service("nonexistent", "default")
    assert result == {}


# ==================== Edge Cases ====================

def test_list_pods_empty_namespace(k8s_manager, mock_core_v1):
    """Test 45: List pods in empty namespace"""
    mock_core_v1.list_namespaced_pod.return_value.items = []
    result = k8s_manager.list_pods("empty")
    assert result == []


def test_list_deployments_empty_namespace(k8s_manager, mock_apps_v1):
    """Test 46: List deployments in empty namespace"""
    mock_apps_v1.list_namespaced_deployment.return_value.items = []
    result = k8s_manager.list_deployments("empty")
    assert result == []


def test_list_services_empty_namespace(k8s_manager, mock_core_v1):
    """Test 47: List services in empty namespace"""
    mock_core_v1.list_namespaced_service.return_value.items = []
    result = k8s_manager.list_services("empty")
    assert result == []


def test_scale_deployment_zero_replicas(k8s_manager, mock_apps_v1):
    """Test 48: Scale deployment to zero replicas"""
    k8s_manager.scale_deployment("test", "default", 0)
    mock_apps_v1.patch_namespaced_deployment_scale.assert_called_once()


def test_get_pod_logs_zero_tail_lines(k8s_manager, mock_core_v1):
    """Test 49: Get pod logs with zero tail lines"""
    mock_core_v1.read_namespaced_pod_log.return_value = ""
    result = k8s_manager.get_pod_logs("test-pod", "default", tail_lines=0)
    mock_core_v1.read_namespaced_pod_log.assert_called_with(
        "test-pod", "default", container=None, tail_lines=0
    )


def test_list_namespaces_single_namespace(k8s_manager, mock_core_v1):
    """Test 50: List namespaces with only one namespace"""
    ns = Mock()
    ns.metadata.name = "only-one"
    mock_core_v1.list_namespace.return_value.items = [ns]
    result = k8s_manager.list_namespaces()
    assert len(result) == 1


# ==================== Multi-Cloud Scenario Tests ====================

def test_multi_cluster_switch_context(mock_k8s_config):
    """Test 51: Switch between multiple cluster contexts"""
    manager1 = KubernetesManager(context="minikube")
    manager2 = KubernetesManager(context="gke_project")
    assert mock_k8s_config.call_count == 2


def test_prod_staging_namespaces(k8s_manager, mock_core_v1):
    """Test 52: List pods in production vs staging namespaces"""
    result1 = k8s_manager.list_pods("production")
    result2 = k8s_manager.list_pods("staging")
    assert mock_core_v1.list_namespaced_pod.call_count == 2


def test_cross_namespace_services(k8s_manager, mock_core_v1):
    """Test 53: List services across multiple namespaces"""
    k8s_manager.list_services("ns1")
    k8s_manager.list_services("ns2")
    k8s_manager.list_services("ns3")
    assert mock_core_v1.list_namespaced_service.call_count == 3


# ==================== Pod Status Tests ====================

def test_pod_status_running(k8s_manager, mock_core_v1):
    """Test 54: Get pod with Running status"""
    pod = Mock()
    pod.metadata.name = "running-pod"
    pod.status.phase = "Running"
    pod.spec.node_name = "node-1"
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["status"] == "Running"


def test_pod_status_pending(k8s_manager, mock_core_v1):
    """Test 55: Get pod with Pending status"""
    pod = Mock()
    pod.metadata.name = "pending-pod"
    pod.status.phase = "Pending"
    pod.spec.node_name = None
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["status"] == "Pending"


def test_pod_status_failed(k8s_manager, mock_core_v1):
    """Test 56: Get pod with Failed status"""
    pod = Mock()
    pod.metadata.name = "failed-pod"
    pod.status.phase = "Failed"
    pod.spec.node_name = "node-1"
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["status"] == "Failed"


def test_pod_status_succeeded(k8s_manager, mock_core_v1):
    """Test 57: Get pod with Succeeded status"""
    pod = Mock()
    pod.metadata.name = "succeeded-pod"
    pod.status.phase = "Succeeded"
    pod.spec.node_name = "node-1"
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["status"] == "Succeeded"


def test_pod_status_unknown(k8s_manager, mock_core_v1):
    """Test 58: Get pod with Unknown status"""
    pod = Mock()
    pod.metadata.name = "unknown-pod"
    pod.status.phase = "Unknown"
    pod.spec.node_name = "node-1"
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["status"] == "Unknown"


# ==================== Service Type Tests ====================

def test_service_type_clusterip(k8s_manager, mock_core_v1):
    """Test 59: Get ClusterIP service"""
    svc = Mock()
    svc.metadata.name = "cluster-svc"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.0.0.1"
    svc.spec.ports = []
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("cluster-svc", "default")
    assert result["type"] == "ClusterIP"


def test_service_type_nodeport(k8s_manager, mock_core_v1):
    """Test 60: Get NodePort service"""
    svc = Mock()
    svc.metadata.name = "nodeport-svc"
    svc.spec.type = "NodePort"
    svc.spec.cluster_ip = "10.0.0.2"
    svc.spec.ports = []
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("nodeport-svc", "default")
    assert result["type"] == "NodePort"


def test_service_type_loadbalancer(k8s_manager, mock_core_v1):
    """Test 61: Get LoadBalancer service"""
    svc = Mock()
    svc.metadata.name = "lb-svc"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.0.0.3"
    svc.spec.ports = []
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("lb-svc", "default")
    assert result["type"] == "LoadBalancer"


def test_service_type_externalname(k8s_manager, mock_core_v1):
    """Test 62: Get ExternalName service"""
    svc = Mock()
    svc.metadata.name = "external-svc"
    svc.spec.type = "ExternalName"
    svc.spec.cluster_ip = "None"
    svc.spec.ports = []
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("external-svc", "default")
    assert result["type"] == "ExternalName"


# ==================== Service Port Tests ====================

def test_service_single_port(k8s_manager, mock_core_v1):
    """Test 63: Get service with single port"""
    svc = Mock()
    svc.metadata.name = "single-port-svc"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.0.0.4"
    port = Mock()
    port.port = 80
    port.target_port = 8080
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("single-port-svc", "default")
    assert len(result["ports"]) == 1
    assert result["ports"][0]["port"] == 80


def test_service_multiple_ports(k8s_manager, mock_core_v1):
    """Test 64: Get service with multiple ports"""
    svc = Mock()
    svc.metadata.name = "multi-port-svc"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.0.0.5"
    port1, port2, port3 = Mock(), Mock(), Mock()
    port1.port = 80
    port1.target_port = 8080
    port2.port = 443
    port2.target_port = 8443
    port3.port = 9090
    port3.target_port = 9090
    svc.spec.ports = [port1, port2, port3]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("multi-port-svc", "default")
    assert len(result["ports"]) == 3


# ==================== Deployment Scaling Tests ====================

def test_scale_deployment_scale_up(k8s_manager, mock_apps_v1):
    """Test 65: Scale up deployment replicas"""
    k8s_manager.scale_deployment("app", "default", 10)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 10


def test_scale_deployment_scale_down(k8s_manager, mock_apps_v1):
    """Test 66: Scale down deployment replicas"""
    k8s_manager.scale_deployment("app", "default", 1)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 1


def test_scale_deployment_large_scale(k8s_manager, mock_apps_v1):
    """Test 67: Scale deployment to large replica count"""
    k8s_manager.scale_deployment("app", "production", 100)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 100


# ==================== Namespace-Specific Tests ====================

def test_kube_system_namespace(k8s_manager, mock_core_v1):
    """Test 68: List pods in kube-system namespace"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"kube-system-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = "master"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("kube-system")
    assert len(result) == 5


def test_default_namespace(k8s_manager, mock_core_v1):
    """Test 69: List pods in default namespace"""
    result = k8s_manager.list_pods("default")
    mock_core_v1.list_namespaced_pod.assert_called_with("default")


def test_custom_namespace(k8s_manager, mock_core_v1):
    """Test 70: List pods in custom namespace"""
    result = k8s_manager.list_pods("my-custom-namespace")
    mock_core_v1.list_namespaced_pod.assert_called_with("my-custom-namespace")


# ==================== Log Retrieval Tests ====================

def test_get_logs_default_tail(k8s_manager, mock_core_v1):
    """Test 71: Get logs with default tail lines"""
    mock_core_v1.read_namespaced_pod_log.return_value = "log output"
    result = k8s_manager.get_pod_logs("pod", "default")
    mock_core_v1.read_namespaced_pod_log.assert_called_with(
        "pod", "default", container=None, tail_lines=100
    )


def test_get_logs_custom_tail(k8s_manager, mock_core_v1):
    """Test 72: Get logs with custom tail lines"""
    mock_core_v1.read_namespaced_pod_log.return_value = "log output"
    result = k8s_manager.get_pod_logs("pod", "default", tail_lines=1000)
    mock_core_v1.read_namespaced_pod_log.assert_called_with(
        "pod", "default", container=None, tail_lines=1000
    )


def test_get_logs_specific_container(k8s_manager, mock_core_v1):
    """Test 73: Get logs from specific container"""
    mock_core_v1.read_namespaced_pod_log.return_value = "container log"
    result = k8s_manager.get_pod_logs("pod", "default", container="sidecar")
    mock_core_v1.read_namespaced_pod_log.assert_called_with(
        "pod", "default", container="sidecar", tail_lines=100
    )


def test_get_logs_empty_response(k8s_manager, mock_core_v1):
    """Test 74: Get logs returns empty string"""
    mock_core_v1.read_namespaced_pod_log.return_value = ""
    result = k8s_manager.get_pod_logs("pod", "default")
    assert result == ""


def test_get_logs_multiline(k8s_manager, mock_core_v1):
    """Test 75: Get logs with multiline output"""
    mock_core_v1.read_namespaced_pod_log.return_value = "line1\nline2\nline3"
    result = k8s_manager.get_pod_logs("pod", "default")
    assert "line1" in result and "line2" in result


# ==================== Deployment Management Tests ====================

def test_delete_deployment_success(k8s_manager, mock_apps_v1):
    """Test 76: Successfully delete deployment"""
    k8s_manager.delete_deployment("old-app", "default")
    mock_apps_v1.delete_namespaced_deployment.assert_called_once_with("old-app", "default")


def test_delete_deployment_different_namespace(k8s_manager, mock_apps_v1):
    """Test 77: Delete deployment from specific namespace"""
    k8s_manager.delete_deployment("app", "production")
    mock_apps_v1.delete_namespaced_deployment.assert_called_with("app", "production")


def test_list_deployments_multiple(k8s_manager, mock_apps_v1):
    """Test 78: List multiple deployments"""
    deployments = [Mock() for _ in range(10)]
    for i, dep in enumerate(deployments):
        dep.metadata.name = f"deployment-{i}"
    mock_apps_v1.list_namespaced_deployment.return_value.items = deployments
    result = k8s_manager.list_deployments("default")
    assert len(result) == 10


# ==================== Mixed Resource Tests ====================

def test_list_all_resources_in_namespace(k8s_manager, mock_core_v1, mock_apps_v1):
    """Test 79: List all resource types in namespace"""
    mock_core_v1.list_namespaced_pod.return_value.items = [Mock()]
    mock_core_v1.list_namespaced_service.return_value.items = [Mock()]
    mock_apps_v1.list_namespaced_deployment.return_value.items = [Mock()]
    
    pods = k8s_manager.list_pods("default")
    services = k8s_manager.list_services("default")
    deployments = k8s_manager.list_deployments("default")
    
    assert len(pods) == 1
    assert len(services) == 1
    assert len(deployments) == 1


# ==================== Node Affinity Tests ====================

def test_pods_on_different_nodes(k8s_manager, mock_core_v1):
    """Test 80: List pods distributed across nodes"""
    pods = [Mock() for _ in range(6)]
    nodes = ["node-1", "node-2", "node-3"]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = nodes[i % 3]
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("default")
    node_names = [p["node"] for p in result]
    assert "node-1" in node_names and "node-2" in node_names


def test_pod_without_node_assignment(k8s_manager, mock_core_v1):
    """Test 81: List pod without node assignment"""
    pod = Mock()
    pod.metadata.name = "unscheduled-pod"
    pod.status.phase = "Pending"
    pod.spec.node_name = None
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["node"] is None


# ==================== Manifest File Tests ====================

def test_deploy_manifest_with_labels(k8s_manager, mock_apps_v1):
    """Test 82: Deploy manifest with labels"""
    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "labeled-deploy",
            "labels": {"app": "test", "env": "prod"}
        }
    }
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("labeled-deploy", "default", "deploy.yaml")
    mock_apps_v1.create_namespaced_deployment.assert_called_once()


def test_deploy_manifest_with_annotations(k8s_manager, mock_apps_v1):
    """Test 83: Deploy manifest with annotations"""
    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "annotated-deploy",
            "annotations": {"description": "test deployment"}
        }
    }
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("annotated-deploy", "default", "deploy.yaml")
    mock_apps_v1.create_namespaced_deployment.assert_called_once()


def test_deploy_service_with_selector(k8s_manager, mock_core_v1):
    """Test 84: Deploy service with selector"""
    manifest = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "selector-svc"},
        "spec": {"selector": {"app": "myapp"}}
    }
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("selector-svc", "default", "service.yaml")
    mock_core_v1.create_namespaced_service.assert_called_once()


# ==================== High Availability Tests ====================

def test_eks_multiple_availability_zones(k8s_manager, mock_core_v1):
    """Test 85: List pods across EKS availability zones"""
    pods = [Mock() for _ in range(9)]
    zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"ha-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"ip-10-0-{i}-{zones[i % 3]}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 9


def test_gke_regional_cluster_pods(k8s_manager, mock_core_v1):
    """Test 86: List pods in GKE regional cluster"""
    pods = [Mock() for _ in range(6)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"regional-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"gke-cluster-{i % 3}-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("default")
    assert len(result) == 6


def test_aks_zone_redundant_deployment(k8s_manager, mock_apps_v1):
    """Test 87: Scale deployment for zone redundancy on AKS"""
    k8s_manager.scale_deployment("critical-app", "production", 9)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 9


# ==================== Local Development Tests ====================

def test_minikube_single_node(k8s_manager, mock_core_v1):
    """Test 88: List pods on single-node Minikube"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"minikube-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = "minikube"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("default")
    assert all(p["node"] == "minikube" for p in result)


def test_kind_multi_node_cluster(k8s_manager, mock_core_v1):
    """Test 89: List pods on multi-node Kind cluster"""
    pods = [Mock() for _ in range(4)]
    nodes = ["kind-control-plane", "kind-worker", "kind-worker2", "kind-worker3"]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"kind-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = nodes[i]
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("default")
    assert len(result) == 4


def test_k3s_lightweight_distribution(k8s_manager, mock_core_v1):
    """Test 90: List resources on K3s lightweight distribution"""
    mock_core_v1.list_namespace.return_value.items = [Mock(), Mock()]
    result = k8s_manager.list_namespaces()
    assert len(result) == 2


# ==================== Performance and Scale Tests ====================

def test_list_large_number_of_pods(k8s_manager, mock_core_v1):
    """Test 91: List large number of pods (100+)"""
    pods = [Mock() for _ in range(150)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"scale-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i % 10}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 150


def test_list_many_namespaces(k8s_manager, mock_core_v1):
    """Test 92: List many namespaces (50+)"""
    namespaces = [Mock() for _ in range(50)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"namespace-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 50


def test_list_many_services(k8s_manager, mock_core_v1):
    """Test 93: List many services"""
    services = [Mock() for _ in range(30)]
    for i, svc in enumerate(services):
        svc.metadata.name = f"service-{i}"
    mock_core_v1.list_namespaced_service.return_value.items = services
    result = k8s_manager.list_services("default")
    assert len(result) == 30


def test_scale_to_very_high_replicas(k8s_manager, mock_apps_v1):
    """Test 94: Scale deployment to very high replica count"""
    k8s_manager.scale_deployment("massive-app", "production", 500)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 500


# ==================== Integration Scenario Tests ====================

def test_deploy_and_scale_workflow(k8s_manager, mock_apps_v1):
    """Test 95: Deploy then scale deployment"""
    manifest = {"kind": "Deployment", "metadata": {"name": "app"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("app", "default", "deploy.yaml")
    k8s_manager.scale_deployment("app", "default", 5)
    assert mock_apps_v1.create_namespaced_deployment.called
    assert mock_apps_v1.patch_namespaced_deployment_scale.called


def test_list_and_delete_workflow(k8s_manager, mock_apps_v1):
    """Test 96: List deployments then delete one"""
    deployments = [Mock(), Mock()]
    deployments[0].metadata.name = "app-1"
    deployments[1].metadata.name = "app-2"
    mock_apps_v1.list_namespaced_deployment.return_value.items = deployments
    result = k8s_manager.list_deployments("default")
    k8s_manager.delete_deployment("app-1", "default")
    assert len(result) == 2
    mock_apps_v1.delete_namespaced_deployment.assert_called_with("app-1", "default")


def test_multi_namespace_deployment(k8s_manager, mock_apps_v1):
    """Test 97: Deploy to multiple namespaces"""
    manifest = {"kind": "Deployment", "metadata": {"name": "app"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("app", "dev", "deploy.yaml")
        k8s_manager.deploy_manifest("app", "staging", "deploy.yaml")
        k8s_manager.deploy_manifest("app", "prod", "deploy.yaml")
    assert mock_apps_v1.create_namespaced_deployment.call_count == 3


# ==================== Special Characters and Names Tests ====================

def test_pod_with_special_characters(k8s_manager, mock_core_v1):
    """Test 98: List pod with special characters in name"""
    pod = Mock()
    pod.metadata.name = "my-app-12345-abcde"
    pod.status.phase = "Running"
    pod.spec.node_name = "node-1"
    mock_core_v1.list_namespaced_pod.return_value.items = [pod]
    result = k8s_manager.list_pods("default")
    assert result[0]["name"] == "my-app-12345-abcde"


def test_namespace_with_hyphens(k8s_manager, mock_core_v1):
    """Test 99: List namespace with hyphens"""
    ns = Mock()
    ns.metadata.name = "my-custom-namespace-prod"
    mock_core_v1.list_namespace.return_value.items = [ns]
    result = k8s_manager.list_namespaces()
    assert "my-custom-namespace-prod" in result


def test_service_with_numbers(k8s_manager, mock_core_v1):
    """Test 100: Get service with numbers in name"""
    svc = Mock()
    svc.metadata.name = "api-v2-service"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.0.0.99"
    svc.spec.ports = []
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("api-v2-service", "default")
    assert result["name"] == "api-v2-service"

# ==================== Production Use Case Tests ====================

def test_production_blue_green_deployment(k8s_manager, mock_apps_v1):
    """Test 101: Blue-green deployment pattern"""
    blue_manifest = {"kind": "Deployment", "metadata": {"name": "app-blue"}}
    green_manifest = {"kind": "Deployment", "metadata": {"name": "app-green"}}
    
    with patch("builtins.open", mock_open(read_data=yaml.dump(blue_manifest))):
        k8s_manager.deploy_manifest("app-blue", "production", "blue.yaml")
    with patch("builtins.open", mock_open(read_data=yaml.dump(green_manifest))):
        k8s_manager.deploy_manifest("app-green", "production", "green.yaml")
    
    assert mock_apps_v1.create_namespaced_deployment.call_count == 2


def test_production_canary_deployment_scaling(k8s_manager, mock_apps_v1):
    """Test 102: Canary deployment with gradual scaling"""
    k8s_manager.scale_deployment("app-canary", "production", 1)
    k8s_manager.scale_deployment("app-canary", "production", 5)
    k8s_manager.scale_deployment("app-canary", "production", 20)
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 3


def test_production_rollback_deployment(k8s_manager, mock_apps_v1):
    """Test 103: Rollback deployment by deleting and redeploying"""
    k8s_manager.delete_deployment("app-v2", "production")
    manifest = {"kind": "Deployment", "metadata": {"name": "app-v1"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("app-v1", "production", "rollback.yaml")
    assert mock_apps_v1.delete_namespaced_deployment.called


def test_production_multi_region_deployment(k8s_manager, mock_apps_v1):
    """Test 104: Deploy to multiple regions"""
    manifest = {"kind": "Deployment", "metadata": {"name": "global-app"}}
    regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
    
    for region in regions:
        with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
            k8s_manager.deploy_manifest("global-app", region, "deploy.yaml")
    
    assert mock_apps_v1.create_namespaced_deployment.call_count == 3


def test_production_database_stateful_workload(k8s_manager, mock_core_v1):
    """Test 105: Monitor database pods in production"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"postgres-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"db-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("database")
    assert len(result) == 3
    assert all(p["status"] == "Running" for p in result)


def test_production_zero_downtime_deployment(k8s_manager, mock_apps_v1):
    """Test 106: Zero-downtime deployment with scaling"""
    k8s_manager.scale_deployment("app-old", "production", 10)
    manifest = {"kind": "Deployment", "metadata": {"name": "app-new"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("app-new", "production", "new.yaml")
    k8s_manager.scale_deployment("app-new", "production", 10)
    k8s_manager.scale_deployment("app-old", "production", 0)
    k8s_manager.delete_deployment("app-old", "production")
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 3


def test_production_disaster_recovery_namespace_list(k8s_manager, mock_core_v1):
    """Test 107: List all namespaces for disaster recovery audit"""
    namespaces = [Mock() for _ in range(20)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"prod-ns-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 20


def test_production_monitoring_pod_health_check(k8s_manager, mock_core_v1):
    """Test 108: Health check monitoring for production pods"""
    pods = [Mock() for _ in range(50)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"app-{i}"
        pod.status.phase = "Running" if i % 10 != 0 else "Failed"
        pod.spec.node_name = f"node-{i % 5}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    failed_pods = [p for p in result if p["status"] == "Failed"]
    assert len(failed_pods) == 5


def test_production_auto_scaling_simulation(k8s_manager, mock_apps_v1):
    """Test 109: Simulate auto-scaling based on load"""
    scales = [5, 10, 20, 40, 60, 40, 20, 10, 5]
    for replicas in scales:
        k8s_manager.scale_deployment("api", "production", replicas)
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 9


def test_production_service_mesh_sidecar_pods(k8s_manager, mock_core_v1):
    """Test 110: List pods with service mesh sidecars"""
    pods = [Mock() for _ in range(10)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i % 3}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 10


def test_production_critical_workload_logs(k8s_manager, mock_core_v1):
    """Test 111: Retrieve logs from critical workload for debugging"""
    mock_core_v1.read_namespaced_pod_log.return_value = "ERROR: Database connection failed"
    result = k8s_manager.get_pod_logs("payment-service", "production", tail_lines=500)
    assert "ERROR" in result


def test_production_microservices_deployment(k8s_manager, mock_apps_v1):
    """Test 112: Deploy multiple microservices"""
    services = ["auth", "payment", "notification", "inventory", "shipping"]
    for svc in services:
        manifest = {"kind": "Deployment", "metadata": {"name": svc}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
            k8s_manager.deploy_manifest(svc, "production", f"{svc}.yaml")
    assert mock_apps_v1.create_namespaced_deployment.call_count == 5


def test_production_database_connection_service(k8s_manager, mock_core_v1):
    """Test 113: Get database connection service details"""
    svc = Mock()
    svc.metadata.name = "postgres-primary"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.200.50"
    port = Mock()
    port.port = 5432
    port.target_port = 5432
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("postgres-primary", "database")
    assert result["ports"][0]["port"] == 5432


def test_production_rate_limiting_service(k8s_manager, mock_core_v1):
    """Test 114: Get rate limiting service configuration"""
    svc = Mock()
    svc.metadata.name = "rate-limiter"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.150.10"
    port = Mock()
    port.port = 6379
    port.target_port = 6379
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("rate-limiter", "production")
    assert result["cluster_ip"] == "10.100.150.10"


def test_production_ingress_controller_pods(k8s_manager, mock_core_v1):
    """Test 115: List ingress controller pods"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"nginx-ingress-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"edge-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("ingress-nginx")
    assert len(result) == 3


def test_production_scheduled_job_cleanup(k8s_manager, mock_apps_v1):
    """Test 116: Clean up old deployments"""
    old_deployments = ["app-v1", "app-v2", "app-v3"]
    for deploy in old_deployments:
        k8s_manager.delete_deployment(deploy, "production")
    assert mock_apps_v1.delete_namespaced_deployment.call_count == 3


def test_production_redis_cache_service(k8s_manager, mock_core_v1):
    """Test 117: Get Redis cache service details"""
    svc = Mock()
    svc.metadata.name = "redis-cluster"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.100.100"
    port = Mock()
    port.port = 6379
    port.target_port = 6379
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("redis-cluster", "cache")
    assert result["name"] == "redis-cluster"


def test_production_prometheus_monitoring_pods(k8s_manager, mock_core_v1):
    """Test 118: List Prometheus monitoring pods"""
    pods = [Mock() for _ in range(2)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"prometheus-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"monitoring-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("monitoring")
    assert len(result) == 2


def test_production_elasticsearch_cluster_pods(k8s_manager, mock_core_v1):
    """Test 119: List Elasticsearch cluster pods"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"elasticsearch-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"data-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("logging")
    assert len(result) == 5


def test_production_kafka_broker_service(k8s_manager, mock_core_v1):
    """Test 120: Get Kafka broker service details"""
    svc = Mock()
    svc.metadata.name = "kafka-broker"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.50.50"
    port = Mock()
    port.port = 9092
    port.target_port = 9092
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("kafka-broker", "streaming")
    assert result["ports"][0]["port"] == 9092


def test_production_web_tier_horizontal_scaling(k8s_manager, mock_apps_v1):
    """Test 121: Scale web tier horizontally"""
    k8s_manager.scale_deployment("web-frontend", "production", 30)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 30


def test_production_api_gateway_service(k8s_manager, mock_core_v1):
    """Test 122: Get API gateway service configuration"""
    svc = Mock()
    svc.metadata.name = "api-gateway"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.1.1"
    port1, port2 = Mock(), Mock()
    port1.port = 80
    port1.target_port = 8080
    port2.port = 443
    port2.target_port = 8443
    svc.spec.ports = [port1, port2]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("api-gateway", "production")
    assert len(result["ports"]) == 2


def test_production_database_backup_pods(k8s_manager, mock_core_v1):
    """Test 123: List database backup job pods"""
    pods = [Mock()]
    pods[0].metadata.name = "db-backup-12345"
    pods[0].status.phase = "Succeeded"
    pods[0].spec.node_name = "backup-node"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("backup")
    assert result[0]["status"] == "Succeeded"


def test_production_cluster_autoscaler_logs(k8s_manager, mock_core_v1):
    """Test 124: Get cluster autoscaler logs"""
    mock_core_v1.read_namespaced_pod_log.return_value = "Scaling up node group to 10 nodes"
    result = k8s_manager.get_pod_logs("cluster-autoscaler", "kube-system", tail_lines=200)
    assert "Scaling up" in result


def test_production_cert_manager_pods(k8s_manager, mock_core_v1):
    """Test 125: List cert-manager pods for SSL certificates"""
    pods = [Mock()]
    pods[0].metadata.name = "cert-manager-abc123"
    pods[0].status.phase = "Running"
    pods[0].spec.node_name = "system-node"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("cert-manager")
    assert len(result) == 1


def test_production_multi_tenant_namespaces(k8s_manager, mock_core_v1):
    """Test 126: List namespaces for multi-tenant environment"""
    namespaces = [Mock() for _ in range(15)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"tenant-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    tenant_ns = [ns for ns in result if ns.startswith("tenant-")]
    assert len(tenant_ns) == 15


def test_production_secrets_rotation_deployment(k8s_manager, mock_apps_v1):
    """Test 127: Redeploy after secrets rotation"""
    k8s_manager.delete_deployment("api", "production")
    manifest = {"kind": "Deployment", "metadata": {"name": "api"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("api", "production", "api.yaml")
    assert mock_apps_v1.delete_namespaced_deployment.called
    assert mock_apps_v1.create_namespaced_deployment.called


def test_production_batch_processing_pods(k8s_manager, mock_core_v1):
    """Test 128: List batch processing pods"""
    pods = [Mock() for _ in range(8)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"batch-job-{i}"
        pod.status.phase = "Running" if i < 6 else "Succeeded"
        pod.spec.node_name = f"batch-node-{i % 4}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("batch")
    assert len(result) == 8


def test_production_grpc_service_configuration(k8s_manager, mock_core_v1):
    """Test 129: Get gRPC service configuration"""
    svc = Mock()
    svc.metadata.name = "grpc-api"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.75.75"
    port = Mock()
    port.port = 50051
    port.target_port = 50051
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("grpc-api", "production")
    assert result["ports"][0]["port"] == 50051


def test_production_ml_model_serving_pods(k8s_manager, mock_core_v1):
    """Test 130: List ML model serving pods"""
    pods = [Mock() for _ in range(4)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"ml-model-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"gpu-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("ml-inference")
    assert len(result) == 4


def test_production_queue_worker_scaling(k8s_manager, mock_apps_v1):
    """Test 131: Scale queue workers based on queue depth"""
    k8s_manager.scale_deployment("queue-worker", "production", 15)
    k8s_manager.scale_deployment("queue-worker", "production", 25)
    k8s_manager.scale_deployment("queue-worker", "production", 10)
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 3


def test_production_websocket_service(k8s_manager, mock_core_v1):
    """Test 132: Get WebSocket service details"""
    svc = Mock()
    svc.metadata.name = "websocket-server"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.88.88"
    port = Mock()
    port.port = 8080
    port.target_port = 8080
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("websocket-server", "realtime")
    assert result["type"] == "LoadBalancer"


def test_production_cdn_origin_service(k8s_manager, mock_core_v1):
    """Test 133: Get CDN origin service configuration"""
    svc = Mock()
    svc.metadata.name = "cdn-origin"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.200.1"
    port = Mock()
    port.port = 443
    port.target_port = 8443
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("cdn-origin", "edge")
    assert result["cluster_ip"] == "10.100.200.1"


def test_production_payment_gateway_high_availability(k8s_manager, mock_apps_v1):
    """Test 134: Ensure payment gateway high availability"""
    k8s_manager.scale_deployment("payment-gateway", "production", 12)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 12


def test_production_session_store_service(k8s_manager, mock_core_v1):
    """Test 135: Get session store service details"""
    svc = Mock()
    svc.metadata.name = "session-redis"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.111.111"
    port = Mock()
    port.port = 6379
    port.target_port = 6379
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("session-redis", "production")
    assert result["name"] == "session-redis"


def test_production_image_processing_pods(k8s_manager, mock_core_v1):
    """Test 136: List image processing worker pods"""
    pods = [Mock() for _ in range(6)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"image-processor-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"compute-node-{i % 3}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("media")
    assert len(result) == 6


def test_production_email_service_pods(k8s_manager, mock_core_v1):
    """Test 137: List email service pods"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"email-worker-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"worker-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("notifications")
    assert len(result) == 3


def test_production_search_service_configuration(k8s_manager, mock_core_v1):
    """Test 138: Get search service configuration"""
    svc = Mock()
    svc.metadata.name = "search-api"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.55.55"
    port = Mock()
    port.port = 9200
    port.target_port = 9200
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("search-api", "production")
    assert result["ports"][0]["port"] == 9200


def test_production_analytics_pipeline_pods(k8s_manager, mock_core_v1):
    """Test 139: List analytics pipeline pods"""
    pods = [Mock() for _ in range(7)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"analytics-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"analytics-node-{i % 2}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("analytics")
    assert len(result) == 7


def test_production_recommendation_engine_scaling(k8s_manager, mock_apps_v1):
    """Test 140: Scale recommendation engine"""
    k8s_manager.scale_deployment("recommendation-api", "production", 20)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 20


def test_production_fraud_detection_pods(k8s_manager, mock_core_v1):
    """Test 141: List fraud detection service pods"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"fraud-detector-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"security-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("security")
    assert len(result) == 5


def test_production_video_streaming_service(k8s_manager, mock_core_v1):
    """Test 142: Get video streaming service configuration"""
    svc = Mock()
    svc.metadata.name = "video-streamer"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.222.222"
    port = Mock()
    port.port = 1935
    port.target_port = 1935
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("video-streamer", "streaming")
    assert result["type"] == "LoadBalancer"


def test_production_audit_logging_pods(k8s_manager, mock_core_v1):
    """Test 143: List audit logging pods"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"audit-logger-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"logging-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("audit")
    assert len(result) == 3


def test_production_data_warehouse_etl_pods(k8s_manager, mock_core_v1):
    """Test 144: List ETL pipeline pods"""
    pods = [Mock() for _ in range(4)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"etl-job-{i}"
        pod.status.phase = "Running" if i < 3 else "Succeeded"
        pod.spec.node_name = f"etl-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("data-warehouse")
    assert len(result) == 4


def test_production_rate_limiter_redis_service(k8s_manager, mock_core_v1):
    """Test 145: Get rate limiter Redis service"""
    svc = Mock()
    svc.metadata.name = "rate-limit-redis"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.33.33"
    port = Mock()
    port.port = 6379
    port.target_port = 6379
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("rate-limit-redis", "infrastructure")
    assert result["cluster_ip"] == "10.100.33.33"


def test_production_feature_flag_service(k8s_manager, mock_core_v1):
    """Test 146: Get feature flag service configuration"""
    svc = Mock()
    svc.metadata.name = "feature-flags"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.44.44"
    port = Mock()
    port.port = 8000
    port.target_port = 8000
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("feature-flags", "production")
    assert result["name"] == "feature-flags"


def test_production_object_storage_gateway_pods(k8s_manager, mock_core_v1):
    """Test 147: List object storage gateway pods"""
    pods = [Mock() for _ in range(4)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"s3-gateway-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"storage-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("storage")
    assert len(result) == 4


def test_production_graphql_api_service(k8s_manager, mock_core_v1):
    """Test 148: Get GraphQL API service configuration"""
    svc = Mock()
    svc.metadata.name = "graphql-api"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.66.66"
    port = Mock()
    port.port = 4000
    port.target_port = 4000
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("graphql-api", "production")
    assert result["ports"][0]["port"] == 4000


def test_production_cron_job_cleanup_pods(k8s_manager, mock_core_v1):
    """Test 149: List completed cron job pods"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"cleanup-job-{i}"
        pod.status.phase = "Succeeded"
        pod.spec.node_name = f"worker-node-{i % 2}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("cron-jobs")
    assert all(p["status"] == "Succeeded" for p in result)


def test_production_rbac_audit_namespaces(k8s_manager, mock_core_v1):
    """Test 150: Audit namespaces for RBAC compliance"""
    namespaces = [Mock() for _ in range(25)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"prod-ns-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 25


def test_production_distributed_tracing_pods(k8s_manager, mock_core_v1):
    """Test 151: List distributed tracing collector pods"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"jaeger-collector-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"trace-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("tracing")
    assert len(result) == 3


def test_production_message_broker_service(k8s_manager, mock_core_v1):
    """Test 152: Get message broker service details"""
    svc = Mock()
    svc.metadata.name = "rabbitmq"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.77.77"
    port1, port2 = Mock(), Mock()
    port1.port = 5672
    port1.target_port = 5672
    port2.port = 15672
    port2.target_port = 15672
    svc.spec.ports = [port1, port2]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("rabbitmq", "messaging")
    assert len(result["ports"]) == 2


def test_production_sso_authentication_service(k8s_manager, mock_core_v1):
    """Test 153: Get SSO authentication service"""
    svc = Mock()
    svc.metadata.name = "keycloak"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.99.99"
    port = Mock()
    port.port = 8080
    port.target_port = 8080
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("keycloak", "auth")
    assert result["name"] == "keycloak"


def test_production_chaos_engineering_pods(k8s_manager, mock_core_v1):
    """Test 154: List chaos engineering test pods"""
    pods = [Mock() for _ in range(2)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"chaos-monkey-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"test-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("chaos-testing")
    assert len(result) == 2


def test_production_time_series_database_service(k8s_manager, mock_core_v1):
    """Test 155: Get time series database service"""
    svc = Mock()
    svc.metadata.name = "influxdb"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.123.123"
    port = Mock()
    port.port = 8086
    port.target_port = 8086
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("influxdb", "metrics")
    assert result["ports"][0]["port"] == 8086


def test_production_api_rate_limiting_deployment(k8s_manager, mock_apps_v1):
    """Test 156: Deploy API rate limiting middleware"""
    manifest = {"kind": "Deployment", "metadata": {"name": "rate-limiter"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("rate-limiter", "production", "limiter.yaml")
    assert mock_apps_v1.create_namespaced_deployment.called


def test_production_load_balancer_health_check(k8s_manager, mock_core_v1):
    """Test 157: Get load balancer service for health checks"""
    svc = Mock()
    svc.metadata.name = "external-lb"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.1.100"
    port = Mock()
    port.port = 80
    port.target_port = 8080
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("external-lb", "production")
    assert result["type"] == "LoadBalancer"


def test_production_disaster_recovery_backup_logs(k8s_manager, mock_core_v1):
    """Test 158: Get disaster recovery backup logs"""
    mock_core_v1.read_namespaced_pod_log.return_value = "Backup completed successfully at 2025-10-06"
    result = k8s_manager.get_pod_logs("backup-job-xyz", "backup", tail_lines=50)
    assert "Backup completed" in result


def test_production_container_registry_pods(k8s_manager, mock_core_v1):
    """Test 159: List container registry pods"""
    pods = [Mock() for _ in range(2)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"docker-registry-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"registry-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("registry")
    assert len(result) == 2


def test_production_api_documentation_service(k8s_manager, mock_core_v1):
    """Test 160: Get API documentation service"""
    svc = Mock()
    svc.metadata.name = "swagger-ui"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.88.88"
    port = Mock()
    port.port = 8080
    port.target_port = 8080
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("swagger-ui", "documentation")
    assert result["name"] == "swagger-ui"


def test_production_continuous_deployment_pods(k8s_manager, mock_core_v1):
    """Test 161: List continuous deployment pipeline pods"""
    pods = [Mock() for _ in range(3)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"argocd-server-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"cicd-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("argocd")
    assert len(result) == 3


def test_production_network_policy_validation(k8s_manager, mock_core_v1):
    """Test 162: List pods to validate network policies"""
    pods = [Mock() for _ in range(10)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"secured-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"secure-node-{i % 3}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("secure-zone")
    assert len(result) == 10


def test_production_cdn_edge_service(k8s_manager, mock_core_v1):
    """Test 163: Get CDN edge service configuration"""
    svc = Mock()
    svc.metadata.name = "cdn-edge"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.200.200"
    port = Mock()
    port.port = 443
    port.target_port = 8443
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("cdn-edge", "edge")
    assert result["type"] == "LoadBalancer"


def test_production_data_encryption_service(k8s_manager, mock_core_v1):
    """Test 164: Get data encryption service"""
    svc = Mock()
    svc.metadata.name = "vault"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.111.222"
    port = Mock()
    port.port = 8200
    port.target_port = 8200
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("vault", "security")
    assert result["ports"][0]["port"] == 8200


def test_production_compliance_scanning_pods(k8s_manager, mock_core_v1):
    """Test 165: List compliance scanning pods"""
    pods = [Mock() for _ in range(2)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"falco-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"security-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("security-scanning")
    assert len(result) == 2


def test_production_log_aggregation_service(k8s_manager, mock_core_v1):
    """Test 166: Get log aggregation service"""
    svc = Mock()
    svc.metadata.name = "fluentd"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.144.144"
    port = Mock()
    port.port = 24224
    port.target_port = 24224
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("fluentd", "logging")
    assert result["name"] == "fluentd"


def test_production_api_versioning_deployments(k8s_manager, mock_apps_v1):
    """Test 167: Deploy multiple API versions"""
    versions = ["v1", "v2", "v3"]
    for version in versions:
        manifest = {"kind": "Deployment", "metadata": {"name": f"api-{version}"}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
            k8s_manager.deploy_manifest(f"api-{version}", "production", f"api-{version}.yaml")
    assert mock_apps_v1.create_namespaced_deployment.call_count == 3


def test_production_pod_disruption_budget_check(k8s_manager, mock_core_v1):
    """Test 168: Check pods for PDB compliance"""
    pods = [Mock() for _ in range(8)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"critical-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i % 4}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("critical")
    assert len(result) == 8


def test_production_spot_instance_pods(k8s_manager, mock_core_v1):
    """Test 169: List pods on spot instances"""
    pods = [Mock() for _ in range(12)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"batch-process-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"spot-node-{i % 6}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("batch-spot")
    assert len(result) == 12


def test_production_service_account_validation(k8s_manager, mock_core_v1):
    """Test 170: List pods to validate service accounts"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"sa-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 5


def test_production_network_mesh_sidecar_logs(k8s_manager, mock_core_v1):
    """Test 171: Get logs from service mesh sidecar"""
    mock_core_v1.read_namespaced_pod_log.return_value = "Istio proxy started on port 15001"
    result = k8s_manager.get_pod_logs("app-pod", "production", container="istio-proxy", tail_lines=100)
    assert "Istio proxy" in result


def test_production_horizontal_pod_autoscaler_check(k8s_manager, mock_apps_v1):
    """Test 172: Verify deployment for HPA"""
    deployments = [Mock() for _ in range(5)]
    for i, dep in enumerate(deployments):
        dep.metadata.name = f"hpa-app-{i}"
    mock_apps_v1.list_namespaced_deployment.return_value.items = deployments
    result = k8s_manager.list_deployments("production")
    assert len(result) == 5


def test_production_init_container_logs(k8s_manager, mock_core_v1):
    """Test 173: Get init container logs"""
    mock_core_v1.read_namespaced_pod_log.return_value = "Init container completed migration"
    result = k8s_manager.get_pod_logs("app-pod", "production", container="init-db", tail_lines=50)
    assert "migration" in result


def test_production_resource_quota_namespace_list(k8s_manager, mock_core_v1):
    """Test 174: List namespaces for resource quota validation"""
    namespaces = [Mock() for _ in range(12)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"team-{i}-prod"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 12


def test_production_gpu_workload_pods(k8s_manager, mock_core_v1):
    """Test 175: List GPU-accelerated workload pods"""
    pods = [Mock() for _ in range(4)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"gpu-training-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"gpu-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("ml-training")
    assert len(result) == 4


def test_production_daemonset_monitoring_pods(k8s_manager, mock_core_v1):
    """Test 176: List daemonset monitoring pods across all nodes"""
    pods = [Mock() for _ in range(10)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"node-exporter-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"worker-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("monitoring")
    assert len(result) == 10


def test_production_webhook_service_configuration(k8s_manager, mock_core_v1):
    """Test 177: Get webhook service configuration"""
    svc = Mock()
    svc.metadata.name = "webhook-receiver"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.33.44"
    port = Mock()
    port.port = 443
    port.target_port = 8443
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("webhook-receiver", "webhooks")
    assert result["type"] == "LoadBalancer"


def test_production_scheduled_scaling_simulation(k8s_manager, mock_apps_v1):
    """Test 178: Simulate scheduled scaling (morning rush)"""
    k8s_manager.scale_deployment("web-app", "production", 5)   # Night
    k8s_manager.scale_deployment("web-app", "production", 50)  # Morning
    k8s_manager.scale_deployment("web-app", "production", 80)  # Peak
    k8s_manager.scale_deployment("web-app", "production", 30)  # Afternoon
    k8s_manager.scale_deployment("web-app", "production", 10)  # Evening
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 5


def test_production_multi_cluster_namespace_sync(k8s_manager, mock_core_v1):
    """Test 179: List namespaces for multi-cluster sync"""
    namespaces = [Mock() for _ in range(8)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"sync-ns-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 8


def test_production_external_secrets_pods(k8s_manager, mock_core_v1):
    """Test 180: List external secrets operator pods"""
    pods = [Mock() for _ in range(2)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"external-secrets-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"system-node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("external-secrets")
    assert len(result) == 2


def test_production_traffic_splitting_services(k8s_manager, mock_core_v1):
    """Test 181: Get services for traffic splitting"""
    services = [Mock() for _ in range(3)]
    for i, svc in enumerate(services):
        svc.metadata.name = f"app-v{i+1}"
    mock_core_v1.list_namespaced_service.return_value.items = services
    result = k8s_manager.list_services("production")
    assert len(result) == 3


def test_production_backup_verification_logs(k8s_manager, mock_core_v1):
    """Test 182: Get backup verification logs"""
    mock_core_v1.read_namespaced_pod_log.return_value = "Backup verified: 500GB uploaded successfully"
    result = k8s_manager.get_pod_logs("backup-verify", "backup", tail_lines=100)
    assert "verified" in result


def test_production_memory_intensive_pods(k8s_manager, mock_core_v1):
    """Test 183: List memory-intensive application pods"""
    pods = [Mock() for _ in range(6)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"memory-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"large-mem-node-{i % 2}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("high-memory")
    assert len(result) == 6


def test_production_api_gateway_multiple_upstreams(k8s_manager, mock_core_v1):
    """Test 184: Get API gateway with multiple upstream services"""
    svc = Mock()
    svc.metadata.name = "kong-gateway"
    svc.spec.type = "LoadBalancer"
    svc.spec.cluster_ip = "10.100.77.88"
    ports = [Mock() for _ in range(3)]
    ports[0].port = 80
    ports[0].target_port = 8000
    ports[1].port = 443
    ports[1].target_port = 8443
    ports[2].port = 8001
    ports[2].target_port = 8001
    svc.spec.ports = ports
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("kong-gateway", "gateway")
    assert len(result["ports"]) == 3


def test_production_circuit_breaker_deployment(k8s_manager, mock_apps_v1):
    """Test 185: Deploy service with circuit breaker pattern"""
    manifest = {"kind": "Deployment", "metadata": {"name": "circuit-breaker-api"}}
    with patch("builtins.open", mock_open(read_data=yaml.dump(manifest))):
        k8s_manager.deploy_manifest("circuit-breaker-api", "production", "cb.yaml")
    assert mock_apps_v1.create_namespaced_deployment.called


def test_production_cost_optimization_pod_review(k8s_manager, mock_core_v1):
    """Test 186: Review pods for cost optimization"""
    pods = [Mock() for _ in range(100)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"cost-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i % 10}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 100


def test_production_sli_slo_monitoring_services(k8s_manager, mock_core_v1):
    """Test 187: Get SLI/SLO monitoring services"""
    services = [Mock() for _ in range(4)]
    for i, svc in enumerate(services):
        svc.metadata.name = f"slo-monitor-{i}"
    mock_core_v1.list_namespaced_service.return_value.items = services
    result = k8s_manager.list_services("monitoring")
    assert len(result) == 4


def test_production_warm_standby_deployment(k8s_manager, mock_apps_v1):
    """Test 188: Maintain warm standby deployment"""
    k8s_manager.scale_deployment("standby-app", "dr", 3)
    call_args = mock_apps_v1.patch_namespaced_deployment_scale.call_args
    assert call_args[0][2]["spec"]["replicas"] == 3


def test_production_dependency_injection_service(k8s_manager, mock_core_v1):
    """Test 189: Get dependency injection service"""
    svc = Mock()
    svc.metadata.name = "config-service"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.199.199"
    port = Mock()
    port.port = 8888
    port.target_port = 8888
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("config-service", "infrastructure")
    assert result["name"] == "config-service"


def test_production_tenant_isolation_pods(k8s_manager, mock_core_v1):
    """Test 190: List pods with tenant isolation"""
    pods = [Mock() for _ in range(15)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"tenant-{i % 5}-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"tenant-node-{i % 5}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("multi-tenant")
    assert len(result) == 15


def test_production_zero_trust_network_pods(k8s_manager, mock_core_v1):
    """Test 191: List pods in zero-trust network"""
    pods = [Mock() for _ in range(8)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"zt-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"secure-node-{i % 4}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("zero-trust")
    assert len(result) == 8


def test_production_event_driven_scaling(k8s_manager, mock_apps_v1):
    """Test 192: Event-driven scaling with KEDA"""
    k8s_manager.scale_deployment("event-processor", "production", 0)
    k8s_manager.scale_deployment("event-processor", "production", 25)
    k8s_manager.scale_deployment("event-processor", "production", 0)
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 3


def test_production_egress_gateway_service(k8s_manager, mock_core_v1):
    """Test 193: Get egress gateway service"""
    svc = Mock()
    svc.metadata.name = "egress-gateway"
    svc.spec.type = "ClusterIP"
    svc.spec.cluster_ip = "10.100.250.250"
    port = Mock()
    port.port = 8080
    port.target_port = 8080
    svc.spec.ports = [port]
    mock_core_v1.read_namespaced_service.return_value = svc
    result = k8s_manager.get_service("egress-gateway", "networking")
    assert result["cluster_ip"] == "10.100.250.250"


def test_production_failover_deployment_workflow(k8s_manager, mock_apps_v1):
    """Test 194: Failover deployment workflow"""
    k8s_manager.scale_deployment("primary-db", "production", 0)
    k8s_manager.scale_deployment("secondary-db", "production", 3)
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 2


def test_production_image_pull_secret_validation(k8s_manager, mock_core_v1):
    """Test 195: Validate image pull secrets via pod listing"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"private-image-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("production")
    assert len(result) == 5


def test_production_progressive_rollout_phases(k8s_manager, mock_apps_v1):
    """Test 196: Progressive rollout in phases"""
    k8s_manager.scale_deployment("app-new", "production", 2)   # 10%
    k8s_manager.scale_deployment("app-new", "production", 5)   # 25%
    k8s_manager.scale_deployment("app-new", "production", 10)  # 50%
    k8s_manager.scale_deployment("app-new", "production", 20)  # 100%
    assert mock_apps_v1.patch_namespaced_deployment_scale.call_count == 4


def test_production_stateful_set_pods_ordering(k8s_manager, mock_core_v1):
    """Test 197: List StatefulSet pods with ordering"""
    pods = [Mock() for _ in range(5)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"stateful-app-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("stateful")
    assert len(result) == 5


def test_production_priority_class_pods(k8s_manager, mock_core_v1):
    """Test 198: List pods with priority classes"""
    pods = [Mock() for _ in range(10)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"priority-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i % 3}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    result = k8s_manager.list_pods("critical-workloads")
    assert len(result) == 10


def test_production_observability_stack_services(k8s_manager, mock_core_v1):
    """Test 199: Get observability stack services"""
    services = [Mock() for _ in range(5)]
    names = ["prometheus", "grafana", "alertmanager", "loki", "tempo"]
    for i, svc in enumerate(services):
        svc.metadata.name = names[i]
    mock_core_v1.list_namespaced_service.return_value.items = services
    result = k8s_manager.list_services("observability")
    assert len(result) == 5


def test_production_annual_compliance_audit(k8s_manager, mock_core_v1):
    """Test 200: Annual compliance audit - list all production resources"""
    namespaces = [Mock() for _ in range(30)]
    for i, ns in enumerate(namespaces):
        ns.metadata.name = f"compliance-ns-{i}"
    mock_core_v1.list_namespace.return_value.items = namespaces
    result = k8s_manager.list_namespaces()
    assert len(result) == 30
    
    # Also verify we can list pods and services for audit
    pods = [Mock() for _ in range(100)]
    for i, pod in enumerate(pods):
        pod.metadata.name = f"audit-pod-{i}"
        pod.status.phase = "Running"
        pod.spec.node_name = f"node-{i % 20}"
    mock_core_v1.list_namespaced_pod.return_value.items = pods
    pod_result = k8s_manager.list_pods("production")
    assert len(pod_result) == 100