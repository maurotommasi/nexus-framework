# Nexus Kubernetes Manager - Usage Examples

## Installation

```bash
pip install kubernetes
```

## Quick Start

```python
from nexus.virtualization.k8s_manager import KubernetesManager

# Initialize the manager (uses default kubeconfig)
k8s = KubernetesManager()

# List all namespaces
namespaces = k8s.list_namespaces()
print(namespaces)
```

---

## Programmatic Examples

### 1. Initialize with Custom Kubeconfig

**Input:**
```python
from nexus.virtualization.k8s_manager import KubernetesManager

# Use default kubeconfig (~/.kube/config)
k8s = KubernetesManager()

# Use custom kubeconfig path
k8s_custom = KubernetesManager(kubeconfig_path='/path/to/kubeconfig')

# Use specific context
k8s_prod = KubernetesManager(context='production-cluster')
```

**Output:**
```
[INFO] KubernetesManager initialized
[INFO] KubernetesManager initialized
[INFO] KubernetesManager initialized
```

---

### 2. List All Namespaces

**Input:**
```python
namespaces = k8s.list_namespaces()

print("Available namespaces:")
for ns in namespaces:
    print(f"  - {ns}")
```

**Output:**
```
Available namespaces:
  - default
  - kube-system
  - kube-public
  - kube-node-lease
  - production
  - staging
  - development
```

---

### 3. List Pods in a Namespace

**Input:**
```python
# List all pods in the default namespace
pods = k8s.list_pods('default')

print(f"Found {len(pods)} pods in 'default' namespace:")
for pod in pods:
    print(f"  Name: {pod['name']}")
    print(f"  Status: {pod['status']}")
    print(f"  Node: {pod['node']}")
    print()
```

**Output:**
```
Found 3 pods in 'default' namespace:
  Name: nginx-deployment-7fb96c846b-4xk2m
  Status: Running
  Node: worker-node-1

  Name: nginx-deployment-7fb96c846b-8zp5n
  Status: Running
  Node: worker-node-2

  Name: redis-master-0
  Status: Running
  Node: worker-node-1
```

---

### 4. Get Pod Logs

**Input:**
```python
# Get last 50 lines of logs from a pod
logs = k8s.get_pod_logs(
    name='nginx-deployment-7fb96c846b-4xk2m',
    namespace='default',
    tail_lines=50
)

print("Pod logs:")
print(logs)
```

**Output:**
```
Pod logs:
2025/09/29 10:30:45 [notice] 1#1: using the "epoll" event method
2025/09/29 10:30:45 [notice] 1#1: nginx/1.23.3
2025/09/29 10:30:45 [notice] 1#1: built by gcc 12.2.0 (Debian 12.2.0-14)
2025/09/29 10:30:45 [notice] 1#1: OS: Linux 5.15.0-78-generic
2025/09/29 10:30:45 [notice] 1#1: getrlimit(RLIMIT_NOFILE): 1048576:1048576
2025/09/29 10:30:45 [notice] 1#1: start worker processes
192.168.1.10 - - [29/Sep/2025:10:35:22 +0000] "GET / HTTP/1.1" 200 612
192.168.1.11 - - [29/Sep/2025:10:36:15 +0000] "GET /health HTTP/1.1" 200 2
```

---

### 5. Get Logs from Specific Container

**Input:**
```python
# Get logs from a specific container in a multi-container pod
logs = k8s.get_pod_logs(
    name='app-pod-with-sidecar',
    namespace='production',
    container='app-container',
    tail_lines=100
)

print("Container logs:")
print(logs[:500])  # Print first 500 characters
```

**Output:**
```
Container logs:
2025-09-29 10:30:00 INFO Starting application server...
2025-09-29 10:30:01 INFO Database connection established
2025-09-29 10:30:01 INFO Redis cache connected
2025-09-29 10:30:02 INFO Listening on port 8000
2025-09-29 10:30:15 INFO Received request: GET /api/users
2025-09-29 10:30:15 INFO Response sent: 200 OK
```

---

### 6. List All Deployments

**Input:**
```python
# List deployments in a namespace
deployments = k8s.list_deployments('default')

print("Deployments in 'default' namespace:")
for dep in deployments:
    print(f"  - {dep}")
```

**Output:**
```
Deployments in 'default' namespace:
  - nginx-deployment
  - api-server
  - worker-service
```

---

### 7. Scale a Deployment

**Input:**
```python
# Scale deployment to 5 replicas
k8s.scale_deployment(
    name='nginx-deployment',
    namespace='default',
    replicas=5
)

# Scale down to 2 replicas
k8s.scale_deployment(
    name='api-server',
    namespace='default',
    replicas=2
)
```

