{
    'name': "Fleet Enquiry Management",
    'version': '16.0.3.0.0',
    'category': 'Human Resources/Fleet',
    'sequence': 346,
    'summary': """Enquiry Management Module for fleet enquiries""",
    'description': 'Can create enquiries from UI/Import also and can manage it from'
                   ' backend.',
    'author': "QWY Software PVT Ltd",
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'website': 'https://qwysoft.com/',
    'depends': ['base', 'fleet' ,
                'mail','report_xlsx',
                'fleet_extend','qwqer_base'],
    'data': [
        'security/ticket_management_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ticket_stage_data.xml',
        'data/helpdesk_types_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/help_team_views.xml',
        'views/report_templates.xml',
        'views/help_ticket_views.xml',
        'views/helpdesk_categories_views.xml',
        'views/helpdesk_tag_views.xml',
        'views/helpdesk_types_views.xml',
        'views/ticket_stage_views.xml',
        'views/helpdesk_replay_template.xml',
        'views/help_ticket_bulk_import.xml',
        'views/ticket_management_menus.xml',
        'report/help_ticket_templates.xml',
        'report/report_xlsx.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'qwqer_ticket_management/static/src/xml/help_ticket_templates.xml',
            'qwqer_ticket_management/static/src/js/helpdesk_dashboard_action.js',
        ],
        'web.assets_frontend': [
            '/qwqer_ticket_management/static/src/cdn/jquery.sumoselect.min.js',
            '/qwqer_ticket_management/static/src/cdn/sumoselect.min.css',
        ]
    },
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
