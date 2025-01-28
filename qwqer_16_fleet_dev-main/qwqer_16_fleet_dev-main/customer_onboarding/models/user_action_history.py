# -*- coding: utf-8 -*-

from odoo import api, fields, models


class UserActionHistory(models.Model):
    """ model for storing the user action"""
    _name = "onboard.user.action.history"
    _description = "User Action History"

    user_id = fields.Many2one(comodel_name='res.users', string="User")
    description = fields.Char(string="Action Description")
    last_updated_on = fields.Datetime(string="Time of Action")
    action_customer_onboard_id = fields.Many2one(comodel_name='customer.onboard',
                                                 string='Customer Onboard Id')
    state_from = fields.Selection(selection=[('draft', 'draft'), ('mu_approvals', 'Under MU Approval'),
                                             ('finance_approvals', 'Under Finance Approval'),
                                             ('under_pricing_config', 'Under Pricing Configuration'),
                                             ('configurations_completed', 'Configurations Completed'),
                                             ('rejected', 'Rejected')
                                             ], string="State From")
    state_to = fields.Selection(selection=[('draft', 'draft'), ('mu_approvals', 'Under MU Approval'),
                                           ('finance_approvals', 'Under Finance Approval'),
                                           ('under_pricing_config', 'Under Pricing Configuration'),
                                           ('configurations_completed', 'Configurations Completed'),
                                           ('rejected', 'Rejected')
                                           ], string="State To")
