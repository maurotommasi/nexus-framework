# Nexus Docker Manager - Usage Examples

## Installation

```bash
pip install docker
```

## Quick Start

```python
from docker_manager import DockerManager

# Initialize the manager
mgr = DockerManager()

# List available templates
print(mgr.list_templates())
```

---

## Programmatic Examples

### 1. Basic Instance Creation

**Input:**
```python
from docker_manager import DockerManager

mgr = DockerManager()

# Create a Flask web application
container = mgr.create_instance('flask', name='my_flask_app', ports={5000: 8080})
```

**Output:**
```
[INFO] Pulling image pallets/flask:2.2 (may take a while)
[INFO] Created container my_flask_app (a1b2c3d4e5f6) from template 'flask'
```

---

### 2. List All Managed Instances

**Input:**
```python
instances = mgr.list_instances()

for inst in instances:
    print(f"Name: {inst.name}")
    print(f"  Template: {inst.template}")
    print(f"  Status: {inst.status}")
    print(f"  Image: {inst.image}")
    print(f"  Ports: {inst.ports}")
    print()
```

**Output:**
```
Name: my_flask_app
  Template: flask
  Status: running
  Image: pallets/flask:2.2
  Ports: {'5000/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '8080'}]}

Name: nexus_postgres_dev
  Template: postgres
  Status: running
  Image: postgres:15
  Ports: {'5432/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '5432'}]}
```

---

### 3. Create Database with Environment Variables

**Input:**
```python
# Create PostgreSQL database
postgres = mgr.create_instance(
    'postgres',
    name='prod_database',
    ports={5432: 5433},
    env={
        'POSTGRES_PASSWORD': 'securepass123',
        'POSTGRES_USER': 'admin',
        'POSTGRES_DB': 'myapp'
    }
)

print(f"Database created: {postgres.name}")
```

**Output:**
```
[INFO] Pulling image postgres:15 (may take a while)
[INFO] Created container prod_database (b2c3d4e5f6g7) from template 'postgres'
Database created: prod_database
```

---

### 4. Container Lifecycle Management

**Input:**
```python
# Stop a container
mgr.stop_instance('my_flask_app')

# Start a container
mgr.start_instance('my_flask_app')

# Restart a container
mgr.restart_instance('my_flask_app')

# Remove a container
mgr.remove_instance('my_flask_app', force=True)
```

**Output:**
```
[INFO] Stopped my_flask_app
[INFO] Started my_flask_app
[INFO] Restarted my_flask_app
[INFO] Removed my_flask_app
```

---

### 5. View Container Logs

**Input:**
```python
# Get last 50 lines of logs
logs = mgr.logs('my_flask_app', tail=50)
print(logs.decode('utf-8'))

# Stream logs in real-time
for line in mgr.logs('my_flask_app', stream=True):
    print(line.decode('utf-8'), end='')
```

**Output:**
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

---

### 6. Execute Commands Inside Container

**Input:**
```python
# Run a command inside the container
result = mgr.exec_in_instance('prod_database', ['psql', '-U', 'admin', '-c', 'SELECT version();'])

print(f"Exit Code: {result['exit_code']}")
print(f"Output: {result['output'].decode('utf-8')}")
```

**Output:**
```
Exit Code: 0
Output:                                                  version
-----------------------------------------------------------------------------------------------------------
 PostgreSQL 15.3 on x86_64-pc-linux-gnu, compiled by gcc (Debian 10.2.1-6) 10.2.1 20210110, 64-bit
(1 row)
```

---

### 7. Scale Applications

**Input:**
```python
# Create 3 instances of a Node.js app
containers = mgr.scale(
    'node',
    count=3,
    base_name='worker',
    ports={3000: None},  # Auto-assign host ports
    env={'NODE_ENV': 'production'}
)

for c in containers:
    print(f"Created: {c.name}")
```

**Output:**
```
[INFO] Created container worker-1 (c3d4e5f6g7h8) from template 'node'
[INFO] Created container worker-2 (d4e5f6g7h8i9) from template 'node'
[INFO] Created container worker-3 (e5f6g7h8i9j0) from template 'node'
Created: worker-1
Created: worker-2
Created: worker-3
```

---

### 8. Create Redis Cache with Volumes

**Input:**
```python
# Create Redis with persistent storage
redis = mgr.create_instance(
    'redis',
    name='cache_server',
    ports={6379: 6379},
    volumes={
        '/host/redis/data': {'bind': '/data', 'mode': 'rw'}
    }
)
```

