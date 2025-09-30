"""
Comprehensive unit tests for Enterprise Database Migration Tool
50 test cases covering all components and edge cases
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from datetime import datetime
import json
import threading
from queue import Queue
import tempfile
import os
import sys

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)

# Import classes to test
from nexus.database.database_simple_migration import (
    MigrationStrategy,
    MigrationStatus,
    MigrationConfig,
    MigrationStats,
    MigrationCheckpoint,
    DataValidator,
    BaseMigration,
    ChunkedMigration,
    ParallelMigration,
    StreamingMigration,
    MigrationOrchestrator
)


class TestMigrationEnums(unittest.TestCase):
    """Test enum classes"""
    
    def test_migration_strategy_values(self):
        """Test 1: Verify all migration strategy values"""
        self.assertEqual(MigrationStrategy.CHUNKED.value, "chunked")
        self.assertEqual(MigrationStrategy.PARALLEL.value, "parallel")
        self.assertEqual(MigrationStrategy.STREAMING.value, "streaming")
        self.assertEqual(MigrationStrategy.ZERO_DOWNTIME.value, "zero_downtime")
    
    def test_migration_status_values(self):
        """Test 2: Verify all migration status values"""
        self.assertEqual(MigrationStatus.PENDING.value, "pending")
        self.assertEqual(MigrationStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(MigrationStatus.COMPLETED.value, "completed")
        self.assertEqual(MigrationStatus.FAILED.value, "failed")
        self.assertEqual(MigrationStatus.PAUSED.value, "paused")


class TestMigrationConfig(unittest.TestCase):
    """Test MigrationConfig dataclass"""
    
    def test_config_creation_with_defaults(self):
        """Test 3: Create config with default values"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users'
        )
        
        self.assertEqual(config.primary_key, 'id')
        self.assertEqual(config.strategy, MigrationStrategy.CHUNKED)
        self.assertEqual(config.chunk_size, 10000)
        self.assertEqual(config.num_workers, 4)
        self.assertTrue(config.enable_validation)
    
    def test_config_creation_with_custom_values(self):
        """Test 4: Create config with custom values"""
        config = MigrationConfig(
            source_db_type='mysql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='orders',
            target_table='orders_new',
            primary_key='order_id',
            chunk_size=5000,
            num_workers=8,
            enable_validation=False
        )
        
        self.assertEqual(config.primary_key, 'order_id')
        self.assertEqual(config.chunk_size, 5000)
        self.assertEqual(config.num_workers, 8)
        self.assertFalse(config.enable_validation)
    
    def test_config_with_transform_function(self):
        """Test 5: Config with transformation function"""
        def transform(record):
            record['processed'] = True
            return record
        
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            transform_function=transform
        )
        
        self.assertIsNotNone(config.transform_function)
        test_record = {'id': 1}
        result = config.transform_function(test_record)
        self.assertTrue(result['processed'])


class TestMigrationStats(unittest.TestCase):
    """Test MigrationStats dataclass"""
    
    def test_stats_initialization(self):
        """Test 6: Stats initialization with defaults"""
        stats = MigrationStats()
        
        self.assertEqual(stats.total_records, 0)
        self.assertEqual(stats.migrated_records, 0)
        self.assertEqual(stats.failed_records, 0)
        self.assertIsNone(stats.start_time)
        self.assertIsNone(stats.end_time)
        self.assertEqual(len(stats.errors), 0)
    
    def test_stats_to_dict(self):
        """Test 7: Stats conversion to dictionary"""
        stats = MigrationStats(
            total_records=1000,
            migrated_records=900,
            failed_records=10
        )
        stats.start_time = datetime(2025, 1, 1, 12, 0, 0)
        stats.end_time = datetime(2025, 1, 1, 13, 0, 0)
        
        result = stats.to_dict()
        
        self.assertEqual(result['total_records'], 1000)
        self.assertEqual(result['migrated_records'], 900)
        self.assertIn('2025-01-01', result['start_time'])
    
    def test_stats_error_tracking(self):
        """Test 8: Stats error list functionality"""
        stats = MigrationStats()
        
        stats.errors.append({'error': 'Connection failed', 'timestamp': '2025-01-01'})
        stats.errors.append({'error': 'Timeout', 'timestamp': '2025-01-02'})
        
        self.assertEqual(len(stats.errors), 2)
        self.assertEqual(stats.errors[0]['error'], 'Connection failed')


