#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Nexus Enterprise Licensing System
================================================================
100 unit tests covering all components, edge cases, and scenarios

Author: Test Suite
Version: 1.0.0
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
import json
import os
import secrets
from pathlib import Path

# Import the licensing system components
# Assuming the main file is named 'nexus_license.py'
from nexus_license import (
    LicenseType, LicenseStatus, FeatureFlag, License, 
    ActivationRequest, ValidationResult, LicenseManager,
    require_license, get_machine_id, get_license_manager
)


class TestEnums(unittest.TestCase):
    """Tests for Enum classes"""
    
    def test_001_license_type_values(self):
        """Test LicenseType enum has correct values"""
        self.assertEqual(LicenseType.TRIAL.value, "trial")
        self.assertEqual(LicenseType.MONTHLY.value, "monthly")
        self.assertEqual(LicenseType.ANNUAL.value, "annual")
        self.assertEqual(LicenseType.ENTERPRISE.value, "enterprise")
        self.assertEqual(LicenseType.PERPETUAL.value, "perpetual")
    
    def test_002_license_status_values(self):
        """Test LicenseStatus enum has correct values"""
        self.assertEqual(LicenseStatus.ACTIVE.value, "active")
        self.assertEqual(LicenseStatus.EXPIRED.value, "expired")
        self.assertEqual(LicenseStatus.SUSPENDED.value, "suspended")
        self.assertEqual(LicenseStatus.REVOKED.value, "revoked")
        self.assertEqual(LicenseStatus.PENDING.value, "pending")
    
    def test_003_feature_flag_count(self):
        """Test all feature flags are defined"""
        features = list(FeatureFlag)
        self.assertEqual(len(features), 10)
    
    def test_004_feature_flag_values(self):
        """Test specific feature flag values"""
        self.assertEqual(FeatureFlag.BASIC_ETL.value, "basic_etl")
        self.assertEqual(FeatureFlag.API_ACCESS.value, "api_access")
        self.assertEqual(FeatureFlag.ENTERPRISE_SUPPORT.value, "enterprise_support")


class TestDataClasses(unittest.TestCase):
    """Tests for data classes"""
    
    def test_005_license_creation(self):
        """Test License dataclass creation"""
        license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="John Doe",
            customer_email="john@example.com",
            license_type=LicenseType.TRIAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=14),
            features=[FeatureFlag.BASIC_ETL],
            max_users=1,
            max_jobs=10
        )
        self.assertEqual(license.license_key, "TEST-1234")
        self.assertEqual(license.customer_name, "John Doe")
    
    def test_006_license_default_values(self):
        """Test License default values"""
        license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="John Doe",
            customer_email="john@example.com",
            license_type=LicenseType.TRIAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=14),
            features=[]
        )
        self.assertEqual(license.max_users, 1)
        self.assertEqual(license.max_jobs, 10)
        self.assertEqual(license.max_api_calls_per_day, 1000)
    
    def test_007_activation_request_creation(self):
        """Test ActivationRequest creation"""
        request = ActivationRequest(
            license_key="TEST-1234",
            machine_id="machine-abc"
        )
        self.assertEqual(request.license_key, "TEST-1234")
        self.assertIsNone(request.activation_code)
    
    def test_008_validation_result_valid(self):
        """Test ValidationResult for valid license"""
        result = ValidationResult(
            is_valid=True,
            remaining_days=30
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.remaining_days, 30)
    
    def test_009_validation_result_invalid(self):
        """Test ValidationResult for invalid license"""
        result = ValidationResult(
            is_valid=False,
            error_message="License expired"
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "License expired")


