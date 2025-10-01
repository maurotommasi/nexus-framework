from nexus.pdf.pdf_template_manager import PDFTemplateManager
from datetime import datetime, timedelta
from pathlib import Path

def generate_sample_invoice():
    """Generate a sample invoice PDF"""
    
    # Initialize the PDF manager
    manager = PDFTemplateManager(
        templates_dir='resources/html_template_pdf',
        output_dir='pdf_output'    )
    
    # Sample invoice data
    invoice_data = {
        # Company info
        'company_name': 'Acme Corporation',
        'company_address': '456 Innovation Drive',
        'company_city': 'San Francisco, CA 94105',
        'company_phone': '(415) 555-0123',
        'company_email': 'billing@acmecorp.com',
        
        # Invoice details
        'invoice_number': 'INV-2024-001',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'status': 'Pending',
        
        # Customer info
        'customer_name': 'John Doe',
        'customer_company': 'Tech Startup Inc.',
        'customer_address': '789 Startup Lane',
        'customer_city': 'Austin, TX 78701',
        'customer_email': 'john.doe@techstartup.com',
        
        # Line items
        'items': [
            {
                'description': 'Website Design & Development',
                'details': 'Custom responsive design with CMS integration',
                'quantity': 1,
                'price': 5000.00
            },
            {
                'description': 'SEO Optimization',
                'details': 'On-page SEO, keyword research, and content optimization',
                'quantity': 1,
                'price': 1500.00
            },
            {
                'description': 'Content Creation',
                'details': '10 blog posts with custom graphics',
                'quantity': 10,
                'price': 200.00
            },
            {
                'description': 'Monthly Maintenance',
                'details': 'Hosting, updates, and technical support',
                'quantity': 3,
                'price': 150.00
            }
        ],
        
        # Totals
        'subtotal': 8950.00,
        'tax_rate': 0.0875,  # 8.75%
        'discount': 0,
        'total': 9733.13,
        
        # Payment info
        'bank_name': 'Silicon Valley Bank',
        'bank_account': '**** **** **** 4567',
        'bank_routing': '121000248',
        'payment_terms': 'Net 30',
        
        # Notes
        'notes': 'Please include the invoice number in your payment reference. Late payments may incur a 1.5% monthly interest charge.'
    }
    
    # PDF options for exact control
    pdf_options = {
        'format': 'A4',  # or 'Letter'
        'print_background': True,  # Include background colors
        'margin': {
            'top': '0.5in',
            'right': '0.5in',
            'bottom': '0.5in',
            'left': '0.5in'
        },
        'prefer_css_page_size': True,  # Use @page CSS rules
    }
    
    # Generate the PDF
    output_path = manager.generate_pdf(
        template_name='template1.html',
        data=invoice_data,
        output_filename=f'invoice_{invoice_data["invoice_number"]}.pdf',
        pdf_options=pdf_options
    )
    
    print(f"✓ Invoice generated: {output_path}")
    
    # Also generate HTML preview for quick viewing
    html_path = manager.preview_html(
        template_name='template1.html',
        data=invoice_data,
        output_filename='invoice_preview.html'
    )
    print(f"✓ HTML preview: {html_path}")
    
    return output_path


def batch_generate_invoices():
    """Generate multiple invoices at once"""
    
    manager = PDFTemplateManager(
        templates_dir='pdf_templates',
        output_dir='pdf_output',
        pdf_engine='playwright'
    )
    
    # Multiple invoice jobs
    jobs = [
        {
            'template': 'invoice.html',
            'output': 'invoice_client_001.pdf',
            'data': {
                'invoice_number': 'INV-2024-001',
                'date': '2024-01-15',
                'company_name': 'Acme Corp',
                'customer_name': 'Client A',
                'items': [
                    {'description': 'Service A', 'quantity': 5, 'price': 100.00}
                ],
                'subtotal': 500.00,
                'tax_rate': 0.10,
                'total': 550.00
            }
        },
        {
            'template': 'invoice.html',
            'output': 'invoice_client_002.pdf',
            'data': {
                'invoice_number': 'INV-2024-002',
                'date': '2024-01-16',
                'company_name': 'Acme Corp',
                'customer_name': 'Client B',
                'items': [
                    {'description': 'Service B', 'quantity': 3, 'price': 250.00}
                ],
                'subtotal': 750.00,
                'tax_rate': 0.10,
                'total': 825.00
            }
        }
    ]
    
    # Generate all invoices
    results = manager.batch_generate(jobs, continue_on_error=True)
    
    # Print results
    for result in results:
        if result['success']:
            print(f"✓ Job {result['job_index']}: {result['output_path']}")
        else:
            print(f"✗ Job {result['job_index']} failed: {result['error']}")


if __name__ == '__main__':
    # Generate a single invoice
    generate_sample_invoice()
    
    # Or batch generate multiple invoices
    # batch_generate_invoices()