# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Spreadsheet dashboard for Fleet",
    'category': 'Hidden',
    'summary': 'Spreadsheet',
    'description': 'Spreadsheet',
    'depends': [ 'spreadsheet', 'web', 'spreadsheet_dashboard', 'fleet_ftl', 'fleet','fleet_urban_haul'],
    'data': [
        "security/fleet_dashboard_groups.xml",
        "data/dashboards.xml",
        "views/dashboard_view.xml"
    ],
    'demo': [],
    'installable': True,
    'assets': {
        "spreadsheet.o_spreadsheet": [
            "spreadsheet_dashboard_fleet/static/src/bundle/**/*.js",
            "spreadsheet_dashboard_fleet/static/src/bundle/**/*.xml",
        ],
        "web.assets_backend": [
            "spreadsheet_dashboard_fleet/static/src/assets/**/*.js",
            "spreadsheet_dashboard_fleet/static/src/**/*.scss",
        ],},
    'license': 'LGPL-3'
}
