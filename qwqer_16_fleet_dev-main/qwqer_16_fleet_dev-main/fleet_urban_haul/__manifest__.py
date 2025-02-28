# -*- coding: utf-8 -*-
{
    'name': 'Fleet Urban Haul',
    'version': '16.0.1.0.02',
    'summary': """Fleet Urban Haul""",
    'description': """ This module contains Urban Haul features in fleet""",
    'category': 'Human Resources/Fleet',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'depends': ['base', 'hr', 'fleet', 'qwqer_base', 'fleet_extend', 'account_base', 'report_xlsx'],
    'website': 'https://qwysoft.com/',
    'data': [
        'security/vehicle_management_group.xml',
        'security/ir.model.access.csv',
        'data/batch_trip_uh_sequence.xml',
        'data/batch_trip_uh_mail_template.xml',
        'data/daily_revenue_report_email_template.xml',
        'data/monthly_revenue_report_email_template.xml',
        'data/cumulative_amount_cron.xml',
        'data/revenue_report_cron.xml',
        'wizard/bulk_trip_approve_wizard_view.xml',
        'wizard/user_action_comment_wizard_view.xml',
        'views/batch_trip_uh_view.xml',
        'views/urban_haul_report.xml',
        'views/trip_summary_uh_view.xml',
        'views/account_move_view.xml',
        'views/res_config_settings_view.xml',
        'views/res_partner_views.xml',
        'views/menu.xml',
        'views/customer_balance_summary.xml',
        'report/report_xlsx.xml',
        'wizard/trip_summary_report_wizard_view.xml',
        'wizard/cost_analysis_report_wizard_view.xml',
        'report/account_invoice_template_inherited.xml'

    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
