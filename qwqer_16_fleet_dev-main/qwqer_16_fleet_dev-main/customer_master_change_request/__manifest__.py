# -*- coding: utf-8 -*-
{
    'name': "Customer Master Change Request",

    'summary': """module for updating customer master""",

    'description': """ In order to track and sync changes against pricing and various related aspects of the customer data 
                 between ERP and console a new process flow is designed wherein users will be able to raise a change
                 request with respect of various data field captured against customer in customer 
                 master without having special access or sending mail request.

    """,

    'version': '16.0.1.0.01',
    'author': 'QWY Software PVT Ltd',
    'company': 'QWY Software PVT Ltd',
    'maintainer': 'QWY Software PVT Ltd',
    # any module necessary for this one to work correctly
    'depends': ['base', 'qwqer_base','customer_onboarding','delivery_base'],

    # always loaded
    'data': [
        'security/customer_change_security.xml',
        'security/ir.model.access.csv',
        'data/change_field_data.xml',
        'data/mu_to_fn_mail_temp.xml',
        'data/rejected_mail_temp.xml',
        'data/return_for_correction_mail.xml',
        'data/user_to_mu_mail_temp.xml',
        'data/customer_request_sequence.xml',
        'views/change_request_view.xml',
        'views/res_partner.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
