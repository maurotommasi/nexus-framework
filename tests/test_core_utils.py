# tests/test_core_utils.py
import pytest
import tempfile
import shutil
import os
import json
import yaml
import time
import socket
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta
from framework.core.utils.io import FileManager, ConfigManager, LogManager
from framework.core.utils.system import SystemUtils, ProcessManager, NetworkUtils
from framework.core.utils.data import DataProcessor, ValidationUtils, CryptoUtils
#from framework.core.utils.cloud import CloudUtils, ResourceNaming
from framework.core.utils.time import TimeUtils, RetryUtils
from framework.core.utils.wrapper import FunctionWrapper, ExecutionContext, LogLevel


class TestFileManager:
    """Test cases 1-25: FileManager utility tests"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # Test 1: Basic file read/write
    def test_read_write_file_basic(self):
        content = "Hello, World!"
        self.file_manager.write_file("test.txt", content)
        result = self.file_manager.read_file("test.txt")
        assert result == content
    
    # Test 2: File write with directory creation
    def test_write_file_create_dirs(self):
        content = "Test content"
        self.file_manager.write_file("subdir/nested/test.txt", content, create_dirs=True)
        assert self.file_manager.file_exists("subdir/nested/test.txt")
    
    # Test 3: File read non-existent file
    def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            self.file_manager.read_file("nonexistent.txt")
    
    # Test 4: JSON file operations
    def test_json_operations(self):
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        self.file_manager.write_json("test.json", data)
        result = self.file_manager.read_json("test.json")
        assert result == data
    
    # Test 5: YAML file operations
    def test_yaml_operations(self):
        data = {"config": {"debug": True, "port": 8080}}
        self.file_manager.write_yaml("test.yaml", data)
        result = self.file_manager.read_yaml("test.yaml")
        assert result == data
    
    # Test 6: Invalid JSON handling
    def test_invalid_json(self):
        self.file_manager.write_file("invalid.json", "{invalid json}")
        with pytest.raises(ValueError):
            self.file_manager.read_json("invalid.json")
    
    # Test 7: Invalid YAML handling
    def test_invalid_yaml(self):
        self.file_manager.write_file("invalid.yaml", "invalid: yaml: content:")
        with pytest.raises(ValueError):
            self.file_manager.read_yaml("invalid.yaml")
    
    # Test 8: File copy operations
    def test_copy_file(self):
        content = "Original content"
        self.file_manager.write_file("original.txt", content)
        self.file_manager.copy_file("original.txt", "copy.txt")
        assert self.file_manager.read_file("copy.txt") == content
    
    # Test 9: File move operations
    def test_move_file(self):
        content = "Move me"
        self.file_manager.write_file("source.txt", content)
        self.file_manager.move_file("source.txt", "destination.txt")
        assert not self.file_manager.file_exists("source.txt")
        assert self.file_manager.read_file("destination.txt") == content
    
    # Test 10: File deletion
    def test_delete_file(self):
        self.file_manager.write_file("delete_me.txt", "content")
        assert self.file_manager.delete_file("delete_me.txt")
        assert not self.file_manager.file_exists("delete_me.txt")
    
    # Test 11: Delete non-existent file with ignore_missing
    def test_delete_nonexistent_ignore(self):
        result = self.file_manager.delete_file("nonexistent.txt", ignore_missing=True)
        assert result is False
    
    # Test 12: Delete non-existent file without ignore_missing
    def test_delete_nonexistent_no_ignore(self):
        with pytest.raises(FileNotFoundError):
            self.file_manager.delete_file("nonexistent.txt", ignore_missing=False)
    
    # Test 13: Directory creation
    def test_create_directory(self):
        self.file_manager.create_directory("new_dir/sub_dir")
        assert Path(self.temp_dir, "new_dir", "sub_dir").exists()
    
    # Test 14: Directory deletion
    def test_delete_directory(self):
        os.makedirs(Path(self.temp_dir, "delete_dir"))
        self.file_manager.delete_directory("delete_dir")
        assert not Path(self.temp_dir, "delete_dir").exists()
    
    # Test 15: List files with pattern
    def test_list_files(self):
        self.file_manager.write_file("test1.txt", "content1")
        self.file_manager.write_file("test2.txt", "content2")
        self.file_manager.write_file("other.log", "log content")
        
        txt_files = self.file_manager.list_files(".", "*.txt")
        assert len(txt_files) == 2
        assert all(f.endswith('.txt') for f in txt_files)
    
    # Test 16: Recursive file listing
    def test_list_files_recursive(self):
        self.file_manager.write_file("root.txt", "content", create_dirs=True)
        self.file_manager.write_file("sub/nested.txt", "content", create_dirs=True)
        
        all_txt = self.file_manager.list_files(".", "*.txt", recursive=True)
        assert len(all_txt) >= 2
    
    # Test 17: File size check
    def test_get_file_size(self):
        content = "Test content for size"
        self.file_manager.write_file("size_test.txt", content)
        size = self.file_manager.get_file_size("size_test.txt")
        assert size == len(content.encode('utf-8'))
    
    # Test 18: File modification time
    def test_get_file_modified_time(self):
        self.file_manager.write_file("time_test.txt", "content")
        mod_time = self.file_manager.get_file_modified_time("time_test.txt")
        assert isinstance(mod_time, datetime)
    
    # Test 19: Temporary file creation
    def test_create_temp_file(self):
        temp_file = self.file_manager.create_temp_file(suffix=".tmp", prefix="test_")
        assert os.path.exists(temp_file)
        assert temp_file.endswith(".tmp")
        assert "test_" in os.path.basename(temp_file)
        os.unlink(temp_file)  # Cleanup
    
    # Test 20: Temporary directory creation
    def test_create_temp_directory(self):
        temp_dir = self.file_manager.create_temp_directory(suffix="_test", prefix="dir_")
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)
        shutil.rmtree(temp_dir)  # Cleanup
    
    # Test 21: Different encoding support
    def test_different_encoding(self):
        content = "Héllo Wörld! 🌍"
        self.file_manager.write_file("utf8_test.txt", content, encoding='utf-8')
        result = self.file_manager.read_file("utf8_test.txt", encoding='utf-8')
        assert result == content
    
    # Test 22: Large file handling
    def test_large_file(self):
        large_content = "Large content line\n" * 10000
        self.file_manager.write_file("large.txt", large_content)
        result = self.file_manager.read_file("large.txt")
        assert len(result.splitlines()) == 10000
    
    # Test 23: JSON with complex data types
    def test_json_complex_data(self):
        data = {
            "string": "value",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"inner": "value"}
        }
        self.file_manager.write_json("complex.json", data)
        result = self.file_manager.read_json("complex.json")
        assert result == data
    
    # Test 24: Path normalization
    def test_path_normalization(self):
        content = "Test content"
        self.file_manager.write_file("./test/../normal.txt", content)
        assert self.file_manager.file_exists("normal.txt")
    
    """
    #Test 25: Binary file handling (edge case)
    def test_binary_file_error(self):
        # Write binary data
        binary_path = Path(self.temp_dir, "binary.dat")
        with open(binary_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')

        # Attempt to read binary data as text (which will fail)
        with open(binary_path, 'rb') as f:
            binary_data = f.read()

        # This will raise a UnicodeDecodeError because binary data cannot be decoded as text
        with pytest.raises(UnicodeDecodeError):
            binary_data.decode('utf-8')  # Attempting to decode binary as text
    """

class TestConfigManager:
    """Test cases 26-35: ConfigManager utility tests"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Create test config files
        test_config = {"database": {"host": "localhost", "port": 5432}, "debug": True}
        with open(Path(self.temp_dir, "test.yaml"), 'w') as f:
            yaml.dump(test_config, f)
        
        with open(Path(self.temp_dir, "test.json"), 'w') as f:
            json.dump(test_config, f)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # Test 26: Load YAML config
    def test_load_yaml_config(self):
        config = self.config_manager.load_config("test", "yaml")
        assert config["database"]["host"] == "localhost"
        assert config["debug"] is True
    
    # Test 27: Load JSON config
    def test_load_json_config(self):
        config = self.config_manager.load_config("test", "json")
        assert config["database"]["port"] == 5432
    
    # Test 28: Get config with dot notation
    def test_get_config_dot_notation(self):
        self.config_manager.load_config("test")
        host = self.config_manager.get_config("test", "database.host")
        assert host == "localhost"
    
    # Test 29: Get config with default value
    def test_get_config_with_default(self):
        self.config_manager.load_config("test")
        value = self.config_manager.get_config("test", "nonexistent.key", "default_value")
        assert value == "default_value"
    
    # Test 30: Set config value
    def test_set_config(self):
        self.config_manager.load_config("test")
        self.config_manager.set_config("test", "new.setting", "new_value")
        value = self.config_manager.get_config("test", "new.setting")
        assert value == "new_value"
    
    # Test 31: Save config
    def test_save_config(self):
        config_data = {"new_config": {"value": 123}}
        self.config_manager.save_config("new_config", config_data, "yaml")
        loaded = self.config_manager.load_config("new_config", "yaml")
        assert loaded == config_data
    
    # Test 32: Merge configs
    def test_merge_configs(self):
        config1 = {"a": 1, "b": {"x": 10}}
        config2 = {"b": {"y": 20}, "c": 3}
        
        self.config_manager.save_config("config1", config1)
        self.config_manager.save_config("config2", config2)
        
        merged = self.config_manager.merge_configs("config1", "config2")
        assert merged["a"] == 1
        assert merged["b"]["x"] == 10
        assert merged["b"]["y"] == 20
        assert merged["c"] == 3

    
    # Test 33: Invalid file type
    def test_invalid_file_type(self):
        with pytest.raises(ValueError):
            self.config_manager.load_config("test", "xml")
    
    # Test 34: Non-existent config file
    def test_nonexistent_config(self):
        with pytest.raises(FileNotFoundError):
            self.config_manager.load_config("nonexistent")
    
    # Test 35: Deep nested config access
    def test_deep_nested_config(self):
        deep_config = {"level1": {"level2": {"level3": {"value": "found"}}}}
        self.config_manager.save_config("deep", deep_config)
        value = self.config_manager.get_config("deep", "level1.level2.level3.value")
        assert value == "found"


class TestLogManager:
    """Test cases 36-45: LogManager utility tests"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_manager = LogManager(log_dir=self.temp_dir, app_name="test_app")
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # Test 36: Basic logger creation
    def test_get_logger(self):
        logger = self.log_manager.get_logger("test_logger")
        assert logger.name == "test_logger"
    
    # Test 37: Log to file
    def test_log_to_file(self):
        self.log_manager.log_to_file("Test message", "INFO", "test_logger")
        log_file = Path(self.temp_dir, "test_logger.log")
        assert log_file.exists()
    
    # Test 38: Different log levels
    def test_different_log_levels(self):
        logger = self.log_manager.get_logger("level_test")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        # Test passes if no exceptions
    
    # Test 39: Console and file logging
    def test_console_and_file_logging(self):
        logger = self.log_manager.get_logger("dual_log", log_to_console=True, log_to_file=True)
        assert len(logger.handlers) == 2  # Console + File handlers
    
    # Test 40: File only logging
    def test_file_only_logging(self):
        logger = self.log_manager.get_logger("file_only", log_to_console=False, log_to_file=True)
        assert len(logger.handlers) == 1
    
    # Test 41: Log statistics
    def test_log_stats(self):
        self.log_manager.log_to_file("Test message")
        stats = self.log_manager.get_log_stats()
        assert stats['total_log_files'] >= 1
        assert stats['total_size_mb'] >= 0
    
    # Test 42: Log rotation
    def test_log_rotation(self):
        # Create a log file
        log_file = Path(self.temp_dir, "test_app.log")
        log_file.write_text("Test log content")
        
        # Rotate logs
        self.log_manager.rotate_logs(max_files=3)
        
        # Check if backup was created
        backup_file = Path(self.temp_dir, "test_app.log.1")
        assert backup_file.exists() or not log_file.exists()
    
    # Test 43: Clear old logs
    def test_clear_logs(self):
        # Create an old log file
        old_log = Path(self.temp_dir, "old.log")
        old_log.write_text("Old log content")
        
        # Set modification time to past
        past_time = time.time() - (40 * 24 * 3600)  # 40 days ago
        os.utime(old_log, (past_time, past_time))
        
        # Clear logs older than 30 days
        self.log_manager.clear_logs(older_than_days=30)
        
        # Old log should be deleted
        assert not old_log.exists()
    
    # Test 44: Logger caching
    def test_logger_caching(self):
        logger1 = self.log_manager.get_logger("cached_logger")
        logger2 = self.log_manager.get_logger("cached_logger")
        assert logger1 is logger2  # Same instance
    
    # Test 45: Custom log level
    def test_custom_log_level(self):
        logger = self.log_manager.get_logger("custom_level", level="WARNING")
        # Should not raise exception
        logger.warning("This should be logged")
        logger.debug("This should not be logged")


class TestSystemUtils:
    """Test cases 46-55: SystemUtils tests"""
    
    # Test 46: Get system info
    def test_get_system_info(self):
        info = SystemUtils.get_system_info()
        required_keys = ['platform', 'system', 'hostname', 'cpu_count', 'memory_gb']
        for key in required_keys:
            assert key in info
    
    # Test 47: Get disk usage
    def test_get_disk_usage(self):
        usage = SystemUtils.get_disk_usage("/")
        assert 'total_gb' in usage
        assert 'used_gb' in usage
        assert 'free_gb' in usage
        assert 'percent_used' in usage
    
    # Test 48: Get memory usage
    def test_get_memory_usage(self):
        memory = SystemUtils.get_memory_usage()
        assert 'virtual' in memory
        assert 'swap' in memory
        assert 'total_gb' in memory['virtual']
        assert 'percent' in memory['virtual']
    
    # Test 49: Get CPU usage
    def test_get_cpu_usage(self):
        cpu = SystemUtils.get_cpu_usage(interval=0.1)
        assert 'overall_percent' in cpu
        assert 'per_cpu' in cpu
        assert isinstance(cpu['overall_percent'], (int, float))
    
    # Test 50: Get network interfaces
    def test_get_network_interfaces(self):
        interfaces = SystemUtils.get_network_interfaces()
        assert isinstance(interfaces, dict)
        # Should have at least loopback interface
        assert len(interfaces) > 0
    
    # Test 51: Environment variable operations
    def test_environment_variables(self):
        # Set a test environment variable
        SystemUtils.set_environment_variable("TEST_VAR", "test_value")
        value = SystemUtils.get_environment_variable("TEST_VAR")
        assert value == "test_value"
    
    # Test 52: Environment variable with default
    def test_environment_variable_default(self):
        value = SystemUtils.get_environment_variable("NONEXISTENT_VAR", "default")
        assert value == "default"
    
    # Test 53: Disk usage error handling
    def test_disk_usage_invalid_path(self):
        usage = SystemUtils.get_disk_usage("/nonexistent/path")
        assert 'error' in usage
    
    # Test 54: System info contains expected types
    def test_system_info_types(self):
        info = SystemUtils.get_system_info()
        assert isinstance(info['cpu_count'], int)
        assert isinstance(info['memory_gb'], (int, float))
        assert isinstance(info['hostname'], str)
    
    # Test 55: Memory usage percentages are valid
    def test_memory_usage_valid_percentages(self):
        memory = SystemUtils.get_memory_usage()
        virtual_percent = memory['virtual']['percent']
        assert 0 <= virtual_percent <= 100


class TestProcessManager:
    """Test cases 56-65: ProcessManager tests"""
    
    # Test 56: Run simple command
    def test_run_simple_command(self):
        if os.name == 'nt':  # Windows
            result = ProcessManager.run_command("echo Hello")
        else:  # Unix-like
            result = ProcessManager.run_command("echo Hello")
        
        assert result['success'] is True
        assert result['return_code'] == 0
        assert "Hello" in result['stdout']
    
    # Test 57: Run command with failure
    def test_run_failing_command(self):
        result = ProcessManager.run_command("nonexistent_command_12345")
        assert result['success'] is False
        assert result['return_code'] != 0
    
    # Test 58: Run command with timeout
    def test_run_command_timeout(self):
        if os.name != 'nt':  # Skip on Windows due to sleep command differences
            result = ProcessManager.run_command("sleep 2", timeout=1)
            assert 'timeout' in result['error'].lower()
    
    # Test 59: Run command with custom working directory
    def test_run_command_with_cwd(self):
        temp_dir = tempfile.mkdtemp()
        try:
            if os.name == 'nt':
                result = ProcessManager.run_command("cd", cwd=temp_dir)
            else:
                result = ProcessManager.run_command("pwd", cwd=temp_dir)
            
            assert result['success'] is True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Test 60: Run command with environment variables
    def test_run_command_with_env(self):
        env = os.environ.copy()
        env['TEST_ENV_VAR'] = 'test_value'
        
        if os.name == 'nt':
            result = ProcessManager.run_command("echo %TEST_ENV_VAR%", env=env)
        else:
            result = ProcessManager.run_command("echo $TEST_ENV_VAR", env=env)
        
        assert result['success'] is True
        assert 'test_value' in result['stdout']
    
    # Test 61: Get running processes
    def test_get_running_processes(self):
        processes = ProcessManager.get_running_processes()
        assert isinstance(processes, list)
        assert len(processes) > 0
        
        # Check first process has expected fields
        first_process = processes[0]
        assert 'pid' in first_process
        assert 'name' in first_process
    
    # Test 62: Find process by name
    def test_find_process_by_name(self):
        # Search for Python processes (should find current process)
        processes = ProcessManager.find_process_by_name("python")
        assert isinstance(processes, list)
        # May or may not find processes depending on system
    
    # Test 63: Kill process (test with mock)
    @patch('psutil.Process')
    def test_kill_process(self, mock_process_class):
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process
        
        result = ProcessManager.kill_process(12345, force=False)
        mock_process.terminate.assert_called_once()
        assert result is True
    
    # Test 64: Kill process with force
    @patch('psutil.Process')
    def test_kill_process_force(self, mock_process_class):
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process
        
        result = ProcessManager.kill_process(12345, force=True)
        mock_process.kill.assert_called_once()
        assert result is True
    
    # Test 65: Process manager error handling
    @patch('psutil.Process')
    def test_kill_process_error_handling(self, mock_process_class):
        mock_process_class.side_effect = Exception("Process not found")
        
        result = ProcessManager.kill_process(99999)
        assert result is False


class TestNetworkUtils:
    """Test cases 66-75: NetworkUtils tests"""
    
    # Test 66: Check internet connection
    def test_check_internet_connection(self):
        # Test with Google DNS
        result = NetworkUtils.check_internet_connection("8.8.8.8", 53, timeout=5)
        assert isinstance(result, bool)
    
    # Test 67: Get local IP
    def test_get_local_ip(self):
        ip = NetworkUtils.get_local_ip()
        assert isinstance(ip, str)
        assert '.' in ip  # Basic IP format check
    
    # Test 68: Get public IP (may fail if no internet)
    def test_get_public_ip(self):
        ip = NetworkUtils.get_public_ip()
        # May return None if no internet connection
        if ip:
            assert isinstance(ip, str)
            assert '.' in ip
    
    # Test 69: Ping localhost
    def test_ping_localhost(self):
        result = NetworkUtils.ping_host("127.0.0.1", count=1)
        assert 'host' in result
        assert result['host'] == "127.0.0.1"
        assert 'success' in result
    
    # Test 70: Ping invalid host
    def test_ping_invalid_host(self):
        result = NetworkUtils.ping_host("invalid.host.12345", count=1)
        assert result['success'] is False
    
    # Test 71: Port scan on localhost
    def test_port_scan_localhost(self):
        # Test common closed ports
        results = NetworkUtils.port_scan("127.0.0.1", [9999, 9998], timeout=1)
        assert isinstance(results, dict)
        assert len(results) == 2
        for port, is_open in results.items():
            assert isinstance(is_open, bool)
    
    # Test 72: Download file (mock)
    @patch('requests.get')
    def test_download_file(self, mock_get):
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '100'}
        mock_response.iter_content = lambda chunk_size: [b'test data']
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            result = NetworkUtils.download_file("http://example.com/file.txt", temp_file.name)
            assert result['success'] is True
            assert result['size_bytes'] > 0
        
        # Explicitly close the file before deleting
        temp_file.close()  # Close it explicitly
        
        # Now you can safely delete the file
        os.unlink(temp_file.name)

    
    # Test 73: Download file error
    @patch('requests.get')
    def test_download_file_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        
        result = NetworkUtils.download_file("http://example.com/file.txt", "/tmp/test.txt")
        assert result['success'] is False
        assert 'error' in result
    
    # Test 74: Check internet with invalid host
    def test_check_internet_invalid_host(self):
        result = NetworkUtils.check_internet_connection("999.999.999.999", 53, timeout=1)
        assert result is False
    
    # Test 75: Port scan with invalid host
    def test_port_scan_invalid_host(self):
        results = NetworkUtils.port_scan("invalid.host", [80], timeout=1)
        assert results[80] is False


class TestDataProcessor:
    """Test cases 76-85: DataProcessor tests"""
    
    # Test 76: Deep merge dictionaries
    def test_deep_merge(self):
        dict1 = {"a": 1, "b": {"x": 10, "y": 20}}
        dict2 = {"b": {"x": 15, "z": 30}, "c": 3}
        
        result = DataProcessor.deep_merge(dict1, dict2)
        
        assert result["a"] == 1
        assert result["b"]["x"] == 15  # Overwritten
        assert result["b"]["y"] == 20  # Preserved
        assert result["b"]["z"] == 30  # Added
        assert result["c"] == 3
    
    # Test 77: Flatten dictionary
    def test_flatten_dict(self):
        data = {"a": 1, "b": {"x": 10, "y": {"z": 20}}}
        result = DataProcessor.flatten_dict(data)
        
        expected = {"a": 1, "b.x": 10, "b.y.z": 20}
        assert result == expected
    
    # Test 78: Unflatten dictionary
    def test_unflatten_dict(self):
        data = {"a": 1, "b.x": 10, "b.y.z": 20}
        result = DataProcessor.unflatten_dict(data)
        
        expected = {"a": 1, "b": {"x": 10, "y": {"z": 20}}}
        assert result == expected
    
    # Test 79: Filter dictionary include
    def test_filter_dict_include(self):
        data = {"a": 1, "b": 2, "c": 3, "d": 4}
        result = DataProcessor.filter_dict(data, ["a", "c"], exclude=False)
        
        expected = {"a": 1, "c": 3}
        assert result == expected
    
    # Test 80: Filter dictionary exclude
    def test_filter_dict_exclude(self):
        data = {"a": 1, "b": 2, "c": 3, "d": 4}
        result = DataProcessor.filter_dict(data, ["a", "c"], exclude=True)
        
        expected = {"b": 2, "d": 4}
        assert result == expected
    
    # Test 81: Sanitize string
    def test_sanitize_string(self):
        text = "Hello<World>:Test/File*"
        result = DataProcessor.sanitize_string(text)
        expected = "Hello_World__Test_File_"
        assert result == expected
    
    # Test 82: Generate hash
    def test_generate_hash(self):
        data = "test data"
        hash_result = DataProcessor.generate_hash(data)
        
        assert len(hash_result) == 64  # SHA-256 produces 64 character hex string
        assert isinstance(hash_result, str)
        
        # Same input should produce same hash
        hash_result2 = DataProcessor.generate_hash(data)
        assert hash_result == hash_result2
    
    # Test 83: Generate hash from dict
    def test_generate_hash_dict(self):
        data = {"key": "value", "number": 42}
        hash_result = DataProcessor.generate_hash(data)
        
        assert len(hash_result) == 64
        assert isinstance(hash_result, str)
    
    # Test 84: Base64 encode/decode
    def test_base64_operations(self):
        original = "Hello, World! 🌍"
        encoded = DataProcessor.encode_base64(original)
        decoded = DataProcessor.decode_base64(encoded).decode('utf-8')
        
        assert decoded == original
        assert isinstance(encoded, str)
    
    # Test 85: Base64 with bytes
    def test_base64_bytes(self):
        original = b"Binary data \x00\x01\x02"
        encoded = DataProcessor.encode_base64(original)
        decoded = DataProcessor.decode_base64(encoded)
        
        assert decoded == original


class TestValidationUtils:
    """Test cases 86-95: ValidationUtils tests"""
    
    # Test 86: Valid email addresses
    def test_validate_email_valid(self):
        valid_emails = [
            "user@example.com",
            "test.email@domain.co.uk",
            "user+tag@example.org",
            "123@domain.com"
        ]
        
        for email in valid_emails:
            assert ValidationUtils.validate_email(email), f"Email should be valid: {email}"
    
    # Test 87: Invalid email addresses
    def test_validate_email_invalid(self):
        invalid_emails = [
            "invalid.email",
            "@domain.com",
            "user@",
            "user space@domain.com",
            "user@domain",
            ""
        ]
        
        for email in invalid_emails:
            assert not ValidationUtils.validate_email(email), f"Email should be invalid: {email}"
    
    # Test 88: Valid IP addresses
    def test_validate_ip_valid(self):
        valid_ips = [
            "192.168.1.1",
            "127.0.0.1",
            "8.8.8.8",
            "255.255.255.255",
            "0.0.0.0"
        ]
        
        for ip in valid_ips:
            assert ValidationUtils.validate_ip_address(ip), f"IP should be valid: {ip}"
    
    # Test 89: Invalid IP addresses
    def test_validate_ip_invalid(self):
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "not.an.ip.address",
            ""
        ]
        
        for ip in invalid_ips:
            assert not ValidationUtils.validate_ip_address(ip), f"IP should be invalid: {ip}"
    
    # Test 90: Valid URLs
    def test_validate_url_valid(self):
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://sub.domain.com/path",
            "http://localhost:8080",
            "https://example.com/path?query=value#anchor"
        ]
        
        for url in valid_urls:
            assert ValidationUtils.validate_url(url), f"URL should be valid: {url}"
    
    # Test 91: Invalid URLs
    def test_validate_url_invalid(self):
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Only http/https supported
            "https://",
            "http://",
            ""
        ]
        
        for url in invalid_urls:
            assert not ValidationUtils.validate_url(url), f"URL should be invalid: {url}"
    
    # Test 92: Valid JSON
    def test_validate_json_valid(self):
        valid_json = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        is_valid, error = ValidationUtils.validate_json(valid_json)
        
        assert is_valid is True
        assert error is None
    
    # Test 93: Invalid JSON
    def test_validate_json_invalid(self):
        invalid_json = '{"key": "value", "invalid": }'
        is_valid, error = ValidationUtils.validate_json(invalid_json)
        
        assert is_valid is False
        assert error is not None
    
    # Test 94: Valid ports
    def test_validate_port_valid(self):
        valid_ports = [1, 80, 443, 8080, 65535]
        
        for port in valid_ports:
            assert ValidationUtils.validate_port(port), f"Port should be valid: {port}"
            assert ValidationUtils.validate_port(str(port)), f"Port string should be valid: {port}"
    
    # Test 95: Invalid ports
    def test_validate_port_invalid(self):
        invalid_ports = [0, -1, 65536, 100000, "not_a_port"]
        
        for port in invalid_ports:
            assert not ValidationUtils.validate_port(port), f"Port should be invalid: {port}"


class TestCryptoUtils:
    """Test cases 96-100: CryptoUtils tests"""
    
    # Test 96: Generate random string
    def test_generate_random_string(self):
        random_str = CryptoUtils.generate_random_string(length=16)
        
        assert len(random_str) == 16
        assert isinstance(random_str, str)
        
        # Two calls should produce different results
        random_str2 = CryptoUtils.generate_random_string(length=16)
        assert random_str != random_str2
    
    # Test 97: Generate random string with symbols
    def test_generate_random_string_with_symbols(self):
        random_str = CryptoUtils.generate_random_string(length=20, include_symbols=True)
        
        assert len(random_str) == 20
        # Should contain at least some variety of characters
        assert not random_str.isalnum()  # Should have symbols
    
    # Test 98: Generate UUID
    def test_generate_uuid(self):
        uuid_v4 = CryptoUtils.generate_uuid(version=4)
        uuid_v1 = CryptoUtils.generate_uuid(version=1)
        
        assert len(uuid_v4) == 36  # Standard UUID length with hyphens
        assert len(uuid_v1) == 36
        assert '-' in uuid_v4
        assert uuid_v4 != uuid_v1
    
    # Test 99: Generate API key
    def test_generate_api_key(self):
        api_key = CryptoUtils.generate_api_key(prefix="test", length=24)
        
        assert api_key.startswith("test_")
        assert len(api_key) == 24 + 5  # 24 + "test_"
        
        # Without prefix
        api_key_no_prefix = CryptoUtils.generate_api_key(length=32)
        assert len(api_key_no_prefix) == 32
        assert "_" not in api_key_no_prefix
    
    # Test 100: Password hashing and verification
    def test_password_operations(self):
        password = "my_secure_password123"
        
        # Hash password
        password_hash, salt = CryptoUtils.hash_password(password)
        
        assert len(password_hash) == 64  # SHA-256 hex
        assert len(salt) == 32  # 16 bytes hex encoded
        assert isinstance(password_hash, str)
        assert isinstance(salt, str)
        
        # Verify correct password
        assert CryptoUtils.verify_password(password, password_hash, salt) is True
        
        # Verify incorrect password
        assert CryptoUtils.verify_password("wrong_password", password_hash, salt) is False


# Additional integration tests for complex scenarios
class TestIntegration:
    """Integration tests for combined functionality"""
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_and_file_integration(self):
        """Test ConfigManager with FileManager integration."""
        file_manager = FileManager(self.temp_dir)
        config_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Create config with FileManager
        config_data = {"app": {"name": "test", "version": "1.0"}}
        file_manager.write_yaml("app.yaml", config_data)
        
        # Load with ConfigManager
        loaded_config = config_manager.load_config("app", "yaml")
        assert loaded_config == config_data
    
    def test_logging_and_system_integration(self):
        """Test LogManager with SystemUtils integration."""
        log_manager = LogManager(log_dir=self.temp_dir)
        logger = log_manager.get_logger("system_test")
        
        # Log system information
        system_info = SystemUtils.get_system_info()
        logger.info(f"System: {system_info['platform']}")
        
        # Verify log file was created
        log_file = Path(self.temp_dir, "system_test.log")
        assert log_file.exists()
    
    def test_validation_and_crypto_integration(self):
        """Test ValidationUtils with CryptoUtils integration."""
        # Generate API key
        api_key = CryptoUtils.generate_api_key(prefix="api", length=32)
        
        # Validate it's a string of expected length
        assert len(api_key) == 36  # 32 + "api_"
        
        # Generate and validate email-like string
        test_email = "user@domain.com"
        assert ValidationUtils.validate_email(test_email)


# Test runner configuration
if __name__ == "__main__":
    # Run specific test classes or all tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "-x"  # Stop on first failure
    ])

# Pytest configuration for the test file
pytest_plugins = []

# Fixtures for common test data
@pytest.fixture
def temp_directory():
    """Provide a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_config():
    """Provide sample configuration data."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db"
        },
        "api": {
            "base_url": "https://api.example.com",
            "timeout": 30
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s"
        }
    }

@pytest.fixture
def mock_system_info():
    """Provide mock system information."""
    return {
        "platform": "Linux-5.4.0-test",
        "system": "Linux",
        "hostname": "test-host",
        "cpu_count": 4,
        "memory_gb": 8.0,
        "python_version": "3.9.0"
    }

# Test markers for categorizing tests
pytestmark = [
    pytest.mark.unit,  # Mark all tests in this file as unit tests
]

# Performance benchmarks (optional)
@pytest.mark.benchmark
class TestPerformance:
    """Performance benchmarks for utilities"""
    
    def test_file_operations_performance(self, benchmark):
        """Benchmark file operations."""
        file_manager = FileManager()
        
        def file_operations():
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                temp_path = f.name
            
            try:
                file_manager.write_file(temp_path, "test content" * 1000)
                content = file_manager.read_file(temp_path)
                return len(content)
            finally:
                os.unlink(temp_path)
        
        result = benchmark(file_operations)
        assert result > 0
    
    def test_data_processing_performance(self, benchmark):
        """Benchmark data processing operations."""
        large_dict = {f"key_{i}": {"nested": {"value": i}} for i in range(1000)}
        
        def process_data():
            flattened = DataProcessor.flatten_dict(large_dict)
            return DataProcessor.unflatten_dict(flattened)
        
        result = benchmark(process_data)
        assert len(result) == 1000