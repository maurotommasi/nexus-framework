import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import re

# Import playwright for browser-based PDF generation
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    raise ImportError("Please install playwright: pip install playwright && playwright install chromium")


def _ensure_parent_dir(path: Path):
    """Ensure the parent directory of the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


class PDFTemplateManager:
    """
    Manages PDF generation from HTML templates with dynamic data injection.
    Uses Jinja2 + Playwright for browser-based PDF generation (matches print preview exactly).
    """

    def __init__(
        self,
        templates_dir: str = 'templates',
        output_dir: str = 'output',
        static_dir: Optional[str] = None,
        auto_create_dirs: bool = True
    ):
        self.auto_create_dirs = auto_create_dirs
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.static_dir = Path(static_dir) if static_dir else self.templates_dir / 'static'

        if self.auto_create_dirs:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.static_dir.mkdir(parents=True, exist_ok=True)
        else:
            if not self.templates_dir.exists():
                raise FileNotFoundError(f"Templates directory does not exist: {self.templates_dir}")
            if not self.output_dir.exists():
                raise FileNotFoundError(f"Output directory does not exist: {self.output_dir}")
            if not self.static_dir.exists():
                raise FileNotFoundError(f"Static directory does not exist: {self.static_dir}")

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        self._register_custom_filters()
        self._register_global_functions()

        # Setup logger
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _register_custom_filters(self):
        """Register custom Jinja2 filters for templates."""

        def currency(value, symbol='$'):
            try:
                return f"{symbol}{float(value):,.2f}"
            except (ValueError, TypeError):
                return value

        def date_format(value, format_str='%Y-%m-%d'):
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            if isinstance(value, datetime):
                return value.strftime(format_str)
            return value

        def percentage(value, decimals=2):
            try:
                return f"{float(value):.{decimals}f}%"
            except (ValueError, TypeError):
                return value

        def truncate_words(value, length=50):
            words = str(value).split()
            if len(words) <= length:
                return value
            return ' '.join(words[:length]) + '...'

        self.env.filters['currency'] = currency
        self.env.filters['date_format'] = date_format
        self.env.filters['percentage'] = percentage
        self.env.filters['truncate_words'] = truncate_words

    def _register_global_functions(self):
        def now(format_str='%Y-%m-%d %H:%M:%S'):
            return datetime.now().strftime(format_str)

        def range_list(start, end, step=1):
            return list(range(start, end, step))

        def sum_field(items, field):
            return sum(item.get(field, 0) for item in items)

        self.env.globals['now'] = now
        self.env.globals['range'] = range_list
        self.env.globals['sum_field'] = sum_field

    def list_templates(self) -> List[str]:
        return [f.name for f in self.templates_dir.glob('*.html') if f.is_file()]

    def validate_template(self, template_name: str) -> Dict[str, Any]:
        try:
            template = self.env.get_template(template_name)
            template.render({})
            return {"valid": True, "template": template_name, "message": "Template is valid"}
        except Exception as e:
            return {"valid": False, "template": template_name, "error": str(e)}

    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        template = self.env.get_template(template_name)
        return template.render(**data)

    def generate_pdf(
        self,
        template_name: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None,
        base_url: Optional[str] = None,
        pdf_options: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate PDF using Playwright (Chromium browser engine).
        Produces output identical to Chrome's print preview.
        
        Args:
            template_name: Name of the HTML template
            data: Data to inject into template
            output_filename: Output PDF filename
            css_file: Optional CSS file (kept for API compatibility, not used)
            base_url: Base URL for resolving relative paths (optional)
            pdf_options: Additional PDF options (format, margins, etc.)
        """
        html_content = self.render_template(template_name, data)
        output_path = self.output_dir / output_filename
        _ensure_parent_dir(output_path)

        self.logger.info(f"Generating PDF with Playwright: {output_path}")

        # Default PDF options
        default_options = {
            'format': 'A4',
            'print_background': True,
            'margin': {
                'top': '0.5in',
                'right': '0.5in',
                'bottom': '0.5in',
                'left': '0.5in'
            }
        }
        
        if pdf_options:
            default_options.update(pdf_options)

        # Generate PDF using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Set content with base URL for relative paths
            if base_url:
                page.goto(base_url)
            
            page.set_content(html_content, wait_until='networkidle')
            
            # Generate PDF
            page.pdf(path=str(output_path), **default_options)
            
            browser.close()

        return output_path

    def batch_generate(
        self,
        jobs: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple PDFs in batch.
        
        Args:
            jobs: List of job dictionaries with keys: template, data, output, css_file (optional), pdf_options (optional)
            continue_on_error: Continue processing if a job fails
            
        Returns:
            List of result dictionaries with success status and output path or error
        """
        results = []
        for i, job in enumerate(jobs):
            try:
                output_path = self.generate_pdf(
                    template_name=job['template'],
                    data=job['data'],
                    output_filename=job['output'],
                    css_file=job.get('css_file'),
                    pdf_options=job.get('pdf_options')
                )
                results.append({"job_index": i, "success": True, "output_path": str(output_path)})
            except Exception as e:
                self.logger.error(f"Job {i} failed: {str(e)}")
                results.append({"job_index": i, "success": False, "error": str(e)})
                if not continue_on_error:
                    break
        return results

    def preview_html(self, template_name: str, data: Dict[str, Any], output_filename: str = 'preview.html') -> Path:
        """
        Generate HTML preview of template with data.
        Useful for debugging templates before generating PDFs.
        """
        html_content = self.render_template(template_name, data)
        output_path = self.output_dir / output_filename
        _ensure_parent_dir(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path

    def create_template_from_string(self, template_name: str, html_content: str) -> Path:
        """
        Create a new template file from HTML string.
        """
        template_path = self.templates_dir / template_name
        _ensure_parent_dir(template_path)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return template_path

    def get_template_variables(self, template_name: str) -> List[str]:
        """Extract variable names from template source (leaf variables only)."""
        source, _, _ = self.env.loader.get_source(self.env, template_name)
        matches = re.findall(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)", source)
        variables = set(match.split('.')[-1] for match in matches)
        return sorted(list(variables))


class PDFMiddleware:
    """Middleware pipeline for PDF processing."""

    def __init__(self):
        self.middlewares = []

    def add(self, func):
        """Add middleware function (func(next_callable, *args, **kwargs))."""
        self.middlewares.append(func)

    def execute(self, final_handler, *args, **kwargs):
        """Execute chain in correct order."""

        def build_chain(handler, middleware):
            return lambda *a, **kw: middleware(handler, *a, **kw)

        chain = final_handler
        for mw in reversed(self.middlewares):
            chain = build_chain(chain, mw)

        return chain(*args, **kwargs)


# Example usage
if __name__ == '__main__':
    # Initialize manager
    manager = PDFTemplateManager(
        templates_dir='pdf_templates',
        output_dir='pdf_output'
    )
    
    # Example: Generate invoice
    invoice_data = {
        'invoice_number': 'INV-2024-001',
        'date': '2024-01-15',
        'company_name': 'Acme Corporation',
        'customer_name': 'John Doe',
        'items': [
            {'description': 'Consulting Services', 'quantity': 10, 'price': 150.00},
            {'description': 'Software License', 'quantity': 1, 'price': 500.00}
        ],
        'subtotal': 2000.00,
        'tax_rate': 0.10,
        'total': 2200.00
    }
    
    # Custom PDF options (optional)
    pdf_options = {
        'format': 'A4',
        'print_background': True,
        'margin': {
            'top': '1cm',
            'right': '1cm',
            'bottom': '1cm',
            'left': '1cm'
        }
    }
    
    # Generate PDF
    output = manager.generate_pdf(
        'invoice.html', 
        invoice_data, 
        'invoice_001.pdf',
        pdf_options=pdf_options
    )
    print(f"PDF generated: {output}")