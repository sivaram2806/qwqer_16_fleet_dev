from email.policy import default

from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import datetime


class PricingPlan(models.Model):
    """inherited for modify the pricing plan model"""
    _inherit = 'pricing.plan'

    change_req_id = fields.Many2one(comodel_name='customer.master.change.request', string='New Change Request')
    previous_change_req_id = fields.Many2one(comodel_name='customer.master.change.request', string='Change Request')
    pricing_plan_id = fields.Many2one(comodel_name='pricing.plan')
    is_changed = fields.Boolean(default=False)


