from odoo import fields, models, api


class CashfreePaymentLine(models.Model):
    _name = 'cashfree.payment.line'
    _description = "Cashfree Payment Line"
    _rec_name = 'transfer'

    payment_id = fields.Many2one('account.payment', string='Payment', ondelete='cascade')
    transfer = fields.Char(string='Transfer ID')
    utr = fields.Char(string='UTR')
    payment_reference = fields.Char(string='Payment Reference')
    transaction_date = fields.Datetime(string='Transaction Date')
    processed_on = fields.Datetime(string='Processed On')
    payment_state = fields.Selection([
        ('initiate', 'Initiated'),
        ('pending', 'Pending'),
        ('fail', 'Failed'),
        ('success', 'Success'), ], string='Status')

    amount = fields.Float(string="Amount")

    @api.model
    def create(self, vals):
        vals['transfer'] = self.env['ir.sequence'].with_company(self.env.company.id).next_by_code('cashfree.payment.line')
        res = super(CashfreePaymentLine, self).create(vals)
        return res
