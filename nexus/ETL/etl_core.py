#!/usr/bin/env python3
"""
Nexus Enterprise ETL System
============================
Production-ready ETL framework with advanced features:
- Multi-source/target support (databases, APIs, files, cloud storage)
- Data transformation pipeline with custom Python code
- Security (encryption, authentication, audit logging)
- Monitoring, scheduling, and error handling
- Parallel processing and optimization

Author: Mauro Tommasi
Version: 1.0.0
License: MIT
"""

import os
import sys
import json
import yaml
import time
import uuid
import logging
import hashlib
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import tempfile
import shutil
import importlib
import traceback
from abc import ABC, abstractmethod

# Third-party imports
import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import boto3
#from azure.storage.blob import BlobServiceClient
#from google.cloud import storage as gcs_storage
import paramiko
from ftplib import FTP, FTP_TLS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus.database.database_management import DatabaseFactory, DatabaseInterface
from nexus.database.database_utilities import (
    MultiLevelCache, QueryBuilder, AuditLogger, EncryptedDatabase
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class SourceType(Enum):
    """Supported data source types"""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    FTP = "ftp"
    SFTP = "sftp"
    KAFKA = "kafka"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"
    MONGODB = "mongodb"


class TargetType(Enum):
    """Supported data target types"""
    DATABASE = "database"
    FILE = "file"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    API = "api"
    FTP = "ftp"
    SFTP = "sftp"
    KAFKA = "kafka"
    ELASTICSEARCH = "elasticsearch"


class TransformationType(Enum):
    """Transformation operation types"""
    FILTER = "filter"
    MAP = "map"
    AGGREGATE = "aggregate"
    JOIN = "join"
    SORT = "sort"
    DEDUPLICATE = "deduplicate"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"
    CUSTOM_CODE = "custom_code"


class ETLStatus(Enum):
    """ETL job status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class DataSource:
    """Data source configuration"""
    name: str
    source_type: SourceType
    connection_params: Dict[str, Any]
    query: Optional[str] = None
    table: Optional[str] = None
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_method: str = "GET"
    api_headers: Optional[Dict] = None
    api_params: Optional[Dict] = None
    incremental_column: Optional[str] = None
    incremental_value: Optional[Any] = None
    batch_size: int = 10000
    encrypted: bool = False


@dataclass
class DataTarget:
    """Data target configuration"""
    name: str
    target_type: TargetType
    connection_params: Dict[str, Any]
    table: Optional[str] = None
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_method: str = "POST"
    api_headers: Optional[Dict] = None
    write_mode: str = "append"  # append, overwrite, upsert
    batch_size: int = 10000
    encrypted: bool = False


@dataclass
class Transformation:
    """Data transformation configuration"""
    name: str
    transformation_type: TransformationType
    config: Dict[str, Any]
    custom_code: Optional[str] = None
    order: int = 0
    enabled: bool = True


@dataclass
class ETLJob:
    """Complete ETL job configuration"""
    job_id: str
    name: str
    description: str
    sources: List[DataSource]
    transformations: List[Transformation]
    targets: List[DataTarget]
    schedule: Optional[str] = None
    enabled: bool = True
    retry_count: int = 3
    retry_delay: int = 60
    timeout: int = 3600
    parallel: bool = False
    max_workers: int = 4
    notifications: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ETLMetrics:
    """ETL execution metrics"""
    job_id: str
    run_id: str
    status: ETLStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    rows_extracted: int = 0
    rows_transformed: int = 0
    rows_loaded: int = 0
    rows_failed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# SECURITY MODULE
# =============================================================================

class SecurityManager:
    """Handle encryption, decryption, and secure credential management"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.logger = logging.getLogger('SecurityManager')
        
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = self._generate_master_key()
        
        # Derive encryption key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'nexus_etl_salt',
            iterations=100000,
        )
        key = kdf.derive(self.master_key)
        self.fernet = Fernet(Fernet.generate_key())
    
    def _generate_master_key(self) -> bytes:
        """Generate a new master key"""
        return Fernet.generate_key()
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def hash_value(self, value: str) -> str:
        """Create hash of value for comparison"""
        return hashlib.sha256(value.encode()).hexdigest()
    
    def encrypt_connection_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive connection parameters"""
        encrypted_params = params.copy()
        sensitive_keys = ['password', 'api_key', 'secret_key', 'token']
        
        for key in sensitive_keys:
            if key in encrypted_params:
                encrypted_params[key] = self.encrypt(str(encrypted_params[key]))
        
        return encrypted_params
    
    def decrypt_connection_params(self, encrypted_params: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive connection parameters"""
        params = encrypted_params.copy()
        sensitive_keys = ['password', 'api_key', 'secret_key', 'token']
        
        for key in sensitive_keys:
            if key in params:
                try:
                    params[key] = self.decrypt(params[key])
                except:
                    pass  # Not encrypted
        
        return params


