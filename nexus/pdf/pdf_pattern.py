"""
Generic PDF Generation Service - Production Ready
Flexible, configurable patterns without hardcoded values
"""

import os
import asyncio
import logging
import time
import json
from pathlib import Path
from threading import Lock
from typing import Dict, Any, List, Optional, Callable, Union
from functools import wraps
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from dataclasses import dataclass, field

# Assume PDFTemplateManager is imported
from pdf_template_manager import PDFTemplateManager


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
        """Add custom metadata.