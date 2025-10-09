## CLI Usage

### Basic Syntax

```bash
python full_database_migration.py \
  --source-type postgresql \
  --source-host source-db.com \
  --source-db production \
  --source-user postgres \
  --source-password password \
  --target-type mysql \
  --target-host target-db.com \
  --target-db production \
  --target-user root \
  --target-password password
```

### CLI Arguments

#### Required Arguments

```bash
--source-type TYPE          # Source database type
--source-host HOST          # Source database host
--source-db DATABASE        # Source database name
--source-user USER          # Source database user
--source-password PASS      # Source database password

--target-type TYPE          # Target database type
--target-host HOST          # Target database host
--target-db DATABASE        # Target database name
--target-user USER          # Target database user
--target-password PASS      # Target database password
```

#### Optional Arguments

```bash
--source-port PORT          # Source database port (default: database default)
--target-port PORT          # Target database port (default: database default)

--schema-only               # Migrate schema only (no data)
--data-only                 # Migrate data only (no schema)

--include-tables T1 T2      # Only migrate specified tables
--exclude-tables T1 T2      # Exclude specified tables

--parallel-tables N         # Number of tables to migrate in parallel (default: 3)
--num-workers N             # Number of workers per table (default: 4)
--chunk-size N              # Chunk size for data migration (default: 10000)

--skip-validation           # Skip validation phase
```

### CLI Examples

#### Example 1: Simple Migration

```bash
python full_database_migration.py \
  --source-type postgresql \
  --source-host old-db.company.com \
  --source-db production \
  --source-user postgres \
  --source-password pg_pass \
  --target-type postgresql \
  --target-host new-db.company.com \
  --target-db production \
  --target-user postgres \
  --target-password pg_pass
```

#### Example 2: Schema Only

```bash
python full_database_migration.py \
  --source-type postgresql \
  --source-host prod-db.com \
  --source-db production \
  --source-user postgres \
  --source-password password \
  --target-type postgresql \
  --target-host dev-db.com \
  --target-db development \
  --target-user postgres \
  --target-password password \
  --schema-only
```

#### Example 3: Selective Tables

```bash
python full_database_migration.py \
  --source-type mysql \
  --source-host source.com \
  --source-db ecommerce \
  --source-user root \
  --source-password password \
  --target-type mysql \
  --target-host backup.com \
  --target-db ecommerce_backup \
  --target-user root \
  --target-password password \
  --include-tables users orders products payments
```

#### Example 4: Exclude Tables

```bash
python full_database_migration.py \
  --source-type postgresql \
  --source-host source.com \
  --source-db mydb \
  --source-user postgres \
  --source-password password \
  --target-type postgresql \
  --target-host target.com \
  --target-db mydb \
  --target-user postgres \
  --target-password password \
  --exclude-tables temp_data logs cache sessions
```

#### Example 5: High Performance

```bash
python full_database_migration.py \
  --source-type postgresql \
  --source-host source.com \
  --source-db bigdata \
  --source-user postgres \
  --source-password password \
  --target-type postgresql \
  --target-host target.com \
  --target-db bigdata \
  --target-user postgres \
  --target-password password \
  --parallel-tables 6 \
  --num-workers 8 \
  --chunk-size 20000
```

#### Example 6: Run Pre-Built Examples

```bash
# Run simple example
python full_database_migration.py --example simple

# Run schema-only example
python full_database_migration.py --example schema

# Run production example (with confirmations)
python full_database_migration.py --example production

# Run cloud migration example
python full_database_migration.py --example cloud
```

---

## Migration Strategies

### Strategy Comparison

| Strategy | Best For | Speed | Memory | Complexity |
|----------|----------|-------|--------|------------|
| CHUNKED | Most cases | Medium | Low | Low |
| PARALLEL | Large databases | Fast | Medium | Medium |
| STREAMING | Memory-constrained | Slow | Very Low | Low |

### When to Use Each Strategy

#### CHUNKED (Recommended for Most Cases)
- Database size: Any
- Single-table processing
- Reliable and predictable
- Good for checkpoints

```python
migration_strategy=MigrationStrategy.CHUNKED
parallel_tables=1  # Sequential
chunk_size=10000
```