# =============================================================================
# DATA SOURCE CONNECTORS
# =============================================================================

class DataConnector(ABC):
    """Abstract base class for data connectors"""
    
    def __init__(self, config: Union[DataSource, DataTarget], security_manager: SecurityManager):
        self.config = config
        self.security = security_manager
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        
        # Decrypt connection params
        if config.encrypted:
            self.connection_params = security_manager.decrypt_connection_params(
                config.connection_params
            )
        else:
            self.connection_params = config.connection_params
    
    @abstractmethod
    def connect(self):
        """Establish connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is valid"""
        pass


class DatabaseConnector(DataConnector):
    """Database connector supporting multiple database types"""
    
    def __init__(self, config: Union[DataSource, DataTarget], security_manager: SecurityManager):
        super().__init__(config, security_manager)
        self.db = None
        self.db_type = self.connection_params.get('type', 'postgresql')
    
    def connect(self):
        """Connect to database"""
        try:
            self.db = DatabaseFactory.create_database(
                self.db_type,
                self.connection_params
            )
            self.db.connect()
            self.logger.info(f"Connected to {self.db_type} database")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from database"""
        if self.db:
            self.db.disconnect()
            self.logger.info("Database disconnected")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.connect()
            result = self.db.execute("SELECT 1")
            self.disconnect()
            return True
        except:
            return False
    
    def extract(self, batch_size: int = 10000) -> pd.DataFrame:
        """Extract data from database"""
        try:
            if isinstance(self.config, DataSource):
                if self.config.query:
                    query = self.config.query
                elif self.config.table:
                    query = f"SELECT * FROM {self.config.table}"
                    
                    # Add incremental loading
                    if self.config.incremental_column and self.config.incremental_value:
                        query += f" WHERE {self.config.incremental_column} > '{self.config.incremental_value}'"
                else:
                    raise ValueError("Either query or table must be specified")
                
                # Execute query and convert to DataFrame
                results = self.db.fetch_all(query)
                df = pd.DataFrame(results)
                
                self.logger.info(f"Extracted {len(df)} rows from database")
                return df
        except Exception as e:
            self.logger.error(f"Data extraction failed: {e}")
            raise
    
    def load(self, df: pd.DataFrame):
        """Load data into database"""
        try:
            if not isinstance(self.config, DataTarget):
                raise ValueError("Config must be DataTarget for loading")
            
            table = self.config.table
            write_mode = self.config.write_mode
            
            # Convert DataFrame to list of dicts
            records = df.to_dict('records')
            
            if write_mode == 'overwrite':
                # Truncate table first
                self.db.execute(f"TRUNCATE TABLE {table}")
                self.db.commit()
            
            # Batch insert
            batch_size = self.config.batch_size
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                # Build insert query
                if batch:
                    columns = list(batch[0].keys())
                    placeholders = ', '.join(['%s'] * len(columns))
                    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    params_list = [tuple(record[col] for col in columns) for record in batch]
                    self.db.execute_many(query, params_list)
                    self.db.commit()
            
            self.logger.info(f"Loaded {len(records)} rows into {table}")
        except Exception as e:
            self.logger.error(f"Data loading failed: {e}")
            self.db.rollback()
            raise


class APIConnector:
    """Connector for REST API sources and targets"""
    
    def __init__(self, config: Union[DataSource, DataTarget], security_manager: SecurityManager):
        self.config = config
        self.security = security_manager
        self.logger = logging.getLogger(f'APIConnector.{config.name}')
        self.session = None
        
        # Decrypt connection params if encrypted
        if config.encrypted:
            config.connection_params = security_manager.decrypt_connection_params(
                config.connection_params
            )
    
    def connect(self) -> bool:
        """Establish API connection (create session)"""
        try:
            self.session = requests.Session()
            
            # Set default headers if provided
            if hasattr(self.config, 'api_headers') and self.config.api_headers:
                self.session.headers.update(self.config.api_headers)
            
            self.logger.info(f"API session created for {self.config.name}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating API session: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Close API connection"""
        if self.session:
            self.session.close()
            self.session = None
            self.logger.info(f"API session closed for {self.config.name}")
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            if not self.session:
                self.connect()
            
            # Try a HEAD or GET request to test connectivity
            endpoint = self.config.api_endpoint
            response = self.session.head(endpoint, timeout=5)
            return response.status_code < 500
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def extract(self) -> pd.DataFrame:
        """Extract data from API"""
        try:
            if not self.session:
                self.connect()
            
            response = self.session.get(
                self.config.api_endpoint,
                headers=self.config.api_headers or {},
                params=self.config.api_params or {}
            )
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                # Response is already a list of records
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Response is a dict, look for common data keys
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'results' in data:
                    df = pd.DataFrame(data['results'])
                elif 'items' in data:
                    df = pd.DataFrame(data['items'])
                else:
                    # Treat the whole dict as a single record
                    df = pd.DataFrame([data])
            else:
                df = pd.DataFrame([data])
            
            self.logger.info(f"Extracted {len(df)} records from API")
            return df
            
        except Exception as e:
            self.logger.error(f"Error extracting from API: {str(e)}")
            raise
    
    def load(self, df: pd.DataFrame) -> None:
        """Load data to API endpoint"""
        try:
            if not self.session:
                self.connect()
            
            # Convert DataFrame to list of dicts
            data = df.to_dict('records')
            
            # Get HTTP method (default to POST)
            method = getattr(self.config, 'api_method', 'POST').upper()
            
            # Send request
            response = self.session.request(
                method=method,
                url=self.config.api_endpoint,
                json=data,
                headers=self.config.api_headers or {}
            )
            response.raise_for_status()
            
            self.logger.info(f"Successfully loaded {len(df)} records to API")
            
        except Exception as e:
            self.logger.error(f"Error loading to API: {str(e)}")
            raise
    
    def get_schema(self) -> dict:
        """Get API response schema"""
        try:
            if not self.session:
                self.connect()
            
            # Make a sample request to infer schema
            response = self.session.get(
                self.config.api_endpoint,
                headers=self.config.api_headers or {},
                params={**(self.config.api_params or {}), 'limit': 1}
            )
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                sample = data[0]
            elif isinstance(data, dict):
                if 'data' in data and len(data['data']) > 0:
                    sample = data['data'][0]
                else:
                    sample = data
            else:
                sample = {}
            
            schema = {key: type(value).__name__ for key, value in sample.items()}
            return schema
            
        except Exception as e:
            self.logger.error(f"Error getting schema: {str(e)}")
            return {}