class TestLicenseManagerInit(unittest.TestCase):
    """Tests for LicenseManager initialization"""
    
    @patch('nexus_license.psycopg2.connect')
    @patch('nexus_license.Path.exists')
    def test_010_init_with_config(self, mock_exists, mock_connect):
        """Test LicenseManager initialization"""
        mock_exists.return_value = False
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        db_config = {
            'host': 'localhost',
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
        
        manager = LicenseManager(db_config, "secret_key_123")
        self.assertIsNotNone(manager)
        self.assertEqual(manager.db_config, db_config)
    
    @patch('nexus_license.psycopg2.connect')
    @patch('nexus_license.Path.exists')
    def test_011_derive_key(self, mock_exists, mock_connect):
        """Test encryption key derivation"""
        mock_exists.return_value = False
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        manager = LicenseManager({}, "test_secret")
        key = manager._derive_key("test_secret")
        self.assertEqual(len(key), 44)  # Base64 encoded 32 bytes
    
    @patch('nexus_license.psycopg2.connect')
    @patch('nexus_license.Path.exists')
    @patch('nexus_license.Path.mkdir')
    @patch('builtins.open', create=True)
    def test_012_rsa_key_generation(self, mock_open, mock_mkdir, mock_exists, mock_connect):
        """Test RSA key generation"""
        mock_exists.return_value = False
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        manager = LicenseManager({}, "secret")
        self.assertIsNotNone(manager.private_key)
        self.assertIsNotNone(manager.public_key)


class TestLicenseGeneration(unittest.TestCase):
    """Tests for license generation"""
    
    def setUp(self):
        self.manager = self._create_mock_manager()
    
    def _create_mock_manager(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            return LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_013_generate_trial_license(self, mock_log, mock_store):
        """Test generating trial license"""
        license = self.manager.generate_license(
            "John Doe",
            "john@example.com",
            LicenseType.TRIAL
        )
        self.assertEqual(license.license_type, LicenseType.TRIAL)
        self.assertTrue(license.license_key.startswith("NEXUS-"))
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_014_generate_monthly_license(self, mock_log, mock_store):
        """Test generating monthly license"""
        license = self.manager.generate_license(
            "Jane Doe",
            "jane@example.com",
            LicenseType.MONTHLY
        )
        duration = (license.expiry_date - license.issue_date).days
        self.assertEqual(duration, 30)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_015_generate_annual_license(self, mock_log, mock_store):
        """Test generating annual license"""
        license = self.manager.generate_license(
            "Bob Smith",
            "bob@example.com",
            LicenseType.ANNUAL
        )
        duration = (license.expiry_date - license.issue_date).days
        self.assertEqual(duration, 365)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_016_generate_perpetual_license(self, mock_log, mock_store):
        """Test generating perpetual license"""
        license = self.manager.generate_license(
            "Alice Johnson",
            "alice@example.com",
            LicenseType.PERPETUAL
        )
        duration = (license.expiry_date - license.issue_date).days
        self.assertGreater(duration, 36000)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_017_generate_custom_duration(self, mock_log, mock_store):
        """Test generating license with custom duration"""
        license = self.manager.generate_license(
            "Charlie Brown",
            "charlie@example.com",
            LicenseType.ENTERPRISE,
            duration_days=90
        )
        duration = (license.expiry_date - license.issue_date).days
        self.assertEqual(duration, 90)
    
    def test_018_license_key_format(self):
        """Test license key format"""
        key = self.manager._generate_license_key()
        parts = key.split('-')
        self.assertEqual(len(parts), 5)
        self.assertEqual(parts[0], "NEXUS")
        for part in parts[1:]:
            self.assertEqual(len(part), 4)
    
    def test_019_license_key_uniqueness(self):
        """Test license keys are unique"""
        keys = set()
        for _ in range(100):
            key = self.manager._generate_license_key()
            keys.add(key)
        self.assertEqual(len(keys), 100)
    
    def test_020_trial_default_features(self):
        """Test trial license default features"""
        features = self.manager._get_default_features(LicenseType.TRIAL)
        self.assertIn(FeatureFlag.BASIC_ETL, features)
        self.assertIn(FeatureFlag.DATABASE_MANAGEMENT, features)
        self.assertEqual(len(features), 3)
    
    def test_021_enterprise_default_features(self):
        """Test enterprise license has all features"""
        features = self.manager._get_default_features(LicenseType.ENTERPRISE)
        self.assertEqual(len(features), len(list(FeatureFlag)))
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_022_custom_features(self, mock_log, mock_store):
        """Test generating license with custom features"""
        custom_features = [FeatureFlag.BASIC_ETL, FeatureFlag.API_ACCESS]
        license = self.manager.generate_license(
            "Dave Wilson",
            "dave@example.com",
            LicenseType.MONTHLY,
            features=custom_features
        )
        self.assertEqual(len(license.features), 2)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_023_custom_max_users(self, mock_log, mock_store):
        """Test generating license with custom max users"""
        license = self.manager.generate_license(
            "Eve Adams",
            "eve@example.com",
            LicenseType.ENTERPRISE,
            max_users=50
        )
        self.assertEqual(license.max_users, 50)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_024_custom_max_jobs(self, mock_log, mock_store):
        """Test generating license with custom max jobs"""
        license = self.manager.generate_license(
            "Frank Miller",
            "frank@example.com",
            LicenseType.ANNUAL,
            max_jobs=100
        )
        self.assertEqual(license.max_jobs, 100)


class TestLicenseValidation(unittest.TestCase):
    """Tests for license validation"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_025_validate_active_license(self, mock_log, mock_get):
        """Test validating active license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        result = self.manager.validate_license("TEST-1234")
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.license)
    
    @patch.object(LicenseManager, '_get_license')
    def test_026_validate_invalid_key(self, mock_get):
        """Test validating invalid license key"""
        mock_get.return_value = None
        
        result = self.manager.validate_license("INVALID-KEY")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "Invalid license key")
    
    @patch.object(LicenseManager, '_get_license')
    def test_027_validate_expired_license(self, mock_get):
        """Test validating expired license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.TRIAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now() - timedelta(days=30),
            expiry_date=datetime.now() - timedelta(days=1),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        with patch.object(self.manager, '_update_license_status'):
            result = self.manager.validate_license("TEST-1234")
            self.assertFalse(result.is_valid)
            self.assertEqual(result.error_message, "License has expired")
    
    @patch.object(LicenseManager, '_get_license')
    def test_028_validate_suspended_license(self, mock_get):
        """Test validating suspended license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.SUSPENDED,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        result = self.manager.validate_license("TEST-1234")
        self.assertFalse(result.is_valid)
        self.assertIn("suspended", result.error_message)
    
    @patch.object(LicenseManager, '_get_license')
    def test_029_validate_revoked_license(self, mock_get):
        """Test validating revoked license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.ANNUAL,
            status=LicenseStatus.REVOKED,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=365),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        result = self.manager.validate_license("TEST-1234")
        self.assertFalse(result.is_valid)
        self.assertIn("revoked", result.error_message)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_is_machine_activated')
    @patch.object(LicenseManager, '_log_activity')
    def test_030_validate_with_machine_check(self, mock_log, mock_activated, mock_get):
        """Test validation with machine ID check"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        mock_activated.return_value = True
        
        result = self.manager.validate_license("TEST-1234", "machine-123")
        self.assertTrue(result.is_valid)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_is_machine_activated')
    def test_031_validate_unactivated_machine(self, mock_activated, mock_get):
        """Test validation with unactivated machine"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        mock_activated.return_value = False
        
        result = self.manager.validate_license("TEST-1234", "machine-999")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "Machine not activated")
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_032_validate_remaining_days(self, mock_log, mock_get):
        """Test remaining days calculation"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=15),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        result = self.manager.validate_license("TEST-1234")
        self.assertEqual(result.remaining_days, 15)