class TestMigrationCheckpoint(unittest.TestCase):
    """Test MigrationCheckpoint class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.checkpoint = MigrationCheckpoint(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test files"""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_save_checkpoint(self):
        """Test 9: Save checkpoint data"""
        data = {'last_id': 5000, 'migrated_records': 4500}
        self.checkpoint.save(data)
        
        with open(self.temp_file.name, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['last_id'], 5000)
        self.assertEqual(saved_data['migrated_records'], 4500)
        self.assertIn('timestamp', saved_data)
    
    def test_load_checkpoint(self):
        """Test 10: Load checkpoint data"""
        data = {'last_id': 3000, 'chunk_number': 30}
        self.checkpoint.save(data)
        
        loaded_data = self.checkpoint.load()
        
        self.assertEqual(loaded_data['last_id'], 3000)
        self.assertEqual(loaded_data['chunk_number'], 30)
    
    def test_load_nonexistent_checkpoint(self):
        """Test 11: Load checkpoint when file doesn't exist"""
        checkpoint = MigrationCheckpoint('nonexistent_file.json')
        result = checkpoint.load()
        
        self.assertIsNone(result)
    
    def test_clear_checkpoint(self):
        """Test 12: Clear checkpoint file"""
        data = {'last_id': 1000}
        self.checkpoint.save(data)
        
        self.checkpoint.clear()
        
        self.assertFalse(os.path.exists(self.temp_file.name))
    
    def test_checkpoint_thread_safety(self):
        """Test 13: Checkpoint thread-safe operations"""
        results = []
        
        def save_data(value):
            self.checkpoint.save({'value': value})
            results.append(value)
        
        threads = [threading.Thread(target=save_data, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not raise any exceptions
        self.assertEqual(len(results), 5)


class TestDataValidator(unittest.TestCase):
    """Test DataValidator class"""
    
    def test_generate_checksum_same_data(self):
        """Test 14: Generate identical checksums for same data"""
        record1 = {'id': 1, 'name': 'John', 'age': 30}
        record2 = {'id': 1, 'name': 'John', 'age': 30}
        
        checksum1 = DataValidator.generate_checksum(record1)
        checksum2 = DataValidator.generate_checksum(record2)
        
        self.assertEqual(checksum1, checksum2)
    
    def test_generate_checksum_different_data(self):
        """Test 15: Generate different checksums for different data"""
        record1 = {'id': 1, 'name': 'John'}
        record2 = {'id': 2, 'name': 'Jane'}
        
        checksum1 = DataValidator.generate_checksum(record1)
        checksum2 = DataValidator.generate_checksum(record2)
        
        self.assertNotEqual(checksum1, checksum2)
    
    def test_generate_checksum_key_order_independence(self):
        """Test 16: Checksums ignore key order"""
        record1 = {'name': 'John', 'id': 1, 'age': 30}
        record2 = {'id': 1, 'age': 30, 'name': 'John'}
        
        checksum1 = DataValidator.generate_checksum(record1)
        checksum2 = DataValidator.generate_checksum(record2)
        
        self.assertEqual(checksum1, checksum2)
    
    def test_validate_record_matching(self):
        """Test 17: Validate matching records"""
        source = {'id': 1, 'name': 'John'}
        target = {'id': 1, 'name': 'John'}
        
        result = DataValidator.validate_record(source, target)
        
        self.assertTrue(result)
    
    def test_validate_record_not_matching(self):
        """Test 18: Validate non-matching records"""
        source = {'id': 1, 'name': 'John'}
        target = {'id': 1, 'name': 'Jane'}
        
        result = DataValidator.validate_record(source, target)
        
        self.assertFalse(result)
    
    def test_validate_counts_matching(self):
        """Test 19: Validate matching record counts"""
        source_db = Mock()
        target_db = Mock()
        
        source_db.fetch_one.return_value = {'count': 1000}
        target_db.fetch_one.return_value = {'count': 1000}
        
        source_count, target_count, match = DataValidator.validate_counts(
            source_db, target_db, 'users', 'users'
        )
        
        self.assertEqual(source_count, 1000)
        self.assertEqual(target_count, 1000)
        self.assertTrue(match)
    
    def test_validate_counts_not_matching(self):
        """Test 20: Validate non-matching record counts"""
        source_db = Mock()
        target_db = Mock()
        
        source_db.fetch_one.return_value = {'count': 1000}
        target_db.fetch_one.return_value = {'count': 950}
        
        source_count, target_count, match = DataValidator.validate_counts(
            source_db, target_db, 'users', 'users'
        )
        
        self.assertEqual(source_count, 1000)
        self.assertEqual(target_count, 950)
        self.assertFalse(match)
    
    def test_validate_counts_with_where_clause(self):
        """Test 21: Validate counts with WHERE clause"""
        source_db = Mock()
        target_db = Mock()
        
        source_db.fetch_one.return_value = {'count': 500}
        target_db.fetch_one.return_value = {'count': 500}
        
        DataValidator.validate_counts(
            source_db, target_db, 'users', 'users', 'active = true'
        )
        
        # Verify WHERE clause was included in queries
        call_args = source_db.fetch_one.call_args[0][0]
        self.assertIn('WHERE active = true', call_args)


class TestBaseMigration(unittest.TestCase):
    """Test BaseMigration class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users'
        )
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_create_connections(self, mock_factory):
        """Test 22: Create database connections"""
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = [mock_source, mock_target]
        
        migration = BaseMigration(self.config)
        source_db, target_db = migration._create_connections()
        
        self.assertEqual(mock_factory.call_count, 2)
        mock_source.connect.assert_called_once()
        mock_target.connect.assert_called_once()
    
    def test_initial_status(self):
        """Test 23: Initial migration status"""
        migration = BaseMigration(self.config)
        
        self.assertEqual(migration.status, MigrationStatus.PENDING)
        self.assertFalse(migration.stop_requested)
    
    def test_get_total_records(self):
        """Test 24: Get total record count"""
        mock_db = Mock()
        mock_db.fetch_one.return_value = {'total': 10000}
        
        migration = BaseMigration(self.config)
        total = migration._get_total_records(mock_db)
        
        self.assertEqual(total, 10000)
    
    def test_get_total_records_with_where_clause(self):
        """Test 25: Get total records with WHERE clause"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            where_clause='active = true'
        )
        
        mock_db = Mock()
        mock_db.fetch_one.return_value = {'total': 5000}
        
        migration = BaseMigration(config)
        migration._get_total_records(mock_db)
        
        call_args = mock_db.fetch_one.call_args[0][0]
        self.assertIn('WHERE active = true', call_args)
    
    def test_get_id_range(self):
        """Test 26: Get min and max ID range"""
        mock_db = Mock()
        mock_db.fetch_one.return_value = {'min_id': 1, 'max_id': 10000}
        
        migration = BaseMigration(self.config)
        min_id, max_id = migration._get_id_range(mock_db)
        
        self.assertEqual(min_id, 1)
        self.assertEqual(max_id, 10000)
    
    def test_transform_records_no_function(self):
        """Test 27: Transform records without transform function"""
        migration = BaseMigration(self.config)
        records = [{'id': 1}, {'id': 2}]
        
        result = migration._transform_records(records)
        
        self.assertEqual(result, records)
    
    def test_transform_records_with_function(self):
        """Test 28: Transform records with transform function"""
        def add_flag(record):
            record['processed'] = True
            return record
        
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            transform_function=add_flag
        )
        
        migration = BaseMigration(config)
        records = [{'id': 1}, {'id': 2}]
        
        result = migration._transform_records(records)
        
        self.assertTrue(all(r['processed'] for r in result))
    
    def test_insert_batch_success(self):
        """Test 29: Successful batch insert"""
        mock_db = Mock()
        mock_db.transaction.return_value.__enter__ = Mock()
        mock_db.transaction.return_value.__exit__ = Mock()
        
        migration = BaseMigration(self.config)
        records = [{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]
        
        result = migration._insert_batch(mock_db, records)
        
        self.assertTrue(result)
        mock_db.execute_many.assert_called_once()
    
    def test_insert_batch_empty_records(self):
        """Test 30: Insert batch with empty records"""
        mock_db = Mock()
        
        migration = BaseMigration(self.config)
        result = migration._insert_batch(mock_db, [])
        
        self.assertTrue(result)
        mock_db.execute_many.assert_not_called()
    
    def test_insert_batch_with_retry(self):
        """Test 31: Insert batch with retry on failure"""
        mock_db = Mock()
        
        # First call raises exception, second succeeds
        call_count = {'count': 0}
        
        def mock_transaction():
            return mock_db.transaction.return_value
        
        def mock_execute_many(query, params):
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise Exception("Connection lost")
            return None
        
        mock_db.transaction.return_value.__enter__ = Mock(return_value=None)
        mock_db.transaction.return_value.__exit__ = Mock(return_value=None)
        mock_db.execute_many = Mock(side_effect=mock_execute_many)
        
        migration = BaseMigration(self.config)
        records = [{'id': 1, 'name': 'John'}]
        
        with patch('time.sleep'):  # Speed up test
            result = migration._insert_batch(mock_db, records)
        
        self.assertTrue(result)
        self.assertEqual(call_count['count'], 2)
    
    def test_insert_batch_max_retries_exceeded(self):
        """Test 32: Insert batch fails after max retries"""
        mock_db = Mock()
        
        def mock_execute_many(query, params):
            raise Exception("Connection lost")
        
        mock_db.transaction.return_value.__enter__ = Mock(return_value=None)
        mock_db.transaction.return_value.__exit__ = Mock(return_value=None)
        mock_db.execute_many = Mock(side_effect=mock_execute_many)
        
        migration = BaseMigration(self.config)
        records = [{'id': 1, 'name': 'John'}]
        
        with patch('time.sleep'):
            result = migration._insert_batch(mock_db, records)
        
        self.assertFalse(result)
        self.assertEqual(len(migration.stats.errors), 1)
        # Should have tried max_retries + 1 times (initial + 3 retries = 4 total)
        self.assertEqual(mock_db.execute_many.call_count, 4)
    
    def test_update_progress(self):
        """Test 33: Update progress statistics"""
        migration = BaseMigration(self.config)
        start_time = 1000.0
        
        with patch('time.time', return_value=1100.0):
            migration._update_progress(500, 1000, start_time)
        
        self.assertEqual(migration.stats.migrated_records, 500)
        self.assertEqual(migration.stats.elapsed_seconds, 100.0)
        self.assertGreater(migration.stats.current_rate, 0)
    
    def test_save_checkpoint_enabled(self):
        """Test 34: Save checkpoint when enabled"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            enable_checkpoints=True
        )
        
        migration = BaseMigration(config)
        migration.checkpoint.save = Mock()
        
        migration._save_checkpoint({'last_id': 5000})
        
        migration.checkpoint.save.assert_called_once()
    
    def test_save_checkpoint_disabled(self):
        """Test 35: Don't save checkpoint when disabled"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            enable_checkpoints=False
        )
        
        migration = BaseMigration(config)
        migration.checkpoint.save = Mock()
        
        migration._save_checkpoint({'last_id': 5000})
        
        migration.checkpoint.save.assert_not_called()


