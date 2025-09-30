# PDF Generation System - Complete Engineer's Guide

> **Complete documentation for both the base PDFTemplateManager and advanced pattern classes**

## Table of Contents

1. [Quick Start](#quick-start)
2. [Base Class: PDFTemplateManager](#base-class-pdftemplatemanager)
3. [Advanced Patterns Class](#advanced-patterns-class)
4. [Configuration](#configuration)
5. [All Design Patterns](#all-design-patterns)
6. [Real-World Examples](#real-world-examples)
7. [Production Deployment](#production-deployment)
8. [Testing](#testing)
9. [Performance Guide](#performance-guide)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
# System dependencies (Ubuntu/Debian)
sudo apt-get install -y python3-cffi libpango-1.0-0 libpangoft2-1.0-0

# Python dependencies
pip install jinja2==3.1.3 weasyprint==60.2
```

### 30-Second Example

```python
from pdf_template_manager import PDFTemplateManager

# Initialize
manager = PDFTemplateManager(
    templates_dir='templates',
    output_dir='output'
)

# Generate PDF
data = {'title': 'Hello World', 'content': 'My first PDF'}
pdf_path = manager.generate_pdf('template.html', data, 'output.pdf')
print(f"PDF created: {pdf_path}")
```

---

## Base Class: PDFTemplateManager

### Overview

The `PDFTemplateManager` is the core class for PDF generation. Use this when you need:
- Simple, straightforward PDF generation
- Direct control over templates and data
- Basic batch processing
- Template validation

### Full API Reference

#### Constructor

```python
PDFTemplateManager(
    templates_dir: str = 'templates',
    output_dir: str = 'output',
    static_dir: Optional[str] = None,
    auto_create_dirs: bool = True
)
```

**Parameters:**
- `templates_dir`: Directory containing HTML templates
- `output_dir`: Directory for generated PDFs
- `static_dir`: Directory for CSS/images (defaults to `templates_dir/static`)
- `auto_create_dirs`: Automatically create directories if missing

**Example:**
```python
manager = PDFTemplateManager(
    templates_dir='my_templates',
    output_dir='pdfs',
    static_dir='assets',
    auto_create_dirs=True
)
```

---

#### Method: generate_pdf()

```python
generate_pdf(
    template_name: str,
    data: Dict[str, Any],
    output_filename: str,
    css_file: Optional[str] = None,
    base_url: Optional[str] = None
) -> Path
```

**Generate a single PDF from template.**

**Parameters:**
- `template_name`: HTML template filename (e.g., 'invoice.html')
- `data`: Dictionary with template variables
- `output_filename`: Name for output PDF
- `css_file`: Optional CSS file from static_dir
- `base_url`: Base URL for resolving relative paths

**Returns:** `Path` object to generated PDF

**Example:**
```python
data = {
    'invoice_number': 'INV-001',
    'client_name': 'Acme Corp',
    'items': [
        {'name': 'Service', 'price': 100}
    ],
    'total': 100
}

pdf_path = manager.generate_pdf(
    template_name='invoice.html',
    data=data,
    output_filename='invoice_001.pdf',
    css_file='invoice_styles.css'  # Optional
)
```

---

#### Method: batch_generate()

```python
batch_generate(
    jobs: List[Dict[str, Any]],
    continue_on_error: bool = True
) -> List[Dict[str, Any]]
```

**Generate multiple PDFs in batch.**

**Parameters:**
- `jobs`: List of job dictionaries, each containing:
  - `template`: Template filename
  - `data`: Template data
  - `output`: Output filename
  - `css_file`: (optional) CSS filename
- `continue_on_error`: Continue if one job fails

**Returns:** List of result dictionaries with:
- `job_index`: Index in jobs list
- `success`: Boolean success flag
- `output_path`: Path to PDF (if successful)
- `error`: Error message (if failed)
- `template`: Template name

**Example:**
```python
jobs = [
    {
        'template': 'invoice.html',
        'data': {'invoice_number': 'INV-001', 'total': 100},
        'output': 'invoice_001.pdf'
    },
    {
        'template': 'receipt.html',
        'data': {'receipt_id': 'REC-001', 'amount': 50},
        'output': 'receipt_001.pdf'
    }
]

results = manager.batch_generate(jobs)

for result in results:
    if result['success']:
        print(f"✓ {result['output_path']}")
    else:
        print(f"✗ Error: {result['error']}")
```

---

#### Method: list_templates()

```python
list_templates() -> List[str]
```

**List all available templates.**

**Returns:** List of template filenames

**Example:**
```python
templates = manager.list_templates()
print("Available templates:", templates)
# Output: ['invoice.html', 'report.html', 'certificate.html']
```

---

#### Method: validate_template()

```python
validate_template(template_name: str) -> Dict[str, Any]
```

**Validate template syntax.**

**Parameters:**
- `template_name`: Template to validate

**Returns:** Dictionary with:
- `valid`: Boolean validity flag
- `template`: Template name
- `message`: Success message (if valid)
- `error`: Error message (if invalid)

**Example:**
```python
result = manager.validate_template('invoice.html')

if result['valid']:
    print(f"✓ {result['message']}")
else:
    print(f"✗ {result['error']}")
```

---

#### Method: render_template()

```python
render_template(
    template_name: str,
    data: Dict[str, Any]
) -> str
```

**Render template to HTML string (without PDF conversion).**

**Example:**
```python
html = manager.render_template('invoice.html', data)
print(html)  # Raw HTML output
```

---

#### Method: preview_html()

```python
preview_html(
    template_name: str,
    data: Dict[str, Any],
    output_filename: str = 'preview.html'
) -> Path
```

**Generate HTML preview without PDF conversion.**

**Example:**
```python
html_path = manager.preview_html(
    'invoice.html',
    data,
    'preview_invoice.html'
)
# Open preview_invoice.html in browser to check layout
```

---

#### Method: get_template_variables()

```python
get_template_variables(template_name: str) -> List[str]
```

**Extract variable names from template.**

**Example:**
```python
variables = manager.get_template_variables('invoice.html')
print("Required variables:", variables)
# Output: ['invoice_number', 'client_name', 'items', 'total']
```

---

#### Method: create_template_from_string()

```python
create_template_from_string(
    template_name: str,
    html_content: str
) -> Path
```

**Create new template from HTML string.**

**Example:**
```python
html = """
<!DOCTYPE html>
<html>
<body>
    <h1>{{ title }}</h1>
</body>
</html>
"""

path = manager.create_template_from_string('new_template.html', html)
print(f"Template created: {path}")
```

---

### Built-in Jinja2 Filters

The manager provides custom filters for templates:

```html
<!-- Currency formatting -->
{{ 1234.56|currency }}           <!-- Output: $1,234.56 -->
{{ 1234.56|currency('€') }}      <!-- Output: €1,234.56 -->

<!-- Date formatting -->
{{ date|date_format('%Y-%m-%d') }}           <!-- Output: 2024-03-25 -->
{{ date|date_format('%B %d, %Y') }}          <!-- Output: March 25, 2024 -->

<!-- Percentage -->
{{ 0.15|percentage }}            <!-- Output: 15.00% -->
{{ 0.15|percentage(1) }}         <!-- Output: 15.0% -->

<!-- Truncate text -->
{{ long_text|truncate_words(50) }}  <!-- First 50 words... -->
```

### Global Functions

```html
<!-- Current timestamp -->
{{ now('%Y-%m-%d') }}            <!-- Today's date -->

<!-- Number range -->
{{ range(1, 10) }}               <!-- [1, 2, 3, ..., 9] -->

<!-- Sum field from list -->
{{ sum_field(items, 'price') }}  <!-- Sum all prices -->
```

---

## Advanced Patterns Class

### Overview

The advanced patterns provide production-ready implementations for:
- Thread-safe singleton service
- Async/parallel processing
- Data transformation pipelines
- Storage strategies (local, S3)
- Lifecycle hooks
- Builder pattern for complex jobs

### When to Use Each Pattern

| Pattern | Use Case | Best For |
|---------|----------|----------|
| **PDFService** (Singleton) | Most common use | Web apps, APIs, general use |
| **AsyncPDFService** | High volume | Batch processing, background jobs |
| **PDFFactory** | Multiple doc types | Apps with data transformation needs |
| **PDFJobBuilder** | Complex setup | Configurable pipelines |
| **PDFServiceWithHooks** | Event-driven | Monitoring, notifications, logging |
| **PDFServiceWithStorage** | Cloud storage | S3, distributed systems |

---

## Configuration

### PDFServiceConfig

Complete configuration object for all patterns:

```python
from dataclasses import dataclass

@dataclass
class PDFServiceConfig:
    # Directories
    templates_dir: str = 'templates'
    output_dir: str = 'output'
    static_dir: Optional[str] = None
    
    # Performance
    max_workers: int = 4
    timeout: int = 30
    enable_cache: bool = True
    
    # Logging
    log_level: str = 'INFO'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Cleanup
    auto_cleanup: bool = False
    cleanup_age_days: int = 7
```

### Creating Configurations

**Method 1: Direct instantiation**
```python
from pdf_patterns import PDFServiceConfig

config = PDFServiceConfig(
    templates_dir='my_templates',
    output_dir='my_output',
    max_workers=8,
    log_level='DEBUG'
)
```

**Method 2: From environment variables**
```python
# Set environment variables first
# export PDF_TEMPLATES_DIR=/app/templates
# export PDF_MAX_WORKERS=8

config = PDFServiceConfig.from_env()
```

**Method 3: From dictionary**
```python
config_dict = {
    'templates_dir': 'templates',
    'output_dir': 'output',
    'max_workers': 4
}

config = PDFServiceConfig.from_dict(config_dict)
```

---

## All Design Patterns

### Pattern 1: Singleton Service (Most Common)

**Use when:** You need a single, thread-safe service instance across your application.

```python
from pdf_patterns import PDFService, PDFServiceConfig

# Initialize once (returns same instance for same config)
config = PDFServiceConfig(
    templates_dir='templates',
    output_dir='output'
)
service = PDFService(config)

# Use anywhere in your app
pdf_path = service.generate(
    template='invoice.html',
    data={'invoice_number': 'INV-001'},
    output_filename='invoice.pdf'
)

# Thread-safe - safe to call from multiple threads
```

**Key Methods:**
```python
# Generate single PDF
service.generate(template, data, filename, css_file=None)

# Batch generation
service.batch_generate(jobs, continue_on_error=True)

# List templates
service.list_templates()

# Validate template
service.validate_template(template)

# Get template variables
service.get_template_variables(template)

# Cleanup old files
service.cleanup_old_files(days=7)
```

---

### Pattern 2: Async Service (High Volume)

**Use when:** Generating many PDFs concurrently (100+ at once).

```python
from pdf_patterns import AsyncPDFService, PDFServiceConfig
import asyncio

config = PDFServiceConfig(max_workers=8)
service = AsyncPDFService(config)

# Single async generation
async def generate_one():
    pdf_path = await service.generate_async(
        template='invoice.html',
        data={'id': 1},
        output_filename='invoice_1.pdf'
    )
    return pdf_path

# Batch async generation
async def generate_many():
    jobs = [
        {
            'template': 'invoice.html',
            'data': {'id': i},
            'output': f'invoice_{i}.pdf'
        }
        for i in range(100)
    ]
    
    results = await service.batch_generate_async(jobs)
    
    for result in results:
        if result['success']:
            print(f"✓ {result['output_path']}")
        else:
            print(f"✗ {result['error']}")

# Run async code
asyncio.run(generate_many())
```

**Performance:**
- Sequential: 100 PDFs in ~20 seconds
- Async (4 workers): 100 PDFs in ~6 seconds
- Async (8 workers): 100 PDFs in ~4 seconds

---

### Pattern 3: Factory with Transformers

**Use when:** You need to transform raw data before PDF generation.

#### Step 1: Create Custom Transformer

```python
from pdf_patterns import DataTransformer
from typing import Dict, Any

class InvoiceTransformer(DataTransformer):
    """Transform order data to invoice format."""
    
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        # Get items from order
        items = raw_data.get('order_items', [])
        
        # Calculate totals
        subtotal = sum(
            item['price'] * item.get('quantity', 1) 
            for item in items
        )
        tax = subtotal * 0.08
        total = subtotal + tax
        
        # Return template-ready data
        return {
            'invoice_number': f"INV-{raw_data['order_id']:06d}",
            'date': raw_data.get('order_date'),
            'client_name': raw_data['customer']['name'],
            'client_address': raw_data['customer']['address'],
            'items': items,
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
```

#### Step 2: Use Factory

```python
from pdf_patterns import PDFFactory, PDFService

service = PDFService()
factory = PDFFactory(service)

# Register transformer
factory.register_transformer('invoice.html', InvoiceTransformer())

# Generate with automatic transformation
raw_order_data = {
    'order_id': 123,
    'order_date': '2024-03-25',
    'customer': {
        'name': 'Acme Corp',
        'address': '123 Business St'
    },
    'order_items': [
        {'name': 'Product A', 'price': 100, 'quantity': 2},
        {'name': 'Product B', 'price': 50, 'quantity': 1}
    ]
}

# Factory automatically transforms data
pdf = factory.create(
    template='invoice.html',
    raw_data=raw_order_data,  # Note: raw_data, not data
    output_filename='invoice_123.pdf'
)
```

#### Multiple Transformers

```python
class ReportTransformer(DataTransformer):
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        # Your transformation logic
        return transformed_data

class CertificateTransformer(DataTransformer):
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        # Your transformation logic
        return transformed_data

# Register all transformers
factory.register_transformer('invoice.html', InvoiceTransformer())
factory.register_transformer('report.html', ReportTransformer())
factory.register_transformer('certificate.html', CertificateTransformer())

# Use different templates with appropriate transformation
factory.create('invoice.html', order_data, 'invoice.pdf')
factory.create('report.html', report_data, 'report.pdf')
factory.create('certificate.html', cert_data, 'cert.pdf')
```

---

### Pattern 4: Builder Pattern

**Use when:** Building complex PDF jobs with many options.

```python
from pdf_patterns import PDFJobBuilder, PDFService

service = PDFService()

# Build job fluently
job = (PDFJobBuilder()
       .with_template('invoice.html')
       .with_data({
           'invoice_number': 'INV-001',
           'total': 1500
       })
       .with_output('invoice.pdf')
       .with_css('styles.css')
       .with_timestamp()  # Adds timestamp to filename
       .add_metadata('department', 'sales')
       .add_metadata('priority', 'high')
       .build())

# Generate from built job
pdf = service.generate(**job)

# Or build multiple jobs
builder = PDFJobBuilder()

jobs = []
for i in range(10):
    job = (builder
           .with_template('invoice.html')
           .with_data({'id': i})
           .with_output(f'invoice_{i}.pdf')
           .with_timestamp()
           .build())
    jobs.append(job)
    builder.reset()  # Reset for next job

# Batch generate
results = service.batch_generate(jobs)
```

**Builder Methods:**
- `with_template(str)` - Set template
- `with_data(dict)` - Set template data
- `with_output(str)` - Set output filename
- `with_css(str)` - Set CSS file
- `with_timestamp()` - Add timestamp to filename
- `add_metadata(key, value)` - Add custom metadata
- `validate()` - Validate builder state
- `build()` - Build job dictionary
- `reset()` - Reset builder

---

### Pattern 5: Service with Hooks

**Use when:** You need to trigger actions during PDF generation lifecycle.

```python
from pdf_patterns import PDFServiceWithHooks, PDFServiceConfig

config = PDFServiceConfig()
service = PDFServiceWithHooks(config)

# Register hooks
def on_start(context):
    """Called before generation."""
    print(f"Starting: {context['template']}")
    # Log to database, send notification, etc.

def on_complete(context):
    """Called after successful generation."""
    print(f"Completed: {context['output_path']}")
    print(f"Duration: {context['duration']:.2f}s")
    # Upload to S3, send email, update database, etc.

def on_failure(error, context):
    """Called on error."""
    print(f"Failed: {error}")
    # Log error, send alert, retry logic, etc.

def validate_data(context):
    """Called before generation for validation."""
    required_fields = ['invoice_number', 'total']
    for field in required_fields:
        if field not in context['data']:
            print(f"Missing field: {field}")
            return False
    return True

# Register all hooks
service.on_before_generate(on_start)
service.on_after_generate(on_complete)
service.on_error(on_failure)
service.on_validate(validate_data)

# Generate with hooks
try:
    pdf = service.generate(
        template='invoice.html',
        data={'invoice_number': 'INV-001', 'total': 100},
        output_filename='invoice.pdf'
    )
except Exception as e:
    print(f"Generation failed: {e}")
```

**Hook Types:**
- `on_before_generate(callback)` - Pre-generation
- `on_after_generate(callback)` - Post-generation (success)
- `on_error(callback)` - On error
- `on_validate(callback)` - Validation (must return bool)

**Context Dictionary:**
```python
{
    'template': 'invoice.html',
    'data': {...},
    'output_filename': 'invoice.pdf',
    'css_file': None,
    'start_time': 1234567890.0,
    'duration': 0.5,  # Only in after/error hooks
    'output_path': Path('output/invoice.pdf'),  # Only in after hook
    'success': True,  # Only in after hook
    'error': Exception(),  # Only in error hook
}
```

---

### Pattern 6: Storage Strategies

**Use when:** PDFs need to be stored in cloud storage (S3, etc.) or custom locations.

#### Local Storage

```python
from pdf_patterns import (
    PDFService,
    PDFServiceWithStorage,
    LocalStorageStrategy
)

service = PDFService()
storage = LocalStorageStrategy('output')
storage_service = PDFServiceWithStorage(service, storage)

# Generate and store
identifier = storage_service.generate_and_store(
    template='invoice.html',
    data={'id': 1},
    output_filename='invoice.pdf'
)

print(f"Stored at: {identifier}")  # Local path

# Retrieve
pdf_path = storage_service.retrieve(identifier)

# Delete
storage_service.delete(identifier)
```

#### S3 Storage

```python
from pdf_patterns import S3StorageStrategy

# Initialize S3 storage
s3_storage = S3StorageStrategy(
    bucket='my-pdf-bucket',
    prefix='invoices/',  # Optional prefix
    region='us-east-1'
)

service = PDFService()
storage_service = PDFServiceWithStorage(service, s3_storage)

# Generate and upload to S3
s3_key = storage_service.generate_and_store(
    template='invoice.html',
    data={'id': 1},
    output_filename='invoice.pdf',
    cleanup_local=True  # Delete local file after upload
)

print(f"Uploaded to S3: {s3_key}")
# Output: invoices/invoice.pdf

# Download from S3
pdf_path = storage_service.retrieve(s3_key)

# Delete from S3
storage_service.delete(s3_key)
```

#### Custom Storage Strategy

```python
from pdf_patterns import StorageStrategy
from pathlib import Path

class CustomStorageStrategy(StorageStrategy):
    """Example: Upload to your custom API."""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
    
    def save(self, pdf_path: Path) -> str:
        """Upload to custom API."""
        import requests
        
        with open(pdf_path, 'rb') as f:
            response = requests.post(
                f"{self.api_url}/upload",
                files={'file': f},
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        
        return response.json()['file_id']
    
    def retrieve(self, identifier: str) -> Path:
        """Download from custom API."""
        import requests
        
        response = requests.get(
            f"{self.api_url}/download/{identifier}",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        
        temp_path = Path(f'/tmp/{identifier}.pdf')
        temp_path.write_bytes(response.content)
        return temp_path
    
    def delete(self, identifier: str) -> bool:
        """Delete from custom API."""
        import requests
        
        response = requests.delete(
            f"{self.api_url}/delete/{identifier}",
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        
        return response.status_code == 200

# Use custom storage
custom_storage = CustomStorageStrategy(
    api_url='https://api.example.com',
    api_key='your-api-key'
)

storage_service = PDFServiceWithStorage(service, custom_storage)
file_id = storage_service.generate_and_store(
    'template.html',
    data,
    'output.pdf'
)
```

---

## Real-World Examples

### Example 1: Flask REST API

```python
from flask import Flask, request, send_file, jsonify
from pdf_patterns import PDFService, PDFServiceConfig

app = Flask(__name__)

# Initialize service once
config = PDFServiceConfig(
    templates_dir='templates',
    output_dir='output',
    max_workers=4
)
pdf_service = PDFService(config)

@app.route('/api/pdf/generate', methods=['POST'])
def generate_pdf():
    """
    Generate PDF from template.
    
    POST /api/pdf/generate
    {
        "template": "invoice.html",
        "data": {...},
        "filename": "invoice.pdf"
    }
    """
    try:
        payload = request.get_json()
        
        # Validate
        if not all(k in payload for k in ['template', 'data', 'filename']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate PDF
        output_path = pdf_service.generate(
            template=payload['template'],
            data=payload['data'],
            output_filename=payload['filename']
        )
        
        # Return file
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=payload['filename']
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/templates', methods=['GET'])
def list_templates():
    """List available templates."""
    templates = pdf_service.list_templates()
    return jsonify({'templates': templates})

if __name__ == '__main__':
    app.run(debug=True)
```

### Example 2: Celery Background Tasks

```python
from celery import Celery
from pdf_patterns import PDFService, PDFServiceConfig

celery = Celery('tasks', broker='redis://localhost:6379/0')

# Initialize service
config = PDFServiceConfig()
pdf_service = PDFService(config)

@celery.task(bind=True, max_retries=3)
def generate_pdf_task(self, template, data, filename):
    """
    Background PDF generation task.
    
    Usage:
        result = generate_pdf_task.delay(
            'invoice.html',
            {'id': 1},
            'invoice.pdf'
        )
        pdf_path = result.get(timeout=30)
    """
    try:
        output_path = pdf_service.generate(template, data, filename)
        return str(output_path)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@celery.task
def batch_generate_task(jobs):
    """Generate multiple PDFs in background."""
    return pdf_service.batch_generate(jobs)
```

### Example 3: Django Integration

```python
# services/pdf_service.py
from django.conf import settings
from pdf_patterns import PDFService, PDFServiceConfig

class DjangoPDFService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            config = PDFServiceConfig(
                templates_dir=settings.PDF_TEMPLATES_DIR,
                output_dir=settings.PDF_OUTPUT_DIR,
                max_workers=settings.PDF_MAX_WORKERS
            )
            cls._instance = PDFService(config)
        return cls._instance

# views.py
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services.pdf_service import DjangoPDFService

@api_view(['POST'])
def generate_invoice(request):
    """Generate invoice PDF."""
    service = DjangoPDFService.get_instance()
    
    invoice_data = request.data
    pdf_path = service.generate(
        template='invoice.html',
        data=invoice_data,
        output_filename=f"invoice_{invoice_data['id']}.pdf"
    )
    
    return FileResponse(
        open(pdf_path, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=pdf_path.name
    )
```

### Example 4: FastAPI with Async

```python
from fastapi import FastAPI, BackgroundTasks
from pdf_patterns import AsyncPDFService, PDFServiceConfig
from pydantic import BaseModel

app = FastAPI()

config = PDFServiceConfig(max_workers=8)
pdf_service = AsyncPDFService(config)

class PDFRequest(BaseModel):
    template: str
    data: dict
    filename: str

@app.post("/api/pdf/generate")
async def generate_pdf(request: PDFRequest):
    """Generate PDF asynchronously."""
    pdf_path = await pdf_service.generate_async(
        template=request.template,
        data=request.data,
        output_filename=request.filename
    )
    
    return {
        "status": "success",
        "path": str(pdf_path)
    }

@app.post("/api/pdf/batch")
async def batch_generate(jobs: list):
    """Generate multiple PDFs."""
    results = await pdf_service.batch_generate_async(jobs)
    return {
        "status": "success",
        "results": results
    }
```

---

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p templates output && chmod 777 output

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  pdf-service:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./templates:/app/templates:ro
      - ./output:/app/output
    environment:
      - PDF_TEMPLATES_DIR=/app/templates
      - PDF_OUTPUT_DIR=/app/output
      - PDF_MAX_WORKERS=4
      - PDF_LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

### Environment Variables

```bash
# .env file
PDF_TEMPLATES_DIR=/app/templates
PDF_OUTPUT_DIR=/app/output
PDF_STATIC_DIR=/app/static
PDF_MAX_WORKERS=4
PDF_TIMEOUT=30
PDF_ENABLE_CACHE=true
PDF_LOG_LEVEL=INFO
PDF_AUTO_CLEANUP=true
PDF_CLEANUP_AGE_DAYS=7

# AWS S3 (if using S3 storage)
PDF_USE_S3=true
PDF_S3_BUCKET=my-pdf-bucket
PDF_S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdf-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdf-service
  template:
    metadata:
      labels:
        app: pdf-service
    spec:
      containers:
      - name: pdf-service
        image: your-registry/pdf-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: PDF_TEMPLATES_DIR
          value: "/app/templates"
        - name: PDF_OUTPUT_DIR
          value: "/app/output"
        - name: PDF_MAX_WORKERS
          value: "4"
        volumeMounts:
        - name: templates
          mountPath: /app/templates
          readOnly: true
        - name: output
          mountPath: /app/output
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: templates
        configMap:
          name: pdf-templates
      - name: output
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: pdf-service
spec:
  selector:
    app: pdf-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Testing

### Unit Tests

```python
# tests/test_pdf_service.py
import pytest
from pathlib import Path
from pdf_patterns import PDFService, PDFServiceConfig

@pytest.fixture
def config(tmp_path):
    """Create temporary config."""
    return PDFServiceConfig(
        templates_dir=str(tmp_path / 'templates'),
        output_dir=str(tmp_path / 'output')
    )

@pytest.fixture
def service(config):
    """Create PDF service."""
    return PDFService(config)

@pytest.fixture
def simple_template(config):
    """Create a simple test template."""
    templates_dir = Path(config.templates_dir)
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    template_path = templates_dir / 'test.html'
    template_path.write_text('''
        <!DOCTYPE html>
        <html>
        <body><h1>{{ title }}</h1></body>
        </html>
    ''')
    return 'test.html'

def test_generate_pdf(service, simple_template):
    """Test basic PDF generation."""
    data = {'title': 'Test Document'}
    output = service.generate(simple_template, data, 'test.pdf')
    
    assert output.exists()
    assert output.suffix == '.pdf'
    assert output.stat().st_size > 0

def test_batch_generate(service, simple_template):
    """Test batch generation."""
    jobs = [
        {
            'template': simple_template,
            'data': {'title': f'Doc {i}'},
            'output': f'doc_{i}.pdf'
        }
        for i in range(5)
    ]
    
    results = service.batch_generate(jobs)
    
    assert len(results) == 5
    assert all(r['success'] for r in results)

def test_validate_template(service, simple_template):
    """Test template validation."""
    result = service.validate_template(simple_template)
    assert result['valid'] is True

def test_list_templates(service, simple_template):
    """Test listing templates."""
    templates = service.list_templates()
    assert simple_template in templates

def test_cleanup_old_files(service, simple_template):
    """Test file cleanup."""
    # Generate some PDFs
    for i in range(3):
        service.generate(simple_template, {'title': f'Doc {i}'}, f'old_{i}.pdf')
    
    # Cleanup (0 days = delete all)
    deleted = service.cleanup_old_files(days=0)
    assert deleted == 3
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
from pdf_patterns import (
    PDFService,
    PDFFactory,
    DataTransformer,
    PDFServiceConfig
)

class TestTransformer(DataTransformer):
    def transform(self, raw_data):
        return {'title': raw_data['name'].upper()}

def test_factory_with_transformer(tmp_path):
    """Test factory with data transformation."""
    # Setup
    config = PDFServiceConfig(
        templates_dir=str(tmp_path / 'templates'),
        output_dir=str(tmp_path / 'output')
    )
    
    # Create template
    templates_dir = Path(config.templates_dir)
    templates_dir.mkdir(parents=True)
    (templates_dir / 'test.html').write_text(
        '<html><body><h1>{{ title }}</h1></body></html>'
    )
    
    # Create factory with transformer
    service = PDFService(config)
    factory = PDFFactory(service)
    factory.register_transformer('test.html', TestTransformer())
    
    # Generate with transformation
    raw_data = {'name': 'test'}
    pdf = factory.create('test.html', raw_data, 'output.pdf')
    
    assert pdf.exists()

def test_async_service(tmp_path):
    """Test async service."""
    import asyncio
    from pdf_patterns import AsyncPDFService
    
    async def run_test():
        config = PDFServiceConfig(
            templates_dir=str(tmp_path / 'templates'),
            output_dir=str(tmp_path / 'output')
        )
        
        # Create template
        templates_dir = Path(config.templates_dir)
        templates_dir.mkdir(parents=True)
        (templates_dir / 'test.html').write_text(
            '<html><body><h1>{{ title }}</h1></body></html>'
        )
        
        service = AsyncPDFService(config)
        
        # Test async generation
        pdf = await service.generate_async(
            'test.html',
            {'title': 'Async Test'},
            'async_test.pdf'
        )
        
        assert pdf.exists()
    
    asyncio.run(run_test())
```

### Load Tests

```python
# tests/test_performance.py
import time
import pytest
from pdf_patterns import PDFService, AsyncPDFService, PDFServiceConfig

def test_sequential_performance(service, simple_template):
    """Test sequential generation performance."""
    start = time.time()
    
    for i in range(100):
        service.generate(
            simple_template,
            {'title': f'Doc {i}'},
            f'perf_{i}.pdf'
        )
    
    duration = time.time() - start
    print(f"\nSequential: 100 PDFs in {duration:.2f}s ({duration/100*1000:.0f}ms per PDF)")
    assert duration < 30  # Should complete in under 30s

def test_batch_performance(service, simple_template):
    """Test batch generation performance."""
    jobs = [
        {
            'template': simple_template,
            'data': {'title': f'Doc {i}'},
            'output': f'batch_{i}.pdf'
        }
        for i in range(100)
    ]
    
    start = time.time()
    results = service.batch_generate(jobs)
    duration = time.time() - start
    
    print(f"\nBatch: 100 PDFs in {duration:.2f}s ({duration/100*1000:.0f}ms per PDF)")
    assert all(r['success'] for r in results)
    assert duration < 25

@pytest.mark.asyncio
async def test_async_performance(tmp_path, simple_template):
    """Test async generation performance."""
    config = PDFServiceConfig(
        templates_dir=str(tmp_path / 'templates'),
        output_dir=str(tmp_path / 'output'),
        max_workers=8
    )
    
    service = AsyncPDFService(config)
    
    jobs = [
        {
            'template': simple_template,
            'data': {'title': f'Doc {i}'},
            'output': f'async_{i}.pdf'
        }
        for i in range(100)
    ]
    
    start = time.time()
    results = await service.batch_generate_async(jobs)
    duration = time.time() - start
    
    print(f"\nAsync: 100 PDFs in {duration:.2f}s ({duration/100*1000:.0f}ms per PDF)")
    assert len(results) == 100
    assert duration < 15  # Should be faster than batch
```

---

## Performance Guide

### Benchmarks

| Method | PDFs | Workers | Time | Per PDF |
|--------|------|---------|------|---------|
| Sequential | 100 | 1 | ~20s | 200ms |
| Batch | 100 | 1 | ~18s | 180ms |
| Async | 100 | 4 | ~6s | 60ms |
| Async | 100 | 8 | ~4s | 40ms |

### Optimization Tips

#### 1. Reuse Service Instance

```python
# ❌ Bad - Creates new instance each time
for i in range(100):
    service = PDFService()  # Don't do this!
    service.generate('template.html', data, f'out_{i}.pdf')

# ✅ Good - Reuse instance
service = PDFService()
for i in range(100):
    service.generate('template.html', data, f'out_{i}.pdf')
```

#### 2. Use Batch Processing

```python
# ❌ Slow - Sequential
for i in range(100):
    service.generate('template.html', data[i], f'out_{i}.pdf')

# ✅ Faster - Batch
jobs = [
    {'template': 'template.html', 'data': data[i], 'output': f'out_{i}.pdf'}
    for i in range(100)
]
service.batch_generate(jobs)
```

#### 3. Use Async for High Volume

```python
# ✅ Fastest - Async with multiple workers
service = AsyncPDFService(PDFServiceConfig(max_workers=8))
results = await service.batch_generate_async(jobs)
```

#### 4. Optimize Templates

```html
<!-- ❌ Slow - Complex CSS -->
<style>
    .item {
        background: linear-gradient(45deg, #fff, #eee);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 10px;
        transform: rotate(0deg);
    }
</style>

<!-- ✅ Fast - Simple CSS -->
<style>
    .item {
        background: #f5f5f5;
        border: 1px solid #ddd;
    }
</style>
```

#### 5. Enable Cleanup

```python
config = PDFServiceConfig(
    auto_cleanup=True,
    cleanup_age_days=7
)
service = PDFService(config)

# Manually cleanup old files
service.cleanup_old_files(days=7)
```

### Memory Management

```python
# For very large batches, process in chunks
def generate_large_batch(jobs, chunk_size=100):
    """Generate PDFs in chunks to manage memory."""
    service = PDFService()
    all_results = []
    
    for i in range(0, len(jobs), chunk_size):
        chunk = jobs[i:i + chunk_size]
        results = service.batch_generate(chunk)
        all_results.extend(results)
        
        # Optional: cleanup after each chunk
        service.cleanup_old_files(days=0)
    
    return all_results

# Process 1000 PDFs in chunks of 100
jobs = [...]  # 1000 jobs
results = generate_large_batch(jobs, chunk_size=100)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: WeasyPrint Installation Failed

**Error:**
```
OSError: cannot load library 'gobject-2.0-0'
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0

# macOS
brew install pango gdk-pixbuf

# Or use Docker
docker run -it python:3.11-slim
apt-get update && apt-get install -y libpango-1.0-0
```

#### Issue 2: Template Not Found

**Error:**
```
TemplateNotFound: invoice.html
```

**Solution:**
```python
# Check templates directory
service = PDFService(PDFServiceConfig(
    templates_dir='/absolute/path/to/templates'
))

# List available templates
print(service.list_templates())

# Verify template exists
from pathlib import Path
template_path = Path('templates/invoice.html')
print(f"Template exists: {template_path.exists()}")
```

#### Issue 3: CSS Not Loading

**Error:**
Styles not applied in PDF

**Solution:**
```python
# Option 1: Use inline CSS in template
# <style>/* CSS here */</style>

# Option 2: Specify static_dir and css_file
service = PDFService(PDFServiceConfig(
    templates_dir='templates',
    static_dir='assets'  # CSS files here
))

service.generate(
    'template.html',
    data,
    'output.pdf',
    css_file='styles.css'  # From assets/styles.css
)

# Option 3: Use base_url
manager.generate_pdf(
    'template.html',
    data,
    'output.pdf',
    base_url='file:///absolute/path/to/templates/'
)
```

#### Issue 4: Memory Errors with Large Batches

**Error:**
```
MemoryError: Unable to allocate memory
```

**Solution:**
```python
# Process in smaller chunks
def process_in_chunks(jobs, chunk_size=50):
    service = PDFService()
    results = []
    
    for i in range(0, len(jobs), chunk_size):
        chunk = jobs[i:i + chunk_size]
        chunk_results = service.batch_generate(chunk)
        results.extend(chunk_results)
        
        # Force garbage collection
        import gc
        gc.collect()
    
    return results

# Or use async with limited workers
config = PDFServiceConfig(max_workers=2)  # Reduce workers
service = AsyncPDFService(config)
```

#### Issue 5: Slow PDF Generation

**Problem:** PDFs taking too long to generate

**Solutions:**
```python
# 1. Simplify templates
# Remove complex CSS, large images, unnecessary elements

# 2. Use async service
service = AsyncPDFService(PDFServiceConfig(max_workers=8))

# 3. Optimize images
# Compress images before adding to templates
# Use appropriate resolution (72-150 DPI for PDFs)

# 4. Cache repeated data
# Store frequently used data in variables

# 5. Profile your templates
import time

start = time.time()
service.generate('template.html', data, 'output.pdf')
print(f"Generation took: {time.time() - start:.2f}s")
```

#### Issue 6: Font Issues

**Error:**
```
Font not found: 'CustomFont'
```

**Solution:**
```python
# Option 1: Use web-safe fonts
# <style>body { font-family: Arial, sans-serif; }</style>

# Option 2: Install fonts system-wide
# sudo apt-get install fonts-liberation

# Option 3: Use @font-face with local files
"""
<style>
@font-face {
    font-family: 'CustomFont';
    src: url('file:///path/to/font.ttf');
}
body { font-family: 'CustomFont', sans-serif; }
</style>
"""
```

### Debug Mode

```python
import logging

# Enable debug logging
config = PDFServiceConfig(log_level='DEBUG')
service = PDFService(config)

# Or set logging manually
logging.basicConfig(level=logging.DEBUG)

# Generate with detailed logs
service.generate('template.html', data, 'output.pdf')
```

### Getting Help

1. **Check logs:**
   ```python
   service.logger.setLevel(logging.DEBUG)
   ```

2. **Validate template:**
   ```python
   result = service.validate_template('your_template.html')
   if not result['valid']:
       print(result['error'])
   ```

3. **Preview HTML:**
   ```python
   # Check HTML before PDF conversion
   html = manager.render_template('template.html', data)
   print(html)
   
   # Or save as HTML file
   manager.preview_html('template.html', data, 'preview.html')
   ```

4. **Check template variables:**
   ```python
   required_vars = service.get_template_variables('template.html')
   print(f"Template needs: {required_vars}")
   
   # Verify your data has all variables
   missing = set(required_vars) - set(data.keys())
   if missing:
       print(f"Missing variables: {missing}")
   ```

---

## Best Practices

### 1. Configuration Management

```python
# ✅ Use environment-based config
config = PDFServiceConfig.from_env()

# ✅ Validate config at startup
assert Path(config.templates_dir).exists(), "Templates directory missing"
assert Path(config.output_dir).exists(), "Output directory missing"

# ✅ Use different configs for different environments
if os.getenv('ENV') == 'production':
    config = PDFServiceConfig(
        templates_dir='/app/templates',
        max_workers=8,
        auto_cleanup=True
    )
else:
    config = PDFServiceConfig(
        templates_dir='./templates',
        max_workers=2,
        log_level='DEBUG'
    )
```

### 2. Error Handling

```python
# ✅ Always use try-except
try:
    pdf = service.generate('template.html', data, 'output.pdf')
except Exception as e:
    logger.error(f"PDF generation failed: {e}")
    # Send alert, retry, or handle gracefully

# ✅ Use hooks for centralized error handling
def error_handler(error, context):
    logger.error(f"Error in {context['template']}: {error}")
    send_alert(error)

service = PDFServiceWithHooks()
service.on_error(error_handler)
```

### 3. Data Validation

```python
# ✅ Validate data before generation
def validate_invoice_data(data):
    required = ['invoice_number', 'client_name', 'items', 'total']
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    if not data['items']:
        raise ValueError("Invoice must have at least one item")
    
    return True

# Use with hooks
service.on_validate(lambda ctx: validate_invoice_data(ctx['data']))
```

### 4. Template Organization

```
templates/
├── invoices/
│   ├── standard_invoice.html
│   ├── premium_invoice.html
│   └── international_invoice.html
├── reports/
│   ├── monthly_report.html
│   └── annual_report.html
├── certificates/
│   └── completion_certificate.html
└── shared/
    ├── header.html
    ├── footer.html
    └── styles/
        ├── invoice.css
        └── report.css
```

### 5. Security

```python
# ✅ Sanitize user input
def sanitize_data(data):
    """Remove potentially dangerous content."""
    import html
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = html.escape(value)
        else:
            sanitized[key] = value
    
    return sanitized

# Use before generation
safe_data = sanitize_data(user_input)
pdf = service.generate('template.html', safe_data, 'output.pdf')

# ✅ Restrict template access
# Don't allow users to specify arbitrary template paths
ALLOWED_TEMPLATES = ['invoice.html', 'receipt.html', 'report.html']

if user_template not in ALLOWED_TEMPLATES:
    raise ValueError("Invalid template")
```

### 6. Monitoring

```python
# ✅ Track metrics
class MetricsCollector:
    def __init__(self):
        self.generated = 0
        self.failed = 0
        self.total_time = 0
    
    def on_success(self, context):
        self.generated += 1
        self.total_time += context['duration']
    
    def on_error(self, error, context):
        self.failed += 1
    
    def report(self):
        avg_time = self.total_time / self.generated if self.generated else 0
        print(f"Generated: {self.generated}")
        print(f"Failed: {self.failed}")
        print(f"Avg time: {avg_time:.2f}s")

metrics = MetricsCollector()
service.on_after_generate(metrics.on_success)
service.on_error(metrics.on_error)
```

---

## Summary

### Quick Reference Card

| Task | Use This |
|------|----------|
| Simple PDF generation | `PDFTemplateManager` |
| Production web app | `PDFService` (Singleton) |
| High volume (100+ PDFs) | `AsyncPDFService` |
| Data transformation | `PDFFactory` + Custom `DataTransformer` |
| Complex configuration | `PDFJobBuilder` |
| Event handling | `PDFServiceWithHooks` |
| Cloud storage | `PDFServiceWithStorage` + `S3StorageStrategy` |

### Cheat Sheet

```python
# Basic usage
from pdf_template_manager import PDFTemplateManager
manager = PDFTemplateManager()
pdf = manager.generate_pdf('template.html', data, 'output.pdf')

# Production usage
from pdf_patterns import PDFService, PDFServiceConfig
config = PDFServiceConfig.from_env()
service = PDFService(config)
pdf = service.generate('template.html', data, 'output.pdf')

# Async usage
from pdf_patterns import AsyncPDFService
service = AsyncPDFService(config)
pdf = await service.generate_async('template.html', data, 'output.pdf')

# With transformer
from pdf_patterns import PDFFactory, DataTransformer
factory = PDFFactory(service)
factory.register_transformer('template.html', MyTransformer())
pdf = factory.create('template.html', raw_data, 'output.pdf')

# With hooks
from pdf_patterns import PDFServiceWithHooks
service = PDFServiceWithHooks(config)
service.on_before_generate(lambda ctx: print("Starting..."))
service.on_after_generate(lambda ctx: print("Done!"))
pdf = service.generate('template.html', data, 'output.pdf')
```

---

**Complete documentation v1.0** | For issues: Check troubleshooting section or enable DEBUG logging