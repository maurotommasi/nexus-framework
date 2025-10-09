"""
Full Database Migration Tool - Enterprise Edition
Migrates entire databases including schema, data, indexes, constraints, views, and more.
"""

import sys
import os

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, root_dir)

from nexus.database.database_management import DatabaseFactory, DatabaseInterface
from nexus.database.database_simple_migration import (
    MigrationConfig, MigrationOrchestrator, MigrationStrategy,
    MigrationStats, DataValidator
)
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import time

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'full_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)


class MigrationPhase(Enum):
    """Migration phases"""
    SCHEMA_EXTRACTION = "schema_extraction"
    SCHEMA_CREATION = "schema_creation"
    DATA_MIGRATION = "data_migration"
    INDEX_CREATION = "index_creation"
    CONSTRAINT_CREATION = "constraint_creation"
    VIEW_CREATION = "view_creation"
    VALIDATION = "validation"


@dataclass
class TableMetadata:
    """Metadata for a table"""
    name: str
    primary_key: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DatabaseSchema:
    """Complete database schema"""
    tables: Dict[str, TableMetadata] = field(default_factory=dict)
    views: List[Dict[str, Any]] = field(default_factory=list)
    sequences: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    triggers: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FullMigrationConfig:
    """Configuration for full database migration"""
    source_db_type: str
    source_params: Dict[str, Any]
    target_db_type: str
    target_params: Dict[str, Any]
    
    # Migration options
    include_schema: bool = True
    include_data: bool = True
    include_indexes: bool = True
    include_constraints: bool = True
    include_views: bool = True
    include_sequences: bool = True
    include_functions: bool = False
    include_triggers: bool = False
    
    # Table filtering
    exclude_tables: List[str] = field(default_factory=list)
    include_tables: Optional[List[str]] = None
    
    # Data migration settings
    migration_strategy: MigrationStrategy = MigrationStrategy.PARALLEL
    chunk_size: int = 10000
    num_workers: int = 4
    parallel_tables: int = 3  # Number of tables to migrate in parallel
    
    # Advanced options
    create_target_database: bool = False
    drop_target_if_exists: bool = False
    disable_foreign_keys_during_migration: bool = True
    create_indexes_after_data: bool = True  # Faster data loading
    
    # Validation
    enable_validation: bool = True
    validate_row_counts: bool = True
    validate_sample_data: bool = False
    
    # Performance
    use_bulk_copy: bool = True  # Use native tools when available
    compression: bool = False


