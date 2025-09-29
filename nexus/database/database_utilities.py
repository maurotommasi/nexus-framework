"""
Enterprise Database Features - Complete Package
All enterprise-grade database features in one module
"""

# Standard Library Imports
import os
import sys
import time
import json
import hashlib
import logging
import threading
import queue
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from collections import OrderedDict
from dataclasses import dataclass, field

# Third-Party Imports (install with: pip install -r requirements.txt)
import redis
from cryptography.fernet import Fernet

# Local Imports
from database import DatabaseFactory, DatabaseInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# 1. ADVANCED CONNECTION POOL
# ============================================================================

class AdvancedConnectionPool:
    """
    Enterprise connection pool with:
    - Health checks
    - Auto-scaling
    - Connection recycling
    - Slow connection detection
    """
    
    def __init__(self, db_config, min_size=5, max_size=20, max_lifetime=3600):
        self.db_config = db_config
        self.min_size = min_size
        self.max_size = max_size
        self.max_lifetime = max_lifetime  # Recycle after 1 hour
        self.pool = queue.Queue(maxsize=max_size)
        self.connection_stats = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger('ConnectionPool')
        
        # Initialize pool
        for _ in range(min_size):
            self.pool.put(self._create_connection())
    
    def _create_connection(self):
        """Create new database connection"""
        conn = DatabaseFactory.create_database(
            self.db_config['type'],
            self.db_config['params']
        )
        conn.connect()
        
        return {
            'connection': conn,
            'created_at': time.time(),
            'last_used': time.time(),
            'query_count': 0
        }
    
    def get_connection(self, timeout=30):
        """Get connection with health check"""
        try:
            conn_info = self.pool.get(timeout=timeout)
        except queue.Empty:
            # Pool exhausted, create new if under max
            with self.lock:
                if self._active_connections() < self.max_size:
                    conn_info = self._create_connection()
                else:
                    raise Exception("Connection pool exhausted")
        
        # Health check
        if not self._is_healthy(conn_info):
            conn_info = self._recycle_connection(conn_info)
        
        # Check lifetime
        if time.time() - conn_info['created_at'] > self.max_lifetime:
            conn_info = self._recycle_connection(conn_info)
        
        conn_info['last_used'] = time.time()
        return conn_info['connection']
    
    def release_connection(self, connection):
        """Return connection to pool"""
        for conn_info in list(self.pool.queue):
            if conn_info['connection'] == connection:
                conn_info['query_count'] += 1
                self.pool.put(conn_info)
                break
    
    def _is_healthy(self, conn_info):
        """Check if connection is healthy"""
        try:
            conn_info['connection'].execute("SELECT 1")
            return True
        except:
            return False
    
    def _recycle_connection(self, old_conn_info):
        """Replace unhealthy/old connection"""
        try:
            old_conn_info['connection'].disconnect()
        except:
            pass
        
        return self._create_connection()
    
    def _active_connections(self):
        """Count active connections"""
        return self.pool.qsize()
    
    def get_stats(self):
        """Get pool statistics"""
        return {
            'pool_size': self.pool.qsize(),
            'min_size': self.min_size,
            'max_size': self.max_size,
            'active': self._active_connections()
        }


# ============================================================================
# 2. MULTI-LEVEL CACHE
# ============================================================================

