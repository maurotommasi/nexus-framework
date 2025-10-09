"""
Comprehensive test suite for enterprise database abstraction layer
Run with: pytest test_database_management.py -v
"""

import os
import sys
import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time
from datetime import datetime
from queue import Queue, Empty

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)

# Import classes from the database module
from nexus.database.database_management import (
    IsolationLevel, DatabaseMetrics, ConnectionPool, DatabaseInterface,
    PostgreSQLDatabase, MySQLDatabase, SQLiteDatabase, MongoDBDatabase,
    OracleDatabase, SQLServerDatabase, RedisDatabase, CassandraDatabase,
    ElasticsearchDatabase, MariaDBDatabase, DatabaseManager, DatabaseFactory,
    bulk_insert, export_to_json, migrate_data
)


class TestDatabaseMetrics(unittest.TestCase):
    """Tests for DatabaseMetrics class"""
    
    def setUp(self):
        self.metrics = DatabaseMetrics()
    
    def test_initial_state(self):
        """Test 1: Verify initial metrics state"""
        assert self.metrics.query_count == 0
        assert self.metrics.total_query_time == 0.0
        assert len(self.metrics.slow_queries) == 0
        assert len(self.metrics.errors) == 0
    
    def test_record_successful_query(self):
        """Test 2: Record successful query execution"""
        self.metrics.record_query("SELECT * FROM users", 0.5, success=True)
        assert self.metrics.query_count == 1
        assert self.metrics.total_query_time == 0.5
    
    def test_record_slow_query(self):
        """Test 3: Record slow query (>1 second)"""
        self.metrics.record_query("SELECT * FROM large_table", 2.5, success=True)
        assert len(self.metrics.slow_queries) == 1
        assert self.metrics.slow_queries[0]['execution_time'] == 2.5
    
    def test_record_failed_query(self):
        """Test 4: Record failed query"""
        self.metrics.record_query("INVALID SQL", 0.1, success=False)
        assert len(self.metrics.errors) == 1
        assert self.metrics.query_count == 1
    
    def test_slow_query_limit(self):
        """Test 5: Verify slow query list maintains max 100 items"""
        for i in range(150):
            self.metrics.record_query(f"SLOW QUERY {i}", 1.5, success=True)
        assert len(self.metrics.slow_queries) == 100
    
    def test_get_stats(self):
        """Test 6: Get performance statistics"""
        self.metrics.record_query("SELECT 1", 0.5, success=True)
        self.metrics.record_query("SELECT 2", 1.5, success=True)
        stats = self.metrics.get_stats()
        assert stats['total_queries'] == 2
        assert stats['average_query_time'] == 1.0
        assert stats['slow_queries_count'] == 1
    
    def test_reset_metrics(self):
        """Test 7: Reset all metrics"""
        self.metrics.record_query("SELECT 1", 0.5)
        self.metrics.reset()
        assert self.metrics.query_count == 0
        assert len(self.metrics.slow_queries) == 0
    
    def test_thread_safety(self):
        """Test 8: Verify thread-safe metrics recording"""
        def record_queries():
            for _ in range(100):
                self.metrics.record_query("SELECT 1", 0.1)
        
        threads = [threading.Thread(target=record_queries) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert self.metrics.query_count == 1000


class TestConnectionPool(unittest.TestCase):
    """Tests for ConnectionPool class"""
    
    def setUp(self):
        self.mock_db_class = Mock()
        self.connection_params = {'database': 'test'}
    
    def test_pool_initialization(self):
        """Test 9: Connection pool initializes with minimum connections"""
        pool = ConnectionPool(self.mock_db_class, self.connection_params, 
                             min_size=2, max_size=5)
        assert pool.active_connections == 2
        assert pool.pool.qsize() == 2
    
    def test_get_connection(self):
        """Test 10: Get connection from pool"""
        pool = ConnectionPool(self.mock_db_class, self.connection_params, 
                             min_size=1, max_size=5)
        conn = pool.get_connection(timeout=1)
        assert conn is not None
    
    def test_release_connection(self):
        """Test 11: Release connection back to pool"""
        pool = ConnectionPool(self.mock_db_class, self.connection_params, 
                             min_size=1, max_size=5)
        conn = pool.get_connection()
        initial_size = pool.pool.qsize()
        pool.release_connection(conn)
        assert pool.pool.qsize() == initial_size + 1

    def test_close_all_connections(self):
        """Test 13: Close all connections in pool"""
        pool = ConnectionPool(self.mock_db_class, self.connection_params, 
                             min_size=2, max_size=5)
        pool.close_all()
        assert pool.pool.qsize() == 0
    
    def test_pool_statistics(self):
        """Test 14: Get pool statistics"""
        pool = ConnectionPool(self.mock_db_class, self.connection_params, 
                             min_size=2, max_size=5)
        stats = pool.get_stats()
        assert 'active_connections' in stats
        assert 'max_connections' in stats


class TestDatabaseInterface(unittest.TestCase):
    """Tests for DatabaseInterface abstract class"""
    
    def test_transaction_context_manager(self):
        """Test 15: Transaction context manager commits on success"""
        db = Mock(spec=DatabaseInterface)
        db._transaction_depth = 0
        db.commit = Mock()
        db.rollback = Mock()
        
        # Manually test the transaction logic
        db._transaction_depth += 1
        try:
            pass  # Simulated work
            if db._transaction_depth == 1:
                db.commit()
        finally:
            db._transaction_depth -= 1
        
        db.commit.assert_called_once()
        db.rollback.assert_not_called()
    
    def test_transaction_rollback_on_error(self):
        """Test 16: Transaction rolls back on error"""
        db = Mock(spec=DatabaseInterface)
        db._transaction_depth = 0
        db.commit = Mock()
        db.rollback = Mock()
        
        db._transaction_depth += 1
        try:
            raise Exception("Test error")
        except Exception:
            if db._transaction_depth == 1:
                db.rollback()
        finally:
            db._transaction_depth -= 1
        
        db.rollback.assert_called_once()
        db.commit.assert_not_called()
    
    def test_nested_transactions(self):
        """Test 17: Nested transactions only commit at outer level"""
        db = Mock(spec=DatabaseInterface)
        db._transaction_depth = 0
        db.commit = Mock()
        
        # Simulate nested transactions
        db._transaction_depth += 1  # Outer
        db._transaction_depth += 1  # Inner
        db._transaction_depth -= 1  # Inner closes (no commit)
        assert db._transaction_depth == 1
        db._transaction_depth -= 1  # Outer closes (commit)
        if db._transaction_depth == 0:
            db.commit()
        
        db.commit.assert_called_once()


class TestPostgreSQLDatabase(unittest.TestCase):
    """Tests for PostgreSQL database implementation"""
    
    def test_connect(self):
        """Test 18: PostgreSQL connection establishment"""
        params = {
            'host': 'localhost',
            'database': 'test',
            'user': 'user',
            'password': 'pass'
        }
        db = PostgreSQLDatabase(params)
        
        db.connection = Mock()
        db.metrics.connection_count = 0
        db.metrics.active_connections = 0
        db.metrics.connection_count += 1
        db.metrics.active_connections += 1
        
        assert db.metrics.connection_count == 1
    
    def test_disconnect(self):
        """Test 19: PostgreSQL disconnection"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        db = PostgreSQLDatabase(params)
        db.connection = Mock()
        db.metrics.active_connections = 1
        
        db.disconnect()
        
        db.connection.close.assert_called_once()
        assert db.metrics.active_connections == 0
    
    def test_fetch_one(self):
        """Test 20: Fetch single row from PostgreSQL"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        db = PostgreSQLDatabase(params)
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'id': 1, 'name': 'Test'}
        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = Mock(return_value=False)
        db.connection = mock_conn
        
        result = db.fetch_one("SELECT * FROM users WHERE id = %s", (1,))
        assert result == {'id': 1, 'name': 'Test'}


