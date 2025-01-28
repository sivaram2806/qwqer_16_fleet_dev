# -*- coding: utf-8 -*-
from odoo import fields, models, api, _



class UserActionLog(models.Model):
    _name = "user.action.log"

    change_req_id = fields.Many2one(comodel_name='customer.master.change.request',string='Change Request')
    res_user = fields.Many2one(comodel_name='res.users', string='User')
    state_from = fields.Char(string="From")
    state_to = fields.Char(string="To")
    comments = fields.Char(string='Comments')