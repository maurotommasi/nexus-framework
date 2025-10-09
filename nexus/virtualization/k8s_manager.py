"""
Nexus Kubernetes Manager

A single-file Python class to manage Kubernetes clusters using the official Python client.

Requirements:
    pip install kubernetes

Usage example:
    from k8s_manager import KubernetesManager
    k8s = KubernetesManager()
    k8s.list_namespaces()
    k8s.deploy_manifest('my-app', 'default', 'deployment.yaml')
    k8s.scale_deployment('my-app', 'default', replicas=3)
"""

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from typing import List, Dict, Optional
import logging
import yaml

logger = logging.getLogger("NexusK8sManager")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(ch)


class KubernetesManager:
    """Manage Kubernetes clusters with common operations."""

    def __init__(self, kubeconfig_path: Optional[str] = None, context: Optional[str] = None):
        """
        Initialize Kubernetes client.
        
        - kubeconfig_path: Path to kubeconfig file (default: ~/.kube/config)
        - context: Specific cluster/context to use
        """
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path, context=context)
        else:
            config.load_kube_config(context=context)
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        logger.info("KubernetesManager initialized")

    # -------------------- Namespace Operations --------------------
    def list_namespaces(self) -> List[str]:
        """Return a list of namespaces in the cluster."""
        try:
            ns_list = self.v1.list_namespace()
            return [ns.metadata.name for ns in ns_list.items]
        except ApiException as e:
            logger.error(f"Error listing namespaces: {e}")
            return []

    # -------------------- Pod Operations --------------------
    def list_pods(self, namespace: str) -> List[Dict]:
        """List pods in a namespace."""
        try:
            pods = self.v1.list_namespaced_pod(namespace)
            return [{
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "node": pod.spec.node_name
            } for pod in pods.items]
        except ApiException as e:
            logger.error(f"Error listing pods in {namespace}: {e}")
            return []

    def get_pod_logs(self, name: str, namespace: str, container: Optional[str] = None, tail_lines: int = 100) -> str:
        """Retrieve logs from a pod/container."""
        try:
            return self.v1.read_namespaced_pod_log(name, namespace, container=container, tail_lines=tail_lines)
        except ApiException as e:
            logger.error(f"Error getting logs for pod {name}: {e}")
            return ""

    # -------------------- Deployment Operations --------------------
    def list_deployments(self, namespace: str) -> List[str]:
        """List deployments in a namespace."""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            return [d.metadata.name for d in deployments.items]
        except ApiException as e:
            logger.error(f"Error listing deployments in {namespace}: {e}")
            return []

    def scale_deployment(self, name: str, namespace: str, replicas: int):
        """Scale a deployment to the specified number of replicas."""
        try:
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
            logger.info(f"Scaled deployment {name} in {namespace} to {replicas} replicas")
        except ApiException as e:
            logger.error(f"Error scaling deployment {name}: {e}")

    def deploy_manifest(self, name: str, namespace: str, manifest_path: str):
        """Create/update a deployment from a YAML manifest."""
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        kind = manifest.get('kind', '').lower()
        try:
            if kind == 'deployment':
                self.apps_v1.create_namespaced_deployment(namespace=namespace, body=manifest)
                logger.info(f"Deployed deployment {name} in {namespace}")
            elif kind == 'service':
                self.v1.create_namespaced_service(namespace=namespace, body=manifest)
                logger.info(f"Created service {name} in {namespace}")
            else:
                logger.warning(f"Unsupported kind {kind} in manifest")
        except ApiException as e:
            logger.error(f"Error deploying {name}: {e}")

    def delete_deployment(self, name: str, namespace: str):
        """Delete a deployment."""
        try:
            self.apps_v1.delete_namespaced_deployment(name, namespace)
            logger.info(f"Deleted deployment {name} in {namespace}")
        except ApiException as e:
            logger.error(f"Error deleting deployment {name}: {e}")

    # -------------------- Service Operations --------------------
    def list_services(self, namespace: str) -> List[str]:
        """List services in a namespace."""
        try:
            services = self.v1.list_namespaced_service(namespace)
            return [s.metadata.name for s in services.items]
        except ApiException as e:
            logger.error(f"Error listing services in {namespace}: {e}")
            return []

    def get_service(self, name: str, namespace: str) -> Dict:
        """Get details of a service."""
        try:
            svc = self.v1.read_namespaced_service(name, namespace)
            return {
                "name": svc.metadata.name,
                "type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": [{"port": p.port, "target_port": p.target_port} for p in svc.spec.ports]
            }
        except ApiException as e:
            logger.error(f"Error getting service {name}: {e}")
            return {}

# -------------------- Quick Demo --------------------
if __name__ == "__main__":
    k8s = KubernetesManager()
    print("Namespaces:", k8s.list_namespaces())
    for ns in k8s.list_namespaces():
        print(f"Pods in {ns}:", k8s.list_pods(ns))
