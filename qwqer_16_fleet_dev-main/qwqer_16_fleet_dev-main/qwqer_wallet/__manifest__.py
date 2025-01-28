# -*- coding: utf-8 -*-

{
    'name': 'QWQER Wallet',
    'category': 'Other',
    'sequence': 55,
    'summary': 'Customer Wallet for QWQER',
    'author': 'QWY Technologies Pvt Ltd',
    'company': 'QWY Technologies Pvt Ltd',
    'website': 'www.qwqer.in',
    'version': '16.0.1.0.02',
    'description': """
        Customer Wallet
        """,
    'depends': ['mail', 'delivery_base','account_base','sale_extended'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/add_wallet_amount_view.xml',
        'wizard/deduct_wallet_amount_view.xml',
        'wizard/wallet_offset_wizard_view.xml',
        'report/customer_wallet_report.xml',
        'report/customer_wallet_detailed_report.xml',
        'data/sequence.xml',
        'data/wallet_data.xml',
        'views/res_partner.xml',
        'views/customer_wallet_configuration_view.xml',
        'views/account_move.xml',
        'views/payment_mode.xml',
        'views/sale_order_inherit.xml',
        'views/menu.xml',



    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
