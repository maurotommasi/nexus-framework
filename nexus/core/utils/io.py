import os
import json
import yaml
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from nexus.core.utils.io import FileManager  # assuming your original FileManager is in io_module.py
from nexus.core.security import Security

class FileManager:
    """Comprehensive file and directory operations utility."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        # Example: FileManager("/tmp") → base_path = /tmp
        
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """Read file content as string."""
        full_path = self.base_path / file_path
        try:
            with open(full_path, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {full_path}")
        except Exception as e:
            raise IOError(f"Error reading file {full_path}: {str(e)}")
        # Example: read_file("test.txt") → "Hello World"

    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> bool:
        """Write content to file."""
        full_path = self.base_path / file_path
        
        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            with open(full_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            raise IOError(f"Error writing file {full_path}: {str(e)}")
        # Example: write_file("test.txt", "Hello") → True

    def read_json(self, file_path: str) -> Dict[str, Any]:
        """Read and parse JSON file."""
        content = self.read_file(file_path)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")
        # Example: read_json("data.json") → {"key": "value"}

    def write_json(self, file_path: str, data: Dict[str, Any], 
                   indent: int = 2, create_dirs: bool = True) -> bool:
        """Write data to JSON file."""
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return self.write_file(file_path, content, create_dirs=create_dirs)
        # Example: write_json("data.json", {"a":1}) → True

    def read_yaml(self, file_path: str) -> Dict[str, Any]:
        """Read and parse YAML file."""
        content = self.read_file(file_path)
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {str(e)}")
        # Example: read_yaml("config.yaml") → {"db": {"host": "localhost"}}

    def write_yaml(self, file_path: str, data: Dict[str, Any], 
                   create_dirs: bool = True) -> bool:
        """Write data to YAML file."""
        content = yaml.dump(data, default_flow_style=False, indent=2)
        return self.write_file(file_path, content, create_dirs=create_dirs)
        # Example: write_yaml("config.yaml", {"db": {"host": "localhost"}}) → True

    def copy_file(self, src: str, dst: str, create_dirs: bool = True) -> bool:
        """Copy file from source to destination."""
        src_path = self.base_path / src
        dst_path = self.base_path / dst
        
        if create_dirs:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            raise IOError(f"Error copying {src_path} to {dst_path}: {str(e)}")
        # Example: copy_file("a.txt", "backup/a.txt") → True

    def move_file(self, src: str, dst: str, create_dirs: bool = True) -> bool:
        """Move file from source to destination."""
        src_path = self.base_path / src
        dst_path = self.base_path / dst
        
        if create_dirs:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
        try:
            shutil.move(str(src_path), str(dst_path))
            return True
        except Exception as e:
            raise IOError(f"Error moving {src_path} to {dst_path}: {str(e)}")
        # Example: move_file("a.txt", "moved/a.txt") → True

    def delete_file(self, file_path: str, ignore_missing: bool = True) -> bool:
        """Delete file."""
        full_path = self.base_path / file_path
        try:
            full_path.unlink()
            return True
        except FileNotFoundError:
            if not ignore_missing:
                raise
            return False
        except Exception as e:
            raise IOError(f"Error deleting {full_path}: {str(e)}")
        # Example: delete_file("test.txt") → True

    def create_directory(self, dir_path: str, parents: bool = True) -> bool:
        """Create directory."""
        full_path = self.base_path / dir_path
        try:
            full_path.mkdir(parents=parents, exist_ok=True)
            return True
        except Exception as e:
            raise IOError(f"Error creating directory {full_path}: {str(e)}")
        # Example: create_directory("new_dir") → True

    def delete_directory(self, dir_path: str, recursive: bool = False) -> bool:
        """Delete directory."""
        full_path = self.base_path / dir_path
        try:
            if recursive:
                shutil.rmtree(full_path)
            else:
                full_path.rmdir()
            return True
        except Exception as e:
            raise IOError(f"Error deleting directory {full_path}: {str(e)}")
        # Example: delete_directory("old_dir", recursive=True) → True

    def list_files(self, directory: str = ".", pattern: str = "*", 
                   recursive: bool = False) -> List[str]:
        """List files in directory matching pattern."""
        dir_path = self.base_path / directory
        
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))
            
        return [str(f.relative_to(self.base_path)) for f in files if f.is_file()]
        # Example: list_files(".", "*.txt") → ["a.txt", "b.txt"]

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / file_path).exists()
        # Example: file_exists("a.txt") → True

    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        full_path = self.base_path / file_path
        return full_path.stat().st_size
        # Example: get_file_size("a.txt") → 1024

    def get_file_modified_time(self, file_path: str) -> datetime:
        """Get file last modified time."""
        full_path = self.base_path / file_path
        timestamp = full_path.stat().st_mtime
        return datetime.fromtimestamp(timestamp)
        # Example: get_file_modified_time("a.txt") → datetime(2025, 9, 22, 12, 0)

    def create_temp_file(self, suffix: str = "", prefix: str = "tmp_") -> str:
        """Create temporary file and return path."""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix=prefix
        )
        temp_file.close()
        return temp_file.name
        # Example: create_temp_file(".txt") → "/tmp/tmp_abcd.txt"

    def create_temp_directory(self, suffix: str = "", prefix: str = "tmp_") -> str:
        """Create temporary directory and return path."""
        return tempfile.mkdtemp(suffix=suffix, prefix=prefix)
        # Example: create_temp_directory("_logs") → "/tmp/tmp_xyz_logs"


class ConfigManager:
    """Configuration management utility."""
    
    def __init__(self, config_dir: str = "config"):
        self.file_manager = FileManager()
        self.config_dir = config_dir
        self.configs = {}
        # Example: ConfigManager("settings") → configs stored in ./settings

    def load_config(self, config_name: str, file_type: str = "yaml") -> Dict[str, Any]:
        """Load configuration from file."""
        file_path = f"{self.config_dir}/{config_name}.{file_type}"
        
        if file_type.lower() == "json":
            config = self.file_manager.read_json(file_path)
        elif file_type.lower() in ["yaml", "yml"]:
            config = self.file_manager.read_yaml(file_path)
        else:
            raise ValueError(f"Unsupported config file type: {file_type}")
            
        self.configs[config_name] = config
        return config
        # Example: load_config("db", "yaml") → {"host": "localhost"}

    def save_config(self, config_name: str, config_data: Dict[str, Any], 
                    file_type: str = "yaml") -> bool:
        """Save configuration to file."""
        file_path = f"{self.config_dir}/{config_name}.{file_type}"
        
        if file_type.lower() == "json":
            return self.file_manager.write_json(file_path, config_data)
        elif file_type.lower() in ["yaml", "yml"]:
            return self.file_manager.write_yaml(file_path, config_data)
        else:
            raise ValueError(f"Unsupported config file type: {file_type}")
        # Example: save_config("db", {"host":"localhost"}, "yaml") → True

    def get_config(self, config_name: str, key: str = None, default: Any = None) -> Any:
        """Get configuration value."""
        if config_name not in self.configs:
            self.load_config(config_name)
            
        config = self.configs[config_name]
        
        if key is None:
            return config
            
        keys = key.split('.')
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        # Example: get_config("db", "host") → "localhost"

    def set_config(self, config_name: str, key: str, value: Any) -> None:
        """Set configuration value."""
        if config_name not in self.configs:
            self.configs[config_name] = {}
            
        keys = key.split('.')
        config = self.configs[config_name]
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        # Example: set_config("db", "host", "127.0.0.1") → None

    def merge_configs(self, *config_names: str) -> Dict[str, Any]:
        merged = {}
        for config_name in config_names:
            if config_name not in self.configs:
                self.load_config(config_name)
            for key, value in self.configs[config_name].items():
                if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                    merged[key] = self.merge_dicts(merged[key], value)
                else:
                    merged[key] = value
        return merged
        # Example: merge_configs("db", "auth") → merged dict

    def merge_dicts(self, dict1, dict2):
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
        # Example: merge_dicts({"a":1}, {"b":2}) → {"a":1, "b":2}


class LogManager:
    """Advanced logging utility."""
    
    def __init__(self, log_dir: str = "logs", app_name: str = "framework"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.file_manager = FileManager()
        self.loggers = {}
        
        self.file_manager.create_directory(log_dir)
        # Example: LogManager("/tmp/logs") → creates directory

    def get_logger(self, name: str = None, level: str = "INFO", 
                   log_to_file: bool = True, log_to_console: bool = True) -> logging.Logger:
        """Get or create logger."""
        logger_name = name or self.app_name
        
        if logger_name in self.loggers:
            return self.loggers[logger_name]
            
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
        
        logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
        if log_to_file:
            log_file = self.log_dir / f"{logger_name}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        self.loggers[logger_name] = logger
        return logger
        # Example: get_logger("app") → logger instance

    def log_to_file(self, message: str, level: str = "INFO", 
                    logger_name: str = None) -> None:
        """Log message to file."""
        logger = self.get_logger(logger_name)
        getattr(logger, level.lower())(message)
        # Example: log_to_file("System started", "INFO") → writes to log

    def rotate_logs(self, max_files: int = 5) -> None:
        """Rotate log files."""
        for log_file in self.log_dir.glob("*.log"):
            for i in range(max_files - 1, 0, -1):
                old_file = log_file.with_suffix(f".log.{i}")
                new_file = log_file.with_suffix(f".log.{i + 1}")
                
                if old_file.exists():
                    if new_file.exists():
                        new_file.unlink()
                    old_file.rename(new_file)
            
            backup_file = log_file.with_suffix(".log.1")
            if backup_file.exists():
                backup_file.unlink()
            log_file.rename(backup_file)
        # Example: rotate_logs(3) → rotates log files up to .log.3

    def clear_logs(self, older_than_days: int = 30) -> None:
        """Clear old log files."""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        for log_file in self.log_dir.glob("*.log*"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                log_file.unlink()
        # Example: clear_logs(7) → deletes logs older than 7 days

    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            'total_log_files': 0,
            'total_size_mb': 0,
            'files': []
        }
        
        for log_file in self.log_dir.glob("*.log*"):
            file_size = log_file.stat().st_size
            stats['total_log_files'] += 1
            stats['total_size_mb'] += file_size / (1024 * 1024)
            stats['files'].append({
                'name': log_file.name,
                'size_mb': file_size / (1024 * 1024),
                'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            })
            
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats
        # Example: get_log_stats() → {'total_log_files':2, 'total_size_mb':1.2, 'files':[...]}

class SecureFileManager(FileManager):
    """FileManager with RSA asymmetric encryption/decryption using Security class."""

    def __init__(self, base_path: Optional[str] = None, private_key_file: str = "private_key.pem", public_key_file: str = "public_key.pem"):
        super().__init__(base_path)
        self.security = Security(private_key_file=private_key_file, public_key_file=public_key_file)

    # -------------------- Override read/write --------------------
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> bool:
        """Encrypt content using public key and save to file."""
        full_path = self.base_path / file_path
        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        encrypted_data = self.security.encrypt(content)
        full_path.write_bytes(encrypted_data)
        return True

    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """Read file and decrypt content using private key."""
        full_path = self.base_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        encrypted_data = full_path.read_bytes()
        decrypted_data = self.security.decrypt(encrypted_data)
        return decrypted_data