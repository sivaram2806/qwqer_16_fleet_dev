# -*- coding: utf-8 -*-
{
    'name': "Fiscal Year Sequence Extensible",

    'summary': """
        Fiscal Year Sequence Extensible""",

    'description': """
        Fiscal year sequence extensible module is to add prefix and suffix from date range of sequence. We can use %(prefix)s and %('suffix')s as prefix and suffix code.
    """,

    "author": "qwysoft [India] Pvt.Ltd.",
    "website": "http://www.qwysoft.com",
    "complexity": "easy",
    'license': 'LGPL-3',
    'support': 'qwysoft@qwysoft.com',
    # for the full list
    'category': 'Account',
    'version': '13.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/ir_sequence_view.xml',
    ],
    'installable': True,
    'application': True,
}
