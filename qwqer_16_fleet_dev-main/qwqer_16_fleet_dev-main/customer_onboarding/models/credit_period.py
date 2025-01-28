from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import datetime


class CreditPeriod(models.Model):
    """model for capturing credit period"""
    _name = 'credit.period'

    from_period = fields.Integer(string='From Period')
    to_period = fields.Integer(string='To Period')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s' % (rec.from_period, rec.to_period)))
        return result
