from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import datetime


class PricingPlan(models.Model):
    """inherited for modify the pricing plan model"""
    _inherit = 'pricing.plan'

    customer_ob_plan_id = fields.Many2one(comodel_name='customer.onboard', string='Customer Pricing Plan')

    # @api.model
    # def create(self, vals_list):
    #     if vals_list['select_plan_type']:
    #         other_plan = self.env['pricing.plan'].search(
    #             [('customer_ob_plan_id', '=', vals_list['customer_ob_plan_id']),
    #              ('select_plan_type', '!=', vals_list['select_plan_type'])])
    #         if other_plan:
    #             for rec in other_plan:
    #                 rec.unlink()
    #     return super().create(vals_list)
