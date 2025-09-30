"""
PDF Template Manager - Enterprise-grade PDF generation from HTML templates
Supports dynamic templating with Jinja2 syntax and converts to PDF using WeasyPrint
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
from weasyprint import HTML, CSS
import re


class PDFTemplateManager:
    """
    Manages PDF generation from HTML templates with dynamic data injection.
    
    Features:
    - Jinja2 templating engine for dynamic content
    - Automatic template discovery
    - Custom filters and functions
    - CSS support with template inheritance
    - Batch PDF generation
    - Template validation
    
    Usage:
        manager = PDFTemplateManager(
            templates_dir='templates',
            output_dir='output'
        )
        
        # Generate single PDF
        manager.generate_pdf(
            template_name='invoice.html',
            data={'invoice_number': '12345', 'total': 1500.00},
            output_filename='invoice_12345.pdf'
        )
        
        # Generate multiple PDFs
        manager.batch_generate([
            {'template': 'invoice.html', 'data': {...}, 'output': 'inv1.pdf'},
            {'template': 'report.html', 'data': {...}, 'output': 'rep1.pdf'}
        ])
    """
    
    def __init__(
        self,
        templates_dir: str = 'templates',
        output_dir: str = 'output',
        static_dir: Optional[str] = None,
        auto_create_dirs: bool = True
    ):
        """
        Initialize the PDF Template Manager.
        
        Args:
            templates_dir: Directory containing HTML templates
            output_dir: Directory for generated PDFs
            static_dir: Directory for static assets (CSS, images)
            auto_create_dirs: Automatically create directories if they don't exist
        """
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.static_dir = Path(static_dir) if static_dir else self.templates_dir / 'static'
        
        if auto_create_dirs:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._register_custom_filters()
        
        # Add global functions
        self._register_global_functions()
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters for templates."""
        
        def currency(value, symbol='$'):
            """Format number as currency."""
            try:
                return f"{symbol}{float(value):,.2f}"
            except (ValueError, TypeError):
                return value
        
        def date_format(value, format_str='%Y-%m-%d'):
            """Format date string."""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            if isinstance(value, datetime):
                return value.strftime(format_str)
            return value
        
        def percentage(value, decimals=2):
            """Format number as percentage."""
            try:
                return f"{float(value):.{decimals}f}%"
            except (ValueError, TypeError):
                return value
        
        def truncate_words(value, length=50):
            """Truncate text to specified word count."""
            words = str(value).split()
            if len(words) <= length:
                return value
            return ' '.join(words[:length]) + '...'
        
        # Register filters
        self.env.filters['currency'] = currency
        self.env.filters['date_format'] = date_format
        self.env.filters['percentage'] = percentage
        self.env.filters['truncate_words'] = truncate_words
    
    def _register_global_functions(self):
        """Register global functions available in templates."""
        
        def now(format_str='%Y-%m-%d %H:%M:%S'):
            """Get current timestamp."""
            return datetime.now().strftime(format_str)
        
        def range_list(start, end, step=1):
            """Generate a range of numbers."""
            return list(range(start, end, step))
        
        def sum_field(items, field):
            """Sum a specific field from list of dicts."""
            return sum(item.get(field, 0) for item in items)
        
        # Register globals
        self.env.globals['now'] = now
        self.env.globals['range'] = range_list
        self.env.globals['sum_field'] = sum_field
    
    def list_templates(self) -> List[str]:
        """
        List all available HTML templates.
        
        Returns:
            List of template filenames
        """
        return [
            f.name for f in self.templates_dir.glob('*.html')
            if f.is_file()
        ]
    
    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """
        Validate template syntax and structure.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Dictionary with validation results
        """
        try:
            template = self.env.get_template(template_name)
            # Try to render with empty data
            template.render({})
            return {
                'valid': True,
                'template': template_name,
                'message': 'Template is valid'
            }
        except Exception as e:
            return {
                'valid': False,
                'template': template_name,
                'error': str(e)
            }
    
    def render_template(
        self,
        template_name: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Render HTML template with data.
        
        Args:
            template_name: Name of the template file
            data: Dictionary containing template variables
            
        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(template_name)
        return template.render(**data)
    
    def generate_pdf(
        self,
        template_name: str,
        data: Dict[str, Any],
        output_filename: str,
        css_file: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Path:
        """
        Generate PDF from template and data.
        
        Args:
            template_name: Name of the template file
            data: Dictionary containing template variables
            output_filename: Name of the output PDF file
            css_file: Optional external CSS file
            base_url: Base URL for resolving relative paths
            
        Returns:
            Path to generated PDF file
        """
        # Render HTML
        html_content = self.render_template(template_name, data)
        
        # Set base URL for resolving assets
        if base_url is None:
            base_url = self.templates_dir.as_uri()
        
        # Create HTML object
        html = HTML(string=html_content, base_url=base_url)
        
        # Add external CSS if provided
        stylesheets = []
        if css_file:
            css_path = self.static_dir / css_file
            if css_path.exists():
                stylesheets.append(CSS(filename=str(css_path)))
        
        # Generate PDF
        output_path = self.output_dir / output_filename
        html.write_pdf(output_path, stylesheets=stylesheets)
        
        return output_path
    
    def batch_generate(
        self,
        jobs: List[Dict[str, Any]],
        continue_on_error: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple PDFs in batch.
        
        Args:
            jobs: List of job dictionaries with keys:
                  - template: template name
                  - data: template data
                  - output: output filename
                  - css_file: (optional) CSS file
            continue_on_error: Continue processing if one job fails
            
        Returns:
            List of results with status for each job
        """
        results = []
        
        for i, job in enumerate(jobs):
            try:
                output_path = self.generate_pdf(
                    template_name=job['template'],
                    data=job['data'],
                    output_filename=job['output'],
                    css_file=job.get('css_file')
                )
                results.append({
                    'job_index': i,
                    'success': True,
                    'output_path': str(output_path),
                    'template': job['template']
                })
            except Exception as e:
                results.append({
                    'job_index': i,
                    'success': False,
                    'error': str(e),
                    'template': job['template']
                })
                if not continue_on_error:
                    break
        
        return results
    
    def preview_html(
        self,
        template_name: str,
        data: Dict[str, Any],
        output_filename: str = 'preview.html'
    ) -> Path:
        """
        Generate HTML preview of template without converting to PDF.
        
        Args:
            template_name: Name of the template file
            data: Dictionary containing template variables
            output_filename: Name of the output HTML file
            
        Returns:
            Path to generated HTML file
        """
        html_content = self.render_template(template_name, data)
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def create_template_from_string(
        self,
        template_name: str,
        html_content: str
    ) -> Path:
        """
        Create a new template file from HTML string.
        
        Args:
            template_name: Name for the new template
            html_content: HTML content string
            
        Returns:
            Path to created template file
        """
        template_path = self.templates_dir / template_name
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return template_path
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """
        Extract variable names used in a template.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            List of variable names found in template
        """
        template = self.env.get_template(template_name)
        source = template.source
        
        # Find all Jinja2 variables {{ variable }}
        variables = set(re.findall(r'\{\{\s*(\w+)', source))
        
        return sorted(list(variables))


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
    
    # List available templates
    print("Available templates:", manager.list_templates())
    
    # Validate template (if exists)
    # validation = manager.validate_template('invoice.html')
    # print("Validation:", validation)
    
    # Generate PDF
    # output = manager.generate_pdf('invoice.html', invoice_data, 'invoice_001.pdf')
    # print(f"PDF generated: {output}")