#### PARALLEL (Recommended for Large Databases)
- Database size: 10GB+
- Multiple tables simultaneously
- Fastest option
- Requires more resources

```python
migration_strategy=MigrationStrategy.PARALLEL
parallel_tables=4  # 4 tables at once
num_workers=8      # 8 workers per table
chunk_size=10000
```

#### STREAMING (Memory-Constrained Environments)
- Limited memory
- Continuous processing
- Lowest memory footprint

```python
migration_strategy=MigrationStrategy.STREAMING
parallel_tables=1
batch_size=500
```

---

## Real-World Scenarios

### Scenario 1: Production Database Upgrade

**Task**: Upgrade PostgreSQL 12 → PostgreSQL 15

```python
from full_database_migration import FullMigrationConfig, FullDatabaseMigration, MigrationStrategy

config = FullMigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'postgres12-prod.company.com',
        'database': 'production',
        'user': 'readonly_user',  # Use read-only user
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'postgres15-prod.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    # Full migration
    include_schema=True,
    include_data=True,
    include_indexes=True,
    include_constraints=True,
    include_views=True,
    include_sequences=True,
    
    # Performance
    migration_strategy=MigrationStrategy.PARALLEL,
    parallel_tables=4,
    num_workers=8,
    chunk_size=10000,
    
    # Best practices
    create_indexes_after_data=True,
    disable_foreign_keys_during_migration=True,
    
    enable_validation=True
)

# Execute with monitoring
print("Starting production database upgrade...")
migration = FullDatabaseMigration(config)
stats = migration.execute()

# Verify results
if stats.failed_tables == 0:
    print("✓ Migration successful!")
    print(f"Migrated {stats.migrated_tables} tables")
    print(f"Total rows: {stats.migrated_rows:,}")
else:
    print(f"✗ Migration completed with {stats.failed_tables} failed tables")
    print("Check logs for details")
```

**Expected Output**:
```
Starting production database upgrade...
============================================================
FULL DATABASE MIGRATION
============================================================

[... detailed phase logs ...]

============================================================
MIGRATION COMPLETE
============================================================

Summary:
  Tables: 87/87
  Rows: 456,789,012/456,789,012
  Time: 245.30 minutes
  Rate: 31,056 rows/second
  Errors: 0
============================================================

✓ Migration successful!
Migrated 87 tables
Total rows: 456,789,012
```

### Scenario 2: Cloud Migration (On-Premise → AWS RDS)

**Task**: Move on-premise PostgreSQL to AWS RDS

```python
config = FullMigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': '192.168.1.100',  # On-premise
        'port': 5432,
        'database': 'company_db',
        'user': 'postgres',
        'password': 'local_password',
        'timeout': 60
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'company-db.abc123.us-east-1.rds.amazonaws.com',
        'port': 5432,
        'database': 'company_db',
        'user': 'admin',
        'password': 'aws_password',
        'timeout': 60
    },
    
    # Full migration
    include_schema=True,
    include_data=True,
    include_indexes=True,
    include_constraints=True,
    include_views=True,
    
    # Conservative settings for network transfer
    migration_strategy=MigrationStrategy.CHUNKED,
    chunk_size=5000,  # Smaller chunks for network
    num_workers=4,
    parallel_tables=2,
    
    enable_validation=True
)

migration = FullDatabaseMigration(config)
stats = migration.execute()

print(f"Cloud migration completed in {(stats.end_time - stats.start_time).total_seconds()/60:.2f} minutes")
```

### Scenario 3: Multi-Region Replication

**Task**: Clone production database to multiple regions

