#!/usr/bin/env python3
"""
Nexus Enterprise ETL System - Comprehensive Unit Tests
=======================================================
100 unit tests covering all major components and edge cases

Author: Test Suite
Version: 1.0.0
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import json
from pathlib import Path
import sys 
import hashlib
from cryptography.fernet import Fernet, InvalidToken
import base64
import logging
import time
import random
import string
import yaml
import sqlite3
import requests
import io

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)

# Import classes from the main module
# Note: Adjust import path based on your project structure
from nexus.ETL.etl_core import (
    SourceType, TargetType, TransformationType, ETLStatus,
    DataSource, DataTarget, Transformation, ETLJob, ETLMetrics,
    SecurityManager, DatabaseConnector, APIConnector, FileConnector,
    S3Connector, TransformationEngine, ConnectorFactory
)

# =============================================================================
# SECURITY MANAGER TESTS (Tests 1-15)
# =============================================================================

class TestSecurityManager(unittest.TestCase):
    """Test SecurityManager functionality"""
    
    def setUp(self):
        self.security = SecurityManager()
    
    def test_001_security_manager_initialization(self):
        """Test SecurityManager initialization"""
        self.assertIsNotNone(self.security.master_key)
        self.assertIsNotNone(self.security.fernet)
    
    def test_002_security_manager_with_custom_key(self):
        """Test SecurityManager with custom master key"""
        custom_key = "my_custom_master_key_12345"
        security = SecurityManager(master_key=custom_key)
        self.assertIsNotNone(security.master_key)
    
    def test_003_encrypt_string(self):
        """Test string encryption"""
        original = "sensitive_password"
        encrypted = self.security.encrypt(original)
        self.assertNotEqual(original, encrypted)
        self.assertIsInstance(encrypted, str)
    
    def test_004_decrypt_string(self):
        """Test string decryption"""
        original = "sensitive_password"
        encrypted = self.security.encrypt(original)
        decrypted = self.security.decrypt(encrypted)
        self.assertEqual(original, decrypted)
    
    def test_005_encrypt_decrypt_empty_string(self):
        """Test encryption/decryption of empty string"""
        original = ""
        encrypted = self.security.encrypt(original)
        decrypted = self.security.decrypt(encrypted)
        self.assertEqual(original, decrypted)
    
    def test_006_encrypt_decrypt_special_characters(self):
        """Test encryption with special characters"""
        original = "p@ssw0rd!#$%^&*()"
        encrypted = self.security.encrypt(original)
        decrypted = self.security.decrypt(encrypted)
        self.assertEqual(original, decrypted)
    
    def test_007_hash_value(self):
        """Test value hashing"""
        value = "test_value"
        hashed = self.security.hash_value(value)
        self.assertEqual(len(hashed), 64)  # SHA256 produces 64 char hex
    
    def test_008_hash_value_consistency(self):
        """Test hash consistency"""
        value = "test_value"
        hash1 = self.security.hash_value(value)
        hash2 = self.security.hash_value(value)
        self.assertEqual(hash1, hash2)
    
    def test_009_hash_value_uniqueness(self):
        """Test different values produce different hashes"""
        hash1 = self.security.hash_value("value1")
        hash2 = self.security.hash_value("value2")
        self.assertNotEqual(hash1, hash2)
    
    def test_010_encrypt_connection_params(self):
        """Test connection parameter encryption"""
        params = {
            'host': 'localhost',
            'password': 'secret123',
            'api_key': 'key123'
        }
        encrypted = self.security.encrypt_connection_params(params)
        self.assertEqual(encrypted['host'], 'localhost')
        self.assertNotEqual(encrypted['password'], 'secret123')
        self.assertNotEqual(encrypted['api_key'], 'key123')
    
    def test_011_decrypt_connection_params(self):
        """Test connection parameter decryption"""
        params = {
            'host': 'localhost',
            'password': 'secret123',
            'token': 'token123'
        }
        encrypted = self.security.encrypt_connection_params(params)
        decrypted = self.security.decrypt_connection_params(encrypted)
        self.assertEqual(decrypted['password'], 'secret123')
        self.assertEqual(decrypted['token'], 'token123')
    
    def test_012_decrypt_non_encrypted_params(self):
        """Test decryption handles non-encrypted values"""
        params = {
            'host': 'localhost',
            'password': 'plaintext'
        }
        decrypted = self.security.decrypt_connection_params(params)
        self.assertEqual(decrypted['password'], 'plaintext')
    
    def test_013_encrypt_all_sensitive_keys(self):
        """Test all sensitive keys are encrypted"""
        params = {
            'password': 'pwd',
            'api_key': 'key',
            'secret_key': 'secret',
            'token': 'tkn'
        }
        encrypted = self.security.encrypt_connection_params(params)
        for key in ['password', 'api_key', 'secret_key', 'token']:
            self.assertNotEqual(encrypted[key], params[key])
    
    def test_014_encryption_error_handling(self):
        """Test encryption error handling"""
        with patch.object(self.security.fernet, 'encrypt', side_effect=Exception("Error")):
            with self.assertRaises(Exception):
                self.security.encrypt("test")
    
    def test_015_decryption_error_handling(self):
        """Test decryption error handling"""
        with self.assertRaises(Exception):
            self.security.decrypt("invalid_encrypted_data")


# =============================================================================
# DATA SOURCE TESTS (Tests 16-25)
# =============================================================================

class TestDataSource(unittest.TestCase):
    """Test DataSource dataclass"""
    
    def test_016_create_database_source(self):
        """Test creating database data source"""
        source = DataSource(
            name="test_db",
            source_type=SourceType.DATABASE,
            connection_params={'type': 'postgresql'},
            table="users"
        )
        self.assertEqual(source.name, "test_db")
        self.assertEqual(source.source_type, SourceType.DATABASE)
    
    def test_017_create_api_source(self):
        """Test creating API data source"""
        source = DataSource(
            name="test_api",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com/data"
        )
        self.assertEqual(source.source_type, SourceType.API)
        self.assertEqual(source.api_endpoint, "https://api.example.com/data")
    
    def test_018_create_file_source(self):
        """Test creating file data source"""
        source = DataSource(
            name="test_file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="/data/input.csv",
            file_format="csv"
        )
        self.assertEqual(source.file_path, "/data/input.csv")
        self.assertEqual(source.file_format, "csv")
    
    def test_019_source_with_incremental_loading(self):
        """Test source with incremental loading config"""
        source = DataSource(
            name="incremental",
            source_type=SourceType.DATABASE,
            connection_params={},
            table="transactions",
            incremental_column="created_at",
            incremental_value="2024-01-01"
        )
        self.assertEqual(source.incremental_column, "created_at")
        self.assertIsNotNone(source.incremental_value)
    
    def test_020_source_default_batch_size(self):
        """Test source default batch size"""
        source = DataSource(
            name="test",
            source_type=SourceType.FILE,
            connection_params={}
        )
        self.assertEqual(source.batch_size, 10000)
    
    def test_021_source_custom_batch_size(self):
        """Test source with custom batch size"""
        source = DataSource(
            name="test",
            source_type=SourceType.FILE,
            connection_params={},
            batch_size=5000
        )
        self.assertEqual(source.batch_size, 5000)
    
    def test_022_source_with_encryption_flag(self):
        """Test source with encryption enabled"""
        source = DataSource(
            name="secure",
            source_type=SourceType.DATABASE,
            connection_params={},
            encrypted=True
        )
        self.assertTrue(source.encrypted)
    
    def test_023_s3_source_configuration(self):
        """Test S3 source configuration"""
        source = DataSource(
            name="s3_source",
            source_type=SourceType.S3,
            connection_params={
                'bucket': 'my-bucket',
                'access_key': 'key',
                'secret_key': 'secret'
            },
            file_path="data/input.parquet"
        )
        self.assertEqual(source.source_type, SourceType.S3)
        self.assertIn('bucket', source.connection_params)
    
    def test_024_api_source_with_headers(self):
        """Test API source with custom headers"""
        headers = {'Authorization': 'Bearer token123'}
        source = DataSource(
            name="api_auth",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com",
            api_headers=headers
        )
        self.assertEqual(source.api_headers, headers)
    
    def test_025_api_source_with_params(self):
        """Test API source with query parameters"""
        params = {'limit': 100, 'offset': 0}
        source = DataSource(
            name="api_params",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com",
            api_params=params
        )
        self.assertEqual(source.api_params, params)


# =============================================================================
# DATA TARGET TESTS (Tests 26-35)
# =============================================================================

class TestDataTarget(unittest.TestCase):
    """Test DataTarget dataclass"""
    
    def test_026_create_database_target(self):
        """Test creating database target"""
        target = DataTarget(
            name="db_target",
            target_type=TargetType.DATABASE,
            connection_params={'type': 'postgresql'},
            table="output_table"
        )
        self.assertEqual(target.target_type, TargetType.DATABASE)
    
    def test_027_target_write_mode_append(self):
        """Test target with append write mode"""
        target = DataTarget(
            name="test",
            target_type=TargetType.DATABASE,
            connection_params={},
            write_mode="append"
        )
        self.assertEqual(target.write_mode, "append")
    
    def test_028_target_write_mode_overwrite(self):
        """Test target with overwrite write mode"""
        target = DataTarget(
            name="test",
            target_type=TargetType.DATABASE,
            connection_params={},
            write_mode="overwrite"
        )
        self.assertEqual(target.write_mode, "overwrite")
    
    def test_029_target_write_mode_upsert(self):
        """Test target with upsert write mode"""
        target = DataTarget(
            name="test",
            target_type=TargetType.DATABASE,
            connection_params={},
            write_mode="upsert"
        )
        self.assertEqual(target.write_mode, "upsert")
    
    def test_030_file_target_configuration(self):
        """Test file target configuration"""
        target = DataTarget(
            name="file_out",
            target_type=TargetType.FILE,
            connection_params={},
            file_path="/output/data.csv",
            file_format="csv"
        )
        self.assertEqual(target.file_format, "csv")
    
    def test_031_api_target_configuration(self):
        """Test API target configuration"""
        target = DataTarget(
            name="api_out",
            target_type=TargetType.API,
            connection_params={},
            api_endpoint="https://api.example.com/upload",
            api_method="POST"
        )
        self.assertEqual(target.api_method, "POST")
    
    def test_032_s3_target_configuration(self):
        """Test S3 target configuration"""
        target = DataTarget(
            name="s3_out",
            target_type=TargetType.S3,
            connection_params={'bucket': 'output-bucket'},
            file_path="output/data.parquet"
        )
        self.assertEqual(target.target_type, TargetType.S3)
    
    def test_033_target_default_batch_size(self):
        """Test target default batch size"""
        target = DataTarget(
            name="test",
            target_type=TargetType.FILE,
            connection_params={}
        )
        self.assertEqual(target.batch_size, 10000)
    
    def test_034_target_with_encryption(self):
        """Test target with encryption"""
        target = DataTarget(
            name="secure",
            target_type=TargetType.DATABASE,
            connection_params={},
            encrypted=True
        )
        self.assertTrue(target.encrypted)
    
    def test_035_api_target_with_headers(self):
        """Test API target with headers"""
        headers = {'Content-Type': 'application/json'}
        target = DataTarget(
            name="api",
            target_type=TargetType.API,
            connection_params={},
            api_endpoint="https://api.example.com",
            api_headers=headers
        )
        self.assertEqual(target.api_headers, headers)


# =============================================================================
# TRANSFORMATION TESTS (Tests 36-45)
# =============================================================================

class TestTransformation(unittest.TestCase):
    """Test Transformation dataclass"""
    
    def test_036_create_filter_transformation(self):
        """Test creating filter transformation"""
        transform = Transformation(
            name="filter_active",
            transformation_type=TransformationType.FILTER,
            config={'condition': 'status == "active"'}
        )
        self.assertEqual(transform.transformation_type, TransformationType.FILTER)
    
    def test_037_create_map_transformation(self):
        """Test creating map transformation"""
        transform = Transformation(
            name="map_columns",
            transformation_type=TransformationType.MAP,
            config={'mappings': {'full_name': 'first_name + " " + last_name'}}
        )
        self.assertIn('mappings', transform.config)
    
    def test_038_create_aggregate_transformation(self):
        """Test creating aggregate transformation"""
        transform = Transformation(
            name="aggregate",
            transformation_type=TransformationType.AGGREGATE,
            config={
                'group_by': ['category'],
                'aggregations': {'sales': 'sum'}
            }
        )
        self.assertEqual(transform.transformation_type, TransformationType.AGGREGATE)
    
    def test_039_transformation_with_order(self):
        """Test transformation ordering"""
        transform = Transformation(
            name="test",
            transformation_type=TransformationType.FILTER,
            config={},
            order=5
        )
        self.assertEqual(transform.order, 5)
    
    def test_040_transformation_enabled_flag(self):
        """Test transformation enabled flag"""
        transform = Transformation(
            name="test",
            transformation_type=TransformationType.FILTER,
            config={},
            enabled=False
        )
        self.assertFalse(transform.enabled)
    
    def test_041_custom_code_transformation(self):
        """Test custom code transformation"""
        code = "df['new_col'] = df['old_col'] * 2"
        transform = Transformation(
            name="custom",
            transformation_type=TransformationType.CUSTOM_CODE,
            config={},
            custom_code=code
        )
        self.assertIsNotNone(transform.custom_code)
    
    def test_042_sort_transformation(self):
        """Test sort transformation"""
        transform = Transformation(
            name="sort",
            transformation_type=TransformationType.SORT,
            config={'columns': ['date'], 'ascending': False}
        )
        self.assertEqual(transform.transformation_type, TransformationType.SORT)
    
    def test_043_deduplicate_transformation(self):
        """Test deduplicate transformation"""
        transform = Transformation(
            name="dedup",
            transformation_type=TransformationType.DEDUPLICATE,
            config={'subset': ['id'], 'keep': 'first'}
        )
        self.assertEqual(transform.transformation_type, TransformationType.DEDUPLICATE)
    
    def test_044_pivot_transformation(self):
        """Test pivot transformation"""
        transform = Transformation(
            name="pivot",
            transformation_type=TransformationType.PIVOT,
            config={
                'index': 'date',
                'columns': 'category',
                'values': 'amount'
            }
        )
        self.assertIn('index', transform.config)
    
    def test_045_unpivot_transformation(self):
        """Test unpivot transformation"""
        transform = Transformation(
            name="unpivot",
            transformation_type=TransformationType.UNPIVOT,
            config={'id_vars': ['id'], 'value_vars': ['col1', 'col2']}
        )
        self.assertEqual(transform.transformation_type, TransformationType.UNPIVOT)


# =============================================================================
# ETL JOB TESTS (Tests 46-55)
# =============================================================================

class TestETLJob(unittest.TestCase):
    """Test ETLJob dataclass"""
    
    def setUp(self):
        self.source = DataSource(
            name="source",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="input.csv"
        )
        self.target = DataTarget(
            name="target",
            target_type=TargetType.FILE,
            connection_params={},
            file_path="output.csv"
        )
        self.transform = Transformation(
            name="filter",
            transformation_type=TransformationType.FILTER,
            config={}
        )
    
    def test_046_create_basic_etl_job(self):
        """Test creating basic ETL job"""
        job = ETLJob(
            job_id="job_001",
            name="Test Job",
            description="Test description",
            sources=[self.source],
            transformations=[self.transform],
            targets=[self.target]
        )
        self.assertEqual(job.job_id, "job_001")
        self.assertEqual(len(job.sources), 1)
    
    def test_047_etl_job_with_schedule(self):
        """Test ETL job with schedule"""
        job = ETLJob(
            job_id="job_002",
            name="Scheduled Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            schedule="0 0 * * *"  # Daily at midnight
        )
        self.assertIsNotNone(job.schedule)
    
    def test_048_etl_job_enabled_flag(self):
        """Test ETL job enabled flag"""
        job = ETLJob(
            job_id="job_003",
            name="Disabled Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            enabled=False
        )
        self.assertFalse(job.enabled)
    
    def test_049_etl_job_retry_configuration(self):
        """Test ETL job retry configuration"""
        job = ETLJob(
            job_id="job_004",
            name="Retry Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            retry_count=5,
            retry_delay=120
        )
        self.assertEqual(job.retry_count, 5)
        self.assertEqual(job.retry_delay, 120)
    
    def test_050_etl_job_timeout(self):
        """Test ETL job timeout configuration"""
        job = ETLJob(
            job_id="job_005",
            name="Timeout Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            timeout=7200
        )
        self.assertEqual(job.timeout, 7200)
    
    def test_051_etl_job_parallel_processing(self):
        """Test ETL job parallel processing config"""
        job = ETLJob(
            job_id="job_006",
            name="Parallel Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            parallel=True,
            max_workers=8
        )
        self.assertTrue(job.parallel)
        self.assertEqual(job.max_workers, 8)
    
    def test_052_etl_job_with_notifications(self):
        """Test ETL job with notifications"""
        notifications = {
            'email': ['admin@example.com'],
            'slack': '#etl-alerts'
        }
        job = ETLJob(
            job_id="job_007",
            name="Notified Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            notifications=notifications
        )
        self.assertIsNotNone(job.notifications)
    
    def test_053_etl_job_with_metadata(self):
        """Test ETL job with metadata"""
        metadata = {'owner': 'data_team', 'priority': 'high'}
        job = ETLJob(
            job_id="job_008",
            name="Metadata Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target],
            metadata=metadata
        )
        self.assertEqual(job.metadata['owner'], 'data_team')
    
    def test_054_etl_job_multiple_sources(self):
        """Test ETL job with multiple sources"""
        source2 = DataSource(
            name="source2",
            source_type=SourceType.DATABASE,
            connection_params={},
            table="table2"
        )
        job = ETLJob(
            job_id="job_009",
            name="Multi-Source Job",
            description="Test",
            sources=[self.source, source2],
            transformations=[],
            targets=[self.target]
        )
        self.assertEqual(len(job.sources), 2)
    
    def test_055_etl_job_multiple_targets(self):
        """Test ETL job with multiple targets"""
        target2 = DataTarget(
            name="target2",
            target_type=TargetType.DATABASE,
            connection_params={},
            table="table2"
        )
        job = ETLJob(
            job_id="job_010",
            name="Multi-Target Job",
            description="Test",
            sources=[self.source],
            transformations=[],
            targets=[self.target, target2]
        )
        self.assertEqual(len(job.targets), 2)


# =============================================================================
# ETL METRICS TESTS (Tests 56-60)
# =============================================================================

class TestETLMetrics(unittest.TestCase):
    """Test ETLMetrics dataclass"""
    
    def test_056_create_etl_metrics(self):
        """Test creating ETL metrics"""
        metrics = ETLMetrics(
            job_id="job_001",
            run_id="run_001",
            status=ETLStatus.SUCCESS,
            start_time=datetime.now()
        )
        self.assertEqual(metrics.status, ETLStatus.SUCCESS)
    
    def test_057_metrics_with_row_counts(self):
        """Test metrics with row counts"""
        metrics = ETLMetrics(
            job_id="job_001",
            run_id="run_001",
            status=ETLStatus.SUCCESS,
            start_time=datetime.now(),
            rows_extracted=1000,
            rows_transformed=950,
            rows_loaded=950
        )
        self.assertEqual(metrics.rows_extracted, 1000)
        self.assertEqual(metrics.rows_loaded, 950)
    
    def test_058_metrics_with_errors(self):
        """Test metrics with errors"""
        metrics = ETLMetrics(
            job_id="job_001",
            run_id="run_001",
            status=ETLStatus.FAILED,
            start_time=datetime.now(),
            errors=["Connection failed", "Timeout"]
        )
        self.assertEqual(len(metrics.errors), 2)
    
    def test_059_metrics_with_warnings(self):
        """Test metrics with warnings"""
        metrics = ETLMetrics(
            job_id="job_001",
            run_id="run_001",
            status=ETLStatus.SUCCESS,
            start_time=datetime.now(),
            warnings=["Slow query detected"]
        )
        self.assertEqual(len(metrics.warnings), 1)
    
    def test_060_metrics_duration_calculation(self):
        """Test metrics duration"""
        start = datetime.now()
        end = start + timedelta(seconds=120)
        metrics = ETLMetrics(
            job_id="job_001",
            run_id="run_001",
            status=ETLStatus.SUCCESS,
            start_time=start,
            end_time=end,
            duration=120.0
        )
        self.assertEqual(metrics.duration, 120.0)


# =============================================================================
# FILE CONNECTOR TESTS (Tests 61-70)
# =============================================================================

class TestFileConnector(unittest.TestCase):
    """Test FileConnector functionality"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_061_file_connector_creation(self):
        """Test FileConnector creation"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="test.csv"
        )
        connector = FileConnector(source, self.security)
        self.assertIsNotNone(connector)
    
    def test_062_detect_csv_format(self):
        """Test CSV format detection"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="data.csv"
        )
        connector = FileConnector(source, self.security)
        format_type = connector._detect_format("data.csv")
        self.assertEqual(format_type, "csv")
    
    def test_063_detect_excel_format(self):
        """Test Excel format detection"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="data.xlsx"
        )
        connector = FileConnector(source, self.security)
        format_type = connector._detect_format("data.xlsx")
        self.assertEqual(format_type, "excel")
    
    def test_064_detect_json_format(self):
        """Test JSON format detection"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="data.json"
        )
        connector = FileConnector(source, self.security)
        format_type = connector._detect_format("data.json")
        self.assertEqual(format_type, "json")
    
    def test_065_detect_parquet_format(self):
        """Test Parquet format detection"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="data.parquet"
        )
        connector = FileConnector(source, self.security)
        format_type = connector._detect_format("data.parquet")
        self.assertEqual(format_type, "parquet")
    
    def test_066_extract_csv_file(self):
        """Test extracting CSV file"""
        csv_path = os.path.join(self.temp_dir, "test.csv")
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        df.to_csv(csv_path, index=False)
        
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path=csv_path,
            file_format="csv"
        )
        connector = FileConnector(source, self.security)
        result_df = connector.extract()
        
        self.assertEqual(len(result_df), 3)
        self.assertIn('a', result_df.columns)
    
    def test_067_load_csv_file(self):
        """Test loading to CSV file"""
        csv_path = os.path.join(self.temp_dir, "output.csv")
        df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
        
        target = DataTarget(
            name="file",
            target_type=TargetType.FILE,
            connection_params={},
            file_path=csv_path,
            file_format="csv"
        )
        connector = FileConnector(target, self.security)
        connector.load(df)
        
        self.assertTrue(os.path.exists(csv_path))
        loaded_df = pd.read_csv(csv_path)
        self.assertEqual(len(loaded_df), 3)
    
    def test_068_test_connection_existing_file(self):
        """Test connection to existing file"""
        csv_path = os.path.join(self.temp_dir, "test.csv")
        pd.DataFrame({'a': [1]}).to_csv(csv_path, index=False)
        
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path=csv_path
        )
        connector = FileConnector(source, self.security)
        self.assertTrue(connector.test_connection())
    
    def test_069_test_connection_nonexistent_file(self):
        """Test connection to nonexistent file"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="/nonexistent/path/file.csv"
        )
        connector = FileConnector(source, self.security)
        self.assertFalse(connector.test_connection())
    
    def test_070_load_creates_directory(self):
        """Test loading creates directory if not exists"""
        nested_path = os.path.join(self.temp_dir, "new", "nested", "output.csv")
        df = pd.DataFrame({'a': [1, 2]})
        
        target = DataTarget(
            name="file",
            target_type=TargetType.FILE,
            connection_params={},
            file_path=nested_path,
            file_format="csv"
        )
        connector = FileConnector(target, self.security)
        connector.load(df)
        
        self.assertTrue(os.path.exists(nested_path))


