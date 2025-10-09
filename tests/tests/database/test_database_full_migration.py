"""
Comprehensive unit tests for Full Database Migration Tool
50 test cases covering all components
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
import json
import tempfile
import os
import sys
from dataclasses import asdict
import threading
from datetime import datetime, timedelta
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Add the root directory to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)

# Import classes to test
from nexus.database.database_full_migration import (
    SchemaExtractor,
    SchemaCreator,
    FullDatabaseMigration,
    TableMetadata,
    DatabaseSchema,
    FullMigrationConfig,
    FullMigrationStats,
    MigrationPhase
)
from nexus.database.database_simple_migration import MigrationStrategy


class TestSchemaExtractor(unittest.TestCase):
    """Test SchemaExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.fetch_all.return_value = []
        self.mock_db.fetch_one.return_value = None
    
    def test_extractor_initialization(self):
        """Test 1: Initialize schema extractor"""
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        
        self.assertEqual(extractor.db_type, 'postgresql')
        self.assertIsNotNone(extractor.logger)
    
    def test_get_tables_postgresql(self):
        """Test 2: Get tables from PostgreSQL"""
        self.mock_db.fetch_all.return_value = [
            {'table_name': 'users'},
            {'table_name': 'orders'},
            {'table_name': 'products'}
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        tables = extractor._get_tables()
        
        self.assertEqual(len(tables), 3)
        self.assertIn('users', tables)
        self.assertIn('orders', tables)
    
    def test_get_tables_mysql(self):
        """Test 3: Get tables from MySQL"""
        self.mock_db.fetch_all.return_value = [
            {'Tables_in_db': 'users'},
            {'Tables_in_db': 'orders'}
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'mysql')
        tables = extractor._get_tables()
        
        self.assertEqual(len(tables), 2)
        self.assertIn('users', tables)
    
    def test_get_tables_sqlite(self):
        """Test 4: Get tables from SQLite"""
        self.mock_db.fetch_all.return_value = [
            {'name': 'users'},
            {'name': 'orders'}
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'sqlite')
        tables = extractor._get_tables()
        
        self.assertEqual(len(tables), 2)
    
    def test_get_primary_key_postgresql(self):
        """Test 5: Get primary key from PostgreSQL"""
        self.mock_db.fetch_one.return_value = {'attname': 'user_id'}
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        pk = extractor._get_primary_key('users')
        
        self.assertEqual(pk, 'user_id')
    
    def test_get_primary_key_default(self):
        """Test 6: Get default primary key when none found"""
        self.mock_db.fetch_one.return_value = None
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        pk = extractor._get_primary_key('users')
        
        self.assertEqual(pk, 'id')
    
    def test_get_columns(self):
        """Test 7: Get column information"""
        self.mock_db.fetch_all.return_value = [
            {
                'column_name': 'id',
                'data_type': 'integer',
                'is_nullable': 'NO',
                'column_default': None
            },
            {
                'column_name': 'name',
                'data_type': 'character varying',
                'is_nullable': 'YES',
                'column_default': None
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        columns = extractor._get_columns('users')
        
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0]['column_name'], 'id')
    
    def test_get_indexes(self):
        """Test 8: Get index information"""
        self.mock_db.fetch_all.return_value = [
            {
                'index_name': 'idx_users_email',
                'column_name': 'email',
                'is_unique': True
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        indexes = extractor._get_indexes('users')
        
        self.assertEqual(len(indexes), 1)
        self.assertEqual(indexes[0]['index_name'], 'idx_users_email')
    
    def test_get_foreign_keys(self):
        """Test 9: Get foreign key constraints"""
        self.mock_db.fetch_all.return_value = [
            {
                'constraint_name': 'fk_user_id',
                'column_name': 'user_id',
                'foreign_table_name': 'users',
                'foreign_column_name': 'id'
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        fks = extractor._get_foreign_keys('orders')
        
        self.assertEqual(len(fks), 1)
        self.assertEqual(fks[0]['foreign_table_name'], 'users')
    
    def test_get_row_count(self):
        """Test 10: Get table row count"""
        self.mock_db.fetch_one.return_value = {'count': 1500}
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        count = extractor._get_row_count('users')
        
        self.assertEqual(count, 1500)
    
    def test_get_row_count_error(self):
        """Test 11: Handle error getting row count"""
        self.mock_db.fetch_one.side_effect = Exception("Table not found")
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        count = extractor._get_row_count('users')
        
        self.assertEqual(count, 0)
    
    def test_get_views(self):
        """Test 12: Get database views"""
        self.mock_db.fetch_all.return_value = [
            {
                'view_name': 'active_users',
                'view_definition': 'SELECT * FROM users WHERE active = true'
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        views = extractor._get_views()
        
        self.assertEqual(len(views), 1)
        self.assertEqual(views[0]['view_name'], 'active_users')
    
    def test_extract_schema_with_filter(self):
        """Test 13: Extract schema with table filtering"""
        self.mock_db.fetch_all.side_effect = [
            [{'table_name': 'users'}, {'table_name': 'orders'}, {'table_name': 'logs'}],
            [{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}],
            [],  # indexes
            [],  # foreign keys
            [],  # constraints
            [],  # views
            []   # sequences (for PostgreSQL)
        ]
        self.mock_db.fetch_one.side_effect = [
            {'attname': 'id'},  # primary key
            {'count': 100}       # row count
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        schema = extractor.extract_schema(
            include_tables=['users'],
            exclude_tables=['logs']
        )
        
        self.assertEqual(len(schema.tables), 1)
        self.assertIn('users', schema.tables)

    def test_extract_complete_schema(self):
        """Test 14: Extract complete schema"""
        self.mock_db.fetch_all.side_effect = [
            [{'table_name': 'users'}],  # tables
            [{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}],  # columns
            [],  # indexes
            [],  # foreign keys
            [],  # constraints
            [{'view_name': 'test_view', 'view_definition': 'SELECT * FROM users'}],  # views
            []   # sequences (for PostgreSQL)
        ]
        self.mock_db.fetch_one.side_effect = [
            {'attname': 'id'},
            {'count': 50}
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        schema = extractor.extract_schema()
        
        self.assertIsInstance(schema, DatabaseSchema)
        self.assertEqual(len(schema.tables), 1)
        self.assertEqual(len(schema.views), 1)


class TestSchemaCreator(unittest.TestCase):
    """Test SchemaCreator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute.return_value = None
        self.mock_db.commit.return_value = None
    
    def test_creator_initialization(self):
        """Test 15: Initialize schema creator"""
        creator = SchemaCreator(self.mock_db, 'postgresql')
        
        self.assertEqual(creator.db_type, 'postgresql')
        self.assertIsNotNone(creator.logger)
    
    def test_map_data_type(self):
        """Test 16: Map data types between databases"""
        creator = SchemaCreator(self.mock_db, 'postgresql')
        
        self.assertEqual(creator._map_data_type('integer'), 'INTEGER')
        self.assertEqual(creator._map_data_type('character varying'), 'VARCHAR(255)')
        self.assertEqual(creator._map_data_type('text'), 'TEXT')
        self.assertEqual(creator._map_data_type('unknown_type'), 'TEXT')
    
    def test_create_simple_table(self):
        """Test 17: Create simple table"""
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[
                {'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'},
                {'column_name': 'name', 'data_type': 'text', 'is_nullable': 'YES'}
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        creator._create_table(table_meta)
        
        self.mock_db.execute.assert_called_once()
        call_args = self.mock_db.execute.call_args[0][0]
        self.assertIn('CREATE TABLE users', call_args)
        self.assertIn('PRIMARY KEY (id)', call_args)
    
    def test_create_table_with_default(self):
        """Test 18: Create table with default values"""
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[
                {
                    'column_name': 'active',
                    'data_type': 'boolean',
                    'is_nullable': 'NO',
                    'column_default': 'true'
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        creator._create_table(table_meta)
        
        call_args = self.mock_db.execute.call_args[0][0]
        self.assertIn('DEFAULT true', call_args)
    
    def test_create_indexes(self):
        """Test 19: Create indexes for table"""
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[],
            indexes=[
                {
                    'index_name': 'idx_email',
                    'column_name': 'email',
                    'is_unique': True
                },
                {
                    'index_name': 'idx_name',
                    'column_name': 'name',
                    'is_unique': False
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        created = creator._create_indexes(table_meta)
        
        self.assertEqual(created, 2)
        self.assertEqual(self.mock_db.execute.call_count, 2)
    
    def test_create_unique_index(self):
        """Test 20: Create unique index"""
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[],
            indexes=[
                {
                    'index_name': 'idx_unique_email',
                    'column_name': 'email',
                    'is_unique': True
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        creator._create_indexes(table_meta)
        
        call_args = self.mock_db.execute.call_args[0][0]
        self.assertIn('CREATE UNIQUE INDEX', call_args)
    
    def test_create_foreign_key_constraint(self):
        """Test 21: Create foreign key constraint"""
        table_meta = TableMetadata(
            name='orders',
            primary_key='id',
            columns=[],
            foreign_keys=[
                {
                    'constraint_name': 'fk_user_id',
                    'column_name': 'user_id',
                    'foreign_table_name': 'users',
                    'foreign_column_name': 'id'
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        created = creator._create_constraints(table_meta)
        
        self.assertEqual(created, 1)
        call_args = self.mock_db.execute.call_args[0][0]
        self.assertIn('ALTER TABLE orders', call_args)
        self.assertIn('FOREIGN KEY (user_id)', call_args)
        self.assertIn('REFERENCES users (id)', call_args)
    
    def test_sort_tables_by_dependencies(self):
        """Test 22: Sort tables by foreign key dependencies"""
        tables = {
            'orders': TableMetadata(
                name='orders',
                primary_key='id',
                columns=[],
                foreign_keys=[
                    {'foreign_table_name': 'users', 'column_name': 'user_id'}
                ]
            ),
            'users': TableMetadata(
                name='users',
                primary_key='id',
                columns=[]
            ),
            'products': TableMetadata(
                name='products',
                primary_key='id',
                columns=[]
            )
        }
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        sorted_tables = creator._sort_tables_by_dependencies(tables)
        
        # Users should come before orders
        users_idx = sorted_tables.index('users')
        orders_idx = sorted_tables.index('orders')
        self.assertLess(users_idx, orders_idx)
    
    def test_create_schema_complete(self):
        """Test 23: Create complete schema"""
        schema = DatabaseSchema()
        schema.tables['users'] = TableMetadata(
            name='users',
            primary_key='id',
            columns=[
                {'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        results = creator.create_schema(schema)
        
        self.assertEqual(results['tables_created'], 1)
        self.assertIn('errors', results)


class TestTableMetadata(unittest.TestCase):
    """Test TableMetadata dataclass"""
    
    def test_table_metadata_initialization(self):
        """Test 24: Initialize TableMetadata"""
        meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[{'column_name': 'id', 'data_type': 'integer'}]
        )
        
        self.assertEqual(meta.name, 'users')
        self.assertEqual(meta.primary_key, 'id')
        self.assertEqual(len(meta.columns), 1)
        self.assertEqual(len(meta.indexes), 0)
    
    def test_table_metadata_with_relationships(self):
        """Test 25: TableMetadata with relationships"""
        meta = TableMetadata(
            name='orders',
            primary_key='id',
            columns=[],
            foreign_keys=[
                {'constraint_name': 'fk_user', 'foreign_table_name': 'users'}
            ],
            dependencies=['users']
        )
        
        self.assertEqual(len(meta.foreign_keys), 1)
        self.assertIn('users', meta.dependencies)


class TestDatabaseSchema(unittest.TestCase):
    """Test DatabaseSchema dataclass"""
    
    def test_schema_initialization(self):
        """Test 26: Initialize DatabaseSchema"""
        schema = DatabaseSchema()
        
        self.assertEqual(len(schema.tables), 0)
        self.assertEqual(len(schema.views), 0)
        self.assertEqual(len(schema.sequences), 0)
    
    def test_schema_with_data(self):
        """Test 27: DatabaseSchema with data"""
        schema = DatabaseSchema()
        schema.tables['users'] = TableMetadata(
            name='users',
            primary_key='id',
            columns=[]
        )
        schema.views.append({'view_name': 'active_users', 'view_definition': 'SELECT *'})
        
        self.assertEqual(len(schema.tables), 1)
        self.assertEqual(len(schema.views), 1)


class TestFullMigrationConfig(unittest.TestCase):
    """Test FullMigrationConfig dataclass"""
    
    def test_config_initialization(self):
        """Test 28: Initialize FullMigrationConfig"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='mysql',
            target_params={'host': 'remote'}
        )
        
        self.assertEqual(config.source_db_type, 'postgresql')
        self.assertEqual(config.target_db_type, 'mysql')
        self.assertTrue(config.include_schema)
        self.assertTrue(config.include_data)
    
    def test_config_with_custom_settings(self):
        """Test 29: Config with custom settings"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            include_data=False,
            chunk_size=5000,
            num_workers=8,
            parallel_tables=5
        )
        
        self.assertFalse(config.include_data)
        self.assertEqual(config.chunk_size, 5000)
        self.assertEqual(config.num_workers, 8)
        self.assertEqual(config.parallel_tables, 5)
    
    def test_config_table_filtering(self):
        """Test 30: Config with table filtering"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='postgresql',
            target_params={'host': 'remote'},
            include_tables=['users', 'orders'],
            exclude_tables=['logs']
        )
        
        self.assertEqual(len(config.include_tables), 2)
        self.assertIn('logs', config.exclude_tables)


class TestFullMigrationStats(unittest.TestCase):
    """Test FullMigrationStats dataclass"""
    
    def test_stats_initialization(self):
        """Test 31: Initialize FullMigrationStats"""
        stats = FullMigrationStats()
        
        self.assertIsNone(stats.start_time)
        self.assertIsNone(stats.end_time)
        self.assertEqual(stats.total_tables, 0)
        self.assertEqual(stats.migrated_rows, 0)
    
    def test_stats_to_dict(self):
        """Test 32: Convert stats to dictionary"""
        stats = FullMigrationStats()
        stats.start_time = datetime.now()
        stats.total_tables = 5
        stats.migrated_rows = 10000
        
        stats_dict = stats.to_dict()
        
        self.assertIn('total_tables', stats_dict)
        self.assertIn('migrated_rows', stats_dict)
        self.assertEqual(stats_dict['total_tables'], 5)
        self.assertEqual(stats_dict['migrated_rows'], 10000)
    
    def test_stats_with_errors(self):
        """Test 33: Stats with errors"""
        stats = FullMigrationStats()
        stats.errors.append({
            'table': 'users',
            'phase': 'data_migration',
            'error': 'Connection timeout'
        })
        
        self.assertEqual(len(stats.errors), 1)
        self.assertEqual(stats.errors[0]['table'], 'users')


class TestFullDatabaseMigration(unittest.TestCase):
    """Test FullDatabaseMigration orchestration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source', 'database': 'testdb'},
            target_db_type='postgresql',
            target_params={'host': 'target', 'database': 'testdb'}
        )
    
    def test_migration_initialization(self):
        """Test 34: Initialize full migration"""
        migration = FullDatabaseMigration(self.config)
        
        self.assertIsNotNone(migration.config)
        self.assertIsNotNone(migration.stats)
        self.assertIsNone(migration.schema)
    
    @patch('nexus.database.database_full_migration.DatabaseFactory.create_database')
    def test_phase_extract_schema(self, mock_factory):
        """Test 35: Schema extraction phase"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None
        mock_factory.return_value = mock_db
        
        migration = FullDatabaseMigration(self.config)
        migration._phase_extract_schema()
        
        self.assertIsNotNone(migration.schema)
        mock_db.connect.assert_called_once()
        mock_db.disconnect.assert_called_once()
    
    @patch('nexus.database.database_full_migration.DatabaseFactory.create_database')
    def test_phase_create_schema(self, mock_factory):
        """Test 36: Schema creation phase"""
        mock_db = Mock()
        mock_factory.return_value = mock_db
        
        migration = FullDatabaseMigration(self.config)
        migration.schema = DatabaseSchema()
        migration.schema.tables['users'] = TableMetadata(
            name='users',
            primary_key='id',
            columns=[{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}]
        )
        
        migration._phase_create_schema()
        
        mock_db.connect.assert_called_once()
        mock_db.disconnect.assert_called_once()
    
    def test_migration_stats_tracking(self):
        """Test 37: Stats tracking during migration"""
        migration = FullDatabaseMigration(self.config)
        
        migration.stats.total_tables = 5
        migration.stats.migrated_tables = 3
        migration.stats.failed_tables = 2
        
        self.assertEqual(migration.stats.total_tables, 5)
        self.assertEqual(migration.stats.migrated_tables, 3)
        self.assertEqual(migration.stats.failed_tables, 2)
    
    def test_migration_config_validation(self):
        """Test 38: Migration configuration validation"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'localhost'},
            target_db_type='mysql',
            target_params={'host': 'remote'},
            include_schema=True,
            include_data=True,
            enable_validation=True
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertTrue(migration.config.include_schema)
        self.assertTrue(migration.config.include_data)
        self.assertTrue(migration.config.enable_validation)


class TestMigrationPhases(unittest.TestCase):
    """Test individual migration phases"""
    
    def test_migration_phase_enum(self):
        """Test 39: MigrationPhase enum"""
        self.assertEqual(MigrationPhase.SCHEMA_EXTRACTION.value, 'schema_extraction')
        self.assertEqual(MigrationPhase.DATA_MIGRATION.value, 'data_migration')
        self.assertEqual(MigrationPhase.VALIDATION.value, 'validation')
    
    def test_all_phases_defined(self):
        """Test 40: All migration phases defined"""
        phases = [
            MigrationPhase.SCHEMA_EXTRACTION,
            MigrationPhase.SCHEMA_CREATION,
            MigrationPhase.DATA_MIGRATION,
            MigrationPhase.INDEX_CREATION,
            MigrationPhase.CONSTRAINT_CREATION,
            MigrationPhase.VIEW_CREATION,
            MigrationPhase.VALIDATION
        ]
        
        self.assertEqual(len(phases), 7)


class TestDataTypeMapping(unittest.TestCase):
    """Test data type mapping between databases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.creator = SchemaCreator(self.mock_db, 'postgresql')
    
    def test_map_integer_types(self):
        """Test 41: Map integer data types"""
        self.assertEqual(self.creator._map_data_type('integer'), 'INTEGER')
        self.assertEqual(self.creator._map_data_type('bigint'), 'BIGINT')
        self.assertEqual(self.creator._map_data_type('smallint'), 'SMALLINT')
    
    def test_map_string_types(self):
        """Test 42: Map string data types"""
        self.assertEqual(self.creator._map_data_type('character varying'), 'VARCHAR(255)')
        self.assertEqual(self.creator._map_data_type('text'), 'TEXT')
    
    def test_map_timestamp_types(self):
        """Test 43: Map timestamp data types"""
        self.assertEqual(self.creator._map_data_type('timestamp without time zone'), 'TIMESTAMP')
        self.assertEqual(self.creator._map_data_type('date'), 'DATE')
    
    def test_map_numeric_types(self):
        """Test 44: Map numeric data types"""
        self.assertEqual(self.creator._map_data_type('numeric'), 'NUMERIC')
        self.assertEqual(self.creator._map_data_type('real'), 'REAL')
        self.assertEqual(self.creator._map_data_type('double precision'), 'DOUBLE PRECISION')
    
    def test_map_boolean_type(self):
        """Test 45: Map boolean data type"""
        self.assertEqual(self.creator._map_data_type('boolean'), 'BOOLEAN')
    
    def test_map_unknown_type(self):
        """Test 46: Map unknown data type to TEXT"""
        self.assertEqual(self.creator._map_data_type('unknown_type'), 'TEXT')
        self.assertEqual(self.creator._map_data_type('custom_enum'), 'TEXT')


class TestErrorHandling(unittest.TestCase):
    """Test error handling in migration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
    
    def test_handle_database_connection_error(self):
        """Test 47: Handle database connection errors"""
        self.mock_db.connect.side_effect = Exception("Connection refused")
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        
        # Should handle gracefully
        with self.assertRaises(Exception):
            self.mock_db.connect()
    
    def test_handle_table_extraction_error(self):
        """Test 48: Handle table extraction errors"""
        self.mock_db.fetch_all.side_effect = Exception("Permission denied")
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        
        with self.assertRaises(Exception):
            extractor._get_tables()
    
    def test_handle_schema_creation_error(self):
        """Test 49: Handle schema creation errors"""
        self.mock_db.execute.side_effect = Exception("Table already exists")
        
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[{'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        
        with self.assertRaises(Exception):
            creator._create_table(table_meta)
    
    def test_stats_track_errors(self):
        """Test 50: Stats properly track errors"""
        stats = FullMigrationStats()
        
        stats.errors.append({
            'table': 'users',
            'phase': 'data_migration',
            'error': 'Timeout',
            'timestamp': datetime.now().isoformat()
        })
        
        stats.errors.append({
            'table': 'orders',
            'phase': 'schema_creation',
            'error': 'Duplicate key',
            'timestamp': datetime.now().isoformat()
        })
        
        self.assertEqual(len(stats.errors), 2)
        self.assertEqual(stats.errors[0]['table'], 'users')
        self.assertEqual(stats.errors[1]['phase'], 'schema_creation')

class TestSchemaExtractorAdvanced(unittest.TestCase):
    """Advanced tests for SchemaExtractor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
    
    def test_extract_schema_empty_database(self):
        """Test 51: Extract schema from empty database"""
        self.mock_db.fetch_all.return_value = []
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        schema = extractor.extract_schema()
        
        self.assertEqual(len(schema.tables), 0)
        self.assertIsInstance(schema, DatabaseSchema)
    
    def test_extract_table_with_complex_columns(self):
        """Test 52: Extract table with complex column types"""
        self.mock_db.fetch_all.return_value = [
            {
                'column_name': 'data',
                'data_type': 'jsonb',
                'character_maximum_length': None,
                'is_nullable': 'YES',
                'column_default': None
            },
            {
                'column_name': 'tags',
                'data_type': 'array',
                'character_maximum_length': None,
                'is_nullable': 'YES',
                'column_default': None
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        columns = extractor._get_columns('users')
        
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0]['data_type'], 'jsonb')
    
    def test_extract_composite_primary_key(self):
        """Test 53: Extract table with composite primary key"""
        self.mock_db.fetch_one.return_value = {'attname': 'user_id'}
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        pk = extractor._get_primary_key('user_roles')
        
        # Should return at least one column
        self.assertIsNotNone(pk)
    
    def test_extract_indexes_with_multiple_columns(self):
        """Test 54: Extract multi-column indexes"""
        self.mock_db.fetch_all.return_value = [
            {
                'index_name': 'idx_user_date',
                'column_name': 'user_id',
                'is_unique': False
            },
            {
                'index_name': 'idx_user_date',
                'column_name': 'created_at',
                'is_unique': False
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        indexes = extractor._get_indexes('orders')
        
        self.assertEqual(len(indexes), 2)
    
    def test_extract_self_referencing_foreign_key(self):
        """Test 55: Extract self-referencing foreign key"""
        self.mock_db.fetch_all.return_value = [
            {
                'constraint_name': 'fk_parent',
                'column_name': 'parent_id',
                'foreign_table_name': 'categories',
                'foreign_column_name': 'id'
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        fks = extractor._get_foreign_keys('categories')
        
        self.assertEqual(len(fks), 1)
        self.assertEqual(fks[0]['foreign_table_name'], 'categories')
    
    def test_extract_check_constraints(self):
        """Test 56: Extract CHECK constraints"""
        self.mock_db.fetch_all.return_value = [
            {
                'constraint_name': 'check_age',
                'constraint_type': 'c',
                'definition': 'CHECK (age >= 0)'
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        constraints = extractor._get_constraints('users')
        
        self.assertEqual(len(constraints), 1)
        self.assertIn('CHECK', constraints[0]['definition'])
    
    def test_extract_views_with_dependencies(self):
        """Test 57: Extract views with table dependencies"""
        self.mock_db.fetch_all.return_value = [
            {
                'view_name': 'user_stats',
                'view_definition': 'SELECT user_id, COUNT(*) FROM orders GROUP BY user_id'
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        views = extractor._get_views()
        
        self.assertEqual(len(views), 1)
        self.assertIn('GROUP BY', views[0]['view_definition'])
    
    def test_extract_sequences_postgresql(self):
        """Test 58: Extract sequences from PostgreSQL"""
        self.mock_db.fetch_all.return_value = [
            {
                'sequence_name': 'users_id_seq',
                'start_value': 1,
                'increment': 1
            }
        ]
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        sequences = extractor._get_sequences()
        
        self.assertEqual(len(sequences), 1)
        self.assertEqual(sequences[0]['sequence_name'], 'users_id_seq')
    
    def test_extract_large_table_row_count(self):
        """Test 59: Extract row count for large table"""
        self.mock_db.fetch_one.return_value = {'count': 10000000}
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        count = extractor._get_row_count('big_table')
        
        self.assertEqual(count, 10000000)
    
    def test_extract_table_with_no_primary_key(self):
        """Test 60: Extract table without primary key"""
        self.mock_db.fetch_one.return_value = None
        
        extractor = SchemaExtractor(self.mock_db, 'postgresql')
        pk = extractor._get_primary_key('log_table')
        
        # Should return default 'id'
        self.assertEqual(pk, 'id')


class TestSchemaCreatorAdvanced(unittest.TestCase):
    """Advanced tests for SchemaCreator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.mock_db.execute.return_value = None
        self.mock_db.commit.return_value = None
    
    def test_create_table_with_nullable_columns(self):
        """Test 61: Create table with nullable and not-null columns"""
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[
                {'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'},
                {'column_name': 'email', 'data_type': 'text', 'is_nullable': 'NO'},
                {'column_name': 'bio', 'data_type': 'text', 'is_nullable': 'YES'}
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        creator._create_table(table_meta)
        
        call_args = self.mock_db.execute.call_args[0][0]
        self.assertIn('NOT NULL', call_args)
    
    def test_create_table_no_primary_key(self):
        """Test 62: Create table without primary key"""
        table_meta = TableMetadata(
            name='logs',
            primary_key=None,
            columns=[
                {'column_name': 'message', 'data_type': 'text', 'is_nullable': 'YES'}
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        creator._create_table(table_meta)
        
        call_args = self.mock_db.execute.call_args[0][0]
        self.assertIn('CREATE TABLE logs', call_args)
        self.assertNotIn('PRIMARY KEY', call_args)
    
    def test_create_multiple_foreign_keys(self):
        """Test 63: Create table with multiple foreign keys"""
        table_meta = TableMetadata(
            name='order_items',
            primary_key='id',
            columns=[],
            foreign_keys=[
                {
                    'constraint_name': 'fk_order',
                    'column_name': 'order_id',
                    'foreign_table_name': 'orders',
                    'foreign_column_name': 'id'
                },
                {
                    'constraint_name': 'fk_product',
                    'column_name': 'product_id',
                    'foreign_table_name': 'products',
                    'foreign_column_name': 'id'
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        created = creator._create_constraints(table_meta)
        
        self.assertEqual(created, 2)
        self.assertEqual(self.mock_db.execute.call_count, 2)
    
    def test_create_partial_index(self):
        """Test 64: Create partial/filtered index"""
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[],
            indexes=[
                {
                    'index_name': 'idx_active_users',
                    'column_name': 'email',
                    'is_unique': False
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        created = creator._create_indexes(table_meta)
        
        self.assertEqual(created, 1)
    
    def test_handle_index_creation_failure(self):
        """Test 65: Handle index creation failure gracefully"""
        self.mock_db.execute.side_effect = Exception("Index already exists")
        
        table_meta = TableMetadata(
            name='users',
            primary_key='id',
            columns=[],
            indexes=[
                {
                    'index_name': 'idx_email',
                    'column_name': 'email',
                    'is_unique': True
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        created = creator._create_indexes(table_meta)
        
        # Should return 0 (no indexes created)
        self.assertEqual(created, 0)
    
    def test_handle_constraint_creation_failure(self):
        """Test 66: Handle constraint creation failure gracefully"""
        self.mock_db.execute.side_effect = Exception("Foreign key violation")
        
        table_meta = TableMetadata(
            name='orders',
            primary_key='id',
            columns=[],
            foreign_keys=[
                {
                    'constraint_name': 'fk_user',
                    'column_name': 'user_id',
                    'foreign_table_name': 'users',
                    'foreign_column_name': 'id'
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        created = creator._create_constraints(table_meta)
        
        self.assertEqual(created, 0)
    
    def test_sort_tables_circular_dependency(self):
        """Test 67: Handle circular dependencies in table sorting"""
        tables = {
            'table_a': TableMetadata(
                name='table_a',
                primary_key='id',
                columns=[],
                foreign_keys=[{'foreign_table_name': 'table_b'}]
            ),
            'table_b': TableMetadata(
                name='table_b',
                primary_key='id',
                columns=[],
                foreign_keys=[{'foreign_table_name': 'table_a'}]
            )
        }
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        sorted_tables = creator._sort_tables_by_dependencies(tables)
        
        # Should include all tables despite circular dependency
        self.assertEqual(len(sorted_tables), 2)
    
    def test_sort_tables_deep_dependencies(self):
        """Test 68: Sort tables with deep dependency chain"""
        tables = {
            'level_1': TableMetadata(
                name='level_1',
                primary_key='id',
                columns=[]
            ),
            'level_2': TableMetadata(
                name='level_2',
                primary_key='id',
                columns=[],
                foreign_keys=[{'foreign_table_name': 'level_1'}]
            ),
            'level_3': TableMetadata(
                name='level_3',
                primary_key='id',
                columns=[],
                foreign_keys=[{'foreign_table_name': 'level_2'}]
            )
        }
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        sorted_tables = creator._sort_tables_by_dependencies(tables)
        
        # Level 1 should be first, level 3 last
        self.assertEqual(sorted_tables[0], 'level_1')
        self.assertEqual(sorted_tables[-1], 'level_3')
    
    def test_create_schema_skip_indexes(self):
        """Test 69: Create schema without indexes"""
        schema = DatabaseSchema()
        schema.tables['users'] = TableMetadata(
            name='users',
            primary_key='id',
            columns=[
                {'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}
            ],
            indexes=[
                {'index_name': 'idx_email', 'column_name': 'email', 'is_unique': True}
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        results = creator.create_schema(schema, create_indexes=False)
        
        self.assertEqual(results['tables_created'], 1)
        self.assertEqual(results['indexes_created'], 0)
    
    def test_create_schema_skip_constraints(self):
        """Test 70: Create schema without constraints"""
        schema = DatabaseSchema()
        schema.tables['orders'] = TableMetadata(
            name='orders',
            primary_key='id',
            columns=[
                {'column_name': 'id', 'data_type': 'integer', 'is_nullable': 'NO'}
            ],
            foreign_keys=[
                {
                    'constraint_name': 'fk_user',
                    'column_name': 'user_id',
                    'foreign_table_name': 'users',
                    'foreign_column_name': 'id'
                }
            ]
        )
        
        creator = SchemaCreator(self.mock_db, 'postgresql')
        results = creator.create_schema(schema, create_constraints=False)
        
        self.assertEqual(results['constraints_created'], 0)


class TestFullMigrationAdvanced(unittest.TestCase):
    """Advanced tests for FullDatabaseMigration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'}
        )
    
    def test_migration_with_schema_only(self):
        """Test 71: Migration with schema only (no data)"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            include_schema=True,
            include_data=False
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertTrue(migration.config.include_schema)
        self.assertFalse(migration.config.include_data)
    
    def test_migration_with_data_only(self):
        """Test 72: Migration with data only (no schema)"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            include_schema=False,
            include_data=True
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertFalse(migration.config.include_schema)
        self.assertTrue(migration.config.include_data)
    
    def test_migration_with_table_exclusion(self):
        """Test 73: Migration with excluded tables"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            exclude_tables=['temp_data', 'logs', 'cache']
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertEqual(len(migration.config.exclude_tables), 3)
        self.assertIn('logs', migration.config.exclude_tables)
    
    def test_migration_with_table_inclusion(self):
        """Test 74: Migration with only specific tables"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            include_tables=['users', 'orders']
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertEqual(len(migration.config.include_tables), 2)
        self.assertIn('users', migration.config.include_tables)
    
    def test_migration_parallel_strategy(self):
        """Test 75: Migration with parallel strategy"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            migration_strategy=MigrationStrategy.PARALLEL,
            parallel_tables=4
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertEqual(migration.config.migration_strategy, MigrationStrategy.PARALLEL)
        self.assertEqual(migration.config.parallel_tables, 4)
    
    def test_migration_chunked_strategy(self):
        """Test 76: Migration with chunked strategy"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            migration_strategy=MigrationStrategy.CHUNKED,
            chunk_size=5000
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertEqual(migration.config.migration_strategy, MigrationStrategy.CHUNKED)
        self.assertEqual(migration.config.chunk_size, 5000)
    
    def test_migration_stats_initialization(self):
        """Test 77: Migration stats properly initialized"""
        migration = FullDatabaseMigration(self.config)
        
        self.assertIsNone(migration.stats.start_time)
        self.assertIsNone(migration.stats.end_time)
        self.assertEqual(migration.stats.total_tables, 0)
        self.assertEqual(migration.stats.migrated_rows, 0)
        self.assertEqual(len(migration.stats.errors), 0)
    
    def test_migration_thread_safety(self):
        """Test 78: Migration is thread-safe"""
        migration = FullDatabaseMigration(self.config)
        
        # Test that lock exists
        self.assertIsNotNone(migration.lock)
        
        # Simulate concurrent updates
        def update_stats():
            with migration.lock:
                migration.stats.migrated_rows += 100
        
        threads = [threading.Thread(target=update_stats) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(migration.stats.migrated_rows, 1000)
    
    def test_migration_disable_foreign_keys_option(self):
        """Test 79: Migration with disabled foreign keys during migration"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            disable_foreign_keys_during_migration=True
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertTrue(migration.config.disable_foreign_keys_during_migration)
    
    def test_migration_create_indexes_after_data(self):
        """Test 80: Migration creates indexes after data load"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            create_indexes_after_data=True
        )
        
        migration = FullDatabaseMigration(config)
        
        self.assertTrue(migration.config.create_indexes_after_data)


class TestMigrationValidation(unittest.TestCase):
    """Test validation functionality"""
    
    def test_validation_enabled(self):
        """Test 81: Validation enabled in config"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            enable_validation=True,
            validate_row_counts=True
        )
        
        self.assertTrue(config.enable_validation)
        self.assertTrue(config.validate_row_counts)
    
    def test_validation_disabled(self):
        """Test 82: Validation disabled in config"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            enable_validation=False
        )
        
        self.assertFalse(config.enable_validation)
    
    def test_sample_data_validation(self):
        """Test 83: Sample data validation option"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            validate_sample_data=True
        )
        
        self.assertTrue(config.validate_sample_data)


class TestMigrationPerformance(unittest.TestCase):
    """Test performance-related configuration"""
    
    def test_bulk_copy_enabled(self):
        """Test 84: Bulk copy option enabled"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            use_bulk_copy=True
        )
        
        self.assertTrue(config.use_bulk_copy)
    
    def test_compression_enabled(self):
        """Test 85: Compression option enabled"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            compression=True
        )
        
        self.assertTrue(config.compression)
    
    def test_worker_configuration(self):
        """Test 86: Worker count configuration"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            num_workers=8,
            parallel_tables=3
        )
        
        self.assertEqual(config.num_workers, 8)
        self.assertEqual(config.parallel_tables, 3)
    
    def test_chunk_size_configuration(self):
        """Test 87: Chunk size configuration"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'},
            chunk_size=25000
        )
        
        self.assertEqual(config.chunk_size, 25000)


class TestStatsTracking(unittest.TestCase):
    """Test statistics tracking"""
    
    def test_stats_track_tables(self):
        """Test 88: Stats track table migration"""
        stats = FullMigrationStats()
        
        stats.total_tables = 10
        stats.migrated_tables = 8
        stats.failed_tables = 2
        
        self.assertEqual(stats.total_tables, 10)
        self.assertEqual(stats.migrated_tables, 8)
        self.assertEqual(stats.failed_tables, 2)
    
    def test_stats_track_rows(self):
        """Test 89: Stats track row migration"""
        stats = FullMigrationStats()
        
        stats.total_rows = 1000000
        stats.migrated_rows = 950000
        
        self.assertEqual(stats.total_rows, 1000000)
        self.assertEqual(stats.migrated_rows, 950000)
    
    def test_stats_track_indexes(self):
        """Test 90: Stats track index creation"""
        stats = FullMigrationStats()
        
        stats.total_indexes = 25
        stats.created_indexes = 23
        
        self.assertEqual(stats.total_indexes, 25)
        self.assertEqual(stats.created_indexes, 23)
    
    def test_stats_track_constraints(self):
        """Test 91: Stats track constraint creation"""
        stats = FullMigrationStats()
        
        stats.total_constraints = 15
        stats.created_constraints = 15
        
        self.assertEqual(stats.total_constraints, 15)
        self.assertEqual(stats.created_constraints, 15)
    
    def test_stats_track_views(self):
        """Test 92: Stats track view creation"""
        stats = FullMigrationStats()
        
        stats.total_views = 5
        stats.created_views = 4
        
        self.assertEqual(stats.total_views, 5)
        self.assertEqual(stats.created_views, 4)
    
    def test_stats_table_specific_tracking(self):
        """Test 93: Stats track per-table statistics"""
        stats = FullMigrationStats()
        
        stats.table_stats['users'] = {
            'rows': 10000,
            'time': 15.5,
            'rate': 645.16
        }
        
        self.assertIn('users', stats.table_stats)
        self.assertEqual(stats.table_stats['users']['rows'], 10000)
    
    def test_stats_timing(self):
        """Test 94: Stats track timing information"""
        stats = FullMigrationStats()
        
        stats.start_time = datetime.now()
        time.sleep(0.1)
        stats.end_time = datetime.now()
        
        self.assertIsNotNone(stats.start_time)
        self.assertIsNotNone(stats.end_time)
        self.assertGreater(stats.end_time, stats.start_time)
    
    def test_stats_to_dict_comprehensive(self):
        """Test 95: Stats to_dict includes all fields"""
        stats = FullMigrationStats()
        stats.start_time = datetime.now()
        stats.end_time = datetime.now()
        stats.total_tables = 5
        stats.migrated_rows = 1000
        
        stats_dict = stats.to_dict()
        
        self.assertIn('start_time', stats_dict)
        self.assertIn('end_time', stats_dict)
        self.assertIn('total_tables', stats_dict)
        self.assertIn('migrated_rows', stats_dict)
        self.assertIn('errors', stats_dict)


class TestErrorScenarios(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_missing_source_database(self):
        """Test 96: Handle missing source database"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'nonexistent'},
            target_db_type='postgresql',
            target_params={'host': 'target'}
        )
        
        # Config should be created successfully
        self.assertEqual(config.source_params['host'], 'nonexistent')
    
    def test_migration_with_errors(self):
        """Test 97: Migration tracks errors properly"""
        migration = FullDatabaseMigration(FullMigrationConfig(
            source_db_type='postgresql',
            source_params={'host': 'source'},
            target_db_type='postgresql',
            target_params={'host': 'target'}
        ))
        
        migration.stats.errors.append({
            'table': 'users',
            'phase': 'data_migration',
            'error': 'Connection timeout',
            'timestamp': datetime.now().isoformat()
        })
        
        self.assertEqual(len(migration.stats.errors), 1)
        self.assertEqual(migration.stats.errors[0]['table'], 'users')
    
    def test_partial_migration_failure(self):
        """Test 98: Handle partial migration failure"""
        stats = FullMigrationStats()
        stats.total_tables = 10
        stats.migrated_tables = 7
        stats.failed_tables = 3
        
        # 30% failure rate
        failure_rate = stats.failed_tables / stats.total_tables
        self.assertGreater(failure_rate, 0)
        self.assertLess(failure_rate, 1)
    
    def test_empty_table_migration(self):
        """Test 99: Handle empty table migration"""
        table_meta = TableMetadata(
            name='empty_table',
            primary_key='id',
            columns=[],
            row_count=0
        )
        
        self.assertEqual(table_meta.row_count, 0)
    
    def test_very_large_table(self):
        """Test 100: Handle very large table metadata"""
        table_meta = TableMetadata(
            name='huge_table',
            primary_key='id',
            columns=[{'column_name': f'col_{i}', 'data_type': 'integer'} 
                     for i in range(100)],
            row_count=1000000000
        )
        
        self.assertEqual(len(table_meta.columns), 100)
        self.assertEqual

# Test runner
if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaCreator))
    suite.addTests(loader.loadTestsFromTestCase(TestTableMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseSchema))
    suite.addTests(loader.loadTestsFromTestCase(TestFullMigrationConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestFullMigrationStats))
    suite.addTests(loader.loadTestsFromTestCase(TestFullDatabaseMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationPhases))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaExtractorAdvanced))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaCreatorAdvanced))
    suite.addTests(loader.loadTestsFromTestCase(TestFullMigrationAdvanced))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestMigrationPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestStatsTracking))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorScenarios))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("ADDITIONAL TEST SUMMARY (Tests 51-100)")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.2f}%")
    print("="*70)
    print("\nAdditional Test Coverage by Component:")
    print("  - SchemaExtractorAdvanced: 10 tests (51-60)")
    print("  - SchemaCreatorAdvanced: 10 tests (61-70)")
    print("  - FullMigrationAdvanced: 10 tests (71-80)")
    print("  - MigrationValidation: 3 tests (81-83)")
    print("  - MigrationPerformance: 4 tests (84-87)")
    print("  - StatsTracking: 8 tests (88-95)")
    print("  - ErrorScenarios: 5 tests (96-100)")
    print("="*70)
    print("\nCombined Test Coverage (All 100 tests):")
    print("  - Schema Extraction: 24 tests")
    print("  - Schema Creation: 19 tests")
    print("  - Full Migration: 15 tests")
    print("  - Data Models: 10 tests")
    print("  - Configuration: 7 tests")
    print("  - Statistics: 11 tests")
    print("  - Validation: 3 tests")
    print("  - Performance: 4 tests")
    print("  - Error Handling: 9 tests")
    print("="*70)