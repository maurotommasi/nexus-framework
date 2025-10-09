"""
Generic PDF Generation Service - Production Ready
Flexible, configurable patterns without hardcoded values
"""

import functools
import os
import asyncio
import logging
import time
import json
from pathlib import Path
from threading import Lock
from typing import Dict, Any, List, Optional, Callable, Union, Type
from functools import wraps
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import hashlib
import pickle
import sys

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)

from nexus.pdf.pdf_template_manager import PDFTemplateManager


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PDFServiceConfig:
    """Configuration for PDF service - fully customizable."""
    
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
    
    # Auto cleanup
    auto_cleanup: bool = False
    cleanup_age_days: int = 7
    
    @classmethod
    def from_env(cls) -> 'PDFServiceConfig':
        """Create config from environment variables."""
        return cls(
            templates_dir=os.getenv('PDF_TEMPLATES_DIR', 'templates'),
            output_dir=os.getenv('PDF_OUTPUT_DIR', 'output'),
            static_dir=os.getenv('PDF_STATIC_DIR'),
            max_workers=int(os.getenv('PDF_MAX_WORKERS', 4)),
            timeout=int(os.getenv('PDF_TIMEOUT', 30)),
            enable_cache=os.getenv('PDF_ENABLE_CACHE', 'true').lower() == 'true',
            log_level=os.getenv('PDF_LOG_LEVEL', 'INFO'),
            auto_cleanup=os.getenv('PDF_AUTO_CLEANUP', 'false').lower() == 'true',
            cleanup_age_days=int(os.getenv('PDF_CLEANUP_AGE_DAYS', 7))
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PDFServiceConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})


# ============================================================================
# PATTERN 1: SINGLETON SERVICE
# ============================================================================

class PDFService:
    """
    Thread-safe singleton PDF service.
    
    Features:
    - Lazy initialization
    - Thread-safe operations
    - Configurable via config object
    - Automatic resource management
    
    Usage:
        config = PDFServiceConfig(templates_dir='my_templates')
        service = PDFService(config)
        pdf_path = service.generate('template.html', data, 'output.pdf')
    """
    
    _instances: Dict[str, 'PDFService'] = {}
    _lock = Lock()
    
    def __new__(cls, config: Optional[PDFServiceConfig] = None):
        """Create or return existing instance based on config hash."""
        config = config or PDFServiceConfig()
        config_key = cls._get_config_key(config)
        
        if config_key not in cls._instances:
            with cls._lock:
                if config_key not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[config_key] = instance
                    instance._initialized = False
        
        return cls._instances[config_key]
    
    def __init__(self, config: Optional[PDFServiceConfig] = None):
        """Initialize service (only runs once per unique config)."""
        if self._initialized:
            return
        
        self.config = config or PDFServiceConfig()
        self._setup_logging()
        self.manager = PDFTemplateManager(
            templates_dir=self.config.templates_dir,
            output_dir=self.config.output_dir,
            static_dir=self.config.static_dir,
            auto_create_dirs=True
        )
        self._initialized = True
        self.logger.info(f"PDFService initialized with config: {self.config}")
    
    @staticmethod
    def _get_config_key(config: PDFServiceConfig) -> str:
        """Generate unique key from config."""
        return f"{config.templates_dir}_{config.output_dir}"
    
    def _setup_logging(self):
        """Setup logging based on config."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(self.config.log_format))
            self.logger.addHandler(handler)
    
    def generate(
        self,
        template: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None
    ) -> Path:
        """
        Generate PDF from template.
        
        Args:
            template: Template filename (e.g., 'invoice.html')
            data: Data dictionary for template
            output_filename: Output filename
            css_file: Optional CSS file from static directory
            
        Returns:
            Path to generated PDF
        """
        start_time = time.time()
        
        try:
            with self._lock:
                output_path = self.manager.generate_pdf(
                    template_name=template,
                    data=data,
                    output_filename=output_filename,
                    css_file=css_file
                )
            
            duration = time.time() - start_time
            self.logger.info(
                f"Generated PDF: {template} -> {output_filename} "
                f"({duration*1000:.0f}ms)"
            )
            
            return output_path
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(
                f"Failed to generate PDF: {template} ({duration*1000:.0f}ms) - {e}"
            )
            raise
    
    def batch_generate(
        self,
        jobs: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple PDFs.
        
        Args:
            jobs: List of dicts with keys: template, data, output, css_file (optional)
            continue_on_error: Continue processing if one job fails
            
        Returns:
            List of result dictionaries
        """
        return self.manager.batch_generate(jobs, continue_on_error)
    
    def list_templates(self) -> List[str]:
        """List all available templates."""
        return self.manager.list_templates()
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """Validate template syntax."""
        return self.manager.validate_template(template)
    
    def get_template_variables(self, template: str) -> List[str]:
        """Extract variables from template."""
        return self.manager.get_template_variables(template)
    
    def cleanup_old_files(self, days: Optional[int] = None) -> int:
        """
        Delete PDFs older than specified days.
        
        Args:
            days: Age threshold (uses config.cleanup_age_days if None)
            
        Returns:
            Number of files deleted
        """
        days = days or self.config.cleanup_age_days
        cutoff = datetime.now() - timedelta(days=days)
        output_path = Path(self.config.output_dir)
        
        deleted = 0
        for pdf_file in output_path.glob('*.pdf'):
            if datetime.fromtimestamp(pdf_file.stat().st_mtime) < cutoff:
                pdf_file.unlink()
                deleted += 1
        
        self.logger.info(f"Cleaned up {deleted} old PDF files")
        return deleted