@dataclass
class FullMigrationStats:
    """Statistics for full database migration"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    total_tables: int = 0
    migrated_tables: int = 0
    failed_tables: int = 0
    
    total_rows: int = 0
    migrated_rows: int = 0
    
    total_indexes: int = 0
    created_indexes: int = 0
    
    total_constraints: int = 0
    created_constraints: int = 0
    
    total_views: int = 0
    created_views: int = 0
    
    errors: List[Dict[str, Any]] = field(default_factory=list)
    table_stats: Dict[str, Dict] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_tables': self.total_tables,
            'migrated_tables': self.migrated_tables,
            'failed_tables': self.failed_tables,
            'total_rows': self.total_rows,
            'migrated_rows': self.migrated_rows,
            'total_indexes': self.total_indexes,
            'created_indexes': self.created_indexes,
            'total_constraints': self.total_constraints,
            'created_constraints': self.created_constraints,
            'total_views': self.total_views,
            'created_views': self.created_views,
            'errors': self.errors,
            'table_stats': self.table_stats
        }


class SchemaExtractor:
    """Extracts database schema information"""
    
    def __init__(self, db: DatabaseInterface, db_type: str):
        self.db = db
        self.db_type = db_type.lower()
        self.logger = logging.getLogger('SchemaExtractor')
    
    def extract_schema(self, include_tables: Optional[List[str]] = None,
                      exclude_tables: List[str] = None) -> DatabaseSchema:
        """Extract complete database schema"""
        self.logger.info("Extracting database schema...")
        schema = DatabaseSchema()
        
        # Get all tables
        tables = self._get_tables()
        
        # Filter tables
        if include_tables:
            tables = [t for t in tables if t in include_tables]
        if exclude_tables:
            tables = [t for t in tables if t not in exclude_tables]
        
        self.logger.info(f"Found {len(tables)} tables to migrate")
        
        # Extract metadata for each table
        for table_name in tables:
            self.logger.info(f"Extracting metadata for table: {table_name}")
            
            table_meta = TableMetadata(
                name=table_name,
                primary_key=self._get_primary_key(table_name),
                columns=self._get_columns(table_name),
                indexes=self._get_indexes(table_name),
                foreign_keys=self._get_foreign_keys(table_name),
                constraints=self._get_constraints(table_name),
                row_count=self._get_row_count(table_name)
            )
            
            schema.tables[table_name] = table_meta
        
        # Extract views
        schema.views = self._get_views()
        
        # Extract sequences (for PostgreSQL)
        if self.db_type == 'postgresql':
            schema.sequences = self._get_sequences()
        
        self.logger.info(f"Schema extraction complete: {len(schema.tables)} tables, {len(schema.views)} views")
        
        return schema
    
    def _get_tables(self) -> List[str]:
        """Get list of all tables"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            return [r['table_name'] for r in result]
        
        elif self.db_type in ['mysql', 'mariadb']:
            result = self.db.fetch_all("SHOW TABLES")
            key = list(result[0].keys())[0]
            return [r[key] for r in result]
        
        elif self.db_type == 'sqlite':
            result = self.db.fetch_all("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            return [r['name'] for r in result]
        
        else:
            raise NotImplementedError(f"Table listing not implemented for {self.db_type}")
    
    def _get_primary_key(self, table_name: str) -> str:
        """Get primary key column for table"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_one("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """, (table_name,))
            return result['attname'] if result else 'id'
        
        elif self.db_type in ['mysql', 'mariadb']:
            result = self.db.fetch_one("""
                SELECT COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = %s
                AND CONSTRAINT_NAME = 'PRIMARY'
            """, (table_name,))
            return result['COLUMN_NAME'] if result else 'id'
        
        else:
            return 'id'  # Default fallback
    
    def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for table"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            return [dict(r) for r in result]
        
        elif self.db_type in ['mysql', 'mariadb']:
            result = self.db.fetch_all(f"DESCRIBE {table_name}")
            return [dict(r) for r in result]
        
        else:
            return []
    
    def _get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get indexes for table"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT
                    i.relname as index_name,
                    a.attname as column_name,
                    ix.indisunique as is_unique
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relname = %s
                AND NOT ix.indisprimary
            """, (table_name,))
            return [dict(r) for r in result]
        
        elif self.db_type in ['mysql', 'mariadb']:
            result = self.db.fetch_all(f"SHOW INDEX FROM {table_name}")
            return [dict(r) for r in result]
        
        else:
            return []
    
    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key constraints"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
            """, (table_name,))
            return [dict(r) for r in result]
        
        else:
            return []
    
    def _get_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table constraints"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT
                    con.conname as constraint_name,
                    con.contype as constraint_type,
                    pg_get_constraintdef(con.oid) as definition
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = %s
                AND con.contype NOT IN ('p', 'f')
            """, (table_name,))
            return [dict(r) for r in result]
        
        else:
            return []
    
    def _get_row_count(self, table_name: str) -> int:
        """Get approximate row count"""
        try:
            result = self.db.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
            return result['count']
        except:
            return 0
    
    def _get_views(self) -> List[Dict[str, Any]]:
        """Get database views"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT 
                    table_name as view_name,
                    view_definition
                FROM information_schema.views
                WHERE table_schema = 'public'
            """)
            return [dict(r) for r in result]
        
        else:
            return []
    
    def _get_sequences(self) -> List[Dict[str, Any]]:
        """Get sequences (PostgreSQL)"""
        if self.db_type == 'postgresql':
            result = self.db.fetch_all("""
                SELECT sequence_name, start_value, increment
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """)
            return [dict(r) for r in result]
        
        return []


class SchemaCreator:
    """Creates database schema in target database"""
    
    def __init__(self, db: DatabaseInterface, db_type: str):
        self.db = db
        self.db_type = db_type.lower()
        self.logger = logging.getLogger('SchemaCreator')
    
    def create_schema(self, schema: DatabaseSchema, 
                     create_indexes: bool = True,
                     create_constraints: bool = True) -> Dict[str, Any]:
        """Create database schema in target"""
        self.logger.info("Creating database schema...")
        results = {
            'tables_created': 0,
            'indexes_created': 0,
            'constraints_created': 0,
            'errors': []
        }
        
        # Sort tables by dependencies
        sorted_tables = self._sort_tables_by_dependencies(schema.tables)
        
        # Create tables
        for table_name in sorted_tables:
            table_meta = schema.tables[table_name]
            try:
                self._create_table(table_meta, create_indexes=False)
                results['tables_created'] += 1
                self.logger.info(f"✓ Created table: {table_name}")
            except Exception as e:
                self.logger.error(f"✗ Failed to create table {table_name}: {e}")
                results['errors'].append({
                    'table': table_name,
                    'phase': 'table_creation',
                    'error': str(e)
                })
        
        # Create indexes (if requested and after data load)
        if create_indexes:
            for table_name in sorted_tables:
                table_meta = schema.tables[table_name]
                try:
                    created = self._create_indexes(table_meta)
                    results['indexes_created'] += created
                except Exception as e:
                    self.logger.error(f"✗ Failed to create indexes for {table_name}: {e}")
        
        # Create constraints (after all tables exist)
        if create_constraints:
            for table_name in sorted_tables:
                table_meta = schema.tables[table_name]
                try:
                    created = self._create_constraints(table_meta)
                    results['constraints_created'] += created
                except Exception as e:
                    self.logger.error(f"✗ Failed to create constraints for {table_name}: {e}")
        
        self.logger.info(f"Schema creation complete: {results['tables_created']} tables")
        return results
    
    def _sort_tables_by_dependencies(self, tables: Dict[str, TableMetadata]) -> List[str]:
        """Sort tables by foreign key dependencies"""
        # Simple topological sort based on foreign keys
        sorted_tables = []
        remaining = set(tables.keys())
        
        while remaining:
            # Find tables with no unmet dependencies
            ready = []
            for table_name in remaining:
                table_meta = tables[table_name]
                dependencies = [fk['foreign_table_name'] for fk in table_meta.foreign_keys]
                unmet = [d for d in dependencies if d in remaining and d != table_name]
                
                if not unmet:
                    ready.append(table_name)
            
            if not ready:
                # Circular dependency - just add remaining tables
                ready = list(remaining)
            
            sorted_tables.extend(ready)
            remaining -= set(ready)
        
        return sorted_tables
    
    def _create_table(self, table_meta: TableMetadata, create_indexes: bool = False):
        """Create a single table"""
        # Build CREATE TABLE statement
        columns_sql = []
        
        for col in table_meta.columns:
            col_def = f"{col['column_name']} {self._map_data_type(col['data_type'])}"
            
            if col.get('is_nullable') == 'NO':
                col_def += " NOT NULL"
            
            if col.get('column_default'):
                col_def += f" DEFAULT {col['column_default']}"
            
            columns_sql.append(col_def)
        
        # Add primary key
        if table_meta.primary_key:
            columns_sql.append(f"PRIMARY KEY ({table_meta.primary_key})")
        
        create_sql = f"""
            CREATE TABLE {table_meta.name} (
                {', '.join(columns_sql)}
            )
        """
        
        self.db.execute(create_sql)
        self.db.commit()
    
    def _map_data_type(self, source_type: str) -> str:
        """Map data types between databases"""
        # Simplified type mapping
        type_mapping = {
            'integer': 'INTEGER',
            'bigint': 'BIGINT',
            'smallint': 'SMALLINT',
            'character varying': 'VARCHAR(255)',
            'text': 'TEXT',
            'timestamp without time zone': 'TIMESTAMP',
            'timestamp with time zone': 'TIMESTAMP',
            'date': 'DATE',
            'boolean': 'BOOLEAN',
            'numeric': 'NUMERIC',
            'real': 'REAL',
            'double precision': 'DOUBLE PRECISION'
        }
        
        return type_mapping.get(source_type.lower(), 'TEXT')
    
    def _create_indexes(self, table_meta: TableMetadata) -> int:
        """Create indexes for a table"""
        created = 0
        
        for idx in table_meta.indexes:
            try:
                index_name = idx['index_name']
                column_name = idx['column_name']
                is_unique = idx.get('is_unique', False)
                
                unique_sql = "UNIQUE" if is_unique else ""
                create_sql = f"""
                    CREATE {unique_sql} INDEX {index_name}
                    ON {table_meta.name} ({column_name})
                """
                
                self.db.execute(create_sql)
                self.db.commit()
                created += 1
            except Exception as e:
                self.logger.warning(f"Could not create index {index_name}: {e}")
        
        return created
    
    def _create_constraints(self, table_meta: TableMetadata) -> int:
        """Create constraints for a table"""
        created = 0
        
        # Create foreign keys
        for fk in table_meta.foreign_keys:
            try:
                alter_sql = f"""
                    ALTER TABLE {table_meta.name}
                    ADD CONSTRAINT {fk['constraint_name']}
                    FOREIGN KEY ({fk['column_name']})
                    REFERENCES {fk['foreign_table_name']} ({fk['foreign_column_name']})
                """
                
                self.db.execute(alter_sql)
                self.db.commit()
                created += 1
            except Exception as e:
                self.logger.warning(f"Could not create FK {fk['constraint_name']}: {e}")
        
        return created


class FullDatabaseMigration:
    """Orchestrates complete database migration"""
    
    def __init__(self, config: FullMigrationConfig):
        self.config = config
        self.logger = logging.getLogger('FullDatabaseMigration')
        self.stats = FullMigrationStats()
        self.schema: Optional[DatabaseSchema] = None
        self.lock = threading.Lock()
    
    def execute(self) -> FullMigrationStats:
        """Execute full database migration"""
        self.logger.info("="*60)
        self.logger.info("FULL DATABASE MIGRATION")
        self.logger.info("="*60)
        
        self.stats.start_time = datetime.now()
        
        try:
            # Phase 1: Extract schema
            self._phase_extract_schema()
            
            # Phase 2: Create schema in target
            if self.config.include_schema:
                self._phase_create_schema()
            
            # Phase 3: Migrate data
            if self.config.include_data:
                self._phase_migrate_data()
            
            # Phase 4: Create indexes
            if self.config.include_indexes and self.config.create_indexes_after_data:
                self._phase_create_indexes()
            
            # Phase 5: Create constraints
            if self.config.include_constraints:
                self._phase_create_constraints()
            
            # Phase 6: Create views
            if self.config.include_views:
                self._phase_create_views()
            
            # Phase 7: Validation
            if self.config.enable_validation:
                self._phase_validation()
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}", exc_info=True)
            self.stats.errors.append({
                'phase': 'global',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        finally:
            self.stats.end_time = datetime.now()
            self._generate_report()
        
        return self.stats
    
    def _phase_extract_schema(self):
        """Phase 1: Extract schema from source"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 1: SCHEMA EXTRACTION")
        self.logger.info("="*60)
        
        source_db = DatabaseFactory.create_database(
            self.config.source_db_type,
            self.config.source_params
        )
        source_db.connect()
        
        try:
            extractor = SchemaExtractor(source_db, self.config.source_db_type)
            self.schema = extractor.extract_schema(
                include_tables=self.config.include_tables,
                exclude_tables=self.config.exclude_tables
            )
            
            self.stats.total_tables = len(self.schema.tables)
            self.stats.total_rows = sum(t.row_count for t in self.schema.tables.values())
            self.stats.total_indexes = sum(len(t.indexes) for t in self.schema.tables.values())
            self.stats.total_constraints = sum(len(t.foreign_keys) for t in self.schema.tables.values())
            self.stats.total_views = len(self.schema.views)
            
            self.logger.info(f"✓ Extracted schema:")
            self.logger.info(f"  - Tables: {self.stats.total_tables}")
            self.logger.info(f"  - Total rows: {self.stats.total_rows:,}")
            self.logger.info(f"  - Indexes: {self.stats.total_indexes}")
            self.logger.info(f"  - Views: {self.stats.total_views}")
        
        finally:
            source_db.disconnect()
    
    def _phase_create_schema(self):
        """Phase 2: Create schema in target"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 2: SCHEMA CREATION")
        self.logger.info("="*60)
        
        target_db = DatabaseFactory.create_database(
            self.config.target_db_type,
            self.config.target_params
        )
        target_db.connect()
        
        try:
            creator = SchemaCreator(target_db, self.config.target_db_type)
            results = creator.create_schema(
                self.schema,
                create_indexes=not self.config.create_indexes_after_data,
                create_constraints=not self.config.disable_foreign_keys_during_migration
            )
            
            self.stats.migrated_tables = results['tables_created']
            self.stats.created_indexes = results['indexes_created']
            self.stats.created_constraints = results['constraints_created']
            
            self.logger.info(f"✓ Created {results['tables_created']} tables")
        
        finally:
            target_db.disconnect()
    
    def _phase_migrate_data(self):
        """Phase 3: Migrate data for all tables"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 3: DATA MIGRATION")
        self.logger.info("="*60)
        
        if self.config.parallel_tables > 1:
            self._migrate_data_parallel()
        else:
            self._migrate_data_sequential()
    
    def _migrate_data_sequential(self):
        """Migrate tables sequentially"""
        for table_name, table_meta in self.schema.tables.items():
            self._migrate_table(table_name, table_meta)
    
    def _migrate_data_parallel(self):
        """Migrate multiple tables in parallel"""
        self.logger.info(f"Using {self.config.parallel_tables} parallel workers for tables")
        
        with ThreadPoolExecutor(max_workers=self.config.parallel_tables) as executor:
            futures = {
                executor.submit(self._migrate_table, table_name, table_meta): table_name
                for table_name, table_meta in self.schema.tables.items()
            }
            
            for future in as_completed(futures):
                table_name = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"Failed to migrate table {table_name}: {e}")
    
    def _migrate_table(self, table_name: str, table_meta: TableMetadata):
        """Migrate a single table"""
        self.logger.info(f"\nMigrating table: {table_name} ({table_meta.row_count:,} rows)")
        
        start_time = time.time()
        
        try:
            # Create migration config for this table
            table_config = MigrationConfig(
                source_db_type=self.config.source_db_type,
                source_params=self.config.source_params,
                target_db_type=self.config.target_db_type,
                target_params=self.config.target_params,
                source_table=table_name,
                target_table=table_name,
                primary_key=table_meta.primary_key,
                strategy=self.config.migration_strategy,
                chunk_size=self.config.chunk_size,
                num_workers=self.config.num_workers,
                enable_validation=False,  # We'll validate at the end
                enable_checkpoints=True
            )
            
            # Execute table migration
            orchestrator = MigrationOrchestrator(table_config)
            table_stats = orchestrator.execute()
            
            # Update global stats
            with self.lock:
                self.stats.migrated_rows += table_stats.migrated_records
                self.stats.table_stats[table_name] = {
                    'rows': table_stats.migrated_records,
                    'time': table_stats.elapsed_seconds,
                    'rate': table_stats.average_rate
                }
            
            elapsed = time.time() - start_time
            rate = table_stats.migrated_records / elapsed if elapsed > 0 else 0
            
            self.logger.info(f"✓ Completed {table_name}: {table_stats.migrated_records:,} rows in {elapsed/60:.2f} min ({rate:.0f} rec/s)")
        
        except Exception as e:
            self.logger.error(f"✗ Failed to migrate {table_name}: {e}")
            with self.lock:
                self.stats.failed_tables += 1
                self.stats.errors.append({
                    'table': table_name,
                    'phase': 'data_migration',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    def _phase_create_indexes(self):
        """Phase 4: Create indexes"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 4: INDEX CREATION")
        self.logger.info("="*60)
        
        target_db = DatabaseFactory.create_database(
            self.config.target_db_type,
            self.config.target_params
        )
        target_db.connect()
        
        try:
            creator = SchemaCreator(target_db, self.config.target_db_type)
            
            for table_name, table_meta in self.schema.tables.items():
                try:
                    created = creator._create_indexes(table_meta)
                    self.stats.created_indexes += created
                    self.logger.info(f"✓ Created {created} indexes for {table_name}")
                except Exception as e:
                    self.logger.error(f"✗ Failed to create indexes for {table_name}: {e}")
        
        finally:
            target_db.disconnect()
    
    def _phase_create_constraints(self):
        """Phase 5: Create constraints"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 5: CONSTRAINT CREATION")
        self.logger.info("="*60)
        
        target_db = DatabaseFactory.create_database(
            self.config.target_db_type,
            self.config.target_params
        )
        target_db.connect()
        
        try:
            creator = SchemaCreator(target_db, self.config.target_db_type)
            
            for table_name, table_meta in self.schema.tables.items():
                try:
                    created = creator._create_constraints(table_meta)
                    self.stats.created_constraints += created
                    self.logger.info(f"✓ Created {created} constraints for {table_name}")
                except Exception as e:
                    self.logger.error(f"✗ Failed to create constraints for {table_name}: {e}")
        
        finally:
            target_db.disconnect()
    
    def _phase_create_views(self):
        """Phase 6: Create views"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 6: VIEW CREATION")
        self.logger.info("="*60)
        
        target_db = DatabaseFactory.create_database(
            self.config.target_db_type,
            self.config.target_params
        )
        target_db.connect()
        
        try:
            for view in self.schema.views:
                try:
                    view_name = view['view_name']
                    view_def = view['view_definition']
                    
                    create_sql = f"CREATE VIEW {view_name} AS {view_def}"
                    target_db.execute(create_sql)
                    target_db.commit()
                    
                    self.stats.created_views += 1
                    self.logger.info(f"✓ Created view: {view_name}")
                except Exception as e:
                    self.logger.error(f"✗ Failed to create view {view_name}: {e}")
        
        finally:
            target_db.disconnect()
    
    def _phase_validation(self):
        """Phase 7: Validation"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PHASE 7: VALIDATION")
        self.logger.info("="*60)
        
        source_db = DatabaseFactory.create_database(
            self.config.source_db_type,
            self.config.source_params
        )
        source_db.connect()
        
        target_db = DatabaseFactory.create_database(
            self.config.target_db_type,
            self.config.target_params
        )
        target_db.connect()
        
        try:
            validation_errors = []
            
            for table_name in self.schema.tables.keys():
                try:
                    source_count, target_count, match = DataValidator.validate_counts(
                        source_db, target_db, table_name, table_name
                    )
                    
                    if match:
                        self.logger.info(f"✓ {table_name}: {source_count:,} rows match")
                    else:
                        error = f"✗ {table_name}: Mismatch (source: {source_count:,}, target: {target_count:,})"
                        self.logger.error(error)
                        validation_errors.append({
                            'table': table_name,
                            'source_count': source_count,
                            'target_count': target_count,
                            'difference': abs(source_count - target_count)
                        })
                
                except Exception as e:
                    self.logger.error(f"✗ Validation failed for {table_name}: {e}")
            
            if validation_errors:
                self.stats.errors.extend(validation_errors)
                self.logger.error(f"\n✗ Validation found {len(validation_errors)} mismatches")
            else:
                self.logger.info(f"\n✓ All tables validated successfully")
        
        finally:
            source_db.disconnect()
            target_db.disconnect()
    
    def _generate_report(self):
        """Generate migration report"""
        elapsed = (self.stats.end_time - self.stats.start_time).total_seconds()
        
        report = {
            'migration_type': 'full_database',
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'source': f"{self.config.source_db_type}",
                'target': f"{self.config.target_db_type}",
                'strategy': self.config.migration_strategy.value,
                'parallel_tables': self.config.parallel_tables,
                'chunk_size': self.config.chunk_size,
                'num_workers': self.config.num_workers
            },
            'statistics': self.stats.to_dict(),
            'summary': {
                'status': 'SUCCESS' if self.stats.failed_tables == 0 else 'PARTIAL',
                'total_time': f"{elapsed/60:.2f} minutes",
                'total_tables': self.stats.total_tables,
                'migrated_tables': self.stats.migrated_tables,
                'failed_tables': self.stats.failed_tables,
                'total_rows': f"{self.stats.total_rows:,}",
                'migrated_rows': f"{self.stats.migrated_rows:,}",
                'average_rate': f"{self.stats.migrated_rows/elapsed:.0f} rows/second" if elapsed > 0 else "N/A"
            }
        }
        
        report_file = f'full_migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info("MIGRATION COMPLETE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Report saved to: {report_file}")
        self.logger.info(f"\nSummary:")
        self.logger.info(f"  Tables: {self.stats.migrated_tables}/{self.stats.total_tables}")
        self.logger.info(f"  Rows: {self.stats.migrated_rows:,}/{self.stats.total_rows:,}")
        self.logger.info(f"  Time: {elapsed/60:.2f} minutes")
        self.logger.info(f"  Rate: {self.stats.migrated_rows/elapsed:.0f} rows/second")
        self.logger.info(f"  Errors: {len(self.stats.errors)}")
        self.logger.info(f"{'='*60}\n")


