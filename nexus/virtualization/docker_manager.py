"""
Nexus Docker Manager

A single-file Python class that creates, manages and runs Docker containers based on
predefined templates. Designed to manage multiple instances and retrieve container
information from the Docker Engine so that instances can be properly managed.

Requirements:
    pip install docker

Usage example:
    from docker_manager import DockerManager
    mgr = DockerManager()
    mgr.create_instance('flask', name='web1', ports={5000:5001})
    mgr.list_instances()

Templates: includes at least 20 common templates (flask, django, fastapi, node, express,
rails, golang, springboot, dotnet, php_laravel, nginx, redis, postgres, mysql, mongo,
elasticsearch, rabbitmq, celery, prometheus, grafana, traefik, wordpress, ghost, nextjs)

Managed containers are labeled with: nexus_cli_managed=true and nexus_template=<template>
"""
from __future__ import annotations
import time
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Any

try:
    import docker
    from docker.models.containers import Container
    from docker.errors import NotFound, APIError
except Exception as e:
    raise RuntimeError("Missing dependency: install 'docker' Python package (pip install docker)") from e

logger = logging.getLogger("NexusDockerManager")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(ch)

MANAGED_LABEL = "nexus_cli_managed"
TEMPLATE_LABEL = "nexus_template"

@dataclass
class InstanceInfo:
    id: str
    name: str
    template: Optional[str]
    image: str
    status: str
    ports: Dict[str, Any]
    env: Dict[str, Any]
    created: str