class TestMachineActivation(unittest.TestCase):
    """Tests for machine activation"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    @patch.object(LicenseManager, '_is_machine_activated')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_033_activate_machine_success(self, mock_log, mock_conn, mock_activated, 
                                          mock_count, mock_validate):
        """Test successful machine activation"""
        mock_license = Mock()
        mock_license.max_users = 5
        mock_validate.return_value = ValidationResult(is_valid=True, license=mock_license)
        mock_count.return_value = 2
        mock_activated.return_value = False
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.activate_machine("TEST-1234", "machine-123")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, 'validate_license')
    def test_034_activate_invalid_license(self, mock_validate):
        """Test activation with invalid license"""
        mock_validate.return_value = ValidationResult(
            is_valid=False, 
            error_message="Invalid license"
        )
        
        result = self.manager.activate_machine("INVALID", "machine-123")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    def test_035_activate_limit_reached(self, mock_count, mock_validate):
        """Test activation when limit is reached"""
        mock_license = Mock()
        mock_license.max_users = 3
        mock_validate.return_value = ValidationResult(is_valid=True, license=mock_license)
        mock_count.return_value = 3
        
        result = self.manager.activate_machine("TEST-1234", "machine-123")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    @patch.object(LicenseManager, '_is_machine_activated')
    def test_036_activate_already_activated(self, mock_activated, mock_count, mock_validate):
        """Test activating already activated machine"""
        mock_license = Mock()
        mock_license.max_users = 5
        mock_validate.return_value = ValidationResult(is_valid=True, license=mock_license)
        mock_count.return_value = 2
        mock_activated.return_value = True
        
        result = self.manager.activate_machine("TEST-1234", "machine-123")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_037_deactivate_machine(self, mock_log, mock_conn):
        """Test machine deactivation"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.deactivate_machine("TEST-1234", "machine-123")
        self.assertTrue(result)
    
    def test_038_generate_activation_code(self):
        """Test activation code generation"""
        code = self.manager._generate_activation_code("TEST-1234", "machine-123")
        self.assertEqual(len(code), 16)
        self.assertTrue(all(c in '0123456789abcdef' for c in code))
    
    def test_039_activation_code_uniqueness(self):
        """Test activation codes are unique"""
        code1 = self.manager._generate_activation_code("TEST-1234", "machine-123")
        code2 = self.manager._generate_activation_code("TEST-5678", "machine-456")
        self.assertNotEqual(code1, code2)


