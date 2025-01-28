# -*- coding: utf-8 -*-

from odoo import fields, models, _
import tempfile
import binascii
import xlrd

from odoo.exceptions import UserError, MissingError, ValidationError


class HdfcWOAdvXlsxImportWizard(models.TransientModel):
    """
    This model contains records on bank data
    """
    _name = "hdfc.wo_adv.xlsx.import.wizard"

    file_name = fields.Char(string="File Name")
    xlxs_file = fields.Binary('XLSX File', filters='*.xlsx')

    def import_file(self):
        """ function to import bank details from  xlsx file """
        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.xlxs_file))
            book = xlrd.open_workbook(file_string.name)
            sheet = book.sheet_by_index(0)
        except Exception:
            raise ValidationError(_("Please choose the correct file"))
        error_rec = []
        for i in range(0, sheet.nrows):
            line = list(sheet.row_values(i))
            if i == 0:
                known_columns = ['Txn type\nRTGS - R\nNEFT - N\nHDFC TRF - I',
                                 'Beneficiary Code\n(Mandatory only for txn type "I")', 'Bene A/c No.', 'Amount',
                                 'Beneficiary Name', 'To be left Blank', 'To be left Blank', 'To be left Blank',
                                 'To be left Blank', 'To be left Blank', 'To be left Blank', 'To be left Blank',
                                 'To be left Blank', 'Customer Ref No\nonly for NEFT " N "', 'Payment Detail 1',
                                 'Payment Detail 2', 'Payment Detail 3', 'Payment Detail 4', 'Payment Detail 5',
                                 'Payment Detail 6', 'Payment Detail 7', 'To be left Blank', 'Inst. Date\nDD/MM/YYYY',
                                 'To be left Blank', 'IFSC code', 'Bene Bank Name', 'Bene Bank Branch Name',
                                 'Bene Email ID', 'Payment Status', 'Payment Date']
                if len(line) >= 31:
                    known_columns.append('UTR Reference Number')
                if line != known_columns:
                    raise UserError(f"Sheet you have imported contains missing or unknown columns !!! \n\n"
                                    f"Please re-upload using proper excel template.")
                continue
            company_id = self.env["res.company"].search([("name", "=", line[16])], limit=1)
            if not company_id:
                error_rec.append(
                    _('DATA MISMATCH: Payment(%s) Company not found %s !!!.\n', line[15], line[16]))
                continue
            wo_id = self.env["work.order"].search([("name", "=", line[14]), ("company_id", "=", company_id.id)],
                                                  limit=1)
            if not wo_id:
                error_rec.append(
                    _('DATA MISMATCH: Payment(%s) Work Order not found %s !!!.\n', line[15], line[14]))
                continue
            payment_id = self.env["account.payment"].search(
                [("name", "=", line[15]), ("company_id", "=", company_id.id)],
                limit=1) if line[15] != '/' else False
            if not payment_id:
                error_rec.append(_('DATA MISMATCH: Payment not found %s !!!.\n', line[15]))
                continue
            if not payment_id.state == 'draft':
                error_rec.append(_('Payment %s is %s' % (
                    line[15], 'already Posted !!!\n' if payment_id.state == 'posted' else 'in cancelled state !\n')))
                continue
            if payment_id.amount != line[3]:
                error_rec.append(
                    _('DATA MISMATCH: Payment %s amount mismatch !!!\n', line[15]))
                continue
            if payment_id in wo_id.payment_ids:
                if payment_id.state == "draft" and line[28].upper() == "YES":
                    payment_id.action_post()
                    self.env.cr.commit()
                else:
                    error_rec.append(
                        _(f"DATA MISMATCH: for Payment:'{line[15]}' and Work order: '{line[14]}'.\n"))
                    continue
        error_rec = ''.join(str(item) for item in error_rec)
        if error_rec:
            message = f"Skipped Records \n{error_rec}"
            header = "Warning"
        else:
            header = "Success"
            message = f"All records has been successfully updated"
        res = self.env["warning.message.popup"].create({"message": message})
        return {

            'name': header,
            'type': 'ir.actions.act_window',
            'res_model': 'warning.message.popup',
            'view_mode': 'form',
            'res_id': res.id,
            'view_type': 'form',
            'target': 'new'
        }
