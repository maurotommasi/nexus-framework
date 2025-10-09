## Summary

The Enterprise Security Manager provides a comprehensive, production-ready security solution with:

- **60+ Features** across 8 specialized managers
- **Enterprise-Grade** security with audit logging
- **Multi-Algorithm Support** for maximum flexibility
- **Easy Integration** with existing applications
- **Comprehensive Documentation** with examples
- **Best Practices** built-in by default

Get started:
```bash
pip install cryptography paramiko bcrypt pyotp pyjwt
python enterprise_security.py  # Run demo
```

For questions or support, contact the security team.# Enterprise Security Manager - Complete API Documentation

**Version:** 2.0.0  
**Author:** Enterprise Security Team  
**License:** Enterprise

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [SSHKeyManager](#sshkeymanager)
4. [SecretManager](#secretmanager)
5. [PasswordManager](#passwordmanager)
6. [APIKeyManager](#apikeymanager)
7. [CertificateManager](#certificatemanager)
8. [TokenManager](#tokenmanager)
9. [TwoFactorAuthManager](#twofactorauthmanager)
10. [AccessControlManager](#accesscontrolmanager)
11. [EnterpriseSecurityManager](#enterprisesecuritymanager)
12. [Data Classes](#data-classes)
13. [Examples](#examples)

---

## Overview

The Enterprise Security Manager is a comprehensive Python security library providing 60+ security features including SSH key management, encryption, password hashing, JWT tokens, 2FA, and RBAC.

### Features Summary

- **SSH Key Management**: Generate, rotate, and manage SSH keys
- **Secret Encryption**: Multi-algorithm encryption for sensitive data
- **Password Management**: Secure hashing and strength validation
- **API Keys**: Generate and validate API keys with permissions
- **Certificates**: SSL/TLS certificate generation and management
- **JWT Tokens**: Token generation, verification, and revocation
- **Two-Factor Auth**: TOTP and backup codes
- **Access Control**: Role-based access control (RBAC)

---

## Installation

```bash
pip install cryptography paramiko bcrypt argon2-cffi passlib pyotp qrcode pyjwt
```

**Optional Dependencies:**
- `bcrypt`: For bcrypt password hashing
- `argon2-cffi`: For Argon2 password hashing
- `passlib`: For PBKDF2 password hashing
- `pyotp`: For TOTP 2FA
- `qrcode`: For QR code generation
- `pyjwt`: For JWT token management

---

## SSHKeyManager

Manages SSH keys with 15+ features including generation, rotation, and validation.

### Constructor

```python
SSHKeyManager(storage_dir: str = "/var/secure/ssh")
```

**Parameters:**
- `storage_dir` (str): Directory for storing SSH keys. Default: `/var/secure/ssh`

**Returns:** `SSHKeyManager` instance

---

### create_temp_key_file()

Create a temporary SSH key file with proper permissions.

```python
def create_temp_key_file(key_content: str) -> str
```

**Parameters:**
- `key_content` (str): SSH private key content in PEM format

**Returns:**
- `str`: Path to the temporary key file

**Raises:**
- `Exception`: If key file creation fails

**Example:**
```python
ssh_manager = SSHKeyManager()
key_path = ssh_manager.create_temp_key_file(my_private_key)
# Returns: "/tmp/tmp_xyz123.pem"
```

---

### generate_ssh_key_pair()

Generate a new SSH key pair.

```python
def generate_ssh_key_pair(
    key_type: KeyType = KeyType.ED25519,
    key_name: str = "id_key",
    passphrase: Optional[str] = None,
    comment: Optional[str] = None
) -> Tuple[str, str]
```

**Parameters:**
- `key_type` (KeyType): Type of key to generate. Options: `KeyType.RSA_2048`, `KeyType.RSA_4096`, `KeyType.ED25519`. Default: `KeyType.ED25519`
- `key_name` (str): Name for the key pair. Default: `"id_key"`
- `passphrase` (Optional[str]): Passphrase to encrypt private key. Default: `None`
- `comment` (Optional[str]): Comment for public key. Default: `None`

**Returns:**
- `Tuple[str, str]`: (private_key_path, public_key_path)

**Example:**
```python
private_path, public_path = ssh_manager.generate_ssh_key_pair(
    key_type=KeyType.ED25519,
    key_name="github_deploy_key",
    passphrase="my-secure-passphrase",
    comment="deploy@myserver"
)
# Returns: ("/var/secure/ssh/github_deploy_key", "/var/secure/ssh/github_deploy_key.pub")
```

---

### validate_ssh_key()

Validate SSH key format and integrity.

```python
def validate_ssh_key(key_content: str) -> bool
```

**Parameters:**
- `key_content` (str): SSH key content (private or public)

**Returns:**
- `bool`: `True` if valid, `False` otherwise

**Example:**
```python
is_valid = ssh_manager.validate_ssh_key(my_key_content)
# Returns: True
```

---

### get_key_fingerprint()

Generate SSH key fingerprint.

```python
def get_key_fingerprint(key_content: str, hash_algo: str = "sha256") -> str
```

**Parameters:**
- `key_content` (str): SSH key content
- `hash_algo` (str): Hash algorithm. Options: `"sha256"`, `"md5"`. Default: `"sha256"`

**Returns:**
- `str`: Key fingerprint

**Example:**
```python
fingerprint = ssh_manager.get_key_fingerprint(my_key)
# Returns: "SHA256:abc123def456..."
```

---

### rotate_ssh_key()

Rotate SSH key by generating a new pair and backing up the old one.

```python
def rotate_ssh_key(key_name: str, backup: bool = True) -> Tuple[str, str]
```

**Parameters:**
- `key_name` (str): Name of the key to rotate
- `backup` (bool): Whether to backup old key. Default: `True`

**Returns:**
- `Tuple[str, str]`: (new_private_path, new_public_path)

**Example:**
```python
new_private, new_public = ssh_manager.rotate_ssh_key("github_deploy_key")
# Returns: ("/var/secure/ssh/github_deploy_key", "/var/secure/ssh/github_deploy_key.pub")
# Old key backed up to: github_deploy_key.backup.1234567890
```

---

### add_passphrase_to_key()

Add or change passphrase on an SSH key.

```python
def add_passphrase_to_key(
    key_path: str,
    new_passphrase: str,
    old_passphrase: Optional[str] = None
) -> bool
```

**Parameters:**
- `key_path` (str): Path to the SSH private key
- `new_passphrase` (str): New passphrase to set
- `old_passphrase` (Optional[str]): Current passphrase if key is encrypted. Default: `None`

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
success = ssh_manager.add_passphrase_to_key(
    "/var/secure/ssh/my_key",
    "new-secure-password",
    old_passphrase="old-password"
)
# Returns: True
```

---

### remove_passphrase_from_key()

Remove passphrase from an SSH key.

```python
def remove_passphrase_from_key(key_path: str, passphrase: str) -> bool
```

**Parameters:**
- `key_path` (str): Path to the SSH private key
- `passphrase` (str): Current passphrase

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
success = ssh_manager.remove_passphrase_from_key(
    "/var/secure/ssh/my_key",
    "current-password"
)
# Returns: True
```

---

### add_to_authorized_keys()

Add public key to authorized_keys file.

```python
def add_to_authorized_keys(
    public_key: str,
    authorized_keys_path: str = "~/.ssh/authorized_keys",
    comment: Optional[str] = None
) -> bool
```

**Parameters:**
- `public_key` (str): Public key content
- `authorized_keys_path` (str): Path to authorized_keys file. Default: `"~/.ssh/authorized_keys"`
- `comment` (Optional[str]): Comment to append to key. Default: `None`

**Returns:**
- `bool`: `True` if added, `False` if already exists

**Example:**
```python
success = ssh_manager.add_to_authorized_keys(
    public_key_content,
    comment="user@hostname"
)
# Returns: True
```

---

### list_ssh_keys()

List all managed SSH keys.

```python
def list_ssh_keys() -> List[Dict]
```

**Parameters:** None

**Returns:**
- `List[Dict]`: List of key information dictionaries

**Output Format:**
```python
[
    {
        "name": "github_key",
        "path": "/var/secure/ssh/github_key",
        "type": "ed25519",
        "created_at": "2024-01-08T10:30:00",
        "has_passphrase": True,
        "fingerprint": "SHA256:abc123..."
    }
]
```

**Example:**
```python
keys = ssh_manager.list_ssh_keys()
for key in keys:
    print(f"{key['name']}: {key['fingerprint']}")
```

---

### delete_ssh_key()

Securely delete an SSH key pair.

```python
def delete_ssh_key(key_name: str, secure_delete: bool = True) -> bool
```

**Parameters:**
- `key_name` (str): Name of the key to delete
- `secure_delete` (bool): Overwrite with random data before deletion. Default: `True`

**Returns:**
- `bool`: `True` if deleted, `False` if not found

**Example:**
```python
success = ssh_manager.delete_ssh_key("old_key", secure_delete=True)
# Returns: True
```

---

### export_public_key()

Export public key in specified format.

```python
def export_public_key(key_name: str, format: str = "openssh") -> Optional[str]
```

**Parameters:**
- `key_name` (str): Name of the key
- `format` (str): Output format. Options: `"openssh"`, `"rfc4716"`. Default: `"openssh"`

**Returns:**
- `Optional[str]`: Public key content or `None` if not found

**Example:**
```python
public_key = ssh_manager.export_public_key("my_key", format="openssh")
# Returns: "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5..."
```

---

### batch_generate_keys()

Generate multiple SSH key pairs.

```python
def batch_generate_keys(
    count: int,
    prefix: str = "key",
    key_type: KeyType = KeyType.ED25519
) -> List[Tuple[str, str]]
```

**Parameters:**
- `count` (int): Number of key pairs to generate
- `prefix` (str): Prefix for key names. Default: `"key"`
- `key_type` (KeyType): Type of keys. Default: `KeyType.ED25519`

**Returns:**
- `List[Tuple[str, str]]`: List of (private_path, public_path) tuples

**Example:**
```python
keys = ssh_manager.batch_generate_keys(5, prefix="deploy")
# Returns: [
#   ("/var/secure/ssh/deploy_1", "/var/secure/ssh/deploy_1.pub"),
#   ("/var/secure/ssh/deploy_2", "/var/secure/ssh/deploy_2.pub"),
#   ...
# ]
```

---

### get_audit_log()

Retrieve SSH key audit log.

```python
def get_audit_log(
    action: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Dict]
```

**Parameters:**
- `action` (Optional[str]): Filter by action type. Default: `None` (all actions)
- `start_time` (Optional[datetime]): Start time filter. Default: `None`
- `end_time` (Optional[datetime]): End time filter. Default: `None`

**Returns:**
- `List[Dict]`: List of audit log entries

**Output Format:**
```python
[
    {
        "timestamp": "2024-01-08T10:30:00",
        "action": "ssh_key_generated",
        "user": "system",
        "resource": "deploy_key",
        "result": "success",
        "metadata": {}
    }
]
```

---

### cleanup()

Remove all temporary key files.

```python
def cleanup()
```

**Parameters:** None

**Returns:** None

**Example:**
```python
ssh_manager.cleanup()
```

---

## SecretManager

Manages encrypted secrets with versioning and rotation.

### Constructor

```python
SecretManager(
    master_key: Optional[str] = None,
    storage_dir: str = "/var/secure/secrets"
)
```

**Parameters:**
- `master_key` (Optional[str]): Master encryption key. If `None`, generates new key. Default: `None`
- `storage_dir` (str): Directory for storing secrets. Default: `/var/secure/secrets`

**Returns:** `SecretManager` instance

---

### encrypt_secret()

Encrypt a secret and store with metadata.

```python
def encrypt_secret(
    secret_value: str,
    secret_name: str,
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET,
    expires_in_days: Optional[int] = None,
    tags: Optional[Dict[str, str]] = None
) -> str
```

**Parameters:**
- `secret_value` (str): Secret value to encrypt
- `secret_name` (str): Name/identifier for the secret
- `algorithm` (EncryptionAlgorithm): Encryption algorithm. Options: `EncryptionAlgorithm.FERNET`, `EncryptionAlgorithm.AES_256_GCM`. Default: `FERNET`
- `expires_in_days` (Optional[int]): Days until expiration. Default: `None` (no expiration)
- `tags` (Optional[Dict[str, str]]): Metadata tags. Default: `None`

**Returns:**
- `str`: Secret ID (UUID)

**Example:**
```python
secret_manager = SecretManager()
secret_id = secret_manager.encrypt_secret(
    "my-database-password",
    "db_password",
    expires_in_days=90,
    tags={"env": "production", "service": "postgres"}
)
# Returns: "550e8400-e29b-41d4-a716-446655440000"
```

---

### decrypt_secret()

Decrypt a secret by ID.

```python
def decrypt_secret(secret_id: str) -> Optional[str]
```

**Parameters:**
- `secret_id` (str): Secret ID (UUID)

**Returns:**
- `Optional[str]`: Decrypted secret value or `None` if not found/expired

**Example:**
```python
secret_value = secret_manager.decrypt_secret("550e8400-e29b-41d4-a716-446655440000")
# Returns: "my-database-password"
```

---

### rotate_secret()

Rotate a secret with a new value.

```python
def rotate_secret(secret_id: str, new_value: str) -> bool
```

**Parameters:**
- `secret_id` (str): Secret ID
- `new_value` (str): New secret value

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
success = secret_manager.rotate_secret(
    "550e8400-e29b-41d4-a716-446655440000",
    "new-password-123"
)
# Returns: True
# Old version backed up as: 550e8400-e29b-41d4-a716-446655440000.enc.v0
```

---

### delete_secret()

Delete a secret securely.

```python
def delete_secret(secret_id: str, secure_delete: bool = True) -> bool
```

**Parameters:**
- `secret_id` (str): Secret ID
- `secure_delete` (bool): Overwrite with random data. Default: `True`

**Returns:**
- `bool`: `True` if deleted, `False` if not found

**Example:**
```python
success = secret_manager.delete_secret("550e8400-e29b-41d4-a716-446655440000")
# Returns: True
```

---

### list_secrets()

List all secrets with optional filtering.

```python
def list_secrets(tag_filter: Optional[Dict[str, str]] = None) -> List[Dict]
```

**Parameters:**
- `tag_filter` (Optional[Dict[str, str]]): Filter by tags. Default: `None` (all secrets)

**Returns:**
- `List[Dict]`: List of secret metadata

**Output Format:**
```python
[
    {
        "secret_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "db_password",
        "created_at": "2024-01-08T10:30:00",
        "expires_at": "2024-04-08T10:30:00",
        "rotation_count": 2,
        "tags": {"env": "production"}
    }
]
```

**Example:**
```python
# List all production secrets
prod_secrets = secret_manager.list_secrets(tag_filter={"env": "production"})
```

---

### export_secrets()

Export secrets to encrypted backup file.

```python
def export_secrets(output_file: str, secret_ids: Optional[List[str]] = None)
```

**Parameters:**
- `output_file` (str): Path to output backup file
- `secret_ids` (Optional[List[str]]): List of secret IDs to export. Default: `None` (all secrets)

**Returns:** None

**Raises:**
- `Exception`: If export fails

**Example:**
```python
secret_manager.export_secrets("backup_2024.enc", secret_ids=[secret_id1, secret_id2])
```

---

### import_secrets()

Import secrets from encrypted backup file.

```python
def import_secrets(import_file: str) -> int
```

**Parameters:**
- `import_file` (str): Path to backup file

**Returns:**
- `int`: Number of secrets imported

**Example:**
```python
count = secret_manager.import_secrets("backup_2024.enc")
# Returns: 15
```

---

## PasswordManager

Manages password hashing, validation, and generation.

### Constructor

```python
PasswordManager(hash_method: PasswordHashMethod = PasswordHashMethod.BCRYPT)
```

**Parameters:**
- `hash_method` (PasswordHashMethod): Hashing method. Options: `PasswordHashMethod.BCRYPT`, `PasswordHashMethod.ARGON2`, `PasswordHashMethod.PBKDF2`, `PasswordHashMethod.SCRYPT`. Default: `BCRYPT`

**Returns:** `PasswordManager` instance

---

### hash_password()

Hash a password using configured method.

```python
def hash_password(password: str) -> str
```

**Parameters:**
- `password` (str): Plain text password

**Returns:**
- `str`: Hashed password

**Example:**
```python
pwd_manager = PasswordManager(hash_method=PasswordHashMethod.BCRYPT)
hashed = pwd_manager.hash_password("MySecurePassword123!")
# Returns: "$2b$12$KIXxGVXqZ..."
```

---

### verify_password()

Verify a password against its hash.

```python
def verify_password(password: str, hashed_password: str) -> bool
```

**Parameters:**
- `password` (str): Plain text password
- `hashed_password` (str): Hashed password to verify against

**Returns:**
- `bool`: `True` if match, `False` otherwise

**Example:**
```python
is_valid = pwd_manager.verify_password("MySecurePassword123!", hashed)
# Returns: True
```

---

### generate_password()

Generate a secure random password.

```python
def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    exclude_ambiguous: bool = True
) -> str
```

**Parameters:**
- `length` (int): Password length. Default: `16`
- `include_uppercase` (bool): Include uppercase letters. Default: `True`
- `include_lowercase` (bool): Include lowercase letters. Default: `True`
- `include_digits` (bool): Include digits. Default: `True`
- `include_symbols` (bool): Include special characters. Default: `True`
- `exclude_ambiguous` (bool): Exclude ambiguous characters (il1Lo0O). Default: `True`

**Returns:**
- `str`: Generated password

**Example:**
```python
password = pwd_manager.generate_password(
    length=20,
    include_symbols=True,
    exclude_ambiguous=True
)
# Returns: "K7#mN2@pQ9!vR4$wX8"
```

---

### check_password_strength()

Analyze password strength.

```python
def check_password_strength(password: str) -> Dict[str, Any]
```

**Parameters:**
- `password` (str): Password to analyze

**Returns:**
- `Dict[str, Any]`: Strength analysis

**Output Format:**
```python
{
    "strength": "strong",           # "weak", "medium", or "strong"
    "score": 6,                     # Numeric score (0-8)
    "entropy": 95.23,               # Bits of entropy
    "feedback": [],                 # List of improvement suggestions
    "length": 16,
    "has_lowercase": True,
    "has_uppercase": True,
    "has_digits": True,
    "has_symbols": True
}
```

**Example:**
```python
strength = pwd_manager.check_password_strength("MyP@ssw0rd123")
print(f"Strength: {strength['strength']}")
print(f"Entropy: {strength['entropy']} bits")
```

---

### calculate_password_entropy()

Calculate password entropy in bits.

```python
def calculate_password_entropy(password: str) -> float
```

**Parameters:**
- `password` (str): Password to analyze

**Returns:**
- `float`: Entropy in bits

**Example:**
```python
entropy = pwd_manager.calculate_password_entropy("MyP@ssw0rd123")
# Returns: 72.5
```

---

### validate_password_policy()

Validate password against policy requirements.

```python
def validate_password_policy(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_symbol: bool = True,
    max_repeated_chars: int = 3
) -> Tuple[bool, List[str]]
```

**Parameters:**
- `password` (str): Password to validate
- `min_length` (int): Minimum length. Default: `8`
- `require_uppercase` (bool): Require uppercase. Default: `True`
- `require_lowercase` (bool): Require lowercase. Default: `True`
- `require_digit` (bool): Require digit. Default: `True`
- `require_symbol` (bool): Require special character. Default: `True`
- `max_repeated_chars` (int): Max repeated characters. Default: `3`

**Returns:**
- `Tuple[bool, List[str]]`: (is_valid, list_of_errors)

**Example:**
```python
is_valid, errors = pwd_manager.validate_password_policy(
    "short",
    min_length=8,
    require_uppercase=True
)
# Returns: (False, ["Password must be at least 8 characters", "Password must contain uppercase letters"])
```

---

### check_password_history()

Check if password was recently used.

```python
def check_password_history(
    user_id: str,
    password: str,
    history_size: int = 5
) -> bool
```

**Parameters:**
- `user_id` (str): User identifier
- `password` (str): Password to check
- `history_size` (int): Number of previous passwords to check. Default: `5`

**Returns:**
- `bool`: `True` if password is new (not in history), `False` if reused

**Example:**
```python
is_new = pwd_manager.check_password_history("user123", "NewPassword123!")
# Returns: True
```

---

### add_to_password_history()

Add password hash to user's history.

```python
def add_to_password_history(user_id: str, password_hash: str)
```

**Parameters:**
- `user_id` (str): User identifier
- `password_hash` (str): Hashed password

**Returns:** None

**Example:**
```python
hashed = pwd_manager.hash_password("NewPassword123!")
pwd_manager.add_to_password_history("user123", hashed)
```

---

## APIKeyManager

Manages API keys with permissions and rate limiting.

### Constructor

```python
APIKeyManager(storage_dir: str = "/var/secure/api_keys")
```

**Parameters:**
- `storage_dir` (str): Directory for storing API keys. Default: `/var/secure/api_keys`

**Returns:** `APIKeyManager` instance

---

### generate_api_key()

Generate a new API key.

```python
def generate_api_key(
    name: str,
    permissions: List[str],
    expires_in_days: Optional[int] = None,
    rate_limit: int = 1000
) -> APIKey
```

**Parameters:**
- `name` (str): Name/description for the API key
- `permissions` (List[str]): List of permission strings
- `expires_in_days` (Optional[int]): Days until expiration. Default: `None` (no expiration)
- `rate_limit` (int): Requests per period. Default: `1000`

**Returns:**
- `APIKey`: API key object

**Output Format:**
```python
APIKey(
    key_id="550e8400-e29b-41d4-a716-446655440000",
    key="sk_abc123def456...",
    name="production_api",
    permissions=["read", "write"],
    created_at=datetime(2024, 1, 8, 10, 30),
    expires_at=datetime(2024, 4, 8, 10, 30),
    last_used=None,
    rate_limit=1000,
    enabled=True
)
```

**Example:**
```python
api_manager = APIKeyManager()
api_key = api_manager.generate_api_key(
    "production_service",
    permissions=["read", "write", "delete"],
    expires_in_days=365,
    rate_limit=5000
)
print(f"API Key: {api_key.key}")
```

---

### validate_api_key()

Validate an API key and check permissions.

```python
def validate_api_key(
    key: str,
    required_permission: Optional[str] = None
) -> Tuple[bool, Optional[str]]
```

**Parameters:**
- `key` (str): API key to validate
- `required_permission` (Optional[str]): Required permission to check. Default: `None`

**Returns:**
- `Tuple[bool, Optional[str]]`: (is_valid, error_message)

**Example:**
```python
is_valid, error = api_manager.validate_api_key(
    "sk_abc123...",
    required_permission="write"
)
if is_valid:
    print("API key is valid")
else:
    print(f"Invalid: {error}")
# Returns: (True, None) or (False, "Missing permission: write")
```

---

### revoke_api_key()

Revoke an API key.

```python
def revoke_api_key(key: str) -> bool
```

**Parameters:**
- `key` (str): API key to revoke

**Returns:**
- `bool`: `True` if revoked, `False` if not found

**Example:**
```python
success = api_manager.revoke_api_key("sk_abc123...")
# Returns: True
```

---

### list_api_keys()

List all API keys (without exposing actual keys).

```python
def list_api_keys() -> List[Dict]
```

**Parameters:** None

**Returns:**
- `List[Dict]`: List of API key information

**Output Format:**
```python
[
    {
        "key_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "production_api",
        "permissions": ["read", "write"],
        "created_at": "2024-01-08T10:30:00",
        "expires_at": "2024-04-08T10:30:00",
        "enabled": True,
        "usage_count": 1523
    }
]
```

---

### reset_rate_limits()

Reset all rate limit counters.

```python
def reset_rate_limits()
```

**Parameters:** None

**Returns:** None

**Example:**
```python
api_manager.reset_rate_limits()
```

---

## CertificateManager

Manages SSL/TLS certificates.

### Constructor

```python
CertificateManager(storage_dir: str = "/var/secure/certs")
```

**Parameters:**
- `storage_dir` (str): Directory for storing certificates. Default: `/var/secure/certs`

**Returns:** `CertificateManager` instance

---

### generate_self_signed_cert()

Generate a self-signed SSL certificate.

```python
def generate_self_signed_cert(
    common_name: str,
    organization: str = "Nexus",
    country: str = "US",
    validity_days: int = 365,
    dns_names: Optional[List[str]] = None
) -> Tuple[str, str]
```

**Parameters:**
- `common_name` (str): Common Name (CN) for the certificate
- `organization` (str): Organization name. Default: `"Nexus"`
- `country` (str): Country code. Default: `"US"`
- `validity_days` (int): Certificate validity in days. Default: `365`
- `dns_names` (Optional[List[str]]): Subject Alternative Names. Default: `None`

**Returns:**
- `Tuple[str, str]`: (cert_path, key_path)

**Example:**
```python
cert_manager = CertificateManager()
cert_path, key_path = cert_manager.generate_self_signed_cert(
    "example.com",
    organization="MyCompany",
    validity_days=730,
    dns_names=["example.com", "*.example.com", "api.example.com"]
)
# Returns: ("/var/secure/certs/example.com.crt", "/var/secure/certs/example.com.key")
```

---

### check_certificate_expiration()

Check certificate expiration status.

```python
def check_certificate_expiration(cert_path: str) -> Dict[str, Any]
```

**Parameters:**
- `cert_path` (str): Path to certificate file

**Returns:**
- `Dict[str, Any]`: Expiration information

**Output Format:**
```python
{
    "is_expired": False,
    "not_before": "2024-01-08T10:30:00",
    "not_after": "2025-01-08T10:30:00",
    "days_until_expiry": 365,
    "expires_soon": False,
    "subject": "CN=example.com,O=MyCompany,C=US",
    "issuer": "CN=example.com,O=MyCompany,C=US"
}
```

**Example:**
```python
info = cert_manager.check_certificate_expiration("/var/secure/certs/example.com.crt")
if info['expires_soon']:
    print(f"Certificate expires in {info['days_until_expiry']} days!")
```

---

### validate_certificate()

Validate certificate format and expiration.

```python
def validate_certificate(cert_path: str) -> Tuple[bool, str]
```

**Parameters:**
- `cert_path` (str): Path to certificate file

**Returns:**
- `Tuple[bool, str]`: (is_valid, message)

**Example:**
```python
is_valid, message = cert_manager.validate_certificate("/var/secure/certs/example.com.crt")
# Returns: (True, "Certificate is valid") or (False, "Certificate has expired")
```

---

### get_certificate_info()

Get detailed certificate information.

```python
def get_certificate_info(cert_path: str) -> Dict[str, Any]
```

**Parameters:**
- `cert_path` (str): Path to certificate file

**Returns:**
- `Dict[str, Any]`: Certificate details

**Output Format:**
```python
{
    "version": "v3",
    "serial_number": 123456789,
    "subject": "CN=example.com,O=MyCompany,C=US",
    "issuer": "CN=example.com,O=MyCompany,C=US",
    "not_before": "2024-01-08T10:30:00",
    "not_after": "2025-01-08T10:30:00",
    "signature_algorithm": "sha256WithRSAEncryption"
}
```

---

### convert_certificate_format()

Convert certificate between PEM and DER formats.

```python
def convert_certificate_format(
    input_path: str,
    output_path: str,
    output_format: str = "DER"
) -> bool
```

**Parameters:**
- `input_path` (str): Input certificate path
- `output_path` (str): Output certificate path
- `output_format` (str): Output format. Options: `"PEM"`, `"DER"`. Default: `"DER"`

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
success = cert_manager.convert_certificate_format(
    "/var/secure/certs/example.com.crt",
    "/var/secure/certs/example.com.der",
    output_format="DER"
)
# Returns: True
```

---

## TokenManager

Manages JWT tokens.

### Constructor

```python
TokenManager(secret_key: Optional[str] = None)
```

**Parameters:**
- `secret_key` (Optional[str]): Secret key for signing tokens. If `None`, generates new key. Default: `None`

**Returns:** `TokenManager` instance

---

### generate_token()

Generate a JWT token.

```python
def generate_token(
    user_id: str,
    claims: Optional[Dict[str, Any]] = None,
    expires_in_minutes: int = 60
) -> str
```

**Parameters:**
- `user_id` (str): User identifier
- `claims` (Optional[Dict[str, Any]]): Additional claims to include. Default: `None`
- `expires_in_minutes` (int): Token expiration time in minutes. Default: `60`

**Returns:**
- `str`: JWT token

**Example:**
```python
token_manager = TokenManager()
token = token_manager.generate_token(
    "user123",
    claims={"role": "admin", "department": "engineering"},
    expires_in_minutes=120
)
# Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### verify_token()

Verify a JWT token.

```python
def verify_token(token: str) -> Tuple[bool, Optional[Dict], Optional[str]]
```

**Parameters:**
- `token` (str): JWT token to verify

**Returns:**
- `Tuple[bool, Optional[Dict], Optional[str]]`: (is_valid, payload, error_message)

**Output Format:**
```python
# Success
(True, {
    "user_id": "user123",
    "role": "admin",
    "iat": 1704710400,
    "exp": 1704714000,
    "jti": "550e8400-e29b-41d4-a716-446655440000"
}, None)

# Failure
(False, None, "Token has expired")
```

**Example:**
```python
is_valid, payload, error = token_manager.verify_token(token)
if is_valid:
    print(f"Token valid for user: {payload['user_id']}")
else:
    print(f"Invalid token: {error}")
```

---

### refresh_token()

Generate a new token from an existing token.

```python
def refresh_token(token: str, expires_in_minutes: int = 60) -> Optional[str]
```

**Parameters:**
- `token` (str): Existing JWT token
- `expires_in_minutes` (int): New token expiration time. Default: `60`

**Returns:**
- `Optional[str]`: New JWT token or `None` if original token is invalid

**Example:**
```python
new_token = token_manager.refresh_token(old_token, expires_in_minutes=120)
# Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." (new token)
```

---

### revoke_token()

Revoke a token by adding to blacklist.

```python
def revoke_token(token: str) -> bool
```

**Parameters:**
- `token` (str): JWT token to revoke

**Returns:**
- `bool`: `True` if revoked, `False` if token is invalid

**Example:**
```python
success = token_manager.revoke_token(token)
# Returns: True
```

---

### cleanup_blacklist()

Clear expired tokens from blacklist.

```python
def cleanup_blacklist()
```

**Parameters:** None

**Returns:** None

**Example:**
```python
token_manager.cleanup_blacklist()
```

---

## TwoFactorAuthManager

Manages TOTP-based two-factor authentication.

### Constructor

```python
TwoFactorAuthManager()
```

**Parameters:** None

**Returns:** `TwoFactorAuthManager` instance

---

### generate_totp_secret()

Generate a TOTP secret for a user.

```python
def generate_totp_secret(user_id: str, issuer: str = "Nexus") -> Dict[str, str]
```

**Parameters:**
- `user_id` (str): User identifier
- `issuer` (str): Application name. Default: `"Nexus"`

**Returns:**
- `Dict[str, str]`: TOTP configuration

**Output Format:**
```python
{
    "secret": "JBSWY3DPEHPK3PXP",
    "provisioning_uri": "otpauth://totp/Nexus:user123?secret=JBSWY3DPEHPK3PXP&issuer=Nexus",
    "user_id": "user123"
}
```

**Example:**
```python
tfa_manager = TwoFactorAuthManager()
totp_data = tfa_manager.generate_totp_secret("user123", issuer="MyApp")
print(f"Secret: {totp_data['secret']}")
print(f"Scan this URI: {totp_data['provisioning_uri']}")
```

---

### generate_qr_code()

Generate a QR code for TOTP setup.

```python
def generate_qr_code(provisioning_uri: str, output_path: str) -> bool
```

**Parameters:**
- `provisioning_uri` (str): TOTP provisioning URI
- `output_path` (str): Path to save QR code image

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
success = tfa_manager.generate_qr_code(
    totp_data['provisioning_uri'],
    "/tmp/qr_code.png"
)
# Returns: True
# QR code saved to: /tmp/qr_code.png
```

---

### verify_totp_code()

Verify a TOTP code.

```python
def verify_totp_code(secret: str, code: str, window: int = 1) -> bool
```

**Parameters:**
- `secret` (str): TOTP secret
- `code` (str): 6-digit TOTP code to verify
- `window` (int): Time window tolerance (±30s per window). Default: `1`

**Returns:**
- `bool`: `True` if valid, `False` otherwise

**Example:**
```python
is_valid = tfa_manager.verify_totp_code(
    "JBSWY3DPEHPK3PXP",
    "123456"
)
# Returns: True or False
```

---

### generate_backup_codes()

Generate backup codes for 2FA recovery.

```python
def generate_backup_codes(user_id: str, count: int = 10) -> List[str]
```

**Parameters:**
- `user_id` (str): User identifier
- `count` (int): Number of backup codes to generate. Default: `10`

**Returns:**
- `List[str]`: List of backup codes

**Example:**
```python
backup_codes = tfa_manager.generate_backup_codes("user123", count=10)
# Returns: ["ABCD-EFGH", "IJKL-MNOP", "QRST-UVWX", ...]
```

---

### verify_backup_code()

Verify and consume a backup code.

```python
def verify_backup_code(user_id: str, code: str) -> bool
```

**Parameters:**
- `user_id` (str): User identifier
- `code` (str): Backup code to verify

**Returns:**
- `bool`: `True` if valid (code is consumed), `False` otherwise

**Example:**
```python
is_valid = tfa_manager.verify_backup_code("user123", "ABCD-EFGH")
# Returns: True (code is now used and cannot be reused)
```

---

## AccessControlManager

Manages role-based access control (RBAC).

### Constructor

```python
AccessControlManager()
```

**Parameters:** None

**Returns:** `AccessControlManager` instance

---

### define_role()

Define a role with permissions.

```python
def define_role(role_name: str, permissions: List[str]) -> bool
```

**Parameters:**
- `role_name` (str): Name of the role
- `permissions` (List[str]): List of permission strings

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
rbac = AccessControlManager()

rbac.define_role("admin", ["*"])  # All permissions
rbac.define_role("editor", ["read", "write", "update"])
rbac.define_role("viewer", ["read"])
# Returns: True
```

---

### assign_role()

Assign a role to a user.

```python
def assign_role(user_id: str, role_name: str) -> bool
```

**Parameters:**
- `user_id` (str): User identifier
- `role_name` (str): Role to assign

**Returns:**
- `bool`: `True` if assigned, `False` if role doesn't exist

**Example:**
```python
success = rbac.assign_role("user123", "editor")
# Returns: True
```

---

### check_permission()

Check if a user has a required permission.

```python
def check_permission(
    user_id: str,
    required_permission: str,
    resource: Optional[str] = None
) -> bool
```

**Parameters:**
- `user_id` (str): User identifier
- `required_permission` (str): Permission to check
- `resource` (Optional[str]): Resource identifier for audit logging. Default: `None`

**Returns:**
- `bool`: `True` if user has permission, `False` otherwise

**Example:**
```python
can_write = rbac.check_permission("user123", "write")
# Returns: True

can_delete = rbac.check_permission("user123", "delete")
# Returns: False
```

---

### set_role_hierarchy()

Set role inheritance.

```python
def set_role_hierarchy(role: str, inherits_from: List[str]) -> bool
```

**Parameters:**
- `role` (str): Role name
- `inherits_from` (List[str]): Roles to inherit permissions from

**Returns:**
- `bool`: `True` if successful, `False` otherwise

**Example:**
```python
rbac.define_role("super_admin", ["admin_panel"])
rbac.define_role("admin", ["user_management"])

# super_admin inherits from admin
rbac.set_role_hierarchy("super_admin", ["admin"])
# super_admin now has: ["admin_panel", "user_management"]
```

---

### get_user_permissions()

Get all permissions for a user.

```python
def get_user_permissions(user_id: str) -> List[str]
```

**Parameters:**
- `user_id` (str): User identifier

**Returns:**
- `List[str]`: List of permissions

**Example:**
```python
permissions = rbac.get_user_permissions("user123")
# Returns: ["read", "write", "update"]
```

---

### get_audit_log()

Get access control audit log.

```python
def get_audit_log() -> List[Dict]
```

**Parameters:** None

**Returns:**
- `List[Dict]`: List of audit log entries

**Output Format:**
```python
[
    {
        "timestamp": "2024-01-08T10:30:00",
        "action": "permission_check",
        "user": "user123",
        "resource": "write",
        "result": "granted",
        "metadata": {"resource": "document_123"}
    }
]
```

---

## EnterpriseSecurityManager

Main class that integrates all security managers.

### Constructor

```python
EnterpriseSecurityManager(
    storage_base_dir: str = "/var/secure",
    master_key: Optional[str] = None
)
```

**Parameters:**
- `storage_base_dir` (str): Base directory for all storage. Default: `"/var/secure"`
- `master_key` (Optional[str]): Master encryption key. Default: `None` (generates new)

**Returns:** `EnterpriseSecurityManager` instance

**Example:**
```python
security = EnterpriseSecurityManager(
    storage_base_dir="/opt/secure",
    master_key="my-master-key-123"
)
```

---

### Properties

Access individual managers through properties:

```python
security.ssh_keys          # SSHKeyManager
security.secrets           # SecretManager
security.passwords         # PasswordManager
security.api_keys          # APIKeyManager
security.certificates      # CertificateManager
security.tokens            # TokenManager
security.two_factor        # TwoFactorAuthManager
security.access_control    # AccessControlManager
```

---

### get_security_status()

Get overall security system status.

```python
def get_security_status() -> Dict[str, Any]
```

**Parameters:** None

**Returns:**
- `Dict[str, Any]`: Security status summary

**Output Format:**
```python
{
    "ssh_keys": 5,              # Number of SSH keys
    "secrets": 12,              # Number of secrets
    "api_keys": 3,              # Number of API keys
    "roles_defined": 4,         # Number of roles
    "users_with_roles": 15,     # Number of users with roles
    "audit_entries": 247        # Total audit log entries
}
```

**Example:**
```python
status = security.get_security_status()
print(f"Total secrets: {status['secrets']}")
print(f"Total audit entries: {status['audit_entries']}")
```

---

### export_audit_logs()

Export all audit logs to a file.

```python
def export_audit_logs(output_file: str)
```

**Parameters:**
- `output_file` (str): Path to output JSON file

**Returns:** None

**Example:**
```python
security.export_audit_logs("/tmp/audit_logs_2024.json")
```

---

## Data Classes

### SecretMetadata

Metadata for encrypted secrets.

```python
@dataclass
class SecretMetadata:
    secret_id: str
    name: str
    algorithm: EncryptionAlgorithm
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    rotation_count: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
```

---

### APIKey

API key structure.

```python
@dataclass
class APIKey:
    key_id: str
    key: str
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    rate_limit: int = 1000
    enabled: bool = True
```

---

### AuditEntry

Security audit log entry.

```python
@dataclass
class AuditEntry:
    timestamp: datetime
    action: str
    user: str
    resource: str
    result: str
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Enums

### KeyType

SSH/Crypto key types.

```python
class KeyType(Enum):
    RSA_2048 = "rsa2048"
    RSA_4096 = "rsa4096"
    ED25519 = "ed25519"
    ECDSA = "ecdsa"
```

---

### EncryptionAlgorithm

Supported encryption algorithms.

```python
class EncryptionAlgorithm(Enum):
    FERNET = "fernet"
    AES_256_GCM = "aes256gcm"
    AES_256_CBC = "aes256cbc"
    CHACHA20 = "chacha20"
    RSA_2048 = "rsa2048"
    RSA_4096 = "rsa4096"
```

---

### PasswordHashMethod

Password hashing methods.

```python
class PasswordHashMethod(Enum):
    BCRYPT = "bcrypt"
    ARGON2 = "argon2"
    PBKDF2 = "pbkdf2"
    SCRYPT = "scrypt"
```

---

### HashAlgorithm

Supported hash algorithms.

```python
class HashAlgorithm(Enum):
    SHA256 = "sha256"
    SHA512 = "sha512"
    SHA3_256 = "sha3_256"
    SHA3_512 = "sha3_512"
    BLAKE2B = "blake2b"
    BLAKE2S = "blake2s"
```

---

## Examples

### Complete Workflow Example

```python
from enterprise_security import EnterpriseSecurityManager, KeyType, PasswordHashMethod

# Initialize
security = EnterpriseSecurityManager(storage_base_dir="/var/secure")

# 1. Generate SSH key for deployment
private_key, public_key = security.ssh_keys.generate_ssh_key_pair(
    key_type=KeyType.ED25519,
    key_name="deploy_key",
    comment="deploy@production"
)
print(f"SSH Key: {private_key}")

# 2. Store database password
db_secret_id = security.secrets.encrypt_secret(
    "my-db-password-123",
    "production_db",
    expires_in_days=90,
    tags={"env": "production", "service": "postgres"}
)

# 3. Create user account with secure password
password = security.passwords.generate_password(length=20)
password_hash = security.passwords.hash_password(password)

# Check password strength
strength = security.passwords.check_password_strength(password)
print(f"Password strength: {strength['strength']}")

# 4. Generate API key for service
api_key = security.api_keys.generate_api_key(
    "backend_service",
    permissions=["read", "write"],
    expires_in_days=365
)
print(f"API Key: {api_key.key}")

# 5. Create SSL certificate
cert_path, key_path = security.certificates.generate_self_signed_cert(
    "api.example.com",
    dns_names=["api.example.com", "*.api.example.com"]
)

# 6. Generate JWT token
token = security.tokens.generate_token(
    "user123",
    claims={"role": "admin"},
    expires_in_minutes=60
)

# Verify token later
is_valid, payload, error = security.tokens.verify_token(token)
if is_valid:
    print(f"Valid token for: {payload['user_id']}")

# 7. Setup 2FA
totp_data = security.two_factor.generate_totp_secret("user123")
security.two_factor.generate_qr_code(
    totp_data['provisioning_uri'],
    "/tmp/qr_code.png"
)
backup_codes = security.two_factor.generate_backup_codes("user123")

# 8. Setup RBAC
security.access_control.define_role("admin", ["*"])
security.access_control.define_role("editor", ["read", "write"])
security.access_control.assign_role("user123", "admin")

can_delete = security.access_control.check_permission("user123", "delete")
print(f"Can delete: {can_delete}")

# 9. Get security status
status = security.get_security_status()
print(f"Security Status: {status}")

# 10. Export audit logs
security.export_audit_logs("/tmp/audit_logs.json")
```

---

### Password Management Example

```python
from enterprise_security import PasswordManager, PasswordHashMethod

# Initialize with bcrypt
pwd_manager = PasswordManager(hash_method=PasswordHashMethod.BCRYPT)

# Generate secure password
password = pwd_manager.generate_password(
    length=16,
    include_symbols=True,
    exclude_ambiguous=True
)
print(f"Generated: {password}")

# Check strength
strength = pwd_manager.check_password_strength(password)
print(f"Strength: {strength['strength']}")
print(f"Entropy: {strength['entropy']} bits")
print(f"Feedback: {strength['feedback']}")

# Hash password
hashed = pwd_manager.hash_password(password)

# Verify password
is_valid = pwd_manager.verify_password(password, hashed)
print(f"Verification: {is_valid}")

# Validate against policy
is_valid, errors = pwd_manager.validate_password_policy(
    password,
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_symbol=True
)
if not is_valid:
    print(f"Policy violations: {errors}")
```

---

### API Key Management Example

```python
from enterprise_security import APIKeyManager

api_manager = APIKeyManager()

# Generate API key
api_key = api_manager.generate_api_key(
    "mobile_app",
    permissions=["read", "write", "profile"],
    expires_in_days=180,
    rate_limit=10000
)

print(f"API Key ID: {api_key.key_id}")
print(f"API Key: {api_key.key}")

# Later, validate the key
is_valid, error = api_manager.validate_api_key(
    api_key.key,
    required_permission="write"
)

if is_valid:
    print("Access granted")
else:
    print(f"Access denied: {error}")

# List all API keys
keys = api_manager.list_api_keys()
for key in keys:
    print(f"{key['name']}: {key['usage_count']} requests")

# Revoke a key
api_manager.revoke_api_key(api_key.key)
```

---

### Certificate Management Example

```python
from enterprise_security import CertificateManager

cert_manager = CertificateManager()

# Generate certificate
cert_path, key_path = cert_manager.generate_self_signed_cert(
    "example.com",
    organization="MyCompany",
    validity_days=730,
    dns_names=["example.com", "www.example.com", "api.example.com"]
)

print(f"Certificate: {cert_path}")
print(f"Private Key: {key_path}")

# Check expiration
expiry_info = cert_manager.check_certificate_expiration(cert_path)
print(f"Expires in: {expiry_info['days_until_expiry']} days")
print(f"Expires soon: {expiry_info['expires_soon']}")

# Validate certificate
is_valid, message = cert_manager.validate_certificate(cert_path)
print(f"Valid: {is_valid} - {message}")

# Get certificate details
info = cert_manager.get_certificate_info(cert_path)
print(f"Subject: {info['subject']}")
print(f"Issuer: {info['issuer']}")
print(f"Valid from: {info['not_before']}")
print(f"Valid until: {info['not_after']}")
```

---

### Two-Factor Authentication Example

```python
from enterprise_security import TwoFactorAuthManager

tfa_manager = TwoFactorAuthManager()

# Setup TOTP for user
totp_data = tfa_manager.generate_totp_secret("user123", issuer="MyApp")
print(f"Secret: {totp_data['secret']}")
print(f"URI: {totp_data['provisioning_uri']}")

# Generate QR code
tfa_manager.generate_qr_code(
    totp_data['provisioning_uri'],
    "/tmp/user123_qr.png"
)
print("QR code saved. User should scan with authenticator app.")

# Generate backup codes
backup_codes = tfa_manager.generate_backup_codes("user123", count=10)
print("Backup codes:")
for code in backup_codes:
    print(f"  {code}")

# Later, verify TOTP code
user_code = input("Enter 6-digit code: ")
is_valid = tfa_manager.verify_totp_code(totp_data['secret'], user_code)

if is_valid:
    print("✓ Code verified")
else:
    print("✗ Invalid code")
    
    # Try backup code
    backup_code = input("Enter backup code: ")
    is_valid = tfa_manager.verify_backup_code("user123", backup_code)
    
    if is_valid:
        print("✓ Backup code accepted (now consumed)")
    else:
        print("✗ Invalid backup code")
```

---

### RBAC Example

```python
from enterprise_security import AccessControlManager

rbac = AccessControlManager()

# Define roles
rbac.define_role("admin", ["*"])
rbac.define_role("editor", ["read", "write", "update"])
rbac.define_role("contributor", ["read", "write"])
rbac.define_role("viewer", ["read"])

# Setup role hierarchy
rbac.set_role_hierarchy("editor", ["contributor"])  # editor inherits contributor perms

# Assign roles to users
rbac.assign_role("alice", "admin")
rbac.assign_role("bob", "editor")
rbac.assign_role("charlie", "viewer")

# Check permissions
print(f"Alice can delete: {rbac.check_permission('alice', 'delete')}")  # True
print(f"Bob can write: {rbac.check_permission('bob', 'write')}")        # True
print(f"Bob can delete: {rbac.check_permission('bob', 'delete')}")      # False
print(f"Charlie can read: {rbac.check_permission('charlie', 'read')}")  # True
print(f"Charlie can write: {rbac.check_permission('charlie', 'write')}") # False

# Get user permissions
bob_perms = rbac.get_user_permissions("bob")
print(f"Bob's permissions: {bob_perms}")

# View audit log
audit_log = rbac.get_audit_log()
for entry in audit_log[-5:]:  # Last 5 entries
    print(f"{entry['timestamp']}: {entry['user']} - {entry['action']} - {entry['result']}")
```

---

## Error Handling

All functions handle errors gracefully and log issues. Here's recommended error handling:

```python
from enterprise_security import EnterpriseSecurityManager

security = EnterpriseSecurityManager()

try:
    # Generate SSH key
    private, public = security.ssh_keys.generate_ssh_key_pair(
        key_type=KeyType.ED25519,
        key_name="deploy_key"
    )
    print(f"✓ Key generated: {private}")
    
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("Install with: pip install paramiko cryptography")
    
except PermissionError as e:
    print(f"✗ Permission denied: {e}")
    print("Check directory permissions")
    
except Exception as e:
    print(f"✗ Unexpected error: {e}")
```

---

## Best Practices

### 1. Secure Storage

```python
# ✓ Good: Use secure storage directory with proper permissions
security = EnterpriseSecurityManager(storage_base_dir="/var/secure")
os.chmod("/var/secure", 0o700)

# ✗ Bad: Use world-readable directory
security = EnterpriseSecurityManager(storage_base_dir="/tmp")
```

### 2. Key Rotation

```python
# ✓ Good: Rotate keys regularly
security.ssh_keys.rotate_ssh_key("deploy_key", backup=True)
security.secrets.rotate_secret(secret_id, "new-password")

# ✗ Bad: Never rotate keys
```

### 3. Password Policies

```python
# ✓ Good: Enforce strong password policy
is_valid, errors = security.passwords.validate_password_policy(
    password,
    min_length=12,
    require_uppercase=True,
    require_symbol=True
)

# ✗ Bad: Accept weak passwords
```

### 4. Cleanup

```python
# ✓ Good: Always cleanup temporary files
try:
    key_path = security.ssh_keys.create_temp_key_file(key_content)
    # Use key...
finally:
    security.ssh_keys.cleanup()

# ✗ Bad: Leave temporary files
```

### 5. Audit Logging

```python
# ✓ Good: Regularly export audit logs
security.export_audit_logs(f"/backups/audit_{datetime.now():%Y%m%d}.json")

# ✗ Bad: Never check audit logs
```

---

## Troubleshooting

### Issue: ImportError for optional dependencies

**Problem:** `ImportError: No module named 'bcrypt'`

**Solution:**
```bash
pip install bcrypt argon2-cffi passlib pyotp qrcode pyjwt
```

Or use alternative methods:
```python
# Use PBKDF2 instead of bcrypt (no extra dependencies)
pwd_manager = PasswordManager(hash_method=PasswordHashMethod.PBKDF2)

# Use Scrypt instead (built into cryptography)
pwd_manager = PasswordManager(hash_method=PasswordHashMethod.SCRYPT)
```

---

### Issue: Permission denied when creating directories

**Problem:** `PermissionError: [Errno 13] Permission denied: '/var/secure'`

**Solution:**
```bash
# Create directory with proper permissions
sudo mkdir -p /var/secure
sudo chown $USER:$USER /var/secure
chmod 700 /var/secure

# Or use user directory
security = EnterpriseSecurityManager(storage_base_dir="/home/user/.secure")
```

---

### Issue: SSH key validation fails

**Problem:** `validate_ssh_key()` returns `False` for valid key

**Solution:**
```python
# Ensure key is properly formatted with newlines
key_content = key_content.strip() + '\n'

# Check if key has proper headers
if not key_content.startswith('-----BEGIN'):
    print("Missing PEM header")

# Validate different key types
if 'OPENSSH PRIVATE KEY' in key_content:
    # Modern OpenSSH format
    pass
elif 'RSA PRIVATE KEY' in key_content:
    # Traditional PEM format
    pass
```

---

### Issue: Certificate expiration warnings

**Problem:** Certificate expires soon warnings

**Solution:**
```python
# Check all certificates regularly
cert_manager = CertificateManager()

for cert_file in Path("/var/secure/certs").glob("*.crt"):
    info = cert_manager.check_certificate_expiration(str(cert_file))
    
    if info['days_until_expiry'] < 30:
        print(f"⚠ Certificate {cert_file.name} expires in {info['days_until_expiry']} days")
        
        # Auto-renew
        common_name = cert_file.stem
        cert_manager.generate_self_signed_cert(
            common_name,
            validity_days=365
        )
```

---

### Issue: Rate limit exceeded for API keys

**Problem:** `validate_api_key()` returns "Rate limit exceeded"

**Solution:**
```python
# Reset rate limits periodically (e.g., hourly cron job)
api_manager.reset_rate_limits()

# Or increase rate limit for specific key
api_key = api_manager.generate_api_key(
    "high_traffic_service",
    permissions=["read"],
    rate_limit=100000  # Higher limit
)
```

---

### Issue: TOTP codes not working

**Problem:** `verify_totp_code()` returns `False` for valid codes

**Solution:**
```python
# Check time synchronization
import time
print(f"Server time: {time.time()}")

# Use wider time window
is_valid = tfa_manager.verify_totp_code(
    secret,
    code,
    window=2  # Allow ±60 seconds
)

# Ensure secret is properly saved
totp_data = tfa_manager.generate_totp_secret("user123")
# IMPORTANT: Save totp_data['secret'] to database
```

---

### Issue: JWT token verification fails

**Problem:** Token verification fails with "Invalid token"

**Solution:**
```python
# Ensure same secret key is used
token_manager1 = TokenManager(secret_key="my-secret-key")
token = token_manager1.generate_token("user123")

# Later (must use same secret key)
token_manager2 = TokenManager(secret_key="my-secret-key")
is_valid, payload, error = token_manager2.verify_token(token)

# Store secret key securely
import os
secret_key = os.getenv("JWT_SECRET_KEY")
token_manager = TokenManager(secret_key=secret_key)
```

---

## Performance Tips

### 1. Batch Operations

```python
# ✓ Efficient: Generate multiple keys at once
keys = ssh_manager.batch_generate_keys(10, prefix="worker")

# ✗ Inefficient: Generate keys one by one
for i in range(10):
    ssh_manager.generate_ssh_key_pair(key_name=f"worker_{i}")
```

---

### 2. Caching

```python
# ✓ Efficient: Cache frequently used secrets
class SecretCache:
    def __init__(self, secret_manager):
        self.manager = secret_manager
        self.cache = {}
    
    def get_secret(self, secret_id: str) -> str:
        if secret_id not in self.cache:
            self.cache[secret_id] = self.manager.decrypt_secret(secret_id)
        return self.cache[secret_id]

cache = SecretCache(security.secrets)
db_password = cache.get_secret(db_secret_id)
```

---

### 3. Async Operations

```python
# ✓ Efficient: Use async for I/O operations
import asyncio

async def generate_multiple_keys():
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, ssh_manager.generate_ssh_key_pair, f"key_{i}")
        for i in range(10)
    ]
    return await asyncio.gather(*tasks)

# Run async
keys = asyncio.run(generate_multiple_keys())
```

---

### 4. Password Hashing

```python
# ✓ Efficient: Use appropriate work factors
pwd_manager = PasswordManager(hash_method=PasswordHashMethod.BCRYPT)
# bcrypt automatically uses 12 rounds (good balance)

# ✗ Inefficient: Don't hash passwords multiple times
hashed = pwd_manager.hash_password(password)
# Don't do: hashed2 = pwd_manager.hash_password(hashed)
```

---

## Security Recommendations

### 1. Master Key Management

```python
# ✓ Best: Store master key in environment variable or secrets manager
import os
master_key = os.getenv("SECURITY_MASTER_KEY")
security = EnterpriseSecurityManager(master_key=master_key)

# ✗ Bad: Hardcode master key
security = EnterpriseSecurityManager(master_key="hardcoded-key-123")
```

---

### 2. SSH Key Passphrases

```python
# ✓ Best: Always use passphrases for SSH keys
private, public = ssh_manager.generate_ssh_key_pair(
    key_name="deploy_key",
    passphrase="strong-passphrase"
)

# ✗ Risky: No passphrase (only for automation contexts)
private, public = ssh_manager.generate_ssh_key_pair(
    key_name="deploy_key"
)
```

---

### 3. Secret Expiration

```python
# ✓ Best: Set expiration for temporary secrets
secret_id = secret_manager.encrypt_secret(
    "temp-token-abc123",
    "temp_access_token",
    expires_in_days=7
)

# ✓ Best: No expiration for permanent secrets
secret_id = secret_manager.encrypt_secret(
    "database-master-password",
    "db_master_password",
    expires_in_days=None
)
```

---

### 4. Audit Log Review

```python
# ✓ Best: Regularly review security events
audit_log = security.access_control.get_audit_log()

# Check for suspicious activity
failed_attempts = [
    entry for entry in audit_log
    if entry['result'] == 'denied'
]

if len(failed_attempts) > 10:
    print("⚠ High number of failed access attempts!")
    
# Monitor specific users
user_activity = [
    entry for entry in audit_log
    if entry['user'] == 'admin'
]
```

---

### 5. Key Rotation Schedule

```python
from datetime import datetime, timedelta

# ✓ Best: Implement key rotation schedule
def rotate_old_keys():
    keys = ssh_manager.list_ssh_keys()
    
    for key in keys:
        created_at = datetime.fromisoformat(key['created_at'])
        age_days = (datetime.now() - created_at).days
        
        if age_days > 90:  # Rotate keys older than 90 days
            print(f"Rotating key: {key['name']} (age: {age_days} days)")
            ssh_manager.rotate_ssh_key(key['name'], backup=True)

# Run monthly
rotate_old_keys()
```

---

## Integration Examples

### Flask/FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, Depends, Header
from enterprise_security import EnterpriseSecurityManager

app = FastAPI()
security = EnterpriseSecurityManager()

# Dependency for API key validation
async def validate_api_key(x_api_key: str = Header(...)):
    is_valid, error = security.api_keys.validate_api_key(
        x_api_key,
        required_permission="read"
    )
    if not is_valid:
        raise HTTPException(status_code=401, detail=error)
    return x_api_key

# Protected endpoint
@app.get("/api/data")
async def get_data(api_key: str = Depends(validate_api_key)):
    return {"data": "sensitive information"}

# Token-based authentication
@app.post("/api/login")
async def login(username: str, password: str):
    # Verify password (simplified)
    user_hash = get_user_hash_from_db(username)
    
    if security.passwords.verify_password(password, user_hash):
        # Generate JWT token
        token = security.tokens.generate_token(
            username,
            claims={"role": "user"},
            expires_in_minutes=60
        )
        return {"token": token}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/protected")
async def protected_route(authorization: str = Header(...)):
    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")
    
    is_valid, payload, error = security.tokens.verify_token(token)
    if not is_valid:
        raise HTTPException(status_code=401, detail=error)
    
    return {"message": f"Hello {payload['user_id']}"}
```

---

### Django Integration

```python
# settings.py
from enterprise_security import EnterpriseSecurityManager

SECURITY_MANAGER = EnterpriseSecurityManager(
    storage_base_dir="/var/django/secure"
)

# middleware.py
from django.http import JsonResponse

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.security = settings.SECURITY_MANAGER
    
    def __call__(self, request):
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            is_valid, error = self.security.api_keys.validate_api_key(api_key)
            if not is_valid:
                return JsonResponse({'error': error}, status=401)
        
        response = self.get_response(request)
        return response

# views.py
from django.contrib.auth.hashers import BasePasswordHasher
from django.conf import settings

class EnterprisePasswordHasher(BasePasswordHasher):
    """Custom password hasher using EnterpriseSecurityManager"""
    algorithm = "enterprise_bcrypt"
    
    def encode(self, password, salt):
        security = settings.SECURITY_MANAGER
        return security.passwords.hash_password(password)
    
    def verify(self, password, encoded):
        security = settings.SECURITY_MANAGER
        return security.passwords.verify_password(password, encoded)
```

---

### Database Integration

```python
import sqlite3
from enterprise_security import EnterpriseSecurityManager

class SecureDatabase:
    def __init__(self, db_path: str):
        self.security = EnterpriseSecurityManager()
        self.db_path = db_path
        self.conn = None
    
    def connect(self, password: str):
        """Connect to encrypted database"""
        # Decrypt database password
        db_secret_id = self.get_db_secret_id()
        db_password = self.security.secrets.decrypt_secret(db_secret_id)
        
        if db_password != password:
            raise ValueError("Invalid database password")
        
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def store_user_password(self, username: str, password: str):
        """Store user password securely"""
        hashed = self.security.passwords.hash_password(password)
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed)
        )
        self.conn.commit()
        
        # Add to password history
        self.security.passwords.add_to_password_history(username, hashed)
    
    def verify_user_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False
        
        return self.security.passwords.verify_password(password, result[0])
```

---

## Migration Guide

### From Basic Storage to Enterprise Security

```python
# Old approach
import json
import hashlib

# Storing passwords (insecure)
password_hash = hashlib.sha256(password.encode()).hexdigest()
with open('passwords.json', 'w') as f:
    json.dump({'user': password_hash}, f)

# Storing secrets (insecure)
with open('secrets.txt', 'w') as f:
    f.write(database_password)

# New approach with Enterprise Security
from enterprise_security import EnterpriseSecurityManager

security = EnterpriseSecurityManager()

# Store passwords securely
password_hash = security.passwords.hash_password(password)
# Store password_hash in database

# Store secrets encrypted
secret_id = security.secrets.encrypt_secret(
    database_password,
    "db_password",
    tags={"service": "postgres"}
)
# Store secret_id in config
```

---

### Migrating Existing Keys

```python
# Migrate plain SSH keys to managed keys
import os
from pathlib import Path

def migrate_ssh_keys():
    old_keys_dir = Path.home() / ".ssh"
    security = EnterpriseSecurityManager()
    
    for key_file in old_keys_dir.glob("id_*"):
        if key_file.suffix == ".pub":
            continue
        
        print(f"Migrating key: {key_file.name}")
        
        # Read old key
        key_content = key_file.read_text()
        
        # Validate
        if security.ssh_keys.validate_ssh_key(key_content):
            # Create managed key
            temp_path = security.ssh_keys.create_temp_key_file(key_content)
            
            # Copy to managed storage
            new_name = f"migrated_{key_file.name}"
            # ... copy logic ...
            
            print(f"✓ Migrated to: {new_name}")
        else:
            print(f"✗ Invalid key: {key_file.name}")

migrate_ssh_keys()
```

---

## API Quick Reference

### Common Operations Cheat Sheet

```python
from enterprise_security import EnterpriseSecurityManager, KeyType

security = EnterpriseSecurityManager()

# SSH Keys
private, public = security.ssh_keys.generate_ssh_key_pair(KeyType.ED25519, "my_key")
keys = security.ssh_keys.list_ssh_keys()
security.ssh_keys.rotate_ssh_key("my_key", backup=True)
security.ssh_keys.delete_ssh_key("old_key")

# Secrets
secret_id = security.secrets.encrypt_secret("value", "name", expires_in_days=90)
value = security.secrets.decrypt_secret(secret_id)
security.secrets.rotate_secret(secret_id, "new_value")
secrets = security.secrets.list_secrets(tag_filter={"env": "prod"})

# Passwords
password = security.passwords.generate_password(length=16)
hashed = security.passwords.hash_password(password)
is_valid = security.passwords.verify_password(password, hashed)
strength = security.passwords.check_password_strength(password)

# API Keys
api_key = security.api_keys.generate_api_key("service", ["read", "write"])
is_valid, error = security.api_keys.validate_api_key(api_key.key, "write")
security.api_keys.revoke_api_key(api_key.key)

# Certificates
cert, key = security.certificates.generate_self_signed_cert("example.com")
info = security.certificates.check_certificate_expiration(cert)
is_valid, msg = security.certificates.validate_certificate(cert)

# JWT Tokens
token = security.tokens.generate_token("user123", expires_in_minutes=60)
is_valid, payload, error = security.tokens.verify_token(token)
new_token = security.tokens.refresh_token(token)

# 2FA
totp = security.two_factor.generate_totp_secret("user123")
security.two_factor.generate_qr_code(totp['provisioning_uri'], "qr.png")
is_valid = security.two_factor.verify_totp_code(totp['secret'], "123456")
codes = security.two_factor.generate_backup_codes("user123")

# RBAC
security.access_control.define_role("admin", ["*"])
security.access_control.assign_role("user123", "admin")
can_access = security.access_control.check_permission("user123", "write")
perms = security.access_control.get_user_permissions("user123")

# Status & Audit
status = security.get_security_status()
security.export_audit_logs("audit.json")
```

---

## Support and Contributing

### Getting Help

- **Documentation**: This document
- **Issues**: Report bugs and request features
- **Examples**: See `examples/` directory in repository

### Reporting Security Issues

**DO NOT** report security vulnerabilities in public issues.

Email security issues to: security@company.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

---

## Changelog

### Version 2.0.0 (2024-01-08)
- Initial release with 60+ security features
- SSH key management (15 features)
- Secret encryption (10 features)
- Password management (10 features)
- API key management (5 features)
- Certificate management (5 features)
- JWT token management (5 features)
- Two-factor authentication (5 features)
- RBAC access control (5 features)

---

## License

Enterprise License - All Rights Reserved

Copyright © 2024 Enterprise Security Team

---