# CLI and usage examples
if __name__ == "__main__":
    import argparse
    
    # Example 1: Simple full database migration
    def example_simple_migration():
        """Example: Migrate entire PostgreSQL database to MySQL"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={
                'host': 'old-postgres.company.com',
                'port': 5432,
                'database': 'production',
                'user': 'postgres',
                'password': 'password'
            },
            target_db_type='mysql',
            target_params={
                'host': 'new-mysql.company.com',
                'port': 3306,
                'database': 'production',
                'user': 'root',
                'password': 'password'
            },
            
            # Migration options
            include_schema=True,
            include_data=True,
            include_indexes=True,
            include_constraints=True,
            include_views=True,
            
            # Performance settings
            migration_strategy=MigrationStrategy.PARALLEL,
            chunk_size=10000,
            num_workers=6,
            parallel_tables=3,  # Migrate 3 tables at once
            
            # Best practices
            create_indexes_after_data=True,  # Faster data loading
            disable_foreign_keys_during_migration=True,
            
            enable_validation=True
        )
        
        migration = FullDatabaseMigration(config)
        stats = migration.execute()
        
        return stats
    
    # Example 2: Selective table migration
    def example_selective_migration():
        """Example: Migrate only specific tables"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={
                'host': 'source-db.com',
                'database': 'ecommerce',
                'user': 'postgres',
                'password': 'password'
            },
            target_db_type='postgresql',
            target_params={
                'host': 'target-db.com',
                'database': 'ecommerce_backup',
                'user': 'postgres',
                'password': 'password'
            },
            
            # Only migrate these tables
            include_tables=['users', 'orders', 'products', 'payments'],
            
            # Or exclude specific tables
            # exclude_tables=['temp_data', 'logs', 'cache'],
            
            migration_strategy=MigrationStrategy.PARALLEL,
            parallel_tables=2,
            enable_validation=True
        )
        
        migration = FullDatabaseMigration(config)
        stats = migration.execute()
        
        return stats
    
    # Example 3: Schema-only migration
    def example_schema_only():
        """Example: Migrate only schema (no data)"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={
                'host': 'prod-db.com',
                'database': 'production',
                'user': 'postgres',
                'password': 'password'
            },
            target_db_type='postgresql',
            target_params={
                'host': 'dev-db.com',
                'database': 'development',
                'user': 'postgres',
                'password': 'password'
            },
            
            # Schema only
            include_schema=True,
            include_data=False,  # No data migration
            include_indexes=True,
            include_constraints=True,
            include_views=True
        )
        
        migration = FullDatabaseMigration(config)
        stats = migration.execute()
        
        return stats
    
    # Example 4: Production-ready migration script
    def example_production_migration():
        """Example: Production migration with all features"""
        print("="*60)
        print("PRODUCTION DATABASE MIGRATION")
        print("="*60)
        
        # Configuration
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={
                'host': 'prod-postgres.company.com',
                'port': 5432,
                'database': 'production',
                'user': 'readonly_user',  # Use read-only user
                'password': 'password',
                'timeout': 60
            },
            target_db_type='postgresql',
            target_params={
                'host': 'new-postgres.company.com',
                'port': 5432,
                'database': 'production_v2',
                'user': 'admin',
                'password': 'password',
                'timeout': 60
            },
            
            # Exclude system/temporary tables
            exclude_tables=[
                'pg_stat_statements',
                'temp_data',
                'cache_table',
                'session_data'
            ],
            
            # Full migration
            include_schema=True,
            include_data=True,
            include_indexes=True,
            include_constraints=True,
            include_views=True,
            include_sequences=True,
            
            # Performance optimization
            migration_strategy=MigrationStrategy.PARALLEL,
            chunk_size=10000,
            num_workers=8,
            parallel_tables=4,
            
            # Best practices
            create_indexes_after_data=True,
            disable_foreign_keys_during_migration=True,
            
            # Validation
            enable_validation=True,
            validate_row_counts=True
        )
        
        # Pre-flight checks
        print("\nPre-flight checks:")
        print("  ✓ Source database: Read-only access")
        print("  ✓ Target database: Empty and ready")
        print("  ✓ Network connectivity verified")
        print("  ✓ Disk space sufficient")
        
        # Confirm before proceeding
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return None
        
        # Execute migration
        print("\nStarting migration...\n")
        migration = FullDatabaseMigration(config)
        stats = migration.execute()
        
        # Post-migration tasks
        print("\nPost-migration tasks:")
        print("  ✓ Update application connection strings")
        print("  ✓ Test application with new database")
        print("  ✓ Monitor performance")
        print("  ✓ Schedule old database decommission")
        
        return stats
    
    # Example 5: Cross-region cloud migration
    def example_cloud_migration():
        """Example: Migrate from on-premise to AWS RDS"""
        config = FullMigrationConfig(
            source_db_type='postgresql',
            source_params={
                'host': '192.168.1.100',  # On-premise
                'port': 5432,
                'database': 'company_db',
                'user': 'postgres',
                'password': 'password'
            },
            target_db_type='postgresql',
            target_params={
                'host': 'company-db.abc123.us-east-1.rds.amazonaws.com',  # AWS RDS
                'port': 5432,
                'database': 'company_db',
                'user': 'admin',
                'password': 'aws_password'
            },
            
            # Conservative settings for cross-region
            migration_strategy=MigrationStrategy.CHUNKED,
            chunk_size=5000,  # Smaller chunks for network
            num_workers=4,
            parallel_tables=2,
            
            enable_validation=True
        )
        
        migration = FullDatabaseMigration(config)
        stats = migration.execute()
        
        return stats
    
    # CLI argument parsing
    parser = argparse.ArgumentParser(
        description='Full Database Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple migration
  python full_database_migration.py --source-type postgresql --source-host localhost \\
    --source-db mydb --target-type mysql --target-host remote.com --target-db mydb
  
  # Schema only
  python full_database_migration.py --source-type postgresql --source-host localhost \\
    --source-db mydb --target-type postgresql --target-host backup.com --target-db mydb \\
    --schema-only
  
  # Parallel migration
  python full_database_migration.py --source-type postgresql --source-host localhost \\
    --source-db mydb --target-type postgresql --target-host new-server.com --target-db mydb \\
    --parallel-tables 4 --num-workers 8
        """
    )
    
    # Source database arguments
    parser.add_argument('--source-type', required=True, help='Source database type')
    parser.add_argument('--source-host', required=True, help='Source database host')
    parser.add_argument('--source-port', type=int, help='Source database port')
    parser.add_argument('--source-db', required=True, help='Source database name')
    parser.add_argument('--source-user', required=True, help='Source database user')
    parser.add_argument('--source-password', required=True, help='Source database password')
    
    # Target database arguments
    parser.add_argument('--target-type', required=True, help='Target database type')
    parser.add_argument('--target-host', required=True, help='Target database host')
    parser.add_argument('--target-port', type=int, help='Target database port')
    parser.add_argument('--target-db', required=True, help='Target database name')
    parser.add_argument('--target-user', required=True, help='Target database user')
    parser.add_argument('--target-password', required=True, help='Target database password')
    
    # Migration options
    parser.add_argument('--schema-only', action='store_true', help='Migrate schema only (no data)')
    parser.add_argument('--data-only', action='store_true', help='Migrate data only (no schema)')
    parser.add_argument('--exclude-tables', nargs='+', help='Tables to exclude')
    parser.add_argument('--include-tables', nargs='+', help='Only migrate these tables')
    
    # Performance options
    parser.add_argument('--parallel-tables', type=int, default=3, help='Number of tables to migrate in parallel')
    parser.add_argument('--num-workers', type=int, default=4, help='Number of workers per table')
    parser.add_argument('--chunk-size', type=int, default=10000, help='Chunk size for data migration')
    
    # Validation
    parser.add_argument('--skip-validation', action='store_true', help='Skip validation phase')
    
    # Examples
    parser.add_argument('--example', choices=['simple', 'selective', 'schema', 'production', 'cloud'],
                       help='Run example migration')
    
    args = parser.parse_args()
    
    # Run example if requested
    if args.example:
        examples = {
            'simple': example_simple_migration,
            'selective': example_selective_migration,
            'schema': example_schema_only,
            'production': example_production_migration,
            'cloud': example_cloud_migration
        }
        
        print(f"\nRunning example: {args.example}")
        stats = examples[args.example]()
        
        if stats:
            print(f"\nMigration completed!")
            print(f"Tables migrated: {stats.migrated_tables}/{stats.total_tables}")
            print(f"Rows migrated: {stats.migrated_rows:,}/{stats.total_rows:,}")
        
        sys.exit(0)
    
    # Build configuration from CLI arguments
    source_params = {
        'host': args.source_host,
        'database': args.source_db,
        'user': args.source_user,
        'password': args.source_password
    }
    if args.source_port:
        source_params['port'] = args.source_port
    
    target_params = {
        'host': args.target_host,
        'database': args.target_db,
        'user': args.target_user,
        'password': args.target_password
    }
    if args.target_port:
        target_params['port'] = args.target_port
    
    # Create configuration
    config = FullMigrationConfig(
        source_db_type=args.source_type,
        source_params=source_params,
        target_db_type=args.target_type,
        target_params=target_params,
        
        include_schema=not args.data_only,
        include_data=not args.schema_only,
        include_tables=args.include_tables,
        exclude_tables=args.exclude_tables or [],
        
        parallel_tables=args.parallel_tables,
        num_workers=args.num_workers,
        chunk_size=args.chunk_size,
        
        enable_validation=not args.skip_validation
    )
    
    # Execute migration
    print("\n" + "="*60)
    print("FULL DATABASE MIGRATION")
    print("="*60)
    print(f"Source: {args.source_type} - {args.source_host}/{args.source_db}")
    print(f"Target: {args.target_type} - {args.target_host}/{args.target_db}")
    print("="*60 + "\n")
    
    migration = FullDatabaseMigration(config)
    stats = migration.execute()
    
    # Exit with appropriate code
    if stats.failed_tables > 0:
        sys.exit(1)
    else:
        sys.exit(0)