class MultiLevelCache:
    """
    L1: In-memory cache (fast, limited capacity)
    L2: Redis cache (distributed, larger capacity)
    L3: Database (source of truth)
    """
    
    def __init__(self, db, redis_client, l1_size=1000, ttl=300):
        self.db = db
        self.redis = redis_client
        self.l1_cache = OrderedDict()  # LRU cache
        self.l1_size = l1_size
        self.ttl = ttl
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'db_hits': 0,
            'total_requests': 0
        }
        self.lock = threading.Lock()
        self.logger = logging.getLogger('MultiLevelCache')
    
    def get(self, query, params=None):
        """Get with cache hierarchy"""
        self.stats['total_requests'] += 1
        cache_key = self._generate_key(query, params)
        
        # L1: Memory cache (fastest)
        with self.lock:
            if cache_key in self.l1_cache:
                self.stats['l1_hits'] += 1
                # Move to end (LRU)
                self.l1_cache.move_to_end(cache_key)
                return self.l1_cache[cache_key]
        
        # L2: Redis cache (fast)
        try:
            redis_value = self.redis.get(cache_key)
            if redis_value:
                self.stats['l2_hits'] += 1
                result = json.loads(redis_value)
                self._set_l1(cache_key, result)
                return result
        except Exception as e:
            self.logger.warning(f"Redis error: {e}")
        
        # L3: Database (slowest)
        self.stats['db_hits'] += 1
        result = self.db.fetch_all(query, params)
        
        # Cache in both levels
        self._set_l1(cache_key, result)
        try:
            self.redis.setex(cache_key, self.ttl, json.dumps(result, default=str))
        except Exception as e:
            self.logger.warning(f"Redis set error: {e}")
        
        return result
    
    def set(self, key, value, ttl=None):
        """Manually set cache value"""
        ttl = ttl or self.ttl
        
        # Set in both caches
        self._set_l1(key, value)
        try:
            self.redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            self.logger.warning(f"Redis set error: {e}")
    
    def invalidate(self, pattern):
        """Invalidate cache entries matching pattern"""
        # Clear L1
        with self.lock:
            keys_to_delete = [k for k in self.l1_cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.l1_cache[key]
        
        # Clear L2
        try:
            for key in self.redis.scan_iter(match=f"*{pattern}*"):
                self.redis.delete(key)
        except Exception as e:
            self.logger.warning(f"Redis invalidate error: {e}")
    
    def clear_all(self):
        """Clear all caches"""
        with self.lock:
            self.l1_cache.clear()
        
        try:
            self.redis.flushdb()
        except Exception as e:
            self.logger.warning(f"Redis clear error: {e}")
    
    def _generate_key(self, query, params):
        """Generate cache key from query and params"""
        key_str = f"{query}:{params}"
        return f"cache:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _set_l1(self, key, value):
        """Set L1 cache with LRU eviction"""
        with self.lock:
            if len(self.l1_cache) >= self.l1_size:
                # Remove oldest (first item)
                self.l1_cache.popitem(last=False)
            
            self.l1_cache[key] = value
    
    def get_stats(self):
        """Get cache performance statistics"""
        total = self.stats['total_requests']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'l1_hit_rate': f"{self.stats['l1_hits'] / total * 100:.2f}%",
            'l2_hit_rate': f"{self.stats['l2_hits'] / total * 100:.2f}%",
            'cache_hit_rate': f"{(self.stats['l1_hits'] + self.stats['l2_hits']) / total * 100:.2f}%",
            'db_hit_rate': f"{self.stats['db_hits'] / total * 100:.2f}%"
        }


# ============================================================================
# 3. QUERY BUILDER
# ============================================================================