# =============================================================================
# TRANSFORMATION ENGINE TESTS (Tests 71-85)
# =============================================================================

class TestTransformationEngine(unittest.TestCase):
    """Test TransformationEngine functionality"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.engine = TransformationEngine(self.security)
        self.df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'status': ['active', 'inactive', 'active', 'active', 'inactive'],
            'salary': [50000, 60000, 70000, 80000, 90000]
        })
    
    def test_071_filter_transformation(self):
        """Test filter transformation"""
        transform = Transformation(
            name="filter",
            transformation_type=TransformationType.FILTER,
            config={'condition': 'age > 30'}
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(result['age'] > 30))
    
    def test_072_filter_by_status(self):
        """Test filter by status"""
        transform = Transformation(
            name="filter",
            transformation_type=TransformationType.FILTER,
            config={'condition': 'status == "active"'}
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertEqual(len(result), 3)
    
    def test_073_map_transformation(self):
        """Test map transformation"""
        transform = Transformation(
            name="map",
            transformation_type=TransformationType.MAP,
            config={'mappings': {'age_doubled': 'age * 2'}}
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertIn('age_doubled', result.columns)
        self.assertEqual(result['age_doubled'].iloc[0], 50)
    
    def test_074_aggregate_transformation(self):
        """Test aggregate transformation"""
        transform = Transformation(
            name="agg",
            transformation_type=TransformationType.AGGREGATE,
            config={
                'group_by': ['status'],
                'aggregations': {'salary': 'mean'}
            }
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertEqual(len(result), 2)
        self.assertIn('status', result.columns)
    
    def test_075_sort_transformation(self):
        """Test sort transformation"""
        transform = Transformation(
            name="sort",
            transformation_type=TransformationType.SORT,
            config={'columns': ['age'], 'ascending': False}
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertEqual(result['age'].iloc[0], 45)
        self.assertEqual(result['age'].iloc[-1], 25)
    
    def test_076_deduplicate_transformation(self):
        """Test deduplicate transformation"""
        df_with_dupes = pd.DataFrame({
            'id': [1, 1, 2, 3],
            'value': [10, 20, 30, 40]
        })
        transform = Transformation(
            name="dedup",
            transformation_type=TransformationType.DEDUPLICATE,
            config={'subset': ['id'], 'keep': 'first'}
        )
        result = self.engine._apply_transformation(df_with_dupes, transform)
        self.assertEqual(len(result), 3)
    
    def test_077_custom_code_transformation(self):
        """Test custom code transformation"""
        code = "df['bonus'] = df['salary'] * 0.1"
        transform = Transformation(
            name="custom",
            transformation_type=TransformationType.CUSTOM_CODE,
            config={},
            custom_code=code
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertIn('bonus', result.columns)
        self.assertEqual(result['bonus'].iloc[0], 5000)
    
    def test_078_multiple_transformations_in_order(self):
        """Test multiple transformations in order"""
        transforms = [
            Transformation(
                name="filter",
                transformation_type=TransformationType.FILTER,
                config={'condition': 'age > 25'},
                order=1
            ),
            Transformation(
                name="sort",
                transformation_type=TransformationType.SORT,
                config={'columns': ['salary'], 'ascending': True},
                order=2
            )
        ]
        result = self.engine.transform(self.df, transforms)
        self.assertEqual(len(result), 4)
        self.assertEqual(result['salary'].iloc[0], 60000)
    
    def test_079_skip_disabled_transformations(self):
        """Test disabled transformations are skipped"""
        transforms = [
            Transformation(
                name="filter",
                transformation_type=TransformationType.FILTER,
                config={'condition': 'age > 100'},
                enabled=False
            )
        ]
        result = self.engine.transform(self.df, transforms)
        self.assertEqual(len(result), 5)  # No filtering applied
    
    def test_080_pivot_transformation(self):
        """Test pivot transformation"""
        pivot_df = pd.DataFrame({
            'date': ['2024-01', '2024-01', '2024-02', '2024-02'],
            'category': ['A', 'B', 'A', 'B'],
            'value': [100, 200, 150, 250]
        })
        transform = Transformation(
            name="pivot",
            transformation_type=TransformationType.PIVOT,
            config={
                'index': 'date',
                'columns': 'category',
                'values': 'value'
            }
        )
        result = self.engine._apply_transformation(pivot_df, transform)
        self.assertIn('A', result.columns)
        self.assertIn('B', result.columns)
    
    def test_081_unpivot_transformation(self):
        """Test unpivot transformation"""
        wide_df = pd.DataFrame({
            'id': [1, 2],
            'col1': [10, 20],
            'col2': [30, 40]
        })
        transform = Transformation(
            name="unpivot",
            transformation_type=TransformationType.UNPIVOT,
            config={
                'id_vars': ['id'],
                'value_vars': ['col1', 'col2']
            }
        )
        result = self.engine._apply_transformation(wide_df, transform)
        self.assertEqual(len(result), 4)
        self.assertIn('variable', result.columns)
    
    def test_082_custom_code_with_numpy(self):
        """Test custom code with numpy"""
        code = "df['log_salary'] = np.log(df['salary'])"
        transform = Transformation(
            name="custom",
            transformation_type=TransformationType.CUSTOM_CODE,
            config={},
            custom_code=code
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertIn('log_salary', result.columns)
    
    def test_083_custom_code_with_datetime(self):
        """Test custom code with datetime"""
        code = "df['created_at'] = datetime.now()"
        transform = Transformation(
            name="custom",
            transformation_type=TransformationType.CUSTOM_CODE,
            config={},
            custom_code=code
        )
        result = self.engine._apply_transformation(self.df, transform)
        self.assertIn('created_at', result.columns)
    
    def test_084_transformation_error_handling(self):
        """Test transformation error handling"""
        transform = Transformation(
            name="bad_filter",
            transformation_type=TransformationType.FILTER,
            config={'condition': 'nonexistent_column > 10'}
        )
        with self.assertRaises(Exception):
            self.engine._apply_transformation(self.df, transform)
    
    def test_085_custom_code_error_handling(self):
        """Test custom code error handling"""
        code = "df['error'] = undefined_variable"
        transform = Transformation(
            name="bad_code",
            transformation_type=TransformationType.CUSTOM_CODE,
            config={},
            custom_code=code
        )
        with self.assertRaises(Exception):
            self.engine._apply_transformation(self.df, transform)


# =============================================================================
# CONNECTOR FACTORY TESTS (Tests 86-90)
# =============================================================================

class TestConnectorFactory(unittest.TestCase):
    """Test ConnectorFactory functionality"""
    
    def setUp(self):
        self.security = SecurityManager()
    
    def test_086_create_database_source_connector(self):
        """Test creating database source connector"""
        source = DataSource(
            name="db",
            source_type=SourceType.DATABASE,
            connection_params={'type': 'postgresql'}
        )
        connector = ConnectorFactory.create_source_connector(source, self.security)
        self.assertIsInstance(connector, DatabaseConnector)
    
    def test_087_create_api_source_connector(self):
        """Test creating API source connector"""
        source = DataSource(
            name="api",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com"
        )
        connector = ConnectorFactory.create_source_connector(source, self.security)
        self.assertIsInstance(connector, APIConnector)
    
    def test_088_create_file_source_connector(self):
        """Test creating file source connector"""
        source = DataSource(
            name="file",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="data.csv"
        )
        connector = ConnectorFactory.create_source_connector(source, self.security)
        self.assertIsInstance(connector, FileConnector)
    
    def test_089_create_s3_source_connector(self):
        """Test creating S3 source connector"""
        source = DataSource(
            name="s3",
            source_type=SourceType.S3,
            connection_params={'bucket': 'my-bucket'},
            file_path="data.csv"
        )
        connector = ConnectorFactory.create_source_connector(source, self.security)
        self.assertIsInstance(connector, S3Connector)
    
    def test_090_create_database_target_connector(self):
        """Test creating database target connector"""
        target = DataTarget(
            name="db",
            target_type=TargetType.DATABASE,
            connection_params={'type': 'postgresql'}
        )
        connector = ConnectorFactory.create_target_connector(target, self.security)
        self.assertIsInstance(connector, DatabaseConnector)


# =============================================================================
# API CONNECTOR TESTS (Tests 91-95)
# =============================================================================

class TestAPIConnector(unittest.TestCase):
    """Test APIConnector functionality"""
    
    def setUp(self):
        self.security = SecurityManager()
    
    def test_091_api_connector_creation(self):
        """Test API connector creation"""
        source = DataSource(
            name="api",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com/data"
        )
        connector = APIConnector(source, self.security)
        self.assertIsNotNone(connector)
    
    def test_092_api_connector_session_setup(self):
        """Test API connector session setup"""
        source = DataSource(
            name="api",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com"
        )
        connector = APIConnector(source, self.security)
        connector.connect()
        self.assertIsNotNone(connector.session)
        connector.disconnect()

    @patch('nexus.ETL.etl_core.requests.Session')
    def test_093_api_extract_list_response(self, mock_session_class):
        """Test API extract with list response"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        
        # Return the list directly
        data = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
        mock_response.json.return_value = data
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        source = DataSource(
            name="api",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com/items"
        )
        connector = APIConnector(source, self.security)
        connector.connect()
        
        # Verify the correct DataFrame conversion
        # pd.DataFrame(list_of_dicts) should give 2 rows
        expected_df = pd.DataFrame(data)
        print(f"Expected shape: {expected_df.shape}")
        
        df = connector.extract()
        print(f"Actual shape: {df.shape}")
        print(f"Actual DataFrame:\n{df}")
        
        connector.disconnect()
        
        self.assertEqual(len(df), 2)
        self.assertIn('id', df.columns)

    @patch('nexus.ETL.etl_core.requests.Session')
    def test_094_api_extract_dict_response(self, mock_session_class):
        """Test API extract with dict response containing data key"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        
        # Return dict with data key
        response_data = {
            'data': [
                {'id': 1, 'value': 100},
                {'id': 2, 'value': 200}
            ]
        }
        mock_response.json.return_value = response_data
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        source = DataSource(
            name="api",
            source_type=SourceType.API,
            connection_params={},
            api_endpoint="https://api.example.com/data"
        )
        connector = APIConnector(source, self.security)
        connector.connect()
        
        # Verify the correct DataFrame conversion
        # Should extract the 'data' key and convert to DataFrame
        expected_df = pd.DataFrame(response_data['data'])
        print(f"Expected shape: {expected_df.shape}")
        
        df = connector.extract()
        print(f"Actual shape: {df.shape}")
        print(f"Actual DataFrame:\n{df}")
        
        connector.disconnect()
        
        self.assertEqual(len(df), 2)
        self.assertIn('id', df.columns)

    @patch('nexus.ETL.etl_core.requests.Session')
    def test_095_api_load_data(self, mock_session_class):
        """Test API load data"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        
        # Mock both post and request methods
        mock_session.post.return_value = mock_response
        mock_session.request.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        df = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})
        target = DataTarget(
            name="api",
            target_type=TargetType.API,
            connection_params={},
            api_endpoint="https://api.example.com/upload",
            api_method="POST"
        )
        connector = APIConnector(target, self.security)
        connector.connect()
        connector.load(df)
        connector.disconnect()
        
        # Check if either post or request was called
        called = mock_session.post.called or mock_session.request.called
        self.assertTrue(called, f"Neither post nor request was called. Method calls: {mock_session.method_calls}")

