# -*- coding: utf-8 -*-
{
    'name': "Qshop Base",
    'summary': """
        """,
    'description': """
       
    """,
    'author': "",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','sale','account','sale_extended','payment_cashfree'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'security/rules.xml',
        'data/product_data.xml',
        'data/sequence.xml',
        'data/qshop_merchant_payout_mail_template.xml',
        'data/qshop_merchant_payout_cashfree_status.xml',
        'report/merchant_payout_line_xlsx_view.xml',
        'wizard/re_init_qshop_payout_wiz.xml',
        'views/partner_service_type_view.xml',
        'views/consolidate_sale_invoice.xml',
        'views/res_partner.xml',
        'views/state_journal_view.xml',
        'views/qwqer_shop_merchant_configuration_view.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order.xml',
        'views/merchant_account_config.xml',
        'views/qshop_merchant_payout.xml',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
