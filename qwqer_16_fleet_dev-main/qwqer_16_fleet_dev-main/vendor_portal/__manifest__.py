# -*- coding: utf-8 -*-
{
    'name': "Vendor Portal",
    "version": "16.0.1.0.0",
    'summary': """custom portal for vendors""",
    'description': """custom portal for vendors""",
    'category': 'website',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    'website': "https://www.qwysoft.com",

    'depends': ['base', 'portal', 'website', 'website_payment', 'fleet_urban_haul'],

    'data': [
        'security/ir.model.access.csv',
        'data/sequence_no.xml',
        'views/vendor_portal_trip_templates.xml',
        'views/vendor_portal_bill.xml',
        'views/vendor_portal_vehicle.xml',
        'views/trip_creation_form.xml',
        'views/qwqer_fleet_login_page.xml',
        'views/trip_bulk_upload_form.xml',
    ],

    'assets': { 
        'web.assets_frontend': [
            'vendor_portal/static/src/scss/loginpage.scss',
            'vendor_portal/static/src/scss/trip_page.scss',
            'vendor_portal/static/src/scss/trip_creation_page.scss',
            'vendor_portal/static/src/js/vendor_portal.js',
            'vendor_portal/static/src/js/vendor_trip_form_portal.js',
            'vendor_portal/static/src/js/bulk_upload_trip.js'
        ],
        'external_dependencies': {
            'python': ['openpyxl', 'python-magic'],
        },
    },

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
