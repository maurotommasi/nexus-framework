# Database Migration Tool - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [Migration Strategies](#migration-strategies)
6. [Input Examples](#input-examples)
7. [Output Examples](#output-examples)
8. [Use Cases](#use-cases)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Enterprise Database Migration Tool is designed to handle massive data migrations (from thousands to billions of records) with enterprise-grade reliability, featuring:

- **Multiple Strategies**: Chunked, Parallel, and Streaming migrations
- **Resumability**: Checkpoint system to resume interrupted migrations
- **Validation**: Automatic data validation and integrity checks
- **Transformation**: Apply custom transformations during migration
- **Monitoring**: Real-time progress tracking and performance metrics
- **Error Recovery**: Automatic retry with exponential backoff

### Supported Databases

- PostgreSQL
- MySQL / MariaDB
- SQLite
- MongoDB
- Oracle
- SQL Server
- Redis
- Cassandra
- Elasticsearch

---

## How It Works

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    MIGRATION PROCESS                         │
└─────────────────────────────────────────────────────────────┘

1. INITIALIZATION
   ├── Load Configuration
   ├── Connect to Source & Target Databases
   ├── Check for Existing Checkpoint (if resume enabled)
   └── Calculate Total Records & ID Range

2. DATA EXTRACTION (Source Database)
   ├── Query records in chunks/ranges
   ├── Apply WHERE clause filters (if any)
   └── Order by Primary Key

3. DATA TRANSFORMATION (Optional)
   ├── Apply custom transformation function
   ├── Map columns
   └── Convert data types

4. DATA LOADING (Target Database)
   ├── Batch insert records
   ├── Retry on failure
   └── Update progress metrics

5. VALIDATION
   ├── Compare record counts
   ├── Verify data integrity
   └── Generate checksums (optional)

6. COMPLETION
   ├── Generate migration report
   ├── Save statistics
   └── Clean up resources
```

### Chunked Migration Flow

```
Source DB                Migration Engine              Target DB
    │                           │                          │
    │  1. Query: Get total      │                          │
    │     records & ID range    │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │  2. Fetch Chunk 1         │                          │
    │     (ID 1-10000)          │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │  3. Return 10K records    │                          │
    │<──────────────────────────┤                          │
    │                           │                          │
    │                           │  4. Transform (optional) │
    │                           │                          │
    │                           │  5. Insert Chunk 1       │
    │                           ├─────────────────────────>│
    │                           │                          │
    │                           │  6. Save Checkpoint      │
    │                           │                          │
    │  7. Fetch Chunk 2         │                          │
    │     (ID 10001-20000)      │                          │
    ├──────────────────────────>│                          │
    │                           │                          │
    │  ... (repeat for all chunks) ...                     │
    │                           │                          │
    │  N. Validate counts       │                          │
    ├──────────────────────────>│                          │
    │                           ├─────────────────────────>│
    │                           │                          │
    │                           │  Generate Report         │
```

### Parallel Migration Flow

```
Source DB         Worker 1    Worker 2    Worker 3    Worker 4    Target DB
    │                │           │           │           │            │
    │  1. Calculate ID ranges for each worker                        │
    │                │           │           │           │            │
    │  ID 1-25K      │           │           │           │            │
    ├───────────────>│           │           │           │            │
    │                │           │           │           │            │
    │  ID 25K-50K    │           │           │           │            │
    ├───────────────────────────>│           │           │            │
    │                │           │           │           │            │
    │  ID 50K-75K    │           │           │           │            │
    ├───────────────────────────────────────>│           │            │
    │                │           │           │           │            │
    │  ID 75K-100K   │           │           │           │            │
    ├───────────────────────────────────────────────────>│            │
    │                │           │           │           │            │
    │  All workers process their ranges in parallel                  │
    │                │           │           │           │            │
    │                │ Insert ───────────────────────────────────────>│
    │                │           │ Insert ───────────────────────────>│
    │                │           │           │ Insert ───────────────>│
    │                │           │           │           │  Insert ──>│
```

---

## Architecture

### Class Hierarchy

```
MigrationOrchestrator
    │
    ├── MigrationConfig (Data Class)
    │   ├── source_db_type
    │   ├── source_params
    │   ├── target_db_type
    │   ├── target_params
    │   ├── strategy (CHUNKED/PARALLEL/STREAMING)
    │   └── ... other settings
    │
    ├── BaseMigration (Abstract)
    │   ├── _create_connections()
    │   ├── _get_total_records()
    │   ├── _transform_records()
    │   ├── _insert_batch()
    │   ├── _validate_migration()
    │   └── ... common methods
    │
    ├── ChunkedMigration (extends BaseMigration)
    │   └── execute()
    │
    ├── ParallelMigration (extends BaseMigration)
    │   ├── execute()
    │   └── _migrate_range()
    │
    └── StreamingMigration (extends BaseMigration)
        └── execute()

Supporting Classes:
    ├── MigrationStats (Data Class)
    ├── MigrationCheckpoint
    └── DataValidator
```

### Key Components

#### 1. MigrationConfig
Holds all configuration parameters for the migration.

#### 2. BaseMigration
Base class with common functionality for all strategies.

#### 3. Strategy Classes
- **ChunkedMigration**: Sequential processing in chunks
- **ParallelMigration**: Concurrent processing with multiple workers
- **StreamingMigration**: Memory-efficient streaming

#### 4. MigrationCheckpoint
Manages checkpoint saving/loading for resumability.

#### 5. DataValidator
Validates migrated data integrity.

#### 6. MigrationStats
Tracks and reports migration statistics.

---

## Configuration

### MigrationConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_db_type` | str | Required | Source database type ('postgresql', 'mysql', etc.) |
| `source_params` | Dict | Required | Source connection parameters |
| `target_db_type` | str | Required | Target database type |
| `target_params` | Dict | Required | Target connection parameters |
| `source_table` | str | Required | Source table name |
| `target_table` | str | Required | Target table name |
| `primary_key` | str | 'id' | Primary key column for chunking |
| `strategy` | MigrationStrategy | CHUNKED | Migration strategy |
| `chunk_size` | int | 10000 | Records per chunk |
| `num_workers` | int | 4 | Number of parallel workers |
| `batch_size` | int | 1000 | Batch insert size |
| `where_clause` | str | None | Filter condition (e.g., "created_at > '2024-01-01'") |
| `transform_function` | Callable | None | Custom transformation function |
| `enable_validation` | bool | True | Enable data validation |
| `enable_checkpoints` | bool | True | Enable checkpoint system |
| `checkpoint_interval` | int | 100000 | Records between checkpoints |
| `max_retries` | int | 3 | Maximum retry attempts |
| `retry_delay` | float | 5.0 | Delay between retries (seconds) |
| `skip_existing` | bool | False | Skip existing records |
| `resume_from_checkpoint` | bool | False | Resume from last checkpoint |

---

## Migration Strategies

### 1. Chunked Migration (CHUNKED)

**Best For**: 
- Most use cases
- 1M - 100M+ records
- Single-server migrations
- When you need checkpoints and resumability

**How It Works**:
- Processes data sequentially in chunks
- Uses ID range-based pagination
- Saves checkpoints periodically
- Low memory footprint

**Pros**:
- Reliable and predictable
- Easy to debug
- Checkpoint support
- Low resource usage

**Cons**:
- Slower than parallel
- Single-threaded

**Configuration**:
```python
strategy=MigrationStrategy.CHUNKED
chunk_size=10000  # Adjust based on your needs
```

### 2. Parallel Migration (PARALLEL)

**Best For**:
- Very large datasets (100M+ records)
- When speed is critical
- Multi-core servers
- Network bandwidth is not the bottleneck

**How It Works**:
- Divides ID range into segments
- Each worker processes a segment independently
- All workers run concurrently
- Results are aggregated

**Pros**:
- Fastest option
- Utilizes multiple CPU cores
- Scales with worker count

**Cons**:
- Higher resource usage
- More complex error handling
- Can overwhelm target database

**Configuration**:
```python
strategy=MigrationStrategy.PARALLEL
num_workers=8  # Adjust based on CPU cores and DB capacity
chunk_size=5000  # Smaller chunks for parallel processing
```

### 3. Streaming Migration (STREAMING)

**Best For**:
- Memory-constrained environments
- Continuous data flow
- Real-time migrations

**How It Works**:
- Fetches records in small batches
- Processes and inserts immediately
- Minimal memory buffering

**Pros**:
- Very low memory usage
- Suitable for constrained environments

**Cons**:
- Slower than other strategies
- Limited checkpoint granularity

**Configuration**:
```python
strategy=MigrationStrategy.STREAMING
batch_size=1000
```

---

## Input Examples

### Example 1: Basic Migration (10M Records)

```python
from database_migration import MigrationConfig, MigrationOrchestrator, MigrationStrategy

# Configuration
config = MigrationConfig(
    # Source database (PostgreSQL)
    source_db_type='postgresql',
    source_params={
        'host': 'source-db.company.com',
        'port': 5432,
        'database': 'production',
        'user': 'readonly_user',
        'password': 'secure_password',
        'timeout': 30
    },
    
    # Target database (MySQL)
    target_db_type='mysql',
    target_params={
        'host': 'target-db.company.com',
        'port': 3306,
        'database': 'production_new',
        'user': 'migration_user',
        'password': 'secure_password',
        'timeout': 30
    },
    
    # Table configuration
    source_table='users',
    target_table='users',
    primary_key='id',
    
    # Migration settings
    strategy=MigrationStrategy.CHUNKED,
    chunk_size=10000,
    enable_validation=True,
    enable_checkpoints=True
)

# Execute migration
orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()

# Print results
print(f"Migrated: {stats.migrated_records:,} records")
print(f"Time: {stats.elapsed_seconds/60:.2f} minutes")
```

**Expected Console Output**:
```
2024-03-15 10:00:00 - ChunkedMigration - INFO - Starting chunked migration: users -> users
2024-03-15 10:00:01 - ChunkedMigration - INFO - Total records to migrate: 10,000,000
2024-03-15 10:00:01 - ChunkedMigration - INFO - ID range: 1 to 10000000
2024-03-15 10:05:00 - ChunkedMigration - INFO - Progress: 1,000,000/10,000,000 (10.00%) | Rate: 3333 rec/s | ETA: 27.0 min
2024-03-15 10:10:00 - ChunkedMigration - INFO - Progress: 2,000,000/10,000,000 (20.00%) | Rate: 3333 rec/s | ETA: 24.0 min
...
2024-03-15 10:30:00 - ChunkedMigration - INFO - Validating migration...
2024-03-15 10:30:05 - ChunkedMigration - INFO - Source records: 10,000,000, Target records: 10,000,000
2024-03-15 10:30:05 - ChunkedMigration - INFO - ✓ Validation passed: Record counts match
2024-03-15 10:30:05 - ChunkedMigration - INFO - ✓ Migration completed successfully
2024-03-15 10:30:05 - MigrationOrchestrator - INFO - Migration report saved to: migration_report_20240315_103005.json

Migrated: 10,000,000 records
Time: 30.08 minutes
```

### Example 2: Parallel Migration (100M Records)

```python
config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'large-db.company.com',
        'database': 'analytics',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'new-analytics-db.company.com',
        'database': 'analytics_v2',
        'user': 'postgres',
        'password': 'password'
    },
    
    source_table='events',
    target_table='events',
    primary_key='event_id',
    
    # Parallel settings
    strategy=MigrationStrategy.PARALLEL,
    num_workers=8,
    chunk_size=5000,
    
    # Only migrate recent data
    where_clause="created_at >= '2024-01-01'",
    
    enable_validation=True
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()
```

**Expected Console Output**:
```
2024-03-15 14:00:00 - ParallelMigration - INFO - Starting parallel migration with 8 workers
2024-03-15 14:00:01 - ParallelMigration - INFO - Total records: 100,000,000, Range: 1 to 100000000
2024-03-15 14:00:01 - ParallelMigration - INFO - Created 8 work ranges
2024-03-15 14:00:01 - ParallelMigration - INFO - Worker 0: Processing range 1 to 12500000
2024-03-15 14:00:01 - ParallelMigration - INFO - Worker 1: Processing range 12500001 to 25000000
2024-03-15 14:00:01 - ParallelMigration - INFO - Worker 2: Processing range 25000001 to 37500000
...
2024-03-15 14:25:30 - ParallelMigration - INFO - Worker 0 completed: 12,500,000 records
2024-03-15 14:26:15 - ParallelMigration - INFO - Worker 3 completed: 12,500,000 records
...
2024-03-15 14:30:00 - ParallelMigration - INFO - Validating migration...
2024-03-15 14:30:10 - ParallelMigration - INFO - ✓ Validation passed: Record counts match
2024-03-15 14:30:10 - MigrationOrchestrator - INFO - Migration report saved to: migration_report_20240315_143010.json
```

### Example 3: Migration with Data Transformation

```python
# Define transformation function
def transform_user_data(record):
    """Transform user data during migration"""
    return {
        'user_id': record['id'],
        'full_name': f"{record['first_name']} {record['last_name']}".strip(),
        'email_address': record['email'].lower(),
        'registration_date': record['created_at'],
        'is_active': 1 if record['status'] == 'active' else 0,
        'migrated_at': datetime.now()
    }

config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'old-system.com',
        'database': 'legacy_db',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='mysql',
    target_params={
        'host': 'new-system.com',
        'database': 'modern_db',
        'user': 'root',
        'password': 'password'
    },
    
    source_table='legacy_users',
    target_table='users',
    
    # Apply transformation
    transform_function=transform_user_data,
    
    strategy=MigrationStrategy.CHUNKED,
    chunk_size=5000
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()
```

**Input Data (Source)**:
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "JOHN.DOE@EXAMPLE.COM",
  "status": "active",
  "created_at": "2024-01-15 10:30:00"
}
```

**Output Data (Target)**:
```json
{
  "user_id": 1,
  "full_name": "John Doe",
  "email_address": "john.doe@example.com",
  "registration_date": "2024-01-15 10:30:00",
  "is_active": 1,
  "migrated_at": "2024-03-15 14:30:00"
}
```

### Example 4: Resumable Migration with Checkpoints

```python
config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'db.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'backup-db.company.com',
        'database': 'production_backup',
        'user': 'postgres',
        'password': 'password'
    },
    
    source_table='transactions',
    target_table='transactions',
    
    strategy=MigrationStrategy.CHUNKED,
    chunk_size=10000,
    
    # Checkpoint configuration
    enable_checkpoints=True,
    checkpoint_interval=100000,  # Save every 100K records
    resume_from_checkpoint=True  # Resume if interrupted
)

