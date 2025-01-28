# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    qshop_invoice_tax_ids = fields.Many2many(comodel_name='account.tax', relation='qshop_invoice_tax',
                                            column1='partner1_id', column2='tax1_id',
                                            string='QWQER Shop Invoice Tax',domain="[('price_include','=', False)]")
    qshop_sale_order_tax_ids = fields.Many2many(comodel_name='account.tax', relation='qshop_sale_order_tax',
                                                column1='partner2_id', column2='tax2_id',
                                                string='QWQER Shop Sale Order Tax',domain="[('price_include','=', True)]")
    is_qshop_customer = fields.Boolean(string='Is Qshop Customer')
    qshop_sale_order_count = fields.Integer(string='QWQER Shop Sale Order Count', compute='_compute_sale_order_count')
    total_qshop_invoiced = fields.Monetary(string="Total QwqerShop Invoiced",groups='account.group_account_invoice', compute='_invoice_total')

    @api.onchange('service_type_id')
    def get_service_type_qshop(self):
        if self.service_type_id and self.service_type_id.is_qshop_service:
            self.is_qshop_customer = True
        else:
            self.is_qshop_customer = False

    def action_view_partner_qshop_orders(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('partner_id', 'child_of', self.id),]
        action['context'] = {'search_default_group_service_type_id': 1}
        return action

    def _compute_sale_order_count(self):
        """
           Compute the count of sale orders for each partner based on service types
           (delivery and QWQER shop services) and their child partners.
           """
        for rec in self:
            # Fetch all child partners, including the current partner.
            all_partners = rec.with_context(active_test=False).search([('id', 'child_of', rec.id)])
            # Prefetch 'parent_id' for better performance.
            all_partners.read(['parent_id'])
            # Group sale orders by partner for delivery services.
            sale_order_groups = self.env['sale.order'].read_group(
                domain=[
                    ('partner_id', 'in', all_partners.ids),
                    ('service_type_id.is_delivery_service', '!=', False)
                ],
                fields=['partner_id'], groupby=['partner_id']
            )

            # Group sale orders by partner for QWQER shop services.
            qshop_sale_order_groups = self.env['sale.order'].read_group(
                domain=[
                    ('partner_id', 'in', all_partners.ids),
                    ('service_type_id.is_qshop_service', '!=', False)
                ],
                fields=['partner_id'], groupby=['partner_id']
            )
            rec.sale_order_count = 0
            rec.qshop_sale_order_count = 0

            for group in sale_order_groups:
                partner = self.env['res.partner'].browse(group['partner_id'][0])
                if partner in all_partners:
                    partner.sale_order_count += group['partner_id_count']

            for group in qshop_sale_order_groups:
                partner = self.env['res.partner'].browse(group['partner_id'][0])
                if partner in all_partners:
                    partner.qshop_sale_order_count += group['partner_id_count']

    def action_view_partner_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('move_type', 'in', ('out_invoice', 'out_refund')),
                            ('partner_id', 'child_of', self.id)]
        action['context'] = {'default_move_type': 'out_invoice', 'move_type': 'out_invoice', 'journal_type': 'sale',
                             'search_default_unpaid': 1, 'search_default_group_service_type_id': 1, 'invoice_form': True}
        return action

    def _invoice_total(self):
        """Computes the total invoiced amount and QShop-specific invoiced amount
           for each partner, including their child partners"""
        for rec in self:
            # Retrieve all partners and their child IDs
            all_partner_ids = rec.with_context(active_test=False).search([('id', 'child_of', rec.id)]).ids
            # Fetch all relevant invoices for these partners
            invoices = self.env['account.move'].search([('partner_id', 'in', all_partner_ids),('state', 'not in', ['draft', 'cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund'))
            ])
            total_qshop_invoiced = 0
            total_invoiced = 0
            for invoice in invoices:
                if invoice.service_type_id.is_qshop_service:
                    total_qshop_invoiced += invoice.amount_untaxed
                else:
                    total_invoiced += invoice.amount_untaxed
            rec.total_qshop_invoiced = total_qshop_invoiced
            rec.total_invoiced = total_invoiced
        return self