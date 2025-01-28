from odoo import fields, models,api,_


class WalletAddAmount(models.TransientModel):
    _name = 'wallet.add.amount'
    _description = 'models for adding amount to customer wallet'



    @api.model
    def default_get(self, field_list):
        res = super(WalletAddAmount, self).default_get(field_list)
        wallet_config = self.env['customer.wallet.config'].search([], limit=1)

        sequence_number = self.env['ir.sequence'].next_by_code('manual.wallet.recharge.sequence') or _('New')
        res.update(
            {
                "order_transaction_no": sequence_number
            }
        )
        if wallet_config:
            res.update(
                {
                    "journal_id": wallet_config.journal_id.id or False,
                    "credit_account_id":wallet_config.default_credit_account_id or False
                }
            )

        return res

    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    journal_id = fields.Many2one(comodel_name="account.journal", string='Wallet Journal',)
    credit_account_id = fields.Many2one(comodel_name="account.account", string='Credit Account')
    debit_account_id = fields.Many2one(comodel_name="account.account", string='Debit Account')
    amount = fields.Float(string="Amount")
    move_id = fields.Many2one(comodel_name="account.move", string='Wallet entry')
    comments = fields.Text(string="Remarks")
    order_transaction_no = fields.Char(string='Transaction Reference No')

    def action_add_amount(self):
        for rec in self:
            if rec.amount > 0:
                move_line_1 = {
                    'partner_id': rec.partner_id.id,
                    'account_id': rec.debit_account_id.id,
                    'credit': 0.0,
                    'debit': rec.amount,
                    'journal_id': rec.journal_id.id,
                    'name': 'Recharge',
                }
                move_line_2 = {
                    'partner_id': rec.partner_id.id,
                    'account_id': rec.credit_account_id.id,
                    'credit': rec.amount,
                    'debit': 0.0,
                    'journal_id': rec.journal_id.id,
                    'name': "Recharge",
                }
                date = rec.create_date
                record = {
                    'partner_id': rec.partner_id.id,
                    'journal_id': rec.journal_id.id,
                    'company_id': self.env.user.company_id.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'date': date,
                    'ref': "Recharge",
                    'move_type': "entry",
                    'comments':rec.comments,
                    'order_transaction_no': self.order_transaction_no,
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                }
                invoice = self.env['account.move'].sudo().create(record)
                invoice.sudo().post()
                rec.move_id = invoice.id