# First run (interrupted at 5M records)
orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()  # Interrupted by Ctrl+C

# Second run (resumes from checkpoint)
orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()  # Continues from 5M records
```

**Checkpoint File (migration_checkpoint.json)**:
```json
{
  "last_id": 5000000,
  "migrated_records": 5000000,
  "chunk_number": 500,
  "timestamp": "2024-03-15T12:30:45.123456",
  "config": {
    "source_table": "transactions",
    "target_table": "transactions",
    "chunk_size": 10000
  }
}
```

**Console Output (Resume)**:
```
2024-03-15 13:00:00 - ChunkedMigration - INFO - Resuming from checkpoint: ID 5000000, 5,000,000 records
2024-03-15 13:05:00 - ChunkedMigration - INFO - Progress: 6,000,000/20,000,000 (30.00%) | Rate: 3333 rec/s | ETA: 70.0 min
...
```

### Example 5: Conditional Migration (Filtered Data)

```python
config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'db.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'analytics-db.company.com',
        'database': 'analytics',
        'user': 'postgres',
        'password': 'password'
    },
    
    source_table='orders',
    target_table='orders_2024',
    
    # Only migrate orders from 2024
    where_clause="order_date >= '2024-01-01' AND order_date < '2025-01-01' AND status = 'completed'",
    
    strategy=MigrationStrategy.CHUNKED,
    chunk_size=10000
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()
```

---

## Output Examples

### 1. Migration Report (JSON)

**File**: `migration_report_20240315_143010.json`

```json
{
  "configuration": {
    "source_db_type": "postgresql",
    "source_params": {
      "host": "source-db.company.com",
      "database": "production",
      "user": "postgres"
    },
    "target_db_type": "mysql",
    "target_params": {
      "host": "target-db.company.com",
      "database": "production_new",
      "user": "root"
    },
    "source_table": "users",
    "target_table": "users",
    "primary_key": "id",
    "strategy": "chunked",
    "chunk_size": 10000,
    "num_workers": 4,
    "batch_size": 1000,
    "where_clause": null,
    "enable_validation": true,
    "enable_checkpoints": true,
    "checkpoint_interval": 100000,
    "max_retries": 3,
    "retry_delay": 5.0
  },
  "statistics": {
    "total_records": 10000000,
    "migrated_records": 10000000,
    "failed_records": 0,
    "skipped_records": 0,
    "start_time": "2024-03-15T10:00:00.123456",
    "end_time": "2024-03-15T10:30:05.654321",
    "elapsed_seconds": 1805.53,
    "current_rate": 5539.2,
    "average_rate": 5539.2,
    "errors": []
  },
  "summary": {
    "status": "SUCCESS",
    "completion_rate": "100.00%",
    "average_speed": "5539 records/second",
    "total_time": "30.09 minutes"
  }
}
```

### 2. Log File Output

**File**: `migration_20240315_100000.log`

```
2024-03-15 10:00:00,123 - ChunkedMigration - INFO - Starting chunked migration: users -> users
2024-03-15 10:00:01,456 - ChunkedMigration - INFO - Total records to migrate: 10,000,000
2024-03-15 10:00:01,789 - ChunkedMigration - INFO - ID range: 1 to 10000000
2024-03-15 10:05:00,234 - ChunkedMigration - INFO - Progress: 1,000,000/10,000,000 (10.00%) | Rate: 3333 rec/s | ETA: 27.0 min
2024-03-15 10:10:00,567 - ChunkedMigration - INFO - Progress: 2,000,000/10,000,000 (20.00%) | Rate: 3333 rec/s | ETA: 24.0 min
2024-03-15 10:15:00,890 - ChunkedMigration - INFO - Progress: 3,000,000/10,000,000 (30.00%) | Rate: 3333 rec/s | ETA: 21.0 min
2024-03-15 10:20:00,123 - ChunkedMigration - INFO - Progress: 4,000,000/10,000,000 (40.00%) | Rate: 3333 rec/s | ETA: 18.0 min
2024-03-15 10:25:00,456 - ChunkedMigration - INFO - Progress: 5,000,000/10,000,000 (50.00%) | Rate: 3333 rec/s | ETA: 15.0 min
2024-03-15 10:30:00,789 - ChunkedMigration - INFO - Validating migration...
2024-03-15 10:30:05,012 - ChunkedMigration - INFO - Source records: 10,000,000, Target records: 10,000,000
2024-03-15 10:30:05,345 - ChunkedMigration - INFO - ✓ Validation passed: Record counts match
2024-03-15 10:30:05,678 - ChunkedMigration - INFO - ✓ Migration completed successfully
2024-03-15 10:30:05,901 - MigrationOrchestrator - INFO - Migration report saved to: migration_report_20240315_103005.json
```

### 3. MigrationStats Object

```python
# After migration completes
stats = orchestrator.execute()

