# framework/core/utils/system.py
import os
import sys
import subprocess
import platform
import psutil
import socket
import requests
from typing import Dict, List, Optional, Any, Tuple
import time
from pathlib import Path

class SystemUtils:
    """System information and operations utility."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information."""
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
    
    @staticmethod
    def get_disk_usage(path: str = "/") -> Dict[str, float]:
        """Get disk usage information."""
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
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get memory usage information."""
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
    
    @staticmethod
    def get_cpu_usage(interval: float = 1.0) -> Dict[str, Any]:
        """Get CPU usage information."""
        return {
            'overall_percent': psutil.cpu_percent(interval=interval),
            'per_cpu': psutil.cpu_percent(interval=interval, percpu=True),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    @staticmethod
    def get_network_interfaces() -> Dict[str, Any]:
        """Get network interface information."""
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
    
    @staticmethod
    def get_environment_variable(var_name: str, default: str = None) -> str:
        """Get environment variable with optional default."""
        return os.getenv(var_name, default)
    
    @staticmethod
    def set_environment_variable(var_name: str, value: str) -> None:
        """Set environment variable."""
        os.environ[var_name] = value

class ProcessManager:
    """Process management utility."""
    
    @staticmethod
    def run_command(command: str, shell: bool = True, capture_output: bool = True,
                    timeout: Optional[int] = None, cwd: Optional[str] = None,
                    env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Run system command and return result."""
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
    
    @staticmethod
    def run_async_command(command: str, callback=None, **kwargs) -> subprocess.Popen:
        """Run command asynchronously."""
        process = subprocess.Popen(
            command,
            shell=kwargs.get('shell', True),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs
        )
        
        if callback:
            # Simple polling approach
            while process.poll() is None:
                time.sleep(0.1)
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        callback(line.strip())
                        
        return process
    
    @staticmethod
    def get_running_processes() -> List[Dict[str, Any]]:
        """Get list of running processes."""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return processes
    
    @staticmethod
    def kill_process(pid: int, force: bool = False) -> bool:
        """Kill process by PID."""
        try:
            process = psutil.Process(pid)
            if force:
                process.kill()
            else:
                process.terminate()
            return True
        except Exception:
            return False
    
    @staticmethod
    def find_process_by_name(name: str) -> List[Dict[str, Any]]:
        """Find processes by name."""
        matching_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if name.lower() in proc.info['name'].lower():
                    matching_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return matching_processes

class NetworkUtils:
    """Network operations utility."""
    
    @staticmethod
    def check_internet_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3) -> bool:
        """Check if internet connection is available."""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False
    
    @staticmethod
    def get_public_ip() -> Optional[str]:
        """Get public IP address."""
        try:
            response = requests.get('https://httpbin.org/ip', timeout=5)
            return response.json().get('origin')
        except Exception:
            return None
    
    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address."""
        try:
            # Connect to a remote address (doesn't have to be reachable)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('10.255.255.255', 1))
                return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'
    
    @staticmethod
    def ping_host(host: str, count: int = 4) -> Dict[str, Any]:
        """Ping a host and return statistics."""
        command = f"ping -c {count} {host}" if platform.system() != "Windows" else f"ping -n {count} {host}"
        result = ProcessManager.run_command(command)
        
        return {
            'host': host,
            'success': result['success'],
            'output': result.get('stdout', ''),
            'error': result.get('stderr', '')
        }
    
    @staticmethod
    def port_scan(host: str, ports: List[int], timeout: int = 1) -> Dict[int, bool]:
        """Scan ports on a host."""
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
    
    @staticmethod
    def download_file(url: str, local_path: str, chunk_size: int = 8192) -> Dict[str, Any]:
        """Download file from URL."""
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