import os
import sys
import subprocess
import platform
import psutil
import socket
import requests
from typing import Dict, List, Optional, Any
import time

class SystemUtils:
    """System information and operations utility."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'hostname': socket.gethostname(),
            'python_version': sys.version,
            'cpu_count': os.cpu_count(),
            'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'disk_usage': SystemUtils.get_disk_usage(),
            'environment_variables': dict(os.environ)
        }
        # Examples:
        # SystemUtils.get_system_info()
        # -> { 'platform': 'Windows-10-10.0.19045-SP0', 'cpu_count': 8, ... }

    @staticmethod
    def get_disk_usage(path: str = "/") -> Dict[str, float]:
        try:
            usage = psutil.disk_usage(path)
            return {
                'total_gb': round(usage.total / (1024**3), 2),
                'used_gb': round(usage.used / (1024**3), 2),
                'free_gb': round(usage.free / (1024**3), 2),
                'percent_used': round((usage.used / usage.total) * 100, 2)
            }
        except Exception as e:
            return {'error': str(e)}
        # Examples:
        # SystemUtils.get_disk_usage("/")
        # -> { 'total_gb': 512.0, 'used_gb': 300.5, 'free_gb': 211.5, 'percent_used': 58.7 }

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'virtual': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            },
            'swap': {
                'total_gb': round(swap.total / (1024**3), 2),
                'used_gb': round(swap.used / (1024**3), 2),
                'free_gb': round(swap.free / (1024**3), 2),
                'percent': swap.percent
            }
        }
        # Examples:
        # SystemUtils.get_memory_usage()
        # -> { 'virtual': { 'total_gb': 16.0, 'used_gb': 7.5, ... }, 'swap': {...} }

    @staticmethod
    def get_cpu_usage(interval: float = 1.0) -> Dict[str, Any]:
        return {
            'overall_percent': psutil.cpu_percent(interval=interval),
            'per_cpu': psutil.cpu_percent(interval=interval, percpu=True),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        # Examples:
        # SystemUtils.get_cpu_usage(1.0)
        # -> { 'overall_percent': 12.5, 'per_cpu': [10.1, 15.3, ...] }

    @staticmethod
    def get_network_interfaces() -> Dict[str, Any]:
        interfaces = {}
        for interface, addresses in psutil.net_if_addrs().items():
            interface_info = {
                'addresses': [],
                'stats': psutil.net_if_stats()[interface]._asdict()
            }
            for addr in addresses:
                interface_info['addresses'].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
            interfaces[interface] = interface_info
        return interfaces
        # Examples:
        # SystemUtils.get_network_interfaces()
        # -> { 'Ethernet0': { 'addresses': [...], 'stats': {...} }, ... }

    @staticmethod
    def get_environment_variable(var_name: str, default: str = None) -> str:
        return os.getenv(var_name, default)
        # Examples:
        # SystemUtils.get_environment_variable("PATH")
        # -> "C:/Windows/System32;..."
        #
        # SystemUtils.get_environment_variable("NOT_DEFINED", default="fallback")
        # -> "fallback"

    @staticmethod
    def set_environment_variable(var_name: str, value: str) -> None:
        os.environ[var_name] = value
        # Examples:
        # SystemUtils.set_environment_variable("MY_VAR", "123")
        # SystemUtils.get_environment_variable("MY_VAR")
        # -> "123"

class ProcessManager:
    """Process management utility."""
    
    @staticmethod
    def run_command(command: str, shell: bool = True, capture_output: bool = True,
                    timeout: Optional[int] = None, cwd: Optional[str] = None,
                    env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env or os.environ
            )
            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': command
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out',
                'timeout': timeout,
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command
            }
        # Examples:
        # ProcessManager.run_command("echo Hello")
        # -> { 'success': True, 'stdout': 'Hello\\n', 'stderr': '' }

    @staticmethod
    def run_async_command(command: str, callback=None, **kwargs) -> subprocess.Popen:
        process = subprocess.Popen(
            command,
            shell=kwargs.get('shell', True),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs
        )
        if callback:
            while process.poll() is None:
                time.sleep(0.1)
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        callback(line.strip())
        return process
        # Examples:
        # ProcessManager.run_async_command("ping 127.0.0.1 -n 2")
        # -> subprocess.Popen object

    @staticmethod
    def get_running_processes() -> List[Dict[str, Any]]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes
        # Examples:
        # ProcessManager.get_running_processes()
        # -> [ { 'pid': 1234, 'name': 'python.exe', ... }, ... ]

    @staticmethod
    def kill_process(pid: int, force: bool = False) -> bool:
        try:
            process = psutil.Process(pid)
            if force:
                process.kill()
            else:
                process.terminate()
            return True
        except Exception:
            return False
        # Examples:
        # ProcessManager.kill_process(1234)
        # -> True

    @staticmethod
    def find_process_by_name(name: str) -> List[Dict[str, Any]]:
        matching_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if name.lower() in proc.info['name'].lower():
                    matching_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return matching_processes
        # Examples:
        # ProcessManager.find_process_by_name("python")
        # -> [ { 'pid': 5678, 'name': 'python.exe', 'cmdline': [...] }, ... ]

class NetworkUtils:
    """Network operations utility."""
    
    @staticmethod
    def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False
        # Examples:
        # NetworkUtils.check_internet_connection()
        # -> True

    @staticmethod
    def get_public_ip() -> Optional[str]:
        try:
            response = requests.get('https://httpbin.org/ip', timeout=5)
            return response.json().get('origin')
        except Exception:
            return None
        # Examples:
        # NetworkUtils.get_public_ip()
        # -> "203.0.113.45"

    @staticmethod
    def get_local_ip() -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('10.255.255.255', 1))
                return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'
        # Examples:
        # NetworkUtils.get_local_ip()
        # -> "192.168.1.100"

    @staticmethod
    def ping_host(host: str, count: int = 4) -> Dict[str, Any]:
        command = f"ping -c {count} {host}" if platform.system() != "Windows" else f"ping -n {count} {host}"
        result = ProcessManager.run_command(command)
        return {
            'host': host,
            'success': result['success'],
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '')
        }
        # Examples:
        # NetworkUtils.ping_host("google.com", 2)
        # -> { 'host': 'google.com', 'success': True, 'output': 'Reply from ...', 'error': '' }

    @staticmethod
    def port_scan(host: str, ports: List[int], timeout: int = 1) -> Dict[int, bool]:
        results = {}
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, port))
                    results[port] = result == 0
            except Exception:
                results[port] = False
        return results
        # Examples:
        # NetworkUtils.port_scan("127.0.0.1", [22, 80])
        # -> {22: False, 80: True}

    @staticmethod
    def download_file(url: str, local_path: str, chunk_size: int = 8192) -> Dict[str, Any]:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            return {
                'success': True,
                'url': url,
                'local_path': local_path,
                'size_bytes': downloaded,
                'total_size': total_size
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'local_path': local_path
            }
        # Examples:
        # NetworkUtils.download_file("https://example.com/file.txt", "./file.txt")
        # -> { 'success': True, 'url': 'https://example.com/file.txt', 'local_path': './file.txt', 'size_bytes': 1024, 'total_size': 1024 }
