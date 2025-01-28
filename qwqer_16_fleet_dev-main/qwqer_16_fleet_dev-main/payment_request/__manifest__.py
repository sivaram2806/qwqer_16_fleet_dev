# -*- coding: utf-8 -*-
{
    'name': "Payment Request",

    'summary': """
        Payment Request module used to see the payment request that created through mail""",

    'description': """
        Payment Request module used to see the payment request that created through mail
    """,

    'author': "QWY Software PVT Ltd",
    'website': "www.qwysoft.com",
    'category': 'Accounts',
    'version': '16.0.1.0.0',
    'depends': ['base',"mail",'account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/payment_req_seq.xml',
        'data/mail_template.xml',
        'report/hdfc_export.xml',
        'wizard/import_bank_data.xml',
        'views/account_move.xml',
        'views/payment_request.xml',
        'views/import_config.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'images': [],
}
