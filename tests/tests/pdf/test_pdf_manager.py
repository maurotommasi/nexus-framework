"""
Comprehensive Test Suite for PDF Generation Service and Template Manager
Tests cover all patterns, edge cases, and production scenarios
"""

import unittest
import asyncio
import tempfile
import shutil
import time
import json
import threading
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import concurrent.futures
import os
import sys
import logging
import re

# Add the root directory (3 levels up) to Python path
root_dir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.insert(0, root_dir)


# Import the modules to test - use absolute imports
from nexus.pdf.pdf_template_manager import PDFTemplateManager
from nexus.pdf.pdf_pattern import (
    PDFServiceConfig, PDFService, AsyncPDFService,
    DataTransformer, PDFFactory, PDFJobBuilder,
    ValidationMiddleware, WatermarkMiddleware, PDFPipeline,
    StandardStrategy, MergeStrategy, StrategyContext,
    PDFQueue, PDFCache, PDFMiddleware, 
    with_retry, with_timing, with_cache
)


# ============================================================================
# TEST FIXTURES AND HELPERS
# ============================================================================

class TestBase(unittest.TestCase):
    """Base test class with common setup/teardown."""
    
    def setUp(self):
        """Create temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.templates_dir = Path(self.temp_dir) / 'templates'
        self.output_dir = Path(self.temp_dir) / 'output'
        self.static_dir = Path(self.temp_dir) / 'static'
        
        # Create directories
        self.templates_dir.mkdir(parents=True)
        self.output_dir.mkdir(parents=True)
        self.static_dir.mkdir(parents=True)
        
        # Create test templates
        self._create_test_templates()
        
        # Create test config
        self.config = PDFServiceConfig(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir),
            static_dir=str(self.static_dir),
            max_workers=2,
            timeout=10
        )
    
    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_templates(self):
        """Create test HTML templates."""
        # Simple template
        simple_template = """
        <!DOCTYPE html>
        <html>
        <head><title>{{ title }}</title></head>
        <body>
            <h1>{{ title }}</h1>
            <p>{{ content }}</p>
        </body>
        </html>
        """
        (self.templates_dir / 'simple.html').write_text(simple_template)
        
        # Invoice template
        invoice_template = """
        <!DOCTYPE html>
        <html>
        <head><title>Invoice {{ invoice_number }}</title></head>
        <body>
            <h1>Invoice #{{ invoice_number }}</h1>
            <p>Customer: {{ customer_name }}</p>
            <p>Amount: {{ amount | currency }}</p>
            <p>Date: {{ date | date_format }}</p>
        </body>
        </html>
        """
        (self.templates_dir / 'invoice.html').write_text(invoice_template)
        
        # Report template with variables
        report_template = """
        <!DOCTYPE html>
        <html>
        <head><title>{{ report_title }}</title></head>
        <body>
            <h1>{{ report_title }}</h1>
            <p>Generated: {{ now() }}</p>
            {% for item in items %}
                <div>{{ item.name }}: {{ item.value }}</div>
            {% endfor %}
            <p>Total: {{ sum_field(items, 'value') }}</p>
        </body>
        </html>
        """
        (self.templates_dir / 'report.html').write_text(report_template)
        
        # CSS file
        css_content = """
        body { font-family: Arial, sans-serif; }
        h1 { color: #333; }
        """
        (self.static_dir / 'styles.css').write_text(css_content)


# ============================================================================
# PDF TEMPLATE MANAGER TESTS (Tests 1-20)
# ============================================================================

class TestPDFTemplateManager(TestBase):
    """Test suite for PDFTemplateManager class."""
    
    def test_01_initialization(self):
        """Test manager initialization with directories."""
        manager = PDFTemplateManager(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir),
            static_dir=str(self.static_dir),
            auto_create_dirs=True
        )
        
        self.assertTrue(self.templates_dir.exists())
        self.assertTrue(self.output_dir.exists())
        self.assertTrue(self.static_dir.exists())
        self.assertIsNotNone(manager.env)
    
    def test_02_list_templates(self):
        """Test listing available templates."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        templates = manager.list_templates()
        
        self.assertIn('simple.html', templates)
        self.assertIn('invoice.html', templates)
        self.assertIn('report.html', templates)
        self.assertEqual(len(templates), 3)
    
    def test_03_validate_valid_template(self):
        """Test validation of valid template."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        result = manager.validate_template('simple.html')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['template'], 'simple.html')
        self.assertIn('message', result)
    
    def test_04_validate_invalid_template(self):
        """Test validation of non-existent template."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        result = manager.validate_template('nonexistent.html')
        
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
    
    def test_05_render_template(self):
        """Test template rendering with data."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        html = manager.render_template('simple.html', {
            'title': 'Test Title',
            'content': 'Test Content'
        })
        
        self.assertIn('Test Title', html)
        self.assertIn('Test Content', html)
        self.assertIn('<h1>Test Title</h1>', html)
    
    def test_06_custom_filters(self):
        """Test custom Jinja2 filters."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        html = manager.render_template('invoice.html', {
            'invoice_number': '12345',
            'customer_name': 'John Doe',
            'amount': 1500.50,
            'date': '2024-01-15'
        })
        
        self.assertIn('$1,500.50', html)  # Currency filter
        self.assertIn('2024-01-15', html)  # Date filter
    
    def test_07_global_functions(self):
        """Test global template functions."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        html = manager.render_template('report.html', {
            'report_title': 'Test Report',
            'items': [
                {'name': 'Item1', 'value': 100},
                {'name': 'Item2', 'value': 200}
            ]
        })
        
        self.assertIn('Test Report', html)
        self.assertIn('Item1: 100', html)
        self.assertIn('Total: 300', html)  # sum_field function
    
    @patch('nexus.pdf.pdf_template_manager.pisa')
    def test_08_generate_pdf(self, mock_pisa):
        """Test PDF generation from template."""
        manager = PDFTemplateManager(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir)
        )
        
        mock_pisa.CreatePDF.return_value.err = False
        
        output = manager.generate_pdf(
            'simple.html',
            {'title': 'Test', 'content': 'Content'},
            'test.pdf'
        )
        
        self.assertEqual(output, self.output_dir / 'test.pdf')
        mock_pisa.CreatePDF.assert_called_once()
    
    @patch('nexus.pdf.pdf_template_manager.pisa')
    def test_09_generate_pdf_with_css(self, mock_pisa):
        """Test PDF generation with CSS file."""
        manager = PDFTemplateManager(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir),
            static_dir=str(self.static_dir)
        )
        
        mock_pisa.CreatePDF.return_value.err = False
        
        output = manager.generate_pdf(
            'simple.html',
            {'title': 'Test', 'content': 'Content'},
            'test.pdf',
            css_file='styles.css'
        )
        
        self.assertEqual(output, self.output_dir / 'test.pdf')
        mock_pisa.CreatePDF.assert_called_once()
    
    @patch('nexus.pdf.pdf_template_manager.pisa')
    def test_10_batch_generate(self, mock_pisa):
        """Test batch PDF generation."""
        manager = PDFTemplateManager(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir)
        )
        
        mock_pisa.CreatePDF.return_value.err = False
        
        jobs = [
            {
                'template': 'simple.html',
                'data': {'title': 'Test1', 'content': 'Content1'},
                'output': 'test1.pdf'
            },
            {
                'template': 'invoice.html',
                'data': {'invoice_number': '001', 'customer_name': 'John', 'amount': 100, 'date': '2024-01-01'},
                'output': 'invoice1.pdf'
            }
        ]
        
        results = manager.batch_generate(jobs)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['success'] for r in results))
        self.assertEqual(mock_pisa.CreatePDF.call_count, 2)
    
    @patch('nexus.pdf.pdf_template_manager.pisa')
    def test_11_batch_generate_with_error(self, mock_pisa):
        """Test batch generation with error handling."""
        manager = PDFTemplateManager(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir)
        )
        
        # Make first call succeed, second fail
        mock_status1 = MagicMock()
        mock_status1.err = False
        mock_status2 = MagicMock()
        mock_status2.err = True
        
        mock_pisa.CreatePDF.side_effect = [mock_status1, Exception("PDF generation failed")]
        
        jobs = [
            {'template': 'simple.html', 'data': {}, 'output': 'test1.pdf'},
            {'template': 'invalid.html', 'data': {}, 'output': 'test2.pdf'}
        ]
        
        results = manager.batch_generate(jobs, continue_on_error=True)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]['success'])
        self.assertFalse(results[1]['success'])
        self.assertIn('error', results[1])
    
    def test_12_preview_html(self):
        """Test HTML preview generation."""
        manager = PDFTemplateManager(
            templates_dir=str(self.templates_dir),
            output_dir=str(self.output_dir)
        )
        
        output = manager.preview_html(
            'simple.html',
            {'title': 'Preview', 'content': 'Test'},
            'preview.html'
        )
        
        self.assertTrue(output.exists())
        html_content = output.read_text()
        self.assertIn('Preview', html_content)
        self.assertIn('Test', html_content)
    
    def test_13_create_template_from_string(self):
        """Test creating template from string."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        
        template_content = "<html><body>{{ message }}</body></html>"
        template_path = manager.create_template_from_string(
            'custom.html',
            template_content
        )
        
        self.assertTrue(template_path.exists())
        self.assertEqual(template_path.read_text(), template_content)
        self.assertIn('custom.html', manager.list_templates())
    
    def test_16_currency_filter_edge_cases(self):
        """Test currency filter with edge cases."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        
        # Test with None
        html = manager.render_template('invoice.html', {
            'invoice_number': '001',
            'customer_name': 'Test',
            'amount': None,
            'date': '2024-01-01'
        })
        self.assertIn('None', html)
        
        # Test with string
        html = manager.render_template('invoice.html', {
            'invoice_number': '001',
            'customer_name': 'Test',
            'amount': 'invalid',
            'date': '2024-01-01'
        })
        self.assertIn('invalid', html)
    
    def test_17_date_format_filter_variations(self):
        """Test date format filter with different inputs."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        
        # Test with datetime object
        html = manager.render_template('invoice.html', {
            'invoice_number': '001',
            'customer_name': 'Test',
            'amount': 100,
            'date': datetime(2024, 1, 15)
        })
        self.assertIn('2024-01-15', html)
        
        # Test with invalid date string
        html = manager.render_template('invoice.html', {
            'invoice_number': '001',
            'customer_name': 'Test',
            'amount': 100,
            'date': 'not-a-date'
        })
        self.assertIn('not-a-date', html)
    
    def test_18_percentage_filter(self):
        """Test percentage filter functionality."""
        # Create template with percentage filter
        template_content = "<html><body>{{ value | percentage }}</body></html>"
        (self.templates_dir / 'percent.html').write_text(template_content)
        
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        html = manager.render_template('percent.html', {'value': 25.5})
        
        self.assertIn('25.50%', html)
    
    def test_19_truncate_words_filter(self):
        """Test truncate words filter."""
        template_content = "<html><body>{{ text | truncate_words(5) }}</body></html>"
        (self.templates_dir / 'truncate.html').write_text(template_content)
        
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        html = manager.render_template('truncate.html', {
            'text': 'This is a very long text that should be truncated'
        })
        
        self.assertIn('This is a very long...', html)
        self.assertNotIn('truncated', html)
    
    def test_20_template_with_empty_data(self):
        """Test rendering template with empty data dictionary."""
        manager = PDFTemplateManager(templates_dir=str(self.templates_dir))
        
        # Should not raise error
        html = manager.render_template('simple.html', {})
        self.assertIn('<html>', html)
        self.assertIn('</html>', html)


