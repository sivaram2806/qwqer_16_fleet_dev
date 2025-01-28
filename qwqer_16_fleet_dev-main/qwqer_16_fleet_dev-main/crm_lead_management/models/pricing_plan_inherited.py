from odoo import api, fields, models, _


class InheritedPricingPlan(models.Model):
    _inherit = "pricing.plan"
    _description = "Pricing Plan For Lead"

    crm_lead_id = fields.Many2one('crm.lead', string="Crm Lead")
