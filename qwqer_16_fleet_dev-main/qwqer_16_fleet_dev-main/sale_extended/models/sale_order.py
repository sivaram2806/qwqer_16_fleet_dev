# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
from lxml import etree


from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

INVOICE_STATUS = [
    ('upselling', 'Upselling Opportunity'),
    ('invoiced', 'Fully Invoiced'),
    ('to invoice', 'To Invoice'),
    ('no', 'Nothing to Invoice')
]


class SaleOrder(models.Model):
    """
       This model Sale.Order is inherited to make modification for delivery and qshop orders
       """
    _inherit = 'sale.order'

    industry_id = fields.Many2one(comodel_name='res.partner.industry')
    service_type_id = fields.Many2one(comodel_name='partner.service.type')
    order_sales_person = fields.Many2one(comodel_name='hr.employee')
    order_id = fields.Char(string='Order ID', index=True, copy=False)
    region_id = fields.Many2one(comodel_name='sales.region', string='Region')
    order_status_id = fields.Many2one(comodel_name='order.status', string='Order Status')
    order_date = fields.Datetime(string='Service Order Date')
    order_amount = fields.Monetary(string='Order Amount')
    discount_amount = fields.Monetary(string='Discount Amount')
    payment_id = fields.Char(string='Payment ID', copy=False)
    payment_status = fields.Char(string='Payment Status', copy=False)
    payment_mode_id = fields.Many2one(comodel_name='payment.mode', string='Payment Mode')
    estimated_distance = fields.Float(string='Estimated Distance')
    estimated_time = fields.Float(string='Estimated Time')
    pickup_distance = fields.Float(string='Pickup Distance')
    deliver_distance = fields.Float(string='Deliver Distance')
    weight = fields.Char(string='Weight')
    item_type = fields.Char(string='Item Type')
    description = fields.Char(string='Description')
    customer_type = fields.Selection(string='Customer Type', related='partner_id.customer_type', store=True)
    accept_sla = fields.Boolean(string='Accepted SLA Breached')
    pickup_sla = fields.Boolean(string='Pick up SLA Breached')
    pricing_plan = fields.Char(string='Pricing Plan')
    from_name = fields.Char(string='From Name')
    from_phone_no = fields.Char(string='From Phone No')
    from_address = fields.Char(string='From Address')
    sender_locality = fields.Char(string='Sender Locality')
    from_postal_code = fields.Char(string='From Postal Code')
    to_name = fields.Char(string='To Name')
    to_phone_no = fields.Char(string='To Phone No')
    to_address = fields.Char(string='To Address')
    receiver_locality = fields.Char(string='Receiver locality')
    to_postal_code = fields.Char(string='To Postal Code')
    driver_id = fields.Many2one(comodel_name='hr.employee', string='Driver ID')
    driver_uid = fields.Char(string="Driver ID", store=True)
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    driver_rating = fields.Char(string='Driver Rating')
    driver_comment = fields.Char(string='Driver Comments')
    customer_rating = fields.Char(string='Customer Rating')
    customer_feedback = fields.Char(string='Customer Feedback')
    customer_comment = fields.Char(string='Customer Comment')
    customer_phone = fields.Char(string="Customer Phone", store=True, related='partner_id.phone')
    order_accepted_date = fields.Datetime(string='Order Accepted Date')
    order_picked_up_date = fields.Datetime(string='Order Picked Up Date')
    order_delivered_date = fields.Datetime(string='Order Delivered Date')
    time_to_accept = fields.Float(string='Time to Accept')
    time_to_pickup = fields.Float(string='Time to Pickup')
    time_to_deliver = fields.Float(string='Time to Deliver')
    overall_order_time = fields.Float(string='Overall Order Time')
    order_source = fields.Char(string='Order Source')
    cancellation_comments = fields.Char(string='Cancellation Comments')
    total_amount = fields.Monetary(string='Amount')

    merchant_journal_ids = fields.One2many(comodel_name='account.move.line', inverse_name='merchant_order_id',
                                           string='merchant order', copy=False)
    is_merchant_journal = fields.Boolean(string='Is Merchant Journal Created', copy=False)
    merchant_journal_entry_id = fields.Many2one(comodel_name='account.move', string='Merchant Journal Entry',
                                                copy=False)
    merchant_order_amount = fields.Monetary(string='Merchant Amount Collected')
    merchant_payment_mode_id = fields.Many2one(comodel_name='payment.mode', string='Merchant Payment Mode')
    merchant_order_id = fields.Char("Merchant Order ID")

    state_id = fields.Many2one(comodel_name='res.country.state', related='region_id.state_id', store=True)
    is_so_updated = fields.Boolean(string="So Updated", default=False, copy=False)
    stop_count = fields.Char('Stop Count')
    stop_details = fields.Text("Stop Details")
    delivery_sla = fields.Boolean(string='Delivery SLA Breached')
    special_instruction = fields.Text("Special Instruction")
    scheduled = fields.Selection(selection=[('no', 'No'), ('yes', 'Yes')], string='Scheduled')
    customer_segment_id = fields.Many2one(comodel_name='partner.segment')
    """ inherited base invoice status for index adding"""
    invoice_status = fields.Selection(
        selection=INVOICE_STATUS,
        string="Invoice Status",
        compute='_compute_invoice_status',
        store=True, index=True, copy=False)
    is_manual_sale_order = fields.Boolean("Is Manual Sale Order", copy=False)
    total_qty = fields.Float(string='Total Qty', digits='Product Unit of Measure', readonly=True,
                             compute="_calculate_total_quantity")
    total_product_qty = fields.Float(string='Total Quantity', digits='Product Unit of Measure',
                                     compute="_calculate_total_quantity", readonly=True, store=True)
    order_source_sel = fields.Selection(
        selection=[('Admin', 'Admin'), ('Web', 'Web'), ('Android', 'Android'), ('API', 'API'), ('CSV', 'CSV'),
                   ('iOS', 'iOS'), ('QSHOP', 'QSHOP')], string="Order Source - Selection")
    order_qty = fields.Integer("Order Quantity")
    item_category_id = fields.Many2one(comodel_name="item.category", string="Item Category", copy=False)
    charges = fields.Json(string="Charges")
    product_line_id = fields.Many2one(comodel_name="product.lines", string="Product Lines")
    driver_payout_id = fields.Many2one('driver.payout', string='Driver Payout')
    # total_customer_under_salesperson = fields.Float()



    """sale_order_import fields"""

    from_sale_import = fields.Boolean(string='From Sale Import')
    is_new_customer = fields.Boolean("Is New customer", store=True, related='partner_id.is_new_customer')
    partner_create_date = fields.Datetime("Is New customer", store=True, related='partner_id.create_date')
    credit_journal_entry_id = fields.Many2one(comodel_name='account.move', string='Credit Journal Entry', copy=False)
    is_credit_journal_created = fields.Boolean(string='Is Credit Journal Created', index=True)

    # Consolidate Sale Invoice
    cs_invoice = fields.Many2one(comodel_name='consolidate.sale.invoice',
                                 string="Related Consolidate Sale Invoice")

    display_order_source = fields.Char(string="Display Order Source", compute='_compute_display_order_source' , store=True)

    _sql_constraints = [
        ('order_id_unique', 'unique (order_id)', 'The Order Id must be unique !')
    ]

    def _apply_permissions(self, node, permissions, fields):
        """Apply permissions to the given node."""
        if permissions['disable_all']:
            for field in fields:
                node.set(field, "0")
        else:
            for field in fields:
                node.set(field, "1" if permissions[field] else "0")

    def get_view(self, view_id=None, view_type='form', **options):
        """Extended to manage create/edit permissions for Sales Order based on user groups."""
        res = super().get_view(view_id, view_type, **options)
        if view_type not in ['form', 'tree']:
            return res

        doc = etree.XML(res['arch'])

        group_permissions = {
            'create': self.env.user.has_group(
                'sale_extended.enable_to_create_sale_order_group') or self.env.user.has_group(
                'base.group_system'),
            'edit': self.env.user.has_group('sale_extended.enable_to_edit_sale_order_group') or self.env.user.has_group(
                'base.group_system'),
            'disable_all': self.env.user.has_group(
                'account_base.account_read_receivables_accounting_group') or self.env.user.has_group(
                'account_base.auditor_menu_access_group'),
        }

        if view_type == 'form':
            for node in doc.xpath("//form[@string='Sales Order']"):
                self._apply_permissions(node, group_permissions, ['create', 'edit'])
        elif view_type == 'tree':
            for string in ['Quotation', 'Sales Orders']:
                for node in doc.xpath(f"//tree[@string='{string}']"):
                    self._apply_permissions(node, group_permissions, ['create'])

        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def default_get(self, field_list):
        res = super(SaleOrder, self).default_get(field_list)
        if self._context.get('default_is_manual_sale_order'):
            payment_mode = self.env['payment.mode'].search([('is_credit_payment', '=', True)], limit=1)
            price_list = self.env['product.pricelist'].search([], limit=1)
            res.update(
                {
                    "payment_mode_id": payment_mode.id,
                    'pricelist_id': price_list.id,
                    'payment_status': "Not Paid",
                    'order_qty': 1
                }
            )
        return res

    @api.onchange('service_type_id')
    def onchange_service_type_id(self):
        for rec in self:
            if rec.service_type_id and rec.partner_id.service_type_id and rec.service_type_id != rec.partner_id.service_type_id:
                raise ValidationError(_('Customer service type and Sale Order service type should be same'))

    @api.onchange('order_amount', 'discount_amount')
    def _onchange_order_amount(self):
        for rec in self:
            if rec.is_manual_sale_order and rec.order_amount > 0:
                rec.total_amount = rec.order_amount - rec.discount_amount

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.order_date:
                order.write({'date_order': order.order_date})
            if order.is_manual_sale_order and order.payment_mode_id.is_credit_payment:
                order.create_credit_order_journal()
        return res

    @api.model
    def bulk_credit_sale_order_creation(self):
        date = False
        date_str = self.env.company.credit_journal_date
        if date_str:
            date = date_str.strftime("%Y-%m-%d")
        limit = self.env.company.credit_journal_limit
        if date and limit:
            so_ids = self.env['sale.order'].search(
                [('order_status_id.is_cancel_order', '!=', True), ('create_date', '>=', date),
                 ('state', '!=', 'cancel'),
                 ('payment_mode_id.is_credit_payment', '=', True), ('customer_type', '=', 'b2b'),
                 ('is_credit_journal_created', '=', False), ('company_id', '=', self.env.company.id)], order='id asc',
                limit=int(limit))
            for so in so_ids:
                so.create_credit_order_journal()

    def create_credit_order_journal(self):
        """create journal for credit sale orders"""
        _logger.info("Inside credit journal create function, Time: %s", fields.datetime.now())
        for rec in self:
            date = rec.date_order
            credit_journal_id = self.env.company.credit_journal_id
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
                allocate_prod_id = self.env.ref('sale_extended.product_delivery_service_allocation_0')

                allocate_accounts = allocate_prod_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
                allocate_acc_id = allocate_accounts['income']
                allocate_label_name = rec._get_computed_name(allocate_prod_id, state_journal_region)
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
                try:
                    invoice = self.env['account.move'].sudo().create(record)
                except Exception as e:
                    raise UserError(e)
                _logger.info("Credit journal created %s, Time: %s", invoice, fields.datetime.now())
                invoice.sudo().post()
                _logger.info("Credit journal Posted, Time: %s", fields.datetime.now())
                rec.is_credit_journal_created = True
                rec.credit_journal_entry_id = invoice.id
                _logger.info("Sale order updated after credit journal creation, Time: %s", fields.datetime.now())
            else:
                raise UserError('Credit Journal Id not added')

    def _get_computed_name(self, product_id, state_journal):
        self.ensure_one()
        if not product_id:
            return ''
        if self.partner_id.lang:
            product = product_id.with_context(lang=self.partner_id.lang)
        else:
            product = product_id
        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if state_journal.delivery_journal_id.type == 'sale':
            if product.description_sale:
                values.append(product.description_sale)
        return '\n'.join(values)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.region_id = rec.partner_id.region_id.id
                rec.order_sales_person = rec.partner_id.order_sales_person.id
                rec.partner_invoice_id = rec.partner_id.id
                rec.partner_shipping_id = rec.partner_id.id
                rec.service_type_id = rec.partner_id.service_type_id.id
                rec.industry_id = rec.partner_id.industry_id.id
                rec.customer_segment_id = rec.partner_id.segment_id.id
                rec.product_line_id = rec.partner_id.product_line_id.id


    @api.depends('order_line.product_uom_qty')
    def _calculate_total_quantity(self):
        """
        Compute the total quantity of the SO.
        """
        for order in self:
            total_qty = 0.0
            for line in order.order_line:
                total_qty += line.product_uom_qty
            order.update({
                'total_qty': total_qty,
                'total_product_qty': total_qty,
            })

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if 'partner_id' in vals:
            for rec in self:
                if rec.partner_id.product_line_id:
                    rec.product_line_id = rec.partner_id.product_line_id.id
                else:
                    rec.product_line_id = False

        if res.is_manual_sale_order:
            if res.service_type_id.is_qshop_service:
                shop_sequence_code = 'qshop.order.id.sequence'
                sequence_order_id = self.env['ir.sequence'].next_by_code(shop_sequence_code) or '/'
            else:
                delivery_sequence_code = 'delivery.order.id.sequence'
                sequence_order_id = self.env['ir.sequence'].next_by_code(delivery_sequence_code) or '/'
            res.order_id = sequence_order_id
        if not res.is_manual_sale_order:
            res.order_qty = res.total_product_qty
        try:
            for rec in res:
                if vals.get('payment_mode_id') or vals.get('state') == 'cancel':
                    if (
                            rec.partner_id.customer_type == 'b2b' and
                            rec.partner_id.service_type_id.is_delivery_service and
                            rec.payment_mode_id.is_credit_payment
                    ):
                        self._manage_customer_balance(rec.partner_id)
        except Exception as e:
            _logger.error("Error in Sale Order Create: %s", str(e))
        return res

    def _manage_customer_balance(self, partner_id):
        """Helper method to manage customer balance."""
        try:
            # Check if a balance record already exists
            customer_balance = self.env['application.customer.balance'].search(
                [('partner_id', '=', partner_id.id)], limit=1
            )
            if not customer_balance:
                # Create a new customer balance record
                self.env['application.customer.balance'].create({
                    'partner_id': partner_id.id,
                    'time_balance_update': fields.datetime.now(),
                    'cus_id': partner_id.customer_ref_key,
                })
        except Exception as e:
            _logger.error("Error in Customer Balance Management: %s", str(e))

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        try:
            for rec in self:
                if vals.get('state') == 'cancel':
                    if (
                            rec.partner_id.customer_type == 'b2b' and
                            rec.partner_id.service_type_id.is_delivery_service and
                            rec.payment_mode_id.is_credit_payment
                    ):
                        self._manage_customer_balance(rec.partner_id)
        except Exception as e:
            _logger.error("Error in Sale Order Write: %s", str(e))
        return res

    @api.onchange('driver_id')
    def onchange_driver_id(self):
        if self.driver_id:
            self.driver_uid = self.driver_id.driver_uid
            self.driver_name = self.driver_id.name
            self.driver_phone = self.driver_id.work_phone or self.driver_id.mobile_phone

    # @api.onchange('amount', 'partner_id', 'region_id', 'order_qty')
    # def _onchange_amount(self):
    #     for rec in self:
    #         rec.order_line = False
    #         if rec.amount > 0 and rec.service_type.is_delivery_service:
    #             order_line_vals = rec.get_order_line_vals()
    #             product = rec.env.company.product_id
    #             if product:
    #                 order_line_vals.update({
    #                     'product_id': product.id,
    #                     'product_uom': product.uom_id.id,
    #                     'name': product.name
    #                 })
    #                 self.order_line = [(0, 0, order_line_vals)]

    # self.order_line = False
    # product = self.env['ir.config_parameter'].sudo().get_param('product_id')

    # if rec.service_type == 'qwqershop':
    #     product = self.env['ir.config_parameter'].sudo().get_param('qwqershop_product_id')
    # product_rec = self.env['product.product'].search([('id', '=', product)], limit=1)

    # tax_list = []
    # if rec.region_id:
    #     state_rec = rec.region_id.state_id
    # else:
    #     state_rec = rec.partner_id.state_id
    # state_journal = self.env['state.journal'].search([('state_id', '=', state_rec.id)], limit=1)
    #
    # if rec.partner_id.customer_type == 'b2b':
    #     for b2b_tax in rec.partner_id.b2b_sale_order_tax_ids:
    #         tax_list.append(b2b_tax)
    # elif rec.partner_id.customer_type == 'b2c':
    #     for b2c_tax in state_journal.tax_b2c_sale_order:
    #         tax_list.append(b2c_tax)
    # vals = {'product_id': product_rec.id,
    #         'product_uom': product_rec.uom_id.id,
    #         'name': product_rec.name,
    #         'product_uom_qty': rec.order_qty,
    #         'price_unit': rec.amount,
    #         'tax_id': [(4, i.id) for i in tax_list],
    #         'service_type': rec.service_type
    #         }

    def get_order_line_vals(self):
        tax_list = []
        if self.region_id:
            state_rec = self.region_id.state_id
        else:
            state_rec = self.partner_id.state_id
        state_journal = self.env['state.journal'].search([('state_id', '=', state_rec.id)], limit=1)

        if self.partner_id.customer_type == 'b2b':
            for b2b_tax in self.partner_id.b2b_sale_order_tax_ids:
                tax_list.append(b2b_tax)
        elif self.partner_id.customer_type == 'b2c':
            for b2c_tax in state_journal.tax_b2c_sale_order:
                tax_list.append(b2c_tax)
        vals = {
            'product_uom_qty': self.order_qty,
            'price_unit': self.total_amount,
            'tax_id': [(4, i.id) for i in tax_list],
            'service_type_id': self.service_type_id.id
        }
        return vals

    def action_cancel_sale_order(self):
        for rec in self:
            rec.reverse_credit_sale_journal()
            rec.reverse_merchant_journal()
            rec._action_cancel()

    def reverse_credit_sale_journal(self):
        for rec in self:
            if rec.credit_journal_entry_id:
                move_pool = self.env['account.move'].sudo().browse(rec.credit_journal_entry_id.id)
                if move_pool:
                    move_pool.button_draft()
                    move_pool.button_cancel()
                rec.is_credit_journal_created = False
                rec.credit_journal_entry_id = False

    def reverse_merchant_journal(self):
        for rec in self:
            if rec.merchant_order_amount > 0:
                move_pool = self.env['account.move'].sudo().browse(rec.merchant_journal_entry_id.id)
                if move_pool:
                    move_pool.button_draft()
                    move_pool.button_cancel()
                    # move_pool.sudo().unlink()
                rec.is_merchant_journal = False
                rec.merchant_journal_entry_id = False

    def action_confirm_quotation(self):
        for i in self:
            if i.state != 'sale':
                i.action_confirm()

    def action_update_analytic_account(self):
        for sale in self:
            if sale.region_id and sale.region_id.analytic_account_id:
                sale.analytic_account_id = sale.region_id.analytic_account_id.id

    def update_customer_industry(self):
        """ script to update the Customer Industry"""
        for rec in self:
            if rec.partner_id and rec.partner_id.industry_id:
                rec.industry_id = rec.partner_id and rec.partner_id.industry_id.id or False
            else:
                if rec.partner_id.opportunity_count > 0:
                    for opportunity in rec.partner_id.opportunity_ids:
                        if opportunity.industry_id:
                            rec.industry_id = opportunity.industry_id.id or False
                            rec.partner_id.industry_id = opportunity.industry_id.id or False

    def update_state(self):
        for rec in self:
            if rec.invoice_status == "to invoice":
                rec.invoice_status = "invoiced"

    def _reverse_shop_merchant_wallet_entry(self):
        for rec in self:
            wallet_config = self.env['customer.wallet.config'].search([], limit=1)
            if wallet_config:
                moves = self.merchant_wallet_move_id

                refund_method = "cancel"
                # Create default values.
                default_values_list = []
                for move in moves:
                    ref = _('Merchant Order Cancelled - %s') % (move.wallet_order_id)
                    order_transaction_no = _('QMWRE_%s') % (move.wallet_transaction_ref_id)
                    default_values = {
                        'ref': ref,
                        'date': fields.Date.today(),
                        'journal_id': move.journal_id.id,
                        'invoice_payment_term_id': None,
                        'wallet_order_id': move.wallet_order_id,
                        'service_type_id': move.service_type_id.id,
                        'order_transaction_no': order_transaction_no
                    }
                    default_values_list.append(default_values)
                batches = [
                    [self.env['account.move'], [], True],  # Moves to be cancelled by the reverses.
                    [self.env['account.move'], [], True],  # Others.
                ]
                for move, default_vals in zip(moves, default_values_list):
                    is_auto_post = bool(default_vals.get('auto_post'))
                    is_cancel_needed = not is_auto_post and refund_method in ('cancel', 'modify')
                    batch_index = 0 if is_cancel_needed else 1
                    batches[batch_index][0] |= move
                    batches[batch_index][1].append(default_vals)
                # Handle reverse method.
                moves_to_redirect = self.env['account.move']
                for moves, default_values_list, is_cancel_needed in batches:
                    new_moves = moves.sudo()._reverse_moves(default_values_list, cancel=is_cancel_needed)

                    new_moves.line_ids.name = "Merchant Amount Refunded"
            rec.merchant_wallet_move_id = False

    @api.depends('is_manual_sale_order', 'order_source', 'order_source_sel')
    def _compute_display_order_source(self):
        for rec in self:
            if rec.is_manual_sale_order:
                rec.display_order_source = rec.order_source_sel
            else:
                rec.display_order_source = rec.order_source