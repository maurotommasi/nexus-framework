# framework/core/utils/data.py
import json
import hashlib
import base64
import secrets
from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime
import uuid

class DataProcessor:
    """Data processing and manipulation utility."""
    
    @staticmethod
    def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataProcessor.deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result
    
    @staticmethod
    def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                items.extend(DataProcessor.flatten_dict(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
                
        return dict(items)
    
    @staticmethod
    def unflatten_dict(data: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """Unflatten dictionary with separator."""
        result = {}
        
        for key, value in data.items():
            keys = key.split(sep)
            current = result
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
                
            current[keys[-1]] = value
            
        return result
    
    @staticmethod
    def filter_dict(data: Dict[str, Any], keys: List[str], exclude: bool = False) -> Dict[str, Any]:
        """Filter dictionary by keys."""
        if exclude:
            return {k: v for k, v in data.items() if k not in keys}
        else:
            return {k: v for k, v in data.items() if k in keys}
    
    @staticmethod
    def sanitize_string(text: str, allowed_chars: str = None) -> str:
        """Sanitize string by removing/replacing unwanted characters."""
        if allowed_chars:
            return ''.join(c for c in text if c in allowed_chars)
        else:
            # Remove common problematic characters
            return re.sub(r'[<>:"/\\|?*]', '_', text)
    
    @staticmethod
    def generate_hash(data: Union[str, bytes, Dict], algorithm: str = 'sha256') -> str:
        """Generate hash of data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        hash_func = getattr(hashlib, algorithm)()
        hash_func.update(data)
        return hash_func.hexdigest()
    
    @staticmethod
    def encode_base64(data: Union[str, bytes]) -> str:
        """Encode data to base64."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')
    
    @staticmethod
    def decode_base64(encoded_data: str) -> bytes:
        """Decode base64 data."""
        return base64.b64decode(encoded_data)

class ValidationUtils:
    """Data validation utility."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_ip_address(ip: str, version: int = None) -> bool:
        """Validate IP address."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(ip)
            if version and addr.version != version:
                return False
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?
        return re.match(pattern, url) is not None
    
    @staticmethod
    def validate_json(json_string: str) -> Tuple[bool, Optional[str]]:
        """Validate JSON string."""
        try:
            json.loads(json_string)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> bool:
        """Validate port number."""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except ValueError:
            return False
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """Validate hostname format."""
        if len(hostname) > 255:
            return False
        
        pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)
        return all(re.match(pattern, label) for label in hostname.split('.'))
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate required fields in dictionary."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_data_types(data: Dict[str, Any], type_mapping: Dict[str, type]) -> List[str]:
        """Validate data types in dictionary."""
        invalid_fields = []
        for field, expected_type in type_mapping.items():
            if field in data and not isinstance(data[field], expected_type):
                invalid_fields.append(f"{field} should be {expected_type.__name__}")
        return invalid_fields

class CryptoUtils:
    """Cryptographic utilities."""
    
    @staticmethod
    def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
        """Generate random string."""
        import string
        
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += string.punctuation
            
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_uuid(version: int = 4) -> str:
        """Generate UUID."""
        if version == 1:
            return str(uuid.uuid1())
        elif version == 4:
            return str(uuid.uuid4())
        else:
            raise ValueError("Only UUID versions 1 and 4 are supported")
    
    @staticmethod
    def generate_api_key(prefix: str = "", length: int = 32) -> str:
        """Generate API key with optional prefix."""
        key = CryptoUtils.generate_random_string(length)
        return f"{prefix}_{key}" if prefix else key
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt (using SHA-256 for simplicity)."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        salted_password = f"{password}{salt}"
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash."""
        computed_hash, _ = CryptoUtils.hash_password(password, salt)
        return computed_hash == password_hash