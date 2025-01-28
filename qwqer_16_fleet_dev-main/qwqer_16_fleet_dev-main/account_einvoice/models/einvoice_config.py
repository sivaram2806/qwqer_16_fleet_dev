# -*- coding: utf-8 -*-
from odoo import models, api, _, fields
from odoo.exceptions import UserError
import json
import requests
from datetime import datetime, timedelta, time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from collections import OrderedDict
import logging

_logger = logging.getLogger(__name__)

HOURS = [("0", "0"), ("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6"), ("7", "7"), ("8", "8"),
         ("9", "9"), ("10", "10"), ("11", "11"), ("12", "12"), ("13", "13"), ("14", "14"), ("15", "15"), ("16", "16"),
         ("17", "17"), ("18", "18"), ("19", "19"), ("20", "20"), ("21", "21"), ("22", "22"), ("23", "23")]


class EinvoiceConfig(models.Model):
    _name = 'einvoice.config'
    _rec_name = "api_gstin"

    api_username = fields.Char("E-Invoice User Name")
    api_password = fields.Char("E-Invoice Password")
    api_client_id = fields.Char("E-Invoice Client ID")
    api_client_secret = fields.Char("Client Secret")
    api_einvoice_url = fields.Char("E-Invoice Generate URL")
    api_gstin = fields.Char("Gstin")
    auth_token = fields.Char("Auth Token", copy=False)
    auth_generated_date = fields.Datetime("Auth Generated On", copy=False)
    token_expiry_time = fields.Datetime("Token Expiry On", copy=False)
    api_auth_url = fields.Char("Auth URL")
    api_cancel_url = fields.Char("E-Invoice Cancel URL")
    asp_id = fields.Char("ASP ID")
    asp_password = fields.Char("ASP Password")
    active = fields.Boolean(default=True)
    next_run_date = fields.Date("Next Bulk Execution Date")
    record_limit = fields.Integer("Record Fetch Limit")
    is_scheduler_run = fields.Boolean("Scheduler To Run")
    payment_mode_ids = fields.Many2many('payment.mode', string='Payment Mode')

    exec_start_time = fields.Selection(HOURS, "Execution Start Hour")

    exec_end_time = fields.Selection(HOURS, "Execution End Hour")

    # Company id for Multi-Company
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.constrains('exec_start_time', 'exec_end_time')
    def _onchange_execution_times(self):
        if self.exec_start_time and not self.exec_end_time:
            raise UserError("Enter value for Execution End Hour")
        if not self.exec_start_time and self.exec_end_time:
            raise UserError("Enter value for Execution Start Hour")

        if int(self.exec_start_time) > int(self.exec_end_time):
            raise UserError('Execution Start Hour should be lesser than Execution End Hour')

        if int(self.exec_end_time) != 0 and int(self.exec_start_time) != 0:
            if int(self.exec_end_time) == int(self.exec_start_time):
                raise UserError("Skip Start Hour and  Skip End Hour should have different values")

    def generate_url_with_auth_data(self):
        url = (self.api_einvoice_url + "?aspid=" + self.asp_id + "&password=" + self.asp_password + "&Gstin=" +
               self.api_gstin + "&AuthToken=" + self.auth_token + "&user_name=" + self.api_username + "&QrCodeSize=250")
        return url

    def check_token_expiry(self, force_authenticate):
        # Get the current UTC time and adjust to IST (UTC+5:30) bcz we are getting IST time from TAXPRO
        datetime_now = datetime.utcnow() + timedelta(hours=5, minutes=30)

        # Calculate the token expiry datetime with a 5-minute buffer
        token_expiry_datetime = self.token_expiry_time and self.token_expiry_time - timedelta(minutes=5)

        # Check if the token has expired or if authentication is forced
        if (not token_expiry_datetime or token_expiry_datetime and token_expiry_datetime <= datetime_now) or force_authenticate:
            return True  # Token needs re authentication
        else:
            return False  # Token is still valid

    def authenticate_tax_pro(self, scheduler=False, force_authenticate=False):
        """
        To Validate E-invoice config and authenticate
        @return: einvoice_config with updated details if success
        """
        config_failed_msg = ""
        if not self.api_username:
            config_failed_msg = "E-Invoice User Name not available in configuration"
        if not self.api_password:
            config_failed_msg = "E-Invoice Password not available in configuration"
        if not self.api_gstin:
            config_failed_msg = "E-Invoice Gstin not available in configuration"
        if not self.api_auth_url:
            config_failed_msg = "E-invoice Auth URl not available in configuration"
        if not self.asp_id:
            config_failed_msg = "ASP ID not available in configuration"
        if not self.asp_password:
            config_failed_msg = "ASP Password not available in configuration"
        if not self.api_einvoice_url:
            config_failed_msg = "E-invoice Generate URl not available in configuration"

        if config_failed_msg and scheduler:
            self.env['einvoice.scheduler.failed.log'].sudo().create({
                'invoice_id': False,
                'gstin': self.api_gstin,
                'reason': config_failed_msg
            })
        elif config_failed_msg:
            self.env.cr.commit()
            raise UserError(_(config_failed_msg))

        if self.check_token_expiry(force_authenticate):
            headers = {"Content-Type": "application/json; charset=utf-8",
                       "gstin": self.api_gstin,
                       "user_name": self.api_username,
                       "eInvPwd": self.api_password,
                       "aspid": self.asp_id,
                       "password": self.asp_password}
            url = self.api_auth_url
            response = requests.get(url, headers=headers)
            outgoing_request_rawlog = self.env['outgoing.api.log'].sudo().create({
                'data': headers and str(headers),
                'name': "Generate authentication",
                'key': self and str(self.api_gstin),
            })
            response_content = json.loads(response.content)
            _logger.info("Einvoice Authentication : Response : %s ", response_content)

            status = response_content.get('Status')
            if status == 1:
                self.write({"auth_token": response_content['Data']['AuthToken'],
                            "auth_generated_date": datetime.now(),
                            "token_expiry_time": response_content['Data']['TokenExpiry']})
                self.env.cr.commit()
            elif status == 0:
                error_msgs = "\n".join(
                    [item.get('ErrorMessage', "") for item in response_content.get('ErrorDetails', [])
                     if item.get('ErrorMessage', "")])
                if scheduler:
                    self.env['einvoice.scheduler.failed.log'].sudo().create({
                        'invoice_id': False,
                        'gstin': self.api_gstin,
                        'reason': error_msgs
                    })
                    if response_content.get('error'):
                        error = response_content.get('error')
                        if error.get('error_cd') and response_content['error']['error_cd'] == "GSP752":
                            self.update({"token_expiry_time": False})
                else:
                    self.env.cr.commit()
                    raise UserError(_(error_msgs))
            if response_content.get('status_cd') == 1:
                self.update({"auth_token": response_content['Data']['AuthToken'],
                             "auth_generated_date": response_content['Data']['TokenExpiry']
                             })
            outgoing_request_rawlog.sudo().update({
                'response': response_content,
                'response_date': datetime.now(),
                'status': "Success" if status == 1 else "Failed"
            })

    def fetch_irn_from_gst_portal(self, url, invoice_obj):
        """
        To create E-Invoice from invoice data
        @param url: TaxPro e-invoice url with auth details
        @return: E-invoice generate api response
        """
        price_precision = self.env['decimal.precision'].precision_get('gst_reporting_price_precision')
        request_body = OrderedDict()
        request_body['Version'] = '1.1'
        # ------------------- TranDtls -----------------#
        transaction_details = {
            "TaxSch": "GST",
            "SupTyp": "B2B",
            "IgstOnIntra": "N",
            "RegRev": "N",
            "EcmGstin": None}
        # ------------------- DocDtls -----------------#
        if invoice_obj.move_type:
            if invoice_obj.move_type in ('in_invoice', 'out_invoice'):
                doc_type = 'INV'
            elif invoice_obj.move_type == 'out_refund':
                doc_type = 'CRN'
            elif invoice_obj.move_type in ['in_refund', 'in_refund_sale']:
                doc_type = 'DBN'
            else:
                doc_type = 'INV'
        else:
            doc_type = 'INV'
        invoice_number = invoice_obj.name or ""
        doc_date = ""
        if invoice_obj.invoice_date:
            doc_date = datetime.strptime(str(invoice_obj.invoice_date), DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
        doc_details = {
            'Typ': doc_type or "INV",
            'No': invoice_number,
            'Dt': doc_date}
        # ------------------- SellerDtls -----------------#
        #  for test PIN 605005
        #  for test STCD "34"
        #  for test GSTN 34AACCC1596Q002
        seller_details = {
            'Gstin': invoice_obj.journal_gstin_partner_id.vat or "",
            'LglNm': invoice_obj.journal_gstin_partner_id.name or "",
            'Addr1': invoice_obj.journal_gstin_partner_id.street or "",
            'Loc': invoice_obj.journal_gstin_partner_id.city or "",
            'Pin': invoice_obj.journal_gstin_partner_id.zip and int(invoice_obj.journal_gstin_partner_id.zip) or "",
            'Stcd': invoice_obj.journal_gstin_partner_id.state_id and invoice_obj.journal_gstin_partner_id.state_id.l10n_in_tin,
            'Ph': invoice_obj.journal_id.l10n_in_gstin_partner_id.phone and invoice_obj.journal_id.l10n_in_gstin_partner_id.phone.replace(
                "+", "") or "",
            'Em': invoice_obj.sudo().journal_id.l10n_in_gstin_partner_id.email or ""}
        if invoice_obj.journal_gstin_partner_id.street2:
            seller_details.update({'Addr2': invoice_obj.journal_gstin_partner_id.street2 or ""})
        # ------------------- BuyerDtls -----------------#

        buyer_details = {'Gstin': str(invoice_obj.partner_id.vat) or "",  # test value "34AACCC1596Q002"
                         'LglNm': invoice_obj.partner_id.name or "",
                         # 'TrdNm': partner and partner.name or ""
                         'Addr1': invoice_obj.partner_id.street or "",

                         'Ph': invoice_obj.partner_id.phone and invoice_obj.partner_id.phone.replace("+", "") or "",
                         'Loc': invoice_obj.partner_id.city or "",
                         'POS': invoice_obj.partner_id.state_id.l10n_in_tin or "",
                         'Pin': invoice_obj.partner_id.zip and int(invoice_obj.partner_id.zip) or "",
                         'Stcd': invoice_obj.partner_id.state_id.l10n_in_tin or "",
                         'Em': invoice_obj.partner_id.email or ""}

        if invoice_obj.partner_id.street2:
            buyer_details.update({'Addr2': invoice_obj.partner_id.street2 or "",})
        # ------------------- Invoice line details ------------------- #
        total_cgst_amount = 0.00
        total_sgst_amount = 0.00
        total_igst_amount = 0.00
        ItemList = []
        total_inv_value = invoice_obj.amount_total
        total_taxable_value = invoice_obj.amount_untaxed
        item_no = 0
        for line in invoice_obj.invoice_line_ids:
            taxable_value = line.price_subtotal or 0.00
            total_value = line.price_subtotal or 0.00
            price_unit = line.price_unit or 0.00
            line_total = line.price_total or 0.00
            igst_rate, cgst_rate, sgst_rate, igst_amount, cgst_amount, sgst_amount = self.get_igst_cgst_sgst_rate_and_amount(
                line, invoice_obj.partner_id)
            total_cgst_amount += cgst_amount
            total_sgst_amount += sgst_amount
            total_igst_amount += igst_amount
            item_no += 1
            item_dict = {'SlNo': str(item_no) or "",
                         'PrdDesc': line.name or "",
                         "IsServc": "Y" if line.product_id.type == 'service' else "N",
                         'HsnCd': line.product_id.l10n_in_hsn_code or '',
                         'Qty': round((line and line.quantity or 0)),
                         'Unit': 'OTH',
                         'UnitPrice': round(price_unit, price_precision) or 0.00,
                         'TotAmt': round(total_value, price_precision),
                         'Discount': 0.00,
                         'PreTaxVal': round(taxable_value, price_precision),
                         'AssAmt': round(taxable_value, price_precision),
                         'GstRt': sgst_rate + cgst_rate + igst_rate,
                         'IgstAmt': abs(round(igst_amount, price_precision)) or 0.00,
                         'CgstAmt': abs(round(cgst_amount, price_precision)) or 0.00,
                         'SgstAmt': abs(round(sgst_amount, price_precision)) or 0.00,
                         'CesRt': 0,
                         'CesAmt': 0,
                         'CesNonAdvlAmt': 0,
                         'StateCesRt': 0,
                         'StateCesAmt': 0,
                         'StateCesNonAdvlAmt': 0,
                         'OthChrg': 0,
                         'TotItemVal': round(line_total, price_precision) or 0.00,
                         }
            ItemList.append(item_dict)

        roundoff_amount = 0.00
        # if self.roundoff_value: TODO:
        #     roundoff_amount = self.roundoff_value
        value_details = {'AssVal': round(total_taxable_value, 2),
                         'IgstVal': abs(round(total_igst_amount, price_precision)),
                         'CgstVal': abs(round(total_cgst_amount, price_precision)),
                         'SgstVal': abs(round(total_sgst_amount, price_precision)),
                         'StCesVal': 0.00,
                         'Discount': 0.00,
                         'CesVal': 0.00,
                         'OthChrg': 0.00,
                         'RndOffAmt': roundoff_amount or 0.00,
                         'TotInvVal': round(total_inv_value, price_precision)}
        request_body.update({'TranDtls': transaction_details,
                             'DocDtls': doc_details,
                             'SellerDtls': seller_details,
                             'BuyerDtls': buyer_details,
                             'ValDtls': value_details,
                             'ItemList': ItemList, })
        outgoing_request_rawlog = self.env['outgoing.api.log'].sudo().create({
            'data': request_body and str(request_body),
            'name': "Generate IRN",
            'key': invoice_obj.name,
        })

        response = requests.post(url, data=json.dumps(dict(request_body)))
        response_content = json.loads(response.content)

        return response_content, outgoing_request_rawlog

    @staticmethod
    def get_igst_cgst_sgst_rate_and_amount(line, partner_id):
        """generate e-invoice tax details
        @param line:  invoice line
        @param partner_id: invoice customer
        @return:  sum of amount and rate
        """
        igst_rate = 0
        cgst_rate = 0
        sgst_rate = 0
        igst_amount = 0.00
        cgst_amount = 0.00
        sgst_amount = 0.00
        taxes_res = line.tax_ids.compute_all(line.price_unit, line.currency_id, line.quantity, line.product_id,
                                             partner_id)
        tax_list = taxes_res['taxes']
        for i in tax_list:
            total_value = round(i['base'], 2)
            if 'CGST' in i['name']:
                cgst_amount = round(i['amount'], 2)
            if 'SGST' in i['name']:
                sgst_amount = round(i['amount'], 2)
            if 'IGST' in i['name']:
                igst_amount = round(i['amount'], 2)

        for tax in line.tax_ids:
            if tax.amount_type == 'group':
                for child_tax in tax.children_tax_ids:
                    if 'CGST' in child_tax.name:
                        cgst_rate = child_tax.amount
                    if 'SGST' in child_tax.name:
                        sgst_rate = child_tax.amount
                    if 'IGST' in child_tax.name:
                        igst_rate = child_tax.amount

            elif tax.amount_type == 'percent':
                for i in tax_list:
                    if 'CGST' in i['name']:
                        cgst_rate = tax.amount
                    if 'SGST' in tax.name:
                        sgst_rate = tax.amount
                    if 'IGST' in tax.name:
                        igst_rate = tax.amount
        return igst_rate, cgst_rate, sgst_rate, igst_amount, cgst_amount, sgst_amount
