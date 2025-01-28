# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qshop_merchant_payout_id = fields.Many2one('qshop.merchant.payout', string='Qshop Merchant Payout', copy=False)

    def _compute_partner_id(self):
        for line in self:
            shop_merchant_discount_accid_id = self.env['merchant.journal.data.configuration'].search([], limit=1).shop_merchant_discount_accid
            if line.account_id.id==shop_merchant_discount_accid_id.id:
                line.partner_id = False
            else:
                line.partner_id = line.move_id.partner_id.commercial_partner_id


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_qshop_service = fields.Boolean(string='Is Qshop service',related='service_type_id.is_qshop_service')
