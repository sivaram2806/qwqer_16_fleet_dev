# -*- coding: utf-8 -*-

{
    'name': 'E-Invoice (TAXPRO)',
    'category': 'Accounting/Accounting',
    'sequence': 55,
    'summary': 'E-Invoice',
    'author': 'QWY Technologies',
    'website': 'www.qwqer.in',
    
    'version': '1.03',

    'description': """
    Automated E-Invoice Generation: Generate electronic invoices quickly and accurately.
    Printing Details: Includes options for printing invoice details as needed.
    Manual, Bulk, and Scheduled E-Invoices: Supports flexible invoicing methods based on user preferences.
        """,
    'depends': ['account_base', 'qwqer_base'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rules_multi_company.xml',
        'data/einvoice_cron.xml',
        'reports/account_invoice_report.xml',
        'wizard/einvoice_bulk_update_wizard_view.xml',
        'view/outgoing_api_log_view.xml',
        'view/einvoice_config_view.xml',
        'view/einvoice_details_view.xml',
        # 'view/einvoice_next_generate_config_view.xml',  TODO: uncomment after implementing other services
        'view/einvoice_scheduler_failed_log.xml',
        'view/account_move_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
}