# Access statistics
print(f"Total Records: {stats.total_records:,}")
print(f"Migrated: {stats.migrated_records:,}")
print(f"Failed: {stats.failed_records:,}")
print(f"Skipped: {stats.skipped_records:,}")
print(f"Duration: {stats.elapsed_seconds/60:.2f} minutes")
print(f"Average Rate: {stats.average_rate:.0f} records/second")

# Check errors
if stats.errors:
    print(f"\nErrors encountered: {len(stats.errors)}")
    for error in stats.errors:
        print(f"  - {error['timestamp']}: {error['error']}")
```

**Output**:
```
Total Records: 10,000,000
Migrated: 10,000,000
Failed: 0
Skipped: 0
Duration: 30.09 minutes
Average Rate: 5539 records/second
```

### 4. Error Handling Output

**Scenario**: Network interruption during migration

**Console Output**:
```
2024-03-15 10:15:30 - ChunkedMigration - WARNING - Batch insert failed (attempt 1): connection timeout
2024-03-15 10:15:35 - ChunkedMigration - INFO - Retrying batch insert...
2024-03-15 10:15:40 - ChunkedMigration - INFO - Batch insert successful on retry
2024-03-15 10:20:00 - ChunkedMigration - INFO - Progress: 4,000,000/10,000,000 (40.00%) | Rate: 3200 rec/s | ETA: 18.8 min
```

**Error in Report**:
```json
{
  "statistics": {
    "errors": [
      {
        "timestamp": "2024-03-15T10:15:30.123456",
        "error": "connection timeout",
        "records_count": 10000,
        "retry_count": 1,
        "resolved": true
      }
    ]
  }
}
```

---

## Use Cases

### Use Case 1: Database Upgrade (PostgreSQL 12 → PostgreSQL 15)

**Scenario**: Upgrading production database to new version

```python
config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'postgres12-prod.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'postgres15-prod.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    source_table='orders',
    target_table='orders',
    
    strategy=MigrationStrategy.PARALLEL,
    num_workers=6,
    chunk_size=5000,
    
    enable_validation=True,
    enable_checkpoints=True
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()
```

**Expected Timeline**:
- 50M records
- 6 parallel workers
- ~15 minutes total time

### Use Case 2: Cloud Migration (On-Premise → AWS RDS)

**Scenario**: Moving from on-premise PostgreSQL to AWS RDS

```python
config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': '192.168.1.100',  # On-premise
        'database': 'company_db',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'company-db.abc123.us-east-1.rds.amazonaws.com',  # AWS RDS
        'database': 'company_db',
        'user': 'admin',
        'password': 'aws_password'
    },
    
    source_table='customers',
    target_table='customers',
    
    strategy=MigrationStrategy.CHUNKED,
    chunk_size=5000,  # Smaller chunks for network transfer
    
    enable_checkpoints=True,
    checkpoint_interval=50000,  # More frequent checkpoints
    resume_from_checkpoint=True,
    
    max_retries=5,  # More retries for network issues
    retry_delay=10.0
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()
```

### Use Case 3: Cross-Database Migration (PostgreSQL → MongoDB)

**Scenario**: Migrating relational data to document store

```python
# Define transformation to convert relational to document structure
def transform_to_document(record):
    """Transform relational record to MongoDB document"""
    return {
        'user_id': record['id'],
        'profile': {
            'name': record['name'],
            'email': record['email'],
            'phone': record['phone']
        },
        'address': {
            'street': record['address_street'],
            'city': record['address_city'],
            'country': record['address_country']
        },
        'preferences': {
            'newsletter': record['newsletter_opt_in'],
            'notifications': record['notifications_enabled']
        },
        'metadata': {
            'created_at': record['created_at'],
            'updated_at': record['updated_at'],
            'migrated_at': datetime.now()
        }
    }

