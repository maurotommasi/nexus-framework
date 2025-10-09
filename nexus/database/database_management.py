"""
Enterprise-grade database abstraction layer with connection pooling, monitoring, and advanced features.
Supports: PostgreSQL, MySQL, SQLite, MongoDB, Oracle, SQL Server, Redis, Cassandra, Elasticsearch, MariaDB
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import logging
import time
import threading
from queue import Queue, Empty
import json
from functools import wraps


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class IsolationLevel(Enum):
    """Transaction isolation levels"""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class DatabaseMetrics:
    """Tracks database performance metrics"""
    
    def __init__(self):
        self.query_count = 0
        self.total_query_time = 0.0
        self.slow_queries = []
        self.errors = []
        self.connection_count = 0
        self.active_connections = 0
        self._lock = threading.Lock()
    
    def record_query(self, query: str, execution_time: float, success: bool = True):
        """Record query execution metrics"""
        with self._lock:
            self.query_count += 1
            self.total_query_time += execution_time
            
            if execution_time > 1.0:  # Slow query threshold: 1 second
                self.slow_queries.append({
                    'query': query[:200],
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Keep only last 100 slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries.pop(0)
            
            if not success:
                self.errors.append({
                    'query': query[:200],
                    'timestamp': datetime.now().isoformat()
                })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._lock:
            avg_time = self.total_query_time / self.query_count if self.query_count > 0 else 0
            return {
                'total_queries': self.query_count,
                'average_query_time': round(avg_time, 4),
                'slow_queries_count': len(self.slow_queries),
                'errors_count': len(self.errors),
                'active_connections': self.active_connections,
                'total_connections': self.connection_count
            }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.query_count = 0
            self.total_query_time = 0.0
            self.slow_queries.clear()
            self.errors.clear()


def measure_time(func):
    """Decorator to measure query execution time"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        success = True
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise e
        finally:
            execution_time = time.time() - start_time
            query = args[0] if args else "Unknown"
            if hasattr(self, 'metrics'):
                self.metrics.record_query(str(query), execution_time, success)
    return wrapper


