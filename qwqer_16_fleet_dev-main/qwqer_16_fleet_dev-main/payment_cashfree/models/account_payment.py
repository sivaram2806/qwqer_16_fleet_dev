import base64
import os

from odoo import models, fields, api, _
from cashfree_sdk.payouts import Payouts
from cashfree_sdk.payouts.beneficiary import Beneficiary
from cashfree_sdk.payouts.transfers import Transfers
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import json
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_cashfree = fields.Boolean(string='Is Work Order Payment?', default=False)
    cashfree_payment_line_ids = fields.One2many('cashfree.payment.line', 'payment_id', copy=False)

    is_cashfree_payin = fields.Boolean(string='Is Cashfree Payin', default=False)

    def action_post(self):
        for payment in self.filtered(lambda p: p.is_cashfree_payin and p.state == 'draft'):
            config = self.env['cash.free.configuration'].search([('payment_type', '=', 'inbound')], limit=1)
            if not config.is_validated:
                rec = super(AccountPayment, self).action_post()
                move_lines = payment.line_ids.filtered(lambda line: not line.reconciled)
                cf_payin = self.env['cashfree.payin'].search([('payment_id', '=', payment.id)])
                cf_payin.state = 'paid'
                for line in move_lines:
                    cf_payin.invoice_id.js_assign_outstanding_line(line.id)
                return rec
        return super(AccountPayment, self).action_post()

    def get_cashfree_credentials(self):
        cashfree_id = self.env['cash.free.credentials'].sudo().search([
            ("company_id", "=", self.company_id.id)], limit=1)
        if not cashfree_id:
            raise UserError("Cashfree configuration is missing, Please contact System Administrator")
        if not cashfree_id.public_key:
            raise UserError("Cashfree Authentication Key is missing, Please contact System Administrator")
        return cashfree_id

    def update_cashfree_payment_status(self):
        for rec in self:
            if rec.is_cashfree:
                cashfree_id = rec.get_cashfree_credentials()
                app_id = cashfree_id.payout_app_id
                app_key = cashfree_id.payout_key
                env = self.env.company.cashfree_env
                Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
                try:
                    get_transfer_status_response = Transfers.get_transfer_status(
                        transferId=rec.cashfree_payment_line_ids.transfer)
                    response = json.loads(get_transfer_status_response.content)

                    if response['status'] == 'SUCCESS':
                        if response['data']['transfer']['status'] == 'SUCCESS':
                            rec.cashfree_payment_line_ids.write({'payment_state': 'success',
                                                                 'payment_reference': response['data']['transfer'][
                                                                     'referenceId'],
                                                                 'utr': response['data']['transfer']['utr'],
                                                                 'processed_on': response['data']['transfer'][
                                                                     'processedOn']})

                        elif response['data']['transfer']['status'] in ('PENDING', 'PROCESSING'):
                            rec.cashfree_payment_line_ids.write({'payment_state': 'pending',
                                                                 'payment_reference': response['data']['transfer'][
                                                                     'referenceId'],
                                                                 'processed_on': response['data']['transfer'][
                                                                     'processedOn']})

                        else:
                            rec.cashfree_payment_line_ids.write({'payment_state': 'fail',
                                                                 'payment_reference': response['data']['transfer'][
                                                                     'referenceId'],
                                                                 'processed_on': response['data']['transfer'][
                                                                     'processedOn']})
                            rec.action_draft()
                            rec.cancel()

                    elif response['status'] in ('PENDING', 'PROCESSING'):
                        rec.cashfree_payment_line_ids.write({'payment_state': 'pending'})

                    else:
                        rec.cashfree_payment_line_ids.write({'payment_state': 'fail'})
                        rec.action_draft()
                        rec.cancel()

                except Exception as e:
                    error_string = repr(e)
                    _logger.error(f"err occurred {error_string}")
                    message = "Cashfree Update Status Failed\nError:%s" % error_string
                    raise ValidationError(_(message))

    @api.model
    def update_advance_cashfree_payment_status(self):
        """
        To update payment status of cashfree
        """
        date_to = fields.datetime.now()
        date_from = (date_to - timedelta(days=15)).replace(hour=0, minute=0, second=0, microsecond=0)
        cashfree_payment_lines = self.env['cashfree.payment.line'].search(
            [('create_date', '>=', date_from), ('create_date', '<=', date_to),
             ('payment_state', 'in', ('initiate', 'pending', 'success'))])
        if cashfree_payment_lines:
            for line in cashfree_payment_lines:
                line.payment_id.update_cashfree_payment_status()

    def action_cashfree_payment(self):
        """
        To transfer amount to partner via cashfree
        @return:
        """
        for rec in self:
            if rec.is_cashfree:

                rec.check_beneficiary_is_valid()
                cashfree_id = rec.get_cashfree_credentials()
                env = self.env.company.cashfree_env
                Payouts.init(cashfree_id.payout_app_id, cashfree_id.payout_key, env,
                             public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
                try:
                    transfer_req = Transfers.request_transfer(
                        beneId=rec.partner_id.beneficiary,
                        transferId=rec.cashfree_payment_line_ids.transfer,
                        amount=rec.amount)
                    response = json.loads(transfer_req.content)

                    if response['status'] == 'SUCCESS':
                        rec.cashfree_payment_line_ids.write({'payment_state': 'success',
                                                             'transaction_date': fields.datetime.now(), })
                        if response['data']['referenceId']:
                            rec.cashfree_payment_line_ids.write({'payment_reference': response['data']['referenceId']})

                        else:
                            rec.cashfree_payment_line_ids.write({'payment_reference': '', })

                    elif response['status'] == 'PENDING':
                        rec.cashfree_payment_line_ids.write({'payment_state': 'pending',
                                                             'transaction_date': fields.datetime.now()})
                    else:
                        rec.cashfree_payment_line_ids.write({'payment_state': 'fail',
                                                             'transaction_date': fields.datetime.now()})
                        rec.action_draft()
                        rec.cancel()

                except Exception as e:
                    error_string = repr(e)
                    _logger.error(f"err occurred {error_string}")
                    message = "Cash Transfer Failed\nError:%s" % error_string
                    raise ValidationError(_(message))

    def check_beneficiary_is_valid(self):
        """
        To check the beneficiary is present and valid
        @return:
        """
        for rec in self:
            if rec.is_cashfree:
                env = self.env.company.cashfree_env
                if rec.partner_id.beneficiary:
                    cashfree_id = rec.get_cashfree_credentials()
                    app_id = cashfree_id.payout_app_id
                    app_key = cashfree_id.payout_key
                    Payouts.init(app_id, app_key, env,
                                 public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
                    try:
                        bene_details = Beneficiary.get_bene_details(rec.partner_id.beneficiary)
                        json_data = json.loads(bene_details.content)
                        _logger.info(f"Beneficiary Details response ---- {json_data}")

                        if 'status' in json_data and json_data['status'] == 'SUCCESS':
                            return
                        else:
                            message = "%s Beneficiary[%s] Invalid" % (rec.partner_id.name, rec.partner_id.beneficiary)
                            raise ValidationError(_(message))

                    except Exception as e:
                        _logger.error(f"err occurred {e}")
                        message = "%s Beneficiary[%s] does not exist" % (rec.partner_id.name, rec.partner_id.beneficiary)
                        raise ValidationError(_(message))
                else:
                    message = f"Please add beneficiary {rec.partner_id.name}"
                    raise ValidationError(_(message))

    def action_draft(self):
        """
        To restrict if already paid
        @return:
        """
        for rec in self:
            if rec.cashfree_payment_line_ids and rec.is_cashfree and rec.state == 'posted':
                cashfree_payment_status = rec.cashfree_payment_line_ids.filtered(lambda s: s.payment_state != 'success')
                if cashfree_payment_status:
                    return super(AccountPayment, self).action_draft()
                else:
                    raise ValidationError(_("Reset to draft is restricted for cashfree payment"))
            else:
                return super(AccountPayment, self).action_draft()