**Output:**
```
[INFO] Scaled deployment nginx-deployment in default to 5 replicas
[INFO] Scaled deployment api-server in default to 2 replicas
```

---

### 8. Deploy from YAML Manifest (Deployment)

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.23
        ports:
        - containerPort: 80
```

**Input:**
```python
# Deploy the application
k8s.deploy_manifest(
    name='web-app',
    namespace='default',
    manifest_path='deployment.yaml'
)
```

**Output:**
```
[INFO] Deployed deployment web-app in default
```

---

### 9. Deploy a Service from YAML Manifest

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  selector:
    app: web
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
```

**Input:**
```python
# Create the service
k8s.deploy_manifest(
    name='web-service',
    namespace='default',
    manifest_path='service.yaml'
)
```

**Output:**
```
[INFO] Created service web-service in default
```

---

### 10. Delete a Deployment

**Input:**
```python
# Delete a deployment
k8s.delete_deployment(
    name='old-deployment',
    namespace='default'
)
```

**Output:**
```
[INFO] Deleted deployment old-deployment in default
```

---

### 11. List All Services

**Input:**
```python
# List services in a namespace
services = k8s.list_services('default')

print("Services in 'default' namespace:")
for svc in services:
    print(f"  - {svc}")
```

**Output:**
```
Services in 'default' namespace:
  - kubernetes
  - web-service
  - api-service
  - database-service
```

---

### 12. Get Service Details

**Input:**
```python
# Get detailed information about a service
service_info = k8s.get_service('web-service', 'default')

print(f"Service: {service_info['name']}")
print(f"Type: {service_info['type']}")
print(f"Cluster IP: {service_info['cluster_ip']}")
print("Ports:")
for port in service_info['ports']:
    print(f"  - Port: {port['port']} → Target: {port['target_port']}")
```

**Output:**
```
Service: web-service
Type: LoadBalancer
Cluster IP: 10.96.123.45
Ports:
  - Port: 80 → Target: 80
  - Port: 443 → Target: 443
```

---

### 13. Monitor Cluster Overview

**Input:**
```python
# Get a complete overview of the cluster
print("=== CLUSTER OVERVIEW ===\n")

# List all namespaces
namespaces = k8s.list_namespaces()
print(f"Total Namespaces: {len(namespaces)}")

for ns in namespaces:
    print(f"\n--- Namespace: {ns} ---")
    
    # Pods
    pods = k8s.list_pods(ns)
    print(f"  Pods: {len(pods)}")
    
    # Deployments
    deployments = k8s.list_deployments(ns)
    print(f"  Deployments: {len(deployments)}")
    
    # Services
    services = k8s.list_services(ns)
    print(f"  Services: {len(services)}")
```

**Output:**
```
=== CLUSTER OVERVIEW ===

Total Namespaces: 4

--- Namespace: default ---
  Pods: 8
  Deployments: 3
  Services: 4

--- Namespace: kube-system ---
  Pods: 12
  Deployments: 2
  Services: 2

--- Namespace: production ---
  Pods: 15
  Deployments: 5
  Services: 6

--- Namespace: staging ---
  Pods: 6
  Deployments: 2
  Services: 3
```

---

### 14. Deploy Complete Application Stack

**Input:**
```python
# Deploy a complete application with multiple components

# 1. Deploy database
k8s.deploy_manifest('postgres-db', 'default', 'manifests/postgres.yaml')

# 2. Deploy Redis cache
k8s.deploy_manifest('redis-cache', 'default', 'manifests/redis.yaml')

# 3. Deploy API backend
k8s.deploy_manifest('api-backend', 'default', 'manifests/api.yaml')

# 4. Deploy frontend
k8s.deploy_manifest('web-frontend', 'default', 'manifests/frontend.yaml')

# 5. Create services
k8s.deploy_manifest('api-service', 'default', 'manifests/api-service.yaml')
k8s.deploy_manifest('web-service', 'default', 'manifests/web-service.yaml')

print("\n✓ Application stack deployed successfully!")
```

**Output:**
```
[INFO] Deployed deployment postgres-db in default
[INFO] Deployed deployment redis-cache in default
[INFO] Deployed deployment api-backend in default
[INFO] Deployed deployment web-frontend in default
[INFO] Created service api-service in default
[INFO] Created service web-service in default

✓ Application stack deployed successfully!
```

---

### 15. Check Pod Status Across Namespaces

