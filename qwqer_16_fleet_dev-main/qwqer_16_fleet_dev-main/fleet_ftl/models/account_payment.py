# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    work_order_id = fields.Many2one(comodel_name='work.order', string='Work Order No.', copy=False)
    work_order_ids = fields.Many2many(comodel_name='work.order', string='Work Order(s)', copy=False)
    work_order_amount = fields.Float(string='Work Order Amount')
    work_order_shipping_address = fields.Text(string='Work Order Shipping Address')

    tax_tds_id = fields.Many2one('account.tax', string="TDS", domain=[('is_tds', '=', True)])
    tds_amount = fields.Monetary(string="TDS Amount", currency_field='currency_id', store=True)

    @api.onchange('work_order_ids')
    def onchange_work_order(self):
        for rec in self:
            if rec.work_order_ids:
                rec.work_order_amount = sum(rec.work_order_ids.mapped("total_amount"))
                rec.work_order_shipping_address = rec.work_order_ids[0].shipping_address
            else:
                rec.work_order_amount = False
                rec.work_order_shipping_address = False


    @api.depends('move_id.line_ids.matched_debit_ids', 'move_id.line_ids.matched_credit_ids')
    def _compute_stat_buttons_from_reconciliation(self):
        super(AccountPayment, self)._compute_stat_buttons_from_reconciliation()
        for pay in self:
            pay.work_order_ids = [(6, 0, pay.reconciled_invoice_ids.mapped('work_order_ids').ids)]


    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        move_line = super()._prepare_move_line_default_vals(write_off_line_vals)

        # checking if payment has TDS
        if self.tax_tds_id:
            # modifying counter Receivable / Payable entry with TDS
            move_line[0]['amount_currency'] = move_line[0].get('amount_currency') + abs(self.tds_amount)
            move_line[0]['credit'] = move_line[0].get('credit') + self.tds_amount
            move_line[1]['tax_ids'] = [Command.set(self.tax_tds_id.ids)]
        return move_line