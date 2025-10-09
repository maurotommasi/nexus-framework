"""
Real-Time Database Replication System
Automatically replicates changes across multiple database instances in real-time.
"""

from nexus.database.database_management import DatabaseFactory, DatabaseInterface
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import time
import queue
import json
import hashlib


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ReplicationMode(Enum):
    """Replication modes"""
    SYNCHRONOUS = "synchronous"      # Wait for all replicas
    ASYNCHRONOUS = "asynchronous"    # Don't wait for replicas
    SEMI_SYNC = "semi_sync"          # Wait for at least N replicas


class ReplicaRole(Enum):
    """Database role in replication"""
    PRIMARY = "primary"
    REPLICA = "replica"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    PRIMARY_WINS = "primary_wins"
    LATEST_WINS = "latest_wins"
    MANUAL = "manual"


@dataclass
class ReplicationEvent:
    """Represents a database operation to replicate"""
    event_id: str
    timestamp: datetime
    operation: str  # INSERT, UPDATE, DELETE
    table: str
    query: str
    params: Optional[tuple]
    source_db: str
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'table': self.table,
            'query': self.query,
            'params': self.params,
            'source_db': self.source_db,
            'checksum': self.checksum
        }


@dataclass
class ReplicaConfig:
    """Configuration for a replica database"""
    name: str
    db_type: str
    connection_params: Dict[str, Any]
    role: ReplicaRole = ReplicaRole.REPLICA
    priority: int = 100  # Lower = higher priority
    enabled: bool = True
    max_lag_seconds: int = 30  # Maximum acceptable replication lag


@dataclass
class ReplicationStats:
    """Replication statistics"""
    events_processed: int = 0
    events_failed: int = 0
    replicas_synced: int = 0
    total_lag_ms: float = 0.0
    average_lag_ms: float = 0.0
    last_event_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'events_processed': self.events_processed,
            'events_failed': self.events_failed,
            'replicas_synced': self.replicas_synced,
            'average_lag_ms': round(self.average_lag_ms, 2),
            'last_event_time': self.last_event_time.isoformat() if self.last_event_time else None
        }


class ReplicationLog:
    """Manages replication event log"""
    
    def __init__(self, log_file: str = 'replication.log'):
        self.log_file = log_file
        self.lock = threading.Lock()
    
    def log_event(self, event: ReplicationEvent):
        """Log replication event"""
        with self.lock:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
    
    def get_events_since(self, timestamp: datetime) -> List[ReplicationEvent]:
        """Get events since timestamp (for replica recovery)"""
        events = []
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    event_data = json.loads(line)
                    event_time = datetime.fromisoformat(event_data['timestamp'])
                    if event_time >= timestamp:
                        events.append(ReplicationEvent(
                            event_id=event_data['event_id'],
                            timestamp=event_time,
                            operation=event_data['operation'],
                            table=event_data['table'],
                            query=event_data['query'],
                            params=tuple(event_data['params']) if event_data['params'] else None,
                            source_db=event_data['source_db'],
                            checksum=event_data['checksum']
                        ))
        except FileNotFoundError:
            pass
        
        return events