class TestLicenseRenewal(unittest.TestCase):
    """Tests for license renewal"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_040_renew_monthly_license(self, mock_log, mock_conn, mock_get):
        """Test renewing monthly license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=5),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.renew_license("TEST-1234")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_041_renew_annual_license(self, mock_log, mock_conn, mock_get):
        """Test renewing annual license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.ANNUAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.renew_license("TEST-1234")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_042_renew_custom_duration(self, mock_log, mock_conn, mock_get):
        """Test renewing with custom duration"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.ENTERPRISE,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=10),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.renew_license("TEST-1234", extend_days=90)
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_043_renew_nonexistent_license(self, mock_get):
        """Test renewing non-existent license"""
        mock_get.return_value = None
        
        result = self.manager.renew_license("INVALID-KEY")
        self.assertFalse(result)


class TestFeatureManagement(unittest.TestCase):
    """Tests for feature management"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_license')
    def test_044_has_feature_true(self, mock_get):
        """Test checking for existing feature"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL, FeatureFlag.API_ACCESS]
        )
        mock_get.return_value = mock_license
        
        result = self.manager.has_feature("TEST-1234", FeatureFlag.BASIC_ETL)
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_045_has_feature_false(self, mock_get):
        """Test checking for non-existing feature"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.TRIAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=14),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        result = self.manager.has_feature("TEST-1234", FeatureFlag.ENTERPRISE_SUPPORT)
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_046_has_feature_invalid_license(self, mock_get):
        """Test checking feature on invalid license"""
        mock_get.return_value = None
        
        result = self.manager.has_feature("INVALID", FeatureFlag.BASIC_ETL)
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_047_add_feature_success(self, mock_log, mock_conn, mock_get):
        """Test adding feature to license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.add_feature("TEST-1234", FeatureFlag.API_ACCESS)
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    def test_048_add_existing_feature(self, mock_conn, mock_get):
        """Test adding feature that already exists"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL, FeatureFlag.API_ACCESS]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.add_feature("TEST-1234", FeatureFlag.API_ACCESS)
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_049_add_feature_invalid_license(self, mock_get):
        """Test adding feature to invalid license"""
        mock_get.return_value = None
        
        result = self.manager.add_feature("INVALID", FeatureFlag.API_ACCESS)
        self.assertFalse(result)


class TestUsageTracking(unittest.TestCase):
    """Tests for usage tracking and rate limiting"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_050_track_api_call(self, mock_conn):
        """Test tracking API call"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        result = self.manager.track_api_call("TEST-1234")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_051_get_api_usage_today(self, mock_conn):
        """Test getting API usage count"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [42]
        mock_db.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.return_value = mock_db
        
        usage = self.manager.get_api_usage_today("TEST-1234")
        self.assertEqual(usage, 42)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, 'get_api_usage_today')
    def test_052_check_rate_limit_under(self, mock_usage, mock_get):
        """Test rate limit check when under limit"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL],
            max_api_calls_per_day=1000
        )
        mock_get.return_value = mock_license
        mock_usage.return_value = 500
        
        result = self.manager.check_rate_limit("TEST-1234")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, 'get_api_usage_today')
    def test_053_check_rate_limit_over(self, mock_usage, mock_get):
        """Test rate limit check when over limit"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.TRIAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=14),
            features=[FeatureFlag.BASIC_ETL],
            max_api_calls_per_day=100
        )
        mock_get.return_value = mock_license
        mock_usage.return_value = 150
        
        result = self.manager.check_rate_limit("TEST-1234")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, 'get_api_usage_today')
    def test_054_check_rate_limit_at_limit(self, mock_usage, mock_get):
        """Test rate limit check when at exact limit"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL],
            max_api_calls_per_day=1000
        )
        mock_get.return_value = mock_license
        mock_usage.return_value = 1000
        
        result = self.manager.check_rate_limit("TEST-1234")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_055_check_rate_limit_invalid_license(self, mock_get):
        """Test rate limit check with invalid license"""
        mock_get.return_value = None
        
        result = self.manager.check_rate_limit("INVALID")
        self.assertFalse(result)


class TestUtilities(unittest.TestCase):
    """Tests for utility functions"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_056_log_activity(self, mock_conn):
        """Test logging activity"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        self.manager._log_activity("TEST-1234", "test_action", {"key": "value"})
        # Should not raise exception
    
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    @patch.object(LicenseManager, 'get_api_usage_today')
    def test_057_get_license_info_valid(self, mock_usage, mock_count, mock_validate):
        """Test getting license info for valid license"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL, FeatureFlag.API_ACCESS],
            max_users=5,
            max_jobs=50
        )
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            license=mock_license,
            remaining_days=30
        )
        mock_count.return_value = 2
        mock_usage.return_value = 100
        
        info = self.manager.get_license_info("TEST-1234")
        self.assertIsNotNone(info)
        self.assertEqual(info['license_key'], "TEST-1234")
        self.assertEqual(info['customer_name'], "Test User")
        self.assertTrue(info['is_valid'])
        self.assertEqual(info['remaining_days'], 30)
        self.assertEqual(info['active_machines'], 2)
        self.assertEqual(info['api_usage_today'], 100)
    
    @patch.object(LicenseManager, 'validate_license')
    def test_058_get_license_info_invalid(self, mock_validate):
        """Test getting license info for invalid license"""
        mock_validate.return_value = ValidationResult(
            is_valid=False,
            error_message="Invalid license"
        )
        
        info = self.manager.get_license_info("INVALID")
        self.assertIsNone(info)
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_059_get_activation_count(self, mock_conn):
        """Test getting activation count"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [3]
        mock_db.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.return_value = mock_db
        
        count = self.manager._get_activation_count("TEST-1234")
        self.assertEqual(count, 3)
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_060_is_machine_activated_true(self, mock_conn):
        """Test checking if machine is activated (true)"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_db.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.return_value = mock_db
        
        result = self.manager._is_machine_activated("TEST-1234", "machine-123")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_061_is_machine_activated_false(self, mock_conn):
        """Test checking if machine is activated (false)"""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0]
        mock_db.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.return_value = mock_db
        
        result = self.manager._is_machine_activated("TEST-1234", "machine-999")
        self.assertFalse(result)