class ConnectionPool:
    """Thread-safe connection pool"""
    
    def __init__(self, db_class, connection_params: Dict[str, Any], 
                 min_size: int = 2, max_size: int = 10, 
                 max_idle_time: int = 300, logger: Optional[logging.Logger] = None):
        self.db_class = db_class
        self.connection_params = connection_params
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.pool = Queue(maxsize=max_size)
        self.active_connections = 0
        self._lock = threading.Lock()
        self.logger = logger or logging.getLogger(__name__)
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize minimum connections"""
        for _ in range(self.min_size):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)
    
    def _create_connection(self):
        """Create a new database connection"""
        try:
            db = self.db_class(self.connection_params)
            db.connect()
            with self._lock:
                self.active_connections += 1
            self.logger.info(f"Created new connection. Active: {self.active_connections}")
            return db
        except Exception as e:
            self.logger.error(f"Failed to create connection: {e}")
            return None
    
    def get_connection(self, timeout: int = 30):
        """Get a connection from the pool"""
        try:
            conn = self.pool.get(timeout=timeout)
            return conn
        except Empty:
            # Pool is empty, try to create new connection
            with self._lock:
                if self.active_connections < self.max_size:
                    conn = self._create_connection()
                    if conn:
                        return conn
            
            self.logger.warning("Connection pool exhausted, waiting for available connection")
            return self.pool.get(timeout=timeout)
    
    def release_connection(self, conn):
        """Return a connection to the pool"""
        if conn:
            try:
                self.pool.put(conn, timeout=5)
            except Exception as e:
                self.logger.error(f"Failed to return connection to pool: {e}")
                conn.disconnect()
                with self._lock:
                    self.active_connections -= 1
    
    def close_all(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.disconnect()
                with self._lock:
                    self.active_connections -= 1
            except Empty:
                break
        
        self.logger.info("All connections closed")
    
    def get_stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        return {
            'active_connections': self.active_connections,
            'available_connections': self.pool.qsize(),
            'max_connections': self.max_size
        }


class DatabaseInterface(ABC):
    """Abstract base class for database operations with enterprise features"""
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.connection = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.metrics = DatabaseMetrics()
        self._transaction_depth = 0
        self._isolation_level = None
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection"""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query and return results"""
        pass
    
    @abstractmethod
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute a query multiple times with different parameters"""
        pass
    
    @abstractmethod
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch a single row"""
        pass
    
    @abstractmethod
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Fetch all rows"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit current transaction"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback current transaction"""
        pass
    
    def is_connected(self) -> bool:
        """Check if connection is alive"""
        try:
            return self.connection is not None
        except:
            return False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to the database"""
        try:
            self.disconnect()
            self.connect()
            self.logger.info("Successfully reconnected to database")
            return True
        except Exception as e:
            self.logger.error(f"Reconnection failed: {e}")
            return False
    
    def set_isolation_level(self, level: IsolationLevel):
        """Set transaction isolation level"""
        self._isolation_level = level
    
    @contextmanager
    def transaction(self, isolation_level: Optional[IsolationLevel] = None):
        """Context manager for transactions with nested support"""
        self._transaction_depth += 1
        is_outer = self._transaction_depth == 1
        
        if is_outer and isolation_level:
            self.set_isolation_level(isolation_level)
        
        try:
            yield self
            if is_outer:
                self.commit()
                self.logger.debug("Transaction committed")
        except Exception as e:
            if is_outer:
                self.rollback()
                self.logger.error(f"Transaction rolled back: {e}")
            raise e
        finally:
            self._transaction_depth -= 1
    
    def execute_with_retry(self, query: str, params: Optional[tuple] = None, 
                          max_retries: int = 3, retry_delay: float = 1.0) -> Any:
        """Execute query with automatic retry on failure"""
        for attempt in range(max_retries):
            try:
                return self.execute(query, params)
            except Exception as e:
                self.logger.warning(f"Query failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    if not self.is_connected():
                        self.reconnect()
                else:
                    raise
    
    def batch_execute(self, queries: List[tuple], batch_size: int = 1000) -> int:
        """Execute multiple queries in batches"""
        total_affected = 0
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            with self.transaction():
                for query, params in batch:
                    affected = self.execute(query, params)
                    total_affected += affected if affected else 0
        return total_affected
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.get_stats()
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics.reset()


class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL database implementation with enterprise features"""
    
    def connect(self) -> None:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from psycopg2 import pool
        
        self.connection = psycopg2.connect(
            host=self.connection_params.get('host', 'localhost'),
            port=self.connection_params.get('port', 5432),
            database=self.connection_params['database'],
            user=self.connection_params['user'],
            password=self.connection_params['password'],
            cursor_factory=RealDictCursor,
            connect_timeout=self.connection_params.get('timeout', 10)
        )
        self.connection.autocommit = False
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("PostgreSQL connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
            self.logger.info("PostgreSQL connection closed")
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        with self.connection.cursor() as cursor:
            cursor.executemany(query, params_list)
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def commit(self) -> None:
        self.connection.commit()
    
    def rollback(self) -> None:
        self.connection.rollback()
    
    def set_isolation_level(self, level: IsolationLevel):
        """Set PostgreSQL isolation level"""
        import psycopg2.extensions
        isolation_map = {
            IsolationLevel.READ_UNCOMMITTED: psycopg2.extensions.ISOLATION_LEVEL_READ_UNCOMMITTED,
            IsolationLevel.READ_COMMITTED: psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
            IsolationLevel.REPEATABLE_READ: psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ,
            IsolationLevel.SERIALIZABLE: psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE
        }
        self.connection.set_isolation_level(isolation_map[level])
    
    def vacuum_analyze(self, table: Optional[str] = None):
        """Run VACUUM ANALYZE for optimization"""
        old_autocommit = self.connection.autocommit
        self.connection.autocommit = True
        try:
            query = f"VACUUM ANALYZE {table}" if table else "VACUUM ANALYZE"
            with self.connection.cursor() as cursor:
                cursor.execute(query)
            self.logger.info(f"VACUUM ANALYZE completed for {table or 'all tables'}")
        finally:
            self.connection.autocommit = old_autocommit


class MySQLDatabase(DatabaseInterface):
    """MySQL database implementation with enterprise features"""
    
    def connect(self) -> None:
        import mysql.connector
        self.connection = mysql.connector.connect(
            host=self.connection_params.get('host', 'localhost'),
            port=self.connection_params.get('port', 3306),
            database=self.connection_params['database'],
            user=self.connection_params['user'],
            password=self.connection_params['password'],
            autocommit=False,
            pool_size=self.connection_params.get('pool_size', 5),
            pool_name=self.connection_params.get('pool_name', 'mypool'),
            connect_timeout=self.connection_params.get('timeout', 10)
        )
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("MySQL connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
            self.logger.info("MySQL connection closed")
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        cursor.close()
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def commit(self) -> None:
        self.connection.commit()
    
    def rollback(self) -> None:
        self.connection.rollback()
    
    def is_connected(self) -> bool:
        """Check if MySQL connection is alive"""
        try:
            self.connection.ping(reconnect=False)
            return True
        except:
            return False


class SQLiteDatabase(DatabaseInterface):
    """SQLite database implementation with enterprise features"""
    
    def connect(self) -> None:
        import sqlite3
        self.connection = sqlite3.connect(
            self.connection_params['database'],
            timeout=self.connection_params.get('timeout', 10),
            check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("SQLite connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
            self.logger.info("SQLite connection closed")
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        cursor.close()
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows]
    
    def commit(self) -> None:
        self.connection.commit()
    
    def rollback(self) -> None:
        self.connection.rollback()


class MongoDBDatabase(DatabaseInterface):
    """MongoDB database implementation with enterprise features"""
    
    def connect(self) -> None:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        
        uri = self.connection_params.get('uri', 'mongodb://localhost:27017')
        self.client = MongoClient(
            uri,
            maxPoolSize=self.connection_params.get('pool_size', 10),
            minPoolSize=self.connection_params.get('min_pool_size', 2),
            serverSelectionTimeoutMS=self.connection_params.get('timeout', 10000)
        )
        
        # Verify connection
        try:
            self.client.admin.command('ismaster')
        except ConnectionFailure:
            raise Exception("Failed to connect to MongoDB")
        
        self.connection = self.client[self.connection_params['database']]
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("MongoDB connection established")
    
    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.metrics.active_connections -= 1
            self.logger.info("MongoDB connection closed")
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        raise NotImplementedError("Use insert_one, update_one, delete_one methods for MongoDB")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        raise NotImplementedError("Use insert_many, update_many for MongoDB")
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        collection = self.connection[query]
        return collection.find_one(params or {})
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        collection = self.connection[query]
        return list(collection.find(params or {}))
    
    @measure_time
    def insert_one(self, collection_name: str, document: Dict) -> str:
        """Insert a single document"""
        collection = self.connection[collection_name]
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    @measure_time
    def insert_many(self, collection_name: str, documents: List[Dict]) -> List[str]:
        """Insert multiple documents"""
        collection = self.connection[collection_name]
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    @measure_time
    def update_one(self, collection_name: str, filter_dict: Dict, update_dict: Dict) -> int:
        """Update a single document"""
        collection = self.connection[collection_name]
        result = collection.update_one(filter_dict, {'$set': update_dict})
        return result.modified_count
    
    @measure_time
    def delete_one(self, collection_name: str, filter_dict: Dict) -> int:
        """Delete a single document"""
        collection = self.connection[collection_name]
        result = collection.delete_one(filter_dict)
        return result.deleted_count
    
    def commit(self) -> None:
        pass
    
    def rollback(self) -> None:
        pass
    
    def create_index(self, collection_name: str, keys: List[tuple], unique: bool = False):
        """Create an index on collection"""
        collection = self.connection[collection_name]
        collection.create_index(keys, unique=unique)
        self.logger.info(f"Index created on {collection_name}")


class OracleDatabase(DatabaseInterface):
    """Oracle database implementation"""
    
    def connect(self) -> None:
        import cx_Oracle
        dsn = cx_Oracle.makedsn(
            self.connection_params.get('host', 'localhost'),
            self.connection_params.get('port', 1521),
            service_name=self.connection_params['service_name']
        )
        self.connection = cx_Oracle.connect(
            user=self.connection_params['user'],
            password=self.connection_params['password'],
            dsn=dsn
        )
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("Oracle connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        cursor.close()
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, row)) if row else None
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or {})
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def commit(self) -> None:
        self.connection.commit()
    
    def rollback(self) -> None:
        self.connection.rollback()


class SQLServerDatabase(DatabaseInterface):
    """Microsoft SQL Server database implementation"""
    
    def connect(self) -> None:
        import pyodbc
        connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.connection_params.get('host', 'localhost')};"
            f"DATABASE={self.connection_params['database']};"
            f"UID={self.connection_params['user']};"
            f"PWD={self.connection_params['password']}"
        )
        self.connection = pyodbc.connect(connection_string)
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("SQL Server connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        cursor.close()
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        cursor.close()
        return dict(zip(columns, row)) if row else None
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return [dict(zip(columns, row)) for row in rows]
    
    def commit(self) -> None:
        self.connection.commit()
    
    def rollback(self) -> None:
        self.connection.rollback()


class RedisDatabase(DatabaseInterface):
    """Redis database implementation with enterprise features"""
    
    def connect(self) -> None:
        import redis
        self.connection = redis.Redis(
            host=self.connection_params.get('host', 'localhost'),
            port=self.connection_params.get('port', 6379),
            db=self.connection_params.get('db', 0),
            password=self.connection_params.get('password'),
            decode_responses=True,
            max_connections=self.connection_params.get('pool_size', 10),
            socket_timeout=self.connection_params.get('timeout', 10)
        )
        self.connection.ping()  # Test connection
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("Redis connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        return self.connection.execute_command(query, *params if params else [])
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        pipeline = self.connection.pipeline()
        for params in params_list:
            pipeline.execute_command(query, *params)
        pipeline.execute()
    
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        value = self.connection.get(query)
        return {'key': query, 'value': value} if value else None
    
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        keys = self.connection.keys(query)
        return [{'key': k, 'value': self.connection.get(k)} for k in keys]
    
    @measure_time
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        return self.connection.set(key, value, ex=ex)
    
    @measure_time
    def get(self, key: str) -> Optional[str]:
        return self.connection.get(key)
    
    @measure_time
    def delete(self, *keys: str) -> int:
        return self.connection.delete(*keys)
    
    def commit(self) -> None:
        pass
    
    def rollback(self) -> None:
        pass


class CassandraDatabase(DatabaseInterface):
    """Apache Cassandra database implementation"""
    
    def connect(self) -> None:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
        
        auth_provider = None
        if 'user' in self.connection_params:
            auth_provider = PlainTextAuthProvider(
                username=self.connection_params['user'],
                password=self.connection_params['password']
            )
        
        self.cluster = Cluster(
            [self.connection_params.get('host', 'localhost')],
            port=self.connection_params.get('port', 9042),
            auth_provider=auth_provider
        )
        self.connection = self.cluster.connect(self.connection_params.get('keyspace'))
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("Cassandra connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.shutdown()
        if self.cluster:
            self.cluster.shutdown()
            self.metrics.active_connections -= 1
    
    @measure_time
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        return self.connection.execute(query, params)
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        prepared = self.connection.prepare(query)
        for params in params_list:
            self.connection.execute(prepared, params)
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        result = self.connection.execute(query, params)
        row = result.one()
        return dict(row._asdict()) if row else None
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        result = self.connection.execute(query, params)
        return [dict(row._asdict()) for row in result]
    
    def commit(self) -> None:
        pass
    
    def rollback(self) -> None:
        pass


class ElasticsearchDatabase(DatabaseInterface):
    """Elasticsearch database implementation with enterprise features"""
    
    def connect(self) -> None:
        from elasticsearch import Elasticsearch
        self.connection = Elasticsearch(
            [self.connection_params.get('host', 'localhost')],
            http_auth=(
                self.connection_params.get('user'),
                self.connection_params.get('password')
            ) if 'user' in self.connection_params else None,
            timeout=self.connection_params.get('timeout', 10)
        )
        
        # Verify connection
        if not self.connection.ping():
            raise Exception("Failed to connect to Elasticsearch")
        
        self.metrics.connection_count += 1
        self.metrics.active_connections += 1
        self.logger.info("Elasticsearch connection established")
    
    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.metrics.active_connections -= 1
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        raise NotImplementedError("Use search, index, update, delete methods for Elasticsearch")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        raise NotImplementedError("Use bulk operations for Elasticsearch")
    
    @measure_time
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        result = self.connection.get(index=query, id=params)
        return result['_source'] if result else None
    
    @measure_time
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        result = self.connection.search(index=query, body=params or {"query": {"match_all": {}}})
        return [hit['_source'] for hit in result['hits']['hits']]
    
    @measure_time
    def index(self, index_name: str, document: Dict, doc_id: Optional[str] = None) -> Dict:
        """Index a document"""
        return self.connection.index(index=index_name, body=document, id=doc_id)
    
    @measure_time
    def search(self, index_name: str, query_body: Dict) -> List[Dict]:
        """Search documents"""
        result = self.connection.search(index=index_name, body=query_body)
        return [hit['_source'] for hit in result['hits']['hits']]
    
    @measure_time
    def update(self, index_name: str, doc_id: str, update_body: Dict) -> Dict:
        """Update a document"""
        return self.connection.update(index=index_name, id=doc_id, body={"doc": update_body})
    
    @measure_time
    def delete(self, index_name: str, doc_id: str) -> Dict:
        """Delete a document"""
        return self.connection.delete(index=index_name, id=doc_id)
    
    def commit(self) -> None:
        pass
    
    def rollback(self) -> None:
        pass


class MariaDBDatabase(MySQLDatabase):
    """MariaDB database implementation (inherits from MySQL)"""
    pass


class DatabaseManager:
    """
    Enterprise database manager with connection pooling, monitoring, and failover support
    """
    
    def __init__(self, db_type: str, connection_params: Dict[str, Any],
                 use_pool: bool = True, pool_config: Optional[Dict[str, int]] = None):
        self.db_type = db_type.lower()
        self.connection_params = connection_params
        self.use_pool = use_pool
        self.pool = None
        self.logger = logging.getLogger(f"DatabaseManager-{db_type}")
        
        # Get database class
        self.db_class = self._get_db_class()
        
        # Initialize connection pool if enabled
        if use_pool:
            pool_config = pool_config or {}
            self.pool = ConnectionPool(
                self.db_class,
                connection_params,
                min_size=pool_config.get('min_size', 2),
                max_size=pool_config.get('max_size', 10),
                max_idle_time=pool_config.get('max_idle_time', 300),
                logger=self.logger
            )
            self.logger.info(f"Connection pool initialized for {db_type}")
    
    def _get_db_class(self):
        """Get the appropriate database class"""
        databases = {
            'postgresql': PostgreSQLDatabase,
            'mysql': MySQLDatabase,
            'sqlite': SQLiteDatabase,
            'mongodb': MongoDBDatabase,
            'oracle': OracleDatabase,
            'sqlserver': SQLServerDatabase,
            'redis': RedisDatabase,
            'cassandra': CassandraDatabase,
            'elasticsearch': ElasticsearchDatabase,
            'mariadb': MariaDBDatabase
        }
        
        db_class = databases.get(self.db_type)
        if not db_class:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        return db_class
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (from pool or new)"""
        if self.use_pool and self.pool:
            conn = self.pool.get_connection()
            try:
                yield conn
            finally:
                self.pool.release_connection(conn)
        else:
            conn = self.db_class(self.connection_params)
            conn.connect()
            try:
                yield conn
            finally:
                conn.disconnect()
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     fetch: str = 'none') -> Any:
        """
        Execute a query with automatic connection management
        
        Args:
            query: SQL query or operation
            params: Query parameters
            fetch: 'none', 'one', or 'all'
        """
        with self.get_connection() as conn:
            if fetch == 'one':
                return conn.fetch_one(query, params)
            elif fetch == 'all':
                return conn.fetch_all(query, params)
            else:
                return conn.execute(query, params)
    
    def execute_transaction(self, operations: List[tuple], 
                          isolation_level: Optional[IsolationLevel] = None) -> bool:
        """
        Execute multiple operations in a transaction
        
        Args:
            operations: List of (query, params) tuples
            isolation_level: Transaction isolation level
        """
        try:
            with self.get_connection() as conn:
                with conn.transaction(isolation_level):
                    for query, params in operations:
                        conn.execute(query, params)
            return True
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity"""
        try:
            with self.get_connection() as conn:
                is_connected = conn.is_connected()
                metrics = conn.get_metrics()
                
                health_status = {
                    'status': 'healthy' if is_connected else 'unhealthy',
                    'database_type': self.db_type,
                    'connected': is_connected,
                    'metrics': metrics,
                    'timestamp': datetime.now().isoformat()
                }
                
                if self.pool:
                    health_status['pool_stats'] = self.pool.get_stats()
                
                return health_status
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database_type': self.db_type,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics from all connections"""
        if self.pool:
            return {
                'pool_stats': self.pool.get_stats(),
                'database_type': self.db_type
            }
        return {'database_type': self.db_type}
    
    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.close_all()
        self.logger.info("Database manager closed")


class DatabaseFactory:
    """Factory class for creating database instances and managers"""
    
    _instances = {}
    _lock = threading.Lock()
    
    @classmethod
    def create_database(cls, db_type: str, connection_params: Dict[str, Any]) -> DatabaseInterface:
        """
        Create a database instance (Singleton pattern support)
        
        Args:
            db_type: Type of database
            connection_params: Connection parameters
        """
        databases = {
            'postgresql': PostgreSQLDatabase,
            'mysql': MySQLDatabase,
            'sqlite': SQLiteDatabase,
            'mongodb': MongoDBDatabase,
            'oracle': OracleDatabase,
            'sqlserver': SQLServerDatabase,
            'redis': RedisDatabase,
            'cassandra': CassandraDatabase,
            'elasticsearch': ElasticsearchDatabase,
            'mariadb': MariaDBDatabase
        }
        
        db_class = databases.get(db_type.lower())
        if not db_class:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return db_class(connection_params)
    
    @classmethod
    def create_manager(cls, db_type: str, connection_params: Dict[str, Any],
                      use_pool: bool = True, pool_config: Optional[Dict[str, int]] = None,
                      singleton: bool = False) -> DatabaseManager:
        """
        Create a database manager
        
        Args:
            db_type: Type of database
            connection_params: Connection parameters
            use_pool: Enable connection pooling
            pool_config: Pool configuration
            singleton: Use singleton pattern (one instance per database)
        """
        if singleton:
            key = f"{db_type}_{connection_params.get('database', 'default')}"
            with cls._lock:
                if key not in cls._instances:
                    cls._instances[key] = DatabaseManager(
                        db_type, connection_params, use_pool, pool_config
                    )
                return cls._instances[key]
        
        return DatabaseManager(db_type, connection_params, use_pool, pool_config)
    
    @classmethod
    def close_all(cls):
        """Close all singleton instances"""
        with cls._lock:
            for manager in cls._instances.values():
                manager.close()
            cls._instances.clear()


# Utility functions for common database operations

def bulk_insert(db: DatabaseInterface, table: str, records: List[Dict], 
                batch_size: int = 1000) -> int:
    """
    Bulk insert records into a table
    
    Args:
        db: Database instance
        table: Table name
        records: List of record dictionaries
        batch_size: Number of records per batch
    """
    if not records:
        return 0
    
    columns = list(records[0].keys())
    placeholders = ', '.join(['%s'] * len(columns))
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    
    total_inserted = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        params_list = [tuple(record[col] for col in columns) for record in batch]
        
        with db.transaction():
            db.execute_many(query, params_list)
            total_inserted += len(batch)
    
    return total_inserted


def export_to_json(db: DatabaseInterface, query: str, 
                   params: Optional[tuple] = None, 
                   output_file: str = 'export.json') -> int:
    """
    Export query results to JSON file
    
    Args:
        db: Database instance
        query: SQL query
        params: Query parameters
        output_file: Output file path
    """
    results = db.fetch_all(query, params)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return len(results)


def migrate_data(source_db: DatabaseInterface, target_db: DatabaseInterface,
                source_query: str, target_table: str, 
                batch_size: int = 1000, transform_fn: Optional[Callable] = None) -> int:
    """
    Migrate data from source to target database
    
    Args:
        source_db: Source database
        target_db: Target database
        source_query: Query to fetch data from source
        target_table: Target table name
        batch_size: Batch size for insertion
        transform_fn: Optional transformation function
    """
    records = source_db.fetch_all(source_query)
    
    if transform_fn:
        records = [transform_fn(record) for record in records]
    
    return bulk_insert(target_db, target_table, records, batch_size)


# Example usage
if __name__ == "__main__":
    # Example 1: Using DatabaseManager with connection pooling
    pg_params = {
        'host': 'localhost',
        'database': 'mydb',
        'user': 'postgres',
        'password': 'password'
    }
    
    pool_config = {
        'min_size': 2,
        'max_size': 10,
        'max_idle_time': 300
    }
    
    # Create manager with connection pooling
    db_manager = DatabaseFactory.create_manager(
        'postgresql',
        pg_params,
        use_pool=True,
        pool_config=pool_config
    )
    
    # Execute queries using the manager
    results = db_manager.execute_query(
        "SELECT * FROM users WHERE age > %s",
        (18,),
        fetch='all'
    )
    print(f"Found {len(results)} users")
    
    # Execute transaction
    operations = [
        ("INSERT INTO users (name, email) VALUES (%s, %s)", ('John', 'john@example.com')),
        ("UPDATE accounts SET balance = balance + %s WHERE user_id = %s", (100, 1))
    ]
    
    success = db_manager.execute_transaction(operations, IsolationLevel.SERIALIZABLE)
    print(f"Transaction {'succeeded' if success else 'failed'}")
    
    # Health check
    health = db_manager.health_check()
    print(f"Database health: {health}")
    
    # Get metrics
    metrics = db_manager.get_metrics()
    print(f"Metrics: {metrics}")
    
    # Close manager
    db_manager.close()
    
    # Example 2: Using direct connection with retry
    db = DatabaseFactory.create_database('postgresql', pg_params)
    db.connect()
    
    try:
        # Execute with automatic retry
        result = db.execute_with_retry(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (1,),
            max_retries=3,
            retry_delay=1.0
        )
        db.commit()
        print(f"Updated {result} rows")
    finally:
        db.disconnect()
    
    # Example 3: Singleton pattern for shared connection pool
    manager1 = DatabaseFactory.create_manager('postgresql', pg_params, singleton=True)
    manager2 = DatabaseFactory.create_manager('postgresql', pg_params, singleton=True)
    
    print(f"Same instance: {manager1 is manager2}")  # True
    
    # Close all singleton instances
    DatabaseFactory.close_all()