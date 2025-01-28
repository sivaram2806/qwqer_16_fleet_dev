# -*- coding: utf-8 -*-

from odoo import models, fields

class MerchantJournalConfiguration(models.Model):
    """This model is for configuring the journal entry data for the merchant merchant.amount.configuration in odoo v13"""

    _name = 'merchant.journal.data.configuration'
    _description = 'Merchant Online  Journal Data Configuration'

    partner_id = fields.Many2one('res.partner', string='Partner')
    journal_id = fields.Many2one("account.journal", string='Journal')