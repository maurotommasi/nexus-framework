#!/usr/bin/env python3
"""
Nexus Enterprise Licensing System
==================================
Production-ready licensing and subscription management system
with API and CLI integration.

Author: Mauro Tommasi
Version: 1.0.0
License: Proprietary
"""

import os
import sys
import json
import uuid
import hashlib
import hmac
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

# Third-party imports
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class LicenseType(Enum):
    """License subscription types"""
    TRIAL = "trial"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ENTERPRISE = "enterprise"
    PERPETUAL = "perpetual"


class LicenseStatus(Enum):
    """License status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class FeatureFlag(Enum):
    """Available features"""
    BASIC_ETL = "basic_etl"
    ADVANCED_ETL = "advanced_etl"
    DATABASE_MANAGEMENT = "database_management"
    PIPELINE_AUTOMATION = "pipeline_automation"
    API_ACCESS = "api_access"
    CLOUD_CONNECTORS = "cloud_connectors"
    CUSTOM_CODE = "custom_code"
    ENTERPRISE_SUPPORT = "enterprise_support"
    UNLIMITED_JOBS = "unlimited_jobs"
    PRIORITY_SUPPORT = "priority_support"


@dataclass
class License:
    """License data model"""
    license_key: str
    customer_id: str
    customer_name: str
    customer_email: str
    license_type: LicenseType
    status: LicenseStatus
    issue_date: datetime
    expiry_date: datetime
    features: List[FeatureFlag]
    max_users: int = 1
    max_jobs: int = 10
    max_api_calls_per_day: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActivationRequest:
    """License activation request"""
    license_key: str
    machine_id: str
    activation_code: Optional[str] = None


@dataclass
class ValidationResult:
    """License validation result"""
    is_valid: bool
    license: Optional[License] = None
    error_message: Optional[str] = None
    remaining_days: Optional[int] = None


# =============================================================================
# LICENSE MANAGER
# =============================================================================

class LicenseManager:
    """
    Enterprise License Management System
    Handles license generation, validation, activation, and renewal
    """
    
    def __init__(self, db_config: Dict[str, Any], secret_key: str):
        self.db_config = db_config
        self.secret_key = secret_key.encode()
        self.logger = logging.getLogger('LicenseManager')
        self.fernet = Fernet(self._derive_key(secret_key))
        
        # RSA keys for signing
        self.private_key = self._load_or_generate_rsa_key()
        self.public_key = self.private_key.public_key()
        
        # Initialize database
        self._init_database()
    
    def _derive_key(self, secret: str) -> bytes:
        """Derive encryption key from secret"""
        return base64.urlsafe_b64encode(
            hashlib.sha256(secret.encode()).digest()
        )
    
    def _load_or_generate_rsa_key(self):
        """Load or generate RSA private key"""
        key_path = Path('.nexus/private_key.pem')
        
        if key_path.exists():
            with open(key_path, 'rb') as f:
                return serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
        else:
            # Generate new key
            key_path.parent.mkdir(exist_ok=True)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Save private key
            with open(key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(key_path.parent / 'public_key.pem', 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            return private_key
    
    def _init_database(self):
        """Initialize database schema"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                # Read and execute schema
                schema_sql = """
                -- See schema.sql for complete schema
                """
                # Execute schema (truncated for brevity)
                cur.execute(schema_sql)
                conn.commit()
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config.get('port', 5432),
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    # =========================================================================
    # LICENSE GENERATION
    # =========================================================================
    
    def generate_license(
        self,
        customer_name: str,
        customer_email: str,
        license_type: LicenseType,
        duration_days: Optional[int] = None,
        features: Optional[List[FeatureFlag]] = None,
        max_users: int = 1,
        max_jobs: int = 10
    ) -> License:
        """Generate new license"""
        
        # Generate unique license key
        license_key = self._generate_license_key()
        customer_id = str(uuid.uuid4())
        
        # Calculate expiry date
        issue_date = datetime.now()
        if license_type == LicenseType.TRIAL:
            expiry_date = issue_date + timedelta(days=14)
        elif license_type == LicenseType.MONTHLY:
            expiry_date = issue_date + timedelta(days=30)
        elif license_type == LicenseType.ANNUAL:
            expiry_date = issue_date + timedelta(days=365)
        elif license_type == LicenseType.PERPETUAL:
            expiry_date = issue_date + timedelta(days=36500)  # 100 years
        else:
            expiry_date = issue_date + timedelta(days=duration_days or 365)
        
        # Default features based on license type
        if features is None:
            features = self._get_default_features(license_type)
        
        # Create license
        license_obj = License(
            license_key=license_key,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            license_type=license_type,
            status=LicenseStatus.ACTIVE,
            issue_date=issue_date,
            expiry_date=expiry_date,
            features=features,
            max_users=max_users,
            max_jobs=max_jobs
        )
        
        # Store in database
        self._store_license(license_obj)
        
        # Log activity
        self._log_activity(
            license_key,
            'license_generated',
            {'customer_email': customer_email, 'type': license_type.value}
        )
        
        self.logger.info(f"Generated license {license_key} for {customer_email}")
        return license_obj
    
    def _generate_license_key(self) -> str:
        """Generate unique license key in format: NEXUS-XXXX-XXXX-XXXX-XXXX"""
        segments = []
        for _ in range(4):
            segment = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(4))
            segments.append(segment)
        
        return f"NEXUS-{'-'.join(segments)}"
    
    def _get_default_features(self, license_type: LicenseType) -> List[FeatureFlag]:
        """Get default features for license type"""
        feature_map = {
            LicenseType.TRIAL: [
                FeatureFlag.BASIC_ETL,
                FeatureFlag.DATABASE_MANAGEMENT,
                FeatureFlag.API_ACCESS
            ],
            LicenseType.MONTHLY: [
                FeatureFlag.BASIC_ETL,
                FeatureFlag.ADVANCED_ETL,
                FeatureFlag.DATABASE_MANAGEMENT,
                FeatureFlag.PIPELINE_AUTOMATION,
                FeatureFlag.API_ACCESS,
                FeatureFlag.CLOUD_CONNECTORS
            ],
            LicenseType.ANNUAL: [
                FeatureFlag.BASIC_ETL,
                FeatureFlag.ADVANCED_ETL,
                FeatureFlag.DATABASE_MANAGEMENT,
                FeatureFlag.PIPELINE_AUTOMATION,
                FeatureFlag.API_ACCESS,
                FeatureFlag.CLOUD_CONNECTORS,
                FeatureFlag.CUSTOM_CODE
            ],
            LicenseType.ENTERPRISE: [feat for feat in FeatureFlag],
            LicenseType.PERPETUAL: [feat for feat in FeatureFlag]
        }
        
        return feature_map.get(license_type, [FeatureFlag.BASIC_ETL])
    
    def _store_license(self, license_obj: License):
        """Store license in database"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO licenses (
                        license_key, customer_id, customer_name, customer_email,
                        license_type, status, issue_date, expiry_date,
                        features, max_users, max_jobs, max_api_calls_per_day,
                        metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    license_obj.license_key,
                    license_obj.customer_id,
                    license_obj.customer_name,
                    license_obj.customer_email,
                    license_obj.license_type.value,
                    license_obj.status.value,
                    license_obj.issue_date,
                    license_obj.expiry_date,
                    json.dumps([f.value for f in license_obj.features]),
                    license_obj.max_users,
                    license_obj.max_jobs,
                    license_obj.max_api_calls_per_day,
                    json.dumps(license_obj.metadata)
                ))
                conn.commit()
    
    # =========================================================================
    # LICENSE VALIDATION
    # =========================================================================
    
    def validate_license(self, license_key: str, machine_id: Optional[str] = None) -> ValidationResult:
        """Validate license key"""
        try:
            # Retrieve license from database
            license_obj = self._get_license(license_key)
            
            if not license_obj:
                return ValidationResult(
                    is_valid=False,
                    error_message="Invalid license key"
                )
            
            # Check status
            if license_obj.status != LicenseStatus.ACTIVE:
                return ValidationResult(
                    is_valid=False,
                    license=license_obj,
                    error_message=f"License is {license_obj.status.value}"
                )
            
            # Check expiry
            if datetime.now() > license_obj.expiry_date:
                # Update status
                self._update_license_status(license_key, LicenseStatus.EXPIRED)
                return ValidationResult(
                    is_valid=False,
                    license=license_obj,
                    error_message="License has expired"
                )
            
            # Check machine activation if required
            if machine_id:
                if not self._is_machine_activated(license_key, machine_id):
                    return ValidationResult(
                        is_valid=False,
                        license=license_obj,
                        error_message="Machine not activated"
                    )
            
            # Calculate remaining days
            remaining_days = (license_obj.expiry_date - datetime.now()).days
            
            # Log validation
            self._log_activity(
                license_key,
                'license_validated',
                {'machine_id': machine_id}
            )
            
            return ValidationResult(
                is_valid=True,
                license=license_obj,
                remaining_days=remaining_days
            )
            
        except Exception as e:
            self.logger.error(f"License validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=str(e)
            )
    
    def _get_license(self, license_key: str) -> Optional[License]:
        """Retrieve license from database"""
        with self._get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM licenses WHERE license_key = %s
                """, (license_key,))
                
                row = cur.fetchone()
                
                if not row:
                    return None
                
                return License(
                    license_key=row['license_key'],
                    customer_id=row['customer_id'],
                    customer_name=row['customer_name'],
                    customer_email=row['customer_email'],
                    license_type=LicenseType(row['license_type']),
                    status=LicenseStatus(row['status']),
                    issue_date=row['issue_date'],
                    expiry_date=row['expiry_date'],
                    features=[FeatureFlag(f) for f in json.loads(row['features'])],
                    max_users=row['max_users'],
                    max_jobs=row['max_jobs'],
                    max_api_calls_per_day=row['max_api_calls_per_day'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
    
    def _update_license_status(self, license_key: str, status: LicenseStatus):
        """Update license status"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE licenses 
                    SET status = %s, updated_at = NOW()
                    WHERE license_key = %s
                """, (status.value, license_key))
                conn.commit()
    
    # =========================================================================
    # MACHINE ACTIVATION
    # =========================================================================
    
    def activate_machine(self, license_key: str, machine_id: str) -> bool:
        """Activate license on specific machine"""
        try:
            # Validate license
            result = self.validate_license(license_key)
            if not result.is_valid:
                self.logger.error(f"Cannot activate: {result.error_message}")
                return False
            
            # Check activation limit
            license_obj = result.license
            current_activations = self._get_activation_count(license_key)
            
            if current_activations >= license_obj.max_users:
                self.logger.error(f"Activation limit reached: {current_activations}/{license_obj.max_users}")
                return False
            
            # Check if already activated
            if self._is_machine_activated(license_key, machine_id):
                self.logger.info(f"Machine {machine_id} already activated")
                return True
            
            # Create activation
            activation_code = self._generate_activation_code(license_key, machine_id)
            
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO machine_activations (
                            license_key, machine_id, activation_code, activated_at
                        ) VALUES (%s, %s, %s, NOW())
                    """, (license_key, machine_id, activation_code))
                    conn.commit()
            
            # Log activity
            self._log_activity(
                license_key,
                'machine_activated',
                {'machine_id': machine_id}
            )
            
            self.logger.info(f"Machine {machine_id} activated for license {license_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Machine activation failed: {e}")
            return False
    
    def deactivate_machine(self, license_key: str, machine_id: str) -> bool:
        """Deactivate license on specific machine"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE machine_activations
                        SET deactivated_at = NOW()
                        WHERE license_key = %s AND machine_id = %s
                    """, (license_key, machine_id))
                    conn.commit()
            
            self._log_activity(
                license_key,
                'machine_deactivated',
                {'machine_id': machine_id}
            )
            
            self.logger.info(f"Machine {machine_id} deactivated")
            return True
            
        except Exception as e:
            self.logger.error(f"Machine deactivation failed: {e}")
            return False
    
    def _is_machine_activated(self, license_key: str, machine_id: str) -> bool:
        """Check if machine is activated"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM machine_activations
                    WHERE license_key = %s 
                    AND machine_id = %s
                    AND deactivated_at IS NULL
                """, (license_key, machine_id))
                
                count = cur.fetchone()[0]
                return count > 0
    
    def _get_activation_count(self, license_key: str) -> int:
        """Get number of active machines"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM machine_activations
                    WHERE license_key = %s AND deactivated_at IS NULL
                """, (license_key,))
                
                return cur.fetchone()[0]
    
    def _generate_activation_code(self, license_key: str, machine_id: str) -> str:
        """Generate activation code"""
        data = f"{license_key}:{machine_id}:{datetime.now().isoformat()}"
        signature = hmac.new(
            self.secret_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{signature[:16]}"
    
    # =========================================================================
    # LICENSE RENEWAL
    # =========================================================================
    
    def renew_license(self, license_key: str, extend_days: Optional[int] = None) -> bool:
        """Renew license"""
        try:
            license_obj = self._get_license(license_key)
            
            if not license_obj:
                return False
            
            # Calculate new expiry
            if extend_days:
                new_expiry = license_obj.expiry_date + timedelta(days=extend_days)
            elif license_obj.license_type == LicenseType.MONTHLY:
                new_expiry = license_obj.expiry_date + timedelta(days=30)
            elif license_obj.license_type == LicenseType.ANNUAL:
                new_expiry = license_obj.expiry_date + timedelta(days=365)
            else:
                new_expiry = license_obj.expiry_date + timedelta(days=365)
            
            # Update database
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE licenses
                        SET expiry_date = %s,
                            status = %s,
                            updated_at = NOW()
                        WHERE license_key = %s
                    """, (new_expiry, LicenseStatus.ACTIVE.value, license_key))
                    conn.commit()
            
            # Log activity
            self._log_activity(
                license_key,
                'license_renewed',
                {'new_expiry': new_expiry.isoformat()}
            )
            
            self.logger.info(f"License {license_key} renewed until {new_expiry}")
            return True
            
        except Exception as e:
            self.logger.error(f"License renewal failed: {e}")
            return False
    
    # =========================================================================
    # FEATURE MANAGEMENT
    # =========================================================================
    
    def has_feature(self, license_key: str, feature: FeatureFlag) -> bool:
        """Check if license has specific feature"""
        license_obj = self._get_license(license_key)
        
        if not license_obj:
            return False
        
        return feature in license_obj.features
    
    def add_feature(self, license_key: str, feature: FeatureFlag) -> bool:
        """Add feature to license"""
        try:
            license_obj = self._get_license(license_key)
            
            if not license_obj:
                return False
            
            if feature not in license_obj.features:
                license_obj.features.append(feature)
                
                with self._get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE licenses
                            SET features = %s, updated_at = NOW()
                            WHERE license_key = %s
                        """, (json.dumps([f.value for f in license_obj.features]), license_key))
                        conn.commit()
                
                self._log_activity(
                    license_key,
                    'feature_added',
                    {'feature': feature.value}
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add feature: {e}")
            return False
    
    # =========================================================================
    # USAGE TRACKING
    # =========================================================================
    
    def track_api_call(self, license_key: str) -> bool:
        """Track API call for rate limiting"""
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO api_usage (license_key, call_timestamp)
                        VALUES (%s, NOW())
                    """, (license_key,))
                    conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to track API call: {e}")
            return False
    
    def get_api_usage_today(self, license_key: str) -> int:
        """Get API usage count for today"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM api_usage
                    WHERE license_key = %s 
                    AND call_timestamp >= CURRENT_DATE
                """, (license_key,))
                
                return cur.fetchone()[0]
    
    def check_rate_limit(self, license_key: str) -> bool:
        """Check if under rate limit"""
        license_obj = self._get_license(license_key)
        
        if not license_obj:
            return False
        
        usage_today = self.get_api_usage_today(license_key)
        
        return usage_today < license_obj.max_api_calls_per_day
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def _log_activity(self, license_key: str, activity_type: str, details: Dict):
        """Log license activity"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO license_activity (
                        license_key, activity_type, activity_details, activity_timestamp
                    ) VALUES (%s, %s, %s, NOW())
                """, (license_key, activity_type, json.dumps(details)))
                conn.commit()
    
    def get_license_info(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Get complete license information"""
        result = self.validate_license(license_key)
        
        if not result.license:
            return None
        
        license_obj = result.license
        
        return {
            'license_key': license_obj.license_key,
            'customer_name': license_obj.customer_name,
            'customer_email': license_obj.customer_email,
            'type': license_obj.license_type.value,
            'status': license_obj.status.value,
            'is_valid': result.is_valid,
            'issue_date': license_obj.issue_date.isoformat(),
            'expiry_date': license_obj.expiry_date.isoformat(),
            'remaining_days': result.remaining_days,
            'features': [f.value for f in license_obj.features],
            'max_users': license_obj.max_users,
            'max_jobs': license_obj.max_jobs,
            'active_machines': self._get_activation_count(license_obj.license_key),
            'api_usage_today': self.get_api_usage_today(license_obj.license_key),
            'max_api_calls_per_day': license_obj.max_api_calls_per_day
        }


# =============================================================================
# CLI & API DECORATOR
# =============================================================================

def require_license(feature: Optional[FeatureFlag] = None):
    """Decorator to enforce license validation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get license manager instance
            license_manager = get_license_manager()
            
            # Get license key from environment or config
            license_key = os.getenv('NEXUS_LICENSE_KEY')
            
            if not license_key:
                raise PermissionError("No license key configured. Set NEXUS_LICENSE_KEY environment variable.")
            
            # Validate license
            result = license_manager.validate_license(license_key, get_machine_id())
            
            if not result.is_valid:
                raise PermissionError(f"License validation failed: {result.error_message}")
            
            # Check specific feature if required
            if feature and not license_manager.has_feature(license_key, feature):
                raise PermissionError(f"License does not include feature: {feature.value}")
            
            # Check rate limit for API calls
            if not license_manager.check_rate_limit(license_key):
                raise PermissionError("API rate limit exceeded")
            
            # Track API usage
            license_manager.track_api_call(license_key)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_machine_id() -> str:
    """Get unique machine identifier"""
    import platform
    import socket
    
    # Combine multiple identifiers
    identifiers = [
        platform.node(),
        socket.gethostname(),
        str(uuid.getnode())  # MAC address
    ]
    
    combined = '|'.join(identifiers)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


# Singleton instance
_license_manager = None

def get_license_manager() -> LicenseManager:
    """Get license manager singleton"""
    global _license_manager
    
    if _license_manager is None:
        db_config = {
            'host': os.getenv('LICENSE_DB_HOST', 'localhost'),
            'port': int(os.getenv('LICENSE_DB_PORT', 5432)),
            'database': os.getenv('LICENSE_DB_NAME', 'nexus_licenses'),
            'user': os.getenv('LICENSE_DB_USER', 'nexus'),
            'password': os.getenv('LICENSE_DB_PASSWORD', '')
        }
        
        secret_key = os.getenv('NEXUS_SECRET_KEY', secrets.token_urlsafe(32))
        
        _license_manager = LicenseManager(db_config, secret_key)
    
    return _license_manager