```python
# Define target regions
target_regions = [
    {
        'name': 'us-east-1',
        'host': 'db-useast1.company.com',
        'user': 'admin',
        'password': 'password_east'
    },
    {
        'name': 'eu-west-1',
        'host': 'db-euwest1.company.com',
        'user': 'admin',
        'password': 'password_eu'
    },
    {
        'name': 'ap-southeast-1',
        'host': 'db-apsoutheast1.company.com',
        'user': 'admin',
        'password': 'password_asia'
    }
]

# Source configuration
source_params = {
    'host': 'primary-db.company.com',
    'database': 'production',
    'user': 'readonly_user',
    'password': 'password'
}

# Migrate to each region
for region in target_regions:
    print(f"\nMigrating to region: {region['name']}")
    
    config = FullMigrationConfig(
        source_db_type='postgresql',
        source_params=source_params,
        target_db_type='postgresql',
        target_params={
            'host': region['host'],
            'database': 'production',
            'user': region['user'],
            'password': region['password']
        },
        
        include_schema=True,
        include_data=True,
        include_indexes=True,
        include_constraints=True,
        
        migration_strategy=MigrationStrategy.PARALLEL,
        parallel_tables=3,
        num_workers=6,
        
        enable_validation=True
    )
    
    migration = FullDatabaseMigration(config)
    stats = migration.execute()
    
    print(f"✓ Region {region['name']}: {stats.migrated_tables} tables, {stats.migrated_rows:,} rows")
```

### Scenario 4: Development Environment Setup

**Task**: Create development databases from production

```python
# Production source
source_params = {
    'host': 'prod-db.company.com',
    'database': 'production',
    'user': 'readonly_user',
    'password': 'prod_password'
}

# Multiple dev environments
dev_environments = ['dev1', 'dev2', 'dev3', 'staging']

for env in dev_environments:
    print(f"\nCreating database for: {env}")
    
    config = FullMigrationConfig(
        source_db_type='postgresql',
        source_params=source_params,
        target_db_type='postgresql',
        target_params={
            'host': 'dev-db.company.com',
            'database': f'{env}_db',
            'user': 'postgres',
            'password': 'dev_password'
        },
        
        # Schema only (no production data)
        include_schema=True,
        include_data=False,  # Don't copy production data
        include_indexes=True,
        include_constraints=True,
        include_views=True
    )
    
    migration = FullDatabaseMigration(config)
    stats = migration.execute()
    
    print(f"✓ Created {env}_db with {stats.migrated_tables} tables")
```

### Scenario 5: Database Consolidation

**Task**: Merge multiple databases into one

```python
# Source databases
source_databases = [
    {'host': 'legacy-db1.com', 'database': 'customers_east', 'prefix': 'east_'},
    {'host': 'legacy-db2.com', 'database': 'customers_west', 'prefix': 'west_'},
    {'host': 'legacy-db3.com', 'database': 'customers_central', 'prefix': 'central_'}
]

# Target consolidated database
target_params = {
    'host': 'consolidated-db.company.com',
    'database': 'customers_unified',
    'user': 'postgres',
    'password': 'password'
}

# Note: This requires custom transformation logic
# Each table would need to be prefixed with region identifier

for source in source_databases:
    print(f"\nMigrating from {source['database']}...")
    
    # This is a simplified example
    # In practice, you'd need custom table name transformation
    config = FullMigrationConfig(
        source_db_type='postgresql',
        source_params={
            'host': source['host'],
            'database': source['database'],
            'user': 'postgres',
            'password': 'password'
        },
        target_db_type='postgresql',
        target_params=target_params,
        
        include_schema=True,
        include_data=True,
        
        migration_strategy=MigrationStrategy.PARALLEL,
        parallel_tables=2
    )
    
    migration = FullDatabaseMigration(config)
    stats = migration.execute()
    
    print(f"✓ Migrated {stats.migrated_tables} tables from {source['database']}")
```

---

## Performance Optimization

### Recommended Settings by Database Size

| Database Size | parallel_tables | num_workers | chunk_size | Expected Time |
|---------------|-----------------|-------------|------------|---------------|
| < 1GB | 1 | 2 | 10000 | 5-15 min |
| 1-10GB | 2 | 4 | 10000 | 15-60 min |
| 10-50GB | 3 | 6 | 10000 | 1-4 hours |
| 50-100GB | 4 | 8 | 10000 | 2-8 hours |
| 100-500GB | 6 | 8 | 15000 | 4-24 hours |
| 500GB+ | 8 | 10 | 20000 | 1+ days |

### Performance Tuning Tips

#### 1. Disable Indexes During Data Load

```python
create_indexes_after_data=True  # Create indexes after all data is loaded
```

**Why**: Inserting data without indexes is 3-5x faster

#### 2. Disable Foreign Keys During Migration

