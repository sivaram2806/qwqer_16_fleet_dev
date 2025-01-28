# -*- coding: utf-8 -*-
import base64

from odoo import fields, models, _
import json
from odoo.exceptions import ValidationError
from cashfree_sdk.payouts import Payouts
from cashfree_sdk.payouts.beneficiary import Beneficiary
from odoo.exceptions import UserError
import re
import os

import logging

_logger = logging.getLogger(__name__)


class InheritPartner(models.Model):
    _inherit = 'res.partner'

    beneficiary = fields.Char(string="Beneficiary ID", copy=False)

    def get_cashfree_credentials(self):
        cashfree_id = self.env['cash.free.credentials'].sudo().search([
            ("company_id", "=", self.company_id.id)], limit=1)
        if not cashfree_id:
            raise UserError("Cashfree configuration is missing, Please contact System Administrator")
        if not cashfree_id.public_key:
            raise UserError("Cashfree Authentication Key is missing, Please contact System Administrator")
        return cashfree_id

    def get_partner_beneficiary(self):
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
                    rec.beneficiary = bene_details_response_content['data']['beneId']
            except Exception as err:
                error_string = repr(err)
                message = "Get Beneficiary Failed\nError:%s" % error_string
                raise ValidationError(_(message))

    def remove_partner_beneficiary(self):
        """To remove partner from cashfree beneficiary"""
        for rec in self:
            env = self.env.company.cashfree_env
            if not rec.beneficiary:
                raise UserError(_('Beneficiary ID is Required '))
            cashfree_id = rec.get_cashfree_credentials()
            if not  cashfree_id:
                raise UserError(_('Beneficiary ID is Required '))

            app_id = cashfree_id.payout_app_id
            app_key = cashfree_id.payout_key
            Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
            try:
                bene_details_response = Beneficiary.remove_bene(rec.beneficiary)
                bene_details_response_content = json.loads(bene_details_response.content)
                rec.beneficiary = ''
                _logger.info(bene_details_response_content)
            except Exception as err:
                error_string = repr(err)
                message = "Remove Beneficiary Failed\nError:%s" % error_string
                raise ValidationError(_(message))

    def add_partner_beneficiary(self):
        """To add partner to cashfree beneficiary"""
        for rec in self:
            env = self.env.company.cashfree_env
            list_mail = []
            if not rec.beneficiary:
                name = 'CUSTID'
                if rec.supplier_rank > 0:
                    name = 'VENDID'
                rec_id = str(rec.id)
                ben_id = name + rec_id
                if ben_id:
                    rec.beneficiary = ben_id
            if not rec.account_no:
                raise UserError(_('Account Number is Required to add Beneficiary ID'))
            if not rec.region_id:
                raise UserError(_('Region is Required to add Beneficiary ID'))
            if not rec.ifsc_code:
                raise UserError(_('IFSC Code is Required to add Beneficiary ID'))
            if not rec.mobile and not rec.phone:
                raise UserError(_('Mobile is Required'))
            else:
                if rec.phone:
                    mobile_temp = rec.phone.replace(" ", "")
                    length = len(mobile_temp)
                    if length >= 10:
                        mobile = mobile_temp
                    else:
                        raise UserError(_('Phone Number should not be less than 10 Characters'))
                else:
                    mobile_temp = rec.mobile.replace(" ", "")
                    length = len(mobile_temp)
                    if length >= 10:
                        if length == 10:
                            mobile = mobile_temp[0: 10]
                        else:
                            l1 = length - 10
                            mobile = mobile_temp[l1: length]
                    else:
                        raise UserError(_('Mobile Number should not be less than 10 Characters'))
            if rec.email:
                mail = rec.email
                list_mail = re.split(",|;", mail)
            name0 = re.sub('\s', '_', rec.name)
            res_name = re.sub('\W', '', name0).replace("_", " ")
            try:
                cashfree_id = rec.get_cashfree_credentials()
                app_id = cashfree_id.payout_app_id
                app_key = cashfree_id.payout_key
                Payouts.init(app_id, app_key, env, public_key=base64.b64decode(cashfree_id.public_key).decode('utf-8'))
                try:
                    bene_details_response = Beneficiary.get_bene_details(rec.beneficiary)
                    bene_details_response_content = json.loads(bene_details_response.content)
                    _logger.info(bene_details_response_content)
                except Exception as err:
                    try:
                        bene_add_response = Beneficiary.add(beneId=rec.beneficiary, name=res_name,
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
