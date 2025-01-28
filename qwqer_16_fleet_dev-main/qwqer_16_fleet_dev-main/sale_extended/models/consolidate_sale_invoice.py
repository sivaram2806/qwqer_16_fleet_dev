# -*- coding: utf-8 -*-
from itertools import product

from odoo import models, fields, api, _
from datetime import datetime, time
import pytz
import logging
import itertools

_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError


class ConsolidateSaleInvoice(models.Model):
    _name = 'consolidate.sale.invoice'
    _description = 'model for creating consolidate invoice for the sale orders'
    _rec_name = 'rec_name'
    _order = "id desc"

    rec_name = fields.Char("Name")
    customer_id = fields.Many2one(comodel_name='res.partner', required=True)
    from_date = fields.Date(string='From Date', default=fields.Date.context_today, required=True)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)
    order_ids = fields.One2many('sale.order', 'cs_invoice')
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    date = fields.Date(string='Invoice Date', default=fields.Date.context_today)
    is_consolidated_inv_created = fields.Boolean()
    vat = fields.Char(string='GSTIN', related='customer_id.vat')
    payment_mode_ids = fields.Many2many(comodel_name='payment.mode', string='Payment Mode')
    region_ids = fields.Many2many(comodel_name='sales.region', string='Region')
    state_ids = fields.Many2many(comodel_name='res.country.state', string='State Region',
                                 domain="[('country_id', '=?', country_id)]")
    invoice_id = fields.Many2one(comodel_name='account.move', string="Invoice")
    invoice_status = fields.Selection(related='invoice_id.state', store=True)
    service_type_id = fields.Many2one(comodel_name='partner.service.type', domain=[('is_delivery_service', '=', True)])
    country_id = fields.Many2one(comodel_name='res.country', string='Country',
                                 default=lambda self: self.env.company.country_id)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),], string='Status', default='draft', track_visibility='onchange',compute="invoice_state_change")

    @api.model
    def create(self, vals):
        sequence_number = self.env['ir.sequence'].next_by_code('invoice.consolidated.sequence') or _('New')
        vals.update({'rec_name': sequence_number})
        res = super(ConsolidateSaleInvoice, self).create(vals)
        return res

    def load_sale_order(self):
        local = pytz.timezone(self.env.user.tz or 'UTC')
        # Process `from_date` (start of the day in UTC)
        from_date = local.localize(datetime.combine(self.from_date, time.min)).astimezone(pytz.utc)
        _logger.info("UTC From date %s", from_date)

        # Process `to_date` (end of the day in UTC)
        to_date = local.localize(datetime.combine(self.to_date, time.max)).astimezone(pytz.utc)
        _logger.info("UTC To date %s", to_date)

        no_credit_domain = [('partner_id', '=', self.customer_id.id),
                            ('date_order', '>=', from_date),
                            ('date_order', '<=', to_date),
                            ('state', '=', 'sale'),
                            ('invoice_status', '!=', 'invoiced'),
                            ('service_type_id', '=', self.service_type_id.id),
                            ('payment_mode_id', 'in', self.payment_mode_ids.ids),
                            ('is_credit_journal_created', '=', False)]
        if self.region_ids:
            no_credit_domain.append(('region_id', 'in', self.region_ids.ids))
        if self.state_ids:
            no_credit_domain.append(('region_id.state_id', 'in', self.state_ids.ids))
        fetch_query = self.env['sale.order']._where_calc(no_credit_domain)
        from_clause, where_clause, where_clause_params = fetch_query.get_sql()
        sql = """
                SELECT sale_order.order_id as so_id FROM %(from)s WHERE %(where)s 
                """ % {'from': from_clause, 'where': where_clause}
        self.env.cr.execute(sql, where_clause_params)
        no_credit_orders = list(itertools.chain(*self.env.cr.fetchall()))
        if no_credit_orders:
            raise ValidationError(_("Credit journal is not created for the sale orders %s" % no_credit_orders))
        else:
            credit_domain = [('partner_id', '=', self.customer_id.id),
                             ('date_order', '>=', from_date),
                             ('date_order', '<=', to_date),
                             ('service_type_id', '=', self.service_type_id.id),
                             ('state', '=', 'sale'),
                             ('invoice_status', '!=', 'invoiced'),
                             ('payment_mode_id', 'in', self.payment_mode_ids.ids)]
            if self.region_ids:
                credit_domain.append(('region_id', 'in', self.region_ids.ids))
            if self.state_ids:
                credit_domain.append(('region_id.state_id', 'in', self.state_ids.ids))
            fetch_query = self.env['sale.order']._where_calc(credit_domain)
            from_clause, where_clause, where_clause_params = fetch_query.get_sql()
            sql = """
                        SELECT sale_order.id as so_id FROM %(from)s WHERE %(where)s 
                        """ % {'from': from_clause, 'where': where_clause}
            self.env.cr.execute(sql, where_clause_params)
            res = list(itertools.chain(*self.env.cr.fetchall()))
            self.order_ids = [(6, 0, res)]

    def generate_bulk_invoice(self):
        allocate_prod_id = self.env.ref('sale_extended.product_delivery_service_allocation_0')
        line_list = []

        for region in self.order_ids.mapped('region_id'):
            region_vise_sale_order = self.order_ids.filtered(lambda so: so.region_id.id == region.id)
            amount_total = sum(region_vise_sale_order.mapped('amount_total')) or 0.0
            total_count = len(region_vise_sale_order) or 0
            if amount_total:
                move_line = {
                    'product_id': self.env['product.product'].search([('id', '=', allocate_prod_id.id)], limit=1).id,
                    'name': 'Charges towards the delivery services (%s nos) for the duration %s to %s'
                            % (total_count, self.from_date.strftime('%d/%m/%Y'), self.to_date.strftime('%d/%m/%Y')),
                    'price_unit': amount_total,
                    'tax_ids': [(6, 0,
                                 self.customer_id.b2b_sale_order_tax_ids.ids)] if self.service_type_id.is_delivery_service else [
                        (6, 0, self.customer_id.qshop_sale_order_tax_ids.ids)],
                    'analytic_distribution': {
                        region.analytic_account_id.id: 100
                    },
                    'is_so_inv_line': True
                }
                line_list.append((0, 0, move_line))
        state_journal = self.env['state.journal'].search([('state_id', '=', self.customer_id.region_id.state_id.id)])
        if not state_journal.delivery_journal_id:
            raise UserError('Journals not added in state Journal')
        if line_list:
            try:
                invoice_id = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'journal_id': state_journal.delivery_journal_id.id if self.service_type_id.is_delivery_service else state_journal.qshop_journal_id.id,
                    'invoice_date': self.date,
                    'partner_id': self.customer_id.id,
                    'service_type_id':self.service_type_id.id,
                    'state': 'draft',
                    'invoice_line_ids': line_list,
                    'consolidated_invoice_id': self.id,
                    'payment_mode_id': self.payment_mode_ids.ids[0],
                    'selling_partner_id': self.customer_id.id if self.service_type_id.is_qshop_service else False

                })
                self.order_ids.order_line.invoice_lines = [(6, 0, invoice_id.invoice_line_ids.ids)]
                self.order_ids.invoice_status = "invoiced"
                self.is_consolidated_inv_created = True
                if not invoice_id:
                    move_list = self.order_ids.mapped('invoice_ids')
                    if move_list and move_list[0]:
                        invoice_id = move_list[0].id
                self.invoice_id = invoice_id
                tree_view = self.env.ref('account.view_invoice_tree')
                form_view = self.env.ref('account.view_move_form')
                return {
                    'name': _('Invoices'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                    'domain': [('id', '=', invoice_id.id)],
                    'target': 'current',
                }
            except Exception as e:
                raise UserError(_(e))

    def write(self, vals):
        order_change = False
        if vals.get('order_ids'):
            order_change = True
        ordr_list1 = self.order_ids.ids
        res = super(ConsolidateSaleInvoice, self).write(vals)
        ordr_list2 = self.order_ids.ids
        removed_ordr_list = [x for x in ordr_list1 if x not in ordr_list2]
        removed_list = self.env['sale.order'].browse(removed_ordr_list)
        removed_list.order_line.invoice_lines = False
        removed_list.invoice_status = "to invoice"
        if order_change:
            if self.invoice_id:
                allocate_prod_id = self.env.ref('sale_extended.product_delivery_service_allocation_0')
                credit_orders = self.order_ids.filtered(lambda r: r.is_credit_journal_created == True)
                if credit_orders:
                    self.update_invoice_lines(credit_orders, allocate_prod_id)
                self.order_ids.order_line.invoice_lines = [(6, 0, self.invoice_id.invoice_line_ids.ids)]
                self.order_ids.invoice_status = "invoiced"
        return res

    def update_invoice_lines(self, orders, product_id):
        if orders:
            for region in orders.mapped('region_id'):
                region_vise_sale_order = self.order_ids.filtered(lambda so: so.region_id.id == region.id)
                total_untaxed_amount = sum(region_vise_sale_order.mapped('amount_untaxed')) or 0.0
                total_count = len(region_vise_sale_order) or 0
                inv_line = self.invoice_id.invoice_line_ids.filtered(lambda r: r.product_id == product_id)
                for line in inv_line:
                    if line.is_so_inv_line:
                        line_result = line.with_context(check_move_validity=False).write({
                            'price_unit': total_untaxed_amount,
                            'name': 'Charges towards the delivery services (%s nos) for the duration %s to %s'
                                    % (total_count, self.from_date.strftime('%d/%m/%Y'),
                                       self.to_date.strftime('%d/%m/%Y')),
                            'is_so_inv_line': True,
                        })
                self.invoice_id._compute_tax_totals()

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.order_ids and len(self.order_ids) > 0:
            self.order_ids = [(5,)]
            return {
                'warning': {'title': "Warning",
                            'message': "Sale orders removed for the previously selected customer. Please click on Load SO button for loading sale orders for currently selected customer"},
            }

    @api.depends('invoice_status')
    def invoice_state_change(self):
        for rec in self:
            if rec.invoice_status:
                if rec.invoice_status in ['draft','posted']:
                    rec.state = 'confirm'
                elif rec.state == 'cancel':
                    rec.state = 'draft'
                else:
                    rec.state = 'draft'
            else:
                rec.state = 'draft'