# ============================================================================
# PATTERN 2: ASYNC SERVICE
# ============================================================================

class AsyncPDFService:
    """
    Async PDF service for high-volume generation.
    
    Features:
    - Process pool for parallel generation
    - Async/await interface
    - Configurable worker count
    - Non-blocking operations
    
    Usage:
        service = AsyncPDFService(config)
        pdf_path = await service.generate_async('template.html', data, 'output.pdf')
        
        # Batch
        results = await service.batch_generate_async(jobs)
    """
    
    def __init__(self, config: Optional[PDFServiceConfig] = None):
        """Initialize async service."""
        self.config = config or PDFServiceConfig()
        self.executor = ProcessPoolExecutor(max_workers=self.config.max_workers)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def generate_async(
        self,
        template: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None
    ) -> Path:
        """
        Generate PDF asynchronously.
        
        Args:
            template: Template filename
            data: Template data
            output_filename: Output filename
            css_file: Optional CSS file
            
        Returns:
            Path to generated PDF
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._generate_sync,
            template,
            data,
            output_filename,
            css_file
        )
    
    def _generate_sync(
        self,
        template: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str]
    ) -> Path:
        """Synchronous generation for executor."""
        manager = PDFTemplateManager(
            templates_dir=self.config.templates_dir,
            output_dir=self.config.output_dir,
            static_dir=self.config.static_dir
        )
        return manager.generate_pdf(template, data, output_filename, css_file)
    
    async def batch_generate_async(
        self,
        jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple PDFs concurrently.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of results
        """
        tasks = [
            self.generate_async(
                job['template'],
                job['data'],
                job['output'],
                job.get('css_file')
            )
            for job in jobs
        ]
        
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                output_path = await task
                results.append({
                    'job_index': i,
                    'success': True,
                    'output_path': str(output_path)
                })
            except Exception as e:
                results.append({
                    'job_index': i,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def __del__(self):
        """Cleanup executor on deletion."""
        self.executor.shutdown(wait=True)


# ============================================================================
# PATTERN 3: FACTORY WITH TRANSFORMERS
# ============================================================================

class DataTransformer:
    """
    Base class for data transformers.
    Extend this to create custom data preparation logic.
    """
    
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw data to template-ready format.
        
        Args:
            raw_data: Raw input data
            
        Returns:
            Transformed data ready for template
        """
        raise NotImplementedError


class PDFFactory:
    """
    Generic factory for PDF generation with pluggable transformers.
    
    Features:
    - Register custom transformers
    - Template-transformer mapping
    - Flexible data transformation pipeline
    - Fallback to passthrough if no transformer
    
    Usage:
        factory = PDFFactory(service)
        
        # Register transformer
        factory.register_transformer('invoice.html', InvoiceTransformer())
        
        # Generate with automatic transformation
        pdf = factory.create('invoice.html', raw_order_data, 'invoice.pdf')
    """
    
    def __init__(self, service: Union[PDFService, AsyncPDFService]):
        """Initialize factory with PDF service."""
        self.service = service
        self.transformers: Dict[str, DataTransformer] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def register_transformer(self, template: str, transformer: DataTransformer):
        """
        Register a data transformer for a template.
        
        Args:
            template: Template filename
            transformer: DataTransformer instance
        """
        self.transformers[template] = transformer
        self.logger.info(f"Registered transformer for {template}")
    
    def unregister_transformer(self, template: str):
        """Remove transformer for a template."""
        if template in self.transformers:
            del self.transformers[template]
            self.logger.info(f"Unregistered transformer for {template}")
    
    def create(
        self,
        template: str,
        raw_data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None,
        skip_transform: bool = False
    ) -> Path:
        """
        Create PDF with optional data transformation.
        
        Args:
            template: Template filename
            raw_data: Raw input data
            output_filename: Output filename
            css_file: Optional CSS file
            skip_transform: Skip transformation if True
            
        Returns:
            Path to generated PDF
        """
        # Transform data if transformer registered
        if not skip_transform and template in self.transformers:
            data = self.transformers[template].transform(raw_data)
            self.logger.debug(f"Data transformed for {template}")
        else:
            data = raw_data
        
        # Generate PDF
        return self.service.generate(template, data, output_filename, css_file)
    
    def create_batch(
        self,
        jobs: List[Dict[str, Any]],
        skip_transform: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Create multiple PDFs with transformation.
        
        Args:
            jobs: List of dicts with: template, raw_data, output, css_file (optional)
            skip_transform: Skip all transformations
            
        Returns:
            List of results
        """
        # Prepare jobs with transformation
        prepared_jobs = []
        for job in jobs:
            template = job['template']
            raw_data = job['raw_data']
            
            # Transform if transformer exists
            if not skip_transform and template in self.transformers:
                data = self.transformers[template].transform(raw_data)
            else:
                data = raw_data
            
            prepared_jobs.append({
                'template': template,
                'data': data,
                'output': job['output'],
                'css_file': job.get('css_file')
            })
        
        return self.service.batch_generate(prepared_jobs)


# ============================================================================
# PATTERN 4: BUILDER PATTERN
# ============================================================================

class PDFJobBuilder:
    """
    Builder for PDF generation jobs.
    
    Features:
    - Fluent interface
    - Validation before generation
    - Default value handling
    - Multiple output options
    
    Usage:
        job = (PDFJobBuilder()
               .with_template('invoice.html')
               .with_data(invoice_data)
               .with_output('invoice.pdf')
               .with_css('styles.css')
               .build())
        
        service.generate(**job)
    """
    
    def __init__(self):
        """Initialize empty builder."""
        self._template: Optional[str] = None
        self._data: Dict[str, Any] = {}
        self._output: Optional[str] = None
        self._css: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
    
    def with_template(self, template: str) -> 'PDFJobBuilder':
        """Set template filename."""
        self._template = template
        return self
    
    def with_data(self, data: Dict[str, Any]) -> 'PDFJobBuilder':
        """Set template data."""
        self._data = data
        return self
    
    def with_output(self, output_filename: str) -> 'PDFJobBuilder':
        """Set output filename."""
        self._output = output_filename
        return self
    
    def with_css(self, css_file: str) -> 'PDFJobBuilder':
        """Set CSS file."""
        self._css = css_file
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'PDFJobBuilder':
        """Add custom metadata."""
        self._metadata[key] = value
        return self
    
    def validate(self) -> bool:
        """
        Validate the job configuration.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        if not self._template:
            raise ValueError("Template is required")
        if not self._output:
            raise ValueError("Output filename is required")
        if not isinstance(self._data, dict):
            raise ValueError("Data must be a dictionary")
        return True
    
    def build(self) -> Dict[str, Any]:
        """
        Build the job dictionary.
        
        Returns:
            Job dictionary ready for service.generate()
        """
        self.validate()
        
        job = {
            'template': self._template,
            'data': self._data,
            'output_filename': self._output
        }
        
        if self._css:
            job['css_file'] = self._css
        
        # Add metadata to data if present
        if self._metadata:
            job['data']['_metadata'] = self._metadata
        
        return job
    
    def reset(self) -> 'PDFJobBuilder':
        """Reset builder to initial state."""
        self._template = None
        self._data = {}
        self._output = None
        self._css = None
        self._metadata = {}
        return self


# ============================================================================
# PATTERN 5: DECORATOR PATTERN
# ============================================================================

def with_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry PDF generation on failure.
    
    Args:
        max_attempts: Maximum retry attempts
        delay: Delay between retries (seconds)
    
    Usage:
        @with_retry(max_attempts=3, delay=2.0)
        def generate_critical_pdf(service, template, data, output):
            return service.generate(template, data, output)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        logging.warning(
                            f"Retry {attempt + 1}/{max_attempts} after error: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def with_timing(logger: Optional[logging.Logger] = None):
    """
    Decorator to measure PDF generation time.
    
    Args:
        logger: Logger for timing info
    
    Usage:
        @with_timing(logger)
        def generate_report(service, data):
            return service.generate('report.html', data, 'report.pdf')
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                
                if logger:
                    logger.info(f"{func.__name__} completed in {duration:.2f}s")
                else:
                    print(f"{func.__name__} completed in {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start
                
                if logger:
                    logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
                else:
                    print(f"{func.__name__} failed after {duration:.2f}s: {e}")
                
                raise
        
        return wrapper
    return decorator


def with_cache(cache_dir: str, ttl: int = 3600):
    """
    Cache decorator that stores results of function calls in a directory.
    cache_dir: directory to store cached files
    ttl: time-to-live in seconds
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

    def _ensure_parent_dir(path: Path):
        """Ensure the parent directory of the given path exists."""
        path.parent.mkdir(parents=True, exist_ok=True)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_str = f"{args}_{kwargs}"
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_file = cache_path / f"{key_hash}.pkl"

            # Check if cache exists and is valid
            if cache_file.exists():
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - mtime < timedelta(seconds=ttl):
                    # Load cached result
                    with open(cache_file, "rb") as f:
                        return pickle.load(f)

            # Call function
            result = func(*args, **kwargs)

            # Save result to cache
            _ensure_parent_dir(cache_file)
            with open(cache_file, "wb") as f:
                pickle.dump(result, f)

            return result

        return wrapper
    return decorator

# ============================================================================
# PATTERN 6: MIDDLEWARE/PIPELINE
# ============================================================================

class PDFMiddleware(ABC):
    """Abstract base class for PDF generation middleware."""
    
    @abstractmethod
    def process_before(
        self,
        template: str,
        data: Dict[str, Any],
        output: str,
        context: Dict[str, Any]
    ) -> tuple:
        """
        Process before PDF generation.
        
        Returns:
            Modified (template, data, output, context)
        """
        pass
    
    @abstractmethod
    def process_after(
        self,
        result: Path,
        context: Dict[str, Any]
    ) -> Path:
        """
        Process after PDF generation.
        
        Returns:
            Modified result path
        """
        pass


class ValidationMiddleware(PDFMiddleware):
    """Middleware for validating data before generation."""
    
    def __init__(self, required_fields: Optional[List[str]] = None):
        self.required_fields = required_fields or []
    
    def process_before(self, template, data, output, context):
        for field in self.required_fields:
            if field not in data:
                raise ValueError(f"Required field missing: {field}")
        return template, data, output, context
    
    def process_after(self, result, context):
        return result


class WatermarkMiddleware(PDFMiddleware):
    """Middleware for adding watermarks to PDFs."""
    
    def __init__(self, watermark_text: str = "DRAFT"):
        self.watermark_text = watermark_text
    
    def process_before(self, template, data, output, context):
        # Add watermark to data
        data['_watermark'] = self.watermark_text
        return template, data, output, context
    
    def process_after(self, result, context):
        # Could implement actual PDF watermarking here
        return result


class PDFPipeline:
    """
    Pipeline for PDF generation with middleware support.
    
    Features:
    - Chain multiple middleware
    - Pre/post processing hooks
    - Context passing between middleware
    - Error handling per middleware
    
    Usage:
        pipeline = PDFPipeline(service)
        pipeline.add_middleware(ValidationMiddleware(['customer_name']))
        pipeline.add_middleware(WatermarkMiddleware('DRAFT'))
        
        pdf = pipeline.generate('invoice.html', data, 'invoice.pdf')
    """
    
    def __init__(self, service: PDFService):
        """Initialize pipeline with service."""
        self.service = service
        self.middleware: List[PDFMiddleware] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def add_middleware(self, middleware: PDFMiddleware):
        """Add middleware to pipeline."""
        self.middleware.append(middleware)
        self.logger.info(f"Added middleware: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware_class: Type[PDFMiddleware]):
        """Remove middleware by class type."""
        self.middleware = [
            m for m in self.middleware
            if not isinstance(m, middleware_class)
        ]
    
    def generate(
        self,
        template: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None
    ) -> Path:
        """
        Generate PDF through middleware pipeline.
        
        Args:
            template: Template filename
            data: Template data
            output_filename: Output filename
            css_file: Optional CSS file
            
        Returns:
            Path to generated PDF
        """
        context = {'css_file': css_file}
        
        # Process before generation
        for middleware in self.middleware:
            try:
                template, data, output_filename, context = middleware.process_before(
                    template, data, output_filename, context
                )
            except Exception as e:
                self.logger.error(
                    f"Middleware {middleware.__class__.__name__} "
                    f"failed in process_before: {e}"
                )
                raise
        
        # Generate PDF
        result = self.service.generate(
            template,
            data,
            output_filename,
            context.get('css_file')
        )
        
        # Process after generation
        for middleware in reversed(self.middleware):
            try:
                result = middleware.process_after(result, context)
            except Exception as e:
                self.logger.error(
                    f"Middleware {middleware.__class__.__name__} "
                    f"failed in process_after: {e}"
                )
                raise
        
        return result


# ============================================================================
# PATTERN 7: STRATEGY PATTERN
# ============================================================================

class GenerationStrategy(ABC):
    """Abstract base class for PDF generation strategies."""
    
    @abstractmethod
    def generate(
        self,
        manager: PDFTemplateManager,
        template: str,
        data: Dict[str, Any],
        output: str,
        **kwargs
    ) -> Path:
        """Generate PDF using specific strategy."""
        pass


class StandardStrategy(GenerationStrategy):
    """Standard single PDF generation."""
    
    def generate(self, manager, template, data, output, **kwargs):
        return manager.generate_pdf(template, data, output, **kwargs)


class MergeStrategy(GenerationStrategy):
    """Generate multiple PDFs and merge them."""
    
    def __init__(self, templates: List[str]):
        self.templates = templates
    
    def generate(self, manager, template, data, output, **kwargs):
        # Generate individual PDFs
        temp_pdfs = []
        for i, tmpl in enumerate(self.templates):
            temp_output = f"temp_{i}_{output}"
            pdf = manager.generate_pdf(tmpl, data, temp_output, **kwargs)
            temp_pdfs.append(pdf)
        
        # Here you would merge PDFs (requires PyPDF2 or similar)
        # For now, return the first one
        return temp_pdfs[0]


class StrategyContext:
    """
    Context for PDF generation strategies.
    
    Usage:
        context = StrategyContext(service.manager)
        
        # Standard generation
        context.set_strategy(StandardStrategy())
        pdf = context.execute('invoice.html', data, 'invoice.pdf')
        
        # Merge multiple templates
        context.set_strategy(MergeStrategy(['page1.html', 'page2.html']))
        pdf = context.execute(None, data, 'merged.pdf')
    """
    
    def __init__(self, manager: PDFTemplateManager):
        """Initialize with PDF manager."""
        self.manager = manager
        self.strategy: Optional[GenerationStrategy] = None
    
    def set_strategy(self, strategy: GenerationStrategy):
        """Set the generation strategy."""
        self.strategy = strategy
    
    def execute(
        self,
        template: str,
        data: Dict[str, Any],
        output: str,
        **kwargs
    ) -> Path:
        """Execute current strategy."""
        if not self.strategy:
            raise ValueError("No strategy set")
        
        return self.strategy.generate(
            self.manager,
            template,
            data,
            output,
            **kwargs
        )


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_usage():
    """
    Comprehensive examples of all patterns.
    """
    
    # 1. Singleton Service
    config = PDFServiceConfig.from_env()
    service = PDFService(config)
    
    # Basic generation
    pdf = service.generate(
        'invoice.html',
        {'customer': 'John Doe', 'amount': 1000},
        'invoice.pdf'
    )
    
    # 2. Async Service
    async def async_example():
        async_service = AsyncPDFService(config)
        
        # Single async generation
        pdf = await async_service.generate_async(
            'report.html',
            {'title': 'Sales Report', 'data': []},
            'report.pdf'
        )
        
        # Batch async
        jobs = [
            {'template': 'invoice.html', 'data': {}, 'output': f'invoice_{i}.pdf'}
            for i in range(10)
        ]
        results = await async_service.batch_generate_async(jobs)
    
    # 3. Factory with Transformers
    class InvoiceTransformer(DataTransformer):
        def transform(self, raw_data):
            return {
                'customer_name': raw_data['customer']['name'],
                'total': sum(item['price'] for item in raw_data['items']),
                'date': datetime.now().strftime('%Y-%m-%d')
            }
    
    factory = PDFFactory(service)
    factory.register_transformer('invoice.html', InvoiceTransformer())
    
    raw_order = {
        'customer': {'name': 'Jane Smith'},
        'items': [{'price': 100}, {'price': 200}]
    }
    pdf = factory.create('invoice.html', raw_order, 'invoice.pdf')
    
    # 4. Builder Pattern
    job = (PDFJobBuilder()
           .with_template('report.html')
           .with_data({'title': 'Annual Report', 'year': 2024})
           .with_output('annual_report.pdf')
           .with_css('corporate.css')
           .add_metadata('author', 'System')
           .add_metadata('department', 'Finance')
           .build())
    
    pdf = service.generate(**job)
    
    # 5. Decorators
    @with_retry(max_attempts=3, delay=2.0)
    @with_timing(service.logger)
    @with_cache(cache_dir='.cache', ttl=3600)
    def generate_critical_report(data):
        return service.generate('critical.html', data, 'critical.pdf')
    
    pdf = generate_critical_report({'data': 'important'})
    
    # 6. Pipeline with Middleware
    pipeline = PDFPipeline(service)
    pipeline.add_middleware(ValidationMiddleware(['customer_name', 'invoice_number']))
    pipeline.add_middleware(WatermarkMiddleware('CONFIDENTIAL'))
    
    pdf = pipeline.generate(
        'invoice.html',
        {
            'customer_name': 'Acme Corp',
            'invoice_number': 'INV-001',
            'amount': 5000
        },
        'secured_invoice.pdf'
    )
    
    # 7. Strategy Pattern
    context = StrategyContext(service.manager)
    
    # Standard strategy
    context.set_strategy(StandardStrategy())
    pdf = context.execute('simple.html', {'text': 'Hello'}, 'simple.pdf')
    
    # Merge strategy
    context.set_strategy(MergeStrategy(['cover.html', 'content.html', 'appendix.html']))
    pdf = context.execute(None, {'title': 'Full Document'}, 'merged_document.pdf')


# ============================================================================
# ADVANCED PATTERNS
# ============================================================================

class PDFQueue:
    """
    Queue-based PDF generation with priority support.
    
    Features:
    - Priority queue for jobs
    - Background processing
    - Job status tracking
    - Callback support
    
    Usage:
        queue = PDFQueue(service)
        queue.start_workers(num_workers=4)
        
        job_id = queue.enqueue(
            template='invoice.html',
            data=invoice_data,
            output='invoice.pdf',
            priority=1,
            callback=lambda result: print(f"Generated: {result}")
        )
        
        status = queue.get_status(job_id)
    """
    
    def __init__(self, service: PDFService):
        """Initialize queue."""
        import queue
        import uuid
        from threading import Thread
        
        self.service = service
        self.job_queue = queue.PriorityQueue()
        self.results = {}
        self.workers = []
        self.running = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def start_workers(self, num_workers: int = 4):
        """Start background worker threads."""
        from threading import Thread
        
        self.running = True
        for i in range(num_workers):
            worker = Thread(target=self._worker, name=f"PDFWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"Started {num_workers} PDF workers")
    
    def stop_workers(self):
        """Stop all workers."""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        self.workers.clear()
        self.logger.info("Stopped all PDF workers")
    
    def _worker(self):
        """Worker thread function."""
        while self.running:
            try:
                priority, job_id, job_data = self.job_queue.get(timeout=1)
                
                self.results[job_id] = {'status': 'processing'}
                
                try:
                    result = self.service.generate(
                        job_data['template'],
                        job_data['data'],
                        job_data['output'],
                        job_data.get('css_file')
                    )
                    
                    self.results[job_id] = {
                        'status': 'completed',
                        'result': result,
                        'timestamp': datetime.now()
                    }
                    
                    # Execute callback if provided
                    if 'callback' in job_data and job_data['callback']:
                        job_data['callback'](result)
                        
                except Exception as e:
                    self.results[job_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': datetime.now()
                    }
                    
                self.job_queue.task_done()
                
            except:
                continue
    
    def enqueue(
        self,
        template: str,
        data: Dict[str, Any],
        output: str,
        priority: int = 5,
        css_file: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Add job to queue.
        
        Args:
            template: Template filename
            data: Template data
            output: Output filename
            priority: Job priority (lower = higher priority)
            css_file: Optional CSS file
            callback: Function to call on completion
            
        Returns:
            Job ID for tracking
        """
        import uuid
        
        job_id = str(uuid.uuid4())
        job_data = {
            'template': template,
            'data': data,
            'output': output,
            'css_file': css_file,
            'callback': callback
        }
        
        self.job_queue.put((priority, job_id, job_data))
        self.results[job_id] = {'status': 'queued'}
        
        self.logger.info(f"Enqueued job {job_id} with priority {priority}")
        return job_id
    
    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status."""
        return self.results.get(job_id, {'status': 'not_found'})
    
    def wait_for_completion(self, job_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Wait for job to complete."""
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_status(job_id)
            if status['status'] in ['completed', 'failed']:
                return status
            time.sleep(0.5)
        
        return {'status': 'timeout'}


class PDFCache:
    """
    Intelligent caching system for PDFs.
    
    Features:
    - LRU cache with size limits
    - TTL support
    - Hash-based cache keys
    - Automatic cleanup
    
    Usage:
        cache = PDFCache(max_size=100, ttl=3600)
        
        # Check cache
        cached_pdf = cache.get(template, data)
        if cached_pdf:
            return cached_pdf
        
        # Generate and cache
        pdf = service.generate(template, data, output)
        cache.put(template, data, pdf)
    """
    
    def __init__(
        self,
        cache_dir: str = '.pdf_cache',
        max_size: int = 100,
        ttl: int = 3600
    ):
        """Initialize cache."""
        from collections import OrderedDict
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size = max_size
        self.ttl = ttl
        self.cache_index: OrderedDict = OrderedDict()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self._load_index()
    
    def _get_cache_key(self, template: str, data: Dict[str, Any]) -> str:
        """Generate cache key from template and data."""
        key_data = {'template': template, 'data': data}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _load_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / 'index.json'
        if index_file.exists():
            try:
                with open(index_file) as f:
                    index_data = json.load(f)
                    self.cache_index = OrderedDict(index_data)
            except:
                self.cache_index = OrderedDict()
    
    def _save_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dir / 'index.json'
        with open(index_file, 'w') as f:
            json.dump(dict(self.cache_index), f)
    
    def get(self, template: str, data: Dict[str, Any]) -> Optional[Path]:
        """
        Get cached PDF if exists and valid.
        
        Returns:
            Path to cached PDF or None
        """
        cache_key = self._get_cache_key(template, data)
        
        if cache_key in self.cache_index:
            entry = self.cache_index[cache_key]
            cache_file = self.cache_dir / f"{cache_key}.pdf"
            
            # Check if file exists and not expired
            if cache_file.exists():
                age = time.time() - entry['timestamp']
                if age < self.ttl:
                    # Move to end (LRU)
                    self.cache_index.move_to_end(cache_key)
                    self.logger.debug(f"Cache hit for {cache_key}")
                    return cache_file
            
            # Remove expired entry
            del self.cache_index[cache_key]
            if cache_file.exists():
                cache_file.unlink()
        
        self.logger.debug(f"Cache miss for {cache_key}")
        return None
    
    def put(self, template: str, data: Dict[str, Any], pdf_path: Path):
        """
        Add PDF to cache.
        
        Args:
            template: Template used
            data: Data used
            pdf_path: Path to generated PDF
        """
        import shutil
        
        cache_key = self._get_cache_key(template, data)
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        
        # Copy PDF to cache
        shutil.copy2(pdf_path, cache_file)
        
        # Update index
        self.cache_index[cache_key] = {
            'template': template,
            'timestamp': time.time(),
            'size': cache_file.stat().st_size
        }
        
        # Enforce size limit
        while len(self.cache_index) > self.max_size:
            oldest_key = next(iter(self.cache_index))
            del self.cache_index[oldest_key]
            old_file = self.cache_dir / f"{oldest_key}.pdf"
            if old_file.exists():
                old_file.unlink()
        
        self._save_index()
        self.logger.debug(f"Cached PDF as {cache_key}")
    
    def clear(self):
        """Clear entire cache."""
        for pdf_file in self.cache_dir.glob('*.pdf'):
            pdf_file.unlink()
        
        self.cache_index.clear()
        self._save_index()
        self.logger.info("Cleared PDF cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(
            (self.cache_dir / f"{key}.pdf").stat().st_size
            for key in self.cache_index
            if (self.cache_dir / f"{key}.pdf").exists()
        )
        
        return {
            'entries': len(self.cache_index),
            'total_size_mb': total_size / (1024 * 1024),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl
        }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Example usage and testing.
    """
    
    # Load configuration
    config = PDFServiceConfig.from_env()
    
    # Initialize service
    service = PDFService(config)
    
    # Example: Generate a simple PDF
    test_data = {
        'title': 'Test Document',
        'content': 'This is a test PDF generation.',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    try:
        # Ensure templates directory exists
        Path(config.templates_dir).mkdir(exist_ok=True)
        
        # Create a simple template if it doesn't exist
        template_path = Path(config.templates_dir) / 'test.html'
        if not template_path.exists():
            template_path.write_text('''
            <!DOCTYPE html>
            <html>
            <head><title>{{ title }}</title></head>
            <body>
                <h1>{{ title }}</h1>
                <p>{{ content }}</p>
                <footer>Generated on {{ date }}</footer>
            </body>
            </html>
            ''')
        
        # Generate PDF
        output_path = service.generate(
            'test.html',
            test_data,
            'test_output.pdf'
        )
        
        print(f"✅ PDF generated successfully: {output_path}")
        
        # Demonstrate other patterns
        print("\n📋 Available templates:", service.list_templates())
        print("🔍 Template variables:", service.get_template_variables('test.html'))
        
        # Builder pattern example
        job = (PDFJobBuilder()
               .with_template('test.html')
               .with_data(test_data)
               .with_output('builder_test.pdf')
               .build())
        
        output_path = service.generate(**job)
        print(f"✅ Builder pattern PDF: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()