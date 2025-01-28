# -*- coding: utf-8 -*-

{
    'name': 'Journal Sequence ',
    'version': '16.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Journal Entry Sequence, Invoice Sequence',
    'description': 'Journal Entry Sequence, Invoice Sequence',
    'sequence': '1',
    "author": "qwysoft [India] Pvt.Ltd.",
    "website": "http://www.qwysoft.com",
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal.xml',
        'views/account_move.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
