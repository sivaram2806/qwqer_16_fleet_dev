# -*- coding: utf-8 -*-
{
    'name': 'Fleet FTL Tracking',
    'version': '16.0.1.0.02',
    'summary': """Fleet FTL module extended""",
    'description': """ This module tracking details in fleet module""",
    'category': 'Human Resources/Fleet',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'depends': ['base', 'fleet_ftl', 'qwqer_sim_based_tracking'],
    'website': 'https://qwysoft.com/',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/track_history_cron.xml',
        'views/batch_trip_ftl_views.xml',
        'views/tracking_details_view.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'fleet_ftl_tracking/static/src/xml/**/*',
            'fleet_ftl_tracking/static/src/css/button_style.css'
        ],
    },
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
