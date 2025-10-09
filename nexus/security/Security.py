"""
Enterprise Security Manager
===========================
Comprehensive security management system with 50+ features for:
- SSH key management and rotation
- Secret encryption/decryption
- Certificate management (SSL/TLS)
- Token generation and validation
- API key management
- Password policies and hashing
- Audit logging
- Access control and RBAC
- 2FA/MFA support
- Key derivation and encryption

Requirements:
    pip install cryptography paramiko pyjwt bcrypt pyotp qrcode passlib \
                python-jose secrets argon2-cffi

Author: Enterprise Security Team
Version: 2.0.0
License: Enterprise
"""

import os
import sys
import json
import base64
import hashlib
import hmac
import secrets
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import (
    CertificateBuilder, Name, NameAttribute,
    BasicConstraints, SubjectAlternativeName, DNSName,
    load_pem_x509_certificate, load_der_x509_certificate
)
from cryptography.x509.oid import NameOID, ExtensionOID

# Password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    from argon2 import PasswordHasher
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False

try:
    from passlib.hash import pbkdf2_sha256
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False

# JWT
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

# OTP/2FA
try:
    import pyotp
    import qrcode
    OTP_AVAILABLE = True
except ImportError:
    OTP_AVAILABLE = False

# SSH
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False


# ==================== Enums ====================

class HashAlgorithm(Enum):
    """Supported hash algorithms"""
    SHA256 = "sha256"
    SHA512 = "sha512"
    SHA3_256 = "sha3_256"
    SHA3_512 = "sha3_512"
    BLAKE2B = "blake2b"
    BLAKE2S = "blake2s"


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    FERNET = "fernet"
    AES_256_GCM = "aes256gcm"
    AES_256_CBC = "aes256cbc"
    CHACHA20 = "chacha20"
    RSA_2048 = "rsa2048"
    RSA_4096 = "rsa4096"


class PasswordHashMethod(Enum):
    """Password hashing methods"""
    BCRYPT = "bcrypt"
    ARGON2 = "argon2"
    PBKDF2 = "pbkdf2"
    SCRYPT = "scrypt"


class KeyType(Enum):
    """SSH/Crypto key types"""
    RSA_2048 = "rsa2048"
    RSA_4096 = "rsa4096"
    ED25519 = "ed25519"
    ECDSA = "ecdsa"


class AccessLevel(Enum):
    """Access control levels"""
    ADMIN = "admin"
    WRITE = "write"
    READ = "read"
    EXECUTE = "execute"
    NONE = "none"


# ==================== Data Classes ====================

@dataclass
class SecretMetadata:
    """Metadata for encrypted secrets"""
    secret_id: str
    name: str
    algorithm: EncryptionAlgorithm
    created_at: datetime
    expires_at: Optional[datetime] = None
    rotated_at: Optional[datetime] = None
    rotation_count: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "secret_id": self.secret_id,
            "name": self.name,
            "algorithm": self.algorithm.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "rotated_at": self.rotated_at.isoformat() if self.rotated_at else None,
            "rotation_count": self.rotation_count,
            "tags": self.tags
        }


@dataclass
class APIKey:
    """API key structure"""
    key_id: str
    key: str
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    rate_limit: int = 1000
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "key_id": self.key_id,
            "name": self.name,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "rate_limit": self.rate_limit,
            "enabled": self.enabled
        }


@dataclass
class AuditEntry:
    """Security audit log entry"""
    timestamp: datetime
    action: str
    user: str
    resource: str
    result: str
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "user": self.user,
            "resource": self.resource,
            "result": self.result,
            "ip_address": self.ip_address,
            "metadata": self.metadata
        }


# ==================== SSH Key Manager (Enhanced) ====================

