# -*- coding: utf-8 -*-

import time
from datetime import timedelta, datetime

from odoo import models, api, fields,_
from odoo.exceptions import UserError


class DayBookExcelReport(models.AbstractModel):
    _name = "report.base_accounting_kit.day_book_report_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def _get_account_move_entry(self, accounts, form_data, pass_date):
        cr = self.env.cr
        move_line = self.env['account.move.line']
        tables, where_clause, where_params = move_line._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        if form_data['target_move'] == 'posted':
            target_move = "AND m.state = 'posted'"
        else:
            target_move = ''
        sql = ('''
                SELECT l.id AS lid, acc.name as accname, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, 
                l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, 
                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,
                m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                JOIN account_account acc ON (l.account_id = acc.id) 
                WHERE l.account_id IN %s AND l.journal_id IN %s ''' + target_move + ''' AND l.date = %s
                GROUP BY l.id, l.account_id, l.date,
                     j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name , acc.name
                     ORDER BY l.date DESC
        ''')
        params = (
        tuple(accounts.ids), tuple(form_data['journal_ids']), pass_date)
        cr.execute(sql, params)
        data = cr.dictfetchall()
        res = {}
        debit = credit = balance = 0.00
        for line in data:
            debit += line['debit']
            credit += line['credit']
            balance += line['balance']
        res['debit'] = debit
        res['credit'] = credit
        res['balance'] = balance
        res['lines'] = data
        return res

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
        format4 = workbook.add_format({'align': 'left', 'bold': True, 'font_size': 10, 'bg_color': '#ededed;'})
        format3 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        format1 = workbook.add_format({'align': 'left', 'bold': True, 'font_size': 10})
        format2 = workbook.add_format({'align': 'left', 'bold': False, 'font_size': 10})
        head = workbook.add_format({'align': 'center', 'size': 12, 'bold': True})
        head2 = workbook.add_format({'align': 'center', 'size': 10, 'bold': True})
        head3 = workbook.add_format({'align': 'center', 'font_size': 10, 'bold': True, 'bg_color': '#808080'})
        worksheet = workbook.add_worksheet('Cash Book.xlsx')
        company_name = self.env.user.company_id.name
        company_street = self.env.user.company_id.street if self.env.user.company_id.street else ''
        company_street2 = self.env.user.company_id.street2 if self.env.user.company_id.street2 else ''
        company_city = self.env.user.company_id.city if self.env.user.company_id.city else ''
        company_zip = self.env.user.company_id.zip if self.env.user.company_id.zip else ''
        company_addr = str(company_street + ' , ' + ' ' + company_street2 + '  ' + company_city + '  ' + company_zip)
        company_mob = self.env.user.company_id.phone if self.env.user.company_id.phone else ''
        company_email = self.env.user.company_id.email if self.env.user.company_id.email else ''
        company_website = self.env.user.company_id.website if self.env.user.company_id.website else ''
        if company_mob and company_email and company_website:
            company_addr1 = 'Ph:' + company_mob + ',' + ' ' + 'Email:' + company_email + ',' + ' ' + 'Website:' + company_website
        else:
            company_addr1 = ''
        worksheet.set_column('A:A', 22)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 25)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 35)
        worksheet.set_column('F:F', 35)

        worksheet.merge_range('A1:F2', company_name, head)
        worksheet.merge_range('A3:F4', company_addr, head2)
        worksheet.merge_range('A5:F6', company_addr1, head2)

        row = 7
        column = 0

        worksheet.merge_range('B7:E7', 'Cash Book Report', head)
        row += 2

        # self.model = self.env.context.get('active_model')
        # docs = self.env[self.model].browse(
        #     self.env.context.get('active_ids', []))
        form_data = data['form']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        active_acc = data['form']['account_ids']
        accounts = self.env['account.account'].search(
            [('id', 'in', active_acc)]) if data['form']['account_ids'] else \
            self.env['account.account'].search([])

        date_start = datetime.strptime(form_data['date_from'],
                                       '%Y-%m-%d').date()
        date_end = datetime.strptime(form_data['date_to'], '%Y-%m-%d').date()
        days = date_end - date_start
        dates = []
        record = []
        for i in range(days.days + 1):
            dates.append(date_start + timedelta(days=i))
        for head in dates:
            pass_date = str(head)
            accounts_res = self.with_context(
                data['form'].get('used_context', {}))._get_account_move_entry(
                accounts, form_data, pass_date)
            if accounts_res['lines']:
                record.append({
                    'date': head,
                    'debit': accounts_res['debit'],
                    'credit': accounts_res['credit'],
                    'balance': accounts_res['balance'],
                    'child_lines': accounts_res['lines']
                })

        worksheet.write(row, column, 'Journals:', format1)
        worksheet.write(row, column + 5, 'Target Moves:', format1)
        row += 1

        worksheet.write(row, column, ', '.join([ lt or '' for lt in codes ]), format2)
        if data['form']['target_move'] == 'all':
            worksheet.write(row, column + 5, 'All Entries', format2)
        if data['form']['target_move'] == 'posted':
            worksheet.write(row, column + 5, 'All Posted Entries', format2)

        row += 2
        worksheet.write(row, column+5, 'Date from:', format1)
        from_date = fields.Date.from_string(data['form']['date_from']).strftime('%d/%m/%Y')
        worksheet.write(row, column+6, from_date, format2)

        row += 1
        worksheet.write(row, column + 5, 'Date to:', format1)
        from_to = fields.Date.from_string(data['form']['date_to']).strftime('%d/%m/%Y')
        worksheet.write(row, column + 6, from_to, format2)

        row += 2
        worksheet.write(row, column, 'Date', cell_text_format)
        worksheet.write(row, column + 1, 'JRNL', cell_text_format)
        worksheet.write(row, column + 2, 'Partner', cell_text_format)
        worksheet.write(row, column + 3, 'Ref', cell_text_format)
        worksheet.write(row, column + 4, 'Move', cell_text_format)
        worksheet.write(row, column + 5, 'Entry Label', cell_text_format)
        worksheet.write(row, column + 6, 'Debit', cell_text_format)
        worksheet.write(row, column + 7, 'Credit', cell_text_format)
        worksheet.write(row, column + 8, 'Balance', cell_text_format)
        # worksheet.write(row, column + 9, 'Currency', cell_text_format)

        for account in record:
            row += 1
            date = fields.Date.from_string(account['date']).strftime('%d/%m/%Y')
            worksheet.write(row + 1, column, date, format4)
            worksheet.write(row + 1, column + 1, '', format4)
            worksheet.write(row + 1, column + 2, '', format4)
            worksheet.write(row + 1, column + 3, '', format4)
            worksheet.write(row + 1, column + 4, '', format4)
            worksheet.write(row + 1, column + 5, '', format4)
            worksheet.write(row + 1, column + 6, account['debit'], format4)
            worksheet.write(row + 1, column + 7, account['credit'], format4)
            worksheet.write(row + 1, column + 8, account['balance'], format4)
            row += 1
            for line in account['child_lines']:
                date = fields.Date.from_string(line['ldate']).strftime('%d/%m/%Y')
                date = '  ' * 4 + date
                worksheet.write(row + 1, column,date, format3)
                worksheet.write(row + 1, column + 1, line['lcode'], format3)
                worksheet.write(row + 1, column + 2, line['partner_name'], format3)
                worksheet.write(row + 1, column + 3, line['lref'], format3)
                worksheet.write(row + 1, column + 4, line['move_name'], format3)
                worksheet.write(row + 1, column + 5, line['lname'], format3)
                worksheet.write(row + 1, column + 6, line['debit'], format3)
                worksheet.write(row + 1, column + 7, line['credit'], format3)
                worksheet.write(row + 1, column + 8, line['balance'], format3)
                row += 1