config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'postgres-db.company.com',
        'database': 'legacy_system',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='mongodb',
    target_params={
        'uri': 'mongodb://mongodb-cluster.company.com:27017',
        'database': 'modern_system'
    },
    
    source_table='users',
    target_table='users',  # MongoDB collection
    
    transform_function=transform_to_document,
    
    strategy=MigrationStrategy.CHUNKED,
    chunk_size=10000
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()
```

**Input (PostgreSQL)**:
```sql
id | name | email | phone | address_street | address_city | newsletter_opt_in
1  | John | j@ex.com | 555-0001 | 123 Main St | NYC | true
```

**Output (MongoDB)**:
```json
{
  "_id": ObjectId("..."),
  "user_id": 1,
  "profile": {
    "name": "John",
    "email": "j@ex.com",
    "phone": "555-0001"
  },
  "address": {
    "street": "123 Main St",
    "city": "NYC"
  },
  "preferences": {
    "newsletter": true
  },
  "metadata": {
    "migrated_at": "2024-03-15T14:30:00"
  }
}
```

### Use Case 4: Data Archival (Move Old Records)

**Scenario**: Archive old transactions to separate database

```python
config = MigrationConfig(
    source_db_type='postgresql',
    source_params={
        'host': 'production-db.company.com',
        'database': 'production',
        'user': 'postgres',
        'password': 'password'
    },
    
    target_db_type='postgresql',
    target_params={
        'host': 'archive-db.company.com',
        'database': 'archive',
        'user': 'postgres',
        'password': 'password'
    },
    
    source_table='transactions',
    target_table='transactions_archive',
    
    # Only migrate records older than 2 years
    where_clause="transaction_date < '2022-01-01'",
    
    strategy=MigrationStrategy.PARALLEL,
    num_workers=4,
    chunk_size=10000,
    
    enable_validation=True
)