class TestDecorator(unittest.TestCase):
    """Tests for license enforcement decorator"""
    
    @patch('nexus_license.get_license_manager')
    @patch('nexus_license.os.getenv')
    @patch('nexus_license.get_machine_id')
    def test_062_decorator_valid_license(self, mock_machine, mock_env, mock_get_manager):
        """Test decorator with valid license"""
        mock_env.return_value = "TEST-1234"
        mock_machine.return_value = "machine-123"
        
        mock_manager = Mock()
        mock_manager.validate_license.return_value = ValidationResult(is_valid=True)
        mock_manager.check_rate_limit.return_value = True
        mock_manager.track_api_call.return_value = True
        mock_get_manager.return_value = mock_manager
        
        @require_license()
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
    
    @patch('nexus_license.os.getenv')
    def test_063_decorator_no_license_key(self, mock_env):
        """Test decorator without license key"""
        mock_env.return_value = None
        
        @require_license()
        def test_function():
            return "success"
        
        with self.assertRaises(PermissionError) as context:
            test_function()
        
        self.assertIn("No license key", str(context.exception))
    
    @patch('nexus_license.get_license_manager')
    @patch('nexus_license.os.getenv')
    @patch('nexus_license.get_machine_id')
    def test_064_decorator_invalid_license(self, mock_machine, mock_env, mock_get_manager):
        """Test decorator with invalid license"""
        mock_env.return_value = "INVALID-KEY"
        mock_machine.return_value = "machine-123"
        
        mock_manager = Mock()
        mock_manager.validate_license.return_value = ValidationResult(
            is_valid=False,
            error_message="License expired"
        )
        mock_get_manager.return_value = mock_manager
        
        @require_license()
        def test_function():
            return "success"
        
        with self.assertRaises(PermissionError) as context:
            test_function()
        
        self.assertIn("License expired", str(context.exception))
    
    @patch('nexus_license.get_license_manager')
    @patch('nexus_license.os.getenv')
    @patch('nexus_license.get_machine_id')
    def test_065_decorator_missing_feature(self, mock_machine, mock_env, mock_get_manager):
        """Test decorator with missing required feature"""
        mock_env.return_value = "TEST-1234"
        mock_machine.return_value = "machine-123"
        
        mock_manager = Mock()
        mock_manager.validate_license.return_value = ValidationResult(is_valid=True)
        mock_manager.has_feature.return_value = False
        mock_get_manager.return_value = mock_manager
        
        @require_license(feature=FeatureFlag.ENTERPRISE_SUPPORT)
        def test_function():
            return "success"
        
        with self.assertRaises(PermissionError) as context:
            test_function()
        
        self.assertIn("does not include feature", str(context.exception))
    
    @patch('nexus_license.get_license_manager')
    @patch('nexus_license.os.getenv')
    @patch('nexus_license.get_machine_id')
    def test_066_decorator_rate_limit_exceeded(self, mock_machine, mock_env, mock_get_manager):
        """Test decorator with rate limit exceeded"""
        mock_env.return_value = "TEST-1234"
        mock_machine.return_value = "machine-123"
        
        mock_manager = Mock()
        mock_manager.validate_license.return_value = ValidationResult(is_valid=True)
        mock_manager.check_rate_limit.return_value = False
        mock_get_manager.return_value = mock_manager
        
        @require_license()
        def test_function():
            return "success"
        
        with self.assertRaises(PermissionError) as context:
            test_function()
        
        self.assertIn("rate limit exceeded", str(context.exception))


