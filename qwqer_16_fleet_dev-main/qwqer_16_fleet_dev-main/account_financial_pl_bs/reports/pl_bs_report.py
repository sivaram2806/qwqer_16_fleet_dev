# -*- coding: utf-8 -*-

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import pytz

from odoo import _, models

from odoo.exceptions import UserError

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def excel_style(row, col):
    """ Convert given row and column number to an Excel-style cell name. """
    result = []
    while col:
        col, rem = divmod(col-1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result) + str(row)

heading = []

class BalanceSheetXlsx(models.AbstractModel):
    _name = 'report.account_financial_pl_bs.balance.sheet.xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    
    # @api.multi
    def get_current_datetime(self):
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_datetime = False
        if date_time:
            time_obj = datetime.strptime(date_time, DEFAULT_SERVER_DATETIME_FORMAT)
            tz_name = self._context.get('tz', False) \
                or self.env.user.tz
            if not tz_name:
                raise UserError(_('Please configure your time zone in preferance'))
            if tz_name and time_obj:
                current_datetime = time_obj.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone(tz_name)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if current_datetime:
            printed_on = datetime.strptime(current_datetime,"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
        else:
            printed_on = False
        return printed_on    


    def generate_rec_row(self, worksheet, data, row, bold, date_format, no_format, normal_num_bold,
                         has_com, show_deb_cre, tb, ope,display_analytic_acc, state, region,group_by_condition,state_list,service_obj, level_limit = 0):
        total_balance = 0.0
        analytic_id_ist = []
        if region:
            analytic_id_ist += region.mapped('analytic_account_id').ids
        elif state:
            for i in state:
                analytic_id_ist += i.regions_ids.mapped('analytic_account_id').ids
        
        analytic_domain = []
        if analytic_id_ist:
            analytic_domain = [('id','in',analytic_id_ist)]
        analytic_account = self.env['account.analytic.account'].search(analytic_domain)
        for rec_data in data:
            if ope:
                if rec_data['level'] < 10 and rec_data['type'] == 'report':
                    if not rec_data['level'] == 0:
                        total_balance += rec_data['balance_cmp_debit']-rec_data['balance_cmp_credit']
        while data:
            col = 0
            hide_report_head = False
            hide_total_report = False
            if 'hide_report_head' in data[0]:
                hide_report_head = data[0]['hide_report_head']
            if 'hide_total_report' in data[0]:
                hide_total_report = data[0]['hide_total_report']
            if data[0]['level'] <= level_limit and level_limit != 0:
                break
            curr_data = data.pop(0)
            name = "  " * curr_data['level']* 3 + curr_data['name']
            if curr_data['level'] < 7 and curr_data['type'] == 'report':
                

                
                temp_row = row
                if curr_data['level'] != 0:
                    if not hide_report_head:
                        worksheet.write(row, col, name, bold)
                        row += 1
                row = self.generate_rec_row(worksheet, data, row, bold, date_format, no_format, normal_num_bold,
                                            has_com, show_deb_cre, tb, ope,display_analytic_acc,state, region,group_by_condition,state_list,service_obj, curr_data['level'])
                if temp_row + 1 == row:
                    row -= 1
                else:
                    print("hide_total_report 11111----------------------- ",hide_total_report," ====hide_report_head====== ",hide_report_head)
                    print("curr_data -------------------- ",curr_data)
                    curr_name = curr_data['name']
                    name = "  " * curr_data['level']* 3 + "Total %s"%(curr_name)
                    if curr_data['name'] == 'Profit & Loss - Qwqer':
                        curr_name = "Profit / Loss"
                        name = "  " * curr_data['level']* 3 + "%s"%(curr_name)
                    if not hide_total_report:
                        worksheet.write(row, col, name, bold)
                col += 1
                if tb:
                    if curr_data['level'] == 0:
                        curr_data['balance_cmp_debit'] = 0.0
                        curr_data['balance_cmp_credit'] = 0.0
                        open_balance = curr_data['balance_cmp']
                        
                    else:
                        open_balance = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                    
                    worksheet.write_number(row, col, open_balance,
                                           normal_num_bold)
                    col += 1
                    worksheet.write_number(row, col, curr_data['debit'], normal_num_bold)
                    col += 1
                    worksheet.write_number(row, col, curr_data['credit'], normal_num_bold)
                    col += 1
                    worksheet.write_number(row, col,curr_data['debit']-  curr_data['credit'], normal_num_bold)
                    col += 1
                    worksheet.write_number(row, col, open_balance +(curr_data['debit'] - curr_data['credit']),
                                               normal_num_bold)
                                               
                else: 
                    if show_deb_cre:
                        if ope:
                            if 'account_id' in curr_data:
                                opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            else:
                                opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            closing_bal = opening_bal + curr_data['balance']
                            worksheet.write_number(row, col, opening_bal, normal_num_bold)
                            col += 1
                        worksheet.write_number(row, col, curr_data['debit'], normal_num_bold)
                        col += 1
                        worksheet.write_number(row, col, curr_data['credit'], normal_num_bold)
                        col += 1
                    elif display_analytic_acc:
                        if ope:
                            if 'account_id' in curr_data:
                                opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            else:
                                opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            closing_bal = opening_bal + curr_data['balance']
                            worksheet.write_number(row, col, opening_bal, normal_num_bold)
                            col += 1
                        if 'analytic_values' in curr_data:
                            if group_by_condition=="region":
                                for analytic in analytic_account:
                                    if analytic.id in curr_data['analytic_values']:
                                        worksheet.write_number(row, col, curr_data['analytic_values'][analytic.id], no_format)
                                        col += 1
                                    else:
                                        worksheet.write_number(row, col, 0.0, no_format)
                                        col += 1
                            else:
                                for state in state_list:
                                    region=self.env['sales.region'].search([('state_id', '=', state.id)])
                                    sum=0
                                    for reg in region:
                                        if reg.analytic_account_id.id in curr_data['analytic_values']:
                                                sum=sum+curr_data['analytic_values'][reg.analytic_account_id.id]
                                        
                                    worksheet.write_number(row, col, sum, no_format)
                                    col += 1      
                                        
                                        
                                        
                    else:
                        if ope:
                            if 'account_id' in curr_data:
                                opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            else:
                                opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            closing_bal = opening_bal + curr_data['balance']
                            worksheet.write_number(row, col, opening_bal, normal_num_bold)
                            col += 1
                    if not hide_total_report:
                        worksheet.write_number(row, col, curr_data['balance'], normal_num_bold)
                    col += 1
                    if ope:
                        worksheet.write_number(row, col, closing_bal, normal_num_bold)
                        col += 1
                    if has_com:
                        worksheet.write_number(row, col, curr_data['balance_cmp'], normal_num_bold)
                if not hide_total_report and curr_data['level'] != 0:
                    row += 1                
            else:
                worksheet.write(row, col, name)
                col += 1
                if tb:
                    closing_bal = 0.00
                    if 'account_id' in curr_data:
                        opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                        closing_bal = (curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']) + (curr_data['debit'] - curr_data['credit'])
                    else:
                        opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                        
                    worksheet.write_number(row, col, opening_bal,no_format)
                    col += 1
                    worksheet.write_number(row, col, curr_data['debit'], no_format)
                    col += 1
                    worksheet.write_number(row, col, curr_data['credit'], no_format)
                    col += 1
                    worksheet.write_number(row, col,curr_data['debit']- curr_data['credit'], no_format)
                    col += 1
                    worksheet.write_number(row, col,closing_bal,
                                           no_format)
                else:  
                    closing_bal = curr_data['balance']
                    if show_deb_cre:
                        if ope:
                            opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            closing_bal = opening_bal + curr_data['balance']
                            
                            worksheet.write_number(row, col, opening_bal, normal_num_bold)
                            col += 1
                        worksheet.write_number(row, col, curr_data['debit'], no_format)
                        col += 1
                        worksheet.write_number(row, col, curr_data['credit'], no_format)
                        col += 1
                    elif display_analytic_acc:
                        if ope:
                            opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            closing_bal = opening_bal + curr_data['balance']
                            worksheet.write_number(row, col, opening_bal, normal_num_bold)
                            col += 1

                        if 'analytic_values' in curr_data:
                            if group_by_condition=="region":
                                for analytic in analytic_account:
                                    if analytic.id in curr_data['analytic_values']:
                                        worksheet.write_number(row, col, curr_data['analytic_values'][analytic.id], no_format)
                                        col += 1
                                    else:
                                        worksheet.write_number(row, col, 0.0, no_format)
                                        col += 1

                            else:
                                for state in state_list:
                                    region=self.env['sales.region'].search([('state_id', '=', state.id)])
                                    sum=0
                                    for reg in region:
                                        if reg.analytic_account_id.id in curr_data['analytic_values']:
                                                sum=sum+curr_data['analytic_values'][reg.analytic_account_id.id]
                                        
                                    worksheet.write_number(row, col, sum, no_format)
                                    col += 1
                    
                    else:
                        if ope:
                            opening_bal = curr_data['balance_cmp_debit']-curr_data['balance_cmp_credit']
                            closing_bal = opening_bal + curr_data['balance']
                            worksheet.write_number(row, col, opening_bal, normal_num_bold)
                            col += 1
                    if not hide_total_report:
                        worksheet.write_number(row, col, curr_data['balance'], no_format)
                    col += 1
                    if ope:
                        worksheet.write_number(row, col, closing_bal, normal_num_bold)
                        col += 1
                    if has_com:
                        worksheet.write_number(row, col, curr_data['balance_cmp'], no_format)
                if not hide_total_report and curr_data['level'] != 0:
                    row += 1
        return row


    def generate_xlsx_report(self, workbook, data, wiz):
        fin_report_pool = self.env['report.accounting_pdf_reports.report_financial']
        context = dict(self.env.context or {})
        real_data = context.get('rep_data', {})
        rep_data = [real_data]
        rep_data[0]['form']['account_report_id'] = wiz.read()[0]['account_report_id']

        fin_data = fin_report_pool.get_account_lines(rep_data[0]['form'])
        ##FORMATS##
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'bold': True, 'size': 18})
        sub_heading_format = workbook.add_format({'align': 'center',
                                                  'valign': 'vcenter',
                                                  'bold': True, 'size': 14})
        bold = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        no_format = workbook.add_format({'num_format': '#,##0.00'})
        normal_num_bold = workbook.add_format({'bold': True, 'num_format': '#,##0.00'})
        ##FORMATS END##
        worksheet = workbook.add_worksheet(rep_data[0]['form']['account_report_id'][1])
        worksheet.set_column('A:A', 50)
        has_com = False
        show_deb_cre = False
        state_list=[]
        analytic_id_ist = []
        if wiz.region_ids:
            analytic_id_ist += wiz.region_ids.mapped('analytic_account_id').ids
        elif wiz.state_ids:
            for i in wiz.state_ids:
                analytic_id_ist += i.regions_ids.mapped('analytic_account_id').ids

        analytic_domain = []
        service=wiz.service_type_id
        if analytic_id_ist:
            analytic_domain = [('id','in',analytic_id_ist)]
        analytic_account = self.env['account.analytic.account'].search(analytic_domain)

        heading_list = ['Account', 'Balance']

        if wiz.enable_filter:
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 20)
            has_com = True
            heading_list = ['Account', 'Balance', wiz.label_filter]
            if wiz.include_opening:
                worksheet.set_column('D:D', 20)
                heading_list = ['Account', 'Opening', 'Current Period', 'Closing Balance', wiz.label_filter]

        if wiz.display_analytic_acc:
            if wiz.group_by_condition=="region":
                col_num = 2
                char_num = 66
                if analytic_account:

                    if wiz.include_opening:
                        col_num += 2

                    for analytic in analytic_account:
                        col_num += 1
                        worksheet.set_column(col_num,col_num, 20)
                    if wiz.include_opening:
                        col_num += 1
                        worksheet.set_column(col_num,col_num, 20)
                        char_num += 1
                        col_num += 1
                        number_text = chr(char_num)
                        worksheet.set_column(col_num,col_num, 20)
                        heading_list = ['Account', 'Opening']
                    else:
                        heading_list = ['Account']
                    for analytic in analytic_account:
                        heading_list.append(analytic.name)
                    if wiz.include_opening:
                        heading_list.append('Current Period')
                        heading_list.append('Closing Balance')
                    else:
                        heading_list.append('Balance')

                else:
                    worksheet.set_column('B:B', 20)
                    heading_list = ['Account', 'Balance']
                    ending_col = "B"

            elif wiz.group_by_condition=="state":
                    col_num = 2
                    # char_num = 66
                    if wiz.state_ids:
                        for state in wiz.state_ids:
                            state_list.append(state)
                    else:
                        reg_id=self.env['sales.region'].search([])

                        for reg in reg_id:
                                if reg.state_id not in state_list:
                                    state_list.append(reg.state_id)
                    if state_list:
                        if wiz.include_opening:
                            col_num += 2
                        for i in state_list:
                            col_num += 1
                            # number_text = chr(char_num)
                            worksheet.set_column(col_num, col_num, 20)

                        if wiz.include_opening:
                            col_num += 1
                            # number_text = chr(char_num)

                            worksheet.set_column(col_num, col_num, 20)
                            col_num += 1
                            # number_text = chr(char_num)
                            worksheet.set_column(col_num, col_num, 20)
                            heading_list = ['Account', 'Opening']
                        else:
                            heading_list = ['Account']

                        for state in state_list:
                            heading_list.append(state.name)
                        if wiz.include_opening:
                            heading_list.append('Current Period')
                            heading_list.append('Closing Balance')
                        else:
                            heading_list.append('Balance')

        elif wiz.debit_credit:
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 20)
            worksheet.set_column('D:D', 20)
            show_deb_cre = True
            ending_col = "D"
            heading_list = ['Account', 'Debit', 'Credit', 'Balance']
            if wiz.include_opening:
                worksheet.set_column('E:E', 20)
                worksheet.set_column('F:F', 20)
                ending_col = "F"
                heading_list = ['Account', 'Opening', 'Debit', 'Credit', 'Current Period', 'Closing Balance']
        else:
            worksheet.set_column('B:B', 20)
            if wiz.include_opening:
                worksheet.set_column('C:C', 20)
                worksheet.set_column('D:D', 20)
                ending_col = "D"
                heading_list = ['Account', 'Opening Balance', 'Current Period', 'Closing Balance']



        worksheet.merge_range('A1:H1', self.env.company.name, heading_format)
        worksheet.merge_range('A2:H2', rep_data[0]['form']['account_report_id'][1], heading_format)
        row = 3
        if wiz.target_move == 'all':
            target_move = 'All Entries'
        else:
            target_move = 'All Posted Entries'
        worksheet.write(row, 0, "Target Moves : %s"%(target_move), bold)
        row += 1
        printed_on = self.get_current_datetime()
        worksheet.write(row, 0, "Printed On : %s"%(printed_on), bold)
        row += 1
        if wiz.date_from:
            date_from = datetime.strptime(str(wiz.date_from), "%Y-%m-%d")
            worksheet.write(row, 0, "Date From : %s"%(date_from.strftime("%d/%m/%Y")), bold)
            row += 1
        if wiz.date_to:
            date_to = datetime.strptime(str(wiz.date_to), "%Y-%m-%d")
            worksheet.write(row, 0, "Date To : %s"%(date_to.strftime("%d/%m/%Y")), bold)
            row += 1
        if service:
            if service.is_qshop_service:
                service_type='Qwqer Shop'
                worksheet.write(row, 0, "Type : %s"%(service_type), bold)
            elif service.is_fleet_service:
                service_type='Fleet'
                worksheet.write(row, 0, "Type : %s"%(service_type), bold)
            else:
                service_type='Delivery'
                worksheet.write(row, 0, "Type : %s"%(service_type), bold)
            row += 1
        row += 1
        col = 0
        for heading in heading_list:
            worksheet.write(row, col, heading, bold)
            col += 1
        row += 1
        tot_list = []
        self.generate_rec_row(worksheet, fin_data, row, bold, date_format, no_format, normal_num_bold, has_com, show_deb_cre,
                            wiz.trail_bal, wiz.include_opening,wiz.display_analytic_acc,wiz.state_ids,wiz.region_ids,wiz.group_by_condition,state_list,service)

