# -*- coding: utf-8 -*-

from odoo import fields, models, _
import tempfile
import binascii
import xlrd

from odoo.exceptions import UserError, ValidationError


class DailyDriverPayoutUpdateWizard(models.TransientModel):
    _name = "daily.driver.payout.update.wizard"
    _description = "Wizard to update daily driver payout deduction incentive"

    filename = fields.Char(string="File Name")
    updated_file = fields.Binary('Updated deduction incentive', filters='*.xlsx')

    def action_update_payout_variables(self):
        """ Function to import payout details from  xlsx file """
        payout_id = self.env['driver.batch.payout'].browse(self._context.get('active_id', []))
        if payout_id and payout_id.state == 'draft':
            try:
                file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
                file_string.write(binascii.a2b_base64(self.updated_file))
                book = xlrd.open_workbook(file_string.name)
                sheet = book.sheet_by_index(0)
            except Exception:
                raise ValidationError(_("Please choose the correct file"))
            for i in range(sheet.nrows):
                line = list(sheet.row_values(i))
                if i == 0:
                    known_columns = ['Transfer ID', 'Driver ID', 'Incentive', 'Deduction', 'Remarks']
                    if line != known_columns:
                        raise UserError(f"Sheet you have imported contains missing or unknown columns !!! \n\n"
                                        f"Please re-upload using proper excel template.")
                    continue
                if line[0]:
                    line_id = self.env['driver.batch.payout.lines'].search(
                        [('transfer_id', '=', line[0]), ('driver_uid', '=', line[1])])
                    if line_id.id:
                        if line[2]:
                            line_id.incentive_amount = line[2]
                        if line[3]:
                            line_id.deduction_amount = line[3]
                        if line[4]:
                            line_id.remarks = line[4]
                    else:
                        raise UserError(_('Transfer ID or Driver does not match any records!'))
        else:
            raise UserError(_('%s download is restricted. Payout is already in %s status.Please Refresh!' % (
            payout_id.name, payout_id.state)))

    def action_export_files(self):
        """
        Function to export sample file if record state in draft
        """
        payout_id = self.env['driver.batch.payout'].browse(self._context.get('active_id', []))
        if payout_id and payout_id.state == 'draft':
            data = {
                'payout_id': payout_id.id,
            }
            return self.env.ref('driver_management.driver_payout_update_excel_sample_action').report_action(self,
                                                                                                            data=data)
        else:
            raise UserError(_('%s download is restricted. Payout is already in %s status.Please Refresh!' % (
            payout_id.name, payout_id.state)))