**Input:**
```python
# Check status of all pods in production namespace
print("Production Pod Status:")
print(f"{'Pod Name':<40} {'Status':<15} {'Node'}")
print("-" * 75)

pods = k8s.list_pods('production')
for pod in pods:
    print(f"{pod['name']:<40} {pod['status']:<15} {pod['node']}")
```

**Output:**
```
Production Pod Status:
Pod Name                                 Status          Node
---------------------------------------------------------------------------
api-server-5d8f9c7b6d-2xm4k             Running         worker-node-1
api-server-5d8f9c7b6d-7pk9m             Running         worker-node-2
api-server-5d8f9c7b6d-9ql2n             Running         worker-node-3
database-postgres-0                      Running         worker-node-1
cache-redis-6b9d8f4c5a-3vn7p            Running         worker-node-2
worker-celery-7c8e5d6f4b-4xm8p          Running         worker-node-3
worker-celery-7c8e5d6f4b-9zp2k          Running         worker-node-1
```

---

### 16. Scale Multiple Deployments

**Input:**
```python
# Scale multiple deployments for high traffic
deployments_to_scale = {
    'api-server': 10,
    'worker-service': 5,
    'cache-proxy': 3
}

print("Scaling deployments for high traffic...")
for deployment, replicas in deployments_to_scale.items():
    k8s.scale_deployment(deployment, 'production', replicas)
    print(f"  ✓ {deployment}: {replicas} replicas")

print("\nScaling complete!")
```

**Output:**
```
Scaling deployments for high traffic...
[INFO] Scaled deployment api-server in production to 10 replicas
  ✓ api-server: 10 replicas
[INFO] Scaled deployment worker-service in production to 5 replicas
  ✓ worker-service: 5 replicas
[INFO] Scaled deployment cache-proxy in production to 3 replicas
  ✓ cache-proxy: 3 replicas

Scaling complete!
```

---

### 17. Debug Application Issues

**Input:**
```python
# Debug a failing application

app_name = 'api-server'
namespace = 'production'

print(f"Debugging {app_name} in {namespace}...\n")

# 1. List all pods for the deployment
pods = k8s.list_pods(namespace)
app_pods = [p for p in pods if app_name in p['name']]

print(f"Found {len(app_pods)} pods:")
for pod in app_pods:
    print(f"  - {pod['name']}: {pod['status']}")

# 2. Get logs from each pod
print("\nFetching logs from pods...")
for pod in app_pods[:2]:  # Check first 2 pods
    print(f"\n--- Logs from {pod['name']} ---")
    logs = k8s.get_pod_logs(pod['name'], namespace, tail_lines=20)
    print(logs)
```

**Output:**
```
Debugging api-server in production...

Found 3 pods:
  - api-server-5d8f9c7b6d-2xm4k: Running
  - api-server-5d8f9c7b6d-7pk9m: CrashLoopBackOff
  - api-server-5d8f9c7b6d-9ql2n: Running

Fetching logs from pods...

--- Logs from api-server-5d8f9c7b6d-2xm4k ---
2025-09-29 10:45:00 INFO Server started on port 8000
2025-09-29 10:45:15 INFO Database connection healthy
2025-09-29 10:45:15 INFO Cache connection healthy
2025-09-29 10:45:30 INFO Processing request: GET /api/health

--- Logs from api-server-5d8f9c7b6d-7pk9m ---
2025-09-29 10:46:00 INFO Server starting...
2025-09-29 10:46:01 ERROR Failed to connect to database
2025-09-29 10:46:01 ERROR Connection refused at postgres:5432
2025-09-29 10:46:01 CRITICAL Exiting due to database connection error
```

---

### 18. List and Inspect Services

**Input:**
```python
# Get detailed information about all services
namespace = 'production'
services = k8s.list_services(namespace)

print(f"Services in '{namespace}' namespace:\n")

for svc_name in services:
    svc = k8s.get_service(svc_name, namespace)
    if svc:
        print(f"📦 {svc['name']}")
        print(f"   Type: {svc['type']}")
        print(f"   Cluster IP: {svc['cluster_ip']}")
        print(f"   Ports: {', '.join([f\"{p['port']}:{p['target_port']}\" for p in svc['ports']])}")
        print()
```

**Output:**
```
Services in 'production' namespace:

📦 api-service
   Type: ClusterIP
   Cluster IP: 10.96.45.123
   Ports: 8000:8000

📦 web-service
   Type: LoadBalancer
   Cluster IP: 10.96.45.124
   Ports: 80:80, 443:443

📦 database-service
   Type: ClusterIP
   Cluster IP: 10.96.45.125
   Ports: 5432:5432

📦 cache-service
   Type: ClusterIP
   Cluster IP: 10.96.45.126
   Ports: 6379:6379
```

