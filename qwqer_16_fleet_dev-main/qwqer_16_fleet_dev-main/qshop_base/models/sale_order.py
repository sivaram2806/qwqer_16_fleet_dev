# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from odoo import models,fields,api,_
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class SaleOrderQwqerShop(models.Model):
    """This model Sale.Order is inherited to make modification for Qwqer Shop orders """

    _inherit = 'sale.order'

    qshop_product_line = fields.One2many('qshop.product.lines', 'sale_order_id')
    billing_partner_id = fields.Many2one('res.partner', string="Billing Customer")


    merchant_discount_amount = fields.Monetary(string='Merchant Discount Amount')
    merchant_total_amount = fields.Monetary(string='Merchant Order Amount')

    promo_code = fields.Char(string='Promo Code')
    promo_desc = fields.Text(string="Promo Code Description")
    is_having_promocode = fields.Boolean(string='Is Having Promocode?')


    is_qshop_service = fields.Boolean(string="Is qshop Service")



    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrderQwqerShop, self).onchange_partner_id()
        for rec in self:
            if rec.service_type_id:
                rec.is_qshop_service = rec.service_type_id.is_qshop_service
        return res



    @api.onchange('merchant_total_amount', 'merchant_discount_amount')
    def _onchange_merchant_order_amount(self):
        for rec in self:
            if rec.is_manual_sale_order and rec.merchant_total_amount > 0:
                if not rec.service_type_id:
                    raise ValidationError(_('Please select a service type'))
                elif rec.service_type_id.is_qshop_service:
                    rec.merchant_order_amount = rec.merchant_total_amount - rec.merchant_discount_amount
                else:
                    rec.merchant_order_amount = 0

    @api.onchange('service_type_id')
    def onchange_service_type_id(self):
        res = super(SaleOrderQwqerShop, self).onchange_service_type_id()
        for rec in self:
            if not rec.service_type_id.is_qshop_service:
                rec.merchant_order_amount = 0
        return res

    @api.onchange('total_amount', 'partner_id', 'region_id', 'order_qty')
    def _onchange_amount(self):
        res = super(SaleOrderQwqerShop, self)._onchange_amount()
        for rec in self:
            if rec.total_amount > 0 and rec.service_type_id.is_qshop_service:
                order_line_vals = rec.get_order_line_vals()
                product = rec.env.company.qwqer_shop_product_id
                if product:
                    order_line_vals.update({
                        'product_id': product.id,
                        'product_uom': product.uom_id.id,
                        'name': product.name
                    })
                    self.order_line = [(0, 0, order_line_vals)]
        return res

    def action_confirm(self):
        sales = super(SaleOrderQwqerShop, self).action_confirm()
        for order in self:
            # for qwqer shop merchant journal creation
            if (    order.service_type_id.is_qshop_service
                    and not order.is_merchant_journal
                    and order.order_status_id
                    and order.order_status_id.code == "4"
                    and order.merchant_order_amount > 0  ):
                order.create_qwqer_shop_merchant_journal()
        return sales

    def create_qwqer_shop_merchant_journal(self):
        _logger.info("Inside Qwqer shop Merchant journal Creation, Time: %s", fields.datetime.now())
        for rec in self:
            merchant_order_amount = rec.merchant_order_amount
            if merchant_order_amount > 0:
                merchant_config = self.env['merchant.journal.data.configuration'].search([], limit=1)
                driver_details = self.env['hr.employee'].search([('driver_uid', '=', rec.driver_id.driver_uid)],
                                                                limit=1)
                wallet_config = self.env['customer.wallet.config'].search([], limit=1)
                if rec.merchant_payment_mode_id.code == "2":
                    debit_entry_partner = merchant_config.partner_id.id
                    debit_entry_account_id = merchant_config.partner_id.property_account_receivable_id.id
                elif rec.merchant_payment_mode_id.is_wallet_payment:
                    debit_entry_partner = rec.billing_partner_id.id
                    debit_entry_account_id = wallet_config.merchant_inter_account_id.id
                else:
                    debit_entry_partner = driver_details.related_partner_id.id
                    debit_entry_account_id = driver_details.related_partner_id.property_account_receivable_id.id

                move_line_1 = {
                    'partner_id': debit_entry_partner,
                    'account_id': debit_entry_account_id,
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
                    'credit': rec.merchant_total_amount if rec.merchant_total_amount > 0 else merchant_order_amount,
                    'debit': 0.0,
                    'journal_id': merchant_config.qshop_journal_id.id,
                    'name': 'Merchant Amount',
                    'merchant_order_id': rec.id,
                    'service_type_id': rec.service_type_id.id,
                }
                line_ids = [(0, 0, move_line_1), (0, 0, move_line_2)]
                if rec.merchant_discount_amount > 0:
                    move_line_3 = {
                        'account_id': merchant_config.sudo().shop_merchant_discount_accid.id,
                        'credit': 0.0,
                        'debit': rec.merchant_discount_amount,
                        'journal_id': merchant_config.qshop_journal_id.id,
                        'name': 'Merchant Amount',
                        'merchant_order_id': rec.id,
                        'service_type_id': rec.service_type_id.id,
                    }
                    line_ids.insert(1,(0, 0, move_line_3))
                record = {
                    'partner_id': rec.partner_id.id,
                    'journal_id': merchant_config.qshop_journal_id.id,
                    'company_id': self.env.user.company_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'date': rec.create_date,
                    'ref': rec.order_id,
                    'move_type': "entry",
                    'service_type_id': rec.service_type_id.id,
                    'segment_id': rec.partner_id.segment_id.id,
                    'line_ids': line_ids,
                }
                invoice = self.env['account.move'].sudo().create(record)
                invoice.sudo().post()
                rec.write({'is_merchant_journal': True, 'merchant_journal_entry_id': invoice.id})

    def create_qwqer_shop_credit_order_journal(self):
        """create journal for qwqer shop credit sale orders"""
        _logger.info("Inside Qshop credit journal create function, Time: %s", fields.datetime.now())
        for rec in self:
            date = rec.date_order
            credit_journal_id = self.env.company.qwqer_shop_credit_journal_id
            if credit_journal_id:
                move_line_1 = {}
                total_amount = 0
                state_journal_region = self.env['state.journal'].search([('state_id', '=', rec.region_id.state_id.id)])
                for order_line in rec.order_line:
                    label_name = rec._get_computed_name(order_line.product_id, state_journal_region)
                    accounts = order_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
                    account_id = accounts['income']
                    price = order_line.price_unit * (1 - (order_line.discount or 0.0) / 100.0)
                    taxes = order_line.tax_id.compute_all(price, order_line.order_id.currency_id,
                                                          order_line.product_uom_qty, product=order_line.product_id,
                                                          partner=order_line.order_id.partner_shipping_id)
                    total_amount += taxes['total_void']
                    analytic_account_ids = rec.region_id.analytic_account_id.id
                    move_line_1 = {
                        'name': label_name,
                        'partner_id': rec.partner_id.id,
                        'account_id': account_id.id,
                        'credit': taxes['total_void'],
                        'debit': 0.00,
                        'journal_id': credit_journal_id.id,
                        'analytic_distribution': {
                            analytic_account_ids: 100
                        },
                    }
                    _logger.info("Credit side data calculated, Time: %s", fields.datetime.now())
                allocate_prod_id = self.env.ref('qshop_base.product_qwqer_shop_service_allocation_0')

                allocate_label_name = rec._get_computed_name(allocate_prod_id, state_journal_region)
                allocate_accounts = allocate_prod_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
                allocate_acc_id = allocate_accounts['income']
                move_line_2 = {
                    'name': allocate_label_name,
                    'partner_id': rec.partner_id.id,
                    'account_id': allocate_acc_id.id,
                    'credit': 0.0,
                    'debit': total_amount,
                    'journal_id': credit_journal_id.id,
                }
                _logger.info("Debit side data Calculated, Time: %s", fields.datetime.now())
                record = {
                    'partner_id': rec.partner_id.id,
                    'journal_id': credit_journal_id.id,
                    'company_id': self.env.user.company_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'date': date,
                    'move_type': "entry",
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)]
                }
                invoice = self.env['account.move'].sudo().create(record)
                _logger.info("Credit journal created %s, Time: %s", invoice, fields.datetime.now())
                invoice.sudo().post()
                _logger.info("Credit journal Posted, Time: %s", fields.datetime.now())
                rec.is_credit_journal_created = True
                rec.credit_journal_entry_id = invoice.id
                _logger.info("Sale order updated after credit journal creation, Time: %s", fields.datetime.now())
            else:
                raise UserError('Qwqer Shop Credit Journal Id not added')