orchestrator = MigrationOrchestrator(config)
stats = orchestrator.execute()

print(f"Archived {stats.migrated_records:,} old transactions")
```

### Use Case 5: Multi-Table Migration

**Scenario**: Migrate multiple related tables

```python
from database_migration import MigrationConfig, MigrationOrchestrator, MigrationStrategy

# Define tables to migrate
tables_to_migrate = [
    ('users', 'users', 'user_id'),
    ('orders', 'orders', 'order_id'),
    ('order_items', 'order_items', 'item_id'),
    ('payments', 'payments', 'payment_id'),
    ('reviews', 'reviews', 'review_id')
]

base_config = {
    'source_db_type': 'postgresql',
    'source_params': {
        'host': 'old-db.company.com',
        'database': 'ecommerce',
        'user': 'postgres',
        'password': 'password'
    },
    'target_db_type': 'mysql',
    'target_params': {
        'host': 'new-db.company.com',
        'database': 'ecommerce_v2',
        'user': 'root',
        'password': 'password'
    },
    'strategy': MigrationStrategy.PARALLEL,
    'num_workers': 6,
    'chunk_size': 5000,
    'enable_validation': True
}

# Migrate each table
total_migrated = 0
migration_results = []

for source_table, target_table, primary_key in tables_to_migrate:
    print(f"\n{'='*60}")
    print(f"Migrating: {source_table} → {target_table}")
    print(f"{'='*60}\n")
    
    config = MigrationConfig(
        **base_config,
        source_table=source_table,
        target_table=target_table,
        primary_key=primary_key
    )
    
    orchestrator = MigrationOrchestrator(config)
    stats = orchestrator.execute()
    
    total_migrated += stats.migrated_records
    migration_results.append({
        'table': source_table,
        'records': stats.migrated_records,
        'time': stats.elapsed_seconds
    })