class QueryBuilder:
    """
    Fluent interface for building SQL queries
    """
    
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('QueryBuilder')
        self._reset()
    
    def _reset(self):
        """Reset builder state"""
        self._table = None
        self._select = ['*']
        self._where = []
        self._joins = []
        self._order_by = []
        self._group_by = []
        self._having = []
        self._limit = None
        self._offset = None
        self._params = []
    
    def table(self, table_name):
        """Set table"""
        self._table = table_name
        return self
    
    def select(self, *columns):
        """Select specific columns"""
        self._select = columns
        return self
    
    def where(self, column, operator, value):
        """Add WHERE clause"""
        self._where.append(f"{column} {operator} %s")
        self._params.append(value)
        return self
    
    def where_in(self, column, values):
        """Add WHERE IN clause"""
        placeholders = ', '.join(['%s'] * len(values))
        self._where.append(f"{column} IN ({placeholders})")
        self._params.extend(values)
        return self
    
    def where_null(self, column):
        """Add WHERE NULL clause"""
        self._where.append(f"{column} IS NULL")
        return self
    
    def where_not_null(self, column):
        """Add WHERE NOT NULL clause"""
        self._where.append(f"{column} IS NOT NULL")
        return self
    
    def join(self, table, on_clause, join_type='INNER'):
        """Add JOIN"""
        self._joins.append(f"{join_type} JOIN {table} ON {on_clause}")
        return self
    
    def left_join(self, table, on_clause):
        """Add LEFT JOIN"""
        return self.join(table, on_clause, 'LEFT')
    
    def right_join(self, table, on_clause):
        """Add RIGHT JOIN"""
        return self.join(table, on_clause, 'RIGHT')
    
    def order_by(self, column, direction='ASC'):
        """Add ORDER BY"""
        self._order_by.append(f"{column} {direction}")
        return self
    
    def group_by(self, *columns):
        """Add GROUP BY"""
        self._group_by.extend(columns)
        return self
    
    def having(self, condition):
        """Add HAVING clause"""
        self._having.append(condition)
        return self
    
    def limit(self, limit):
        """Add LIMIT"""
        self._limit = limit
        return self
    
    def offset(self, offset):
        """Add OFFSET"""
        self._offset = offset
        return self
    
    def get(self):
        """Execute and get all results"""
        query = self._build_select_query()
        result = self.db.fetch_all(query, tuple(self._params))
        self._reset()
        return result
    
    def first(self):
        """Get first result"""
        self.limit(1)
        results = self.get()
        return results[0] if results else None
    
    def count(self):
        """Get count"""
        original_select = self._select
        self._select = ['COUNT(*) as count']
        query = self._build_select_query()
        result = self.db.fetch_one(query, tuple(self._params))
        self._reset()
        return result['count'] if result else 0
    
    def insert(self, data):
        """Insert record"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})"
        
        result = self.db.execute(query, tuple(data.values()))
        self.db.commit()
        self._reset()
        return result
    
    def update(self, data):
        """Update records"""
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {self._table} SET {set_clause}"
        
        params = list(data.values())
        
        if self._where:
            query += " WHERE " + " AND ".join(self._where)
            params.extend(self._params)
        
        result = self.db.execute(query, tuple(params))
        self.db.commit()
        self._reset()
        return result
    
    def delete(self):
        """Delete records"""
        query = f"DELETE FROM {self._table}"
        
        if self._where:
            query += " WHERE " + " AND ".join(self._where)
        
        result = self.db.execute(query, tuple(self._params))
        self.db.commit()
        self._reset()
        return result
    
    def _build_select_query(self):
        """Build SELECT query"""
        query = f"SELECT {', '.join(self._select)} FROM {self._table}"
        
        if self._joins:
            query += " " + " ".join(self._joins)
        
        if self._where:
            query += " WHERE " + " AND ".join(self._where)
        
        if self._group_by:
            query += " GROUP BY " + ", ".join(self._group_by)
        
        if self._having:
            query += " HAVING " + " AND ".join(self._having)
        
        if self._order_by:
            query += " ORDER BY " + ", ".join(self._order_by)
        
        if self._limit:
            query += f" LIMIT {self._limit}"
        
        if self._offset:
            query += f" OFFSET {self._offset}"
        
        return query
    
    def to_sql(self):
        """Get SQL without executing"""
        return self._build_select_query()


# ============================================================================
# 4. AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """
    Comprehensive audit logging for compliance and forensics
    """
    
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger('AuditLogger')
        self._ensure_audit_table()
    
    def _ensure_audit_table(self):
        """Create audit log table if not exists"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR(255),
                user_email VARCHAR(255),
                action VARCHAR(50),
                table_name VARCHAR(255),
                record_id VARCHAR(255),
                old_values JSONB,
                new_values JSONB,
                changes JSONB,
                ip_address VARCHAR(45),
                user_agent TEXT,
                session_id VARCHAR(255),
                request_id VARCHAR(255)
            )
        """)
        
        # Create indexes for performance
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name, record_id)")
        
        self.db.commit()
    
    def log_change(self, action, table, record_id, 
                   old_values=None, new_values=None,
                   user_id=None, user_email=None,
                   ip_address=None, user_agent=None,
                   session_id=None, request_id=None):
        """Log a database change with full context"""
        
        # Calculate changes
        changes = self._calculate_changes(old_values, new_values)
        
        self.db.execute("""
            INSERT INTO audit_log 
            (user_id, user_email, action, table_name, record_id, 
             old_values, new_values, changes, ip_address, user_agent, 
             session_id, request_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            user_email,
            action,
            table,
            str(record_id),
            json.dumps(old_values, default=str) if old_values else None,
            json.dumps(new_values, default=str) if new_values else None,
            json.dumps(changes, default=str) if changes else None,
            ip_address,
            user_agent,
            session_id,
            request_id
        ))
        self.db.commit()
        
        self.logger.info(f"Audit: {action} on {table}.{record_id} by user {user_id}")
    
    def _calculate_changes(self, old_values, new_values):
        """Calculate what changed between old and new values"""
        if not old_values or not new_values:
            return None
        
        changes = {}
        for key in new_values.keys():
            if key in old_values and old_values[key] != new_values[key]:
                changes[key] = {
                    'old': old_values[key],
                    'new': new_values[key]
                }
        
        return changes if changes else None
    
    def get_history(self, table, record_id, limit=100):
        """Get complete change history for a record"""
        return self.db.fetch_all("""
            SELECT * FROM audit_log
            WHERE table_name = %s AND record_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (table, str(record_id), limit))
    
    def get_user_activity(self, user_id, start_date=None, end_date=None, limit=1000):
        """Get all activity for a specific user"""
        query = "SELECT * FROM audit_log WHERE user_id = %s"
        params = [user_id]
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_table_activity(self, table, start_date=None, end_date=None, limit=1000):
        """Get all changes to a specific table"""
        query = "SELECT * FROM audit_log WHERE table_name = %s"
        params = [table]
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        
        return self.db.fetch_all(query, tuple(params))


# ============================================================================
# 5. ENCRYPTED DATABASE
# ============================================================================

class EncryptedDatabase:
    """
    Transparent field-level encryption for sensitive data
    """
    
    def __init__(self, db, encryption_key):
        self.db = db
        self.fernet = Fernet(encryption_key)
        self.encrypted_fields = {}  # {table: [field1, field2]}
        self.logger = logging.getLogger('EncryptedDatabase')
    
    def register_encrypted_fields(self, table, fields):
        """Register which fields should be encrypted"""
        self.encrypted_fields[table] = fields
        self.logger.info(f"Registered encrypted fields for {table}: {fields}")
    
    def insert(self, table, data):
        """Insert with automatic encryption"""
        encrypted_data = self._encrypt_fields(table, data)
        
        columns = ', '.join(encrypted_data.keys())
        placeholders = ', '.join(['%s'] * len(encrypted_data))
        values = tuple(encrypted_data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        result = self.db.execute(query, values)
        self.db.commit()
        return result
    
    def select(self, table, conditions=None):
        """Select with automatic decryption"""
        query = f"SELECT * FROM {table}"
        params = None
        
        if conditions:
            where_clause = ' AND '.join([f"{k} = %s" for k in conditions.keys()])
            query += f" WHERE {where_clause}"
            params = tuple(conditions.values())
        
        results = self.db.fetch_all(query, params)
        
        # Decrypt results
        return [self._decrypt_fields(table, row) for row in results]
    
    def _encrypt_fields(self, table, data):
        """Encrypt sensitive fields"""
        encrypted = data.copy()
        
        if table in self.encrypted_fields:
            for field in self.encrypted_fields[table]:
                if field in encrypted and encrypted[field]:
                    encrypted[field] = self.fernet.encrypt(
                        str(encrypted[field]).encode()
                    ).decode()
        
        return encrypted
    
    def _decrypt_fields(self, table, data):
        """Decrypt sensitive fields"""
        decrypted = dict(data)
        
        if table in self.encrypted_fields:
            for field in self.encrypted_fields[table]:
                if field in decrypted and decrypted[field]:
                    try:
                        decrypted[field] = self.fernet.decrypt(
                            decrypted[field].encode()
                        ).decode()
                    except:
                        pass  # Field not encrypted
        
        return decrypted


# ============================================================================
# 6. BACKUP MANAGER
# ============================================================================

class BackupManager:
    """
    Automated backup and point-in-time recovery
    """
    
    def __init__(self, db_config, backup_dir='/backups'):
        self.db_config = db_config
        self.backup_dir = backup_dir
        self.logger = logging.getLogger('BackupManager')
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, backup_name=None):
        """Create full database backup"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = os.path.join(self.backup_dir, f"{backup_name}.sql")
        
        # PostgreSQL example
        if self.db_config['type'] == 'postgresql':
            params = self.db_config['params']
            cmd = f"pg_dump -h {params['host']} -U {params['user']} -d {params['database']} > {backup_file}"
            os.system(cmd)
        
        # MySQL example
        elif self.db_config['type'] == 'mysql':
            params = self.db_config['params']
            cmd = f"mysqldump -h {params['host']} -u {params['user']} -p{params['password']} {params['database']} > {backup_file}"
            os.system(cmd)
        
        # Compress
        self._compress_backup(backup_file)
        
        self.logger.info(f"Backup created: {backup_file}.gz")
        return f"{backup_file}.gz"
    
    def restore_backup(self, backup_file):
        """Restore from backup"""
        # Decompress
        if backup_file.endswith('.gz'):
            self._decompress_backup(backup_file)
            backup_file = backup_file[:-3]
        
        # Restore
        if self.db_config['type'] == 'postgresql':
            params = self.db_config['params']
            cmd = f"psql -h {params['host']} -U {params['user']} -d {params['database']} < {backup_file}"
            os.system(cmd)
        
        elif self.db_config['type'] == 'mysql':
            params = self.db_config['params']
            cmd = f"mysql -h {params['host']} -u {params['user']} -p{params['password']} {params['database']} < {backup_file}"
            os.system(cmd)
        
        self.logger.info(f"Backup restored from: {backup_file}")
    
    def list_backups(self):
        """List available backups"""
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.sql.gz'):
                stat = os.stat(os.path.join(self.backup_dir, file))
                backups.append({
                    'name': file,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime)
                })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def _compress_backup(self, file_path):
        """Compress backup file"""
        with open(file_path, 'rb') as f_in:
            with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        os.remove(file_path)
    
    def _decompress_backup(self, file_path):
        """Decompress backup file"""
        with gzip.open(file_path, 'rb') as f_in:
            with open(file_path[:-3], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AdvancedConnectionPool',
    'MultiLevelCache',
    'QueryBuilder',
    'AuditLogger',
    'EncryptedDatabase',
    'BackupManager'
]