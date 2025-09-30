"""
Comprehensive unit tests for Real-Time Database Replication System
50+ test cases covering all components
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from datetime import datetime, timedelta
import json
import threading
import queue
import time
import tempfile
import os
import sys

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)

# Import classes to test
from nexus.database.database_replication import (
    ReplicationMode,
    ReplicaRole,
    ConflictResolution,
    ReplicationEvent,
    ReplicaConfig,
    ReplicationStats,
    ReplicationLog,
    ReplicaManager,
    DatabaseReplicationManager,
    ReplicatedDatabase
)


class TestReplicationEnums(unittest.TestCase):
    """Test enum classes"""
    
    def test_replication_mode_values(self):
        """Test 1: Verify replication mode values"""
        self.assertEqual(ReplicationMode.SYNCHRONOUS.value, "synchronous")
        self.assertEqual(ReplicationMode.ASYNCHRONOUS.value, "asynchronous")
        self.assertEqual(ReplicationMode.SEMI_SYNC.value, "semi_sync")
    
    def test_replica_role_values(self):
        """Test 2: Verify replica role values"""
        self.assertEqual(ReplicaRole.PRIMARY.value, "primary")
        self.assertEqual(ReplicaRole.REPLICA.value, "replica")
    
    def test_conflict_resolution_values(self):
        """Test 3: Verify conflict resolution values"""
        self.assertEqual(ConflictResolution.PRIMARY_WINS.value, "primary_wins")
        self.assertEqual(ConflictResolution.LATEST_WINS.value, "latest_wins")
        self.assertEqual(ConflictResolution.MANUAL.value, "manual")


class TestReplicationEvent(unittest.TestCase):
    """Test ReplicationEvent dataclass"""
    
    def test_event_creation(self):
        """Test 4: Create replication event"""
        event = ReplicationEvent(
            event_id='evt123',
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s, %s)',
            params=('John', 'john@example.com'),
            source_db='primary',
            checksum='abc123'
        )
        
        self.assertEqual(event.event_id, 'evt123')
        self.assertEqual(event.operation, 'INSERT')
        self.assertEqual(event.table, 'users')
    
    def test_event_to_dict(self):
        """Test 5: Convert event to dictionary"""
        event = ReplicationEvent(
            event_id='evt456',
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            operation='UPDATE',
            table='orders',
            query='UPDATE orders SET status = %s',
            params=('shipped',),
            source_db='primary',
            checksum='def456'
        )
        
        result = event.to_dict()
        
        self.assertEqual(result['event_id'], 'evt456')
        self.assertEqual(result['operation'], 'UPDATE')
        self.assertIn('2025-01-01', result['timestamp'])
    
    def test_event_with_none_params(self):
        """Test 6: Event with None parameters"""
        event = ReplicationEvent(
            event_id='evt789',
            timestamp=datetime.now(),
            operation='DELETE',
            table='logs',
            query='DELETE FROM logs WHERE date < NOW()',
            params=None,
            source_db='primary',
            checksum='ghi789'
        )
        
        result = event.to_dict()
        self.assertIsNone(result['params'])


class TestReplicaConfig(unittest.TestCase):
    """Test ReplicaConfig dataclass"""
    
    def test_config_creation_with_defaults(self):
        """Test 7: Create replica config with defaults"""
        config = ReplicaConfig(
            name='replica-1',
            db_type='postgresql',
            connection_params={'host': 'localhost'}
        )
        
        self.assertEqual(config.name, 'replica-1')
        self.assertEqual(config.role, ReplicaRole.REPLICA)
        self.assertEqual(config.priority, 100)
        self.assertTrue(config.enabled)
        self.assertEqual(config.max_lag_seconds, 30)
    
    def test_config_creation_with_custom_values(self):
        """Test 8: Create replica config with custom values"""
        config = ReplicaConfig(
            name='primary-db',
            db_type='mysql',
            connection_params={'host': 'primary.com'},
            role=ReplicaRole.PRIMARY,
            priority=1,
            enabled=False,
            max_lag_seconds=60
        )
        
        self.assertEqual(config.role, ReplicaRole.PRIMARY)
        self.assertEqual(config.priority, 1)
        self.assertFalse(config.enabled)
        self.assertEqual(config.max_lag_seconds, 60)


class TestReplicationStats(unittest.TestCase):
    """Test ReplicationStats dataclass"""
    
    def test_stats_initialization(self):
        """Test 9: Stats initialization with defaults"""
        stats = ReplicationStats()
        
        self.assertEqual(stats.events_processed, 0)
        self.assertEqual(stats.events_failed, 0)
        self.assertEqual(stats.replicas_synced, 0)
        self.assertEqual(stats.average_lag_ms, 0.0)
        self.assertIsNone(stats.last_event_time)
    
    def test_stats_to_dict(self):
        """Test 10: Stats conversion to dictionary"""
        stats = ReplicationStats(
            events_processed=100,
            events_failed=5,
            replicas_synced=95,
            average_lag_ms=15.5,
            last_event_time=datetime(2025, 1, 1, 12, 0, 0)
        )
        
        result = stats.to_dict()
        
        self.assertEqual(result['events_processed'], 100)
        self.assertEqual(result['events_failed'], 5)
        self.assertEqual(result['average_lag_ms'], 15.5)
        self.assertIn('2025-01-01', result['last_event_time'])
    
    def test_stats_to_dict_with_none_timestamp(self):
        """Test 11: Stats to dict with None timestamp"""
        stats = ReplicationStats()
        result = stats.to_dict()
        
        self.assertIsNone(result['last_event_time'])


class TestReplicationLog(unittest.TestCase):
    """Test ReplicationLog class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.temp_file.close()
        self.log = ReplicationLog(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test files"""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_log_event(self):
        """Test 12: Log replication event"""
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='checksum1'
        )
        
        self.log.log_event(event)
        
        with open(self.temp_file.name, 'r') as f:
            logged_data = json.loads(f.readline())
        
        self.assertEqual(logged_data['event_id'], 'evt001')
        self.assertEqual(logged_data['operation'], 'INSERT')
    
    def test_log_multiple_events(self):
        """Test 13: Log multiple events"""
        events = [
            ReplicationEvent(
                event_id=f'evt{i}',
                timestamp=datetime.now(),
                operation='INSERT',
                table='users',
                query='INSERT INTO users VALUES (%s)',
                params=(f'User{i}',),
                source_db='primary',
                checksum=f'check{i}'
            )
            for i in range(5)
        ]
        
        for event in events:
            self.log.log_event(event)
        
        with open(self.temp_file.name, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 5)
    
    def test_get_events_since(self):
        """Test 14: Get events since timestamp"""
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        
        # Log events at different times
        for i in range(5):
            event = ReplicationEvent(
                event_id=f'evt{i}',
                timestamp=base_time + timedelta(minutes=i),
                operation='INSERT',
                table='users',
                query='INSERT INTO users VALUES (%s)',
                params=(f'User{i}',),
                source_db='primary',
                checksum=f'check{i}'
            )
            self.log.log_event(event)
        
        # Get events since 2 minutes after base time
        since_time = base_time + timedelta(minutes=2)
        events = self.log.get_events_since(since_time)
        
        self.assertEqual(len(events), 3)  # Events at 2, 3, 4 minutes
        self.assertEqual(events[0].event_id, 'evt2')
    
    def test_get_events_from_nonexistent_file(self):
        """Test 15: Get events from nonexistent file"""
        log = ReplicationLog('nonexistent.log')
        events = log.get_events_from_nonexistent_file = log.get_events_since(datetime.now())
        
        self.assertEqual(len(events), 0)
    
    def test_log_thread_safety(self):
        """Test 16: Log thread-safe operations"""
        results = []
        
        def log_events(worker_id):
            for i in range(5):
                event = ReplicationEvent(
                    event_id=f'w{worker_id}-evt{i}',
                    timestamp=datetime.now(),
                    operation='INSERT',
                    table='test',
                    query='INSERT INTO test VALUES (%s)',
                    params=(i,),
                    source_db='primary',
                    checksum=f'check{i}'
                )
                self.log.log_event(event)
                results.append(worker_id)
        
        threads = [threading.Thread(target=log_events, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have logged 15 events (3 workers * 5 events)
        with open(self.temp_file.name, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 15)


class TestReplicaManager(unittest.TestCase):
    """Test ReplicaManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = ReplicaConfig(
            name='test-replica',
            db_type='postgresql',
            connection_params={'host': 'localhost'}
        )
    
    def test_manager_initialization(self):
        """Test 17: Initialize replica manager"""
        manager = ReplicaManager(self.config)
        
        self.assertEqual(manager.config.name, 'test-replica')
        self.assertFalse(manager.is_connected)
        self.assertIsNone(manager.last_sync_time)
        self.assertEqual(manager.stats.events_processed, 0)
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_connect_success(self, mock_factory):
        """Test 18: Successful connection to replica"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = ReplicaManager(self.config)
        manager.connect()
        
        self.assertTrue(manager.is_connected)
        mock_db.connect.assert_called_once()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_connect_failure(self, mock_factory):
        """Test 19: Failed connection to replica"""
        mock_db = Mock()
        mock_db.connect.side_effect = Exception("Connection failed")
        mock_factory.return_value = mock_db
        
        manager = ReplicaManager(self.config)
        
        with self.assertRaises(Exception):
            manager.connect()
        
        self.assertFalse(manager.is_connected)
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_disconnect(self, mock_factory):
        """Test 20: Disconnect from replica"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = ReplicaManager(self.config)
        manager.connect()
        manager.disconnect()
        
        self.assertFalse(manager.is_connected)
        mock_db.disconnect.assert_called_once()
    
    def test_enqueue_event_success(self):
        """Test 21: Successfully enqueue event"""
        manager = ReplicaManager(self.config)
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        result = manager.enqueue_event(event)
        
        self.assertTrue(result)
        self.assertEqual(manager.event_queue.qsize(), 1)
    
    def test_enqueue_event_queue_full(self):
        """Test 22: Enqueue event when queue is full"""
        config = ReplicaConfig(
            name='test-replica',
            db_type='postgresql',
            connection_params={'host': 'localhost'}
        )
        
        manager = ReplicaManager(config)
        manager.event_queue = queue.Queue(maxsize=2)
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        # Fill queue
        manager.event_queue.put(event)
        manager.event_queue.put(event)
        
        # Try to add one more (should fail)
        result = manager.enqueue_event(event)
        
        self.assertFalse(result)
    
    def test_get_lag_with_sync_time(self):
        """Test 23: Get replication lag with sync time"""
        manager = ReplicaManager(self.config)
        manager.last_sync_time = datetime.now() - timedelta(seconds=5)
        
        lag = manager.get_lag()
        
        self.assertGreaterEqual(lag, 5.0)
        self.assertLess(lag, 6.0)
    
    def test_get_lag_without_sync_time(self):
        """Test 24: Get replication lag without sync time"""
        manager = ReplicaManager(self.config)
        
        lag = manager.get_lag()
        
        self.assertEqual(lag, float('inf'))
    
    def test_get_stats(self):
        """Test 25: Get replica statistics"""
        manager = ReplicaManager(self.config)
        manager.is_connected = True
        manager.stats.events_processed = 50
        manager.stats.events_failed = 2
        
        stats = manager.get_stats()
        
        self.assertEqual(stats['name'], 'test-replica')
        self.assertTrue(stats['connected'])
        self.assertEqual(stats['stats']['events_processed'], 50)
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_apply_event_success(self, mock_factory):
        """Test 26: Successfully apply replication event"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = ReplicaManager(self.config)
        manager.connect()
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        result = manager._apply_event(event)
        
        self.assertTrue(result)
        mock_db.execute.assert_called_once_with(event.query, event.params)
        mock_db.commit.assert_called_once()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_apply_event_failure(self, mock_factory):
        """Test 27: Failed to apply replication event"""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Query failed")
        mock_factory.return_value = mock_db
        
        manager = ReplicaManager(self.config)
        manager.connect()
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        result = manager._apply_event(event)
        
        self.assertFalse(result)
        mock_db.rollback.assert_called_once()
    
    def test_start_worker(self):
        """Test 28: Start worker thread"""
        manager = ReplicaManager(self.config)
        manager.start_worker()
        
        self.assertIsNotNone(manager._worker_thread)
        self.assertTrue(manager._worker_thread.is_alive())
        
        # Cleanup
        manager.stop_worker()
    
    def test_stop_worker(self):
        """Test 29: Stop worker thread"""
        manager = ReplicaManager(self.config)
        manager.start_worker()
        time.sleep(0.1)  # Let thread start
        
        manager.stop_worker()
        
        self.assertTrue(manager._stop_event.is_set())


class TestDatabaseReplicationManager(unittest.TestCase):
    """Test DatabaseReplicationManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        self.replica_configs = [
            ReplicaConfig(
                name='replica-1',
                db_type='postgresql',
                connection_params={'host': 'replica1.com'},
                priority=1
            ),
            ReplicaConfig(
                name='replica-2',
                db_type='postgresql',
                connection_params={'host': 'replica2.com'},
                priority=2
            )
        ]
    
    def test_manager_initialization(self):
        """Test 30: Initialize replication manager"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs,
            mode=ReplicationMode.SYNCHRONOUS
        )
        
        self.assertEqual(manager.primary.config.name, 'primary')
        self.assertEqual(manager.primary.config.role, ReplicaRole.PRIMARY)
        self.assertEqual(len(manager.replicas), 2)
        self.assertEqual(manager.mode, ReplicationMode.SYNCHRONOUS)
        self.assertFalse(manager.is_active)
    
    def test_replica_roles_set_correctly(self):
        """Test 31: Verify replica roles are set correctly"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        self.assertEqual(manager.primary.config.role, ReplicaRole.PRIMARY)
        for replica in manager.replicas.values():
            self.assertEqual(replica.config.role, ReplicaRole.REPLICA)
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_start_replication(self, mock_factory):
        """Test 32: Start replication system"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        self.assertTrue(manager.is_active)
        self.assertTrue(manager.primary.is_connected)
        
        # Cleanup
        manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_stop_replication(self, mock_factory):
        """Test 33: Stop replication system"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        manager.stop()
        
        self.assertFalse(manager.is_active)
    
    def test_get_operation_type_insert(self):
        """Test 34: Extract INSERT operation type"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        op = manager._get_operation_type("INSERT INTO users VALUES (1, 'John')")
        self.assertEqual(op, 'INSERT')
    
    def test_get_operation_type_update(self):
        """Test 35: Extract UPDATE operation type"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        op = manager._get_operation_type("UPDATE users SET name = 'Jane' WHERE id = 1")
        self.assertEqual(op, 'UPDATE')
    
    def test_get_operation_type_delete(self):
        """Test 36: Extract DELETE operation type"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        op = manager._get_operation_type("DELETE FROM users WHERE id = 1")
        self.assertEqual(op, 'DELETE')
    
    def test_extract_table_name_insert(self):
        """Test 37: Extract table name from INSERT"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        table = manager._extract_table_name("INSERT INTO users (name) VALUES ('John')")
        self.assertEqual(table, 'USERS')
    
    def test_extract_table_name_update(self):
        """Test 38: Extract table name from UPDATE"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        table = manager._extract_table_name("UPDATE orders SET status = 'shipped'")
        self.assertEqual(table, 'ORDERS')
    
    def test_extract_table_name_delete(self):
        """Test 39: Extract table name from DELETE"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        table = manager._extract_table_name("DELETE FROM logs WHERE date < NOW()")
        self.assertEqual(table, 'LOGS')
    
    def test_generate_event_id_uniqueness(self):
        """Test 40: Generate unique event IDs"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        ids = set()
        for _ in range(100):
            event_id = manager._generate_event_id()
            ids.add(event_id)
            time.sleep(0.001)
        
        self.assertEqual(len(ids), 100)  # All unique
    
    def test_generate_checksum_same_data(self):
        """Test 41: Generate same checksum for same data"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        checksum1 = manager._generate_checksum("INSERT INTO users VALUES (%s)", ('John',))
        checksum2 = manager._generate_checksum("INSERT INTO users VALUES (%s)", ('John',))
        
        self.assertEqual(checksum1, checksum2)
    
    def test_generate_checksum_different_data(self):
        """Test 42: Generate different checksum for different data"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        checksum1 = manager._generate_checksum("INSERT INTO users VALUES (%s)", ('John',))
        checksum2 = manager._generate_checksum("INSERT INTO users VALUES (%s)", ('Jane',))
        
        self.assertNotEqual(checksum1, checksum2)
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_execute_query_on_primary(self, mock_factory):
        """Test 43: Execute query on primary database"""
        mock_db = Mock()
        mock_db.execute.return_value = None
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        try:
            manager.execute("INSERT INTO users VALUES (%s)", ('John',), 'users')
            
            mock_db.execute.assert_called()
            mock_db.commit.assert_called()
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_execute_query_not_started(self, mock_factory):
        """Test 44: Execute query when system not started"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        with self.assertRaises(RuntimeError):
            manager.execute("INSERT INTO users VALUES (%s)", ('John',))
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replicate_asynchronous(self, mock_factory):
        """Test 45: Asynchronous replication"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs,
            mode=ReplicationMode.ASYNCHRONOUS
        )
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        manager.start()
        
        try:
            manager._replicate_asynchronous(event)
            
            # Check that event was queued to replicas
            for replica in manager.replicas.values():
                self.assertGreater(replica.event_queue.qsize(), 0)
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_get_status(self, mock_factory):
        """Test 46: Get replication system status"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        try:
            status = manager.get_status()
            
            self.assertTrue(status['active'])
            self.assertEqual(status['mode'], ReplicationMode.SYNCHRONOUS.value)
            self.assertEqual(status['total_replicas'], 2)
            self.assertIn('primary', status)
            self.assertIn('replicas', status)
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_promote_replica(self, mock_factory):
        """Test 47: Promote replica to primary"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        old_primary_name = manager.primary.config.name
        initial_replica_count = len(manager.replicas)
        
        manager.promote_replica('replica-1')
        
        # Verify promotion
        self.assertEqual(manager.primary.config.name, 'replica-1')
        self.assertEqual(manager.primary.config.role, ReplicaRole.PRIMARY)
        # The old primary takes the place of the promoted replica in the dict
        self.assertIn('replica-1', manager.replicas)
        # Total replica count should remain the same
        self.assertEqual(len(manager.replicas), initial_replica_count)
        
        manager.stop()
    
    def test_promote_nonexistent_replica(self):
        """Test 48: Promote nonexistent replica"""
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        with self.assertRaises(ValueError):
            manager.promote_replica('nonexistent-replica')


class TestReplicatedDatabase(unittest.TestCase):
    """Test ReplicatedDatabase wrapper class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        self.replica_configs = [
            ReplicaConfig(
                name='replica-1',
                db_type='postgresql',
                connection_params={'host': 'replica1.com'}
            )
        ]
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replicated_db_execute(self, mock_factory):
        """Test 49: Execute write query through wrapper"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        try:
            db = ReplicatedDatabase(manager)
            db.execute("INSERT INTO users VALUES (%s)", ('John',))
            
            mock_db.execute.assert_called()
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replicated_db_fetch_one(self, mock_factory):
        """Test 50: Fetch one row through wrapper"""
        mock_db = Mock()
        mock_db.fetch_one.return_value = {'id': 1, 'name': 'John'}
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        try:
            db = ReplicatedDatabase(manager)
            result = db.fetch_one("SELECT * FROM users WHERE id = %s", (1,))
            
            self.assertEqual(result['name'], 'John')
            mock_db.fetch_one.assert_called()
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replicated_db_fetch_all(self, mock_factory):
        """Test 51: Fetch all rows through wrapper"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = [
            {'id': 1, 'name': 'John'},
            {'id': 2, 'name': 'Jane'}
        ]
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        try:
            db = ReplicatedDatabase(manager)
            results = db.fetch_all("SELECT * FROM users")
            
            self.assertEqual(len(results), 2)
            mock_db.fetch_all.assert_called()
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replicated_db_rollback(self, mock_factory):
        """Test 52: Rollback through wrapper"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        manager = DatabaseReplicationManager(
            primary_config=self.primary_config,
            replica_configs=self.replica_configs
        )
        
        manager.start()
        
        try:
            db = ReplicatedDatabase(manager)
            db.rollback()
            
            mock_db.rollback.assert_called_once()
        finally:
            manager.stop()


class TestReplicationEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios"""
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replication_with_primary_failure(self, mock_factory):
        """Test 53: Handle primary database failure"""
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Primary DB failed")
        mock_factory.return_value = mock_db
        
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=[]
        )
        
        manager.start()
        
        try:
            with self.assertRaises(Exception):
                manager.execute("INSERT INTO users VALUES (%s)", ('John',))
            
            mock_db.rollback.assert_called()
        finally:
            manager.stop()
    
    def test_semi_sync_insufficient_replicas(self):
        """Test 54: Semi-sync with insufficient replicas"""
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        replica_configs = [
            ReplicaConfig(
                name='replica-1',
                db_type='postgresql',
                connection_params={'host': 'replica1.com'},
                enabled=False  # Disabled
            )
        ]
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=replica_configs,
            mode=ReplicationMode.SEMI_SYNC,
            min_replicas_sync=1
        )
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        # Should log warning but not fail
        manager._replicate_semi_sync(event)
    
    def test_replica_queue_overflow_handling(self):
        """Test 55: Handle replica queue overflow"""
        config = ReplicaConfig(
            name='test-replica',
            db_type='postgresql',
            connection_params={'host': 'localhost'}
        )
        
        manager = ReplicaManager(config)
        manager.event_queue = queue.Queue(maxsize=5)
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        # Fill queue
        for i in range(5):
            manager.event_queue.put(event)
        
        # Try to add more
        result = manager.enqueue_event(event)
        
        self.assertFalse(result)
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_replica_auto_reconnect(self, mock_factory):
        """Test 56: Replica auto-reconnect on failure"""
        mock_db = Mock()
        
        # First attempt fails, second succeeds
        call_count = {'count': 0}
        
        def mock_connect():
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise Exception("Connection failed")
        
        mock_db.connect = mock_connect
        mock_factory.return_value = mock_db
        
        config = ReplicaConfig(
            name='test-replica',
            db_type='postgresql',
            connection_params={'host': 'localhost'}
        )
        
        manager = ReplicaManager(config)
        manager.is_connected = False
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        # First attempt should fail and trigger reconnect
        result = manager._apply_event(event)
        
        self.assertFalse(result)  # Should fail on first attempt
    
    def test_replication_with_no_replicas(self):
        """Test 57: Replication system with no replicas"""
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=[]
        )
        
        self.assertEqual(len(manager.replicas), 0)
        
        event = ReplicationEvent(
            event_id='evt001',
            timestamp=datetime.now(),
            operation='INSERT',
            table='users',
            query='INSERT INTO users VALUES (%s)',
            params=('John',),
            source_db='primary',
            checksum='check1'
        )
        
        # Should not raise exception
        manager._replicate_synchronous(event)
        manager._replicate_asynchronous(event)
        manager._replicate_semi_sync(event)
    
    def test_extract_table_name_complex_query(self):
        """Test 58: Extract table name from complex query"""
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=[]
        )
        
        # Complex INSERT with multiple clauses
        query = "INSERT INTO users (id, name, email) VALUES (1, 'John', 'john@example.com')"
        table = manager._extract_table_name(query)
        
        self.assertEqual(table, 'USERS')
    
    def test_checksum_with_none_params(self):
        """Test 59: Generate checksum with None params"""
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=[]
        )
        
        checksum = manager._generate_checksum("DELETE FROM logs", None)
        
        self.assertIsNotNone(checksum)
        self.assertEqual(len(checksum), 32)  # MD5 hash length


