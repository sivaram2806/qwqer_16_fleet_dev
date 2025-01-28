from odoo import fields, models,api,_
from odoo.exceptions import UserError, Warning, ValidationError


class WalletOffsetWizard(models.TransientModel):
    _name = 'wallet.offset.wizard'
    
    
    @api.model
    def default_get(self, fields):
        res = super(WalletOffsetWizard, self).default_get(fields)
        account_move_record = self.env['account.move'].browse(self._context.get('active_id'))
        if account_move_record:
            res.update({'deduction_amount':account_move_record.amount_residual,
                        'balance_amount':account_move_record.partner_id.wallet_balance})
            
            
        return res
    
    balance_amount = fields.Float(string='Balance Amount')
    deduction_amount = fields.Float(string='Deduction Amount for Payment')
    
    
    
    def action_create_journal(self):
        for rec in self:
            wallet_config = self.env['customer.wallet.config'].search([], limit=1)
            if wallet_config and wallet_config.journal_id and wallet_config.wallet_payment_method_id:
                if self._context.get('active_model') == 'account.move':
                    invoice = self.env['account.move'].browse(self._context.get('active_id',False))
                    if invoice.partner_id.is_wallet_active: 
                        if rec.deduction_amount <= invoice.partner_id.wallet_balance:
                        
                            payment = self.env['account.payment'].create({
                                        'partner_type':'customer',
                                        'payment_type':'inbound',
                                        'service_type_id':invoice.service_type_id.id,
                                        'partner_id' :invoice.partner_id.id,
                                        'amount' :rec.deduction_amount,
                                        'journal_id':wallet_config.journal_id.id,
                                        'payment_method_id':wallet_config.wallet_payment_method_id.id,
                                        'ref':'Wallet-'+invoice.name,
                                        # 'invoice_ids':invoice
                                        })
                            if rec.deduction_amount <= invoice.partner_id.wallet_balance:
                            
                                payment.action_post()
                            else:
                                raise ValidationError(_('Insufficient wallet balance.'))
                        else:
                            raise ValidationError(_('Insufficient wallet balance.'))
                    else:
                        raise ValidationError(_('You cannot perform this operation,customer wallet account is not active.'))
            else:
                raise ValidationError(_('Please configure wallet journal and payment method.'))
    