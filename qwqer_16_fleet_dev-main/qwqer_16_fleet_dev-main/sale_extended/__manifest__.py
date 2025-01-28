# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Sale Extended',
    'version': '16.0.1.0.03',
    'category': 'Sales/Sales',
    'summary': 'extending Sales module',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'description': """
This module contains all the extended features of Sales Management and eCommerce.   
    """,
    'website': 'https://qwysoft.com/',
    'depends': ['sale', 'account', 'account_base','sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/csv_import_fields_data.xml',
        'data/product_data.xml',
        'data/import_seq.xml',
        'data/sequence.xml',
        'data/scheduler_data.xml',
        'report/report_xlsx.xml',
        'report/sale_order_csv_report_export_view.xml',
        'report/account_invoice_template_inherited.xml',
        'wizard/sale_order_csv_report.xml',
        'views/order_status.xml',
        'views/account_move.xml',
        'views/sale_order.xml',
        'views/sale_order_manual_import.xml',
        'views/consolidate_sale_invoice.xml',
        'views/res_config_settings_views.xml',
        'views/individual_invoice_view.xml',
        'views/state_journal_view.xml',
        'views/merchant_account_config.xml',
        'views/merchant_configuration_view.xml',
        'views/merchant_consolidate.xml',
        'views/res_partner.xml',
        'views/customer_balance.xml',
        'views/application_driver_balance_view.xml'
    ],

    'assets': {
            'web.assets_backend': [
                'sale_extended/static/src/js/json_charge_field.js',
                'sale_extended/static/src/xml/json_charge_field_widget_template.xml'
            ]
        },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
