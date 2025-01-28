# -*- coding: utf-8 -*-
{
    'name': 'Account GST Reports',
    'version': '16.0.1.0.0',
    'summary': 'GST Reports',
    'sequence': 30,
    'author': 'qwysofyware',
    'company': 'QWY Software PVT Ltd',
    'website': '',
    'description': """
    """,
    'category': 'Other',
    'images': [],
    'depends': ['account','fleet_extend'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/gst_report_wizard.xml',
        'reports/gst_report.xml',

    ],
    'demo': [

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
}