```python
disable_foreign_keys_during_migration=True
```

**Why**: FK checks slow down inserts, add them after data load

#### 3. Optimize Chunk Size

```python
# For small rows (< 100 bytes)
chunk_size=50000

# For medium rows (100-500 bytes)
chunk_size=10000

# For large rows (> 500 bytes)
chunk_size=5000
```

#### 4. Tune Worker Count

```python
import multiprocessing

# Use 75% of available CPU cores
cpu_count = multiprocessing.cpu_count()
num_workers = int(cpu_count * 0.75)

config = FullMigrationConfig(
    ...,
    num_workers=num_workers
)
```

#### 5. Database-Specific Optimizations

**PostgreSQL Target**:
```python
# Before migration
target_db.execute("ALTER TABLE users SET (autovacuum_enabled = false)")

# After migration
target_db.execute("ALTER TABLE users SET (autovacuum_enabled = true)")
target_db.execute("VACUUM ANALYZE users")
```

**MySQL Target**:
```python
# Before migration
target_db.execute("SET FOREIGN_KEY_CHECKS=0")
target_db.execute("SET UNIQUE_CHECKS=0")
target_db.execute("SET AUTOCOMMIT=0")

# After migration
target_db.execute("SET FOREIGN_KEY_CHECKS=1")
target_db.execute("SET UNIQUE_CHECKS=1")
target_db.execute("COMMIT")
```

### Monitoring Performance

```python
import time
from datetime import datetime

start_time = time.time()

migration = FullDatabaseMigration(config)
stats = migration.execute()

elapsed = time.time() - start_time

print(f"\n{'='*60}")
print("PERFORMANCE REPORT")
print(f"{'='*60}")
print(f"Total Time: {elapsed/60:.2f} minutes")
print(f"Total Rows: {stats.migrated_rows:,}")
print(f"Average Rate: {stats.migrated_rows/elapsed:.0f} rows/second")
print(f"\nPer-Table Performance:")
for table, table_stats in stats.table_stats.items():
    print(f"  {table}: {table_stats['rows']:,} rows at {table_stats['rate']:.0f} rec/s")
print(f"{'='*60}")
```

---

## Troubleshooting

### Issue 1: Migration Takes Too Long

**Symptoms**:
- Migration running for hours/days
- Low throughput

**Solutions**:

1. Increase parallelism:
```python
parallel_tables=6  # More tables simultaneously
num_workers=10     # More workers per table
```

2. Use PARALLEL strategy:
```python
migration_strategy=MigrationStrategy.PARALLEL
```

3. Disable indexes during migration:
```python
create_indexes_after_data=True
```

4. Check network bandwidth (for remote migrations)

### Issue 2: Out of Memory

**Symptoms**:
- MemoryError
- System becomes unresponsive

**Solutions**:

1. Reduce chunk size:
```python
chunk_size=5000  # Smaller chunks
```

2. Reduce parallelism:
```python
parallel_tables=1
num_workers=2
```

3. Use STREAMING strategy:
```python
migration_strategy=MigrationStrategy.STREAMING
```

### Issue 3: Foreign Key Errors

**Symptoms**:
- "foreign key constraint fails"
- Constraint creation errors

**Solutions**:

1. Disable FK checks during migration:
```python
disable_foreign_keys_during_migration=True
```

2. Verify table creation order:
- Tool automatically sorts by dependencies
- Check logs for order

3. Manually verify constraints after migration

### Issue 4: Data Type Incompatibilities

**Symptoms**:
- "data type mismatch"
- "invalid input syntax"

**Solutions**:

1. Check supported type mappings
2. Use transformation functions (requires custom code)
3. Pre-create target schema with correct types

### Issue 5: Index Creation Failures

**Symptoms**:
- Indexes not created
- Partial index errors

**Solutions**:

1. Create indexes manually after migration
2. Check index compatibility between databases
3. Review index definitions in source

### Issue 6: Validation Fails

**Symptoms**:
- Row count mismatches
- Validation errors

**Solutions**:

1. Check for concurrent writes to source:
```python
# Lock source tables (read-only)
source_db.execute("LOCK TABLE users IN ACCESS SHARE MODE")
```

