"""
PDF Queue Manager - Advanced Queue System for PDF Generation
Supports multiple backends: In-Memory, Redis, RabbitMQ, AWS SQS
"""

import json
import time
import uuid
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from queue import Queue, PriorityQueue, Empty

from pdf_template_manager import PDFTemplateManager
from pdf_pattern import PDFService, PDFServiceConfig


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class JobStatus(Enum):
    """PDF job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass
class PDFJob:
    """PDF generation job."""
    job_id: str
    template: str
    data: Dict[str, Any]
    output_filename: str
    css_file: Optional[str] = None
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['priority'] = self.priority.name
        data['status'] = self.status.name
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFJob':
        """Create from dictionary."""
        data['priority'] = JobPriority[data['priority']]
        data['status'] = JobStatus[data['status']]
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['started_at']:
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


# ============================================================================
# QUEUE BACKEND INTERFACE
# ============================================================================

class QueueBackend(ABC):
    """Abstract queue backend interface."""
    
    @abstractmethod
    def enqueue(self, job: PDFJob) -> bool:
        """Add job to queue."""
        pass
    
    @abstractmethod
    def dequeue(self, timeout: Optional[float] = None) -> Optional[PDFJob]:
        """Get next job from queue."""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[PDFJob]:
        """Get job by ID."""
        pass
    
    @abstractmethod
    def update_job(self, job: PDFJob) -> bool:
        """Update job status."""
        pass
    
    @abstractmethod
    def get_pending_count(self) -> int:
        """Get number of pending jobs."""
        pass
    
    @abstractmethod
    def get_all_jobs(self, status: Optional[JobStatus] = None) -> List[PDFJob]:
        """Get all jobs, optionally filtered by status."""
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """Clear all jobs. Returns number of jobs cleared."""
        pass


# ============================================================================
# IN-MEMORY BACKEND
# ============================================================================

class InMemoryBackend(QueueBackend):
    """
    In-memory queue backend using Python Queue.
    Best for: Development, testing, single-process apps.
    """
    
    def __init__(self):
        """Initialize in-memory backend."""
        self.queue = PriorityQueue()
        self.jobs: Dict[str, PDFJob] = {}
        self.lock = threading.Lock()
    
    def enqueue(self, job: PDFJob) -> bool:
        """Add job to queue."""
        with self.lock:
            self.jobs[job.job_id] = job
            # Priority queue: (priority_value, timestamp, job_id)
            self.queue.put((
                job.priority.value,
                time.time(),
                job.job_id
            ))
        return True
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[PDFJob]:
        """Get next job from queue."""
        try:
            _, _, job_id = self.queue.get(timeout=timeout)
            with self.lock:
                job = self.jobs.get(job_id)
                if job and job.status == JobStatus.PENDING:
                    return job
        except Empty:
            return None
        return None
    
    def get_job(self, job_id: str) -> Optional[PDFJob]:
        """Get job by ID."""
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job(self, job: PDFJob) -> bool:
        """Update job."""
        with self.lock:
            if job.job_id in self.jobs:
                self.jobs[job.job_id] = job
                return True
        return False
    
    def get_pending_count(self) -> int:
        """Get pending jobs count."""
        with self.lock:
            return sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING)
    
    def get_all_jobs(self, status: Optional[JobStatus] = None) -> List[PDFJob]:
        """Get all jobs."""
        with self.lock:
            if status:
                return [j for j in self.jobs.values() if j.status == status]
            return list(self.jobs.values())
    
    def clear(self) -> int:
        """Clear all jobs."""
        with self.lock:
            count = len(self.jobs)
            self.jobs.clear()
            # Clear queue
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Empty:
                    break
            return count


# ============================================================================
# REDIS BACKEND
# ============================================================================

class RedisBackend(QueueBackend):
    """
    Redis queue backend.
    Best for: Production, distributed systems, multi-process apps.
    
    Requires: pip install redis
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        queue_name: str = 'pdf_queue'
    ):
        """Initialize Redis backend."""
        try:
            import redis
        except ImportError:
            raise ImportError("redis package required: pip install redis")
        
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self.queue_name = queue_name
        self.jobs_key = f"{queue_name}:jobs"
    
    def enqueue(self, job: PDFJob) -> bool:
        """Add job to queue."""
        # Store job data
        self.redis.hset(self.jobs_key, job.job_id, json.dumps(job.to_dict()))
        
        # Add to sorted set (priority queue)
        score = job.priority.value * 1000000 + time.time()
        self.redis.zadd(self.queue_name, {job.job_id: score})
        
        return True
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[PDFJob]:
        """Get next job from queue."""
        # Get highest priority job (lowest score)
        result = self.redis.zpopmin(self.queue_name, count=1)
        
        if not result:
            if timeout:
                time.sleep(timeout)
            return None
        
        job_id = result[0][0]
        job_data = self.redis.hget(self.jobs_key, job_id)
        
        if job_data:
            job = PDFJob.from_dict(json.loads(job_data))
            if job.status == JobStatus.PENDING:
                return job
        
        return None
    
    def get_job(self, job_id: str) -> Optional[PDFJob]:
        """Get job by ID."""
        job_data = self.redis.hget(self.jobs_key, job_id)
        if job_data:
            return PDFJob.from_dict(json.loads(job_data))
        return None
    
    def update_job(self, job: PDFJob) -> bool:
        """Update job."""
        self.redis.hset(self.jobs_key, job.job_id, json.dumps(job.to_dict()))
        return True
    
    def get_pending_count(self) -> int:
        """Get pending jobs count."""
        return self.redis.zcard(self.queue_name)
    
    def get_all_jobs(self, status: Optional[JobStatus] = None) -> List[PDFJob]:
        """Get all jobs."""
        all_job_data = self.redis.hgetall(self.jobs_key)
        jobs = [PDFJob.from_dict(json.loads(data)) for data in all_job_data.values()]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return jobs
    
    def clear(self) -> int:
        """Clear all jobs."""
        count = self.redis.hlen(self.jobs_key)
        self.redis.delete(self.queue_name, self.jobs_key)
        return count


