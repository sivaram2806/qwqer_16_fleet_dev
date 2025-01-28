from odoo import fields, models, api, _


class AccountMoves(models.Model):
    _inherit = 'account.move'


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMoves, self)._onchange_partner_id()
        self.update({
            'sales_person_id': self.partner_id.order_sales_person.id,
        })
        return res

    def action_register_payment(self):
        invoice_payment = super(AccountMoves, self).action_register_payment()
        invoice_payment['context'] = invoice_payment.get('context', {})
        invoice_payment['context'].update({
            'default_region_id': self.region_id.id if self.region_id else False,
            'default_sales_person_id': self.sales_person_id.id if self.sales_person_id else False,
        })

        return invoice_payment