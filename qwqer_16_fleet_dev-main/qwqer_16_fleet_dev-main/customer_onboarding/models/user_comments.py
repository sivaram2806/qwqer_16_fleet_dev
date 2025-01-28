# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class UserComments(models.Model):
    """ model for saving the user comments"""
    _name = "user.comments"
    _description = "User Comments"

    user_id = fields.Many2one(comodel_name='res.users', string="User")
    user_comment = fields.Text('Comments')
    comment_customer_onboard_id = fields.Many2one(comodel_name='customer.onboard', string='Customer Onboard id')
    commented_on = fields.Datetime(string="Commented on")