# ============================================================================
# PDF SERVICE CONFIGURATION TESTS (Tests 21-25)
# ============================================================================

class TestPDFServiceConfig(TestBase):
    """Test suite for PDFServiceConfig."""
    
    def test_21_config_defaults(self):
        """Test default configuration values."""
        config = PDFServiceConfig()
        
        self.assertEqual(config.templates_dir, 'templates')
        self.assertEqual(config.output_dir, 'output')
        self.assertIsNone(config.static_dir)
        self.assertEqual(config.max_workers, 4)
        self.assertEqual(config.timeout, 30)
        self.assertTrue(config.enable_cache)
        self.assertEqual(config.log_level, 'INFO')
        self.assertFalse(config.auto_cleanup)
        self.assertEqual(config.cleanup_age_days, 7)
    
    @patch.dict('os.environ', {
        'PDF_TEMPLATES_DIR': 'custom_templates',
        'PDF_OUTPUT_DIR': 'custom_output',
        'PDF_MAX_WORKERS': '8',
        'PDF_ENABLE_CACHE': 'false'
    })
    def test_22_config_from_env(self):
        """Test configuration from environment variables."""
        config = PDFServiceConfig.from_env()
        
        self.assertEqual(config.templates_dir, 'custom_templates')
        self.assertEqual(config.output_dir, 'custom_output')
        self.assertEqual(config.max_workers, 8)
        self.assertFalse(config.enable_cache)
    
    def test_23_config_from_dict(self):
        """Test configuration from dictionary."""
        config_dict = {
            'templates_dir': 'dict_templates',
            'output_dir': 'dict_output',
            'max_workers': 6,
            'enable_cache': False,
            'extra_field': 'ignored'  # Should be ignored
        }
        
        config = PDFServiceConfig.from_dict(config_dict)
        
        self.assertEqual(config.templates_dir, 'dict_templates')
        self.assertEqual(config.output_dir, 'dict_output')
        self.assertEqual(config.max_workers, 6)
        self.assertFalse(config.enable_cache)
        self.assertFalse(hasattr(config, 'extra_field'))
    
    def test_24_config_equality(self):
        """Test configuration equality comparison."""
        config1 = PDFServiceConfig(templates_dir='test', max_workers=2)
        config2 = PDFServiceConfig(templates_dir='test', max_workers=2)
        config3 = PDFServiceConfig(templates_dir='other', max_workers=2)
        
        # Configs with same values should generate same key
        from nexus.pdf.pdf_pattern import PDFService
        key1 = PDFService._get_config_key(config1)
        key2 = PDFService._get_config_key(config2)
        key3 = PDFService._get_config_key(config3)
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)
    
    def test_25_config_log_format(self):
        """Test custom log format configuration."""
        custom_format = '%(levelname)s - %(message)s'
        config = PDFServiceConfig(log_format=custom_format)
        
        self.assertEqual(config.log_format, custom_format)


