{
    'name': "Scheduled Activity Report",
    'version': '16.0.3.0.0',
    'category': 'CRM Lead Management',
    'sequence': 348,
    'summary': """Scheduled Activity Report""",
    'description': 'List view and excel download of Activities scheduled or marked under the CRM lead management',
    'author': "QWY Software PVT Ltd",
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'website': 'https://qwysoft.com/',
    'depends': ['base','crm','mail','report_xlsx'],
    'data': [
        'security/mail_activity_security.xml',
        'report/report_xlsx.xml',
        'views/mail_activity_inherit.xml'
    ],
    'assets': {},
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