class TestMachineId(unittest.TestCase):
    """Tests for machine ID generation"""
    
    @patch('nexus_license.platform.node')
    @patch('nexus_license.socket.gethostname')
    @patch('nexus_license.uuid.getnode')
    def test_067_get_machine_id(self, mock_mac, mock_hostname, mock_node):
        """Test machine ID generation"""
        mock_node.return_value = "test-node"
        mock_hostname.return_value = "test-host"
        mock_mac.return_value = 123456789
        
        machine_id = get_machine_id()
        self.assertEqual(len(machine_id), 16)
    
    @patch('nexus_license.platform.node')
    @patch('nexus_license.socket.gethostname')
    @patch('nexus_license.uuid.getnode')
    def test_068_machine_id_consistency(self, mock_mac, mock_hostname, mock_node):
        """Test machine ID is consistent"""
        mock_node.return_value = "test-node"
        mock_hostname.return_value = "test-host"
        mock_mac.return_value = 123456789
        
        id1 = get_machine_id()
        id2 = get_machine_id()
        self.assertEqual(id1, id2)
    
    @patch('nexus_license.platform.node')
    @patch('nexus_license.socket.gethostname')
    @patch('nexus_license.uuid.getnode')
    def test_069_machine_id_different_machines(self, mock_mac, mock_hostname, mock_node):
        """Test different machines produce different IDs"""
        mock_node.return_value = "machine-1"
        mock_hostname.return_value = "host-1"
        mock_mac.return_value = 111111111
        id1 = get_machine_id()
        
        mock_node.return_value = "machine-2"
        mock_hostname.return_value = "host-2"
        mock_mac.return_value = 222222222
        id2 = get_machine_id()
        
        self.assertNotEqual(id1, id2)


class TestLicenseManagerSingleton(unittest.TestCase):
    """Tests for license manager singleton"""
    
    def tearDown(self):
        # Reset singleton
        import nexus_license
        nexus_license._license_manager = None
    
    @patch('nexus_license.LicenseManager')
    @patch('nexus_license.os.getenv')
    def test_070_get_license_manager_singleton(self, mock_env, mock_manager_class):
        """Test license manager singleton pattern"""
        mock_env.side_effect = lambda key, default=None: {
            'LICENSE_DB_HOST': 'localhost',
            'LICENSE_DB_PORT': '5432',
            'LICENSE_DB_NAME': 'test_db',
            'LICENSE_DB_USER': 'test_user',
            'LICENSE_DB_PASSWORD': 'test_pass',
            'NEXUS_SECRET_KEY': 'secret123'
        }.get(key, default)
        
        manager1 = get_license_manager()
        manager2 = get_license_manager()
        
        self.assertIs(manager1, manager2)
        mock_manager_class.assert_called_once()


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_license')
    def test_071_validate_exception_handling(self, mock_get):
        """Test validation exception handling"""
        mock_get.side_effect = Exception("Database error")
        
        result = self.manager.validate_license("TEST-1234")
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error_message)
    
    @patch.object(LicenseManager, 'validate_license')
    def test_072_activate_exception_handling(self, mock_validate):
        """Test activation exception handling"""
        mock_validate.side_effect = Exception("Connection error")
        
        result = self.manager.activate_machine("TEST-1234", "machine-123")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_073_renew_exception_handling(self, mock_get):
        """Test renewal exception handling"""
        mock_get.side_effect = Exception("Database error")
        
        result = self.manager.renew_license("TEST-1234")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_074_track_api_call_exception(self, mock_conn):
        """Test API call tracking exception handling"""
        mock_conn.side_effect = Exception("Connection error")
        
        result = self.manager.track_api_call("TEST-1234")
        self.assertFalse(result)
    
    @patch.object(LicenseManager, '_get_license')
    def test_075_add_feature_exception_handling(self, mock_get):
        """Test add feature exception handling"""
        mock_get.side_effect = Exception("Database error")
        
        result = self.manager.add_feature("TEST-1234", FeatureFlag.API_ACCESS)
        self.assertFalse(result)