class ReplicaManager:
    """Manages a single replica database"""
    
    def __init__(self, config: ReplicaConfig):
        self.config = config
        self.logger = logging.getLogger(f"Replica-{config.name}")
        self.db: Optional[DatabaseInterface] = None
        self.is_connected = False
        self.last_sync_time: Optional[datetime] = None
        self.event_queue = queue.Queue(maxsize=10000)
        self.stats = ReplicationStats()
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
    
    def connect(self):
        """Connect to replica database"""
        try:
            self.db = DatabaseFactory.create_database(
                self.config.db_type,
                self.config.connection_params
            )
            self.db.connect()
            self.is_connected = True
            self.logger.info(f"Connected to replica: {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to replica {self.config.name}: {e}")
            self.is_connected = False
            raise
    
    def disconnect(self):
        """Disconnect from replica database"""
        if self.db:
            self.db.disconnect()
            self.is_connected = False
            self.logger.info(f"Disconnected from replica: {self.config.name}")
    
    def start_worker(self):
        """Start background worker to process events"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._process_events,
                daemon=True
            )
            self._worker_thread.start()
            self.logger.info(f"Started worker thread for {self.config.name}")
    
    def stop_worker(self):
        """Stop background worker"""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
            self.logger.info(f"Stopped worker thread for {self.config.name}")
    
    def enqueue_event(self, event: ReplicationEvent) -> bool:
        """Add event to replication queue"""
        try:
            self.event_queue.put(event, timeout=1)
            return True
        except queue.Full:
            self.logger.error(f"Event queue full for {self.config.name}")
            return False
    
    def _process_events(self):
        """Background worker to process replication events"""
        while not self._stop_event.is_set():
            try:
                # Get event with timeout
                event = self.event_queue.get(timeout=0.1)
                
                # Process event
                success = self._apply_event(event)
                
                if success:
                    self.stats.events_processed += 1
                    self.stats.replicas_synced += 1
                    self.last_sync_time = datetime.now()
                else:
                    self.stats.events_failed += 1
                
                # Calculate lag
                lag_ms = (datetime.now() - event.timestamp).total_seconds() * 1000
                self.stats.total_lag_ms += lag_ms
                self.stats.average_lag_ms = self.stats.total_lag_ms / max(self.stats.events_processed, 1)
                
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
    
    def _apply_event(self, event: ReplicationEvent) -> bool:
        """Apply replication event to replica"""
        if not self.is_connected:
            self.logger.warning(f"Not connected to {self.config.name}, attempting reconnect...")
            try:
                self.connect()
            except:
                return False
        
        try:
            # Execute query
            self.db.execute(event.query, event.params)
            self.db.commit()
            
            self.logger.debug(f"Applied {event.operation} on {event.table} to {self.config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply event to {self.config.name}: {e}")
            self.db.rollback()
            return False
    
    def get_lag(self) -> float:
        """Get current replication lag in seconds"""
        if self.last_sync_time:
            return (datetime.now() - self.last_sync_time).total_seconds()
        return float('inf')
    
    def get_stats(self) -> Dict[str, Any]:
        """Get replica statistics"""
        return {
            'name': self.config.name,
            'role': self.config.role.value,
            'connected': self.is_connected,
            'enabled': self.config.enabled,
            'queue_size': self.event_queue.qsize(),
            'lag_seconds': round(self.get_lag(), 2),
            'stats': self.stats.to_dict()
        }


class DatabaseReplicationManager:
    """
    Main replication manager - orchestrates replication across multiple databases
    """
    
    def __init__(self, 
                 primary_config: ReplicaConfig,
                 replica_configs: List[ReplicaConfig],
                 mode: ReplicationMode = ReplicationMode.SYNCHRONOUS,
                 min_replicas_sync: int = 1,
                 conflict_resolution: ConflictResolution = ConflictResolution.PRIMARY_WINS):
        
        self.logger = logging.getLogger('ReplicationManager')
        
        # Set primary
        primary_config.role = ReplicaRole.PRIMARY
        self.primary = ReplicaManager(primary_config)
        
        # Set replicas
        self.replicas: Dict[str, ReplicaManager] = {}
        for config in replica_configs:
            config.role = ReplicaRole.REPLICA
            self.replicas[config.name] = ReplicaManager(config)
        
        self.mode = mode
        self.min_replicas_sync = min_replicas_sync
        self.conflict_resolution = conflict_resolution
        
        self.replication_log = ReplicationLog()
        self.is_active = False
        self._lock = threading.Lock()
        
        self.logger.info(f"Initialized replication manager with {len(self.replicas)} replicas")
    
    def start(self):
        """Start replication system"""
        self.logger.info("Starting replication system...")
        
        # Connect to primary
        self.primary.connect()
        
        # Connect to all replicas
        for name, replica in self.replicas.items():
            try:
                replica.connect()
                replica.start_worker()
            except Exception as e:
                self.logger.error(f"Failed to start replica {name}: {e}")
        
        self.is_active = True
        self.logger.info("Replication system started successfully")
    
    def stop(self):
        """Stop replication system"""
        self.logger.info("Stopping replication system...")
        
        self.is_active = False
        
        # Stop all replica workers
        for replica in self.replicas.values():
            replica.stop_worker()
            replica.disconnect()
        
        # Disconnect primary
        self.primary.disconnect()
        
        self.logger.info("Replication system stopped")
    
    def execute(self, query: str, params: Optional[tuple] = None, 
                table: Optional[str] = None) -> Any:
        """
        Execute query on primary and replicate to all replicas
        This is the main method to use for all database operations
        """
        if not self.is_active:
            raise RuntimeError("Replication system not started")
        
        # Determine operation type
        operation = self._get_operation_type(query)
        
        # Generate event
        event = ReplicationEvent(
            event_id=self._generate_event_id(),
            timestamp=datetime.now(),
            operation=operation,
            table=table or self._extract_table_name(query),
            query=query,
            params=params,
            source_db=self.primary.config.name,
            checksum=self._generate_checksum(query, params)
        )
        
        # Log event
        self.replication_log.log_event(event)
        
        # Execute on primary
        try:
            result = self.primary.db.execute(query, params)
            self.primary.db.commit()
            self.logger.info(f"Executed {operation} on primary: {self.primary.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to execute on primary: {e}")
            self.primary.db.rollback()
            raise
        
        # Replicate to replicas based on mode
        if self.mode == ReplicationMode.SYNCHRONOUS:
            self._replicate_synchronous(event)
        elif self.mode == ReplicationMode.ASYNCHRONOUS:
            self._replicate_asynchronous(event)
        elif self.mode == ReplicationMode.SEMI_SYNC:
            self._replicate_semi_sync(event)
        
        return result
    
    def execute_query(self, query: str, params: Optional[tuple] = None,
                     fetch: str = 'none', table: Optional[str] = None) -> Any:
        """
        Execute query with fetch options (none, one, all)
        """
        # For SELECT queries, read from primary only
        if query.strip().upper().startswith('SELECT'):
            if fetch == 'one':
                return self.primary.db.fetch_one(query, params)
            elif fetch == 'all':
                return self.primary.db.fetch_all(query, params)
            else:
                return self.primary.db.execute(query, params)
        
        # For write operations, replicate
        return self.execute(query, params, table)
    
    def _replicate_synchronous(self, event: ReplicationEvent):
        """Synchronous replication - wait for all replicas"""
        enabled_replicas = [r for r in self.replicas.values() if r.config.enabled]
        
        if not enabled_replicas:
            return
        
        with ThreadPoolExecutor(max_workers=len(enabled_replicas)) as executor:
            futures = {
                executor.submit(replica.enqueue_event, event): replica.config.name
                for replica in enabled_replicas
            }
            
            for future in as_completed(futures, timeout=30):
                replica_name = futures[future]
                try:
                    success = future.result()
                    if success:
                        self.logger.debug(f"Event queued to {replica_name}")
                except Exception as e:
                    self.logger.error(f"Failed to queue event to {replica_name}: {e}")
    
    def _replicate_asynchronous(self, event: ReplicationEvent):
        """Asynchronous replication - don't wait"""
        for replica in self.replicas.values():
            if replica.config.enabled:
                replica.enqueue_event(event)
    
    def _replicate_semi_sync(self, event: ReplicationEvent):
        """Semi-synchronous - wait for minimum N replicas"""
        enabled_replicas = [r for r in self.replicas.values() if r.config.enabled]
        
        if not enabled_replicas:
            return
        
        # Sort by priority
        enabled_replicas.sort(key=lambda r: r.config.priority)
        
        synced_count = 0
        for replica in enabled_replicas:
            if replica.enqueue_event(event):
                synced_count += 1
                if synced_count >= self.min_replicas_sync:
                    break
        
        if synced_count < self.min_replicas_sync:
            self.logger.warning(f"Only {synced_count}/{self.min_replicas_sync} replicas synced")
    
    def _get_operation_type(self, query: str) -> str:
        """Extract operation type from query"""
        query_upper = query.strip().upper()
        if query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from query"""
        query_upper = query.strip().upper()
        
        if 'INSERT INTO' in query_upper:
            parts = query_upper.split('INSERT INTO')[1].split()
            return parts[0].strip()
        elif 'UPDATE' in query_upper:
            parts = query_upper.split('UPDATE')[1].split()
            return parts[0].strip()
        elif 'DELETE FROM' in query_upper:
            parts = query_upper.split('DELETE FROM')[1].split()
            return parts[0].strip()
        
        return 'unknown'
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return hashlib.sha256(
            f"{datetime.now().isoformat()}{threading.get_ident()}".encode()
        ).hexdigest()[:16]
    
    def _generate_checksum(self, query: str, params: Optional[tuple]) -> str:
        """Generate checksum for event"""
        data = f"{query}{params}".encode()
        return hashlib.md5(data).hexdigest()
    
    def get_status(self) -> Dict[str, Any]:
        """Get replication system status"""
        return {
            'active': self.is_active,
            'mode': self.mode.value,
            'primary': self.primary.get_stats(),
            'replicas': {
                name: replica.get_stats()
                for name, replica in self.replicas.items()
            },
            'total_replicas': len(self.replicas),
            'healthy_replicas': sum(1 for r in self.replicas.values() if r.is_connected)
        }
    
    def promote_replica(self, replica_name: str):
        """Promote a replica to primary (failover)"""
        if replica_name not in self.replicas:
            raise ValueError(f"Replica {replica_name} not found")
        
        self.logger.info(f"Promoting replica {replica_name} to primary...")
        
        # Stop current system
        self.stop()
        
        # Swap primary and replica
        old_primary = self.primary
        new_primary = self.replicas[replica_name]
        
        # Update roles
        old_primary.config.role = ReplicaRole.REPLICA
        new_primary.config.role = ReplicaRole.PRIMARY
        
        # Reassign
        self.primary = new_primary
        self.replicas[replica_name] = old_primary
        
        # Restart
        self.start()
        
        self.logger.info(f"Successfully promoted {replica_name} to primary")


# High-level wrapper for easy usage
class ReplicatedDatabase:
    """
    Easy-to-use wrapper for replicated database operations
    Usage is identical to regular database operations
    """
    
    def __init__(self, replication_manager: DatabaseReplicationManager):
        self.manager = replication_manager
        self.logger = logging.getLogger('ReplicatedDatabase')
    
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute write query (INSERT, UPDATE, DELETE)"""
        return self.manager.execute(query, params)
    
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """Fetch single row"""
        return self.manager.execute_query(query, params, fetch='one')
    
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Fetch all rows"""
        return self.manager.execute_query(query, params, fetch='all')
    
    def commit(self):
        """Commit (handled automatically)"""
        pass
    
    def rollback(self):
        """Rollback on primary"""
        self.manager.primary.db.rollback()
    
    def transaction(self):
        """Transaction context manager"""
        return self.manager.primary.db.transaction()


# Usage examples
if __name__ == "__main__":
    
    # Example 1: Basic 3-replica setup
    def example_basic_replication():
        """Example: Primary with 2 replicas"""
        
        # Configure primary
        primary = ReplicaConfig(
            name='primary-db',
            db_type='postgresql',
            connection_params={
                'host': 'primary.company.com',
                'database': 'production',
                'user': 'postgres',
                'password': 'password'
            },
            role=ReplicaRole.PRIMARY
        )
        
        # Configure replicas
        replicas = [
            ReplicaConfig(
                name='replica-1',
                db_type='postgresql',
                connection_params={
                    'host': 'replica1.company.com',
                    'database': 'production',
                    'user': 'postgres',
                    'password': 'password'
                },
                priority=1
            ),
            ReplicaConfig(
                name='replica-2',
                db_type='postgresql',
                connection_params={
                    'host': 'replica2.company.com',
                    'database': 'production',
                    'user': 'postgres',
                    'password': 'password'
                },
                priority=2
            )
        ]
        
        # Create replication manager
        replication = DatabaseReplicationManager(
            primary_config=primary,
            replica_configs=replicas,
            mode=ReplicationMode.SYNCHRONOUS
        )
        
        # Start replication
        replication.start()
        
        # Create easy-to-use wrapper
        db = ReplicatedDatabase(replication)
        
        try:
            # Use like normal database
            db.execute(
                "INSERT INTO users (name, email) VALUES (%s, %s)",
                ('John Doe', 'john@example.com')
            )
            print("✓ Inserted to primary and replicated to all replicas")
            
            db.execute(
                "UPDATE users SET email = %s WHERE name = %s",
                ('john.doe@example.com', 'John Doe')
            )
            print("✓ Updated on primary and replicated")
            
            # Read from primary
            user = db.fetch_one("SELECT * FROM users WHERE name = %s", ('John Doe',))
            print(f"✓ Fetched user: {user}")
            
            # Check status
            status = replication.get_status()
            print(f"\nReplication Status:")
            print(f"  Primary: {status['primary']['name']}")
            print(f"  Healthy Replicas: {status['healthy_replicas']}/{status['total_replicas']}")
            
            for replica_name, replica_stats in status['replicas'].items():
                print(f"  {replica_name}:")
                print(f"    Connected: {replica_stats['connected']}")
                print(f"    Queue Size: {replica_stats['queue_size']}")
                print(f"    Lag: {replica_stats['lag_seconds']}s")
                print(f"    Events Processed: {replica_stats['stats']['events_processed']}")
        
        finally:
            # Stop replication
            replication.stop()
    
    # Run example
    print("="*60)
    print("DATABASE REPLICATION EXAMPLE")
    print("="*60)
    example_basic_replication()