class TestChunkedMigration(unittest.TestCase):
    """Test ChunkedMigration class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            chunk_size=100
        )
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_execute_successful_migration(self, mock_factory):
        """Test 36: Execute successful chunked migration"""
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = [mock_source, mock_target]
        
        # Setup mock responses
        mock_source.fetch_one.side_effect = [
            {'total': 250},  # Total records
            {'min_id': 1, 'max_id': 250}  # ID range
        ]
        
        # Simulate three chunks of data
        mock_source.fetch_all.side_effect = [
            [{'id': i} for i in range(1, 101)],
            [{'id': i} for i in range(101, 201)],
            [{'id': i} for i in range(201, 251)],
            []
        ]
        
        mock_target.transaction.return_value.__enter__ = Mock()
        mock_target.transaction.return_value.__exit__ = Mock()
        
        migration = ChunkedMigration(self.config)
        
        with patch.object(migration, '_validate_migration', return_value=True):
            stats = migration.execute()
        
        self.assertEqual(stats.migrated_records, 250)
        self.assertEqual(migration.status, MigrationStatus.COMPLETED)
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_execute_with_stop_signal(self, mock_factory):
        """Test 37: Execute migration with stop signal"""
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = [mock_source, mock_target]
        
        mock_source.fetch_one.side_effect = [
            {'total': 1000},
            {'min_id': 1, 'max_id': 1000}
        ]
        
        migration = ChunkedMigration(self.config)
        migration.stop_requested = True
        
        stats = migration.execute()
        
        self.assertEqual(migration.status, MigrationStatus.PAUSED)


class TestParallelMigration(unittest.TestCase):
    """Test ParallelMigration class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            num_workers=2,
            chunk_size=50
        )
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_execute_parallel_migration(self, mock_factory):
        """Test 38: Execute parallel migration"""
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = [mock_source, mock_target] * 10
        
        mock_source.fetch_one.side_effect = [
            {'total': 200},
            {'min_id': 1, 'max_id': 200}
        ] * 5
        
        mock_source.fetch_all.return_value = []
        mock_target.transaction.return_value.__enter__ = Mock()
        mock_target.transaction.return_value.__exit__ = Mock()
        
        migration = ParallelMigration(self.config)
        
        with patch.object(migration, '_validate_migration', return_value=True):
            stats = migration.execute()
        
        self.assertEqual(migration.status, MigrationStatus.COMPLETED)


