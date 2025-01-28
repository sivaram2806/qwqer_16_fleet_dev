# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountTax(models.Model):
    """ The model account_tax is inherited to make modifications """
    _inherit = 'account.tax'

    is_tds = fields.Boolean(string='TDS')
    tds_applicable = fields.Selection([('person', 'Individual'),
                                       ('company', 'Company'),
                                       ('common', 'Common')], string='Applicable to')
    payment_excess = fields.Float('Payment in excess of')

