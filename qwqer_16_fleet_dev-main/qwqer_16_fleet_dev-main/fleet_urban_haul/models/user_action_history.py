# -*- coding: utf-8 -*-

from odoo import api, fields, models


class UserActionHistory(models.Model):
    """
    The model used for storing action history done by every users.
    """
    _name = "user.action.history"
    _description = "User Action History"

    description = fields.Char(string="Comments")
    batch_trip_uh_id = fields.Many2one('batch.trip.uh')
    action = fields.Char(string="Action Performed")



