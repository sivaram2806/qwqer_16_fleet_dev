from odoo import models, fields


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    payment_account_id = fields.Many2one(
        comodel_name='account.account',
        check_company=True,
        copy=False,
        ondelete='restrict',
        domain="[('deprecated', '=', False), "
                "('company_id', '=', company_id), "
                "('account_type', 'not in', ('asset_receivable', 'liability_payable')), "
                "'|', ('account_type', 'in', ('asset_current', 'liability_current', 'income_other')), ('id', '=', parent.default_account_id)]"
    )