class TestStreamingMigration(unittest.TestCase):
    """Test StreamingMigration class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            batch_size=50
        )
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_execute_streaming_migration(self, mock_factory):
        """Test 39: Execute streaming migration"""
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = [mock_source, mock_target]
        
        mock_source.fetch_one.return_value = {'total': 150}
        mock_source.fetch_all.return_value = [{'id': i} for i in range(150)]
        
        mock_target.transaction.return_value.__enter__ = Mock()
        mock_target.transaction.return_value.__exit__ = Mock()
        
        migration = StreamingMigration(self.config)
        
        with patch.object(migration, '_validate_migration', return_value=True):
            stats = migration.execute()
        
        self.assertEqual(stats.migrated_records, 150)
        self.assertEqual(migration.status, MigrationStatus.COMPLETED)


class TestMigrationOrchestrator(unittest.TestCase):
    """Test MigrationOrchestrator class"""
    
    def test_orchestrator_chunked_strategy(self):
        """Test 40: Orchestrator with chunked strategy"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            strategy=MigrationStrategy.CHUNKED
        )
        
        orchestrator = MigrationOrchestrator(config)
        
        with patch.object(ChunkedMigration, 'execute') as mock_execute:
            mock_execute.return_value = MigrationStats(total_records=100, migrated_records=100)
            stats = orchestrator.execute()
        
        mock_execute.assert_called_once()
        self.assertEqual(stats.migrated_records, 100)
    
    def test_orchestrator_parallel_strategy(self):
        """Test 41: Orchestrator with parallel strategy"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            strategy=MigrationStrategy.PARALLEL
        )
        
        orchestrator = MigrationOrchestrator(config)
        
        with patch.object(ParallelMigration, 'execute') as mock_execute:
            mock_execute.return_value = MigrationStats(total_records=100, migrated_records=100)
            orchestrator.execute()
        
        mock_execute.assert_called_once()
    
    def test_orchestrator_streaming_strategy(self):
        """Test 42: Orchestrator with streaming strategy"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            strategy=MigrationStrategy.STREAMING
        )
        
        orchestrator = MigrationOrchestrator(config)
        
        with patch.object(StreamingMigration, 'execute') as mock_execute:
            mock_execute.return_value = MigrationStats(total_records=100, migrated_records=100)
            orchestrator.execute()
        
        mock_execute.assert_called_once()
    
    def test_orchestrator_unsupported_strategy(self):
        """Test 43: Orchestrator with unsupported strategy"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            strategy=MigrationStrategy.ZERO_DOWNTIME
        )
        
        orchestrator = MigrationOrchestrator(config)
        
        with self.assertRaises(ValueError):
            orchestrator.execute()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_generate_report(self, mock_json_dump, mock_file):
        """Test 44: Generate migration report"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users'
        )
        
        stats = MigrationStats(total_records=1000, migrated_records=1000)
        stats.elapsed_seconds = 60.0
        stats.average_rate = 16.67
        
        orchestrator = MigrationOrchestrator(config)
        orchestrator._generate_report(stats)
        
        mock_json_dump.assert_called_once()
        report_data = mock_json_dump.call_args[0][0]
        self.assertIn('configuration', report_data)
        self.assertIn('statistics', report_data)
        self.assertIn('summary', report_data)


class TestMigrationEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios"""
    
    def test_migration_with_zero_records(self):
        """Test 45: Migration with zero records"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='empty_table',
            target_table='empty_table'
        )
        
        migration = BaseMigration(config)
        mock_db = Mock()
        mock_db.fetch_one.return_value = {'total': 0}
        
        total = migration._get_total_records(mock_db)
        
        self.assertEqual(total, 0)
    
    def test_migration_with_null_ids(self):
        """Test 46: Handle NULL IDs gracefully"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users'
        )
        
        migration = BaseMigration(config)
        mock_db = Mock()
        mock_db.fetch_one.return_value = {'min_id': None, 'max_id': None}
        
        min_id, max_id = migration._get_id_range(mock_db)
        
        self.assertIsNone(min_id)
        self.assertIsNone(max_id)
    
    def test_checkpoint_with_special_characters(self):
        """Test 47: Checkpoint with special characters in data"""
        checkpoint = MigrationCheckpoint('test_checkpoint.json')
        
        data = {
            'last_id': 5000,
            'special': "String with 'quotes' and \"double quotes\" and \n newlines"
        }
        
        try:
            checkpoint.save(data)
            loaded = checkpoint.load()
            
            self.assertEqual(loaded['last_id'], 5000)
            self.assertIn('special', loaded)
        finally:
            checkpoint.clear()
    
    def test_transform_function_exception_handling(self):
        """Test 48: Handle exceptions in transform function"""
        def faulty_transform(record):
            if record['id'] == 5:
                raise ValueError("Transform failed")
            return record
        
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            transform_function=faulty_transform
        )
        
        migration = BaseMigration(config)
        records = [{'id': 1}, {'id': 5}, {'id': 10}]
        
        with self.assertRaises(ValueError):
            migration._transform_records(records)
    
    def test_concurrent_checkpoint_access(self):
        """Test 49: Concurrent checkpoint file access"""
        checkpoint = MigrationCheckpoint('concurrent_test.json')
        results = []
        
        def concurrent_save(worker_id):
            for i in range(5):
                checkpoint.save({'worker_id': worker_id, 'iteration': i})
                loaded = checkpoint.load()
                results.append(loaded is not None)
        
        try:
            threads = [threading.Thread(target=concurrent_save, args=(i,)) 
                      for i in range(3)]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # All saves should succeed
            self.assertTrue(all(results))
        finally:
            checkpoint.clear()
    
    def test_large_batch_insert(self):
        """Test 50: Insert very large batch of records"""
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            source_table='users',
            target_table='users',
            batch_size=10000
        )
        
        mock_db = Mock()
        mock_db.transaction.return_value.__enter__ = Mock()
        mock_db.transaction.return_value.__exit__ = Mock()
        
        migration = BaseMigration(config)
        
        # Create large batch
        large_batch = [{'id': i, 'name': f'User{i}'} for i in range(10000)]
        
        result = migration._insert_batch(mock_db, large_batch)
        
        self.assertTrue(result)
        mock_db.execute_many.assert_called_once()
        
        # Verify correct number of parameters
        call_args = mock_db.execute_many.call_args[0]
        self.assertEqual(len(call_args[1]), 10000)


class TestMigrationIntegration(unittest.TestCase):
    """Integration tests for complete migration workflows"""
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_end_to_end_chunked_migration(self, mock_factory):
        """Integration Test: Complete chunked migration workflow"""
        # Setup mocks
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = lambda db_type, params: mock_source if params.get('host') == 'source' else mock_target
        
        # Configure source responses
        mock_source.fetch_one.side_effect = [
            {'total': 250},
            {'min_id': 1, 'max_id': 250},
            {'count': 250}  # Validation count
        ]
        
        # Simulate data chunks
        mock_source.fetch_all.side_effect = [
            [{'id': i, 'name': f'User{i}'} for i in range(1, 101)],
            [{'id': i, 'name': f'User{i}'} for i in range(101, 201)],
            [{'id': i, 'name': f'User{i}'} for i in range(201, 251)],
            []
        ]
        
        # Configure target responses
        mock_target.fetch_one.return_value = {'count': 250}
        mock_target.transaction.return_value.__enter__ = Mock()
        mock_target.transaction.return_value.__exit__ = Mock()
        
        # Create config and execute
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            source_table='users',
            target_table='users',
            chunk_size=100,
            enable_validation=True,
            enable_checkpoints=False
        )
        
        orchestrator = MigrationOrchestrator(config)
        stats = orchestrator.execute()
        
        # Assertions
        self.assertEqual(stats.total_records, 250)
        self.assertEqual(stats.migrated_records, 250)
        self.assertEqual(stats.failed_records, 0)
    
    @patch('nexus.database.database_simple_migration.DatabaseFactory.create_database')
    def test_end_to_end_with_transformation(self, mock_factory):
        """Integration Test: Migration with data transformation"""
        mock_source = Mock()
        mock_target = Mock()
        mock_factory.side_effect = lambda db_type, params: mock_source if params.get('host') == 'source' else mock_target
        
        # Define transformation
        def uppercase_names(record):
            record['name'] = record['name'].upper()
            return record
        
        mock_source.fetch_one.side_effect = [
            {'total': 3},
            {'min_id': 1, 'max_id': 3},
            {'count': 3}
        ]
        
        mock_source.fetch_all.side_effect = [
            [
                {'id': 1, 'name': 'john'},
                {'id': 2, 'name': 'jane'},
                {'id': 3, 'name': 'bob'}
            ],
            []
        ]
        
        mock_target.fetch_one.return_value = {'count': 3}
        mock_target.transaction.return_value.__enter__ = Mock()
        mock_target.transaction.return_value.__exit__ = Mock()
        
        captured_records = []
        
        def capture_insert(query, params_list):
            captured_records.extend(params_list)
        
        mock_target.execute_many.side_effect = capture_insert
        
        config = MigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            source_table='users',
            target_table='users',
            chunk_size=100,
            transform_function=uppercase_names,
            enable_validation=True,
            enable_checkpoints=False
        )
        
        orchestrator = MigrationOrchestrator(config)
        stats = orchestrator.execute()
        
        # Verify transformations were applied
        self.assertEqual(stats.migrated_records, 3)
        self.assertTrue(all(name[1].isupper() for name in captured_records if len(name) > 1))


# Test runner
if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationEnums))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationStats))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationCheckpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestBaseMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestChunkedMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestParallelMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestStreamingMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationIntegration))
    
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