# -*- coding: utf-8 -*-
{
    'name': 'QWQER Client Api',
    'version': '16.0.1.0.06',
    'summary': """base """,
    'description': """ This module contains sync api from V13 to V16 """,
    'category': '',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'depends': ['base','customer_onboarding'],
    'website': 'https://qwysoft.com/',
    'data': [
        'security/ir.model.access.csv',
        'views/partner_api_view.xml',
        'views/api_credential_view.xml',
        'views/customer_onboard.xml',
        'views/change_req.xml',
        'views/balance_sync_service.xml'
    ],
    'images': ["static/description/icon.png"],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