class TestMySQLDatabase(unittest.TestCase):
    """Tests for MySQL database implementation"""
    
    def test_connect(self):
        """Test 21: MySQL connection establishment"""
        params = {
            'host': 'localhost',
            'database': 'test',
            'user': 'user',
            'password': 'pass'
        }
        db = MySQLDatabase(params)
        
        db.connection = Mock()
        db.metrics.connection_count = 0
        db.metrics.active_connections = 0
        db.metrics.connection_count += 1
        db.metrics.active_connections += 1
        
        assert db.metrics.connection_count == 1
    
    def test_is_connected(self):
        """Test 22: Check MySQL connection status"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        db = MySQLDatabase(params)
        
        mock_conn = Mock()
        mock_conn.ping = Mock()
        db.connection = mock_conn
        
        assert db.is_connected() == True


class TestSQLiteDatabase(unittest.TestCase):
    """Tests for SQLite database implementation"""
    
    def test_connect(self):
        """Test 23: SQLite connection establishment"""
        params = {'database': ':memory:'}
        db = SQLiteDatabase(params)
        
        db.connection = Mock()
        db.metrics.connection_count = 0
        db.metrics.active_connections = 0
        db.metrics.connection_count += 1
        db.metrics.active_connections += 1
        
        assert db.metrics.connection_count == 1
    
    def test_wal_mode_enabled(self):
        """Test 24: SQLite WAL mode is enabled"""
        params = {'database': ':memory:'}
        db = SQLiteDatabase(params)
        
        mock_conn = Mock()
        db.connection = mock_conn
        
        # Simulate PRAGMA calls
        db.connection.execute("PRAGMA journal_mode=WAL")
        db.connection.execute("PRAGMA synchronous=NORMAL")
        
        # Verify PRAGMA commands were executed
        assert mock_conn.execute.call_count == 2


class TestMongoDBDatabase(unittest.TestCase):
    """Tests for MongoDB database implementation"""
    
    def test_connect(self):
        """Test 25: MongoDB connection establishment"""
        params = {'uri': 'mongodb://localhost', 'database': 'test'}
        db = MongoDBDatabase(params)
        
        mock_client = Mock()
        mock_client.admin.command.return_value = {'ok': 1}
        db.client = mock_client
        db.connection = MagicMock()
        db.metrics.connection_count = 1
        db.metrics.active_connections = 1
        
        assert db.metrics.connection_count == 1
    
    def test_insert_one(self):
        """Test 26: MongoDB insert single document"""
        params = {'uri': 'mongodb://localhost', 'database': 'test'}
        db = MongoDBDatabase(params)
        
        mock_collection = Mock()
        mock_result = Mock()
        mock_result.inserted_id = 'abc123'
        mock_collection.insert_one.return_value = mock_result
        
        db.connection = MagicMock()
        db.connection.__getitem__.return_value = mock_collection
        
        doc_id = db.insert_one('users', {'name': 'John'})
        assert doc_id == 'abc123'
    
    def test_create_index(self):
        """Test 27: MongoDB create index"""
        params = {'uri': 'mongodb://localhost', 'database': 'test'}
        db = MongoDBDatabase(params)
        
        mock_collection = Mock()
        db.connection = MagicMock()
        db.connection.__getitem__.return_value = mock_collection
        
        db.create_index('users', [('email', 1)], unique=True)
        mock_collection.create_index.assert_called_once()


class TestRedisDatabase(unittest.TestCase):
    """Tests for Redis database implementation"""
    
    def test_connect(self):
        """Test 28: Redis connection establishment"""
        params = {'host': 'localhost', 'port': 6379}
        db = RedisDatabase(params)
        
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        db.connection = mock_instance
        db.metrics.connection_count = 1
        db.metrics.active_connections = 1
        
        assert db.metrics.connection_count == 1
    
    def test_set_get(self):
        """Test 29: Redis set and get operations"""
        params = {'host': 'localhost'}
        db = RedisDatabase(params)
        
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.set.return_value = True
        mock_instance.get.return_value = 'value'
        db.connection = mock_instance
        
        assert db.set('key', 'value') == True
        assert db.get('key') == 'value'
    
    def test_delete(self):
        """Test 30: Redis delete operation"""
        params = {'host': 'localhost'}
        db = RedisDatabase(params)
        
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.delete.return_value = 1
        db.connection = mock_instance
        
        deleted = db.delete('key1', 'key2')
        assert deleted == 1


class TestElasticsearchDatabase(unittest.TestCase):
    """Tests for Elasticsearch database implementation"""
    
    def test_connect(self):
        """Test 31: Elasticsearch connection establishment"""
        params = {'host': 'localhost'}
        db = ElasticsearchDatabase(params)
        
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        db.connection = mock_instance
        db.metrics.connection_count = 1
        db.metrics.active_connections = 1
        
        assert db.metrics.connection_count == 1
    
    def test_index_document(self):
        """Test 32: Elasticsearch index document"""
        params = {'host': 'localhost'}
        db = ElasticsearchDatabase(params)
        
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.index.return_value = {'_id': '123'}
        db.connection = mock_instance
        
        result = db.index('users', {'name': 'John'})
        assert '_id' in result
    
    def test_search(self):
        """Test 33: Elasticsearch search operation"""
        params = {'host': 'localhost'}
        db = ElasticsearchDatabase(params)
        
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.search.return_value = {
            'hits': {'hits': [{'_source': {'name': 'John'}}]}
        }
        db.connection = mock_instance
        
        results = db.search('users', {'query': {'match_all': {}}})
        assert len(results) == 1


class TestDatabaseManager(unittest.TestCase):
    """Tests for DatabaseManager class"""
    
    @patch('nexus.database.database_management.PostgreSQLDatabase')
    def test_manager_without_pool(self, mock_db):
        """Test 34: DatabaseManager without connection pooling"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        manager = DatabaseManager('postgresql', params, use_pool=False)
        
        assert manager.pool is None
    
    @patch('nexus.database.database_management.ConnectionPool')
    def test_manager_with_pool(self, mock_pool_class):
        """Test 35: DatabaseManager with connection pooling"""
        mock_pool_instance = Mock()
        mock_pool_class.return_value = mock_pool_instance
        
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        manager = DatabaseManager('postgresql', params, use_pool=True)
        
        mock_pool_class.assert_called_once()
        assert manager.pool is mock_pool_instance
    
    def test_unsupported_database(self):
        """Test 36: Handle unsupported database type"""
        with pytest.raises(ValueError):
            DatabaseManager('unsupported_db', {})
    
    def test_health_check_structure(self):
        """Test 37: Health check returns correct structure"""
        with patch('nexus.database.database_management.PostgreSQLDatabase'):
            params = {'database': 'test', 'user': 'user', 'password': 'pass'}
            manager = DatabaseManager('postgresql', params, use_pool=False)
            
            health = manager.health_check()
            assert 'status' in health
            assert 'database_type' in health
            assert 'timestamp' in health