# Summary report
print(f"\n{'='*60}")
print("MIGRATION SUMMARY - ALL TABLES")
print(f"{'='*60}")
for result in migration_results:
    print(f"{result['table']:20} {result['records']:>15,} records in {result['time']/60:>8.2f} min")
print(f"{'='*60}")
print(f"{'TOTAL':20} {total_migrated:>15,} records")
print(f"{'='*60}")
```

**Output**:
```
============================================================
MIGRATION SUMMARY - ALL TABLES
============================================================
users                        5,000,000 records in    15.30 min
orders                      25,000,000 records in    45.20 min
order_items                 75,000,000 records in   120.50 min
payments                    20,000,000 records in    38.10 min
reviews                     10,000,000 records in    22.40 min
============================================================
TOTAL                      135,000,000 records
============================================================
```

---

## Performance Tuning

### Optimizing Chunk Size

**Rule of Thumb**:
- Small datasets (< 1M): 5,000 - 10,000
- Medium datasets (1M - 10M): 10,000 - 20,000
- Large datasets (10M - 100M): 10,000 - 50,000
- Very large datasets (> 100M): 5,000 - 20,000 (with parallel)

**Example**: Finding optimal chunk size

```python
import time

# Test different chunk sizes
chunk_sizes = [5000, 10000, 20000, 50000]
results = []

for chunk_size in chunk_sizes:
    config = MigrationConfig(
        source_db_type='postgresql',
        source_params={...},
        target_db_type='postgresql',
        target_params={...},
        source_table='test_table',
        target_table='test_table_copy',
        chunk_size=chunk_size,
        # Test on subset
        where_clause="id <= 100000"
    )
    
    start = time.time()
    orchestrator = MigrationOrchestrator(config)
    stats = orchestrator.execute()
    elapsed = time.time() - start
    
    results.append({
        'chunk_size': chunk_size,
        'time': elapsed,
        'rate': stats.migrated_records / elapsed
    })

# Find best chunk size
best = max(results, key=lambda x: x['rate'])
print(f"Optimal chunk size: {best['chunk_size']} ({best['rate']:.0f} rec/s)")
```

### Optimizing Worker Count

**Formula**: `num_workers = min(CPU_cores, DB_max_connections / 2)`

```python
import multiprocessing

# Get CPU count
cpu_count = multiprocessing.cpu_count()

# Configure based on resources
if cpu_count >= 16:
    num_workers = 12  # Leave some CPUs for system
elif cpu_count >= 8:
    num_workers = 6
elif cpu_count >= 4:
    num_workers = 4
else:
    num_workers = 2

config = MigrationConfig(
    ...,
    strategy=MigrationStrategy.PARALLEL,
    num_workers=num_workers
)
```

### Database-Specific Optimizations

#### PostgreSQL

```python
# Before migration - disable autovacuum on target table
target_db.execute("ALTER TABLE users SET (autovacuum_enabled = false)")

# Run migration
orchestrator.execute()

# After migration - re-enable and run vacuum
target_db.execute("ALTER TABLE users SET (autovacuum_enabled = true)")
target_db.execute("VACUUM ANALYZE users")
```

#### MySQL

```python
# Before migration - disable keys for faster inserts
target_db.execute("ALTER TABLE users DISABLE KEYS")

# Run migration
orchestrator.execute()

