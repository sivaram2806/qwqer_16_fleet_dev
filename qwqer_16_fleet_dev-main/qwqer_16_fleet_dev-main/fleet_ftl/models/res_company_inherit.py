from odoo import models, fields, api


class CompanyExtended(models.Model):
    _inherit = 'res.company'

    ftl_back_days = fields.Integer(string='Ftl Back Days', readonly=False)
    ftl_online_payment_method_ids = fields.Many2many(comodel_name='account.journal', relation='ftl_online_payment_methods',
                                                     column1='method_id', column2='online_payment_method_id',
                                                     string='FTL Work Order bank payment methods')
    ftl_bank_payment_method_ids = fields.Many2many(comodel_name='account.journal', relation='ftl_bank_payment_methods',
                                                   column1='method_id', column2='bank_payment_method_id',
                                                   string='FTL Work Order bank payment methods')