class DockerManager:
    """Manage Docker containers using templates.

    - Maintains a built-in template registry (>=20 templates)
    - Creates containers with a label so they can be discovered and managed
    - Provides common lifecycle operations and inspection methods
    """

    def __init__(self, base_namespace: str = "nexus", auto_pull: bool = True, timeout: int = 30):
        self.client = docker.from_env()
        self.api = docker.APIClient(base_url='unix://var/run/docker.sock')
        self.base_namespace = base_namespace
        self.auto_pull = auto_pull
        self.timeout = timeout
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._register_default_templates()

    # -------------------- Templates --------------------
    def _register_default_templates(self):
        """Register a set of common templates. Each template describes an image and defaults."""
        defaults = {
            # Web frameworks
            "flask": {"image": "pallets/flask:2.2", "expose": {5000: 5000}, "cmd": None},
            "django": {"image": "django:latest", "expose": {8000: 8000}, "cmd": "gunicorn app.wsgi:application -b 0.0.0.0:8000"},
            "fastapi": {"image": "tiangolo/uvicorn-gunicorn-fastapi:python3.9", "expose": {80: 8000}},
            "node": {"image": "node:18", "expose": {3000:3000}, "cmd": "npm start"},
            "express": {"image": "node:18", "expose": {3000:3000}, "cmd": "node server.js"},
            "nextjs": {"image": "node:18", "expose": {3000:3000}, "cmd": "npm start"},
            "ghost": {"image": "ghost:5-alpine", "expose": {2368:2368}},
            "wordpress": {"image": "wordpress:php8.1-fpm", "expose": {80:80}},
            # Backend / languages
            "rails": {"image": "ruby:3.2", "expose": {3000:3000}, "cmd": "rails server -b 0.0.0.0"},
            "golang": {"image": "golang:1.20", "expose": {}},
            "springboot": {"image": "openjdk:17-jdk-slim", "expose": {8080:8080}},
            "dotnet": {"image": "mcr.microsoft.com/dotnet/aspnet:7.0", "expose": {80:80}},
            "php_laravel": {"image": "php:8.1-fpm", "expose": {9000:9000}},
            # Databases / caches / brokers
            "redis": {"image": "redis:7-alpine", "expose": {6379:6379}},
            "postgres": {"image": "postgres:15", "expose": {5432:5432}, "env": {"POSTGRES_PASSWORD": "password"}},
            "mysql": {"image": "mysql:8", "expose": {3306:3306}, "env": {"MYSQL_ROOT_PASSWORD": "password"}},
            "mongo": {"image": "mongo:6", "expose": {27017:27017}},
            "elasticsearch": {"image": "docker.elastic.co/elasticsearch/elasticsearch:8.6.3", "expose": {9200:9200}, "env": {"discovery.type": "single-node"}},
            "rabbitmq": {"image": "rabbitmq:3-management", "expose": {5672:5672, 15672:15672}},
            "celery": {"image": "celery:latest", "expose": {}},
            # Monitoring / reverse proxies
            "prometheus": {"image": "prom/prometheus:latest", "expose": {9090:9090}},
            "grafana": {"image": "grafana/grafana:latest", "expose": {3000:3000}},
            "traefik": {"image": "traefik:v2.10", "expose": {80:80, 8080:8080}},
            "nginx": {"image": "nginx:stable-alpine", "expose": {80:80}},
        }

        # Ensure at least 20 unique templates
        for k, v in defaults.items():
            self.templates[k] = v

    def register_template(self, name: str, image: str, expose: Optional[Dict[int,int]] = None, env: Optional[Dict[str,str]] = None, cmd: Optional[str] = None):
        """Register a new template at runtime."""
        self.templates[name] = {"image": image, "expose": expose or {}, "env": env or {}, "cmd": cmd}
        logger.info(f"Registered template '{name}' -> {image}")

    def list_templates(self) -> List[str]:
        return sorted(list(self.templates.keys()))

    # -------------------- Discovery --------------------
    def discover_managed_instances(self) -> List[InstanceInfo]:
        """Discover containers labeled as managed by this system."""
        containers = self.client.containers.list(all=True, filters={"label": f"{MANAGED_LABEL}=true"})
        result: List[InstanceInfo] = []
        for c in containers:
            meta = c.attrs
            tpl = meta.get('Config', {}).get('Labels', {}).get(TEMPLATE_LABEL)
            ports = meta.get('NetworkSettings', {}).get('Ports') or {}
            envlist = meta.get('Config', {}).get('Env') or []
            env = {k: v for k, v in (item.split('=', 1) for item in envlist)} if envlist else {}
            info = InstanceInfo(
                id=c.id,
                name=c.name,
                template=tpl,
                image=meta.get('Config', {}).get('Image', ''),
                status=c.status,
                ports=ports,
                env=env,
                created=meta.get('Created')
            )
            result.append(info)
        return result

    # -------------------- Lifecycle --------------------
    def create_instance(self, template: str, name: Optional[str] = None, ports: Optional[Dict[int,int]] = None,
                        env: Optional[Dict[str,str]] = None, volumes: Optional[Dict[str, Dict[str,str]]] = None,
                        command: Optional[Any] = None, detach: bool = True, labels: Optional[Dict[str,str]] = None, **kwargs) -> Container:
        """Create a container from a template.

        - template: template name registered in self.templates
        - name: container name (if None, autogenerated)
        - ports: mapping container_port:host_port
        - env: environment variables
        - volumes: docker volumes mapping {host_path: {'bind': container_path, 'mode': 'rw'}}
        - command: override command
        - labels: additional labels
        """
        if template not in self.templates:
            raise ValueError(f"Unknown template '{template}'. Available: {list(self.templates.keys())}")

        tpl = self.templates[template]
        image = tpl.get('image')
        tpl_env = tpl.get('env', {})
        tpl_expose = tpl.get('expose', {})
        tpl_cmd = tpl.get('cmd')

        # Merge provided with template
        final_env = {**tpl_env, **(env or {})}
        final_ports = {**tpl_expose, **(ports or {})}

        # Pull image if missing
        if self.auto_pull:
            try:
                logger.info(f"Pulling image {image} (may take a while)")
                self.client.images.pull(image)
            except Exception as e:
                logger.warning(f"Could not pull image {image}: {e}")

        lbls = {MANAGED_LABEL: "true", TEMPLATE_LABEL: template}
        if labels:
            lbls.update(labels)

        cname = name or f"{self.base_namespace}_{template}_{int(time.time())}"

        try:
            container = self.client.containers.run(
                image=image,
                name=cname,
                command=command or tpl_cmd,
                environment=final_env,
                ports=final_ports or None,
                volumes=volumes or None,
                detach=detach,
                labels=lbls,
                **kwargs,
            )
            logger.info(f"Created container {container.name} ({container.id[:12]}) from template '{template}'")
            return container
        except APIError as e:
            raise RuntimeError(f"Docker API error creating container: {e.explanation}")
        except Exception as e:
            raise RuntimeError(f"Error creating container: {e}")

    def start_instance(self, name_or_id: str) -> None:
        c = self._get_container(name_or_id)
        c.start()
        logger.info(f"Started {c.name}")

    def stop_instance(self, name_or_id: str, timeout: Optional[int] = None) -> None:
        c = self._get_container(name_or_id)
        c.stop(timeout=timeout or self.timeout)
        logger.info(f"Stopped {c.name}")

    def restart_instance(self, name_or_id: str, timeout: Optional[int] = None) -> None:
        c = self._get_container(name_or_id)
        c.restart(timeout=timeout or self.timeout)
        logger.info(f"Restarted {c.name}")

    def remove_instance(self, name_or_id: str, force: bool = False) -> None:
        c = self._get_container(name_or_id)
        c.remove(force=force)
        logger.info(f"Removed {c.name}")

    # -------------------- Utilities --------------------
    def list_instances(self, template: Optional[str] = None) -> List[InstanceInfo]:
        all_instances = self.discover_managed_instances()
        if template:
            return [i for i in all_instances if i.template == template]
        return all_instances

    def inspect_instance(self, name_or_id: str) -> Dict[str, Any]:
        c = self._get_container(name_or_id)
        return c.attrs

    def logs(self, name_or_id: str, tail: int = 200, stream: bool = False, since: Optional[int] = None):
        c = self._get_container(name_or_id)
        return c.logs(tail=tail, stream=stream, since=since)

    def exec_in_instance(self, name_or_id: str, cmd: List[str], workdir: Optional[str] = None, user: Optional[str] = None, demux: bool = False) -> Dict[str, Any]:
        c = self._get_container(name_or_id)
        exec_res = c.exec_run(cmd, workdir=workdir, user=user, demux=demux)
        return {"exit_code": exec_res.exit_code, "output": exec_res.output}

    def get_stats(self, name_or_id: str, stream: bool = False):
        c = self._get_container(name_or_id)
        return c.stats(stream=stream)

    def scale(self, template: str, count: int, base_name: Optional[str] = None, start_index: int = 1, **kwargs) -> List[Container]:
        """Create `count` instances of a template. Names will be base_name-1, base_name-2, ..."""
        created = []
        bname = base_name or f"{self.base_namespace}_{template}"
        for i in range(start_index, start_index + count):
            name = f"{bname}-{i}"
            c = self.create_instance(template, name=name, **kwargs)
            created.append(c)
        return created

    def find_similar(self, name_fragment: str) -> List[str]:
        all_keys = list(self.templates.keys())
        return [k for k in all_keys if name_fragment.lower() in k.lower()]

    def prune(self, remove_unused_images: bool = False):
        """Remove stopped managed containers and optionally unused images."""
        managed = self.list_instances()
        removed = []
        for info in managed:
            if info.status in ("exited", "created"):
                try:
                    self.remove_instance(info.id, force=True)
                    removed.append(info.name)
                except Exception as e:
                    logger.warning(f"Could not remove {info.name}: {e}")
        if remove_unused_images:
            self.client.images.prune()
        return removed

    # -------------------- Helpers --------------------
    def _get_container(self, name_or_id: str) -> Container:
        try:
            return self.client.containers.get(name_or_id)
        except NotFound:
            raise ValueError(f"Container '{name_or_id}' not found")

    def pull_image(self, image: str):
        try:
            return self.client.images.pull(image)
        except Exception as e:
            raise RuntimeError(f"Error pulling image {image}: {e}")

    def build_image(self, path: str, tag: str, dockerfile: str = 'Dockerfile', rm: bool = True, buildargs: Optional[Dict[str,str]] = None):
        """Build an image from a Dockerfile on disk."""
        try:
            image, logs = self.client.images.build(path=path, tag=tag, dockerfile=dockerfile, rm=rm, buildargs=buildargs or {})
            logger.info(f"Built image {tag}")
            return image
        except Exception as e:
            raise RuntimeError(f"Error building image: {e}")

    def export_instance(self, name_or_id: str, output_path: str):
        c = self._get_container(name_or_id)
        stream = c.export()
        with open(output_path, 'wb') as f:
            for chunk in stream:
                f.write(chunk)
        logger.info(f"Exported {name_or_id} to {output_path}")

    def import_image(self, tar_path: str, tag: Optional[str] = None):
        with open(tar_path, 'rb') as f:
            res = self.client.images.load(f.read())
        if tag:
            # optionally retag
            for img in res:
                try:
                    img.tag(tag)
                except Exception:
                    pass
        return res

    def snapshot_image(self, image_name: str, output_path: str):
        image = self.client.images.get(image_name)
        with open(output_path, "wb") as f:
            for chunk in image.save(named=True):
                f.write(chunk)
            return output_path

if __name__ == '__main__':
    # Quick demo (will connect to local Docker)
    mgr = DockerManager()
    print("Templates available:", mgr.list_templates())
    print("Existing managed instances:")
    for inst in mgr.list_instances():
        print(asdict(inst))

    # Example: create a temporary flask container (will pull image if needed)
    # Uncomment to run (careful: will start containers on your machine)
    # ctr = mgr.create_instance('flask', name='nexus_flask_demo', ports={5000:5000})
    # print('Created:', ctr.name)