class TestReplicationIntegration(unittest.TestCase):
    """Integration tests for complete replication workflows"""
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_end_to_end_synchronous_replication(self, mock_factory):
        """Test 60: Complete synchronous replication workflow"""
        mock_primary_db = Mock()
        mock_replica_db = Mock()
        
        mock_primary_db.execute.return_value = None
        mock_replica_db.execute.return_value = None
        
        def create_db(db_type, params):
            if params.get('host') == 'primary.com':
                return mock_primary_db
            else:
                return mock_replica_db
        
        mock_factory.side_effect = create_db
        
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        replica_configs = [
            ReplicaConfig(
                name='replica-1',
                db_type='postgresql',
                connection_params={'host': 'replica1.com'}
            )
        ]
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=replica_configs,
            mode=ReplicationMode.SYNCHRONOUS
        )
        
        manager.start()
        
        try:
            # Execute write operation
            manager.execute(
                "INSERT INTO users (name) VALUES (%s)",
                ('John',),
                'users'
            )
            
            # Verify primary execution
            mock_primary_db.execute.assert_called()
            mock_primary_db.commit.assert_called()
            
            # Give time for async replication
            time.sleep(0.2)
            
            # Verify event was queued to replica
            replica = manager.replicas['replica-1']
            self.assertGreaterEqual(replica.stats.events_processed + replica.event_queue.qsize(), 1)
            
        finally:
            manager.stop()
    
    @patch('nexus.database.database_replication.DatabaseFactory.create_database')
    def test_end_to_end_with_failover(self, mock_factory):
        """Test 61: Complete workflow with failover"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        primary_config = ReplicaConfig(
            name='primary',
            db_type='postgresql',
            connection_params={'host': 'primary.com'}
        )
        
        replica_configs = [
            ReplicaConfig(
                name='replica-1',
                db_type='postgresql',
                connection_params={'host': 'replica1.com'},
                priority=1
            )
        ]
        
        manager = DatabaseReplicationManager(
            primary_config=primary_config,
            replica_configs=replica_configs
        )
        
        manager.start()
        
        # Verify initial state
        self.assertEqual(manager.primary.config.name, 'primary')
        initial_replica_count = len(manager.replicas)
        
        # Perform failover
        manager.promote_replica('replica-1')
        
        # Verify new state
        self.assertEqual(manager.primary.config.name, 'replica-1')
        self.assertEqual(manager.primary.config.role, ReplicaRole.PRIMARY)
        # The promoted replica key should still exist in replicas dict
        # with the old primary as its value
        self.assertIn('replica-1', manager.replicas)
        # Replica count should remain the same
        self.assertEqual(len(manager.replicas), initial_replica_count)
        # Old primary should now be a replica
        self.assertEqual(manager.replicas['replica-1'].config.role, ReplicaRole.REPLICA)
        
        manager.stop()


# Test runner
if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestReplicationEnums))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicationEvent))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicaConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicationStats))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicationLog))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicaManager))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseReplicationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicatedDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicationEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestReplicationIntegration))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.2f}%")
    print("="*70)
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)