2. Re-run validation manually:
```python
from database_migration import DataValidator

for table in schema.tables.keys():
    source_count, target_count, match = DataValidator.validate_counts(
        source_db, target_db, table, table
    )
    if not match:
        print(f"Mismatch in {table}: {source_count} vs {target_count}")
```

3. Compare sample data manually

---

## Best Practices Checklist

### Pre-Migration

```
□ Backup source database
□ Test migration on subset/copy
□ Verify target database is empty
□ Check available disk space (2-3x database size)
□ Verify network connectivity and bandwidth
□ Schedule maintenance window
□ Notify stakeholders
□ Prepare rollback plan
□ Test application with target database
□ Document custom transformations needed
```

### During Migration

```
□ Monitor progress logs
□ Watch system resources (CPU, memory, disk I/O)
□ Keep database connections minimal
□ Don't run other heavy operations
□ Have DBA available for issues
□ Monitor source database performance
```

### Post-Migration

```
□ Run validation
□ Compare row counts for all tables
□ Test sample queries
□ Rebuild/analyze statistics
□ Re-enable monitoring/alerts
□ Update application connection strings
□ Test application thoroughly
□ Monitor performance for 24-48 hours
□ Archive migration logs
□ Document lessons learned
□ Schedule source database decommission
```

---

## Output Files

### Migration Report (JSON)

**File**: `full_migration_report_YYYYMMDD_HHMMSS.json`

```json
{
  "migration_type": "full_database",
  "timestamp": "2024-03-15T12:00:00",
  "configuration": {
    "source": "postgresql",
    "target": "mysql",
    "strategy": "parallel",
    "parallel_tables": 3,
    "chunk_size": 10000,
    "num_workers": 6
  },
  "statistics": {
    "start_time": "2024-03-15T10:00:00",
    "end_time": "2024-03-15T12:00:00",
    "total_tables": 45,
    "migrated_tables": 45,
    "failed_tables": 0,
    "total_rows": 125430000,
    "migrated_rows": 125430000,
    "total_indexes": 178,
    "created_indexes": 178,
    "total_constraints": 89,
    "created_constraints": 89,
    "total_views": 12,
    "created_views": 12,
    "errors": []
  },
  "summary": {
    "status": "SUCCESS",
    "total_time": "120.00 minutes",
    "average_rate": "17,405 rows/second"
  },
  "table_stats": {
    "users": {
      "rows": 5000000,
      "time": 235.5,
      "rate": 21234
    },
    "orders": {
      "rows": 25000000,
      "time": 1185.2,
      "rate": 21097
    }
  }
}
```

### Log File

**File**: `full_migration_YYYYMMDD_HHMMSS.log`

Contains detailed logs of entire migration process including:
- Phase-by-phase progress
- Table-by-table migration details
- Error messages and stack traces
- Performance metrics
- Validation results

---

## Summary

The Full Database Migration Tool provides enterprise-grade capabilities for migrating entire databases:

✅ **Complete**: Migrates schema, data, indexes, constraints, and views  
✅ **Fast**: Parallel processing for optimal performance  
✅ **Reliable**: Validation, error handling, and detailed logging  
✅ **Flexible**: Configure what to migrate and how  
✅ **Resume**: Checkpoint support for large migrations  
✅ **Cross-Platform**: Works across different database types  

**Quick Reference**:

```python
# Simplest usage
config = FullMigrationConfig(
    source_db_type='postgresql',
    source_params={'host': 'old', 'database': 'db', 'user': 'u', 'password': 'p'},
    target_db_type='postgresql',
    target_params={'host': 'new', 'database': 'db', 'user': 'u', 'password': 'p'}
)

migration = FullDatabaseMigration(config)
stats = migration.execute()
```

**For massive databases (100GB+)**, use:
- `parallel_tables=6-8`
- `num_workers=8-10`
- `create_indexes_after_data=True`
- `disable_foreign_keys_during_migration=True`