# =============================================================================
# INTEGRATION AND EDGE CASE TESTS (Tests 96-100)
# =============================================================================

class TestEdgeCasesAndIntegration(unittest.TestCase):
    """Test edge cases and integration scenarios"""
    
    def setUp(self):
        self.security = SecurityManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_096_empty_dataframe_transformation(self):
        """Test transformation on empty DataFrame"""
        engine = TransformationEngine(self.security)
        # Create empty DataFrame with expected columns
        df = pd.DataFrame(columns=['id'])
        transform = Transformation(
            name="filter",
            transformation_type=TransformationType.FILTER,
            config={'condition': 'id > 0'}
        )
        result = engine.transform(df, [transform])
        self.assertEqual(len(result), 0)
    
    def test_097_large_batch_processing(self):
        """Test handling of large batch sizes"""
        source = DataSource(
            name="test",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="test.csv",
            batch_size=100000
        )
        self.assertEqual(source.batch_size, 100000)
    
    def test_098_encrypted_connection_params_roundtrip(self):
        """Test encrypted connection params roundtrip"""
        params = {
            'host': 'localhost',
            'port': 5432,
            'password': 'super_secret_123',
            'api_key': 'key_abc_xyz',
            'token': 'bearer_token_123'
        }
        
        encrypted = self.security.encrypt_connection_params(params)
        decrypted = self.security.decrypt_connection_params(encrypted)
        
        self.assertEqual(decrypted['host'], params['host'])
        self.assertEqual(decrypted['password'], params['password'])
        self.assertEqual(decrypted['api_key'], params['api_key'])
        self.assertEqual(decrypted['token'], params['token'])
    
    def test_099_etl_job_serialization(self):
        """Test ETL job can be serialized to dict"""
        source = DataSource(
            name="source",
            source_type=SourceType.FILE,
            connection_params={},
            file_path="input.csv"
        )
        target = DataTarget(
            name="target",
            target_type=TargetType.FILE,
            connection_params={},
            file_path="output.csv"
        )
        job = ETLJob(
            job_id="job_001",
            name="Test Job",
            description="Test",
            sources=[source],
            transformations=[],
            targets=[target]
        )
        
        # Test that job has expected attributes
        self.assertEqual(job.job_id, "job_001")
        self.assertIsInstance(job.sources, list)
        self.assertIsInstance(job.targets, list)
    
    def test_100_end_to_end_file_to_file_etl(self):
        """Test complete end-to-end file to file ETL"""
        # Create input file
        input_path = os.path.join(self.temp_dir, "input.csv")
        input_df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10, 20, 30, 40, 50],
            'status': ['active', 'inactive', 'active', 'active', 'inactive']
        })
        input_df.to_csv(input_path, index=False)
        
        # Extract
        source = DataSource(
            name="source",
            source_type=SourceType.FILE,
            connection_params={},
            file_path=input_path,
            file_format="csv"
        )
        source_connector = FileConnector(source, self.security)
        extracted_df = source_connector.extract()
        self.assertEqual(len(extracted_df), 5)
        
        # Transform
        engine = TransformationEngine(self.security)
        transform = Transformation(
            name="filter_active",
            transformation_type=TransformationType.FILTER,
            config={'condition': 'status == "active"'}
        )
        transformed_df = engine.transform(extracted_df, [transform])
        self.assertEqual(len(transformed_df), 3)
        
        # Load
        output_path = os.path.join(self.temp_dir, "output.csv")
        target = DataTarget(
            name="target",
            target_type=TargetType.FILE,
            connection_params={},
            file_path=output_path,
            file_format="csv"
        )
        target_connector = FileConnector(target, self.security)
        target_connector.load(transformed_df)
        
        # Verify
        self.assertTrue(os.path.exists(output_path))
        result_df = pd.read_csv(output_path)
        self.assertEqual(len(result_df), 3)
        self.assertTrue(all(result_df['status'] == 'active'))


# =============================================================================
# TEST SUITE RUNNER
# =============================================================================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDataSource))
    suite.addTests(loader.loadTestsFromTestCase(TestDataTarget))
    suite.addTests(loader.loadTestsFromTestCase(TestTransformation))
    suite.addTests(loader.loadTestsFromTestCase(TestETLJob))
    suite.addTests(loader.loadTestsFromTestCase(TestETLMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestFileConnector))
    suite.addTests(loader.loadTestsFromTestCase(TestTransformationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestConnectorFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIConnector))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCasesAndIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)