---

### 19. Rolling Update Workflow

**Input:**
```python
# Perform a rolling update of an application

deployment_name = 'api-server'
namespace = 'production'

print(f"Rolling update for {deployment_name}...\n")

# 1. Check current state
deployments = k8s.list_deployments(namespace)
print(f"Current deployments: {', '.join(deployments)}")

# 2. Deploy new version
print(f"\nDeploying new version...")
k8s.deploy_manifest(deployment_name, namespace, 'manifests/api-v2.yaml')

# 3. Wait and verify
import time
time.sleep(5)

# 4. Check new pods
pods = k8s.list_pods(namespace)
api_pods = [p for p in pods if deployment_name in p['name']]
print(f"\nNew pods status:")
for pod in api_pods:
    print(f"  {pod['name']}: {pod['status']}")

# 5. Check logs to verify
print(f"\nVerifying deployment...")
logs = k8s.get_pod_logs(api_pods[0]['name'], namespace, tail_lines=10)
print(logs[:200])

print("\n✓ Rolling update complete!")
```

**Output:**
```
Rolling update for api-server...

Current deployments: api-server, worker-service, cache-proxy

Deploying new version...
[INFO] Deployed deployment api-server in production

New pods status:
  api-server-7f9d8c6b5a-3xk2m: Running
  api-server-7f9d8c6b5a-8zp5n: Running
  api-server-7f9d8c6b5a-4ym9p: Running

Verifying deployment...
2025-09-29 11:00:00 INFO API Server v2.0 starting...
2025-09-29 11:00:01 INFO New features enabled
2025-09-29 11:00:01 INFO Database connection established
2025-09-29 11:00:02 INFO Server ready on port 8000

✓ Rolling update complete!
```

---

### 20. Multi-Cluster Management

**Input:**
```python
# Manage multiple Kubernetes clusters

clusters = {
    'development': KubernetesManager(context='dev-cluster'),
    'staging': KubernetesManager(context='staging-cluster'),
    'production': KubernetesManager(context='prod-cluster')
}

print("Multi-Cluster Status Report\n")
print(f"{'Cluster':<15} {'Namespaces':<12} {'Total Pods':<12} {'Deployments'}")
print("-" * 60)

for cluster_name, k8s_client in clusters.items():
    namespaces = k8s_client.list_namespaces()
    
    total_pods = 0
    total_deployments = 0
    
    for ns in namespaces:
        pods = k8s_client.list_pods(ns)
        deployments = k8s_client.list_deployments(ns)
        total_pods += len(pods)
        total_deployments += len(deployments)
    
    print(f"{cluster_name:<15} {len(namespaces):<12} {total_pods:<12} {total_deployments}")
```

**Output:**
```
[INFO] KubernetesManager initialized
[INFO] KubernetesManager initialized
[INFO] KubernetesManager initialized
Multi-Cluster Status Report

Cluster         Namespaces   Total Pods   Deployments
------------------------------------------------------------
development     5            12           4
staging         6            25           8
production      8            47           15
```

---

## Error Handling Examples

### 21. Handling Missing Resources

**Input:**
```python
# Attempt to get logs from non-existent pod
logs = k8s.get_pod_logs('non-existent-pod', 'default')

if logs:
    print(logs)
else:
    print("No logs available - pod may not exist")

# Attempt to scale non-existent deployment
k8s.scale_deployment('missing-deployment', 'default', replicas=3)
```

**Output:**
```
[ERROR] Error getting logs for pod non-existent-pod: (404)
Reason: Not Found
No logs available - pod may not exist
[ERROR] Error scaling deployment missing-deployment: (404)
Reason: Not Found
```

---

## Common Manifest Templates

### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://postgres:5432/myapp"
```

### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

---

## Available Methods Summary

**Namespace Operations:**
- `list_namespaces()` - List all namespaces

**Pod Operations:**
- `list_pods(namespace)` - List pods in a namespace
- `get_pod_logs(name, namespace, container, tail_lines)` - Get pod logs

**Deployment Operations:**
- `list_deployments(namespace)` - List deployments
- `scale_deployment(name, namespace, replicas)` - Scale a deployment
- `deploy_manifest(name, namespace, manifest_path)` - Deploy from YAML
- `delete_deployment(name, namespace)` - Delete a deployment

**Service Operations:**
- `list_services(namespace)` - List services
- `get_service(name, namespace)` - Get service details