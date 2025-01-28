# -*- coding: utf-8 -*-
from odoo import fields, models, _
import tempfile
import binascii
import certifi
import urllib3
import xlrd
from odoo.exceptions import UserError, Warning, ValidationError
from datetime import datetime


class ImportBankXlsWizard(models.TransientModel):
    """
    This model contains records on bank data
    """
    _name = "import.bank.xlxs.wizard"

    xlxs_file = fields.Binary('Xlxs File', filters='*.xlsx')

    def import_file(self):
        """ function to import bank details from  xlsx file """
        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.xlxs_file))
            book = xlrd.open_workbook(file_string.name)
            sheet = book.sheet_by_index(0)
            http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                       ca_certs=certifi.where())
        except Exception as e:
            raise UserError(_("Please choose the correct file"))
        config_id = self.env['bill.import.config'].sudo().search([('company_id', '=', self.env.company.id)], limit=1)
        utr_bill_list = []
        for i in range(1, sheet.nrows):
            line = list(sheet.row_values(i))
            try:
                if line[14]:
                    bill_id = self.env['account.move'].search([('name', '=', line[14])])
                    if bill_id and bill_id.id:
                        if bill_id.vehicle_customer_consolidate_id and bill_id.move_type in (
                                'in_invoice', 'in_refund') and not line[30]:
                            utr_bill_list.append(bill_id.name)
                        if not utr_bill_list:
                            date_object = False
                            if bill_id.vehicle_customer_consolidate_id and bill_id.move_type in (
                                    'in_invoice', 'in_refund'):
                                if line[30]:
                                    bill_id.utr_ref = line[30]
                            if line[29]:
                                date_object = datetime.strptime(line[29],'%d/%m/%Y').date()
                                if date_object > datetime.now().date():
                                    raise ValidationError(_("Payment date should not be greater than the current date"))
                            if line[28] and line[28].replace(" ", "").lower() == 'yes':
                                payment = self.env['account.payment'].create({
                                    'partner_type': config_id.partner_type,
                                    'partner_id': bill_id.partner_id and bill_id.partner_id.id or False,
                                    'amount': line[3] or bill_id.amount_residual,
                                    'journal_id': config_id.journal_id.id,
                                    'payment_type': config_id.payment_type,
                                    'payment_method_id': config_id.payment_method_id.id,
                                    'date': date_object or fields.Date.today(),
                                    'ref': bill_id.name,
                                })
                                payment.sudo().with_context({'region_id': bill_id.region_id.id}).action_post()
            except Exception as e:
                raise UserError(_(e))
        if utr_bill_list:
            str_utr_bill_list = "\n".join(utr_bill_list)
            raise UserError(_(f"Below listed bills have no UTR Reference Number\n{str_utr_bill_list}"))
