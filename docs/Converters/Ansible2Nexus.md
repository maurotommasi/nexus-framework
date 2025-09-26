# Ansible to Nexus Pipeline Converter - Usage Guide

A practical guide for converting Ansible playbooks to Nexus Enterprise Pipeline Management System configurations.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Real-World Examples](#real-world-examples)
- [Configuration Options](#configuration-options)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Quick Start

### Installation

```python
# Save the converter code to: ansible_to_nexus_converter.py
# Then import it in your project:

from ansible_to_nexus_converter import convert_ansible_playbook, ConversionOptions
```

### Convert Your First Playbook

```python
# Simple one-line conversion
config = convert_ansible_playbook("my-playbook.yml", "nexus-pipeline.yaml")
```

That's it! Your Ansible playbook is now converted to a Nexus Pipeline configuration.

## Basic Usage

### Method 1: File-to-File Conversion

```python
from ansible_to_nexus_converter import convert_ansible_playbook

# Convert playbook file and save result
converted_config = convert_ansible_playbook(
    playbook_path="deploy-app.yml",
    output_path="nexus-deploy-app.yaml"
)

print("Conversion completed! Check nexus-deploy-app.yaml")
```

### Method 2: Using the Converter Class

```python
from ansible_to_nexus_converter import AnsibleToNexusConverter

# Create converter instance
converter = AnsibleToNexusConverter()

# Convert from file
config = converter.convert_playbook_file("my-playbook.yml")

# Save the result
converter.save_pipeline_config(config, "output.yaml")

# View conversion report
print(converter.generate_conversion_report())
```

### Method 3: Convert from Python Dictionary

```python
# If you have playbook data as Python dict
playbook_data = [
    {
        "name": "My Play",
        "hosts": "servers",
        "tasks": [
            {
                "name": "Install nginx",
                "apt": {"name": "nginx", "state": "present"}
            }
        ]
    }
]

converter = AnsibleToNexusConverter()
config = converter.convert_playbook(playbook_data, "my-pipeline")
```

## Advanced Usage

### Custom Configuration Options

```python
from ansible_to_nexus_converter import AnsibleToNexusConverter, ConversionOptions

# Configure conversion behavior
options = ConversionOptions(
    include_comments=True,      # Keep original Ansible tasks as comments
    convert_handlers=True,      # Convert handlers to pipeline steps
    convert_variables=True,     # Map variables to environment vars
    parallel_tasks=True,        # Enable parallel execution where safe
    default_timeout=600,        # 10-minute timeout for steps
    default_retry_count=2       # Retry failed steps twice
)

converter = AnsibleToNexusConverter(options)
config = converter.convert_playbook_file("complex-playbook.yml")
```

### Batch Conversion

```python
import os
from pathlib import Path

def convert_multiple_playbooks(playbooks_dir, output_dir):
    """Convert all YAML files in a directory"""
    
    converter = AnsibleToNexusConverter()
    
    for playbook_file in Path(playbooks_dir).glob("*.yml"):
        print(f"Converting {playbook_file.name}...")
        
        try:
            config = converter.convert_playbook_file(playbook_file)
            
            output_file = Path(output_dir) / f"nexus-{playbook_file.stem}.yaml"
            converter.save_pipeline_config(config, output_file)
            
            print(f"✓ Saved: {output_file}")
            
        except Exception as e:
            print(f"✗ Failed to convert {playbook_file.name}: {e}")

# Convert all playbooks
convert_multiple_playbooks("./ansible-playbooks", "./nexus-pipelines")
```

## Real-World Examples

### Example 1: Web Application Deployment

**Input Ansible Playbook (deploy-webapp.yml):**

```yaml
---
- name: Deploy Web Application
  hosts: webservers
  become: yes
  vars:
    app_name: "mywebapp"
    app_version: "v1.2.3"
    app_port: 8080
    deploy_path: "/opt/{{ app_name }}"
    
  tasks:
    - name: Install system packages
      apt:
        name: 
          - nginx
          - nodejs
          - npm
        state: present
        update_cache: yes

    - name: Create application user
      user:
        name: "{{ app_name }}"
        system: yes
        home: "{{ deploy_path }}"

    - name: Create application directory
      file:
        path: "{{ deploy_path }}"
        state: directory
        owner: "{{ app_name }}"
        mode: '0755'

    - name: Clone application repository
      git:
        repo: "https://github.com/company/{{ app_name }}.git"
        dest: "{{ deploy_path }}/src"
        version: "{{ app_version }}"
      notify: restart app

    - name: Install Node.js dependencies
      npm:
        path: "{{ deploy_path }}/src"
        state: present
      become_user: "{{ app_name }}"

    - name: Build application
      shell: npm run build
      args:
        chdir: "{{ deploy_path }}/src"
      become_user: "{{ app_name }}"

    - name: Configure nginx
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-available/{{ app_name }}
      notify: reload nginx

    - name: Enable nginx site
      file:
        src: /etc/nginx/sites-available/{{ app_name }}
        dest: /etc/nginx/sites-enabled/{{ app_name }}
        state: link
      notify: reload nginx

    - name: Start application service
      systemd:
        name: "{{ app_name }}"
        state: started
        enabled: yes

  handlers:
    - name: restart app
      systemd:
        name: "{{ app_name }}"
        state: restarted

    - name: reload nginx
      systemd:
        name: nginx
        state: reloaded
```

**Conversion:**

```python
from ansible_to_nexus_converter import convert_ansible_playbook

# Convert with custom options
config = convert_ansible_playbook(
    playbook_path="deploy-webapp.yml",
    output_path="nexus-webapp-deployment.yaml"
)

print("Web application deployment playbook converted!")
```

**Output Nexus Pipeline (nexus-webapp-deployment.yaml):**

```yaml
name: deploy-web-application
version: 1.0.0
description: Converted from Ansible playbook
environment:
  APP_NAME: mywebapp
  APP_VERSION: v1.2.3
  APP_PORT: '8080'
  DEPLOY_PATH: /opt/mywebapp
max_parallel_jobs: 5
artifacts_retention: 30

steps:
  - name: play_1_install_system_packages
    command: apt-get update && apt-get install -y nginx nodejs npm
    working_dir: "."
    timeout: 300
    retry_count: 0
    environment: {}
    depends_on: []
    condition: null
    parallel: false
    critical: true
    artifacts: []

  - name: play_1_create_application_user
    command: "# TODO: Convert user module manually - Args: --name mywebapp --system True --home /opt/mywebapp"
    working_dir: "."
    timeout: 300
    depends_on: [play_1_install_system_packages]

  - name: play_1_create_application_directory
    command: mkdir -p /opt/mywebapp && chown mywebapp /opt/mywebapp && chmod 0755 /opt/mywebapp
    working_dir: "."
    timeout: 300
    depends_on: [play_1_create_application_user]

  - name: play_1_clone_application_repository
    command: git clone https://github.com/company/mywebapp.git /opt/mywebapp/src
    working_dir: "."
    timeout: 300
    depends_on: [play_1_create_application_directory]

  - name: play_1_install_node_js_dependencies
    command: npm install
    working_dir: "/opt/mywebapp/src"
    timeout: 300
    depends_on: [play_1_clone_application_repository]

  - name: play_1_build_application
    command: npm run build
    working_dir: "/opt/mywebapp/src"
    timeout: 300
    depends_on: [play_1_install_node_js_dependencies]

  - name: play_1_configure_nginx
    command: "# TODO: Convert template module manually - Args: --src nginx.conf.j2 --dest /etc/nginx/sites-available/mywebapp"
    working_dir: "."
    timeout: 300
    depends_on: [play_1_build_application]

  - name: play_1_enable_nginx_site
    command: ln -s /etc/nginx/sites-available/mywebapp /etc/nginx/sites-enabled/mywebapp
    timeout: 300
    depends_on: [play_1_configure_nginx]

  - name: play_1_start_application_service
    command: systemctl started mywebapp
    timeout: 300
    depends_on: [play_1_enable_nginx_site]

  # Converted handlers
  - name: handler_1_restart_app
    command: systemctl restarted mywebapp
    parallel: false

  - name: handler_2_reload_nginx
    command: systemctl reloaded nginx
    parallel: false
```

### Example 2: Docker Application with Database

**Input Ansible Playbook (docker-app.yml):**

```yaml
---
- name: Deploy Containerized Application
  hosts: docker_hosts
  vars:
    app_name: "api-service"
    db_password: "{{ vault_db_password }}"
    
  tasks:
    - name: Create application network
      docker_network:
        name: "{{ app_name }}-network"

    - name: Start PostgreSQL database
      docker_container:
        name: "{{ app_name }}-db"
        image: postgres:13
        state: started
        env:
          POSTGRES_DB: "{{ app_name }}"
          POSTGRES_PASSWORD: "{{ db_password }}"
        volumes:
          - "{{ app_name }}-db-data:/var/lib/postgresql/data"
        networks:
          - name: "{{ app_name }}-network"

    - name: Wait for database to be ready
      wait_for:
        port: 5432
        host: "{{ app_name }}-db"
        delay: 10

    - name: Start application container
      docker_container:
        name: "{{ app_name }}"
        image: "myregistry/{{ app_name }}:latest"
        state: started
        ports:
          - "8080:8080"
        env:
          DATABASE_URL: "postgresql://postgres:{{ db_password }}@{{ app_name }}-db/{{ app_name }}"
        networks:
          - name: "{{ app_name }}-network"
        restart_policy: always

    - name: Run database migrations
      docker_container:
        name: "{{ app_name }}-migrate"
        image: "myregistry/{{ app_name }}:latest"
        command: ["python", "manage.py", "migrate"]
        env:
          DATABASE_URL: "postgresql://postgres:{{ db_password }}@{{ app_name }}-db/{{ app_name }}"
        networks:
          - name: "{{ app_name }}-network"
        detach: false
        cleanup: yes
```

**Conversion:**

```python
# Convert with focus on Docker operations
options = ConversionOptions(
    parallel_tasks=False,  # Keep sequential for database dependencies
    default_timeout=600,   # Longer timeout for container operations
    convert_variables=True
)

config = convert_ansible_playbook(
    playbook_path="docker-app.yml",
    output_path="nexus-docker-app.yaml",
    options=options
)
```

### Example 3: Multi-Environment Deployment

**Conversion Script:**

```python
from ansible_to_nexus_converter import AnsibleToNexusConverter, ConversionOptions

def convert_for_environment(env_name):
    """Convert playbook for specific environment"""
    
    options = ConversionOptions(
        include_comments=True,
        convert_handlers=True,
        parallel_tasks=(env_name == "production"),  # Parallel only in prod
        default_timeout=900 if env_name == "production" else 300
    )
    
    converter = AnsibleToNexusConverter(options)
    
    # Convert main playbook
    config = converter.convert_playbook_file(f"deploy-{env_name}.yml")
    
    # Customize for environment
    config["name"] = f"deploy-to-{env_name}"
    config["environment"]["TARGET_ENV"] = env_name.upper()
    
    # Save environment-specific config
    converter.save_pipeline_config(
        config, 
        f"nexus-deploy-{env_name}.yaml"
    )
    
    print(f"✓ Converted for {env_name} environment")
    return config

# Convert for all environments
environments = ["development", "staging", "production"]
for env in environments:
    convert_for_environment(env)
```

## Configuration Options

### ConversionOptions Reference

```python
options = ConversionOptions(
    # Include original Ansible tasks as comments in output
    include_comments=True,
    
    # Convert Ansible handlers to pipeline steps  
    convert_handlers=True,
    
    # Map Ansible variables to pipeline environment variables
    convert_variables=True,
    
    # Enable parallel execution of independent tasks
    parallel_tasks=False,
    
    # Default timeout for pipeline steps (seconds)
    default_timeout=300,
    
    # Default number of retry attempts for failed steps
    default_retry_count=0,
    
    # Maintain structure and naming from original playbook
    preserve_ansible_structure=True
)
```

### When to Use Each Option

| Scenario | Recommended Settings |
|----------|---------------------|
| **Development/Testing** | `include_comments=True, parallel_tasks=False, default_timeout=300` |
| **Production** | `include_comments=False, parallel_tasks=True, default_timeout=600, default_retry_count=2` |
| **CI/CD Integration** | `convert_handlers=False, preserve_ansible_structure=False` |
| **Complex Playbooks** | `include_comments=True, convert_handlers=True, parallel_tasks=False` |

## Troubleshooting

### Common Issues and Solutions

#### 1. Module Not Supported

**Error:** `Warning: Unknown module 'my_custom_module'`

**Solution:**
```python
# Add custom module mapping before conversion
converter = AnsibleToNexusConverter()

# Add your custom module mapping
converter.module_mappings['my_custom_module'] = lambda args: f"./scripts/my_script.sh {args.get('param1', '')}"

config = converter.convert_playbook_file("playbook.yml")
```

#### 2. Complex Variable Substitution

**Issue:** Ansible variables like `{{ item.name }}` don't convert properly.

**Solution:** Pre-process playbook or manually adjust after conversion:
```python
# After conversion, manually replace complex variables
config = converter.convert_playbook_file("playbook.yml")

# Find and replace complex variable patterns
for step in config['steps']:
    step['command'] = step['command'].replace('{{ item.name }}', '${ITEM_NAME}')
```

#### 3. File Encoding Issues

**Error:** `UnicodeDecodeError` when reading playbook

**Solution:**
```python
# Specify encoding explicitly
with open("playbook.yml", 'r', encoding='utf-8') as f:
    playbook_data = yaml.safe_load(f)

converter = AnsibleToNexusConverter()
config = converter.convert_playbook(playbook_data)
```

### Debugging Conversions

Enable detailed logging:

```python
converter = AnsibleToNexusConverter()

# Convert with detailed logging
config = converter.convert_playbook_file("debug-playbook.yml")

# Review conversion log
for message in converter.conversion_log:
    print(f"LOG: {message}")

# Generate detailed report
print(converter.generate_conversion_report())
```

## Best Practices

### 1. Pre-Conversion Preparation

```bash
# Validate Ansible playbook syntax before conversion
ansible-playbook --syntax-check my-playbook.yml

# Test playbook in check mode
ansible-playbook --check my-playbook.yml
```

### 2. Post-Conversion Review

```python
# Always review converted configuration
config = convert_ansible_playbook("playbook.yml")

# Check for TODO comments that need manual attention
for step in config['steps']:
    if 'TODO' in step['command']:
        print(f"Manual conversion needed: {step['name']}")
        print(f"Command: {step['command']}")
```

### 3. Test Converted Pipelines

```python
# Create test version of converted pipeline
from framework.devops.pipeline import Pipeline

# Load converted configuration
pipeline = Pipeline("test-conversion")
pipeline.load_config("nexus-converted.yaml")

# Validate configuration
errors = pipeline.validate_config()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✓ Configuration is valid")
```

### 4. Version Control Integration

```python
# Add conversion metadata for tracking
def convert_with_metadata(playbook_path):
    import datetime
    
    config = convert_ansible_playbook(playbook_path)
    
    # Add conversion tracking
    config['metadata'] = {
        'converted_from': playbook_path,
        'conversion_date': datetime.datetime.now().isoformat(),
        'converter_version': '1.0.0',
        'review_required': True
    }
    
    return config
```

### 5. Gradual Migration Strategy

1. **Convert in phases:** Start with simple playbooks
2. **Test thoroughly:** Validate each converted pipeline
3. **Maintain both:** Keep Ansible playbooks during transition
4. **Document changes:** Track what required manual conversion
5. **Train team:** Ensure team understands Nexus Pipeline format

This comprehensive guide should help you convert your Ansible playbooks to Nexus Pipeline configurations efficiently and safely.