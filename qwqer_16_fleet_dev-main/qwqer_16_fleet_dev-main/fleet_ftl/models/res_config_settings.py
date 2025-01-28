from odoo import models, fields, api


class CompanyExtended(models.Model):
    _inherit = 'res.company'

    ftl_back_days = fields.Integer(string='Ftl Back Days', readonly=False)

class ResConfigFtlSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftl_back_days = fields.Integer(related='company_id.ftl_back_days', string='Ftl Back Days', readonly=False)
    ftl_online_payment_method_ids = fields.Many2many(related='company_id.ftl_online_payment_method_ids', readonly=False,
                                                     string='FTL Work Order bank payment methods')
    ftl_bank_payment_method_ids = fields.Many2many(related='company_id.ftl_bank_payment_method_ids', readonly=False,
                                                   string='FTL Work Order bank payment methods')