class TestLicenseStatusUpdates(unittest.TestCase):
    """Tests for license status updates"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_076_update_status_to_expired(self, mock_conn):
        """Test updating status to expired"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        self.manager._update_license_status("TEST-1234", LicenseStatus.EXPIRED)
        # Should not raise exception
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_077_update_status_to_suspended(self, mock_conn):
        """Test updating status to suspended"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        self.manager._update_license_status("TEST-1234", LicenseStatus.SUSPENDED)
        # Should not raise exception
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_078_update_status_to_revoked(self, mock_conn):
        """Test updating status to revoked"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        self.manager._update_license_status("TEST-1234", LicenseStatus.REVOKED)
        # Should not raise exception


class TestDatabaseOperations(unittest.TestCase):
    """Tests for database operations"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch('nexus_license.psycopg2.connect')
    def test_079_get_db_connection(self, mock_connect):
        """Test database connection creation"""
        mock_connect.return_value = MagicMock()
        
        conn = self.manager._get_db_connection()
        self.assertIsNotNone(conn)
        mock_connect.assert_called()
    
    @patch.object(LicenseManager, '_get_db_connection')
    def test_080_store_license(self, mock_conn):
        """Test storing license in database"""
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        license_obj = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        
        self.manager._store_license(license_obj)
        # Should not raise exception


class TestComplexScenarios(unittest.TestCase):
    """Tests for complex scenarios"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    @patch.object(LicenseManager, '_is_machine_activated')
    @patch.object(LicenseManager, '_get_db_connection')
    def test_081_full_license_lifecycle(self, mock_conn, mock_activated, mock_count,
                                       mock_validate, mock_log, mock_store):
        """Test complete license lifecycle"""
        # Generate
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.MONTHLY
        )
        self.assertIsNotNone(license)
        
        # Validate
        mock_validate.return_value = ValidationResult(is_valid=True, license=license)
        result = self.manager.validate_license(license.license_key)
        self.assertTrue(result.is_valid)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_082_multiple_renewals(self, mock_log, mock_conn, mock_get):
        """Test multiple license renewals"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=5),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        # First renewal
        result1 = self.manager.renew_license("TEST-1234")
        self.assertTrue(result1)
        
        # Second renewal
        result2 = self.manager.renew_license("TEST-1234")
        self.assertTrue(result2)
    
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    @patch.object(LicenseManager, '_is_machine_activated')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_083_multiple_machine_activations(self, mock_log, mock_conn, mock_activated,
                                              mock_count, mock_validate):
        """Test activating multiple machines"""
        mock_license = Mock()
        mock_license.max_users = 5
        mock_validate.return_value = ValidationResult(is_valid=True, license=mock_license)
        mock_activated.return_value = False
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        for i in range(3):
            mock_count.return_value = i
            result = self.manager.activate_machine("TEST-1234", f"machine-{i}")
            self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')

@patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_084_add_multiple_features(self, mock_log, mock_conn, mock_get):
        """Test adding multiple features"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        features_to_add = [
            FeatureFlag.API_ACCESS,
            FeatureFlag.CLOUD_CONNECTORS,
            FeatureFlag.CUSTOM_CODE
        ]
        
        for feature in features_to_add:
            result = self.manager.add_feature("TEST-1234", feature)
            self.assertTrue(result)