**Output:**
```
[INFO] Pulling image redis:7-alpine (may take a while)
[INFO] Created container cache_server (f6g7h8i9j0k1) from template 'redis'
```

---

### 9. Custom Template Registration

**Input:**
```python
# Register a custom template
mgr.register_template(
    name='custom_api',
    image='mycompany/api:v1.2',
    expose={8000: 8000},
    env={'API_KEY': 'secret', 'DEBUG': 'false'},
    cmd='python main.py'
)

# Use the custom template
api = mgr.create_instance('custom_api', name='production_api')
```

**Output:**
```
[INFO] Registered template 'custom_api' -> mycompany/api:v1.2
[INFO] Pulling image mycompany/api:v1.2 (may take a while)
[INFO] Created container production_api (g7h8i9j0k1l2) from template 'custom_api'
```

---

### 10. Inspect Container Details

**Input:**
```python
# Get full container information
details = mgr.inspect_instance('my_flask_app')

print(f"ID: {details['Id']}")
print(f"Created: {details['Created']}")
print(f"State: {details['State']['Status']}")
print(f"IP Address: {details['NetworkSettings']['IPAddress']}")
```

**Output:**
```
ID: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
Created: 2025-09-29T10:30:45.123456789Z
State: running
IP Address: 172.17.0.2
```

---

### 11. Get Container Statistics

**Input:**
```python
# Get resource usage stats
stats = mgr.get_stats('my_flask_app', stream=False)

print(f"CPU Usage: {stats['cpu_stats']}")
print(f"Memory Usage: {stats['memory_stats']['usage'] / 1024 / 1024:.2f} MB")
```

**Output:**
```
CPU Usage: {'cpu_usage': {'total_usage': 1234567890}, 'system_cpu_usage': 9876543210, ...}
Memory Usage: 45.23 MB
```

---

### 12. List Instances by Template

**Input:**
```python
# Get all postgres instances
postgres_instances = mgr.list_instances(template='postgres')

print(f"Found {len(postgres_instances)} PostgreSQL instances:")
for inst in postgres_instances:
    print(f"  - {inst.name} ({inst.status})")
```

**Output:**
```
Found 2 PostgreSQL instances:
  - prod_database (running)
  - test_database (exited)
```

---

### 13. Search for Templates

**Input:**
```python
# Find templates matching a pattern
results = mgr.find_similar('node')
print(f"Templates matching 'node': {results}")

results = mgr.find_similar('data')
print(f"Templates matching 'data': {results}")
```

**Output:**
```
Templates matching 'node': ['node', 'express', 'nextjs']
Templates matching 'data': []
```

---

### 14. Clean Up Stopped Containers

**Input:**
```python
# Remove all stopped managed containers
removed = mgr.prune(remove_unused_images=True)

print(f"Removed {len(removed)} containers:")
for name in removed:
    print(f"  - {name}")
```

**Output:**
```
[INFO] Removed test_database
[INFO] Removed old_flask_app
Removed 2 containers:
  - test_database
  - old_flask_app
```

---

### 15. Build Custom Image

**Input:**
```python
# Build an image from a Dockerfile
image = mgr.build_image(
    path='/path/to/dockerfile/directory',
    tag='myapp:latest',
    dockerfile='Dockerfile',
    buildargs={'VERSION': '1.0'}
)

print(f"Built image: {image.tags}")
```

**Output:**
```
[INFO] Built image myapp:latest
Built image: ['myapp:latest']
```

---

### 16. Export and Import Containers

**Input:**
```python
# Export a container as a tarball
mgr.export_instance('my_flask_app', '/tmp/flask_backup.tar')

# Import an image from tarball
images = mgr.import_image('/tmp/flask_backup.tar', tag='flask:backup')
```

**Output:**
```
[INFO] Exported my_flask_app to /tmp/flask_backup.tar
```

---

### 17. Multi-Service Setup (Microservices)

**Input:**
```python
# Create a complete microservices stack
services = {
    'web': mgr.create_instance('nginx', name='web_gateway', ports={80: 8080}),
    'api': mgr.create_instance('fastapi', name='api_service', ports={80: 8000}),
    'cache': mgr.create_instance('redis', name='cache_layer', ports={6379: 6379}),
    'db': mgr.create_instance('postgres', name='database', ports={5432: 5432}),
    'queue': mgr.create_instance('rabbitmq', name='message_queue', ports={5672: 5672})
}

print("Microservices stack created:")
for name, container in services.items():
    print(f"  {name}: {container.name} ({container.status})")
```

