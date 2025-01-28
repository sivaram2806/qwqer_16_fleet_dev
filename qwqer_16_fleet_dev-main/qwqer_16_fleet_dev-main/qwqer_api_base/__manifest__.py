# -*- coding: utf-8 -*-
{
    'name': 'QWQER API Base',
    'version': '16.0.1.0.0',
    'summary': """base """,
    'description': """ This module contains API KEY auth and response modification for fail auth """,
    'category': 'Tools',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'depends': ['base', 'qwqer_base'],
    'website': 'https://qwysoft.com/',
    'data': [
        "security/ir.model.access.csv",
        "views/api_request_response_raw_log.xml",
        "data/clear_api_log.xml"
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}