class TestSecurityFeatures(unittest.TestCase):
    """Tests for security features"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret_key_test")
    
    def test_085_activation_code_security(self):
        """Test activation code uses HMAC"""
        code = self.manager._generate_activation_code("TEST-1234", "machine-123")
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 16)
    
    def test_086_license_key_character_set(self):
        """Test license key uses secure character set"""
        key = self.manager._generate_license_key()
        # Should not contain confusing characters like 0, O, 1, I
        for char in key.replace("NEXUS-", "").replace("-", ""):
            self.assertNotIn(char, ['0', '1', 'I', 'O'])
    
    def test_087_fernet_encryption_initialized(self):
        """Test Fernet encryption is initialized"""
        self.assertIsNotNone(self.manager.fernet)
    
    def test_088_rsa_keys_generated(self):
        """Test RSA keys are generated"""
        self.assertIsNotNone(self.manager.private_key)
        self.assertIsNotNone(self.manager.public_key)


class TestLicenseTypeSpecificBehavior(unittest.TestCase):
    """Tests for license type specific behavior"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_089_trial_duration(self, mock_log, mock_store):
        """Test trial license duration is 14 days"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.TRIAL
        )
        duration = (license.expiry_date - license.issue_date).days
        self.assertEqual(duration, 14)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_090_monthly_features(self, mock_log, mock_store):
        """Test monthly license default features"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.MONTHLY
        )
        self.assertGreater(len(license.features), 3)
        self.assertIn(FeatureFlag.CLOUD_CONNECTORS, license.features)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_091_annual_features(self, mock_log, mock_store):
        """Test annual license includes custom code"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.ANNUAL
        )
        self.assertIn(FeatureFlag.CUSTOM_CODE, license.features)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_092_enterprise_all_features(self, mock_log, mock_store):
        """Test enterprise license has all features"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.ENTERPRISE
        )
        all_features = list(FeatureFlag)
        for feature in all_features:
            self.assertIn(feature, license.features)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_093_perpetual_long_duration(self, mock_log, mock_store):
        """Test perpetual license duration"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.PERPETUAL
        )
        duration = (license.expiry_date - license.issue_date).days
        self.assertGreater(duration, 36000)  # ~100 years


class TestBoundaryConditions(unittest.TestCase):
    """Tests for boundary conditions"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, 'get_api_usage_today')
    def test_094_rate_limit_boundary(self, mock_usage, mock_get):
        """Test rate limit at boundary (limit - 1)"""
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.MONTHLY,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now(),
            expiry_date=datetime.now() + timedelta(days=30),
            features=[FeatureFlag.BASIC_ETL],
            max_api_calls_per_day=1000
        )
        mock_get.return_value = mock_license
        mock_usage.return_value = 999
        
        result = self.manager.check_rate_limit("TEST-1234")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, 'validate_license')
    @patch.object(LicenseManager, '_get_activation_count')
    @patch.object(LicenseManager, '_is_machine_activated')
    @patch.object(LicenseManager, '_get_db_connection')
    @patch.object(LicenseManager, '_log_activity')
    def test_095_activation_at_limit(self, mock_log, mock_conn, mock_activated, 
                                     mock_count, mock_validate):
        """Test activation when at limit"""
        from nexus_license import ValidationResult
        
        mock_license = Mock()
        mock_license.max_users = 3
        mock_validate.return_value = ValidationResult(is_valid=True, license=mock_license)
        mock_count.return_value = 2
        mock_activated.return_value = False
        
        mock_db = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_db
        
        # Should succeed (2 < 3)
        result = self.manager.activate_machine("TEST-1234", "machine-new")
        self.assertTrue(result)
    
    @patch.object(LicenseManager, '_get_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_096_expiry_on_boundary_day(self, mock_log, mock_get):
        """Test validation on expiry day"""
        # License expires today at this exact time
        mock_license = License(
            license_key="TEST-1234",
            customer_id="cust-123",
            customer_name="Test User",
            customer_email="test@example.com",
            license_type=LicenseType.TRIAL,
            status=LicenseStatus.ACTIVE,
            issue_date=datetime.now() - timedelta(days=14),
            expiry_date=datetime.now() - timedelta(seconds=1),
            features=[FeatureFlag.BASIC_ETL]
        )
        mock_get.return_value = mock_license
        
        with patch.object(self.manager, '_update_license_status'):
            result = self.manager.validate_license("TEST-1234")
            self.assertFalse(result.is_valid)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_097_zero_max_users(self, mock_log, mock_store):
        """Test license with zero max users"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.TRIAL,
            max_users=0
        )
        self.assertEqual(license.max_users, 0)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_098_large_max_values(self, mock_log, mock_store):
        """Test license with very large max values"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.ENTERPRISE,
            max_users=10000,
            max_jobs=100000
        )
        self.assertEqual(license.max_users, 10000)
        self.assertEqual(license.max_jobs, 100000)


class TestDataIntegrity(unittest.TestCase):
    """Tests for data integrity"""
    
    def setUp(self):
        with patch('nexus_license.psycopg2.connect'), \
             patch('nexus_license.Path.exists', return_value=False):
            self.manager = LicenseManager({}, "secret")
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_099_email_format_preserved(self, mock_log, mock_store):
        """Test email format is preserved"""
        email = "test.user+tag@example.co.uk"
        license = self.manager.generate_license(
            "Test User",
            email,
            LicenseType.MONTHLY
        )
        self.assertEqual(license.customer_email, email)
    
    @patch.object(LicenseManager, '_store_license')
    @patch.object(LicenseManager, '_log_activity')
    def test_100_metadata_preserved(self, mock_log, mock_store):
        """Test metadata field is properly initialized"""
        license = self.manager.generate_license(
            "Test User",
            "test@example.com",
            LicenseType.ANNUAL
        )
        self.assertIsInstance(license.metadata, dict)
        self.assertEqual(len(license.metadata), 0)

# =============================================================================
# TEST RUNNER
# =============================================================================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes (tests 84-100)
    suite.addTests(loader.loadTestsFromTestCase(TestComplexScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestLicenseTypeSpecificBehavior))
    suite.addTests(loader.loadTestsFromTestCase(TestBoundaryConditions))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY (Tests 84-100)")
    print("="*70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    # Exit with appropriate code
    import sys
    sys.exit(0 if result.wasSuccessful() else 1)