**Always test first** on a copy or subset! 🚀# Full Database Migration - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [What Gets Migrated](#what-gets-migrated)
3. [Migration Phases](#migration-phases)
4. [Quick Start Examples](#quick-start-examples)
5. [Configuration Options](#configuration-options)
6. [CLI Usage](#cli-usage)
7. [Migration Strategies](#migration-strategies)
8. [Real-World Scenarios](#real-world-scenarios)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **Full Database Migration Tool** migrates entire databases including schema, data, indexes, constraints, views, and more. It's designed for:

- **Complete Database Migrations**: Move entire databases between servers
- **Database Upgrades**: Migrate to newer database versions
- **Cloud Migrations**: Move on-premise databases to cloud (AWS, Azure, GCP)
- **Cross-Database Migrations**: PostgreSQL → MySQL, MySQL → PostgreSQL, etc.
- **Backup & Cloning**: Create complete database copies

### Key Features

✅ **Complete Schema Migration**: Tables, columns, data types, primary keys  
✅ **Data Migration**: All table data with optimized batch processing  
✅ **Index Migration**: All indexes including unique, composite, and partial indexes  
✅ **Constraint Migration**: Foreign keys, check constraints, unique constraints  
✅ **View Migration**: Database views with dependencies  
✅ **Sequence Migration**: Auto-increment sequences (PostgreSQL)  
✅ **Parallel Processing**: Migrate multiple tables simultaneously  
✅ **Validation**: Automatic data validation and integrity checks  
✅ **Progress Tracking**: Real-time progress for each phase  
✅ **Resume Capability**: Resume interrupted migrations  

---

## What Gets Migrated

### Automatically Migrated

| Component | Description | Configurable |
|-----------|-------------|--------------|
| **Tables** | Table structure and definitions | ✓ |
| **Columns** | All columns with data types | ✓ |
| **Primary Keys** | Primary key constraints | ✓ |
| **Data** | All table data | ✓ |
| **Indexes** | All indexes (unique, composite, etc.) | ✓ |
| **Foreign Keys** | Foreign key constraints | ✓ |
| **Check Constraints** | Check constraints | ✓ |
| **Unique Constraints** | Unique constraints | ✓ |
| **Views** | Database views | ✓ |
| **Sequences** | Auto-increment sequences | ✓ |

### Not Migrated (Manual Steps Required)

- **Users & Permissions**: Must be recreated manually
- **Stored Procedures**: Database-specific, requires manual migration
- **Functions**: Database-specific syntax varies
- **Triggers**: Database-specific, requires manual migration
- **Tablespaces**: Database-specific configuration
- **Extensions**: Must be installed separately (e.g., PostGIS)

---

## Migration Phases

The tool executes migration in **7 distinct phases**:

```
Phase 1: SCHEMA EXTRACTION
    ├── Connect to source database
    ├── Extract table definitions
    ├── Extract column information
    ├── Extract primary keys
    ├── Extract foreign keys
    ├── Extract indexes
    ├── Extract constraints
    ├── Extract views
    └── Extract sequences

Phase 2: SCHEMA CREATION
    ├── Connect to target database
    ├── Create tables (sorted by dependencies)
    ├── Create primary keys
    └── Skip indexes/constraints (if configured)

Phase 3: DATA MIGRATION
    ├── For each table (parallel or sequential):
    │   ├── Extract data in chunks
    │   ├── Apply transformations (if any)
    │   ├── Batch insert to target
    │   └── Track progress
    └── Report statistics

Phase 4: INDEX CREATION
    ├── For each table:
    │   ├── Create unique indexes
    │   ├── Create composite indexes
    │   └── Create regular indexes

Phase 5: CONSTRAINT CREATION
    ├── For each table:
    │   ├── Create foreign key constraints
    │   ├── Create check constraints
    │   └── Create unique constraints

Phase 6: VIEW CREATION
    ├── For each view:
    │   └── Create view definition

Phase 7: VALIDATION
    ├── For each table:
    │   ├── Compare row counts
    │   ├── Verify data integrity
    │   └── Report mismatches
    └── Generate final report
```

### Why This Order?

1. **Schema First**: Tables must exist before data
2. **Data Before Indexes**: Faster to insert data without indexes
3. **Indexes Before Constraints**: Some constraints need indexes
4. **Constraints Last**: All referenced tables must exist
5. **Views Last**: All dependent tables must exist
6. **Validation Final**: Verify after everything is complete

---

## Quick Start Examples

### Example 1: Simple Database Migration

```python
from full_database_migration import FullMigrationConfig, FullDatabaseMigration, MigrationStrategy

# Configuration
config = FullMigrationConfig(
    # Source database
    source_db_type='postgresql',
    source_params={
        'host': 'old-server.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    # Target database
    target_db_type='postgresql',
    target_params={
        'host': 'new-server.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    # What to migrate
    include_schema=True,
    include_data=True,
    include_indexes=True,
    include_constraints=True,
    include_views=True,
    
    # Performance
    migration_strategy=MigrationStrategy.PARALLEL,
    parallel_tables=3,
    num_workers=6,
    chunk_size=10000
)

# Execute
migration = FullDatabaseMigration(config)
stats = migration.execute()

print(f"Migrated {stats.migrated_tables} tables")
print(f"Total rows: {stats.migrated_rows:,}")
```

**Console Output**:
```
============================================================
FULL DATABASE MIGRATION
============================================================

============================================================
PHASE 1: SCHEMA EXTRACTION
============================================================
2024-03-15 10:00:01 - SchemaExtractor - INFO - Extracting database schema...
2024-03-15 10:00:05 - SchemaExtractor - INFO - Found 45 tables to migrate
2024-03-15 10:00:15 - SchemaExtractor - INFO - ✓ Extracted schema:
  - Tables: 45
  - Total rows: 125,430,000
  - Indexes: 178
  - Views: 12

============================================================
PHASE 2: SCHEMA CREATION
============================================================
2024-03-15 10:00:20 - SchemaCreator - INFO - Creating database schema...
2024-03-15 10:00:22 - SchemaCreator - INFO - ✓ Created table: users
2024-03-15 10:00:23 - SchemaCreator - INFO - ✓ Created table: orders
...
2024-03-15 10:01:30 - SchemaCreator - INFO - ✓ Created 45 tables

============================================================
PHASE 3: DATA MIGRATION
============================================================
2024-03-15 10:01:35 - FullDatabaseMigration - INFO - Using 3 parallel workers for tables

Migrating table: users (5,000,000 rows)
2024-03-15 10:05:30 - FullDatabaseMigration - INFO - ✓ Completed users: 5,000,000 rows in 3.92 min (21,250 rec/s)

Migrating table: orders (25,000,000 rows)
2024-03-15 10:25:15 - FullDatabaseMigration - INFO - ✓ Completed orders: 25,000,000 rows in 19.75 min (21,097 rec/s)

...

============================================================
PHASE 4: INDEX CREATION
============================================================
2024-03-15 11:30:00 - FullDatabaseMigration - INFO - ✓ Created 4 indexes for users
2024-03-15 11:35:00 - FullDatabaseMigration - INFO - ✓ Created 8 indexes for orders
...

============================================================
PHASE 5: CONSTRAINT CREATION
============================================================
2024-03-15 11:45:00 - FullDatabaseMigration - INFO - ✓ Created 3 constraints for orders
...

============================================================
PHASE 6: VIEW CREATION
============================================================
2024-03-15 11:50:00 - FullDatabaseMigration - INFO - ✓ Created view: user_orders_summary
...

============================================================
PHASE 7: VALIDATION
============================================================
2024-03-15 11:55:00 - FullDatabaseMigration - INFO - ✓ users: 5,000,000 rows match
2024-03-15 11:55:05 - FullDatabaseMigration - INFO - ✓ orders: 25,000,000 rows match
...
2024-03-15 12:00:00 - FullDatabaseMigration - INFO - ✓ All tables validated successfully

============================================================
MIGRATION COMPLETE
============================================================
Report saved to: full_migration_report_20240315_120000.json

Summary:
  Tables: 45/45
  Rows: 125,430,000/125,430,000
  Time: 120.42 minutes
  Rate: 17,370 rows/second
  Errors: 0
============================================================
```

### Example 2: Cross-Database Migration (PostgreSQL → MySQL)

```python
config = FullMigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'postgres-server.com',
        'database': 'myapp',
        'user': 'postgres',
        'password': 'pg_password'
    },
    
    target_db_type='mysql',
    target_params={
        'host': 'mysql-server.com',
        'database': 'myapp',
        'user': 'root',
        'password': 'mysql_password'
    },
    
    # Full migration
    include_schema=True,
    include_data=True,
    include_indexes=True,
    include_constraints=True,

    # Parallel processing
    migration_strategy=MigrationStrategy.PARALLEL,
    parallel_tables=4,
    num_workers=8,
    
    # Optimization
    create_indexes_after_data=True,
    disable_foreign_keys_during_migration=True
)

migration = FullDatabaseMigration(config)
stats = migration.execute()
```

### Example 3: Schema-Only Migration

```python
config = FullMigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'production.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'development.company.com',
        'database': 'development',
        'user': 'postgres',
        'password': 'password'
    },
    
    # Schema only - no data
    include_schema=True,
    include_data=False,  # Skip data migration
    include_indexes=True,
    include_constraints=True,
    include_views=True
)

migration = FullDatabaseMigration(config)
stats = migration.execute()

print("Schema migration completed!")
print(f"Created {stats.migrated_tables} tables")
print(f"Created {stats.created_indexes} indexes")
print(f"Created {stats.created_constraints} constraints")
print(f"Created {stats.created_views} views")
```

### Example 4: Selective Table Migration

```python
config = FullMigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'source.company.com',
        'database': 'ecommerce',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'target.company.com',
        'database': 'ecommerce_backup',
        'user': 'postgres',
        'password': 'password'
    },
    
    # Only migrate specific tables
    include_tables=['users', 'orders', 'products', 'payments'],
    
    # OR exclude specific tables
    # exclude_tables=['temp_data', 'logs', 'sessions'],
    
    include_schema=True,
    include_data=True,
    migration_strategy=MigrationStrategy.PARALLEL,
    parallel_tables=2
)

migration = FullDatabaseMigration(config)
stats = migration.execute()
```

---

## Configuration Options

### FullMigrationConfig Parameters

#### Connection Parameters

```python
source_db_type: str          # 'postgresql', 'mysql', 'sqlite', etc.
source_params: Dict          # Connection parameters for source
target_db_type: str          # Target database type
target_params: Dict          # Connection parameters for target
```

**Example**:
```python
source_params = {
    'host': 'db.company.com',
    'port': 5432,
    'database': 'production',
    'user': 'readonly_user',
    'password': 'secure_password',
    'timeout': 60
}
```

#### Migration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_schema` | bool | True | Migrate table schemas |
| `include_data` | bool | True | Migrate table data |
| `include_indexes` | bool | True | Migrate indexes |
| `include_constraints` | bool | True | Migrate constraints |
| `include_views` | bool | True | Migrate views |
| `include_sequences` | bool | True | Migrate sequences |
| `include_functions` | bool | False | Migrate functions (experimental) |
| `include_triggers` | bool | False | Migrate triggers (experimental) |

#### Table Filtering

```python
# Include only specific tables
include_tables = ['users', 'orders', 'products']

# Exclude specific tables
exclude_tables = ['temp_data', 'logs', 'cache', 'sessions']
```

#### Performance Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `migration_strategy` | MigrationStrategy | PARALLEL | CHUNKED, PARALLEL, or STREAMING |
| `chunk_size` | int | 10000 | Records per chunk |
| `num_workers` | int | 4 | Workers per table |
| `parallel_tables` | int | 3 | Tables to migrate simultaneously |

#### Advanced Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `create_indexes_after_data` | bool | True | Create indexes after data (faster) |
| `disable_foreign_keys_during_migration` | bool | True | Disable FKs during migration |
| `use_bulk_copy` | bool | True | Use native bulk copy tools |
| `compression` | bool | False | Use compression for transfer |

#### Validation Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_validation` | bool | True | Validate after migration |
| `validate_row_counts` | bool | True | Validate row counts |
| `validate_sample_data` | bool | False | Validate sample data checksums |

---

## CLI Usage

### Basic Syntax

```bash
python full_database_migration.py \
  --source-type postgresql \
  --source-host source-db.com \
  --source-db production \
  --source-user postgres \
  --source-password password \
  --target-type mysql \
  --target-host target-db.com \
  --target-db production \
  --target-user root \
  --target-password password
```