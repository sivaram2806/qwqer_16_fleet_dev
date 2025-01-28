# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, api, _
import json
from odoo.exceptions import ValidationError
from cashfree_sdk.payouts import Payouts
from cashfree_sdk.payouts.beneficiary import Beneficiary
from odoo.exceptions import UserError
import re

import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    cashfree_payment = fields.Boolean(string='Payment via Cashfree')

    @api.onchange('driver_partner_id')
    def onchange_vendor_bank_details(self):
        self.write({"cashfree_payment": False})

    def enable_cashfree_payment(self):
        # enable cashfree_payment for all selected records
        for rec in self:
            rec.cashfree_payment = True

    def disable_cashfree_payment(self):
        # disable cashfree_payment for all selected records
        for rec in self:
            rec.cashfree_payment = False

    def get_cashfree_credentials(self):
        cashfree_id = self.env['cash.free.credentials'].sudo().search([
            ("company_id", "=", self.company_id.id)], limit=1)
        if not cashfree_id:
            raise UserError("Cashfree configuration is missing, Please contact System Administrator")
        if not cashfree_id.public_key:
            raise UserError("Cashfree Authentication Key is missing, Please contact System Administrator")
        return cashfree_id

    def get_emp_beneficiary(self):
        for rec in self:
            env = self.env.company.cashfree_env
            if not rec.account_no:
                raise UserError(_('Account Number is Required to get Beneficiary in Cashfree'))
            if not rec.ifsc_code:
                raise UserError(_('IFSC Code is Required to get Beneficiary in Cashfree'))
            cashfree_id = rec.get_cashfree_credentials()
            app_id = cashfree_id.payout_app_id
            app_key = cashfree_id.payout_key
            Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
            try:
                bene_details_response = Beneficiary.get_bene_id(rec.account_no, rec.ifsc_code)
                bene_details_response_content = json.loads(bene_details_response.content)
                _logger.info(bene_details_response_content)
                if bene_details_response_content['status'] == 'SUCCESS':
                    rec.beneficiary_uid = bene_details_response_content['data']['beneId']
            except Exception as err:
                error_string = repr(err)
                message = "Get Beneficiary Failed\nError:%s" % error_string
                raise ValidationError(_(message))

    def remove_emp_beneficiary(self):
        """To remove partner from cashfree beneficiary"""
        for rec in self:
            env = self.env.company.cashfree_env
            if not rec.beneficiary_uid:
                raise UserError(_('Beneficiary ID is Required '))
            cashfree_id = rec.get_cashfree_credentials()
            if not  cashfree_id:
                raise UserError(_('Beneficiary ID is Required '))

            app_id = cashfree_id.payout_app_id
            app_key = cashfree_id.payout_key
            Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
            try:
                bene_details_response = Beneficiary.remove_bene(rec.beneficiary_uid)
                bene_details_response_content = json.loads(bene_details_response.content)
                rec.beneficiary_uid = ''
                _logger.info(bene_details_response_content)
            except Exception as err:
                error_string = repr(err)
                message = "Remove Beneficiary Failed\nError:%s" % error_string
                raise ValidationError(_(message))

    def add_emp_beneficiary(self):
        """To add partner to cashfree beneficiary"""
        for rec in self:
            env = self.env.company.cashfree_env
            list_mail = []
            if not rec.beneficiary_uid:
                if rec.driver_uid:
                    ben_id = (re.sub(r'[\W_]+', '', rec.name) + rec.driver_uid).upper()
                    rec.beneficiary_uid = ben_id
                else:
                    raise UserError(_('Driver ID is Required to add Beneficiary ID'))
            if not rec.account_no:
                raise UserError(_('Account Number is Required to add Beneficiary ID'))
            if not rec.region_id:
                raise UserError(_('Region is Required to add Beneficiary ID'))
            if not rec.ifsc_code:
                raise UserError(_('IFSC Code is Required to add Beneficiary ID'))
            if not rec.work_phone:
                raise UserError(_('Work phone is Required'))
            if not rec.work_email:
                raise UserError(_('Work email is Required'))
            else:
                if rec.work_phone:
                    mobile_temp = rec.work_phone.replace(" ", "")
                    length = len(mobile_temp)
                    if length >= 10:
                        mobile = mobile_temp
                    else:
                        raise UserError(_('Work phone number should not be less than 10 Characters'))
                else:
                    mobile_temp = rec.mobile_phone.replace(" ", "")
                    length = len(mobile_temp)
                    if length >= 10:
                        if length == 10:
                            mobile = mobile_temp[0: 10]
                        else:
                            l1 = length - 10
                            mobile = mobile_temp[l1: length]
                    else:
                        raise UserError(_('Work Mobile Number should not be less than 10 Characters'))
            if rec.work_email:
                mail = rec.work_email
                list_mail = re.split(",|;", mail)
            name0 = re.sub('\s', '_', rec.name)
            res_name = re.sub('\W', '', name0).replace("_", " ")
            try:
                cashfree_id = rec.get_cashfree_credentials()
                app_id = cashfree_id.payout_app_id
                app_key = cashfree_id.payout_key
                Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
                try:
                    bene_details_response = Beneficiary.get_bene_details(rec.beneficiary_uid)
                    bene_details_response_content = json.loads(bene_details_response.content)
                    _logger.info(bene_details_response_content)
                except Exception as err:
                    try:
                        bene_add_response = Beneficiary.add(beneId=rec.beneficiary_uid, name=res_name,
                                                            email=list_mail and list_mail[0] or 'noreplay@qwqer.in',
                                                            phone=mobile, bankAccount=rec.account_no,
                                                            ifsc=rec.ifsc_code, address1=rec.region_id.name)
                        json_data = json.loads(bene_add_response.content)
                        _logger.error(f"beneficiary addition response {json_data}")
                    except Exception as err:
                        error_string = repr(err)
                        message = "Add Beneficiary Failed\nError:%s" % error_string
                        raise ValidationError(_(message))
            except Exception as err:
                error_string = repr(err)
                message = "Add Beneficiary Failed\nError:%s" % error_string
                raise ValidationError(_(message))

    def get_add_driver_beneficiary(self):
        for rec in self:
            try:
                rec.get_emp_beneficiary()
            except Exception as err:
                if rec.beneficiary_uid:
                    try:
                        rec.remove_emp_beneficiary()
                        try:
                            rec.add_emp_beneficiary()
                        except Exception as err:
                            rec.beneficiary_uid = ''
                            _logger.info(f"Error Occur  get_add_driver_beneficiary *****aaaaaaaaa*******************{err}")
                    except Exception as err:
                        try:
                            rec.add_emp_beneficiary()
                        except Exception as err:
                            rec.beneficiary_uid = ''
                            _logger.info(f"Error Occur  get_add_driver_beneficiary *****aaaaaaaaa*******************{err}")
                else:
                    try:
                        rec.get_emp_beneficiary()
                    except Exception as err:
                        try:
                            rec.add_emp_beneficiary()
                        except Exception as err:
                            rec.beneficiary_uid = ''
                            _logger.info(f"Error Occur  get_add_driver_beneficiary *****aaaaaaaaa*******************{err}")
