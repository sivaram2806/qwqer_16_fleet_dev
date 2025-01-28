from odoo import models, fields, api, _


class IndividualInvoice(models.TransientModel):
    _name = 'invoice.individual'
    _description = 'Invoice Individual'
    _rec_name = 'customer_id'

    @api.onchange('customer_id', 'from_date', 'to_date')
    def _onchange_customer(self):
        order_list = []
        orders = self.env['sale.order'].search([('partner_id', '=', self.customer_id.id),
                                                ('date_order', '>=', self.from_date),
                                                ('date_order', '<=', self.to_date),
                                                ('state', '=', 'sale')])
        for i in orders:
            if not i.invoice_ids:
                order_list.append(i.id)
        self.order_ids = [(6, 0, order_list)]

    customer_id = fields.Many2one('res.partner', required=True)
    from_date = fields.Date(string='From Date', default=fields.Date.context_today, required=True)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)
    order_ids = fields.Many2many('sale.order')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    date = fields.Date(string='To Date', default=fields.Date.context_today)
    is_invoice_created = fields.Boolean()


    def generate_invoice(self):
        inv_list = []
        for sale_line in self.order_ids:
            invoices = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'invoice_date': self.date,
                'state': 'draft',
                'invoice_line_ids': [(0, 0, {
                    'product_id': rec.product_id.id,
                    'price_unit': rec.price_subtotal,
                    'tax_ids': rec.tax_id.ids,
                }) for rec in sale_line.order_line],
                'order_line_ids': [(6, 0, self.order_ids.ids)]
            })
            inv_list.append(invoices)
            for j in invoices.order_line_ids:
                for lines in j.order_line:
                    lines.write({'invoice_lines': [(6, 0, invoices.invoice_line_ids.ids)]})
        self.is_invoice_created = True
        tree_view = self.env.ref('account.view_invoice_tree')
        form_view = self.env.ref('account.view_move_form')
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', 'in', [x.id for x in inv_list])],
            'target': 'current',
        }