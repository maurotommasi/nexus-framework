# conftest.py - Shared pytest configuration and fixtures
import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add framework to Python path
sys.path.insert(0, str(Path(__file__).parent))

@pytest.fixture(scope="session")
def test_data_dir():
    """Create test data directory for the session."""
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    yield test_dir
    # Cleanup after session
    if test_dir.exists():
        shutil.rmtree(test_dir)

@pytest.fixture
def temp_dir():
    """Provide a temporary directory that's cleaned up after test."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        "string_value": "test",
        "integer_value": 42,
        "float_value": 3.14159,
        "boolean_value": True,
        "null_value": None,
        "array_value": [1, 2, 3, "four"],
        "object_value": {
            "nested_key": "nested_value",
            "nested_number": 100
        }
    }

@pytest.fixture
def sample_yaml_data():
    """Sample YAML data for testing."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {
                "username": "testuser",
                "password": "testpass"
            }
        },
        "api_config": {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "retry_count": 3
        },
        "features": ["auth", "logging", "monitoring"]
    }

@pytest.fixture
def mock_system_environment():
    """Mock system environment for testing."""
    mock_env = {
        "TEST_ENV": "pytest",
        "DEBUG": "true",
        "API_KEY": "test_key_12345"
    }
    
    with patch.dict(os.environ, mock_env, clear=False):
        yield mock_env

@pytest.fixture
def mock_network_responses():
    """Mock network responses for testing."""
    with patch('requests.get') as mock_get, \
         patch('socket.socket') as mock_socket:
        
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ip": "203.0.113.1"}
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content = lambda chunk_size: [b"test content"]
        mock_get.return_value = mock_response
        
        # Mock socket connection
        mock_socket_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance
        
        yield {
            "http_response": mock_response,
            "socket": mock_socket_instance
        }

# Test data files setup
def pytest_configure(config):
    """Configure pytest with test data files."""
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Create sample config files
    sample_json = {
        "app_name": "nexuas-framework",
        "version": "1.0.0",
        "database": {"host": "localhost", "port": 5432}
    }
    
    sample_yaml = {
        "logging": {"level": "INFO", "format": "%(message)s"},
        "features": {"auth": True, "monitoring": False}
    }
    
    # Write test files
    import json
    import yaml
    
    with open(test_data_dir / "sample.json", 'w') as f:
        json.dump(sample_json, f)
    
    with open(test_data_dir / "sample.yaml", 'w') as f:
        yaml.dump(sample_yaml, f)
    
    # Create invalid files for error testing
    with open(test_data_dir / "invalid.json", 'w') as f:
        f.write('{"invalid": json}')
    
    with open(test_data_dir / "invalid.yaml", 'w') as f:
        f.write('invalid: yaml: content:')

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark network tests
        if "network" in item.name.lower() or "internet" in item.name.lower():
            item.add_marker(pytest.mark.network)
        
        # Mark slow tests
        if "performance" in item.name.lower() or "benchmark" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        
        # Mark system tests
        if "system" in item.name.lower() or "process" in item.name.lower():
            item.add_marker(pytest.mark.system)

# Custom pytest markers
def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Skip network tests if no internet connection
    if "network" in [mark.name for mark in item.iter_markers()]:
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
        except (socket.error, socket.timeout):
            pytest.skip("No internet connection available")