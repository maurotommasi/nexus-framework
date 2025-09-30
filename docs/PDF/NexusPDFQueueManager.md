
**PDF Queue Manager Guide v1.0** | For support: Check troubleshooting or enable DEBUG logging# PDF Queue Manager - Engineer's Guide

> **Complete guide for implementing scalable, production-ready PDF generation with queue management**

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Queue Backends](#queue-backends)
5. [Job Management](#job-management)
6. [Worker Configuration](#worker-configuration)
7. [Monitoring & Statistics](#monitoring--statistics)
8. [Production Patterns](#production-patterns)
9. [Error Handling & Retries](#error-handling--retries)
10. [Performance Tuning](#performance-tuning)
11. [Deployment Examples](#deployment-examples)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### What is PDF Queue Manager?

A production-ready queue system for managing PDF generation at scale with:

- ✅ **Multiple backend support**: In-Memory, Redis, AWS SQS
- ✅ **Priority-based processing**: 4 priority levels (Urgent, High, Normal, Low)
- ✅ **Worker pool management**: Configurable thread-based workers
- ✅ **Automatic retries**: Configurable retry logic with exponential backoff
- ✅ **Job tracking**: Complete status tracking and lifecycle management
- ✅ **Callbacks/hooks**: Event-driven architecture for notifications
- ✅ **Distributed processing**: Support for multi-server deployments

### When to Use Queue Manager vs Direct Generation

| Feature | Queue Manager | Direct Service |
|---------|--------------|----------------|
| **Volume** | 100+ PDFs | < 100 PDFs |
| **Async Processing** | ✅ Built-in | ⚠️ Manual |
| **Priority Handling** | ✅ Yes | ❌ No |
| **Retry Logic** | ✅ Automatic | ⚠️ Manual |
| **Distributed** | ✅ Yes | ❌ No |
| **Monitoring** | ✅ Built-in | ⚠️ Manual |
| **Real-time** | ⚠️ Slight delay | ✅ Immediate |
| **Setup Complexity** | ⚠️ Higher | ✅ Simple |

**Use Queue Manager when:**
- Processing 100+ PDFs daily
- Need background processing
- Require priority handling
- Running distributed systems
- Need automatic retries
- Want built-in monitoring

**Use Direct Service when:**
- < 100 PDFs daily
- Need immediate results
- Simple single-server setup
- Real-time generation required

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Application                      │
│                (Web API / Celery / Scheduler)                │
└───────────────────────┬─────────────────────────────────────┘
                        │ submit_job()
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     PDFQueueManager                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Worker 1   │  │   Worker 2   │  │   Worker N   │     │
│  │   (Thread)   │  │   (Thread)   │  │   (Thread)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Queue Backend                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  In-Memory  │  │    Redis    │  │   AWS SQS   │        │
│  │  (Development)│ │ (Production)│ │  (Cloud)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     PDFService                               │
│              (PDFTemplateManager core)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    File System / S3                          │
│                   (Generated PDFs)                           │
└─────────────────────────────────────────────────────────────┘
```

### Job Lifecycle

```
SUBMITTED → PENDING → PROCESSING → COMPLETED
                ↓                      ↓
            CANCELLED              FAILED
                                      ↓
                               RETRY (if < max_retries)
                                      ↓
                              FAILED (permanent)
```

---

## Quick Start

### Installation

```bash
# Base requirements
pip install jinja2 weasyprint

# Redis backend (optional)
pip install redis

# AWS SQS backend (optional)
pip install boto3
```

### 5-Minute Example

```python
from pdf_queue_manager import (
    PDFQueueManager,
    InMemoryBackend,
    JobPriority
)
from pdf_patterns import PDFService, PDFServiceConfig

# 1. Initialize backend
backend = InMemoryBackend()

# 2. Initialize PDF service
config = PDFServiceConfig(
    templates_dir='templates',
    output_dir='output'
)
pdf_service = PDFService(config)

# 3. Create queue manager
manager = PDFQueueManager(
    backend=backend,
    pdf_service=pdf_service,
    num_workers=2  # Number of concurrent workers
)

# 4. Start processing
manager.start()

# 5. Submit a job
job_id = manager.submit_job(
    template='invoice.html',
    data={'invoice_number': 'INV-001', 'total': 1500.00},
    output_filename='invoice_001.pdf',
    priority=JobPriority.HIGH
)

print(f"Job submitted: {job_id}")

# 6. Wait for completion
try:
    completed_job = manager.wait_for_job(job_id, timeout=30)
    print(f"✓ PDF generated: {completed_job.result_path}")
except TimeoutError:
    print("✗ Job timed out")
except RuntimeError as e:
    print(f"✗ Job failed: {e}")

# 7. Stop processing
manager.stop()
```

---

## Queue Backends

### 1. In-Memory Backend

**Best for:** Development, testing, single-process applications

```python
from pdf_queue_manager import InMemoryBackend

backend = InMemoryBackend()
```

**Characteristics:**
- No external dependencies
- Fast for low volumes
- Not persistent (data lost on restart)
- Single-process only
- Perfect for development

**Example Use Case:**
```python
# Development/testing environment
if os.getenv('ENV') == 'development':
    backend = InMemoryBackend()
```

---

### 2. Redis Backend (Recommended for Production)

**Best for:** Production, distributed systems, high volume

```python
from pdf_queue_manager import RedisBackend

backend = RedisBackend(
    host='localhost',      # Redis server host
    port=6379,             # Redis server port
    db=0,                  # Redis database number
    password=None,         # Redis password (if required)
    queue_name='pdf_queue' # Queue name prefix
)
```

#### Setup Redis

**Option 1: Docker (Recommended)**
```bash
# Run Redis container
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:alpine

# With persistence
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:alpine redis-server --appendonly yes
```

**Option 2: System Installation**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# macOS
brew install redis
brew services start redis

# Verify
redis-cli ping
# Should return: PONG
```

**Python Package:**
```bash
pip install redis
```

#### Configuration

```python
# Basic configuration
backend = RedisBackend(host='localhost')

# Production configuration
backend = RedisBackend(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD'),
    queue_name='pdf_queue_prod'
)

# Multiple queues
invoice_backend = RedisBackend(queue_name='pdf_invoices')
report_backend = RedisBackend(queue_name='pdf_reports')
```

**Characteristics:**
- ✅ Persistent queue (survives restarts)
- ✅ Multi-process/distributed support
- ✅ High performance (10k+ ops/sec)
- ✅ Priority queue support
- ✅ Atomic operations
- ⚠️ Requires Redis server

---

### 3. AWS SQS Backend

**Best for:** AWS infrastructure, serverless, highly scalable

```python
from pdf_queue_manager import SQSBackend

backend = SQSBackend(
    queue_url='https://sqs.us-east-1.amazonaws.com/123456789/pdf-queue',
    region_name='us-east-1',
    dynamodb_table='pdf-jobs'  # Optional: for job metadata
)
```

#### Setup AWS Resources

**1. Create SQS Queue**
```bash
# Using AWS CLI
aws sqs create-queue \
  --queue-name pdf-queue \
  --attributes VisibilityTimeout=300,ReceiveMessageWaitTimeSeconds=20

# Get queue URL
aws sqs get-queue-url --queue-name pdf-queue
```

**2. Create DynamoDB Table (Optional)**
```bash
aws dynamodb create-table \
  --table-name pdf-jobs \
  --attribute-definitions \
    AttributeName=job_id,AttributeType=S \
  --key-schema \
    AttributeName=job_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

**3. IAM Permissions**

Create IAM policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:PurgeQueue"
      ],
      "Resource": "arn:aws:sqs:us-east-1:123456789:pdf-queue"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789:table/pdf-jobs"
    }
  ]
}
```

**4. Environment Configuration**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Python Package:**
```bash
pip install boto3
```

**Characteristics:**
- ✅ Fully managed AWS service
- ✅ Auto-scaling
- ✅ High availability
- ✅ Dead letter queue support
- ✅ Message retention (up to 14 days)
- ⚠️ AWS-specific
- ⚠️ Network latency
- 💰 Pay per request

---

### Backend Comparison

| Feature | In-Memory | Redis | AWS SQS |
|---------|-----------|-------|---------|
| **Persistence** | ❌ No | ✅ Yes | ✅ Yes |
| **Distributed** | ❌ No | ✅ Yes | ✅ Yes |
| **Setup Complexity** | ✅ Easy | ⚠️ Medium | ⚠️ Medium |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Scalability** | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cost** | Free | Low | Pay-per-use |
| **Best For** | Dev/Test | Production | AWS/Serverless |

---

## Job Management

### Submit Single Job

```python
from pdf_queue_manager import JobPriority

job_id = manager.submit_job(
    template='invoice.html',              # Required
    data={                                 # Required
        'invoice_number': 'INV-001',
        'client_name': 'Acme Corp',
        'items': [...],
        'total': 1500.00
    },
    output_filename='invoice_001.pdf',    # Required
    css_file='invoice_styles.css',        # Optional
    priority=JobPriority.HIGH,            # Optional (default: NORMAL)
    metadata={                             # Optional custom data
        'user_id': 123,
        'department': 'sales',
        'customer_email': 'customer@example.com'
    },
    max_retries=3                         # Optional (default: 3)
)

print(f"Job ID: {job_id}")
```

### Priority Levels

```python
from pdf_queue_manager import JobPriority

# Priority levels (processed in order)
JobPriority.URGENT   # 0 - Highest priority
JobPriority.HIGH     # 1
JobPriority.NORMAL   # 2 - Default
JobPriority.LOW      # 3 - Lowest priority

# Example: Urgent invoice
manager.submit_job(
    template='invoice.html',
    data=data,
    output_filename='urgent_invoice.pdf',
    priority=JobPriority.URGENT
)

# Example: Low priority report
manager.submit_job(
    template='report.html',
    data=data,
    output_filename='monthly_report.pdf',
    priority=JobPriority.LOW
)
```

### Submit Batch Jobs

```python
# Simple batch
jobs = [
    {
        'template': 'invoice.html',
        'data': {'invoice_number': f'INV-{i:03d}'},
        'output': f'invoice_{i:03d}.pdf'
    }
    for i in range(100)
]

job_ids = manager.submit_batch(
    jobs,
    priority=JobPriority.NORMAL  # Default priority for all
)

print(f"Submitted {len(job_ids)} jobs")

# Batch with individual priorities
jobs = [
    {
        'template': 'invoice.html',
        'data': {'id': 1},
        'output': 'urgent_invoice.pdf',
        'priority': JobPriority.URGENT  # Individual priority
    },
    {
        'template': 'report.html',
        'data': {'id': 2},
        'output': 'report.pdf',
        'priority': JobPriority.LOW
    }
]

job_ids = manager.submit_batch(jobs)
```

### Check Job Status

```python
from pdf_queue_manager import JobStatus

# Get status enum
status = manager.get_job_status(job_id)

if status == JobStatus.PENDING:
    print("Job is waiting in queue")
elif status == JobStatus.PROCESSING:
    print("Job is being processed")
elif status == JobStatus.COMPLETED:
    print("Job completed successfully")
elif status == JobStatus.FAILED:
    print("Job failed")
elif status == JobStatus.CANCELLED:
    print("Job was cancelled")
else:
    print("Job not found")

# Get complete job details
job = manager.get_job(job_id)

if job:
    print(f"Job ID: {job.job_id}")
    print(f"Template: {job.template}")
    print(f"Status: {job.status.name}")
    print(f"Priority: {job.priority.name}")
    print(f"Created: {job.created_at}")
    print(f"Started: {job.started_at}")
    print(f"Completed: {job.completed_at}")
    print(f"Result: {job.result_path}")
    print(f"Error: {job.error}")
    print(f"Retries: {job.retry_count}/{job.max_retries}")
    print(f"Metadata: {job.metadata}")
```

### Wait for Job Completion

```python
# Blocking wait with timeout
try:
    completed_job = manager.wait_for_job(
        job_id=job_id,
        timeout=60,          # Maximum wait time in seconds
        poll_interval=0.5    # Check status every 0.5 seconds
    )
    
    print(f"✓ Success!")
    print(f"  PDF: {completed_job.result_path}")
    print(f"  Duration: {(completed_job.completed_at - completed_job.started_at).total_seconds():.2f}s")
    
except TimeoutError:
    print(f"✗ Job did not complete within 60 seconds")
    
except RuntimeError as e:
    print(f"✗ Job failed: {e}")
    
# Wait forever (no timeout)
completed_job = manager.wait_for_job(job_id, timeout=None)

# Async wait pattern
import time

def wait_async(job_id, callback):
    """Non-blocking wait with callback."""
    def check_status():
        while True:
            status = manager.get_job_status(job_id)
            if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job = manager.get_job(job_id)
                callback(job)
                break
            time.sleep(1)
    
    import threading
    thread = threading.Thread(target=check_status, daemon=True)
    thread.start()

# Usage
def on_complete(job):
    print(f"Job {job.job_id} completed!")

wait_async(job_id, on_complete)
```

### Cancel Job

```python
# Cancel a pending job
success = manager.cancel_job(job_id)

if success:
    print("✓ Job cancelled successfully")
else:
    print("✗ Cannot cancel (already processing or completed)")

# Check if cancellable
job = manager.get_job(job_id)
if job and job.status == JobStatus.PENDING:
    manager.cancel_job(job_id)
else:
    print("Job cannot be cancelled")
```

---

## Worker Configuration

### Basic Configuration

```python
# Configure number of workers
manager = PDFQueueManager(
    backend=backend,
    pdf_service=service,
    num_workers=4,        # Number of concurrent workers
    poll_interval=1.0     # Queue polling interval (seconds)
)
```

### Worker Scaling Guidelines

| Workload | Workers | Backend | Notes |
|----------|---------|---------|-------|
| Light (< 100/day) | 1-2 | In-Memory | Single server |
| Medium (100-1000/day) | 2-4 | Redis | Single server |
| Heavy (1000-10000/day) | 4-8 | Redis | Multiple servers |
| Very Heavy (10000+/day) | 8-16 | Redis/SQS | Distributed |

### CPU vs I/O Bound

```python
# I/O bound (network, disk) - More workers
manager = PDFQueueManager(
    backend=backend,
    pdf_service=service,
    num_workers=8  # Can handle more concurrent I/O
)

# CPU bound (complex templates) - Fewer workers
manager = PDFQueueManager(
    backend=backend,
    pdf_service=service,
    num_workers=4  # Match CPU cores
)

# Get CPU count
import os
cpu_count = os.cpu_count() or 4
manager = PDFQueueManager(
    backend=backend,
    pdf_service=service,
    num_workers=cpu_count
)
```

### Lifecycle Management

```python
# Start workers
manager.start()
print(f"Workers started: {manager.num_workers}")

# Check if running
if manager.running:
    print("Manager is active")

# Stop gracefully (wait for current jobs)
manager.stop(timeout=30)  # Wait up to 30 seconds

# Force stop (for emergencies)
manager.running = False

# Context manager pattern
class ManagedQueue:
    def __init__(self, manager):
        self.manager = manager
    
    def __enter__(self):
        self.manager.start()
        return self.manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.stop()

# Usage
with ManagedQueue(manager) as queue:
    job_id = queue.submit_job(...)
    queue.wait_for_job(job_id)
# Automatically stopped
```

---

## Monitoring & Statistics

### Queue Statistics

```python
stats = manager.get_queue_stats()

print(f"Total Jobs: {stats['total_jobs']}")
print(f"Pending: {stats['pending']}")
print(f"Processing: {stats['processing']}")
print(f"Completed: {stats['completed']}")
print(f"Failed: {stats['failed']}")
print(f"Cancelled: {stats['cancelled']}")
print(f"Workers: {stats['workers']}")
print(f"Running: {stats['running']}")

# Real-time monitoring
import time

def monitor_queue(interval=5):
    """Monitor queue in real-time."""
    while True:
        stats = manager.get_queue_stats()
        print(f"\r[{time.strftime('%H:%M:%S')}] "
              f"Pending: {stats['pending']:3d} | "
              f"Processing: {stats['processing']:2d} | "
              f"Completed: {stats['completed']:4d} | "
              f"Failed: {stats['failed']:3d}",
              end='', flush=True)
        time.sleep(interval)

# Run in background
import threading
monitor_thread = threading.Thread(target=monitor_queue, daemon=True)
monitor_thread.start()
```

### Get Jobs by Status

```python
from pdf_queue_manager import JobStatus

# Get all pending jobs
pending = manager.backend.get_all_jobs(status=JobStatus.PENDING)
print(f"Pending jobs: {len(pending)}")
for job in pending[:10]:  # Show first 10
    print(f"  - {job.job_id}: {job.template} (priority: {job.priority.name})")

# Get all failed jobs
failed = manager.backend.get_all_jobs(status=JobStatus.FAILED)
print(f"\nFailed jobs: {len(failed)}")
for job in failed:
    print(f"  - {job.job_id}: {job.error}")
    print(f"    Retries: {job.retry_count}/{job.max_retries}")

# Get completed jobs
completed = manager.backend.get_all_jobs(status=JobStatus.COMPLETED)
print(f"\nCompleted jobs: {len(completed)}")
for job in completed[-10:]:  # Show last 10
    duration = (job.completed_at - job.started_at).total_seconds()
    print(f"  - {job.job_id}: {duration:.2f}s")

# Get all jobs (no filter)
all_jobs = manager.backend.get_all_jobs()
print(f"\nTotal jobs in system: {len(all_jobs)}")
```

### Performance Metrics

```python
def calculate_metrics():
    """Calculate queue performance metrics."""
    completed = manager.backend.get_all_jobs(status=JobStatus.COMPLETED)
    
    if not completed:
        return None
    
    # Calculate average processing time
    durations = [
        (job.completed_at - job.started_at).total_seconds()
        for job in completed
        if job.started_at and job.completed_at
    ]
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    min_duration = min(durations) if durations else 0
    max_duration = max(durations) if durations else 0
    
    # Calculate throughput
    if len(completed) > 1:
        first_job = min(completed, key=lambda j: j.created_at)
        last_job = max(completed, key=lambda j: j.completed_at)
        time_span = (last_job.completed_at - first_job.created_at).total_seconds()
        throughput = len(completed) / (time_span / 3600)  # jobs per hour
    else:
        throughput = 0
    
    return {
        'total_completed': len(completed),
        'avg_duration': avg_duration,
        'min_duration': min_duration,
        'max_duration': max_duration,
        'throughput_per_hour': throughput
    }

metrics = calculate_metrics()
if metrics:
    print(f"Average Duration: {metrics['avg_duration']:.2f}s")
    print(f"Min Duration: {metrics['min_duration']:.2f}s")
    print(f"Max Duration: {metrics['max_duration']:.2f}s")
    print(f"Throughput: {metrics['throughput_per_hour']:.1f} jobs/hour")
```

---

## Production Patterns

### Pattern 1: Flask REST API

```python
from flask import Flask, request, jsonify, send_file
from pdf_queue_manager import (
    PDFQueueManager, RedisBackend, JobPriority, JobStatus
)
from pdf_patterns import PDFService, PDFServiceConfig

app = Flask(__name__)

# Initialize queue manager (once)
backend = RedisBackend(
    host=os.getenv('REDIS_HOST', 'localhost'),
    queue_name='pdf_api_queue'
)
service = PDFService(PDFServiceConfig.from_env())
manager = PDFQueueManager(backend, service, num_workers=4)

# Start on app startup
@app.before_first_request
def startup():
    manager.start()

# Stop on app shutdown
import atexit
atexit.register(lambda: manager.stop())

@app.route('/api/pdf', methods=['POST'])
def create_pdf():
    """
    Create PDF generation job.
    
    POST /api/pdf
    {
        "template": "invoice.html",
        "data": {...},
        "filename": "invoice.pdf",
        "priority": "high"
    }
    
    Returns: 202 Accepted
    {
        "job_id": "abc-123",
        "status": "pending"
    }
    """
    data = request.get_json()
    
    # Validate
    required = ['template', 'data', 'filename']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Map priority
    priority_map = {
        'urgent': JobPriority.URGENT,
        'high': JobPriority.HIGH,
        'normal': JobPriority.NORMAL,
        'low': JobPriority.LOW
    }
    priority = priority_map.get(
        data.get('priority', 'normal'),
        JobPriority.NORMAL
    )
    
    # Submit job
    job_id = manager.submit_job(
        template=data['template'],
        data=data['data'],
        output_filename=data['filename'],
        priority=priority,
        metadata={
            'user_id': request.headers.get('X-User-ID'),
            'ip_address': request.remote_addr
        }
    )
    
    return jsonify({
        'job_id': job_id,
        'status': 'pending',
        'check_url': f'/api/pdf/{job_id}'
    }), 202

@app.route('/api/pdf/<job_id>', methods=['GET'])
def get_pdf_status(job_id):
    """
    Get PDF job status.
    
    GET /api/pdf/{job_id}
    
    Returns:
    {
        "job_id": "abc-123",
        "status": "completed",
        "created_at": "2024-03-25T10:00:00",
        "result_url": "/api/pdf/abc-123/download"
    }
    """
    job = manager.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    response = {
        'job_id': job.job_id,
        'status': job.status.name.lower(),
        'created_at': job.created_at.isoformat(),
        'priority': job.priority.name.lower()
    }
    
    if job.started_at:
        response['started_at'] = job.started_at.isoformat()
    
    if job.completed_at:
        response['completed_at'] = job.completed_at.isoformat()
        duration = (job.completed_at - job.started_at).total_seconds()
        response['duration'] = f"{duration:.2f}s"
    
    if job.status == JobStatus.COMPLETED:
        response['download_url'] = f'/api/pdf/{job_id}/download'
    
    if job.status == JobStatus.FAILED:
        response['error'] = job.error
        response['retries'] = f"{job.retry_count}/{job.max_retries}"
    
    return jsonify(response)

@app.route('/api/pdf/<job_id>/download', methods=['GET'])
def download_pdf(job_id):
    """Download generated PDF."""
    job = manager.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != JobStatus.COMPLETED:
        return jsonify({
            'error': 'PDF not ready',
            'status': job.status.name.lower()
        }), 400
    
    return send_file(
        job.result_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=job.output_filename
    )

@app.route('/api/pdf/<job_id>', methods=['DELETE'])
def cancel_pdf(job_id):
    """Cancel pending job."""
    success = manager.cancel_job(job_id)
    
    if success:
        return jsonify({'message': 'Job cancelled'}), 200
    else:
        return jsonify({'error': 'Cannot cancel job'}), 400

@app.route('/api/queue/stats', methods=['GET'])
def queue_stats():
    """Get queue statistics."""
    stats = manager.get_queue_stats()
    return jsonify(stats)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    stats = manager.get_queue_stats()
    
    health = {
        'status': 'healthy' if manager.running else 'unhealthy',
        'workers': stats['workers'],
        'queue_size': stats['pending'] + stats['processing']
    }
    
    status_code = 200 if manager.running else 503
    return jsonify(health), status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Client Usage:**
```bash
# Submit job
curl -X POST http://localhost:5000/api/pdf \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 123" \
  -d '{
    "template": "invoice.html",
    "data": {"invoice_number": "INV-001"},
    "filename": "invoice.pdf",
    "priority": "high"
  }'
# Response: {"job_id": "abc-123", "status": "pending"}

# Check status
curl http://localhost:5000/api/pdf/abc-123

# Download when ready
curl http://localhost:5000/api/pdf/abc-123/download -o invoice.pdf

# Queue stats
curl http://localhost:5000/api/queue/stats
```

---

### Pattern 2: Django Integration

```python
# myapp/services.py
from django.conf import settings
from pdf_queue_manager import PDFQueueManager, RedisBackend
from pdf_patterns import PDFService, PDFServiceConfig

class PDFQueueService:
    """Singleton PDF queue service for Django."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            backend = RedisBackend(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                queue_name='django_pdf_queue'
            )
            
            config = PDFServiceConfig(
                templates_dir=settings.PDF_TEMPLATES_DIR,
                output_dir=settings.PDF_OUTPUT_DIR
            )
            
            pdf_service = PDFService(config)
            
            cls._instance = PDFQueueManager(
                backend=backend,
                pdf_service=pdf_service,
                num_workers=settings.PDF_WORKERS
            )
            
            cls._instance.start()
        
        return cls._instance

# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        """Start queue manager on app startup."""
        from .services import PDFQueueService
        PDFQueueService.get_instance()

# myapp/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services import PDFQueueService

@api_view(['POST'])
def generate_pdf(request):
    """Generate PDF endpoint."""
    queue = PDFQueueService.get_instance()
    
    job_id = queue.submit_job(
        template=request.data['template'],
        data=request.data['data'],
        output_filename=request.data['filename'],
        metadata={'user_id': request.user.id}
    )
    
    return Response({
        'job_id': job_id,
        'status': 'pending'
    }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
def pdf_status(request, job_id):
    """Check PDF status."""
    queue = PDFQueueService.get_instance()
    job = queue.get_job(job_id)
    
    if not job:
        return Response(
            {'error': 'Job not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'job_id': job.job_id,
        'status': job.status.name.lower(),
        'result_path': job.result_path
    })
```

---

### Pattern 3: Celery Integration

```python
# tasks.py
from celery import Celery
from pdf_queue_manager import PDFQueueManager, RedisBackend, JobPriority
from pdf_patterns import PDFService, PDFServiceConfig

celery = Celery('tasks', broker='redis://localhost:6379/0')

# Initialize queue manager
backend = RedisBackend(host='localhost', queue_name='celery_pdf_queue')
service = PDFService(PDFServiceConfig())
manager = PDFQueueManager(backend, service, num_workers=4)
manager.start()

@celery.task(bind=True, max_retries=3)
def generate_pdf_task(self, template, data, filename, priority='normal'):
    """
    Celery task for PDF generation.
    
    Usage:
        from tasks import generate_pdf_task
        
        result = generate_pdf_task.delay(
            'invoice.html',
            {'id': 1},
            'invoice.pdf',
            priority='high'
        )
        
        # Wait for result
        job_info = result.get(timeout=300)
        print(f"PDF: {job_info['path']}")
    """
    try:
        priority_map = {
            'urgent': JobPriority.URGENT,
            'high': JobPriority.HIGH,
            'normal': JobPriority.NORMAL,
            'low': JobPriority.LOW
        }
        
        job_id = manager.submit_job(
            template=template,
            data=data,
            output_filename=filename,
            priority=priority_map.get(priority, JobPriority.NORMAL)
        )
        
        # Wait for completion
        completed_job = manager.wait_for_job(job_id, timeout=300)
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'path': completed_job.result_path
        }
    
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60)

@celery.task
def generate_batch_task(jobs):
    """Generate multiple PDFs."""
    job_ids = manager.submit_batch(jobs)
    
    results = []
    for job_id in job_ids:
        try:
            job = manager.wait_for_job(job_id, timeout=300)
            results.append({
                'job_id': job_id,
                'status': 'completed',
                'path': job.result_path
            })
        except Exception as e:
            results.append({
                'job_id': job_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return results

@celery.task
def cleanup_old_pdfs():
    """Periodic task to cleanup old PDFs."""
    deleted = service.cleanup_old_files(days=7)
    return {'deleted': deleted}

# Periodic tasks
from celery.schedules import crontab

celery.conf.beat_schedule = {
    'cleanup-old-pdfs': {
        'task': 'tasks.cleanup_old_pdfs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    }
}
```

---

### Pattern 4: Scheduled Jobs

```python
# scheduler.py
import schedule
import time
from datetime import datetime
from pdf_queue_manager import PDFQueueManager, RedisBackend, JobPriority
from pdf_patterns import PDFService, PDFServiceConfig

# Initialize
backend = RedisBackend(host='localhost')
service = PDFService(PDFServiceConfig())
manager = PDFQueueManager(backend, service, num_workers=4)
manager.start()

def generate_daily_report():
    """Generate daily report at 9 AM."""
    print(f"[{datetime.now()}] Generating daily report...")
    
    # Fetch data
    data = {
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'metrics': fetch_daily_metrics(),  # Your data source
        'summary': fetch_summary()
    }
    
    job_id = manager.submit_job(
        template='daily_report.html',
        data=data,
        output_filename=f'daily_report_{datetime.now():%Y%m%d}.pdf',
        priority=JobPriority.HIGH,
        metadata={'report_type': 'daily'}
    )
    
    print(f"Daily report job submitted: {job_id}")

def generate_weekly_summary():
    """Generate weekly summary on Monday."""
    print(f"[{datetime.now()}] Generating weekly summary...")
    
    data = fetch_weekly_data()
    
    job_id = manager.submit_job(
        template='weekly_summary.html',
        data=data,
        output_filename=f'weekly_summary_{datetime.now():%Y_W%W}.pdf',
        priority=JobPriority.HIGH
    )
    
    print(f"Weekly summary job submitted: {job_id}")

def generate_monthly_invoices():
    """Generate all customer invoices on 1st of month."""
    print(f"[{datetime.now()}] Generating monthly invoices...")
    
    customers = get_customers()  # Your data source
    
    jobs = [
        {
            'template': 'invoice.html',
            'data': get_invoice_data(customer),
            'output': f'invoice_{customer.id}_{datetime.now():%Y%m}.pdf',
            'priority': JobPriority.NORMAL,
            'metadata': {'customer_id': customer.id}
        }
        for customer in customers
    ]
    
    job_ids = manager.submit_batch(jobs)
    print(f"Submitted {len(job_ids)} invoice jobs")

def cleanup_old_files():
    """Cleanup old PDFs."""
    print(f"[{datetime.now()}] Cleaning up old files...")
    deleted = service.cleanup_old_files(days=30)
    print(f"Deleted {deleted} old PDFs")

# Schedule jobs
schedule.every().day.at("09:00").do(generate_daily_report)
schedule.every().monday.at("10:00").do(generate_weekly_summary)
schedule.every().month.at("00:01").do(generate_monthly_invoices)
schedule.every().sunday.at("03:00").do(cleanup_old_files)

# Run scheduler
print("Scheduler started. Press Ctrl+C to exit.")
try:
    while True:
        schedule.run_pending()
        time.sleep(60)
except KeyboardInterrupt:
    print("\nShutting down...")
    manager.stop()
```

**Run as systemd service:**
```ini
# /etc/systemd/system/pdf-scheduler.service
[Unit]
Description=PDF Generation Scheduler
After=network.target redis.service

[Service]
Type=simple
User=pdfuser
WorkingDirectory=/app
Environment="PYTHONPATH=/app"
ExecStart=/usr/bin/python3 /app/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable pdf-scheduler
sudo systemctl start pdf-scheduler
sudo systemctl status pdf-scheduler
```

---

## Error Handling & Retries

### Automatic Retry Configuration

```python
# Configure retry behavior
job_id = manager.submit_job(
    template='invoice.html',
    data=data,
    output_filename='invoice.pdf',
    max_retries=3  # Retry up to 3 times
)

# Custom retry logic per job
urgent_job = manager.submit_job(
    template='urgent_report.html',
    data=data,
    output_filename='urgent.pdf',
    max_retries=5,  # More retries for important jobs
    priority=JobPriority.URGENT
)

# No retries (fail immediately)
job_id = manager.submit_job(
    template='test.html',
    data=data,
    output_filename='test.pdf',
    max_retries=0
)
```

### Retry Flow

```
Job Fails
    ↓
retry_count < max_retries?
    ↓ YES                      ↓ NO
Re-queue job          Mark as FAILED
    ↓
Back to PENDING
```

### Error Callbacks

```python
def on_job_failed(job, error):
    """Handle failed jobs."""
    print(f"Job {job.job_id} failed: {error}")
    
    # Check if permanently failed
    if job.retry_count >= job.max_retries:
        print(f"  Job permanently failed after {job.retry_count} retries")
        
        # Send alert
        send_alert(
            f"PDF generation failed: {job.template}",
            details=f"Error: {error}\nJob ID: {job.job_id}"
        )
        
        # Log to error tracking
        import sentry_sdk
        sentry_sdk.capture_exception(error)
        
        # Notify user
        user_email = job.metadata.get('user_email')
        if user_email:
            send_email(
                to=user_email,
                subject="PDF Generation Failed",
                body=f"Your PDF could not be generated. Error: {error}"
            )
    else:
        print(f"  Will retry ({job.retry_count + 1}/{job.max_retries})")

# Register callback
manager.on_job_failed = on_job_failed
```

### Common Error Scenarios

```python
# Handle specific errors
def smart_error_handler(job, error):
    """Handle errors intelligently."""
    error_str = str(error)
    
    if "Template not found" in error_str:
        # Template issue - don't retry
        print(f"Template error: {error_str}")
        job.max_retries = 0  # Prevent retries
        manager.backend.update_job(job)
        
    elif "Memory" in error_str:
        # Memory issue - wait longer before retry
        print("Memory error - will retry after longer delay")
        time.sleep(30)
        
    elif "Timeout" in error_str:
        # Timeout - might work on retry
        print("Timeout - retrying...")
        
    else:
        # Unknown error
        print(f"Unknown error: {error_str}")

manager.on_job_failed = smart_error_handler
```

---

## Performance Tuning

### Benchmark Your System

```python
import time
from pdf_queue_manager import PDFQueueManager, InMemoryBackend

def benchmark_queue(num_jobs=100, num_workers=4):
    """Benchmark queue performance."""
    backend = InMemoryBackend()
    service = PDFService(PDFServiceConfig())
    manager = PDFQueueManager(backend, service, num_workers=num_workers)
    
    manager.start()
    
    # Submit jobs
    start_time = time.time()
    job_ids = []
    
    for i in range(num_jobs):
        job_id = manager.submit_job(
            template='simple.html',
            data={'id': i},
            output_filename=f'test_{i}.pdf'
        )
        job_ids.append(job_id)
    
    submit_time = time.time() - start_time
    
    # Wait for all to complete
    for job_id in job_ids:
        manager.wait_for_job(job_id, timeout=300)
    
    total_time = time.time() - start_time
    
    manager.stop()
    
    print(f"\nBenchmark Results:")
    print(f"  Jobs: {num_jobs}")
    print(f"  Workers: {num_workers}")
    print(f"  Submit time: {submit_time:.2f}s")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg per job: {(total_time / num_jobs) * 1000:.0f}ms")
    print(f"  Throughput: {num_jobs / total_time:.1f} jobs/sec")

# Run benchmarks
benchmark_queue(num_jobs=100, num_workers=2)
benchmark_queue(num_jobs=100, num_workers=4)
benchmark_queue(num_jobs=100, num_workers=8)
```

### Optimization Tips

#### 1. Choose Right Worker Count

```python
import os

# Rule of thumb for worker count
def optimal_workers():
    """Calculate optimal worker count."""
    cpu_count = os.cpu_count() or 4
    
    # For CPU-bound tasks (complex templates)
    cpu_bound_workers = cpu_count
    
    # For I/O-bound tasks (simple templates, network storage)
    io_bound_workers = cpu_count * 2
    
    return {
        'cpu_bound': cpu_bound_workers,
        'io_bound': io_bound_workers
    }

workers = optimal_workers()
print(f"CPU-bound: {workers['cpu_bound']} workers")
print(f"I/O-bound: {workers['io_bound']} workers")
```

#### 2. Optimize Templates

```python
# Bad - Slow template
"""
<style>
    .item {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        transform: rotate(2deg);
        animation: slideIn 1s ease-in-out;
    }
</style>
"""

# Good - Fast template
"""
<style>
    .item {
        background: #667eea;
        border: 1px solid #ddd;
    }
</style>
"""
```

#### 3. Use Appropriate Backend

```python
# Development - Fast setup
if os.getenv('ENV') == 'development':
    backend = InMemoryBackend()

# Production - Persistent, distributed
elif os.getenv('ENV') == 'production':
    backend = RedisBackend(
        host=os.getenv('REDIS_HOST'),
        queue_name='prod_queue'
    )

# AWS - Fully managed
elif os.getenv('ENV') == 'aws':
    backend = SQSBackend(
        queue_url=os.getenv('SQS_QUEUE_URL'),
        dynamodb_table='pdf-jobs-prod'
    )
```

#### 4. Batch Similar Jobs

```python
# Inefficient - Submit one by one
for customer in customers:
    manager.submit_job(
        template='invoice.html',
        data=get_customer_data(customer),
        output_filename=f'invoice_{customer.id}.pdf'
    )

# Efficient - Submit as batch
jobs = [
    {
        'template': 'invoice.html',
        'data': get_customer_data(customer),
        'output': f'invoice_{customer.id}.pdf'
    }
    for customer in customers
]
manager.submit_batch(jobs)
```

#### 5. Monitor and Adjust

```python
def auto_scale_workers():
    """Automatically adjust worker count based on queue size."""
    stats = manager.get_queue_stats()
    pending = stats['pending']
    workers = stats['workers']
    
    # Scale up if queue is growing
    if pending > 100 and workers < 8:
        print(f"Scaling up: {pending} pending jobs")
        # Note: Would need to restart with more workers
        # In practice, use multiple instances
    
    # Scale down if queue is empty
    elif pending < 10 and workers > 2:
        print(f"Scaling down: {pending} pending jobs")

# Run periodically
import threading
import time

def monitor_and_scale():
    while True:
        auto_scale_workers()
        time.sleep(60)

monitor_thread = threading.Thread(target=monitor_and_scale, daemon=True)
monitor_thread.start()
```

---

## Deployment Examples

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  pdf-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - PDF_WORKERS=4
      - PDF_TEMPLATES_DIR=/app/templates
      - PDF_OUTPUT_DIR=/app/output
    volumes:
      - ./templates:/app/templates:ro
      - ./output:/app/output
      - pdf-data:/app/data
    depends_on:
      redis:
        condition: service_healthy
    command: gunicorn -w 4 -b 0.0.0.0:5000 app:app

  pdf-worker:
    build: .
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - PDF_WORKERS=4
      - PDF_TEMPLATES_DIR=/app/templates
      - PDF_OUTPUT_DIR=/app/output
    volumes:
      - ./templates:/app/templates:ro
      - ./output:/app/output
      - pdf-data:/app/data
    depends_on:
      redis:
        condition: service_healthy
    command: python worker.py
    deploy:
      replicas: 2  # Multiple worker instances

volumes:
  redis-data:
  pdf-data:
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p templates output data && \
    chmod 777 output

# Non-root user
RUN useradd -m pdfuser && chown -R pdfuser:pdfuser /app
USER pdfuser

EXPOSE 5000

CMD ["python", "app.py"]
```

```bash
# Start services
docker-compose up -d

# Scale workers
docker-compose up -d --scale pdf-worker=4

# View logs
docker-compose logs -f pdf-worker

# Stop
docker-compose down
```

---

### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pdf-config
data:
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  PDF_WORKERS: "4"
  PDF_TEMPLATES_DIR: "/app/templates"
  PDF_OUTPUT_DIR: "/app/output"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdf-worker
  template:
    metadata:
      labels:
        app: pdf-worker
    spec:
      containers:
      - name: worker
        image: your-registry/pdf-worker:latest
        envFrom:
        - configMapRef:
            name: pdf-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        volumeMounts:
        - name: templates
          mountPath: /app/templates
          readOnly: true
        - name: output
          mountPath: /app/output
      volumes:
      - name: templates
        persistentVolumeClaim:
          claimName: pdf-templates-pvc
      - name: output
        persistentVolumeClaim:
          claimName: pdf-output-pvc

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pdf-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pdf-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Jobs Stuck in PENDING

**Symptoms:**
- Jobs submitted but never processed
- Queue stats show pending jobs but no processing

**Solutions:**
```python
# Check if workers are running
if not manager.running:
    print("Workers not started!")
    manager.start()

# Check worker count
stats = manager.get_queue_stats()
print(f"Workers: {stats['workers']}")
if stats['workers'] == 0:
    manager.stop()
    manager.start()

# Check backend connection
try:
    backend.get_pending_count()
    print("Backend connection OK")
except Exception as e:
    print(f"Backend error: {e}")
```

#### Issue 2: High Failure Rate

**Symptoms:**
- Many jobs in FAILED status
- Errors in logs

**Solutions:**
```python
# Analyze failed jobs
failed_jobs = manager.backend.get_all_jobs(status=JobStatus.FAILED)

error_summary = {}
for job in failed_jobs:
    error_type = job.error.split(':')[0] if job.error else 'Unknown'
    error_summary[error_type] = error_summary.get(error_type, 0) + 1

print("Error Summary:")
for error, count in sorted(error_summary.items(), key=lambda x: -x[1]):
    print(f"  {error}: {count}")

# Common fixes:
# 1. Template errors - validate templates
# 2. Data errors - validate input data
# 3. Memory errors - reduce worker count
# 4. Timeout errors - increase timeout
```

#### Issue 3: Slow Processing

**Symptoms:**
- Jobs taking too long
- Low throughput

**Solutions:**
```python
# 1. Check worker utilization
stats = manager.get_queue_stats()
utilization = stats['processing'] / stats['workers']
print(f"Worker utilization: {utilization:.0%}")

if utilization < 0.5:
    print("Workers underutilized - check for bottlenecks")

# 2. Analyze job durations
completed = manager.backend.get_all_jobs(status=JobStatus.COMPLETED)
durations = [
    (job.completed_at - job.started_at).total_seconds()
    for job in completed[-100:]  # Last 100 jobs
    if job.started_at and job.completed_at
]

import statistics
print(f"Avg duration: {statistics.mean(durations):.2f}s")
print(f"Median duration: {statistics.median(durations):.2f}s")
print(f"Max duration: {max(durations):.2f}s")

# 3. Optimize based on findings
# - Simplify templates if durations are high
# - Increase workers if utilization is high
# - Check for I/O bottlenecks (disk, network)
```

#### Issue 4: Memory Leaks

**Symptoms:**
- Memory usage grows over time
- Workers crash

**Solutions:**
```python
# 1. Enable cleanup
service.cleanup_old_files(days=1)

# 2. Limit queue size
MAX_QUEUE_SIZE = 1000
pending = manager.backend.get_pending_count()
if pending > MAX_QUEUE_SIZE:
    print(f"Queue too large: {pending}")
    # Reject new jobs or scale up

# 3. Monitor memory
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_mb:.1f} MB")

# 4. Restart workers periodically
import time
start_time = time.time()
MAX_RUNTIME = 3600  # 1 hour

if time.time() - start_time > MAX_RUNTIME:
    manager.stop()
    manager.start()
    start_time = time.time()
```

---

## Summary & Best Practices

### Quick Reference

| Task | Command |
|------|---------|
| **Submit job** | `manager.submit_job(template, data, filename)` |
| **Submit batch** | `manager.submit_batch(jobs)` |
| **Check status** | `manager.get_job_status(job_id)` |
| **Wait for job** | `manager.wait_for_job(job_id, timeout=60)` |
| **Cancel job** | `manager.cancel_job(job_id)` |
| **Get stats** | `manager.get_queue_stats()` |
| **Start workers** | `manager.start()` |
| **Stop workers** | `manager.stop()` |

### Checklist for Production

- [ ] Use Redis or SQS backend (not in-memory)
- [ ] Configure appropriate worker count
- [ ] Set up monitoring and alerts
- [ ] Implement error callbacks
- [ ] Enable automatic cleanup
- [ ] Configure retry logic
- [ ] Set up health checks
- [ ] Use environment variables for config
- [ ] Implement rate limiting if needed
- [ ] Set up logging and metrics
- [ ] Test failure scenarios
- [ ] Document recovery procedures

### Performance Guidelines

- **Workers:** Start with CPU count, adjust based on workload
- **Retries:** 3 retries for most jobs, 0 for test jobs
- **Cleanup:** Run daily, keep PDFs for 7-30 days
- **Monitoring:** Check queue stats every 5 minutes
- **Scaling:** Scale horizontally (more instances) not vertically

---
