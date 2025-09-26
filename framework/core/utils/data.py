import json
import hashlib
import base64
import secrets
from typing import Any, Dict, List, Optional, Union, Tuple
import re
from datetime import datetime
import uuid


class DataProcessor:
    """Data processing and manipulation utility."""

    @staticmethod
    def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries recursively."""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataProcessor.deep_merge(result[key], value)
            else:
                result[key] = value
        return result

        # Example:
        # dict1 = {"a": 1, "b": {"c": 2}}
        # dict2 = {"b": {"d": 3}, "e": 4}
        # Output: {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

    @staticmethod
    def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary into a single level with separator."""
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(DataProcessor.flatten_dict(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
        return dict(items)

        # Example:
        # {"a": {"b": {"c": 1}}, "d": 2}
        # Output: {'a.b.c': 1, 'd': 2}

    @staticmethod
    def unflatten_dict(data: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """Convert a flattened dict back into a nested dictionary."""
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

        # Example:
        # {'a.b.c': 1, 'd': 2}
        # Output: {'a': {'b': {'c': 1}}, 'd': 2}

    @staticmethod
    def filter_dict(data: Dict[str, Any], keys: List[str], exclude: bool = False) -> Dict[str, Any]:
        """Filter dictionary by including/excluding given keys."""
        if exclude:
            return {k: v for k, v in data.items() if k not in keys}
        else:
            return {k: v for k, v in data.items() if k in keys}

        # Example:
        # {"name": "Alice", "age": 30, "city": "Paris"}
        # filter_dict(..., ["name", "city"]) -> {'name': 'Alice', 'city': 'Paris'}

    @staticmethod
    def sanitize_string(
        text: str,
        allowed_chars: str = None,
        regex_pattern: str = r'[<>:"/\\|?*]',
        replacement_char: str = '_'
    ) -> str:
        """Sanitize string by removing/replacing unwanted characters."""
        if allowed_chars:
            return ''.join(c for c in text if c in allowed_chars)
        else:
            return re.sub(regex_pattern, replacement_char, text)

        # Examples:
        # sanitize_string("Hello:World*<>")
        # -> "Hello_World___"
        # sanitize_string("Hello:World*<>", regex_pattern=r'[:*]', replacement_char='-')
        # -> "Hello-World-<>"
        # sanitize_string("Hello:World*<>", allowed_chars="HeloWrd")
        # -> "HelloWorld"

    @staticmethod
    def generate_hash(data: Union[str, bytes, Dict], algorithm: str = 'sha256') -> str:
        """Generate a hash (MD5, SHA256, etc.) of input data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        if isinstance(data, str):
            data = data.encode('utf-8')
        hash_func = getattr(hashlib, algorithm)()
        hash_func.update(data)
        return hash_func.hexdigest()

        # Example:
        # generate_hash("hello world", "md5") -> '5eb63bbbe01eeed093cb22bb8f5acdc3'

    @staticmethod
    def encode_base64(data: Union[str, bytes]) -> str:
        """Encode data to base64 string."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return base64.b64encode(data).decode('utf-8')

        # Example:
        # encode_base64("hello") -> 'aGVsbG8='

    @staticmethod
    def decode_base64(encoded_data: str) -> bytes:
        """Decode base64 string into bytes."""
        return base64.b64decode(encoded_data)

        # Example:
        # decode_base64("aGVsbG8=") -> b'hello'

    # 🔹 Extra functions
    @staticmethod
    def to_json(data: Any, pretty: bool = False) -> str:
        """Convert Python object to JSON string."""
        return json.dumps(data, indent=4 if pretty else None)

        # Example:
        # to_json({"name": "Alice"}, pretty=True)
        # -> '{\n    "name": "Alice"\n}'

    @staticmethod
    def from_json(data: str) -> Any:
        """Parse JSON string to Python object."""
        return json.loads(data)

        # Example:
        # from_json('{"name": "Alice"}') -> {'name': 'Alice'}

    @staticmethod
    def generate_slug(text: str) -> str:
        """Generate URL-friendly slug."""
        return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

        # Example:
        # generate_slug("Hello World!!") -> 'hello-world'

    @staticmethod
    def mask_sensitive(data: str, visible: int = 4) -> str:
        """Mask sensitive string leaving last N chars visible."""
        return '*' * (len(data) - visible) + data[-visible:]

        # Example:
        # mask_sensitive("1234567890", 4) -> '******7890'

    @staticmethod
    def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
        """Split list into chunks of given size."""
        return [lst[i:i + size] for i in range(0, len(lst), size)]

        # Example:
        # chunk_list([1, 2, 3, 4, 5], 2) -> [[1, 2], [3, 4], [5]]


class ValidationUtils:
    """Data validation utility."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

        # Example:
        # validate_email("test@example.com") -> True
        # validate_email("bad@com") -> False

    @staticmethod
    def validate_ip_address(ip: str, version: int = None) -> bool:
        """Validate IP address (IPv4/IPv6)."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(ip)
            if version and addr.version != version:
                return False
            return True
        except ValueError:
            return False

        # Example:
        # "192.168.0.1" -> True
        # "999.999.999.999" -> False

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate HTTP/HTTPS URL format."""
        pattern = r'^https?://(?:[-\\w.])+(?::[0-9]+)?(?:/(?:[\\w/_.])*(?:\\?(?:[\\w&=%.])*)?(?:#(?:[\\w.])*)?)?'
        return re.match(pattern, url) is not None

        # Example:
        # "https://example.com" -> True
        # "ftp://example.com" -> False

    @staticmethod
    def validate_json(json_string: str) -> Tuple[bool, Optional[str]]:
        """Check if a string is valid JSON."""
        try:
            json.loads(json_string)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)

        # Example:
        # '{"name": "Alice"}' -> (True, None)
        # '{"name": Alice}'   -> (False, "...error...")

    @staticmethod
    def validate_port(port: Union[int, str]) -> bool:
        """Validate if a port number is between 1 and 65535."""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except ValueError:
            return False

        # Example:
        # 8080 -> True
        # 70000 -> False

    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """Validate hostname according to RFC rules."""
        if len(hostname) > 255:
            return False
        pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$'
        return all(re.match(pattern, label) for label in hostname.split('.'))

        # Example:
        # "example.com" -> True
        # "-bad.com" -> False

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Check if required fields exist and are non-empty."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        return missing_fields

        # Example:
        # {"name": "Alice", "age": None}, ["name", "age", "city"]
        # -> ['age', 'city']

    @staticmethod
    def validate_data_types(data: Dict[str, Any], type_mapping: Dict[str, type]) -> List[str]:
        """Validate dictionary fields against expected data types."""
        invalid_fields = []
        for field, expected_type in type_mapping.items():
            if field in data and not isinstance(data[field], expected_type):
                invalid_fields.append(f"{field} should be {expected_type.__name__}")
        return invalid_fields

        # Example:
        # {"name": "Alice", "age": "30"}, {"age": int}
        # -> ['age should be int']

    # 🔹 Extra functions
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate international phone numbers."""
        pattern = r'^\\+?[1-9]\\d{1,14}$'
        return re.match(pattern, phone) is not None

        # Example:
        # "+14155552671" -> True
        # "123-456" -> False

    @staticmethod
    def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
        """Validate date string with given format."""
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            return False

        # Example:
        # "2023-01-01" -> True
        # "01/01/2023" -> False

    @staticmethod
    def validate_credit_card(card: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        digits = [int(d) for d in card if d.isdigit()]
        checksum = 0
        parity = len(digits) % 2
        for i, d in enumerate(digits):
            if i % 2 == parity:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

        # Example:
        # "4532015112830366" -> True
        # "1234567890123456" -> False

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate strong password (min 8 chars, upper, lower, digit, symbol)."""
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,}$'
        return re.match(pattern, password) is not None

        # Example:
        # "StrongP@ss1" -> True
        # "weakpass" -> False

    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Check if string is valid UUID."""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

        # Example:
        # "f47ac10b-58cc-4372-a567-0e02b2c3d479" -> True
        # "invalid-uuid" -> False


class CryptoUtils:
    """Cryptographic utilities."""

    @staticmethod
    def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
        """Generate random string of given length."""
        import string
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(length))

        # Example:
        # generate_random_string(10) -> 'kD8fj29XnQ'

    @staticmethod
    def generate_uuid(version: int = 4) -> str:
        """Generate UUID (v1 or v4)."""
        if version == 1:
            return str(uuid.uuid1())
        elif version == 4:
            return str(uuid.uuid4())
        else:
            raise ValueError("Only UUID versions 1 and 4 are supported")

        # Example:
        # generate_uuid(4) -> 'f47ac10b-58cc-4372-a567-0e02b2c3d479'

    @staticmethod
    def generate_api_key(prefix: str = "", length: int = 32) -> str:
        """Generate random API key with optional prefix."""
        key = CryptoUtils.generate_random_string(length)
        return f"{prefix}_{key}" if prefix else key

        # Example:
        # generate_api_key("API", 16) -> 'API_Xk9pQa7hPz8T3mKd'

    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash a password with salt using SHA-256."""
        if salt is None:
            salt = secrets.token_hex(16)
        salted_password = f"{password}{salt}"
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        return password_hash, salt

        # Example:
        # hash_password("mysecret") -> ('hashvalue', 'salt')

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash and salt."""
        computed_hash, _ = CryptoUtils.hash_password(password, salt)
        return computed_hash == password_hash

        # Example:
        # verify_password("mysecret", hash, salt) -> True
        # verify_password("wrong", hash, salt) -> False

    # 🔹 Extra functions
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure token using secrets."""
        return secrets.token_urlsafe(length)

        # Example:
        # generate_token(16) -> 'N2vY7fK9xk3pAqD4'

    @staticmethod
    def generate_sha256(data: str) -> str:
        """Generate SHA-256 hash of string."""
        return hashlib.sha256(data.encode()).hexdigest()

        # Example:
        # generate_sha256("hello") -> '2cf24dba5fb0a30e26e83b2ac5bcae4b...'