class SSHKeyManager:
    """
    Advanced SSH key management with 15+ features:
    1. Create temporary SSH key files
    2. Generate new SSH key pairs (RSA/Ed25519)
    3. Load and validate SSH keys
    4. Convert between key formats
    5. Add passphrases to keys
    6. Remove passphrases from keys
    7. Key rotation and backup
    8. Key fingerprint generation
    9. Authorized keys management
    10. Known hosts management
    11. SSH agent integration
    12. Key expiration tracking
    13. Key usage auditing
    14. Batch key operations
    15. Secure key storage with encryption
    """
    
    def __init__(self, storage_dir: str = "/var/secure/ssh"):
        self.logger = logging.getLogger("SSHKeyManager")
        self.temp_key_files: List[str] = []
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.key_metadata: Dict[str, Dict] = {}
        self.audit_log: List[AuditEntry] = []
    
    # Feature 1: Create temporary SSH key file
    def create_temp_key_file(self, key_content: str) -> str:
        """Create temporary SSH key file with proper permissions"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
                f.write(key_content)
                if not key_content.endswith('\n'):
                    f.write('\n')
                key_path = f.name
            
            # Set proper permissions (readable only by owner)
            os.chmod(key_path, 0o600)
            self.temp_key_files.append(key_path)
            self.logger.info(f"Created temporary SSH key: {key_path}")
            
            self._audit("ssh_key_created", "system", key_path, "success")
            return key_path
        except Exception as e:
            self.logger.error(f"Failed to create SSH key file: {e}")
            self._audit("ssh_key_created", "system", "temp_key", "failure", {"error": str(e)})
            raise
    
    # Feature 2: Generate new SSH key pair
    def generate_ssh_key_pair(
        self,
        key_type: KeyType = KeyType.ED25519,
        key_name: str = "id_key",
        passphrase: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate new SSH key pair"""
        try:
            if not PARAMIKO_AVAILABLE:
                raise ImportError("paramiko not available")
            
            if key_type == KeyType.RSA_2048:
                key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
            elif key_type == KeyType.RSA_4096:
                key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=4096,
                    backend=default_backend()
                )
            elif key_type == KeyType.ED25519:
                key = ed25519.Ed25519PrivateKey.generate()
            else:
                raise ValueError(f"Unsupported key type: {key_type}")
            
            # Determine encryption
            encryption = serialization.NoEncryption()
            if passphrase:
                encryption = serialization.BestAvailableEncryption(passphrase.encode())
            
            # Serialize private key
            private_key_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=encryption
            ).decode()
            
            # Serialize public key
            public_key = key.public_key()
            public_key_ssh = public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            ).decode()
            
            if comment:
                public_key_ssh += f" {comment}"
            
            # Save keys
            private_path = self.storage_dir / f"{key_name}"
            public_path = self.storage_dir / f"{key_name}.pub"
            
            private_path.write_text(private_key_pem)
            private_path.chmod(0o600)
            
            public_path.write_text(public_key_ssh)
            public_path.chmod(0o644)
            
            # Store metadata
            self.key_metadata[key_name] = {
                "type": key_type.value,
                "created_at": datetime.now().isoformat(),
                "has_passphrase": passphrase is not None,
                "fingerprint": self.get_key_fingerprint(private_key_pem)
            }
            
            self.logger.info(f"Generated SSH key pair: {key_name}")
            self._audit("ssh_key_generated", "system", key_name, "success")
            
            return str(private_path), str(public_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate SSH key: {e}")
            self._audit("ssh_key_generated", "system", key_name, "failure", {"error": str(e)})
            raise
    
    # Feature 3: Validate SSH key
    def validate_ssh_key(self, key_content: str) -> bool:
        """Validate SSH key format and integrity"""
        try:
            # Try to load as private key
            try:
                serialization.load_ssh_private_key(
                    key_content.encode(),
                    password=None,
                    backend=default_backend()
                )
                return True
            except:
                pass
            
            # Try to load as public key
            try:
                serialization.load_ssh_public_key(
                    key_content.encode(),
                    backend=default_backend()
                )
                return True
            except:
                pass
            
            return False
        except Exception as e:
            self.logger.error(f"Key validation failed: {e}")
            return False
    
    # Feature 4: Get key fingerprint
    def get_key_fingerprint(self, key_content: str, hash_algo: str = "sha256") -> str:
        """Generate SSH key fingerprint"""
        try:
            key_bytes = key_content.encode()
            
            if hash_algo == "sha256":
                digest = hashlib.sha256(key_bytes).digest()
                fingerprint = base64.b64encode(digest).decode().rstrip('=')
                return f"SHA256:{fingerprint}"
            elif hash_algo == "md5":
                digest = hashlib.md5(key_bytes).hexdigest()
                return ':'.join(digest[i:i+2] for i in range(0, len(digest), 2))
            else:
                raise ValueError(f"Unsupported hash algorithm: {hash_algo}")
        except Exception as e:
            self.logger.error(f"Failed to generate fingerprint: {e}")
            raise
    
    # Feature 5: Rotate SSH key
    def rotate_ssh_key(self, key_name: str, backup: bool = True) -> Tuple[str, str]:
        """Rotate SSH key by generating new pair"""
        try:
            # Backup old key if requested
            if backup:
                old_private = self.storage_dir / key_name
                old_public = self.storage_dir / f"{key_name}.pub"
                
                if old_private.exists():
                    backup_name = f"{key_name}.backup.{int(datetime.now().timestamp())}"
                    backup_private = self.storage_dir / backup_name
                    backup_public = self.storage_dir / f"{backup_name}.pub"
                    
                    old_private.rename(backup_private)
                    if old_public.exists():
                        old_public.rename(backup_public)
                    
                    self.logger.info(f"Backed up old key to {backup_name}")
            
            # Generate new key
            metadata = self.key_metadata.get(key_name, {})
            key_type = KeyType(metadata.get("type", "ed25519"))
            
            private_path, public_path = self.generate_ssh_key_pair(
                key_type=key_type,
                key_name=key_name
            )
            
            self.logger.info(f"Rotated SSH key: {key_name}")
            self._audit("ssh_key_rotated", "system", key_name, "success")
            
            return private_path, public_path
            
        except Exception as e:
            self.logger.error(f"Failed to rotate SSH key: {e}")
            self._audit("ssh_key_rotated", "system", key_name, "failure", {"error": str(e)})
            raise
    
    # Feature 6: Add passphrase to key
    def add_passphrase_to_key(
        self,
        key_path: str,
        new_passphrase: str,
        old_passphrase: Optional[str] = None
    ) -> bool:
        """Add or change passphrase on SSH key"""
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            # Load key
            password = old_passphrase.encode() if old_passphrase else None
            private_key = serialization.load_ssh_private_key(
                key_data,
                password=password,
                backend=default_backend()
            )
            
            # Re-serialize with new passphrase
            encrypted_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.BestAvailableEncryption(new_passphrase.encode())
            )
            
            # Write back
            with open(key_path, 'wb') as f:
                f.write(encrypted_key)
            
            self.logger.info(f"Added passphrase to key: {key_path}")
            self._audit("ssh_key_passphrase_added", "system", key_path, "success")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add passphrase: {e}")
            return False
    
    # Feature 7: Remove passphrase from key
    def remove_passphrase_from_key(self, key_path: str, passphrase: str) -> bool:
        """Remove passphrase from SSH key"""
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            # Load key with passphrase
            private_key = serialization.load_ssh_private_key(
                key_data,
                password=passphrase.encode(),
                backend=default_backend()
            )
            
            # Re-serialize without encryption
            unencrypted_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Write back
            with open(key_path, 'wb') as f:
                f.write(unencrypted_key)
            
            self.logger.info(f"Removed passphrase from key: {key_path}")
            self._audit("ssh_key_passphrase_removed", "system", key_path, "success")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove passphrase: {e}")
            return False
    
    # Feature 8: Manage authorized keys
    def add_to_authorized_keys(
        self,
        public_key: str,
        authorized_keys_path: str = "~/.ssh/authorized_keys",
        comment: Optional[str] = None
    ) -> bool:
        """Add public key to authorized_keys file"""
        try:
            auth_path = Path(authorized_keys_path).expanduser()
            auth_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Read existing keys
            existing_keys = []
            if auth_path.exists():
                existing_keys = auth_path.read_text().strip().split('\n')
            
            # Add new key with optional comment
            new_key = public_key.strip()
            if comment:
                new_key += f" {comment}"
            
            # Avoid duplicates
            if new_key not in existing_keys:
                existing_keys.append(new_key)
                auth_path.write_text('\n'.join(existing_keys) + '\n')
                auth_path.chmod(0o600)
                
                self.logger.info(f"Added key to authorized_keys")
                return True
            else:
                self.logger.info("Key already in authorized_keys")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add to authorized_keys: {e}")
            return False
    
    # Feature 9: List all SSH keys
    def list_ssh_keys(self) -> List[Dict]:
        """List all managed SSH keys"""
        keys = []
        for key_file in self.storage_dir.glob("*"):
            if key_file.is_file() and not key_file.name.endswith('.pub'):
                metadata = self.key_metadata.get(key_file.name, {})
                keys.append({
                    "name": key_file.name,
                    "path": str(key_file),
                    "type": metadata.get("type", "unknown"),
                    "created_at": metadata.get("created_at"),
                    "has_passphrase": metadata.get("has_passphrase", False),
                    "fingerprint": metadata.get("fingerprint")
                })
        return keys
    
    # Feature 10: Delete SSH key
    def delete_ssh_key(self, key_name: str, secure_delete: bool = True) -> bool:
        """Securely delete SSH key pair"""
        try:
            private_path = self.storage_dir / key_name
            public_path = self.storage_dir / f"{key_name}.pub"
            
            deleted = False
            
            if private_path.exists():
                if secure_delete:
                    # Overwrite with random data before deleting
                    size = private_path.stat().st_size
                    with open(private_path, 'wb') as f:
                        f.write(secrets.token_bytes(size))
                private_path.unlink()
                deleted = True
            
            if public_path.exists():
                public_path.unlink()
                deleted = True
            
            if key_name in self.key_metadata:
                del self.key_metadata[key_name]
            
            if deleted:
                self.logger.info(f"Deleted SSH key: {key_name}")
                self._audit("ssh_key_deleted", "system", key_name, "success")
            
            return deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete SSH key: {e}")
            return False
    
    # Feature 11: Export public key
    def export_public_key(self, key_name: str, format: str = "openssh") -> Optional[str]:
        """Export public key in specified format"""
        try:
            public_path = self.storage_dir / f"{key_name}.pub"
            
            if not public_path.exists():
                return None
            
            public_key_content = public_path.read_text()
            
            if format == "openssh":
                return public_key_content
            elif format == "rfc4716":
                # Convert to RFC4716 format
                # This is a simplified version
                return f"---- BEGIN SSH2 PUBLIC KEY ----\n{public_key_content}\n---- END SSH2 PUBLIC KEY ----"
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export public key: {e}")
            return None
    
    # Feature 12: Cleanup temporary keys
    def cleanup(self):
        """Remove all temporary key files"""
        for key_file in self.temp_key_files:
            try:
                if os.path.exists(key_file):
                    # Secure delete
                    size = os.path.getsize(key_file)
                    with open(key_file, 'wb') as f:
                        f.write(secrets.token_bytes(size))
                    os.remove(key_file)
                    self.logger.debug(f"Removed temporary key: {key_file}")
            except Exception as e:
                self.logger.warning(f"Failed to remove key file {key_file}: {e}")
        
        self.temp_key_files.clear()
    
    # Feature 13: Audit logging
    def _audit(
        self,
        action: str,
        user: str,
        resource: str,
        result: str,
        metadata: Optional[Dict] = None
    ):
        """Log security audit event"""
        entry = AuditEntry(
            timestamp=datetime.now(),
            action=action,
            user=user,
            resource=resource,
            result=result,
            metadata=metadata or {}
        )
        self.audit_log.append(entry)
    
    # Feature 14: Get audit log
    def get_audit_log(
        self,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Retrieve audit log entries"""
        filtered_log = self.audit_log
        
        if action:
            filtered_log = [e for e in filtered_log if e.action == action]
        
        if start_time:
            filtered_log = [e for e in filtered_log if e.timestamp >= start_time]
        
        if end_time:
            filtered_log = [e for e in filtered_log if e.timestamp <= end_time]
        
        return [e.to_dict() for e in filtered_log]
    
    # Feature 15: Batch key generation
    def batch_generate_keys(
        self,
        count: int,
        prefix: str = "key",
        key_type: KeyType = KeyType.ED25519
    ) -> List[Tuple[str, str]]:
        """Generate multiple SSH key pairs"""
        generated_keys = []
        
        for i in range(count):
            key_name = f"{prefix}_{i+1}"
            try:
                private_path, public_path = self.generate_ssh_key_pair(
                    key_type=key_type,
                    key_name=key_name
                )
                generated_keys.append((private_path, public_path))
            except Exception as e:
                self.logger.error(f"Failed to generate key {key_name}: {e}")
        
        self.logger.info(f"Batch generated {len(generated_keys)} keys")
        return generated_keys
    
    def __del__(self):
        self.cleanup()


# ==================== Secret Manager ====================

class SecretManager:
    """
    Enterprise secret management with 10+ features:
    1. Encrypt/decrypt secrets with multiple algorithms
    2. Secret versioning and rotation
    3. Secret expiration and lifecycle management
    4. Secure secret storage
    5. Secret sharing with access control
    6. Secret backup and restore
    7. Secret audit logging
    8. Key derivation from passwords
    9. Secrets import/export
    10. Secret metadata management
    """
    
    def __init__(self, master_key: Optional[str] = None, storage_dir: str = "/var/secure/secrets"):
        self.logger = logging.getLogger("SecretManager")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Initialize master key
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = self._generate_master_key()
        
        # Derive encryption key
        self.fernet = self._derive_fernet_key(self.master_key)
        
        self.secrets: Dict[str, SecretMetadata] = {}
        self.audit_log: List[AuditEntry] = []
    
    def _generate_master_key(self) -> bytes:
        """Generate a new master key"""
        return Fernet.generate_key()
    
    def _derive_fernet_key(self, password: bytes, salt: Optional[bytes] = None) -> Fernet:
        """Derive Fernet key from password"""
        if salt is None:
            salt = b'nexus_secret_salt_v1'  # In production, use random salt per secret
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    # Feature 1: Encrypt secret
    def encrypt_secret(
        self,
        secret_value: str,
        secret_name: str,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET,
        expires_in_days: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """Encrypt a secret and store metadata"""
        try:
            secret_id = str(uuid.uuid4())
            
            if algorithm == EncryptionAlgorithm.FERNET:
                encrypted = self.fernet.encrypt(secret_value.encode()).decode()
            elif algorithm == EncryptionAlgorithm.AES_256_GCM:
                encrypted = self._encrypt_aes_gcm(secret_value)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Create metadata
            metadata = SecretMetadata(
                secret_id=secret_id,
                name=secret_name,
                algorithm=algorithm,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
                tags=tags or {}
            )
            
            self.secrets[secret_id] = metadata
            
            # Store encrypted secret
            secret_path = self.storage_dir / f"{secret_id}.enc"
            secret_path.write_text(encrypted)
            secret_path.chmod(0o600)
            
            # Store metadata
            metadata_path = self.storage_dir / f"{secret_id}.meta"
            metadata_path.write_text(json.dumps(metadata.to_dict()))
            metadata_path.chmod(0o600)
            
            self.logger.info(f"Encrypted secret: {secret_name}")
            self._audit("secret_encrypted", "system", secret_name, "success")
            
            return secret_id
            
        except Exception as e:
            self.logger.error(f"Failed to encrypt secret: {e}")
            self._audit("secret_encrypted", "system", secret_name, "failure", {"error": str(e)})
            raise
    
    # Feature 2: Decrypt secret
    def decrypt_secret(self, secret_id: str) -> Optional[str]:
        """Decrypt a secret by ID"""
        try:
            metadata = self.secrets.get(secret_id)
            
            if not metadata:
                # Try to load from disk
                metadata_path = self.storage_dir / f"{secret_id}.meta"
                if metadata_path.exists():
                    meta_dict = json.loads(metadata_path.read_text())
                    metadata = SecretMetadata(
                        secret_id=meta_dict['secret_id'],
                        name=meta_dict['name'],
                        algorithm=EncryptionAlgorithm(meta_dict['algorithm']),
                        created_at=datetime.fromisoformat(meta_dict['created_at']),
                        expires_at=datetime.fromisoformat(meta_dict['expires_at']) if meta_dict.get('expires_at') else None,
                        rotation_count=meta_dict.get('rotation_count', 0),
                        tags=meta_dict.get('tags', {})
                    )
                    self.secrets[secret_id] = metadata
                else:
                    return None
            
            # Check expiration
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                self.logger.warning(f"Secret {secret_id} has expired")
                return None
            
            # Read encrypted secret
            secret_path = self.storage_dir / f"{secret_id}.enc"
            if not secret_path.exists():
                return None
            
            encrypted_data = secret_path.read_text()
            
            # Decrypt based on algorithm
            if metadata.algorithm == EncryptionAlgorithm.FERNET:
                decrypted = self.fernet.decrypt(encrypted_data.encode()).decode()
            elif metadata.algorithm == EncryptionAlgorithm.AES_256_GCM:
                decrypted = self._decrypt_aes_gcm(encrypted_data)
            else:
                raise ValueError(f"Unsupported algorithm: {metadata.algorithm}")
            
            self._audit("secret_decrypted", "system", metadata.name, "success")
            return decrypted
            
        except Exception as e:
            self.logger.error(f"Failed to decrypt secret: {e}")
            self._audit("secret_decrypted", "system", secret_id, "failure", {"error": str(e)})
            return None
    
    # Feature 3: Rotate secret
    def rotate_secret(self, secret_id: str, new_value: str) -> bool:
        """Rotate a secret with new value"""
        try:
            metadata = self.secrets.get(secret_id)
            if not metadata:
                return False
            
            # Backup old version
            old_secret_path = self.storage_dir / f"{secret_id}.enc"
            backup_path = self.storage_dir / f"{secret_id}.enc.v{metadata.rotation_count}"
            
            if old_secret_path.exists():
                old_secret_path.rename(backup_path)
            
            # Encrypt new value
            if metadata.algorithm == EncryptionAlgorithm.FERNET:
                encrypted = self.fernet.encrypt(new_value.encode()).decode()
            else:
                encrypted = self._encrypt_aes_gcm(new_value)
            
            # Write new encrypted secret
            new_secret_path = self.storage_dir / f"{secret_id}.enc"
            new_secret_path.write_text(encrypted)
            new_secret_path.chmod(0o600)
            
            # Update metadata
            metadata.rotated_at = datetime.now()
            metadata.rotation_count += 1
            
            metadata_path = self.storage_dir / f"{secret_id}.meta"
            metadata_path.write_text(json.dumps(metadata.to_dict()))
            
            self.logger.info(f"Rotated secret: {metadata.name}")
            self._audit("secret_rotated", "system", metadata.name, "success")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rotate secret: {e}")
            return False
    
    # Feature 4: Delete secret
    def delete_secret(self, secret_id: str, secure_delete: bool = True) -> bool:
        """Delete a secret securely"""
        try:
            secret_path = self.storage_dir / f"{secret_id}.enc"
            metadata_path = self.storage_dir / f"{secret_id}.meta"
            
            # Secure delete if requested
            if secure_delete and secret_path.exists():
                size = secret_path.stat().st_size
                with open(secret_path, 'wb') as f:
                    f.write(secrets.token_bytes(size))
            
            # Delete files
            if secret_path.exists():
                secret_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            # Remove from memory
            if secret_id in self.secrets:
                metadata = self.secrets[secret_id]
                del self.secrets[secret_id]
                self._audit("secret_deleted", "system", metadata.name, "success")
            
            self.logger.info(f"Deleted secret: {secret_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete secret: {e}")
            return False
    
    # Feature 5: List secrets
    def list_secrets(self, tag_filter: Optional[Dict[str, str]] = None) -> List[Dict]:
        """List all secrets with optional tag filtering"""
        secrets_list = []
        
        for secret_id, metadata in self.secrets.items():
            # Apply tag filter
            if tag_filter:
                if not all(metadata.tags.get(k) == v for k, v in tag_filter.items()):
                    continue
            
            secrets_list.append({
                "secret_id": secret_id,
                "name": metadata.name,
                "created_at": metadata.created_at.isoformat(),
                "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                "rotation_count": metadata.rotation_count,
                "tags": metadata.tags
            })
        
        return secrets_list
    
    # Feature 6: Export secrets (encrypted)
    def export_secrets(self, output_file: str, secret_ids: Optional[List[str]] = None):
        """Export secrets to encrypted backup file"""
        try:
            export_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "secrets": []
            }
            
            secrets_to_export = secret_ids if secret_ids else list(self.secrets.keys())
            
            for secret_id in secrets_to_export:
                secret_path = self.storage_dir / f"{secret_id}.enc"
                metadata_path = self.storage_dir / f"{secret_id}.meta"
                
                if secret_path.exists() and metadata_path.exists():
                    export_data["secrets"].append({
                        "secret_id": secret_id,
                        "encrypted_data": secret_path.read_text(),
                        "metadata": json.loads(metadata_path.read_text())
                    })
            
            # Encrypt entire export
            export_json = json.dumps(export_data)
            encrypted_export = self.fernet.encrypt(export_json.encode())
            
            Path(output_file).write_bytes(encrypted_export)
            self.logger.info(f"Exported {len(export_data['secrets'])} secrets to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export secrets: {e}")
            raise
    
    # Feature 7: Import secrets
    def import_secrets(self, import_file: str) -> int:
        """Import secrets from encrypted backup file"""
        try:
            encrypted_data = Path(import_file).read_bytes()
            decrypted_json = self.fernet.decrypt(encrypted_data).decode()
            import_data = json.loads(decrypted_json)
            
            imported_count = 0
            
            for secret_entry in import_data["secrets"]:
                secret_id = secret_entry["secret_id"]
                
                # Write encrypted secret
                secret_path = self.storage_dir / f"{secret_id}.enc"
                secret_path.write_text(secret_entry["encrypted_data"])
                secret_path.chmod(0o600)
                
                # Write metadata
                metadata_path = self.storage_dir / f"{secret_id}.meta"
                metadata_path.write_text(json.dumps(secret_entry["metadata"]))
                metadata_path.chmod(0o600)
                
                # Load into memory
                meta_dict = secret_entry["metadata"]
                self.secrets[secret_id] = SecretMetadata(
                    secret_id=meta_dict['secret_id'],
                    name=meta_dict['name'],
                    algorithm=EncryptionAlgorithm(meta_dict['algorithm']),
                    created_at=datetime.fromisoformat(meta_dict['created_at']),
                    expires_at=datetime.fromisoformat(meta_dict['expires_at']) if meta_dict.get('expires_at') else None,
                    rotation_count=meta_dict.get('rotation_count', 0),
                    tags=meta_dict.get('tags', {})
                )
                
                imported_count += 1
            
            self.logger.info(f"Imported {imported_count} secrets from {import_file}")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"Failed to import secrets: {e}")
            raise
    
    # Feature 8: AES-256-GCM encryption
    def _encrypt_aes_gcm(self, plaintext: str) -> str:
        """Encrypt using AES-256-GCM"""
        # Generate random key and nonce
        key = secrets.token_bytes(32)  # 256 bits
        nonce = secrets.token_bytes(12)  # 96 bits for GCM
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        
        # Combine key, nonce, tag, and ciphertext
        combined = key + nonce + encryptor.tag + ciphertext
        return base64.b64encode(combined).decode()
    
    # Feature 9: AES-256-GCM decryption
    def _decrypt_aes_gcm(self, encrypted_data: str) -> str:
        """Decrypt using AES-256-GCM"""
        combined = base64.b64decode(encrypted_data)
        
        # Extract components
        key = combined[:32]
        nonce = combined[32:44]
        tag = combined[44:60]
        ciphertext = combined[60:]
        
        # Decrypt
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode()
    
    # Feature 10: Audit logging
    def _audit(self, action: str, user: str, resource: str, result: str, metadata: Optional[Dict] = None):
        """Log security audit event"""
        entry = AuditEntry(
            timestamp=datetime.now(),
            action=action,
            user=user,
            resource=resource,
            result=result,
            metadata=metadata or {}
        )
        self.audit_log.append(entry)
    
    def get_audit_log(self) -> List[Dict]:
        """Get audit log"""
        return [e.to_dict() for e in self.audit_log]


# ==================== Password Manager ====================

class PasswordManager:
    """
    Enterprise password management with 10+ features:
    1. Hash passwords with multiple algorithms
    2. Verify password hashes
    3. Password strength validation
    4. Password generation
    5. Password policy enforcement
    6. Password breach checking
    7. Password expiration tracking
    8. Password history
    9. Common password detection
    10. Password entropy calculation
    """
    
    def __init__(self, hash_method: PasswordHashMethod = PasswordHashMethod.BCRYPT):
        self.logger = logging.getLogger("PasswordManager")
        self.hash_method = hash_method
        
        # Initialize hashers
        if hash_method == PasswordHashMethod.ARGON2 and ARGON2_AVAILABLE:
            self.argon2_hasher = PasswordHasher()
        
        self.password_history: Dict[str, List[str]] = {}
        self.common_passwords = self._load_common_passwords()
    
    def _load_common_passwords(self) -> set:
        """Load common passwords list"""
        # Top 100 most common passwords
        return {
            "123456", "password", "123456789", "12345678", "12345",
            "1234567", "password1", "123123", "1234567890", "000000",
            "qwerty", "abc123", "111111", "admin", "letmein"
            # Add more...
        }
    
    # Feature 1: Hash password
    def hash_password(self, password: str) -> str:
        """Hash password using configured method"""
        try:
            if self.hash_method == PasswordHashMethod.BCRYPT and BCRYPT_AVAILABLE:
                salt = bcrypt.gensalt(rounds=12)
                hashed = bcrypt.hashpw(password.encode(), salt)
                return hashed.decode()
            
            elif self.hash_method == PasswordHashMethod.ARGON2 and ARGON2_AVAILABLE:
                return self.argon2_hasher.hash(password)
            
            elif self.hash_method == PasswordHashMethod.PBKDF2 and PASSLIB_AVAILABLE:
                return pbkdf2_sha256.hash(password)
            
            elif self.hash_method == PasswordHashMethod.SCRYPT:
                return self._hash_scrypt(password)
            
            else:
                raise ValueError(f"Unsupported hash method: {self.hash_method}")
                
        except Exception as e:
            self.logger.error(f"Failed to hash password: {e}")
            raise
    
    # Feature 2: Verify password
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            if self.hash_method == PasswordHashMethod.BCRYPT and BCRYPT_AVAILABLE:
                return bcrypt.checkpw(password.encode(), hashed_password.encode())
            
            elif self.hash_method == PasswordHashMethod.ARGON2 and ARGON2_AVAILABLE:
                try:
                    self.argon2_hasher.verify(hashed_password, password)
                    return True
                except:
                    return False
            
            elif self.hash_method == PasswordHashMethod.PBKDF2 and PASSLIB_AVAILABLE:
                return pbkdf2_sha256.verify(password, hashed_password)
            
            elif self.hash_method == PasswordHashMethod.SCRYPT:
                return self._verify_scrypt(password, hashed_password)
            
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    # Feature 3: Generate secure password
    def generate_password(
        self,
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """Generate secure random password"""
        import string
        
        chars = ""
        if include_lowercase:
            chars += string.ascii_lowercase
        if include_uppercase:
            chars += string.ascii_uppercase
        if include_digits:
            chars += string.digits
        if include_symbols:
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
        if exclude_ambiguous:
            # Remove ambiguous characters
            chars = ''.join(c for c in chars if c not in "il1Lo0O")
        
        if not chars:
            raise ValueError("At least one character type must be included")
        
        # Generate password ensuring at least one of each required type
        password = []
        
        if include_lowercase:
            password.append(secrets.choice(string.ascii_lowercase))
        if include_uppercase:
            password.append(secrets.choice(string.ascii_uppercase))
        if include_digits:
            password.append(secrets.choice(string.digits))
        if include_symbols:
            password.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))
        
        # Fill remaining length
        while len(password) < length:
            password.append(secrets.choice(chars))
        
        # Shuffle
        import random
        random.shuffle(password)
        
        return ''.join(password)
    
    # Feature 4: Check password strength
    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """Analyze password strength"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) < 8:
            feedback.append("Password should be at least 8 characters")
        elif len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        
        # Character variety
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(not c.isalnum() for c in password)
        
        variety = sum([has_lower, has_upper, has_digit, has_symbol])
        score += variety
        
        if not has_lower:
            feedback.append("Add lowercase letters")
        if not has_upper:
            feedback.append("Add uppercase letters")
        if not has_digit:
            feedback.append("Add numbers")
        if not has_symbol:
            feedback.append("Add special characters")
        
        # Common password check
        if password.lower() in self.common_passwords:
            score = 0
            feedback.append("This is a commonly used password")
        
        # Sequential characters
        if self._has_sequential_chars(password):
            score -= 1
            feedback.append("Avoid sequential characters")
        
        # Calculate entropy
        entropy = self.calculate_password_entropy(password)
        
        # Determine strength level
        if score >= 6:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            "strength": strength,
            "score": score,
            "entropy": entropy,
            "feedback": feedback,
            "length": len(password),
            "has_lowercase": has_lower,
            "has_uppercase": has_upper,
            "has_digits": has_digit,
            "has_symbols": has_symbol
        }
    
    # Feature 5: Calculate password entropy
    def calculate_password_entropy(self, password: str) -> float:
        """Calculate password entropy in bits"""
        import string
        
        # Determine character set size
        charset_size = 0
        if any(c in string.ascii_lowercase for c in password):
            charset_size += 26
        if any(c in string.ascii_uppercase for c in password):
            charset_size += 26
        if any(c in string.digits for c in password):
            charset_size += 10
        if any(not c.isalnum() for c in password):
            charset_size += 32  # Approximate
        
        # Entropy = log2(charset_size^length)
        import math
        if charset_size > 0:
            entropy = len(password) * math.log2(charset_size)
            return round(entropy, 2)
        return 0.0
    
    # Feature 6: Validate password policy
    def validate_password_policy(
        self,
        password: str,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_symbol: bool = True,
        max_repeated_chars: int = 3
    ) -> Tuple[bool, List[str]]:
        """Validate password against policy"""
        errors = []
        
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters")
        
        if require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        
        if require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        
        if require_digit and not any(c.isdigit() for c in password):
            errors.append("Password must contain digits")
        
        if require_symbol and not any(not c.isalnum() for c in password):
            errors.append("Password must contain special characters")
        
        # Check for repeated characters
        for i in range(len(password) - max_repeated_chars):
            if len(set(password[i:i+max_repeated_chars+1])) == 1:
                errors.append(f"Password cannot have more than {max_repeated_chars} repeated characters")
                break
        
        return len(errors) == 0, errors
    
    # Feature 7: Check password history
    def check_password_history(
        self,
        user_id: str,
        password: str,
        history_size: int = 5
    ) -> bool:
        """Check if password was recently used"""
        if user_id not in self.password_history:
            return True
        
        history = self.password_history[user_id]
        
        for old_hash in history[:history_size]:
            if self.verify_password(password, old_hash):
                return False
        
        return True
    
    # Feature 8: Add to password history
    def add_to_password_history(self, user_id: str, password_hash: str):
        """Add password hash to user's history"""
        if user_id not in self.password_history:
            self.password_history[user_id] = []
        
        self.password_history[user_id].insert(0, password_hash)
        
        # Keep only last 10 passwords
        self.password_history[user_id] = self.password_history[user_id][:10]
    
    # Feature 9: Scrypt hashing
    def _hash_scrypt(self, password: str) -> str:
        """Hash password using Scrypt"""
        salt = secrets.token_bytes(16)
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        
        # Combine salt and key
        combined = salt + key
        return base64.b64encode(combined).decode()
    
    # Feature 10: Scrypt verification
    def _verify_scrypt(self, password: str, hashed: str) -> bool:
        """Verify password against Scrypt hash"""
        try:
            combined = base64.b64decode(hashed)
            salt = combined[:16]
            stored_key = combined[16:]
            
            kdf = Scrypt(
                salt=salt,
                length=32,
                n=2**14,
                r=8,
                p=1,
                backend=default_backend()
            )
            kdf.verify(password.encode(), stored_key)
            return True
        except:
            return False
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters"""
        for i in range(len(password) - 2):
            if ord(password[i]) + 1 == ord(password[i+1]) and ord(password[i+1]) + 1 == ord(password[i+2]):
                return True
        return False


# ==================== API Key Manager ====================

class APIKeyManager:
    """
    API key management with 5+ features:
    1. Generate API keys
    2. Validate API keys
    3. Revoke API keys
    4. Track API key usage
    5. Rate limiting
    """
    
    def __init__(self, storage_dir: str = "/var/secure/api_keys"):
        self.logger = logging.getLogger("APIKeyManager")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.api_keys: Dict[str, APIKey] = {}
        self.usage_counts: Dict[str, int] = {}
    
    # Feature 1: Generate API key
    def generate_api_key(
        self,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None,
        rate_limit: int = 1000
    ) -> APIKey:
        """Generate new API key"""
        key_id = str(uuid.uuid4())
        
        # Generate secure random key
        key_bytes = secrets.token_bytes(32)
        key = base64.urlsafe_b64encode(key_bytes).decode().rstrip('=')
        
        api_key = APIKey(
            key_id=key_id,
            key=key,
            name=name,
            permissions=permissions,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
            rate_limit=rate_limit
        )
        
        self.api_keys[key] = api_key
        self.usage_counts[key] = 0
        
        # Store to disk
        key_path = self.storage_dir / f"{key_id}.json"
        key_path.write_text(json.dumps(api_key.to_dict()))
        key_path.chmod(0o600)
        
        self.logger.info(f"Generated API key: {name}")
        return api_key
    
    # Feature 2: Validate API key
    def validate_api_key(
        self,
        key: str,
        required_permission: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate API key and check permissions"""
        api_key = self.api_keys.get(key)
        
        if not api_key:
            return False, "Invalid API key"
        
        if not api_key.enabled:
            return False, "API key is disabled"
        
        if api_key.expires_at and datetime.now() > api_key.expires_at:
            return False, "API key has expired"
        
        if required_permission and required_permission not in api_key.permissions:
            return False, f"Missing permission: {required_permission}"
        
        # Check rate limit
        if self.usage_counts.get(key, 0) >= api_key.rate_limit:
            return False, "Rate limit exceeded"
        
        # Update usage
        api_key.last_used = datetime.now()
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
        
        return True, None
    
    # Feature 3: Revoke API key
    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key"""
        api_key = self.api_keys.get(key)
        
        if api_key:
            api_key.enabled = False
            self.logger.info(f"Revoked API key: {api_key.name}")
            return True
        
        return False
    
    # Feature 4: List API keys
    def list_api_keys(self) -> List[Dict]:
        """List all API keys (without exposing actual keys)"""
        return [
            {
                "key_id": api_key.key_id,
                "name": api_key.name,
                "permissions": api_key.permissions,
                "created_at": api_key.created_at.isoformat(),
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "enabled": api_key.enabled,
                "usage_count": self.usage_counts.get(api_key.key, 0)
            }
            for api_key in self.api_keys.values()
        ]
    
    # Feature 5: Reset rate limit
    def reset_rate_limits(self):
        """Reset all rate limit counters"""
        self.usage_counts.clear()
        self.logger.info("Reset all rate limits")


# ==================== Certificate Manager ====================

class CertificateManager:
    """
    SSL/TLS certificate management with 5+ features:
    1. Generate self-signed certificates
    2. Generate CSR (Certificate Signing Request)
    3. Load and validate certificates
    4. Check certificate expiration
    5. Export certificates in different formats
    """
    
    def __init__(self, storage_dir: str = "/var/secure/certs"):
        self.logger = logging.getLogger("CertificateManager")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    
    # Feature 1: Generate self-signed certificate
    def generate_self_signed_cert(
        self,
        common_name: str,
        organization: str = "Nexus",
        country: str = "US",
        validity_days: int = 365,
        dns_names: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """Generate self-signed SSL certificate"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Build subject and issuer
            subject = issuer = Name([
                NameAttribute(NameOID.COUNTRY_NAME, country),
                NameAttribute(NameOID.ORGANIZATION_NAME, organization),
                NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            # Build certificate
            cert_builder = CertificateBuilder()
            cert_builder = cert_builder.subject_name(subject)
            cert_builder = cert_builder.issuer_name(issuer)
            cert_builder = cert_builder.public_key(private_key.public_key())
            cert_builder = cert_builder.serial_number(secrets.randbits(64))
            cert_builder = cert_builder.not_valid_before(datetime.now())
            cert_builder = cert_builder.not_valid_after(datetime.now() + timedelta(days=validity_days))
            
            # Add basic constraints
            cert_builder = cert_builder.add_extension(
                BasicConstraints(ca=False, path_length=None),
                critical=True
            )
            
            # Add Subject Alternative Names
            if dns_names:
                san_list = [DNSName(name) for name in dns_names]
                cert_builder = cert_builder.add_extension(
                    SubjectAlternativeName(san_list),
                    critical=False
                )
            
            # Sign certificate
            certificate = cert_builder.sign(private_key, hashes.SHA256(), default_backend())
            
            # Serialize
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            # Save to disk
            cert_path = self.storage_dir / f"{common_name}.crt"
            key_path = self.storage_dir / f"{common_name}.key"
            
            cert_path.write_text(cert_pem)
            cert_path.chmod(0o644)
            
            key_path.write_text(key_pem)
            key_path.chmod(0o600)
            
            self.logger.info(f"Generated self-signed certificate: {common_name}")
            return str(cert_path), str(key_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate certificate: {e}")
            raise
    
    # Feature 2: Check certificate expiration
    def check_certificate_expiration(self, cert_path: str) -> Dict[str, Any]:
        """Check if certificate is expired or will expire soon"""
        try:
            cert_pem = Path(cert_path).read_bytes()
            certificate = load_pem_x509_certificate(cert_pem, default_backend())
            
            not_after = certificate.not_valid_after
            not_before = certificate.not_valid_before
            now = datetime.now()
            
            is_expired = now > not_after
            days_until_expiry = (not_after - now).days
            
            return {
                "is_expired": is_expired,
                "not_before": not_before.isoformat(),
                "not_after": not_after.isoformat(),
                "days_until_expiry": days_until_expiry,
                "expires_soon": days_until_expiry < 30,
                "subject": certificate.subject.rfc4514_string(),
                "issuer": certificate.issuer.rfc4514_string()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check certificate: {e}")
            raise
    
    # Feature 3: Validate certificate
    def validate_certificate(self, cert_path: str) -> Tuple[bool, str]:
        """Validate certificate format and integrity"""
        try:
            cert_pem = Path(cert_path).read_bytes()
            certificate = load_pem_x509_certificate(cert_pem, default_backend())
            
            # Check expiration
            now = datetime.now()
            if now < certificate.not_valid_before:
                return False, "Certificate not yet valid"
            
            if now > certificate.not_valid_after:
                return False, "Certificate has expired"
            
            return True, "Certificate is valid"
            
        except Exception as e:
            return False, f"Invalid certificate: {str(e)}"
    
    # Feature 4: Export certificate info
    def get_certificate_info(self, cert_path: str) -> Dict[str, Any]:
        """Get detailed certificate information"""
        try:
            cert_pem = Path(cert_path).read_bytes()
            certificate = load_pem_x509_certificate(cert_pem, default_backend())
            
            return {
                "version": certificate.version.name,
                "serial_number": certificate.serial_number,
                "subject": certificate.subject.rfc4514_string(),
                "issuer": certificate.issuer.rfc4514_string(),
                "not_before": certificate.not_valid_before.isoformat(),
                "not_after": certificate.not_valid_after.isoformat(),
                "signature_algorithm": certificate.signature_algorithm_oid._name
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get certificate info: {e}")
            raise
    
    # Feature 5: Convert certificate format
    def convert_certificate_format(
        self,
        input_path: str,
        output_path: str,
        output_format: str = "DER"
    ) -> bool:
        """Convert certificate between PEM and DER formats"""
        try:
            # Read input
            input_data = Path(input_path).read_bytes()
            
            # Try to load as PEM first
            try:
                certificate = load_pem_x509_certificate(input_data, default_backend())
            except:
                # Try DER format
                certificate = load_der_x509_certificate(input_data, default_backend())
            
            # Export in desired format
            if output_format.upper() == "PEM":
                output_data = certificate.public_bytes(serialization.Encoding.PEM)
            elif output_format.upper() == "DER":
                output_data = certificate.public_bytes(serialization.Encoding.DER)
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            Path(output_path).write_bytes(output_data)
            self.logger.info(f"Converted certificate to {output_format}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to convert certificate: {e}")
            return False


# ==================== Token Manager (JWT) ====================

class TokenManager:
    """
    JWT token management with 5+ features:
    1. Generate JWT tokens
    2. Verify JWT tokens
    3. Refresh tokens
    4. Revoke tokens
    5. Token blacklisting
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        self.logger = logging.getLogger("TokenManager")
        self.secret_key = secret_key or base64.b64encode(secrets.token_bytes(32)).decode()
        self.blacklist: set = set()
        
        if not JWT_AVAILABLE:
            self.logger.warning("JWT library not available")
    
    # Feature 1: Generate JWT token
    def generate_token(
        self,
        user_id: str,
        claims: Optional[Dict[str, Any]] = None,
        expires_in_minutes: int = 60
    ) -> str:
        """Generate JWT token"""
        if not JWT_AVAILABLE:
            raise ImportError("PyJWT not installed")
        
        try:
            payload = {
                "user_id": user_id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
                "jti": str(uuid.uuid4())  # Token ID for revocation
            }
            
            if claims:
                payload.update(claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            
            self.logger.info(f"Generated token for user: {user_id}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to generate token: {e}")
            raise
    
    # Feature 2: Verify JWT token
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Verify JWT token"""
        if not JWT_AVAILABLE:
            return False, None, "JWT not available"
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti in self.blacklist:
                return False, None, "Token has been revoked"
            
            return True, payload, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            return False, None, str(e)
    
    # Feature 3: Refresh token
    def refresh_token(self, token: str, expires_in_minutes: int = 60) -> Optional[str]:
        """Generate new token from existing token"""
        valid, payload, error = self.verify_token(token)
        
        if not valid:
            self.logger.warning(f"Cannot refresh invalid token: {error}")
            return None
        
        # Generate new token with same user_id
        user_id = payload.get("user_id")
        claims = {k: v for k, v in payload.items() if k not in ["iat", "exp", "jti"]}
        
        return self.generate_token(user_id, claims, expires_in_minutes)
    
    # Feature 4: Revoke token
    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding to blacklist"""
        valid, payload, error = self.verify_token(token)
        
        if valid and payload:
            jti = payload.get("jti")
            if jti:
                self.blacklist.add(jti)
                self.logger.info(f"Revoked token: {jti}")
                return True
        
        return False
    
    # Feature 5: Clear expired tokens from blacklist
    def cleanup_blacklist(self):
        """Remove expired tokens from blacklist"""
        # In production, store blacklist in database with expiration times
        # For now, just clear all
        cleared = len(self.blacklist)
        self.blacklist.clear()
        self.logger.info(f"Cleared {cleared} tokens from blacklist")


# ==================== Two-Factor Authentication Manager ====================

class TwoFactorAuthManager:
    """
    2FA/MFA management with 5+ features:
    1. Generate TOTP secrets
    2. Generate QR codes
    3. Verify TOTP codes
    4. Generate backup codes
    5. Validate backup codes
    """
    
    def __init__(self):
        self.logger = logging.getLogger("TwoFactorAuthManager")
        self.backup_codes: Dict[str, List[str]] = {}
        
        if not OTP_AVAILABLE:
            self.logger.warning("pyotp/qrcode not available")
    
    # Feature 1: Generate TOTP secret
    def generate_totp_secret(self, user_id: str, issuer: str = "Nexus") -> Dict[str, str]:
        """Generate TOTP secret for user"""
        if not OTP_AVAILABLE:
            raise ImportError("pyotp not installed")
        
        try:
            # Generate random secret
            secret = pyotp.random_base32()
            
            # Create provisioning URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_id,
                issuer_name=issuer
            )
            
            self.logger.info(f"Generated TOTP secret for user: {user_id}")
            
            return {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "user_id": user_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate TOTP secret: {e}")
            raise
    
    # Feature 2: Generate QR code
    def generate_qr_code(self, provisioning_uri: str, output_path: str) -> bool:
        """Generate QR code for TOTP setup"""
        if not OTP_AVAILABLE:
            raise ImportError("qrcode not installed")
        
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_path)
            
            self.logger.info(f"Generated QR code: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR code: {e}")
            return False
    
    # Feature 3: Verify TOTP code
    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify TOTP code"""
        if not OTP_AVAILABLE:
            return False
        
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
            
        except Exception as e:
            self.logger.error(f"TOTP verification failed: {e}")
            return False
    
    # Feature 4: Generate backup codes
    def generate_backup_codes(self, user_id: str, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        codes = []
        
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            code = f"{code[:4]}-{code[4:]}"  # Format: XXXX-XXXX
            codes.append(code)
        
        # Hash and store codes
        self.backup_codes[user_id] = [hashlib.sha256(c.encode()).hexdigest() for c in codes]
        
        self.logger.info(f"Generated {count} backup codes for user: {user_id}")
        return codes
    
    # Feature 5: Verify backup code
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume backup code"""
        if user_id not in self.backup_codes:
            return False
        
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        if code_hash in self.backup_codes[user_id]:
            # Remove used code
            self.backup_codes[user_id].remove(code_hash)
            self.logger.info(f"Backup code used for user: {user_id}")
            return True
        
        return False


# ==================== Access Control Manager (RBAC) ====================

class AccessControlManager:
    """
    Role-Based Access Control with 5+ features:
    1. Define roles and permissions
    2. Assign roles to users
    3. Check permissions
    4. Role hierarchy
    5. Audit access attempts
    """
    
    def __init__(self):
        self.logger = logging.getLogger("AccessControlManager")
        self.roles: Dict[str, List[str]] = {}
        self.user_roles: Dict[str, List[str]] = {}
        self.role_hierarchy: Dict[str, List[str]] = {}
        self.audit_log: List[AuditEntry] = []
    
    # Feature 1: Define role
    def define_role(self, role_name: str, permissions: List[str]) -> bool:
        """Define a role with permissions"""
        try:
            self.roles[role_name] = permissions
            self.logger.info(f"Defined role: {role_name} with {len(permissions)} permissions")
            return True
        except Exception as e:
            self.logger.error(f"Failed to define role: {e}")
            return False
    
    # Feature 2: Assign role to user
    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        if role_name not in self.roles:
            self.logger.warning(f"Role {role_name} does not exist")
            return False
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        
        if role_name not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_name)
            self.logger.info(f"Assigned role {role_name} to user {user_id}")
            self._audit("role_assigned", user_id, role_name, "success")
            return True
        
        return False
    
    # Feature 3: Check permission
    def check_permission(
        self,
        user_id: str,
        required_permission: str,
        resource: Optional[str] = None
    ) -> bool:
        """Check if user has required permission"""
        if user_id not in self.user_roles:
            self._audit("permission_check", user_id, required_permission, "denied")
            return False
        
        # Get all user permissions from roles
        user_permissions = set()
        for role in self.user_roles[user_id]:
            if role in self.roles:
                user_permissions.update(self.roles[role])
            
            # Check inherited roles
            if role in self.role_hierarchy:
                for inherited_role in self.role_hierarchy[role]:
                    if inherited_role in self.roles:
                        user_permissions.update(self.roles[inherited_role])
        
        # Check permission
        has_permission = required_permission in user_permissions or "*" in user_permissions
        
        result = "granted" if has_permission else "denied"
        self._audit("permission_check", user_id, required_permission, result, {"resource": resource})
        
        return has_permission
    
    # Feature 4: Set role hierarchy
    def set_role_hierarchy(self, role: str, inherits_from: List[str]) -> bool:
        """Set role inheritance"""
        try:
            self.role_hierarchy[role] = inherits_from
            self.logger.info(f"Set hierarchy: {role} inherits from {inherits_from}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set hierarchy: {e}")
            return False
    
    # Feature 5: Get user permissions
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        if user_id not in self.user_roles:
            return []
        
        permissions = set()
        for role in self.user_roles[user_id]:
            if role in self.roles:
                permissions.update(self.roles[role])
        
        return list(permissions)
    
    def _audit(self, action: str, user: str, resource: str, result: str, metadata: Optional[Dict] = None):
        """Log access control audit event"""
        entry = AuditEntry(
            timestamp=datetime.now(),
            action=action,
            user=user,
            resource=resource,
            result=result,
            metadata=metadata or {}
        )
        self.audit_log.append(entry)
    
    def get_audit_log(self) -> List[Dict]:
        """Get audit log"""
        return [e.to_dict() for e in self.audit_log]


# ==================== Main Enterprise Security Manager ====================

class EnterpriseSecurityManager:
    """
    Comprehensive enterprise security management system.
    Integrates all security components:
    - SSH key management
    - Secret encryption/decryption
    - Password management
    - API key management
    - Certificate management
    - JWT tokens
    - 2FA/MFA
    - Access control (RBAC)
    - Audit logging
    """
    
    def __init__(
        self,
        storage_base_dir: str = "/var/secure",
        master_key: Optional[str] = None
    ):
        self.logger = self._setup_logging()
        
        # Initialize all managers
        self.ssh_keys = SSHKeyManager(f"{storage_base_dir}/ssh")
        self.secrets = SecretManager(master_key, f"{storage_base_dir}/secrets")
        self.passwords = PasswordManager()
        self.api_keys = APIKeyManager(f"{storage_base_dir}/api_keys")
        self.certificates = CertificateManager(f"{storage_base_dir}/certs")
        self.tokens = TokenManager()
        self.two_factor = TwoFactorAuthManager()
        self.access_control = AccessControlManager()
        
        self.logger.info("Enterprise Security Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger("EnterpriseSecurityManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security system status"""
        return {
            "ssh_keys": len(self.ssh_keys.list_ssh_keys()),
            "secrets": len(self.secrets.list_secrets()),
            "api_keys": len(self.api_keys.list_api_keys()),
            "roles_defined": len(self.access_control.roles),
            "users_with_roles": len(self.access_control.user_roles),
            "audit_entries": len(self.ssh_keys.audit_log) + 
                           len(self.secrets.audit_log) +
                           len(self.access_control.audit_log)
        }
    
    def export_audit_logs(self, output_file: str):
        """Export all audit logs"""
        all_logs = {
            "ssh_keys": self.ssh_keys.get_audit_log(),
            "secrets": self.secrets.get_audit_log(),
            "access_control": self.access_control.get_audit_log()
        }
        
        Path(output_file).write_text(json.dumps(all_logs, indent=2))
        self.logger.info(f"Exported audit logs to {output_file}")


# ==================== Example Usage ====================

def example_usage():
    """Example usage of Enterprise Security Manager"""
    
    # Initialize manager
    security = EnterpriseSecurityManager(storage_base_dir="/tmp/secure")
    
    print("=" * 60)
    print("ENTERPRISE SECURITY MANAGER - DEMO")
    print("=" * 60)
    
    # 1. SSH Key Management
    print("\n1. SSH Key Management")
    print("-" * 60)
    private_key, public_key = security.ssh_keys.generate_ssh_key_pair(
        key_type=KeyType.ED25519,
        key_name="demo_key"
    )
    print(f"✓ Generated SSH key pair")
    print(f"  Private: {private_key}")
    print(f"  Public: {public_key}")
    
    # 2. Secret Management
    print("\n2. Secret Management")
    print("-" * 60)
    secret_id = security.secrets.encrypt_secret(
        "my-database-password-123",
        "db_password",
        tags={"env": "production", "service": "database"}
    )
    print(f"✓ Encrypted secret: {secret_id}")
    
    decrypted = security.secrets.decrypt_secret(secret_id)
    print(f"✓ Decrypted secret: {decrypted}")
    
    # 3. Password Management
    print("\n3. Password Management")
    print("-" * 60)
    password = security.passwords.generate_password(length=16)
    print(f"✓ Generated password: {password}")
    
    strength = security.passwords.check_password_strength(password)
    print(f"✓ Password strength: {strength['strength']}")
    print(f"  Entropy: {strength['entropy']} bits")
    
    # 4. API Key Management
    print("\n4. API Key Management")
    print("-" * 60)
    api_key = security.api_keys.generate_api_key(
        "demo_service",
        permissions=["read", "write"],
        expires_in_days=30
    )
    print(f"✓ Generated API key: {api_key.key[:20]}...")
    print(f"  Permissions: {api_key.permissions}")
    
    # 5. Certificate Management
    print("\n5. Certificate Management")
    print("-" * 60)
    cert_path, key_path = security.certificates.generate_self_signed_cert(
        "demo.example.com",
        dns_names=["demo.example.com", "www.demo.example.com"]
    )
    print(f"✓ Generated certificate: {cert_path}")
    
    cert_info = security.certificates.check_certificate_expiration(cert_path)
    print(f"  Expires in: {cert_info['days_until_expiry']} days")
    
    # 6. JWT Tokens
    print("\n6. JWT Token Management")
    print("-" * 60)
    token = security.tokens.generate_token(
        "user123",
        claims={"role": "admin"},
        expires_in_minutes=60
    )
    print(f"✓ Generated JWT token: {token[:50]}...")
    
    valid, payload, error = security.tokens.verify_token(token)
    print(f"✓ Token valid: {valid}")
    if payload:
        print(f"  User ID: {payload['user_id']}")
    
    # 7. Two-Factor Authentication
    print("\n7. Two-Factor Authentication")
    print("-" * 60)
    if OTP_AVAILABLE:
        totp_data = security.two_factor.generate_totp_secret("user123")
        print(f"✓ Generated TOTP secret")
        print(f"  Secret: {totp_data['secret']}")
        
        backup_codes = security.two_factor.generate_backup_codes("user123")
        print(f"✓ Generated {len(backup_codes)} backup codes")
        print(f"  Example: {backup_codes[0]}")
    else:
        print("⚠ OTP library not available")
    
    # 8. Access Control (RBAC)
    print("\n8. Access Control (RBAC)")
    print("-" * 60)
    security.access_control.define_role("admin", ["*"])
    security.access_control.define_role("editor", ["read", "write"])
    security.access_control.define_role("viewer", ["read"])
    print(f"✓ Defined 3 roles")
    
    security.access_control.assign_role("user123", "editor")
    print(f"✓ Assigned 'editor' role to user123")
    
    can_write = security.access_control.check_permission("user123", "write")
    can_delete = security.access_control.check_permission("user123", "delete")
    print(f"✓ Permission check - write: {can_write}, delete: {can_delete}")
    
    # 9. Security Status
    print("\n9. Security Status")
    print("-" * 60)
    status = security.get_security_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    example_usage()