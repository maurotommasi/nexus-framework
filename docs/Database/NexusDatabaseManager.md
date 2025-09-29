# Database.py - Complete Function Reference Guide

## Table of Contents

1. [Core Classes](#core-classes)
   - [DatabaseInterface](#databaseinterface)
   - [DatabaseManager](#databasemanager)
   - [DatabaseFactory](#databasefactory)
   - [ConnectionPool](#connectionpool)
   - [DatabaseMetrics](#databasemetrics)
2. [Database-Specific Classes](#database-specific-classes)
3. [Utility Functions](#utility-functions)
4. [Enums and Constants](#enums-and-constants)

---

## Core Classes

### DatabaseInterface

The abstract base class that all database implementations inherit from.

#### `__init__(connection_params: Dict[str, Any])`

**Description**: Initialize a database instance with connection parameters.

**Parameters**:
- `connection_params` (Dict): Dictionary containing connection details

**Example**:
```python
from database import PostgreSQLDatabase

params = {
    'host': 'localhost',
    'port': 5432,
    'database': 'mydb',
    'user': 'postgres',
    'password': 'password',
    'timeout': 10
}

db = PostgreSQLDatabase(params)
```

---

#### `connect()`

**Description**: Establish connection to the database.

**Parameters**: None

**Returns**: None

**Raises**: Connection errors specific to database type

**Example**:
```python
from database import PostgreSQLDatabase

params = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'postgres',
    'password': 'password'
}

db = PostgreSQLDatabase(params)
db.connect()
print("Connected successfully!")
```

---

#### `disconnect()`

**Description**: Close the database connection and free resources.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Do some work...

db.disconnect()
print("Connection closed")
```

---

#### `execute(query: str, params: Optional[tuple] = None) -> Any`

**Description**: Execute a query (INSERT, UPDATE, DELETE) and return affected row count.

**Parameters**:
- `query` (str): SQL query string
- `params` (Optional[tuple]): Query parameters for parameterized queries

**Returns**: Number of affected rows (int)

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Simple INSERT
rows_affected = db.execute(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    ('John Doe', 'john@example.com')
)
print(f"Inserted {rows_affected} row(s)")

# UPDATE with parameters
rows_affected = db.execute(
    "UPDATE users SET email = %s WHERE id = %s",
    ('newemail@example.com', 1)
)
print(f"Updated {rows_affected} row(s)")

# DELETE
rows_affected = db.execute(
    "DELETE FROM users WHERE id = %s",
    (1,)
)
print(f"Deleted {rows_affected} row(s)")

db.commit()
db.disconnect()
```

---

#### `execute_many(query: str, params_list: List[tuple])`

**Description**: Execute the same query multiple times with different parameters (batch operation).

**Parameters**:
- `query` (str): SQL query string
- `params_list` (List[tuple]): List of parameter tuples

**Returns**: None

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Batch insert multiple users
users_data = [
    ('Alice', 'alice@example.com', 28),
    ('Bob', 'bob@example.com', 32),
    ('Charlie', 'charlie@example.com', 25),
    ('Diana', 'diana@example.com', 30)
]

db.execute_many(
    "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)",
    users_data
)

db.commit()
print(f"Inserted {len(users_data)} users")

db.disconnect()
```

---

#### `fetch_one(query: str, params: Optional[tuple] = None) -> Optional[Dict]`

**Description**: Execute a SELECT query and return a single row as a dictionary.

**Parameters**:
- `query` (str): SQL SELECT query
- `params` (Optional[tuple]): Query parameters

**Returns**: Dictionary representing the row, or None if no results

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Fetch single user by ID
user = db.fetch_one(
    "SELECT id, name, email, age FROM users WHERE id = %s",
    (1,)
)

if user:
    print(f"User: {user['name']}, Email: {user['email']}, Age: {user['age']}")
else:
    print("User not found")

# Fetch with aggregate function
count_result = db.fetch_one(
    "SELECT COUNT(*) as total FROM users WHERE age > %s",
    (25,)
)
print(f"Total users over 25: {count_result['total']}")

db.disconnect()
```

---

#### `fetch_all(query: str, params: Optional[tuple] = None) -> List[Dict]`

**Description**: Execute a SELECT query and return all rows as a list of dictionaries.

**Parameters**:
- `query` (str): SQL SELECT query
- `params` (Optional[tuple]): Query parameters

**Returns**: List of dictionaries, each representing a row

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Fetch all active users
users = db.fetch_all(
    "SELECT id, name, email FROM users WHERE status = %s ORDER BY name",
    ('active',)
)

print(f"Found {len(users)} active users:")
for user in users:
    print(f"- {user['name']} ({user['email']})")

# Fetch with JOIN
orders = db.fetch_all("""
    SELECT u.name, o.order_id, o.total_amount
    FROM users u
    JOIN orders o ON u.id = o.user_id
    WHERE o.created_at > %s
    ORDER BY o.created_at DESC
""", ('2024-01-01',))

for order in orders:
    print(f"{order['name']} - Order #{order['order_id']}: ${order['total_amount']}")

db.disconnect()
```

---

#### `commit()`

**Description**: Commit the current transaction to the database.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

try:
    db.execute("INSERT INTO users (name) VALUES (%s)", ('Alice',))
    db.execute("INSERT INTO users (name) VALUES (%s)", ('Bob',))
    
    # Commit both inserts
    db.commit()
    print("Transaction committed successfully")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.disconnect()
```

---

#### `rollback()`

**Description**: Rollback the current transaction, undoing all changes since the last commit.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

try:
    db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    
    # Simulate an error
    raise Exception("Something went wrong!")
    
    db.commit()
    
except Exception as e:
    print(f"Error occurred: {e}")
    db.rollback()  # Undo both updates
    print("Transaction rolled back")
    
finally:
    db.disconnect()
```

---

#### `transaction(isolation_level: Optional[IsolationLevel] = None)`

**Description**: Context manager for handling transactions with automatic commit/rollback.

**Parameters**:
- `isolation_level` (Optional[IsolationLevel]): Transaction isolation level

**Returns**: Context manager yielding the database instance

**Example**:
```python
from database import PostgreSQLDatabase, IsolationLevel

db = PostgreSQLDatabase(params)
db.connect()

# Basic transaction
try:
    with db.transaction():
        db.execute("INSERT INTO users (name) VALUES (%s)", ('Alice',))
        db.execute("INSERT INTO logs (message) VALUES (%s)", ('User created',))
        # Automatically commits if no exception
    
    print("Transaction successful")
    
except Exception as e:
    print(f"Transaction failed: {e}")
    # Automatically rolled back

# Transaction with isolation level
try:
    with db.transaction(isolation_level=IsolationLevel.SERIALIZABLE):
        balance = db.fetch_one("SELECT balance FROM accounts WHERE id = %s", (1,))
        
        if balance['balance'] >= 100:
            db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = %s", (1,))
            db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = %s", (2,))
        else:
            raise Exception("Insufficient funds")
    
    print("Transfer completed")
    
except Exception as e:
    print(f"Transfer failed: {e}")

db.disconnect()
```

---

#### `is_connected() -> bool`

**Description**: Check if the database connection is alive and active.

**Parameters**: None

**Returns**: True if connected, False otherwise

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

if db.is_connected():
    print("Database is connected")
    
    # Do some work
    users = db.fetch_all("SELECT * FROM users")
    
else:
    print("Database is not connected")

db.disconnect()

if not db.is_connected():
    print("Database connection closed")
```

---

#### `reconnect() -> bool`

**Description**: Attempt to reconnect to the database if connection is lost.

**Parameters**: None

**Returns**: True if reconnection successful, False otherwise

**Example**:
```python
from database import PostgreSQLDatabase
import time

db = PostgreSQLDatabase(params)
db.connect()

try:
    users = db.fetch_all("SELECT * FROM users")
    
except Exception as e:
    print(f"Connection error: {e}")
    
    # Attempt to reconnect
    if db.reconnect():
        print("Reconnection successful!")
        users = db.fetch_all("SELECT * FROM users")
    else:
        print("Reconnection failed")

db.disconnect()
```

---

#### `set_isolation_level(level: IsolationLevel)`

**Description**: Set the transaction isolation level for the connection.

**Parameters**:
- `level` (IsolationLevel): Desired isolation level

**Returns**: None

**Example**:
```python
from database import PostgreSQLDatabase, IsolationLevel

db = PostgreSQLDatabase(params)
db.connect()

# Set isolation level
db.set_isolation_level(IsolationLevel.SERIALIZABLE)

# Now all transactions use SERIALIZABLE isolation
with db.transaction():
    db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
    db.execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")

db.disconnect()
```

---

#### `execute_with_retry(query: str, params: Optional[tuple] = None, max_retries: int = 3, retry_delay: float = 1.0) -> Any`

**Description**: Execute a query with automatic retry on failure (useful for transient network errors).

**Parameters**:
- `query` (str): SQL query
- `params` (Optional[tuple]): Query parameters
- `max_retries` (int): Maximum number of retry attempts (default: 3)
- `retry_delay` (float): Delay between retries in seconds (default: 1.0)

**Returns**: Result of execute operation

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

try:
    # Will retry up to 5 times with 2-second delays
    rows_affected = db.execute_with_retry(
        "UPDATE products SET stock = stock - %s WHERE id = %s",
        (5, 101),
        max_retries=5,
        retry_delay=2.0
    )
    
    db.commit()
    print(f"Successfully updated {rows_affected} row(s) after potential retries")
    
except Exception as e:
    print(f"Failed after all retry attempts: {e}")
    db.rollback()

db.disconnect()
```

---

#### `batch_execute(queries: List[tuple], batch_size: int = 1000) -> int`

**Description**: Execute multiple queries in batches with automatic transaction management.

**Parameters**:
- `queries` (List[tuple]): List of (query, params) tuples
- `batch_size` (int): Number of queries per batch (default: 1000)

**Returns**: Total number of affected rows

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Prepare many operations
queries = []
for i in range(5000):
    queries.append((
        "INSERT INTO events (event_type, user_id, timestamp) VALUES (%s, %s, NOW())",
        ('page_view', f'user_{i % 100}')
    ))

# Execute in batches of 500
total_affected = db.batch_execute(queries, batch_size=500)
print(f"Executed {len(queries)} queries, affected {total_affected} rows")

db.disconnect()
```

---

#### `get_metrics() -> Dict[str, Any]`

**Description**: Get performance metrics for the database connection.

**Parameters**: None

**Returns**: Dictionary containing performance statistics

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Execute some queries
db.fetch_all("SELECT * FROM users")
db.execute("INSERT INTO logs (message) VALUES (%s)", ('test',))
db.commit()

# Get metrics
metrics = db.get_metrics()

print(f"Total Queries: {metrics['total_queries']}")
print(f"Average Query Time: {metrics['average_query_time']}s")
print(f"Slow Queries: {metrics['slow_queries_count']}")
print(f"Errors: {metrics['errors_count']}")
print(f"Active Connections: {metrics['active_connections']}")

db.disconnect()
```

---

#### `reset_metrics()`

**Description**: Reset all performance metrics to zero.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import PostgreSQLDatabase

db = PostgreSQLDatabase(params)
db.connect()

# Execute some queries
db.fetch_all("SELECT * FROM users")

metrics_before = db.get_metrics()
print(f"Queries before reset: {metrics_before['total_queries']}")

# Reset metrics
db.reset_metrics()

metrics_after = db.get_metrics()
print(f"Queries after reset: {metrics_after['total_queries']}")  # 0

db.disconnect()
```

---

### DatabaseManager

High-level manager class that handles connection pooling and provides simplified database access.

#### `__init__(db_type: str, connection_params: Dict[str, Any], use_pool: bool = True, pool_config: Optional[Dict[str, int]] = None)`

**Description**: Initialize a database manager with optional connection pooling.

**Parameters**:
- `db_type` (str): Type of database ('postgresql', 'mysql', 'mongodb', etc.)
- `connection_params` (Dict): Connection parameters
- `use_pool` (bool): Enable connection pooling (default: True)
- `pool_config` (Optional[Dict]): Pool configuration

**Example**:
```python
from database import DatabaseManager

params = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'postgres',
    'password': 'password'
}

pool_config = {
    'min_size': 5,      # Minimum connections in pool
    'max_size': 20,     # Maximum connections in pool
    'max_idle_time': 300  # Connection idle timeout
}

# With connection pooling (recommended for production)
manager = DatabaseManager('postgresql', params, use_pool=True, pool_config=pool_config)

# Without connection pooling
manager_simple = DatabaseManager('postgresql', params, use_pool=False)
```

---

#### `get_connection()`

**Description**: Context manager that provides a database connection from the pool.

**Parameters**: None

**Returns**: Context manager yielding database connection

**Example**:
```python
from database import DatabaseManager

manager = DatabaseManager('postgresql', params, use_pool=True)

# Get connection from pool
with manager.get_connection() as db:
    users = db.fetch_all("SELECT * FROM users")
    print(f"Found {len(users)} users")
    
    db.execute("INSERT INTO logs (message) VALUES (%s)", ('Query executed',))
    db.commit()
# Connection automatically returned to pool

# Multiple connections
with manager.get_connection() as db1:
    with manager.get_connection() as db2:
        # Two separate connections from pool
        users = db1.fetch_all("SELECT * FROM users")
        orders = db2.fetch_all("SELECT * FROM orders")

manager.close()
```

---

#### `execute_query(query: str, params: Optional[tuple] = None, fetch: str = 'none') -> Any`

**Description**: Execute a query with automatic connection management.

**Parameters**:
- `query` (str): SQL query
- `params` (Optional[tuple]): Query parameters
- `fetch` (str): Fetch mode: 'none', 'one', or 'all'

**Returns**: Depends on fetch mode - None, single row dict, or list of dicts

**Example**:
```python
from database import DatabaseManager

manager = DatabaseManager('postgresql', params, use_pool=True)

# Execute without fetching (INSERT, UPDATE, DELETE)
rows_affected = manager.execute_query(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    ('Alice', 'alice@example.com'),
    fetch='none'
)
print(f"Inserted {rows_affected} row(s)")

# Fetch one row
user = manager.execute_query(
    "SELECT * FROM users WHERE id = %s",
    (1,),
    fetch='one'
)
print(f"User: {user['name']}")

# Fetch all rows
all_users = manager.execute_query(
    "SELECT * FROM users WHERE age > %s",
    (18,),
    fetch='all'
)
print(f"Found {len(all_users)} users")

manager.close()
```

---

#### `execute_transaction(operations: List[tuple], isolation_level: Optional[IsolationLevel] = None) -> bool`

**Description**: Execute multiple operations in a single transaction.

**Parameters**:
- `operations` (List[tuple]): List of (query, params) tuples
- `isolation_level` (Optional[IsolationLevel]): Transaction isolation level

**Returns**: True if successful, False if failed

**Example**:
```python
from database import DatabaseManager, IsolationLevel

manager = DatabaseManager('postgresql', params, use_pool=True)

# Simple transaction
operations = [
    ("INSERT INTO users (name, email) VALUES (%s, %s)", ('Alice', 'alice@example.com')),
    ("INSERT INTO users (name, email) VALUES (%s, %s)", ('Bob', 'bob@example.com')),
    ("UPDATE settings SET value = %s WHERE key = %s", ('2', 'user_count'))
]

success = manager.execute_transaction(operations)
if success:
    print("Transaction completed successfully")
else:
    print("Transaction failed")

# Money transfer with SERIALIZABLE isolation
transfer_operations = [
    ("UPDATE accounts SET balance = balance - %s WHERE id = %s", (100, 1)),
    ("UPDATE accounts SET balance = balance + %s WHERE id = %s", (100, 2)),
    ("INSERT INTO transactions (from_id, to_id, amount) VALUES (%s, %s, %s)", (1, 2, 100))
]

success = manager.execute_transaction(
    transfer_operations,
    isolation_level=IsolationLevel.SERIALIZABLE
)

if success:
    print("Transfer completed")
else:
    print("Transfer failed - rolled back")

manager.close()
```

---

#### `health_check() -> Dict[str, Any]`

**Description**: Check database health and get status information.

**Parameters**: None

**Returns**: Dictionary with health status and metrics

**Example**:
```python
from database import DatabaseManager
import json

manager = DatabaseManager('postgresql', params, use_pool=True)

# Execute some queries
manager.execute_query("SELECT * FROM users", fetch='all')

# Check health
health = manager.health_check()

print(f"Status: {health['status']}")
print(f"Connected: {health['connected']}")
print(f"Database Type: {health['database_type']}")
print(f"Total Queries: {health['metrics']['total_queries']}")
print(f"Avg Query Time: {health['metrics']['average_query_time']}s")

if 'pool_stats' in health:
    print(f"\nPool Statistics:")
    print(f"Active Connections: {health['pool_stats']['active_connections']}")
    print(f"Available Connections: {health['pool_stats']['available_connections']}")
    print(f"Max Connections: {health['pool_stats']['max_connections']}")

# Export health status to JSON
with open('health_status.json', 'w') as f:
    json.dump(health, f, indent=2)

manager.close()
```

---

#### `get_metrics() -> Dict[str, Any]`

**Description**: Get aggregated metrics from the database manager.

**Parameters**: None

**Returns**: Dictionary containing metrics

**Example**:
```python
from database import DatabaseManager

manager = DatabaseManager('postgresql', params, use_pool=True)

# Execute queries
for i in range(100):
    manager.execute_query("SELECT * FROM users LIMIT 10", fetch='all')

# Get metrics
metrics = manager.get_metrics()

print(f"Database Type: {metrics['database_type']}")
print(f"Pool Stats: {metrics['pool_stats']}")

manager.close()
```

---

#### `close()`

**Description**: Close all database connections and clean up resources.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import DatabaseManager

manager = DatabaseManager('postgresql', params, use_pool=True)

try:
    # Use the manager
    users = manager.execute_query("SELECT * FROM users", fetch='all')
    print(f"Found {len(users)} users")
    
finally:
    # Always close when done
    manager.close()
    print("All connections closed")
```

---

### DatabaseFactory

Factory class for creating database instances with singleton support.

#### `create_database(db_type: str, connection_params: Dict[str, Any]) -> DatabaseInterface`

**Description**: Create a database instance of the specified type.

**Parameters**:
- `db_type` (str): Type of database
- `connection_params` (Dict): Connection parameters

**Returns**: DatabaseInterface instance

**Example**:
```python
from database import DatabaseFactory

# Create PostgreSQL instance
pg_params = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'postgres',
    'password': 'password'
}

pg_db = DatabaseFactory.create_database('postgresql', pg_params)
pg_db.connect()
users = pg_db.fetch_all("SELECT * FROM users")
pg_db.disconnect()

# Create MySQL instance
mysql_params = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'root',
    'password': 'password'
}

mysql_db = DatabaseFactory.create_database('mysql', mysql_params)
mysql_db.connect()
products = mysql_db.fetch_all("SELECT * FROM products")
mysql_db.disconnect()

# Create MongoDB instance
mongo_params = {
    'uri': 'mongodb://localhost:27017',
    'database': 'mydb'
}

mongo_db = DatabaseFactory.create_database('mongodb', mongo_params)
mongo_db.connect()
documents = mongo_db.fetch_all('users', {})
mongo_db.disconnect()
```

---

#### `create_manager(db_type: str, connection_params: Dict[str, Any], use_pool: bool = True, pool_config: Optional[Dict[str, int]] = None, singleton: bool = False) -> DatabaseManager`

**Description**: Create a database manager with optional singleton pattern.

**Parameters**:
- `db_type` (str): Type of database
- `connection_params` (Dict): Connection parameters
- `use_pool` (bool): Enable connection pooling
- `pool_config` (Optional[Dict]): Pool configuration
- `singleton` (bool): Use singleton pattern (one instance per database)

**Returns**: DatabaseManager instance

**Example**:
```python
from database import DatabaseFactory

params = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'postgres',
    'password': 'password'
}

pool_config = {
    'min_size': 5,
    'max_size': 20
}

# Create regular manager (new instance each time)
manager1 = DatabaseFactory.create_manager(
    'postgresql',
    params,
    use_pool=True,
    pool_config=pool_config,
    singleton=False
)

manager2 = DatabaseFactory.create_manager(
    'postgresql',
    params,
    use_pool=True,
    pool_config=pool_config,
    singleton=False
)

print(f"Same instance? {manager1 is manager2}")  # False

# Create singleton manager (same instance returned)
singleton1 = DatabaseFactory.create_manager(
    'postgresql',
    params,
    use_pool=True,
    singleton=True
)

singleton2 = DatabaseFactory.create_manager(
    'postgresql',
    params,
    use_pool=True,
    singleton=True
)

print(f"Same singleton? {singleton1 is singleton2}")  # True

# Clean up
manager1.close()
manager2.close()
DatabaseFactory.close_all()  # Closes all singletons
```

---

#### `close_all()`

**Description**: Close all singleton manager instances.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import DatabaseFactory

params = {'host': 'localhost', 'database': 'db1', 'user': 'user', 'password': 'pass'}

# Create multiple singleton managers
manager1 = DatabaseFactory.create_manager('postgresql', params, singleton=True)
manager2 = DatabaseFactory.create_manager('mysql', params, singleton=True)
manager3 = DatabaseFactory.create_manager('mongodb', params, singleton=True)

# Use managers...
manager1.execute_query("SELECT * FROM users", fetch='all')
manager2.execute_query("SELECT * FROM products", fetch='all')

# Close all singleton instances at once
DatabaseFactory.close_all()
print("All singleton managers closed")
```

---

### ConnectionPool

Thread-safe connection pool for managing database connections.

#### `__init__(db_class, connection_params: Dict[str, Any], min_size: int = 2, max_size: int = 10, max_idle_time: int = 300, logger: Optional[logging.Logger] = None)`

**Description**: Initialize a connection pool.

**Parameters**:
- `db_class`: Database class to instantiate
- `connection_params` (Dict): Connection parameters
- `min_size` (int): Minimum number of connections (default: 2)
- `max_size` (int): Maximum number of connections (default: 10)
- `max_idle_time` (int): Idle timeout in seconds (default: 300)
- `logger` (Optional[Logger]): Custom logger instance

**Example**:
```python
from database import ConnectionPool, PostgreSQLDatabase
import logging

# Setup logger
logger = logging.getLogger('MyApp')
logger.setLevel(logging.INFO)

params = {
    'host': 'localhost',
    'database': 'mydb',
    'user': 'postgres',
    'password': 'password'
}

# Create connection pool
pool = ConnectionPool(
    PostgreSQLDatabase,
    params,
    min_size=3,
    max_size=15,
    max_idle_time=600,
    logger=logger
)

# Use connections from pool
conn1 = pool.get_connection()
users = conn1.fetch_all("SELECT * FROM users")
pool.release_connection(conn1)

conn2 = pool.get_connection()
products = conn2.fetch_all("SELECT * FROM products")
pool.release_connection(conn2)

# Get pool statistics
stats = pool.get_stats()
print(f"Active: {stats['active_connections']}")
print(f"Available: {stats['available_connections']}")

# Clean up
pool.close_all()
```

---

#### `get_connection(timeout: int = 30)`

**Description**: Get a connection from the pool.

**Parameters**:
- `timeout` (int): Maximum wait time in seconds (default: 30)

**Returns**: Database connection instance

**Example**:
```python
from database import ConnectionPool, PostgreSQLDatabase

pool = ConnectionPool(PostgreSQLDatabase, params, min_size=2, max_size=10)

try:
    # Get connection with 10-second timeout
    conn = pool.get_connection(timeout=10)
    
    # Use connection
    users = conn.fetch_all("SELECT * FROM users")
    print(f"Found {len(users)} users")
    
finally:
    # Always return connection to pool
    pool.release_connection(conn)

pool.close_all()
```

---

#### `release_connection(conn)`

**Description**: Return a connection to the pool for reuse.

**Parameters**:
- `conn`: Database connection to return

**Returns**: None

**Example**:
```python
from database import ConnectionPool, PostgreSQLDatabase

pool = ConnectionPool(PostgreSQLDatabase, params)

# Get connection
conn = pool.get_connection()

try:
    # Use connection
    result = conn.fetch_one("SELECT COUNT(*) as total FROM users")
    print(f"Total users: {result['total']}")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    # Return to pool (even if error occurred)
    pool.release_connection(conn)

pool.close_all()
```

---

#### `close_all()`

**Description**: Close all connections in the pool.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import ConnectionPool, PostgreSQLDatabase

pool = ConnectionPool(PostgreSQLDatabase, params, min_size=5, max_size=20)

# Use the pool...
conn = pool.get_connection()
conn.fetch_all("SELECT * FROM users")
pool.release_connection(conn)

# Close all connections when shutting down
pool.close_all()
print("Pool closed, all connections terminated")
```

---

#### `get_stats() -> Dict[str, int]`

**Description**: Get connection pool statistics.

**Parameters**: None

**Returns**: Dictionary with pool statistics

**Example**:
```python
from database import ConnectionPool, PostgreSQLDatabase
import time

pool = ConnectionPool(PostgreSQLDatabase, params, min_size=3, max_size=10)

# Get some connections
conn1 = pool.get_connection()
conn2 = pool.get_connection()

# Check stats
stats = pool.get_stats()
print(f"Active Connections: {stats['active_connections']}")
print(f"Available Connections: {stats['available_connections']}")
print(f"Max Connections: {stats['max_connections']}")

# Return connections
pool.release_connection(conn1)
pool.release_connection(conn2)

# Check stats again
stats = pool.get_stats()
print(f"\nAfter returning connections:")
print(f"Available Connections: {stats['available_connections']}")

pool.close_all()
```

---

### DatabaseMetrics

Tracks and stores database performance metrics.

#### `__init__()`

**Description**: Initialize metrics tracking.

**Parameters**: None

**Example**:
```python
from database import DatabaseMetrics

metrics = DatabaseMetrics()
print(f"Initial query count: {metrics.query_count}")
```

---

#### `record_query(query: str, execution_time: float, success: bool = True)`

**Description**: Record a query execution with timing information.

**Parameters**:
- `query` (str): The executed query
- `execution_time` (float): Execution time in seconds
- `success` (bool): Whether query succeeded (default: True)

**Returns**: None

**Example**:
```python
from database import DatabaseMetrics
import time

metrics = DatabaseMetrics()

# Simulate query execution
query = "SELECT * FROM users WHERE age > 25"
start_time = time.time()
# ... execute query ...
execution_time = time.time() - start_time

# Record the query
metrics.record_query(query, execution_time, success=True)

# Record a slow query
metrics.record_query("SELECT * FROM large_table", 2.5, success=True)

# Record a failed query
metrics.record_query("INVALID SQL", 0.1, success=False)

# Get statistics
stats = metrics.get_stats()
print(f"Total queries: {stats['total_queries']}")
print(f"Slow queries: {stats['slow_queries_count']}")
print(f"Errors: {stats['errors_count']}")
```

---

#### `get_stats() -> Dict[str, Any]`

**Description**: Get current performance statistics.

**Parameters**: None

**Returns**: Dictionary with statistics

**Example**:
```python
from database import DatabaseMetrics

metrics = DatabaseMetrics()

# Record some queries
metrics.record_query("SELECT * FROM users", 0.05, True)
metrics.record_query("SELECT * FROM orders", 0.03, True)
metrics.record_query("SELECT * FROM products", 1.2, True)  # Slow query
metrics.record_query("INVALID", 0.01, False)  # Error

# Get comprehensive stats
stats = metrics.get_stats()

print(f"Total Queries: {stats['total_queries']}")
print(f"Average Query Time: {stats['average_query_time']}s")
print(f"Slow Queries Count: {stats['slow_queries_count']}")
print(f"Errors Count: {stats['errors_count']}")
print(f"Active Connections: {stats['active_connections']}")
print(f"Total Connections: {stats['total_connections']}")
```

---

#### `reset()`

**Description**: Reset all metrics to zero.

**Parameters**: None

**Returns**: None

**Example**:
```python
from database import DatabaseMetrics

metrics = DatabaseMetrics()

# Record queries
metrics.record_query("SELECT * FROM users", 0.05, True)
metrics.record_query("SELECT * FROM orders", 0.03, True)

stats_before = metrics.get_stats()
print(f"Queries before reset: {stats_before['total_queries']}")

# Reset all metrics
metrics.reset()

stats_after = metrics.get_stats()
print(f"Queries after reset: {stats_after['total_queries']}")  # 0
print(f"Slow queries after reset: {stats_after['slow_queries_count']}")  # 0
```

---

## Utility Functions

### `bulk_insert(db: DatabaseInterface, table: str, records: List[Dict], batch_size: int = 1000) -> int`

**Description**: Efficiently insert large numbers of records in batches.

**Parameters**:
- `db` (DatabaseInterface): Database instance
- `table` (str): Target table name
- `records` (List[Dict]): List of record dictionaries
- `batch_size` (int): Records per batch (default: 1000)

**Returns**: Total number of records inserted

**Example**:
```python
from database import DatabaseFactory, bulk_insert

db = DatabaseFactory.create_database('postgresql', params)
db.connect()

# Prepare 10,000 user records
users = []
for i in range(10000):
    users.append({
        'name': f'User {i}',
        'email': f'user{i}@example.com',
        'age': 20 + (i % 50),
        'status': 'active'
    })

# Bulk insert with automatic batching
total_inserted = bulk_insert(db, 'users', users, batch_size=500)
print(f"Successfully inserted {total_inserted} users")

db.disconnect()
```

**Advanced Example with Timing**:
```python
from database import DatabaseFactory, bulk_insert
import time

db = DatabaseFactory.create_database('postgresql', params)
db.connect()

# Generate large dataset
records = []
for i in range(50000):
    records.append({
        'event_type': 'page_view',
        'user_id': f'user_{i % 1000}',
        'timestamp': '2024-03-15 12:00:00',
        'page': f'/page/{i % 100}'
    })

# Measure performance
start_time = time.time()

total = bulk_insert(db, 'events', records, batch_size=1000)

elapsed = time.time() - start_time
rate = total / elapsed

print(f"Inserted {total} records in {elapsed:.2f} seconds")
print(f"Rate: {rate:.0f} records/second")

db.disconnect()
```

---

### `export_to_json(db: DatabaseInterface, query: str, params: Optional[tuple] = None, output_file: str = 'export.json') -> int`

**Description**: Export query results to a JSON file.

**Parameters**:
- `db` (DatabaseInterface): Database instance
- `query` (str): SQL query to export
- `params` (Optional[tuple]): Query parameters
- `output_file` (str): Output file path (default: 'export.json')

**Returns**: Number of records exported

**Example**:
```python
from database import DatabaseFactory, export_to_json

db = DatabaseFactory.create_database('postgresql', params)
db.connect()

# Export all active users
count = export_to_json(
    db,
    "SELECT id, name, email, age FROM users WHERE status = %s",
    ('active',),
    output_file='active_users.json'
)

print(f"Exported {count} users to active_users.json")

# Export with complex query
count = export_to_json(
    db,
    """
    SELECT 
        u.name,
        COUNT(o.id) as order_count,
        SUM(o.total) as total_spent
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id, u.name
    HAVING COUNT(o.id) > 5
    """,
    output_file='top_customers.json'
)

print(f"Exported {count} top customers")

db.disconnect()
```

**Reading Exported Data**:
```python
import json

# Read the exported JSON file
with open('active_users.json', 'r') as f:
    users = json.load(f)

print(f"Loaded {len(users)} users from JSON")
for user in users[:5]:
    print(f"- {user['name']} ({user['email']})")
```

---

### `migrate_data(source_db: DatabaseInterface, target_db: DatabaseInterface, source_query: str, target_table: str, batch_size: int = 1000, transform_fn: Optional[Callable] = None) -> int`

**Description**: Migrate data from source database to target database with optional transformation.

**Parameters**:
- `source_db` (DatabaseInterface): Source database
- `target_db` (DatabaseInterface): Target database
- `source_query` (str): Query to fetch data from source
- `target_table` (str): Target table name
- `batch_size` (int): Batch size for insertion (default: 1000)
- `transform_fn` (Optional[Callable]): Transformation function

**Returns**: Number of records migrated

**Example 1: Simple Migration**:
```python
from database import DatabaseFactory, migrate_data

# Connect to source (PostgreSQL)
source_params = {
    'host': 'old-server.com',
    'database': 'old_db',
    'user': 'postgres',
    'password': 'password'
}
source_db = DatabaseFactory.create_database('postgresql', source_params)
source_db.connect()

# Connect to target (MySQL)
target_params = {
    'host': 'new-server.com',
    'database': 'new_db',
    'user': 'root',
    'password': 'password'
}
target_db = DatabaseFactory.create_database('mysql', target_params)
target_db.connect()

# Migrate all users
count = migrate_data(
    source_db,
    target_db,
    "SELECT id, name, email, created_at FROM users",
    "users",
    batch_size=500
)

print(f"Migrated {count} users from PostgreSQL to MySQL")

source_db.disconnect()
target_db.disconnect()
```

**Example 2: Migration with Transformation**:
```python
from database import DatabaseFactory, migrate_data
from datetime import datetime

source_db = DatabaseFactory.create_database('postgresql', source_params)
source_db.connect()

target_db = DatabaseFactory.create_database('mysql', target_params)
target_db.connect()

# Define transformation function
def transform_user(record):
    """Transform user data during migration"""
    return {
        'user_id': record['id'],
        'full_name': record['name'].upper(),  # Convert to uppercase
        'email_address': record['email'].lower(),  # Convert to lowercase
        'registration_date': record['created_at'],
        'migrated_at': datetime.now().isoformat()
    }

# Migrate with transformation
count = migrate_data(
    source_db,
    target_db,
    "SELECT id, name, email, created_at FROM users WHERE active = true",
    "migrated_users",
    batch_size=1000,
    transform_fn=transform_user
)

print(f"Migrated and transformed {count} users")

source_db.disconnect()
target_db.disconnect()
```

**Example 3: Cross-Database Migration (PostgreSQL to MongoDB)**:
```python
from database import DatabaseFactory, migrate_data

# Source: PostgreSQL
pg_db = DatabaseFactory.create_database('postgresql', pg_params)
pg_db.connect()

# Target: MongoDB
mongo_db = DatabaseFactory.create_database('mongodb', mongo_params)
mongo_db.connect()

# Transform relational data to document structure
def transform_to_document(record):
    """Transform relational record to MongoDB document"""
    return {
        'user_id': record['id'],
        'profile': {
            'name': record['name'],
            'email': record['email'],
            'age': record['age']
        },
        'metadata': {
            'created_at': record['created_at'],
            'migrated_at': datetime.now()
        }
    }

# Note: For MongoDB, we use insert_many instead
records = pg_db.fetch_all("SELECT * FROM users")
transformed = [transform_to_document(r) for r in records]
inserted_ids = mongo_db.insert_many('users', transformed)

print(f"Migrated {len(inserted_ids)} records to MongoDB")

pg_db.disconnect()
mongo_db.disconnect()
```

---

## Enums and Constants

### IsolationLevel

**Description**: Enum defining transaction isolation levels.

**Values**:
- `READ_UNCOMMITTED`: Lowest isolation, allows dirty reads
- `READ_COMMITTED`: Prevents dirty reads
- `REPEATABLE_READ`: Prevents dirty and non-repeatable reads
- `SERIALIZABLE`: Highest isolation, full transaction isolation

**Example**:
```python
from database import DatabaseFactory, IsolationLevel

db = DatabaseFactory.create_database('postgresql', params)
db.connect()

# READ UNCOMMITTED - fastest but least safe
with db.transaction(isolation_level=IsolationLevel.READ_UNCOMMITTED):
    db.execute("UPDATE stats SET views = views + 1")

# READ COMMITTED - prevents dirty reads (default for most databases)
with db.transaction(isolation_level=IsolationLevel.READ_COMMITTED):
    balance = db.fetch_one("SELECT balance FROM accounts WHERE id = 1")
    if balance['balance'] > 100:
        db.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")

# REPEATABLE READ - prevents dirty and non-repeatable reads
with db.transaction(isolation_level=IsolationLevel.REPEATABLE_READ):
    total = db.fetch_one("SELECT SUM(amount) as total FROM orders")
    db.execute("INSERT INTO reports (total_orders) VALUES (%s)", (total['total'],))

# SERIALIZABLE - full isolation (slowest but safest)
with db.transaction(isolation_level=IsolationLevel.SERIALIZABLE):
    # Critical financial transaction
    db.execute("UPDATE accounts SET balance = balance - 1000 WHERE id = 1")
    db.execute("UPDATE accounts SET balance = balance + 1000 WHERE id = 2")
    db.execute("INSERT INTO audit_log (action) VALUES ('transfer')")

db.disconnect()
```

---

## Complete Usage Examples

### Example 1: Web Application with Connection Pooling

```python
from database import DatabaseFactory, IsolationLevel
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize database manager with connection pool
db_manager = DatabaseFactory.create_manager(
    'postgresql',
    {
        'host': 'localhost',
        'database': 'webapp',
        'user': 'postgres',
        'password': 'password'
    },
    use_pool=True,
    pool_config={'min_size': 5, 'max_size': 20},
    singleton=True  # Reuse same manager
)

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = db_manager.execute_query(
        "SELECT id, name, email FROM users WHERE active = true",
        fetch='all'
    )
    return jsonify(users)

@app.route('/users', methods=['POST'])
def create_user():
    """Create new user"""
    data = request.json
    
    user_id = db_manager.execute_query(
        "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
        (data['name'], data['email']),
        fetch='one'
    )
    
    return jsonify({'id': user_id['id'], 'message': 'User created'}), 201

@app.route('/transfer', methods=['POST'])
def transfer_money():
    """Transfer money between accounts"""
    data = request.json
    
    operations = [
        ("UPDATE accounts SET balance = balance - %s WHERE id = %s AND balance >= %s",
         (data['amount'], data['from_account'], data['amount'])),
        ("UPDATE accounts SET balance = balance + %s WHERE id = %s",
         (data['amount'], data['to_account'])),
        ("INSERT INTO transactions (from_id, to_id, amount) VALUES (%s, %s, %s)",
         (data['from_account'], data['to_account'], data['amount']))
    ]
    
    success = db_manager.execute_transaction(
        operations,
        isolation_level=IsolationLevel.SERIALIZABLE
    )
    
    if success:
        return jsonify({'message': 'Transfer successful'}), 200
    else:
        return jsonify({'error': 'Transfer failed'}), 400

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health = db_manager.health_check()
    return jsonify(health)

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        DatabaseFactory.close_all()
```

---

### Example 2: Data Analytics Pipeline

```python
from database import DatabaseFactory, bulk_insert, export_to_json
import pandas as pd
from datetime import datetime, timedelta

# Setup connections
source_db = DatabaseFactory.create_database('postgresql', source_params)
source_db.connect()

analytics_db = DatabaseFactory.create_database('postgresql', analytics_params)
analytics_db.connect()

# Extract data from source
print("Extracting data...")
raw_data = source_db.fetch_all("""
    SELECT 
        user_id,
        event_type,
        event_timestamp,
        page_url,
        session_id
    FROM events
    WHERE event_timestamp >= %s
""", (datetime.now() - timedelta(days=7),))

print(f"Extracted {len(raw_data)} events")

# Transform data
print("Transforming data...")
transformed = []
for event in raw_data:
    transformed.append({
        'user_id': event['user_id'],
        'event_type': event['event_type'],
        'date': event['event_timestamp'].date(),
        'hour': event['event_timestamp'].hour,
        'page_category': event['page_url'].split('/')[1] if '/' in event['page_url'] else 'home',
        'session_id': event['session_id']
    })

# Load to analytics database
print("Loading to analytics database...")
inserted = bulk_insert(analytics_db, 'analytics_events', transformed, batch_size=1000)
print(f"Loaded {inserted} transformed events")

# Generate reports
print("Generating reports...")
report_data = analytics_db.fetch_all("""
    SELECT 
        date,
        event_type,
        COUNT(*) as event_count,
        COUNT(DISTINCT user_id) as unique_users
    FROM analytics_events
    GROUP BY date, event_type
    ORDER BY date DESC, event_count DESC
""")

# Export report
export_to_json(
    analytics_db,
    """
    SELECT 
        date,
        event_type,
        COUNT(*) as event_count,
        COUNT(DISTINCT user_id) as unique_users
    FROM analytics_events
    GROUP BY date, event_type
    ORDER BY date DESC
    """,
    output_file=f'analytics_report_{datetime.now().strftime("%Y%m%d")}.json'
)

print("Analytics pipeline completed successfully")

# Cleanup
source_db.disconnect()
analytics_db.disconnect()
```

---

### Example 3: Microservice with Health Monitoring

```python
from database import DatabaseFactory
import time
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('OrderService')

class OrderService:
    def __init__(self):
        self.db_manager = DatabaseFactory.create_manager(
            'postgresql',
            {
                'host': 'localhost',
                'database': 'orders',
                'user': 'postgres',
                'password': 'password'
            },
            use_pool=True,
            pool_config={'min_size': 10, 'max_size': 50},
            singleton=True
        )
        
        # Start health monitoring
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_health, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_health(self):
        """Continuously monitor database health"""
        while self.monitoring:
            health = self.db_manager.health_check()
            
            if health['status'] != 'healthy':
                logger.error(f"Database unhealthy: {health}")
            else:
                metrics = health['metrics']
                if metrics['slow_queries_count'] > 10:
                    logger.warning(f"High number of slow queries: {metrics['slow_queries_count']}")
                
                pool_stats = health.get('pool_stats', {})
                if pool_stats.get('available_connections', 0) < 3:
                    logger.warning("Connection pool running low")
            
            time.sleep(30)  # Check every 30 seconds
    
    def create_order(self, customer_id: int, items: list) -> dict:
        """Create a new order"""
        try:
            operations = [
                ("""
                    INSERT INTO orders (customer_id, status, created_at)
                    VALUES (%s, 'pending', NOW())
                    RETURNING id
                """, (customer_id,))
            ]
            
            # This is simplified - in production, get the order_id first
            order_id = self.db_manager.execute_query(
                "INSERT INTO orders (customer_id, status) VALUES (%s, 'pending') RETURNING id",
                (customer_id,),
                fetch='one'
            )['id']
            
            # Add items
            item_operations = []
            for item in items:
                item_operations.append((
                    "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order_id, item['product_id'], item['quantity'], item['price'])
                ))
            
            success = self.db_manager.execute_transaction(item_operations)
            
            if success:
                logger.info(f"Order {order_id} created successfully")
                return {'order_id': order_id, 'status': 'created'}
            else:
                logger.error(f"Failed to create order items")
                return {'error': 'Failed to create order'}
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {'error': str(e)}
    
    def get_order(self, order_id: int) -> dict:
        """Get order details"""
        order = self.db_manager.execute_query(
            """
            SELECT o.id, o.customer_id, o.status, o.created_at,
                   json_agg(json_build_object(
                       'product_id', oi.product_id,
                       'quantity', oi.quantity,
                       'price', oi.price
                   )) as items
            FROM orders o
            LEFT JOIN order_items oi ON o.id = oi.order_id
            WHERE o.id = %s
            GROUP BY o.id
            """,
            (order_id,),
            fetch='one'
        )
        
        return order if order else {'error': 'Order not found'}
    
    def get_metrics(self) -> dict:
        """Get service metrics"""
        return self.db_manager.get_metrics()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down OrderService")
        self.monitoring = False
        self.db_manager.close()

# Usage
if __name__ == '__main__':
    service = OrderService()
    
    try:
        # Create order
        result = service.create_order(
            customer_id=1001,
            items=[
                {'product_id': 1, 'quantity': 2, 'price': 29.99},
                {'product_id': 2, 'quantity': 1, 'price': 59.99}
            ]
        )
        print(f"Order created: {result}")
        
        # Get order
        if 'order_id' in result:
            order = service.get_order(result['order_id'])
            print(f"Order details: {order}")
        
        # Get metrics
        metrics = service.get_metrics()
        print(f"Service metrics: {metrics}")
        
        # Keep running for monitoring
        time.sleep(60)
        
    finally:
        service.shutdown()
```

---