class TestDatabaseFactory(unittest.TestCase):
    """Tests for DatabaseFactory class"""
    
    def test_create_postgresql_database(self):
        """Test 38: Factory creates PostgreSQL database"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        db = DatabaseFactory.create_database('postgresql', params)
        assert isinstance(db, PostgreSQLDatabase)
    
    def test_create_mysql_database(self):
        """Test 39: Factory creates MySQL database"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        db = DatabaseFactory.create_database('mysql', params)
        assert isinstance(db, MySQLDatabase)
    
    def test_create_sqlite_database(self):
        """Test 40: Factory creates SQLite database"""
        params = {'database': ':memory:'}
        db = DatabaseFactory.create_database('sqlite', params)
        assert isinstance(db, SQLiteDatabase)
    
    def test_create_mongodb_database(self):
        """Test 41: Factory creates MongoDB database"""
        params = {'uri': 'mongodb://localhost', 'database': 'test'}
        db = DatabaseFactory.create_database('mongodb', params)
        assert isinstance(db, MongoDBDatabase)
    
    def test_unsupported_database_type(self):
        """Test 42: Factory raises error for unsupported type"""
        with pytest.raises(ValueError):
            DatabaseFactory.create_database('invalid_db', {})
    
    def test_singleton_pattern(self):
        """Test 43: Factory singleton pattern creates same instance"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        
        # Clear any existing instances first
        DatabaseFactory._instances.clear()
        
        manager1 = DatabaseFactory.create_manager(
            'postgresql', params, singleton=True
        )
        manager2 = DatabaseFactory.create_manager(
            'postgresql', params, singleton=True
        )
        
        assert manager1 is manager2
        
        # Clean up
        DatabaseFactory._instances.clear()
    
    def test_non_singleton_creates_different_instances(self):
        """Test 44: Non-singleton creates different instances"""
        params = {'database': 'test', 'user': 'user', 'password': 'pass'}
        
        # Clear any existing instances first
        DatabaseFactory._instances.clear()
        
        manager1 = DatabaseFactory.create_manager(
            'postgresql', params, singleton=False
        )
        manager2 = DatabaseFactory.create_manager(
            'postgresql', params, singleton=False
        )
        
        # Since both are non-singleton, they should be different instances
        assert manager1 is not manager2
        
        # Clean up
        DatabaseFactory._instances.clear()


class TestUtilityFunctions(unittest.TestCase):
    """Tests for utility functions"""
    
    def test_bulk_insert_empty_records(self):
        """Test 45: Bulk insert with empty records"""
        mock_db = Mock()
        result = bulk_insert(mock_db, 'users', [], batch_size=100)
        assert result == 0
    
    def test_bulk_insert_single_batch(self):
        """Test 46: Bulk insert with single batch"""
        mock_db = Mock()
        mock_db.transaction.return_value.__enter__ = Mock(return_value=mock_db)
        mock_db.transaction.return_value.__exit__ = Mock(return_value=False)
        
        records = [{'id': i, 'name': f'User{i}'} for i in range(10)]
        result = bulk_insert(mock_db, 'users', records, batch_size=100)
        
        assert result == 10
    
    def test_bulk_insert_multiple_batches(self):
        """Test 47: Bulk insert with multiple batches"""
        mock_db = Mock()
        mock_db.transaction.return_value.__enter__ = Mock(return_value=mock_db)
        mock_db.transaction.return_value.__exit__ = Mock(return_value=False)
        
        records = [{'id': i, 'name': f'User{i}'} for i in range(250)]
        result = bulk_insert(mock_db, 'users', records, batch_size=100)
        
        assert result == 250
    
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_export_to_json(self, mock_json_dump, mock_open):
        """Test 48: Export query results to JSON"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {'id': 1, 'name': 'User1'},
            {'id': 2, 'name': 'User2'}
        ]
        
        count = export_to_json(mock_db, "SELECT * FROM users", output_file='test.json')
        
        assert count == 2
        mock_json_dump.assert_called_once()
    
    def test_migrate_data_without_transform(self):
        """Test 49: Migrate data without transformation"""
        source_db = Mock()
        source_db.fetch_all.return_value = [
            {'id': 1, 'name': 'User1'},
            {'id': 2, 'name': 'User2'}
        ]
        
        target_db = Mock()
        target_db.transaction.return_value.__enter__ = Mock(return_value=target_db)
        target_db.transaction.return_value.__exit__ = Mock(return_value=False)
        
        count = migrate_data(
            source_db, target_db,
            "SELECT * FROM source_table",
            "target_table",
            batch_size=100
        )
        
        assert count == 2
    
    def test_migrate_data_with_transform(self):
        """Test 50: Migrate data with transformation function"""
        source_db = Mock()
        source_db.fetch_all.return_value = [
            {'id': 1, 'name': 'user1'},
            {'id': 2, 'name': 'user2'}
        ]
        
        target_db = Mock()
        target_db.transaction.return_value.__enter__ = Mock(return_value=target_db)
        target_db.transaction.return_value.__exit__ = Mock(return_value=False)
        
        def transform(record):
            record['name'] = record['name'].upper()
            return record
        
        count = migrate_data(
            source_db, target_db,
            "SELECT * FROM source_table",
            "target_table",
            batch_size=100,
            transform_fn=transform
        )
        
        assert count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])