# ============================================================================
# AWS SQS BACKEND
# ============================================================================

class SQSBackend(QueueBackend):
    """
    AWS SQS queue backend.
    Best for: AWS infrastructure, serverless, scalable systems.
    
    Requires: pip install boto3
    """
    
    def __init__(
        self,
        queue_url: str,
        region_name: str = 'us-east-1',
        dynamodb_table: Optional[str] = None
    ):
        """Initialize SQS backend."""
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 package required: pip install boto3")
        
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.queue_url = queue_url
        
        # Use DynamoDB for job metadata storage
        if dynamodb_table:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.table = self.dynamodb.Table(dynamodb_table)
        else:
            self.dynamodb = None
            self.table = None
    
    def enqueue(self, job: PDFJob) -> bool:
        """Add job to queue."""
        message_body = json.dumps(job.to_dict())
        
        # Send to SQS
        response = self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=message_body,
            MessageAttributes={
                'Priority': {
                    'StringValue': job.priority.name,
                    'DataType': 'String'
                }
            }
        )
        
        # Store in DynamoDB if available
        if self.table:
            self.table.put_item(Item=job.to_dict())
        
        return 'MessageId' in response
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[PDFJob]:
        """Get next job from queue."""
        wait_time = int(timeout) if timeout else 0
        
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=wait_time,
            MessageAttributeNames=['All']
        )
        
        messages = response.get('Messages', [])
        if not messages:
            return None
        
        message = messages[0]
        job = PDFJob.from_dict(json.loads(message['Body']))
        
        # Store receipt handle for deletion
        job.metadata['receipt_handle'] = message['ReceiptHandle']
        
        return job
    
    def get_job(self, job_id: str) -> Optional[PDFJob]:
        """Get job by ID from DynamoDB."""
        if not self.table:
            return None
        
        response = self.table.get_item(Key={'job_id': job_id})
        item = response.get('Item')
        
        if item:
            return PDFJob.from_dict(item)
        return None
    
    def update_job(self, job: PDFJob) -> bool:
        """Update job in DynamoDB."""
        if not self.table:
            return False
        
        self.table.put_item(Item=job.to_dict())
        
        # Delete from SQS if completed
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            receipt_handle = job.metadata.get('receipt_handle')
            if receipt_handle:
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
        
        return True
    
    def get_pending_count(self) -> int:
        """Get approximate pending jobs count."""
        response = self.sqs.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        return int(response['Attributes']['ApproximateNumberOfMessages'])
    
    def get_all_jobs(self, status: Optional[JobStatus] = None) -> List[PDFJob]:
        """Get all jobs from DynamoDB."""
        if not self.table:
            return []
        
        response = self.table.scan()
        jobs = [PDFJob.from_dict(item) for item in response['Items']]
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return jobs
    
    def clear(self) -> int:
        """Purge SQS queue."""
        self.sqs.purge_queue(QueueUrl=self.queue_url)
        return 0  # Can't get exact count before purge


