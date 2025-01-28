# -*- coding: utf-8 -*-

from odoo import models,api
import logging
_logger = logging.getLogger(__name__)

class SaleOrderDelivery(models.Model):
    """This model Sale.Order is inherited to make modification for delivery orders """

    _inherit = 'sale.order'

    @api.onchange('total_amount', 'partner_id', 'region_id', 'order_qty')
    def _onchange_amount(self):
        for rec in self:
            rec.order_line = False
            if rec.total_amount > 0 and rec.service_type_id.is_delivery_service:
                order_line_vals = rec.get_order_line_vals()
                product = rec.env.company.product_id
                if product:
                    order_line_vals.update({
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'name': product.name
                    })
                    self.order_line = [(0, 0, order_line_vals)]

    def action_confirm(self):
        sales = super(SaleOrderDelivery, self).action_confirm()
        for order in self:
            # for delivery merchant journal creation
             if (order.service_type_id.is_delivery_service
                    and not order.is_merchant_journal
                    and order.order_status_id
                    and order.order_status_id.code == "4"
                    and order.merchant_order_amount > 0):
                # Ensure that a merchant journal does not already exist before creating a new one
                order.create_delivery_merchant_journal()
        return sales

    def create_delivery_merchant_journal(self):
        for rec in self:
            if rec.merchant_order_amount > 0:
                merchant_config = self.env['merchant.journal.data.configuration'].search([], limit=1)
                driver_details = self.env['hr.employee'].search([('driver_uid', '=', rec.driver_id.driver_uid)], limit=1)
                debit_entry_partner = (
                    merchant_config.partner_id if rec.merchant_payment_mode_id.code == "2" else driver_details.related_partner_id)

                move_line_1 = {
                    'partner_id': debit_entry_partner.id,
                    'account_id': debit_entry_partner.property_account_receivable_id.id,
                    'credit': 0.0,
                    'debit': rec.merchant_order_amount,
                    'journal_id': driver_details.journal_id.id,
                    'name': 'Merchant Amount',
                    'merchant_order_id': rec.id,
                    'service_type_id': rec.service_type_id.id,
                }
                move_line_2 = {
                    'partner_id': rec.partner_id.id,
                    'account_id': rec.partner_id.property_account_payable_id.id,
                    'credit': rec.merchant_order_amount,
                    'debit': 0.0,
                    'journal_id': merchant_config.journal_id.id,
                    'name': 'Merchant Amount',
                    'merchant_order_id': rec.id,
                    'service_type_id': rec.service_type_id.id,
                }
                record = {
                    'partner_id': rec.partner_id.id,
                    'journal_id': merchant_config.journal_id.id,
                    'company_id': self.env.user.company_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'date': rec.create_date,
                    'ref': rec.order_id,
                    'service_type_id': rec.service_type_id.id,
                    'move_type': "entry",
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                }
                invoice = self.env['account.move'].sudo().create(record)
                invoice.sudo().post()
                rec.write({'is_merchant_journal':True,'merchant_journal_entry_id':invoice.id})