# ============================================================================
# PDF SERVICE SINGLETON TESTS (Tests 26-35)
# ============================================================================

class TestPDFService(TestBase):
    """Test suite for PDFService singleton pattern."""
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_26_singleton_pattern(self, mock_manager):
        """Test singleton pattern implementation."""
        service1 = PDFService(self.config)
        service2 = PDFService(self.config)
        
        self.assertIs(service1, service2)
        # Manager should only be created once
        mock_manager.assert_called_once()
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_27_different_configs_different_instances(self, mock_manager):
        """Test different configs create different instances."""
        config1 = PDFServiceConfig(templates_dir='dir1')
        config2 = PDFServiceConfig(templates_dir='dir2')
        
        service1 = PDFService(config1)
        service2 = PDFService(config2)
        
        self.assertIsNot(service1, service2)
        self.assertEqual(mock_manager.call_count, 2)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_28_thread_safe_initialization(self, mock_manager):
        """Test thread-safe singleton initialization."""
        services = []
        
        def create_service():
            services.append(PDFService(self.config))
        
        threads = [threading.Thread(target=create_service) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be the same instance
        self.assertTrue(all(s is services[0] for s in services))
        # Manager should only be created once
        mock_manager.assert_called_once()
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_29_generate_pdf(self, mock_manager):
        """Test PDF generation through service."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        result = service.generate(
            'template.html',
            {'data': 'test'},
            'output.pdf'
        )
        
        self.assertEqual(result, Path('test.pdf'))
        mock_instance.generate_pdf.assert_called_once_with(
            template_name='template.html',
            data={'data': 'test'},
            output_filename='output.pdf',
            css_file=None
        )
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_30_generate_with_css(self, mock_manager):
        """Test PDF generation with CSS file."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        result = service.generate(
            'template.html',
            {'data': 'test'},
            'output.pdf',
            css_file='styles.css'
        )
        
        mock_instance.generate_pdf.assert_called_once_with(
            template_name='template.html',
            data={'data': 'test'},
            output_filename='output.pdf',
            css_file='styles.css'
        )
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_31_batch_generate(self, mock_manager):
        """Test batch PDF generation."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.batch_generate.return_value = [
            {'success': True, 'output_path': 'file1.pdf'},
            {'success': True, 'output_path': 'file2.pdf'}
        ]
        
        service = PDFService(self.config)
        jobs = [
            {'template': 't1.html', 'data': {}, 'output': 'f1.pdf'},
            {'template': 't2.html', 'data': {}, 'output': 'f2.pdf'}
        ]
        
        results = service.batch_generate(jobs)
        
        self.assertEqual(len(results), 2)
        mock_instance.batch_generate.assert_called_once()
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_32_list_templates(self, mock_manager):
        """Test listing templates through service."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.list_templates.return_value = ['t1.html', 't2.html']
        
        service = PDFService(self.config)
        templates = service.list_templates()
        
        self.assertEqual(templates, ['t1.html', 't2.html'])
        mock_instance.list_templates.assert_called_once()
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_33_cleanup_old_files(self, mock_manager):
        """Test cleanup of old PDF files."""
        # Create old and new PDF files
        old_file = self.output_dir / 'old.pdf'
        new_file = self.output_dir / 'new.pdf'
        
        old_file.touch()
        new_file.touch()
        
        # Make old file older
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days old
        os.utime(old_file, (old_time, old_time))
        
        service = PDFService(self.config)
        deleted = service.cleanup_old_files(days=7)
        
        self.assertEqual(deleted, 1)
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.exists())
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_34_generate_with_exception(self, mock_manager):
        """Test PDF generation with exception handling."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.side_effect = Exception("Generation failed")
        
        service = PDFService(self.config)
        
        with self.assertRaises(Exception) as context:
            service.generate('template.html', {}, 'output.pdf')
        
        self.assertIn("Generation failed", str(context.exception))
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_35_service_logging(self, mock_manager):
        """Test service logging configuration."""
        config = PDFServiceConfig(log_level='DEBUG')
        service = PDFService(config)
        
        self.assertEqual(service.logger.level, logging.DEBUG)
        self.assertTrue(len(service.logger.handlers) > 0)


# ============================================================================
# ASYNC SERVICE TESTS (Tests 36-40)
# ============================================================================

class TestAsyncPDFService(TestBase):
    """Test suite for AsyncPDFService."""
    
    def test_36_async_initialization(self):
        """Test async service initialization."""
        service = AsyncPDFService(self.config)
        
        self.assertIsNotNone(service.executor)
        self.assertEqual(service.config.max_workers, 2)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    async def test_37_generate_async(self, mock_manager):
        """Test async PDF generation."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = AsyncPDFService(self.config)
        result = await service.generate_async(
            'template.html',
            {'data': 'test'},
            'output.pdf'
        )
        
        self.assertEqual(result, Path('test.pdf'))
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    async def test_38_batch_generate_async(self, mock_manager):
        """Test async batch generation."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = AsyncPDFService(self.config)
        jobs = [
            {'template': f't{i}.html', 'data': {}, 'output': f'f{i}.pdf'}
            for i in range(3)
        ]
        
        results = await service.batch_generate_async(jobs)
        
        self.assertEqual(len(results), 3)
        success_count = sum(1 for r in results if r['success'])
        self.assertEqual(success_count, 3)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    async def test_39_async_error_handling(self, mock_manager):
        """Test async error handling."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        
        # Make second call fail
        mock_instance.generate_pdf.side_effect = [
            Path('test1.pdf'),
            Exception("Failed"),
            Path('test3.pdf')
        ]
        
        service = AsyncPDFService(self.config)
        jobs = [
            {'template': f't{i}.html', 'data': {}, 'output': f'f{i}.pdf'}
            for i in range(3)
        ]
        
        results = await service.batch_generate_async(jobs)
        
        success_count = sum(1 for r in results if r['success'])
        self.assertEqual(success_count, 2)
        
        fail_count = sum(1 for r in results if not r['success'])
        self.assertEqual(fail_count, 1)
    
    def test_40_executor_cleanup(self):
        """Test executor cleanup on deletion."""
        service = AsyncPDFService(self.config)
        executor = service.executor
        
        # Trigger cleanup
        del service
        
        # Executor should be shut down
        with self.assertRaises(RuntimeError):
            executor.submit(lambda: None)


