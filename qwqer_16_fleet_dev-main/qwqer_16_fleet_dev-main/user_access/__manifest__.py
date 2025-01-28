# -*- coding: utf-8 -*-
{
    'name': 'User Access',
    'version': '16.0.1.0.1',
    'summary': """User access""",
    'description': """ This module contains the user access to given to user""",
    'category': 'Human Resources/Fleet',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'depends': ['base', 'account','spreadsheet_dashboard',
                'sale','mail','contacts','utm','hr','fleet','stock','qwqer_ticket_management','crm','driver_management',
                'hr_attendance','customer_onboarding','vendor_onboarding'],
    'website': 'https://qwysoft.com/',
    'data': [
        'security/ir.model.access.csv',
        'security/qwqer_security.xml',
        'views/menu_item.xml',
        'wizard/access_duplicate_wizard_view.xml'

    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
