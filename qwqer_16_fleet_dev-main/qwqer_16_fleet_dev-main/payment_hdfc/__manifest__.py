# -*- coding: utf-8 -*-
{
    'name': 'HDFC Payments',
    'version': '16.0.1.0.0',
    'summary': """Integrations related to HDFC bank are added in this module""",
    'description': """To sync, create and manage HDFC bank payments""",
    'category': 'Accounting/Payment',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'depends': ['base', 'account_base', 'account', 'fleet_ftl', 'payment_request'],
    'website': 'https://qwysoft.com/',
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'wizard/hdfc_adv_pay_import_wizard.xml',
        'reports/hdfc_adv_pay_export.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {

    },

}