**Output:**
```
[INFO] Created container web_gateway (h8i9j0k1l2m3) from template 'nginx'
[INFO] Created container api_service (i9j0k1l2m3n4) from template 'fastapi'
[INFO] Created container cache_layer (j0k1l2m3n4o5) from template 'redis'
[INFO] Created container database (k1l2m3n4o5p6) from template 'postgres'
[INFO] Created container message_queue (l2m3n4o5p6q7) from template 'rabbitmq'
Microservices stack created:
  web: web_gateway (running)
  api: api_service (running)
  cache: cache_layer (running)
  db: database (running)
  queue: message_queue (running)
```

---

### 18. Monitor Multiple Containers

**Input:**
```python
# Monitor all running instances
instances = mgr.list_instances()

print(f"{'Container':<20} {'Template':<15} {'Status':<10} {'Ports'}")
print("-" * 70)

for inst in instances:
    ports_str = ', '.join([f"{k}→{v}" for k, v in (inst.ports or {}).items()])
    print(f"{inst.name:<20} {inst.template:<15} {inst.status:<10} {ports_str}")
```

**Output:**
```
Container            Template        Status     Ports
----------------------------------------------------------------------
web_gateway          nginx           running    80/tcp→8080
api_service          fastapi         running    80/tcp→8000
cache_layer          redis           running    6379/tcp→6379
database             postgres        running    5432/tcp→5432
message_queue        rabbitmq        running    5672/tcp→5672, 15672/tcp→15672
```

---

### 19. Complete Application Example

**Input:**
```python
from docker_manager import DockerManager
import time

# Initialize manager
mgr = DockerManager(base_namespace="myapp", auto_pull=True)

# Create development environment
print("Setting up development environment...")

# Database
db = mgr.create_instance(
    'postgres',
    name='myapp_db_dev',
    ports={5432: 5432},
    env={'POSTGRES_PASSWORD': 'dev123', 'POSTGRES_DB': 'myapp'}
)

# Cache
cache = mgr.create_instance('redis', name='myapp_cache_dev', ports={6379: 6379})

# API
api = mgr.create_instance(
    'fastapi',
    name='myapp_api_dev',
    ports={80: 8000},
    env={
        'DATABASE_URL': 'postgresql://postgres:dev123@localhost:5432/myapp',
        'REDIS_URL': 'redis://localhost:6379'
    }
)

print("\n✓ Development environment ready!")
print(f"  Database: localhost:5432")
print(f"  Cache: localhost:6379")
print(f"  API: http://localhost:8000")

# Wait a moment
time.sleep(2)

# Check status
print("\nStatus check:")
for name in ['myapp_db_dev', 'myapp_cache_dev', 'myapp_api_dev']:
    inst = mgr.inspect_instance(name)
    status = inst['State']['Status']
    print(f"  {name}: {status}")
```

**Output:**
```
Setting up development environment...
[INFO] Pulling image postgres:15 (may take a while)
[INFO] Created container myapp_db_dev (m3n4o5p6q7r8) from template 'postgres'
[INFO] Pulling image redis:7-alpine (may take a while)
[INFO] Created container myapp_cache_dev (n4o5p6q7r8s9) from template 'redis'
[INFO] Pulling image tiangolo/uvicorn-gunicorn-fastapi:python3.9 (may take a while)
[INFO] Created container myapp_api_dev (o5p6q7r8s9t0) from template 'fastapi'

✓ Development environment ready!
  Database: localhost:5432
  Cache: localhost:6379
  API: http://localhost:8000

Status check:
  myapp_db_dev: running
  myapp_cache_dev: running
  myapp_api_dev: running
```

---

## Available Templates

The manager includes 24 pre-configured templates:

- **Web Frameworks**: flask, django, fastapi, node, express, nextjs, rails, springboot, dotnet, php_laravel
- **Databases**: postgres, mysql, mongo
- **Caching/Queuing**: redis, rabbitmq, celery, elasticsearch
- **Servers**: nginx, traefik
- **Monitoring**: prometheus, grafana
- **CMS**: wordpress, ghost
- **Languages**: golang

Use `mgr.list_templates()` to see all available templates.