# After migration - re-enable keys
target_db.execute("ALTER TABLE users ENABLE KEYS")
target_db.execute("OPTIMIZE TABLE users")
```

### Network Optimization

For cross-region migrations:

```python
config = MigrationConfig(
    ...,
    chunk_size=2000,  # Smaller chunks for network
    batch_size=500,   # Smaller batches
    max_retries=5,    # More retries
    retry_delay=10.0, # Longer delay
    num_workers=2     # Fewer workers to avoid overwhelming network
)
```

---

## Troubleshooting

### Issue 1: Migration Too Slow

**Symptoms**:
- Rate < 1000 records/second
- ETA shows hours/days

**Solutions**:

1. **Increase chunk size**:
```python
chunk_size=50000  # Larger chunks
```

2. **Use parallel strategy**:
```python
strategy=MigrationStrategy.PARALLEL
num_workers=8
```

3. **Disable constraints temporarily**:
```python
# Before migration
target_db.execute("ALTER TABLE users DISABLE TRIGGER ALL")
target_db.execute("ALTER TABLE users DROP CONSTRAINT users_email_key")

# Run migration
orchestrator.execute()

# After migration
target_db.execute("ALTER TABLE users ENABLE TRIGGER ALL")
target_db.execute("ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email)")
```

### Issue 2: Out of Memory

**Symptoms**:
- MemoryError exceptions
- System becomes unresponsive

**Solutions**:

1. **Reduce chunk size**:
```python
chunk_size=1000  # Much smaller
```

2. **Use streaming strategy**:
```python
strategy=MigrationStrategy.STREAMING
batch_size=500
```

3. **Reduce workers**:
```python
num_workers=2  # Fewer parallel workers
```

### Issue 3: Connection Timeouts

**Symptoms**:
- "connection timeout" errors
- Frequent retry attempts

**Solutions**:

1. **Increase connection timeout**:
```python
source_params={
    'host': 'db.company.com',
    'database': 'production',
    'user': 'postgres',
    'password': 'password',
    'timeout': 60  # Increase from default 10
}
```

2. **Configure retry settings**:
```python
max_retries=10
retry_delay=15.0
```

3. **Use connection pooling** (requires database.py enhancement):
```python
source_params={
    ...,
    'pool_size': 5,
    'max_overflow': 10
}
```

### Issue 4: Validation Fails

**Symptoms**:
- Record count mismatch
- "Validation failed" message

**Solutions**:

1. **Check for concurrent writes**:
```python
# Lock source table during migration
source_db.execute("LOCK TABLE users IN ACCESS SHARE MODE")
```

2. **Re-run validation manually**:
```python
from database_migration import DataValidator

validation_passed = DataValidator.validate_counts(
    source_db, target_db,
    'users', 'users',
    where_clause="created_at < '2024-03-15'"
)

if not validation_passed:
    # Identify missing records
    source_ids = set([r['id'] for r in source_db.fetch_all("SELECT id FROM users")])
    target_ids = set([r['id'] for r in target_db.fetch_all("SELECT id FROM users")])
    missing = source_ids - target_ids
    print(f"Missing IDs: {missing}")
```

3. **Disable validation temporarily**:
```python
enable_validation=False  # Run manual validation after
```

### Issue 5: Checkpoint Not Resuming

**Symptoms**:
- Migration restarts from beginning
- Checkpoint file not found

**Solutions**:

1. **Verify checkpoint file exists**:
```python
import os
if os.path.exists('migration_checkpoint.json'):
    print("Checkpoint file found")
else:
    print("No checkpoint file - starting fresh")
```

2. **Manually load checkpoint**:
```python
from database_migration import MigrationCheckpoint

checkpoint = MigrationCheckpoint()
data = checkpoint.load()

if data:
    print(f"Last checkpoint: {data['last_id']}")
    print(f"Migrated so far: {data['migrated_records']}")
```

3. **Force resume**:
```python
resume_from_checkpoint=True  # Ensure this is set
```

### Issue 6: Primary Key Gaps

**Symptoms**:
- Large gaps in ID sequences
- Workers finish at different times

**Solutions**:

1. **Use sequential strategy**:
```python
strategy=MigrationStrategy.CHUNKED  # Instead of PARALLEL
```

2. **Optimize ID range**:
```python
# Find actual ID distribution
source_db.execute("""
    SELECT 
        MIN(id) as min_id,
        MAX(id) as max_id,
        COUNT(*) as total,
        (MAX(id) - MIN(id)) / COUNT(*) as gap_ratio
    FROM users
""")
```

### Issue 7: Data Type Mismatches

**Symptoms**:
- "data type mismatch" errors
- Truncated data

**Solutions**:

1. **Use transformation function**:
```python
def fix_data_types(record):
    return {
        'id': int(record['id']),
        'amount': float(record['amount']),
        'created_at': str(record['created_at'])  # Convert datetime
    }