# ============================================================================
# QUEUE MANAGER
# ============================================================================

class PDFQueueManager:
    """
    PDF Queue Manager - Manages PDF generation queue with workers.
    
    Features:
    - Multiple backend support (Memory, Redis, SQS)
    - Priority-based job processing
    - Worker pool management
    - Automatic retries
    - Job status tracking
    - Callbacks/hooks
    
    Usage:
        # In-memory (development)
        manager = PDFQueueManager(
            backend=InMemoryBackend(),
            pdf_service=PDFService()
        )
        
        # Redis (production)
        manager = PDFQueueManager(
            backend=RedisBackend(host='localhost'),
            pdf_service=PDFService(),
            num_workers=4
        )
        
        # Start processing
        manager.start()
        
        # Submit jobs
        job_id = manager.submit_job(
            template='invoice.html',
            data={'id': 1},
            output_filename='invoice.pdf',
            priority=JobPriority.HIGH
        )
        
        # Check status
        status = manager.get_job_status(job_id)
        
        # Stop
        manager.stop()
    """
    
    def __init__(
        self,
        backend: QueueBackend,
        pdf_service: PDFService,
        num_workers: int = 2,
        poll_interval: float = 1.0
    ):
        """
        Initialize queue manager.
        
        Args:
            backend: Queue backend implementation
            pdf_service: PDF service for generation
            num_workers: Number of worker threads
            poll_interval: Queue polling interval in seconds
        """
        self.backend = backend
        self.pdf_service = pdf_service
        self.num_workers = num_workers
        self.poll_interval = poll_interval
        
        self.workers: List[threading.Thread] = []
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Callbacks
        self.on_job_start: Optional[Callable[[PDFJob], None]] = None
        self.on_job_complete: Optional[Callable[[PDFJob], None]] = None
        self.on_job_failed: Optional[Callable[[PDFJob, Exception], None]] = None
    
    def submit_job(
        self,
        template: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> str:
        """
        Submit PDF generation job to queue.
        
        Args:
            template: Template filename
            data: Template data
            output_filename: Output PDF filename
            css_file: Optional CSS file
            priority: Job priority
            metadata: Optional job metadata
            max_retries: Maximum retry attempts
            
        Returns:
            Job ID
        """
        job = PDFJob(
            job_id=str(uuid.uuid4()),
            template=template,
            data=data,
            output_filename=output_filename,
            css_file=css_file,
            priority=priority,
            metadata=metadata or {},
            max_retries=max_retries
        )
        
        self.backend.enqueue(job)
        self.logger.info(f"Job submitted: {job.job_id} (priority: {priority.name})")
        
        return job.job_id
    
    def submit_batch(
        self,
        jobs: List[Dict[str, Any]],
        priority: JobPriority = JobPriority.NORMAL
    ) -> List[str]:
        """
        Submit multiple jobs at once.
        
        Args:
            jobs: List of job specifications
            priority: Default priority for all jobs
            
        Returns:
            List of job IDs
        """
        job_ids = []
        
        for job_spec in jobs:
            job_id = self.submit_job(
                template=job_spec['template'],
                data=job_spec['data'],
                output_filename=job_spec['output'],
                css_file=job_spec.get('css_file'),
                priority=job_spec.get('priority', priority),
                metadata=job_spec.get('metadata'),
                max_retries=job_spec.get('max_retries', 3)
            )
            job_ids.append(job_id)
        
        self.logger.info(f"Batch submitted: {len(job_ids)} jobs")
        return job_ids
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status."""
        job = self.backend.get_job(job_id)
        return job.status if job else None
    
    def get_job(self, job_id: str) -> Optional[PDFJob]:
        """Get complete job information."""
        return self.backend.get_job(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        job = self.backend.get_job(job_id)
        
        if job and job.status == JobStatus.PENDING:
            job.status = JobStatus.CANCELLED
            self.backend.update_job(job)
            self.logger.info(f"Job cancelled: {job_id}")
            return True
        
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        all_jobs = self.backend.get_all_jobs()
        
        stats = {
            'total_jobs': len(all_jobs),
            'pending': sum(1 for j in all_jobs if j.status == JobStatus.PENDING),
            'processing': sum(1 for j in all_jobs if j.status == JobStatus.PROCESSING),
            'completed': sum(1 for j in all_jobs if j.status == JobStatus.COMPLETED),
            'failed': sum(1 for j in all_jobs if j.status == JobStatus.FAILED),
            'cancelled': sum(1 for j in all_jobs if j.status == JobStatus.CANCELLED),
            'workers': self.num_workers,
            'running': self.running
        }
        
        return stats
    
    def start(self):
        """Start worker threads."""
        if self.running:
            self.logger.warning("Queue manager already running")
            return
        
        self.running = True
        self.workers = []
        
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Started {self.num_workers} workers")
    
    def stop(self, timeout: float = 30.0):
        """
        Stop worker threads.
        
        Args:
            timeout: Maximum time to wait for workers to finish
        """
        if not self.running:
            return
        
        self.logger.info("Stopping workers...")
        self.running = False
        
        # Wait for workers to finish
        start_time = time.time()
        for worker in self.workers:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0:
                worker.join(timeout=remaining_time)
        
        self.workers = []
        self.logger.info("All workers stopped")
    
    def _worker_loop(self, worker_id: int):
        """Worker thread main loop."""
        self.logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get next job from queue
                job = self.backend.dequeue(timeout=self.poll_interval)
                
                if job:
                    self._process_job(job, worker_id)
                
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
                time.sleep(1)
        
        self.logger.info(f"Worker {worker_id} stopped")
    
    def _process_job(self, job: PDFJob, worker_id: int):
        """Process a single job."""
        self.logger.info(f"Worker {worker_id} processing job: {job.job_id}")
        
        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        self.backend.update_job(job)
        
        # Callback: job started
        if self.on_job_start:
            try:
                self.on_job_start(job)
            except Exception as e:
                self.logger.error(f"on_job_start callback error: {e}")
        
        try:
            # Generate PDF
            output_path = self.pdf_service.generate(
                template=job.template,
                data=job.data,
                output_filename=job.output_filename,
                css_file=job.css_file
            )
            
            # Update job as completed
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result_path = str(output_path)
            self.backend.update_job(job)
            
            duration = (job.completed_at - job.started_at).total_seconds()
            self.logger.info(
                f"Worker {worker_id} completed job: {job.job_id} ({duration:.2f}s)"
            )
            
            # Callback: job completed
            if self.on_job_complete:
                try:
                    self.on_job_complete(job)
                except Exception as e:
                    self.logger.error(f"on_job_complete callback error: {e}")
        
        except Exception as e:
            # Job failed
            job.error = str(e)
            job.retry_count += 1
            
            # Retry if under max retries
            if job.retry_count < job.max_retries:
                job.status = JobStatus.PENDING
                self.backend.update_job(job)
                self.backend.enqueue(job)  # Re-queue
                self.logger.warning(
                    f"Job {job.job_id} failed, retry {job.retry_count}/{job.max_retries}"
                )
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                self.backend.update_job(job)
                self.logger.error(f"Job {job.job_id} failed permanently: {e}")
                
                # Callback: job failed
                if self.on_job_failed:
                    try:
                        self.on_job_failed(job, e)
                    except Exception as callback_error:
                        self.logger.error(f"on_job_failed callback error: {callback_error}")
    
    def wait_for_job(
        self,
        job_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 0.5
    ) -> PDFJob:
        """
        Wait for job to complete.
        
        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait (None = wait forever)
            poll_interval: How often to check status
            
        Returns:
            Completed PDFJob
            
        Raises:
            TimeoutError: If timeout exceeded
            RuntimeError: If job failed
        """
        start_time = time.time()
        
        while True:
            job = self.backend.get_job(job_id)
            
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            if job.status == JobStatus.COMPLETED:
                return job
            
            if job.status == JobStatus.FAILED:
                raise RuntimeError(f"Job failed: {job.error}")
            
            if job.status == JobStatus.CANCELLED:
                raise RuntimeError("Job was cancelled")
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")
            
            time.sleep(poll_interval)
    
    def clear_queue(self) -> int:
        """Clear all jobs from queue. Returns number cleared."""
        count = self.backend.clear()
        self.logger.info(f"Cleared {count} jobs from queue")
        return count


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example 1: In-Memory Queue (Development)
    print("=== Example 1: In-Memory Queue ===")
    
    backend = InMemoryBackend()
    pdf_service = PDFService(PDFServiceConfig())
    manager = PDFQueueManager(backend, pdf_service, num_workers=2)
    
    # Start workers
    manager.start()
    
    # Submit jobs
    job_id1 = manager.submit_job(
        template='invoice.html',
        data={'invoice_number': 'INV-001'},
        output_filename='invoice_001.pdf',
        priority=JobPriority.HIGH
    )
    
    job_id2 = manager.submit_job(
        template='receipt.html',
        data={'receipt_id': 'REC-001'},
        output_filename='receipt_001.pdf',
        priority=JobPriority.NORMAL
    )
    
    # Wait for completion
    print(f"Waiting for job {job_id1}...")
    try:
        completed_job = manager.wait_for_job(job_id1, timeout=30)
        print(f"Job completed: {completed_job.result_path}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get stats
    stats = manager.get_queue_stats()
    print(f"Queue stats: {stats}")
    
    # Stop
    manager.stop()
    
    # Example 2: Redis Queue (Production)
    print("\n=== Example 2: Redis Queue ===")
    
    try:
        redis_backend = RedisBackend(host='localhost')
        redis_manager = PDFQueueManager(redis_backend, pdf_service, num_workers=4)
        
        redis_manager.start()
        
        # Submit batch
        jobs = [
            {'template': 'invoice.html', 'data': {'id': i}, 'output': f'invoice_{i}.pdf'}
            for i in range(10)
        ]
        job_ids = redis_manager.submit_batch(jobs, priority=JobPriority.NORMAL)
        print(f"Submitted {len(job_ids)} jobs")
        
        # Monitor queue
        time.sleep(2)
        stats = redis_manager.get_queue_stats()
        print(f"Queue stats: {stats}")
        
        redis_manager.stop()
        
    except Exception as e:
        print(f"Redis example failed (Redis not available?): {e}")
    
    print("\n✅ Queue manager examples completed!")