# -*- coding: utf-8 -*-

{
    'name': 'Financial Reports in Excel',
    'version': '13.47',
    'author': 'Zesty Beanz Technology FZE',
    'website': 'www.zbeanztech.com',
    'depends': ['account', 'report_xlsx','accounting_pdf_reports', 'qwqer_base'],
    'demo': [],
    'description': 
        """
        Profit and Loss, Balance Sheet in Excel
        """,
    'data': [
        'security/user_groups.xml',
        # 'data/account_report_data.xml',
        'wizard/account_fin_report_wiz.xml',
        'views/financial_report_view.xml',
        # 'views/account_type_view.xml',
        'views/report_financial_inherit.xml',
        'reports/pl_bs_report.xml',
        'views/menu.xml',
        
        ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'images': [],
    'summary': '',
    'category': 'Account',
}