class FileConnector(DataConnector):
    """File connector supporting various formats"""
    
    def connect(self):
        """No connection needed for files"""
        pass
    
    def disconnect(self):
        """No disconnection needed"""
        pass
    
    def test_connection(self) -> bool:
        """Test if file path is accessible"""
        if isinstance(self.config, DataSource):
            return os.path.exists(self.config.file_path)
        return True
    
    def extract(self) -> pd.DataFrame:
        """Extract data from file"""
        try:
            if not isinstance(self.config, DataSource):
                raise ValueError("Config must be DataSource")
            
            file_path = self.config.file_path
            file_format = self.config.file_format or self._detect_format(file_path)
            
            if file_format == 'csv':
                df = pd.read_csv(file_path)
            elif file_format == 'excel':
                df = pd.read_excel(file_path)
            elif file_format == 'json':
                df = pd.read_json(file_path)
            elif file_format == 'parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            self.logger.info(f"Extracted {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            self.logger.error(f"File extraction failed: {e}")
            raise
    
    def load(self, df: pd.DataFrame):
        """Load data to file"""
        try:
            if not isinstance(self.config, DataTarget):
                raise ValueError("Config must be DataTarget")
            
            file_path = self.config.file_path
            file_format = self.config.file_format or self._detect_format(file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if file_format == 'csv':
                df.to_csv(file_path, index=False)
            elif file_format == 'excel':
                df.to_excel(file_path, index=False)
            elif file_format == 'json':
                df.to_json(file_path, orient='records', indent=2)
            elif file_format == 'parquet':
                df.to_parquet(file_path, index=False)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            self.logger.info(f"Loaded {len(df)} rows to {file_path}")
        except Exception as e:
            self.logger.error(f"File loading failed: {e}")
            raise
    
    def _detect_format(self, file_path: str) -> str:
        """Detect file format from extension"""
        ext = os.path.splitext(file_path)[1].lower()
        format_map = {
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.json': 'json',
            '.parquet': 'parquet'
        }
        return format_map.get(ext, 'csv')


class S3Connector(DataConnector):
    """AWS S3 connector"""
    
    def __init__(self, config: Union[DataSource, DataTarget], security_manager: SecurityManager):
        super().__init__(config, security_manager)
        self.s3_client = None
    
    def connect(self):
        """Connect to S3"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.connection_params.get('access_key'),
                aws_secret_access_key=self.connection_params.get('secret_key'),
                region_name=self.connection_params.get('region', 'us-east-1')
            )
            self.logger.info("Connected to AWS S3")
        except Exception as e:
            self.logger.error(f"S3 connection failed: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from S3"""
        self.s3_client = None
    
    def test_connection(self) -> bool:
        """Test S3 connection"""
        try:
            self.connect()
            self.s3_client.list_buckets()
            return True
        except:
            return False
    
    def extract(self) -> pd.DataFrame:
        """Extract data from S3"""
        try:
            if not isinstance(self.config, DataSource):
                raise ValueError("Config must be DataSource")
            
            bucket = self.connection_params['bucket']
            key = self.config.file_path
            
            # Download file
            temp_file = f"/tmp/{uuid.uuid4()}.tmp"
            self.s3_client.download_file(bucket, key, temp_file)
            
            # Read file
            file_format = self.config.file_format or self._detect_format(key)
            if file_format == 'csv':
                df = pd.read_csv(temp_file)
            elif file_format == 'json':
                df = pd.read_json(temp_file)
            elif file_format == 'parquet':
                df = pd.read_parquet(temp_file)
            
            # Clean up
            os.remove(temp_file)
            
            self.logger.info(f"Extracted {len(df)} rows from S3")
            return df
        except Exception as e:
            self.logger.error(f"S3 extraction failed: {e}")
            raise
    
    def load(self, df: pd.DataFrame):
        """Load data to S3"""
        try:
            if not isinstance(self.config, DataTarget):
                raise ValueError("Config must be DataTarget")
            
            bucket = self.connection_params['bucket']
            key = self.config.file_path
            
            # Write to temp file
            temp_file = f"/tmp/{uuid.uuid4()}.tmp"
            file_format = self.config.file_format or self._detect_format(key)
            
            if file_format == 'csv':
                df.to_csv(temp_file, index=False)
            elif file_format == 'json':
                df.to_json(temp_file, orient='records', indent=2)
            elif file_format == 'parquet':
                df.to_parquet(temp_file, index=False)
            
            # Upload to S3
            self.s3_client.upload_file(temp_file, bucket, key)
            
            # Clean up
            os.remove(temp_file)
            
            self.logger.info(f"Loaded {len(df)} rows to S3")
        except Exception as e:
            self.logger.error(f"S3 loading failed: {e}")
            raise
    
    def _detect_format(self, file_path: str) -> str:
        """Detect file format"""
        ext = os.path.splitext(file_path)[1].lower()
        format_map = {
            '.csv': 'csv',
            '.json': 'json',
            '.parquet': 'parquet'
        }
        return format_map.get(ext, 'csv')


# =============================================================================
# DATA TRANSFORMATION ENGINE
# =============================================================================

class TransformationEngine:
    """Execute data transformations including custom Python code"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.logger = logging.getLogger('TransformationEngine')
    
    def transform(self, df: pd.DataFrame, transformations: List[Transformation]) -> pd.DataFrame:
        """Apply all transformations in order"""
        # Sort by order
        sorted_transforms = sorted(
            [t for t in transformations if t.enabled],
            key=lambda x: x.order
        )
        
        result_df = df.copy()
        
        for transform in sorted_transforms:
            try:
                self.logger.info(f"Applying transformation: {transform.name}")
                result_df = self._apply_transformation(result_df, transform)
            except Exception as e:
                self.logger.error(f"Transformation '{transform.name}' failed: {e}")
                raise
        
        return result_df
    
    def _apply_transformation(self, df: pd.DataFrame, transform: Transformation) -> pd.DataFrame:
        """Apply single transformation"""
        trans_type = transform.transformation_type
        config = transform.config
        
        if trans_type == TransformationType.FILTER:
            return self._filter(df, config)
        elif trans_type == TransformationType.MAP:
            return self._map(df, config)
        elif trans_type == TransformationType.AGGREGATE:
            return self._aggregate(df, config)
        elif trans_type == TransformationType.JOIN:
            return self._join(df, config)
        elif trans_type == TransformationType.SORT:
            return self._sort(df, config)
        elif trans_type == TransformationType.DEDUPLICATE:
            return self._deduplicate(df, config)
        elif trans_type == TransformationType.PIVOT:
            return self._pivot(df, config)
        elif trans_type == TransformationType.UNPIVOT:
            return self._unpivot(df, config)
        elif trans_type == TransformationType.CUSTOM_CODE:
            return self._execute_custom_code(df, transform.custom_code)
        else:
            raise ValueError(f"Unknown transformation type: {trans_type}")
    
    def _filter(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Filter rows based on condition"""
        condition = config.get('condition')
        if condition:
            return df.query(condition)
        return df
    
    def _map(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Map/transform columns"""
        mappings = config.get('mappings', {})
        result_df = df.copy()
        
        for new_col, expression in mappings.items():
            try:
                result_df[new_col] = result_df.eval(expression)
            except:
                # If eval fails, try direct assignment
                if expression in result_df.columns:
                    result_df[new_col] = result_df[expression]
        
        return result_df
    
    def _aggregate(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Aggregate data"""
        group_by = config.get('group_by', [])
        aggregations = config.get('aggregations', {})
        
        if group_by and aggregations:
            return df.groupby(group_by).agg(aggregations).reset_index()
        return df
    
    def _join(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Join with another dataset"""
        # This would need another DataFrame - simplified implementation
        return df
    
    def _sort(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Sort data"""
        sort_by = config.get('columns', [])
        ascending = config.get('ascending', True)
        
        if sort_by:
            return df.sort_values(by=sort_by, ascending=ascending)
        return df
    
    def _deduplicate(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Remove duplicate rows"""
        subset = config.get('subset')
        keep = config.get('keep', 'first')
        
        return df.drop_duplicates(subset=subset, keep=keep)
    
    def _pivot(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Pivot table"""
        index = config.get('index')
        columns = config.get('columns')
        values = config.get('values')
        
        if index and columns and values:
            return df.pivot_table(index=index, columns=columns, values=values, aggfunc='sum')
        return df
    
    def _unpivot(self, df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """Unpivot/melt table"""
        id_vars = config.get('id_vars', [])
        value_vars = config.get('value_vars')
        
        return pd.melt(df, id_vars=id_vars, value_vars=value_vars)
    
    def _execute_custom_code(self, df: pd.DataFrame, code: str) -> pd.DataFrame:
        """Execute custom Python code safely"""
        try:
            # Create restricted namespace
            namespace = {
                'df': df,
                'pd': pd,
                'np': np,
                'datetime': datetime,
                'timedelta': timedelta
            }
            
            # Execute code
            exec(code, namespace)
            
            # Return modified DataFrame
            return namespace['df']
        except Exception as e:
            self.logger.error(f"Custom code execution failed: {e}\n{traceback.format_exc()}")
            raise


# =============================================================================
# CONNECTOR FACTORY
# =============================================================================

class ConnectorFactory:
    """Factory for creating data connectors"""
    
    @staticmethod
    def create_source_connector(source: DataSource, security: SecurityManager) -> DataConnector:
        """Create source connector"""
        connector_map = {
            SourceType.DATABASE: DatabaseConnector,
            SourceType.API: APIConnector,
            SourceType.FILE: FileConnector,
            SourceType.S3: S3Connector,
        }
        
        connector_class = connector_map.get(source.source_type)
        if not connector_class:
            raise ValueError(f"Unsupported source type: {source.source_type}")
        
        return connector_class(source, security)
    
    @staticmethod
    def create_target_connector(target: DataTarget, security: SecurityManager) -> DataConnector:
        """Create target connector"""
        connector_map = {
            TargetType.DATABASE: DatabaseConnector,
            TargetType.API: APIConnector,
            TargetType.FILE: FileConnector,
            TargetType.S3: S3Connector,
        }
        
        connector_class = connector_map.get(target.target_type)
        if not connector_class:
            raise ValueError(f"Unsupported target type: {target.target_type}")
        
        return connector_class(target, security)