# ============================================================================
# FACTORY AND TRANSFORMER TESTS (Tests 41-45)
# ============================================================================

class TestPDFFactory(TestBase):
    """Test suite for PDFFactory and DataTransformer."""
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_41_factory_initialization(self, mock_manager):
        """Test factory initialization."""
        service = PDFService(self.config)
        factory = PDFFactory(service)
        
        self.assertEqual(factory.service, service)
        self.assertEqual(len(factory.transformers), 0)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_42_register_transformer(self, mock_manager):
        """Test registering data transformer."""
        service = PDFService(self.config)
        factory = PDFFactory(service)
        
        class TestTransformer(DataTransformer):
            def transform(self, raw_data):
                return {'transformed': True, **raw_data}
        
        transformer = TestTransformer()
        factory.register_transformer('test.html', transformer)
        
        self.assertIn('test.html', factory.transformers)
        self.assertEqual(factory.transformers['test.html'], transformer)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_43_create_with_transformation(self, mock_manager):
        """Test PDF creation with data transformation."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        factory = PDFFactory(service)
        
        class InvoiceTransformer(DataTransformer):
            def transform(self, raw_data):
                return {
                    'invoice_number': raw_data['order_id'],
                    'total': sum(item['price'] for item in raw_data['items'])
                }
        
        factory.register_transformer('invoice.html', InvoiceTransformer())
        
        raw_data = {
            'order_id': 'ORD-001',
            'items': [{'price': 100}, {'price': 200}]
        }
        
        result = factory.create('invoice.html', raw_data, 'invoice.pdf')
        
        # Check that transformation was applied
        call_args = mock_instance.generate_pdf.call_args
        transformed_data = call_args[1]['data']
        self.assertEqual(transformed_data['invoice_number'], 'ORD-001')
        self.assertEqual(transformed_data['total'], 300)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_44_create_without_transformer(self, mock_manager):
        """Test PDF creation without transformer (passthrough)."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        factory = PDFFactory(service)
        
        raw_data = {'data': 'unchanged'}
        result = factory.create('template.html', raw_data, 'output.pdf')
        
        # Data should pass through unchanged
        call_args = mock_instance.generate_pdf.call_args
        self.assertEqual(call_args[1]['data'], raw_data)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_45_batch_create_with_transformers(self, mock_manager):
        """Test batch creation with mixed transformers."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.batch_generate.return_value = [
            {'success': True, 'output_path': 'file1.pdf'},
            {'success': True, 'output_path': 'file2.pdf'}
        ]
        
        service = PDFService(self.config)
        factory = PDFFactory(service)
        
        class UpperTransformer(DataTransformer):
            def transform(self, raw_data):
                return {k: v.upper() if isinstance(v, str) else v 
                       for k, v in raw_data.items()}
        
        factory.register_transformer('upper.html', UpperTransformer())
        
        jobs = [
            {'template': 'upper.html', 'raw_data': {'text': 'hello'}, 'output': 'f1.pdf'},
            {'template': 'normal.html', 'raw_data': {'text': 'world'}, 'output': 'f2.pdf'}
        ]
        
        results = factory.create_batch(jobs)
        
        # Check transformation was applied to first job
        call_args = mock_instance.batch_generate.call_args
        prepared_jobs = call_args[0][0]
        self.assertEqual(prepared_jobs[0]['data']['text'], 'HELLO')
        self.assertEqual(prepared_jobs[1]['data']['text'], 'world')


# ============================================================================
# BUILDER PATTERN TESTS (Tests 46-50)
# ============================================================================

class TestPDFJobBuilder(TestBase):
    """Test suite for PDFJobBuilder."""
    
    def test_46_builder_initialization(self):
        """Test builder initialization."""
        builder = PDFJobBuilder()
        
        self.assertIsNone(builder._template)
        self.assertEqual(builder._data, {})
        self.assertIsNone(builder._output)
        self.assertIsNone(builder._css)
        self.assertEqual(builder._metadata, {})
    
    def test_47_fluent_interface(self):
        """Test fluent interface chaining."""
        builder = PDFJobBuilder()
        
        result = (builder
                 .with_template('template.html')
                 .with_data({'key': 'value'})
                 .with_output('output.pdf')
                 .with_css('styles.css')
                 .add_metadata('author', 'Test'))
        
        self.assertIs(result, builder)
        self.assertEqual(builder._template, 'template.html')
        self.assertEqual(builder._data, {'key': 'value'})
        self.assertEqual(builder._output, 'output.pdf')
        self.assertEqual(builder._css, 'styles.css')
        self.assertEqual(builder._metadata['author'], 'Test')
    
    def test_48_build_valid_job(self):
        """Test building valid job dictionary."""
        job = (PDFJobBuilder()
               .with_template('invoice.html')
               .with_data({'invoice_number': '001'})
               .with_output('invoice.pdf')
               .with_css('styles.css')
               .add_metadata('created_by', 'System')
               .build())
        
        self.assertEqual(job['template'], 'invoice.html')
        self.assertEqual(job['data']['invoice_number'], '001')
        self.assertEqual(job['data']['_metadata']['created_by'], 'System')
        self.assertEqual(job['output_filename'], 'invoice.pdf')
        self.assertEqual(job['css_file'], 'styles.css')
    
    def test_49_validation_errors(self):
        """Test validation of incomplete jobs."""
        builder = PDFJobBuilder()
        
        # Missing template
        with self.assertRaises(ValueError) as context:
            builder.with_data({'test': 'data'}).with_output('out.pdf').build()
        self.assertIn("Template is required", str(context.exception))
        
        # Missing output
        builder.reset()
        with self.assertRaises(ValueError) as context:
            builder.with_template('t.html').with_data({'test': 'data'}).build()
        self.assertIn("Output filename is required", str(context.exception))
        
        # Invalid data type
        builder.reset()
        with self.assertRaises(ValueError) as context:
            builder.with_template('t.html').with_data("not a dict").with_output('out.pdf').build()
        self.assertIn("Data must be a dictionary", str(context.exception))
    
    def test_50_builder_reset(self):
        """Test resetting builder to initial state."""
        builder = (PDFJobBuilder()
                  .with_template('template.html')
                  .with_data({'key': 'value'})
                  .with_output('output.pdf'))
        
        builder.reset()
        
        self.assertIsNone(builder._template)
        self.assertEqual(builder._data, {})
        self.assertIsNone(builder._output)
        self.assertIsNone(builder._css)
        self.assertEqual(builder._metadata, {})


# ============================================================================
# DECORATOR PATTERN TESTS (Tests 51-55)
# ============================================================================

class TestDecorators(TestBase):
    """Test suite for decorator patterns."""
    
    def test_51_retry_decorator_success(self):
        """Test retry decorator with successful execution."""
        call_count = 0
        
        @with_retry(max_attempts=3, delay=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "Success"
        
        result = flaky_function()
        
        self.assertEqual(result, "Success")
        self.assertEqual(call_count, 2)
    
    def test_52_retry_decorator_failure(self):
        """Test retry decorator with all attempts failing."""
        call_count = 0
        
        @with_retry(max_attempts=3, delay=0.1)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception(f"Failure {call_count}")
        
        with self.assertRaises(Exception) as context:
            always_fails()
        
        self.assertEqual(call_count, 3)
        self.assertIn("Failure 3", str(context.exception))
    
    def test_53_timing_decorator(self):
        """Test timing decorator."""
        logger = Mock()
        
        @with_timing(logger)
        def timed_function():
            time.sleep(0.1)
            return "Done"
        
        result = timed_function()
        
        self.assertEqual(result, "Done")
        logger.info.assert_called_once()
        call_args = logger.info.call_args[0][0]
        self.assertIn("timed_function completed", call_args)
    
    def test_54_timing_decorator_with_exception(self):
        """Test timing decorator with exception."""
        logger = Mock()
        
        @with_timing(logger)
        def failing_function():
            time.sleep(0.1)
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_function()
        
        logger.error.assert_called_once()
        call_args = logger.error.call_args[0][0]
        self.assertIn("failing_function failed", call_args)
        self.assertIn("Test error", call_args)
    
    def test_55_cache_decorator(self):
        """Test cache decorator."""
        cache_dir = Path(self.temp_dir) / 'cache'
        call_count = 0
        
        @with_cache(cache_dir=str(cache_dir), ttl=60)
        def cached_function(value):
            nonlocal call_count
            call_count += 1
            return Path(f"result_{value}.pdf")
        
        # First call
        result1 = cached_function("test")
        self.assertEqual(call_count, 1)
        
        # Second call (should use cache)
        result2 = cached_function("test")
        self.assertEqual(call_count, 1)  # Not incremented
        
        # Different argument (should not use cache)
        result3 = cached_function("other")
        self.assertEqual(call_count, 2)


# ============================================================================
# MIDDLEWARE/PIPELINE TESTS (Tests 56-60)
# ============================================================================

class TestPDFPipeline(TestBase):
    """Test suite for PDFPipeline and Middleware."""
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_56_pipeline_initialization(self, mock_manager):
        """Test pipeline initialization."""
        service = PDFService(self.config)
        pipeline = PDFPipeline(service)
        
        self.assertEqual(pipeline.service, service)
        self.assertEqual(len(pipeline.middleware), 0)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_57_add_middleware(self, mock_manager):
        """Test adding middleware to pipeline."""
        service = PDFService(self.config)
        pipeline = PDFPipeline(service)
        
        validation = ValidationMiddleware(['field1', 'field2'])
        watermark = WatermarkMiddleware('DRAFT')
        
        pipeline.add_middleware(validation)
        pipeline.add_middleware(watermark)
        
        self.assertEqual(len(pipeline.middleware), 2)
        self.assertIsInstance(pipeline.middleware[0], ValidationMiddleware)
        self.assertIsInstance(pipeline.middleware[1], WatermarkMiddleware)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_58_validation_middleware(self, mock_manager):
        """Test validation middleware functionality."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        pipeline = PDFPipeline(service)
        pipeline.add_middleware(ValidationMiddleware(['required_field']))
        
        # Should fail without required field
        with self.assertRaises(ValueError) as context:
            pipeline.generate('template.html', {}, 'output.pdf')
        self.assertIn("Required field missing: required_field", str(context.exception))
        
        # Should succeed with required field
        result = pipeline.generate(
            'template.html',
            {'required_field': 'value'},
            'output.pdf'
        )
        self.assertEqual(result, Path('test.pdf'))
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_59_watermark_middleware(self, mock_manager):
        """Test watermark middleware functionality."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        pipeline = PDFPipeline(service)
        pipeline.add_middleware(WatermarkMiddleware('CONFIDENTIAL'))
        
        pipeline.generate('template.html', {'data': 'test'}, 'output.pdf')
        
        # Check that watermark was added to data
        call_args = mock_instance.generate_pdf.call_args
        self.assertEqual(call_args[1]['data']['_watermark'], 'CONFIDENTIAL')
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_60_middleware_order(self, mock_manager):
        """Test middleware execution order."""
        service = PDFService(self.config)
        pipeline = PDFPipeline(service)
        
        execution_order = []
        
        class OrderTestMiddleware1(PDFMiddleware):
            def process_before(self, template, data, output, context):
                execution_order.append('before1')
                return template, data, output, context
            
            def process_after(self, result, context):
                execution_order.append('after1')
                return result
        
        class OrderTestMiddleware2(PDFMiddleware):
            def process_before(self, template, data, output, context):
                execution_order.append('before2')
                return template, data, output, context
            
            def process_after(self, result, context):
                execution_order.append('after2')
                return result
        
        pipeline.add_middleware(OrderTestMiddleware1())
        pipeline.add_middleware(OrderTestMiddleware2())
        
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        pipeline.generate('template.html', {}, 'output.pdf')
        
        # Before: 1 then 2, After: 2 then 1 (reversed)
        self.assertEqual(execution_order, ['before1', 'before2', 'after2', 'after1'])


# ============================================================================
# ADDITIONAL ADVANCED TESTS (Tests 61-70)
# ============================================================================

class TestAdvancedFeatures(TestBase):
    """Test suite for advanced features."""
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_61_strategy_pattern(self, mock_manager):
        """Test strategy pattern implementation."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        context = StrategyContext(mock_instance)
        
        # Test standard strategy
        context.set_strategy(StandardStrategy())
        result = context.execute('template.html', {'data': 'test'}, 'output.pdf')
        
        self.assertEqual(result, Path('test.pdf'))
        mock_instance.generate_pdf.assert_called_once()
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_62_merge_strategy(self, mock_manager):
        """Test merge strategy for multiple templates."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        context = StrategyContext(mock_instance)
        context.set_strategy(MergeStrategy(['page1.html', 'page2.html']))
        
        result = context.execute(None, {'data': 'test'}, 'merged.pdf')
        
        # Should generate multiple PDFs
        self.assertEqual(mock_instance.generate_pdf.call_count, 2)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_63_pdf_queue_initialization(self, mock_manager):
        """Test PDF queue initialization."""
        service = PDFService(self.config)
        queue = PDFQueue(service)
        
        self.assertEqual(queue.service, service)
        self.assertFalse(queue.running)
        self.assertEqual(len(queue.workers), 0)
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_64_pdf_queue_enqueue_and_status(self, mock_manager):
        """Test enqueueing jobs and checking status."""
        service = PDFService(self.config)
        queue = PDFQueue(service)
        
        job_id = queue.enqueue(
            'template.html',
            {'data': 'test'},
            'output.pdf',
            priority=1
        )
        
        self.assertIsNotNone(job_id)
        
        status = queue.get_status(job_id)
        self.assertEqual(status['status'], 'queued')
    
    @patch('nexus.pdf.pdf_pattern.PDFTemplateManager')
    def test_65_pdf_queue_worker_processing(self, mock_manager):
        """Test queue worker processing."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance
        mock_instance.generate_pdf.return_value = Path('test.pdf')
        
        service = PDFService(self.config)
        queue = PDFQueue(service)
        
        queue.start_workers(num_workers=2)
        self.assertTrue(queue.running)
        self.assertEqual(len(queue.workers), 2)
        
        job_id = queue.enqueue('template.html', {'data': 'test'}, 'output.pdf')
        
        # Wait for processing
        result = queue.wait_for_completion(job_id, timeout=5)
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['result'], Path('test.pdf'))
        
        queue.stop_workers()
        self.assertFalse(queue.running)
    
    def test_66_pdf_cache_initialization(self):
        """Test PDF cache initialization."""
        cache_dir = Path(self.temp_dir) / 'pdf_cache'
        cache = PDFCache(cache_dir=str(cache_dir), max_size=10, ttl=3600)
        
        self.assertTrue(cache_dir.exists())
        self.assertEqual(cache.max_size, 10)
        self.assertEqual(cache.ttl, 3600)
    
    def test_67_pdf_cache_get_put(self):
        """Test cache get and put operations."""
        cache_dir = Path(self.temp_dir) / 'pdf_cache'
        cache = PDFCache(cache_dir=str(cache_dir), max_size=10, ttl=3600)
        
        # Create a test PDF
        test_pdf = self.output_dir / 'test.pdf'
        test_pdf.write_bytes(b'PDF content')
        
        # Put in cache
        cache.put('template.html', {'data': 'test'}, test_pdf)
        
        # Get from cache
        cached = cache.get('template.html', {'data': 'test'})
        self.assertIsNotNone(cached)
        self.assertTrue(cached.exists())
        
        # Different data should not hit cache
        not_cached = cache.get('template.html', {'data': 'different'})
        self.assertIsNone(not_cached)
    
    def test_68_pdf_cache_expiration(self):
        """Test cache expiration based on TTL."""
        cache_dir = Path(self.temp_dir) / 'pdf_cache'
        cache = PDFCache(cache_dir=str(cache_dir), max_size=10, ttl=1)  # 1 second TTL
        
        test_pdf = self.output_dir / 'test.pdf'
        test_pdf.write_bytes(b'PDF content')
        
        cache.put('template.html', {'data': 'test'}, test_pdf)
        
        # Should exist immediately
        self.assertIsNotNone(cache.get('template.html', {'data': 'test'}))
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        self.assertIsNone(cache.get('template.html', {'data': 'test'}))
    
    def test_69_pdf_cache_size_limit(self):
        """Test cache size limit enforcement."""
        cache_dir = Path(self.temp_dir) / 'pdf_cache'
        cache = PDFCache(cache_dir=str(cache_dir), max_size=3, ttl=3600)
        
        test_pdf = self.output_dir / 'test.pdf'
        test_pdf.write_bytes(b'PDF content')
        
        # Add more than max_size items
        for i in range(5):
            cache.put('template.html', {'data': f'test{i}'}, test_pdf)
        
        # Cache should only have max_size items
        stats = cache.get_stats()
        self.assertLessEqual(stats['entries'], 3)
        
        # Oldest items should be evicted
        self.assertIsNone(cache.get('template.html', {'data': 'test0'}))
        self.assertIsNone(cache.get('template.html', {'data': 'test1'}))
        self.assertIsNotNone(cache.get('template.html', {'data': 'test4'}))
    
    def test_70_pdf_cache_clear(self):
        """Test clearing entire cache."""
        cache_dir = Path(self.temp_dir) / 'pdf_cache'
        cache = PDFCache(cache_dir=str(cache_dir))
        
        test_pdf = self.output_dir / 'test.pdf'
        test_pdf.write_bytes(b'PDF content')
        
        # Add items to cache
        for i in range(3):
            cache.put('template.html', {'data': f'test{i}'}, test_pdf)
        
        stats_before = cache.get_stats()
        self.assertEqual(stats_before['entries'], 3)
        
        # Clear cache
        cache.clear()
        
        stats_after = cache.get_stats()
        self.assertEqual(stats_after['entries'], 0)
        
        # All items should be gone
        for i in range(3):
            self.assertIsNone(cache.get('template.html', {'data': f'test{i}'}))


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_tests():
    """Run all tests with detailed output."""
    import logging
    
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPDFTemplateManager,
        TestPDFServiceConfig,
        TestPDFService,
        TestAsyncPDFService,
        TestPDFFactory,
        TestPDFJobBuilder,
        TestDecorators,
        TestPDFPipeline,
        TestAdvancedFeatures
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)