config = MigrationConfig(
    ...,
    transform_function=fix_data_types
)
```

2. **Pre-create target schema**:
```sql
-- Create target table with correct types
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMP
);
```

---

## Best Practices

### 1. Pre-Migration Checklist

```
□ Backup source database
□ Test migration on small subset
□ Verify target database has sufficient space
□ Check network bandwidth between servers
□ Ensure target database has no active connections
□ Create indexes AFTER migration (not before)
□ Disable triggers and constraints temporarily
□ Set appropriate timeouts
□ Plan for maintenance window
□ Prepare rollback plan
```

### 2. During Migration

```
□ Monitor progress logs
□ Check system resources (CPU, memory, disk I/O)
□ Watch for errors in logs
□ Verify checkpoint files are being created
□ Keep database connections minimal
□ Don't run other heavy operations
```

### 3. Post-Migration Checklist

```
□ Run validation
□ Rebuild indexes
□ Update statistics (ANALYZE)
□ Re-enable constraints and triggers
□ Test application with new database
□ Compare sample data manually
□ Archive migration logs
□ Document any issues encountered
□ Update connection strings
□ Celebrate! 🎉
```

### 4. Example Complete Migration Script

```python
#!/usr/bin/env python3
"""
Complete migration script with all best practices
"""

from database_migration import (
    MigrationConfig, MigrationOrchestrator, 
    MigrationStrategy, DatabaseFactory
)
import logging
import sys

def pre_migration_checks(config):
    """Run pre-migration checks"""
    print("Running pre-migration checks...")
    
    # Check source connection
    try:
        source_db = DatabaseFactory.create_database(
            config.source_db_type,
            config.source_params
        )
        source_db.connect()
        source_db.disconnect()
        print("✓ Source database connection successful")
    except Exception as e:
        print(f"✗ Source database connection failed: {e}")
        return False
    
    # Check target connection
    try:
        target_db = DatabaseFactory.create_database(
            config.target_db_type,
            config.target_params
        )
        target_db.connect()
        target_db.disconnect()
        print("✓ Target database connection successful")
    except Exception as e:
        print(f"✗ Target database connection failed: {e}")
        return False
    
    return True

def post_migration_tasks(config, stats):
    """Run post-migration tasks"""
    print("\nRunning post-migration tasks...")
    
    target_db = DatabaseFactory.create_database(
        config.target_db_type,
        config.target_params
    )
    target_db.connect()
    
    try:
        # Rebuild indexes
        print("Rebuilding indexes...")
        target_db.execute(f"REINDEX TABLE {config.target_table}")
        
        # Update statistics
        print("Updating statistics...")
        target_db.execute(f"ANALYZE {config.target_table}")
        
        print("✓ Post-migration tasks completed")
        
    except Exception as e:
        print(f"✗ Post-migration tasks failed: {e}")
    finally:
        target_db.disconnect()

def main():
    # Configuration
    config = MigrationConfig(
        source_db_type='postgresql',
        source_params={
            'host': 'source-db.company.com',
            'database': 'production',
            'user': 'postgres',
            'password': 'password'
        },
        target_db_type='postgresql',
        target_params={
            'host': 'target-db.company.com',
            'database': 'production_new',
            'user': 'postgres',
            'password': 'password'
        },
        source_table='users',
        target_table='users',
        strategy=MigrationStrategy.PARALLEL,
        num_workers=8,
        chunk_size=10000,
        enable_validation=True,
        enable_checkpoints=True,
        resume_from_checkpoint=True
    )
    
    # Pre-migration checks
    if not pre_migration_checks(config):
        print("Pre-migration checks failed. Aborting.")
        sys.exit(1)
    
    # Confirm
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    # Execute migration
    print("\nStarting migration...")
    orchestrator = MigrationOrchestrator(config)
    stats = orchestrator.execute()
    
    # Post-migration tasks
    post_migration_tasks(config, stats)
    
    # Summary
    print(f"\n{'='*60}")
    print("MIGRATION COMPLETED")
    print(f"{'='*60}")
    print(f"Total Records: {stats.total_records:,}")
    print(f"Migrated: {stats.migrated_records:,}")
    print(f"Failed: {stats.failed_records:,}")
    print(f"Duration: {stats.elapsed_seconds/60:.2f} minutes")
    print(f"Average Rate: {stats.average_rate:.0f} records/second")
    print(f"{'='*60}")
    
    if stats.migrated_records == stats.total_records:
        print("✓ Migration successful!")
        sys.exit(0)
    else:
        print("✗ Migration incomplete. Check logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## Summary

The Enterprise Database Migration Tool provides:

✅ **Flexibility**: Multiple strategies for different scenarios  
✅ **Reliability**: Checkpoints, retry logic, and validation  
✅ **Performance**: Parallel processing and optimized batching  
✅ **Visibility**: Real-time progress and detailed logging  
✅ **Recoverability**: Resume from interruption  
✅ **Extensibility**: Custom transformations and filters  

**When to Use Each Strategy**:

| Records | Strategy | Workers | Chunk Size | Typical Time |
|---------|----------|---------|------------|--------------|
| < 1M | CHUNKED | 1 | 10K | < 5 min |
| 1M - 10M | CHUNKED | 1 | 10-20K | 5-30 min |
| 10M - 50M | PARALLEL | 4-6 | 5-10K | 10-60 min |
| 50M - 100M | PARALLEL | 6-8 | 5-10K | 30-120 min |
| 100M+ | PARALLEL | 8-12 | 5K | 1+ hours |

**Remember**: Always test on a subset first! 🚀