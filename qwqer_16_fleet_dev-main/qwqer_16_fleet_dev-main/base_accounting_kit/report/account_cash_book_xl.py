import logging

from odoo import models, fields

_logger = logging.getLogger('__name__')


class InvoiceExcelReport(models.AbstractModel):
    _name = "report.base_accounting_kit.report_cash_book_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def _get_account_move_entry(self, accounts, init_balance, sortby,
                                display_account):

        cr = self.env.cr
        move_line = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = move_line.with_context(
                date_from=self.env.context.get('date_from'), date_to=False,
                initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id',
                                           'm').replace('account_move_line',
                                                        'l')
            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                    '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                    NULL AS currency_id,\
                    '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                    '' AS partner_name\
                    FROM account_move_line l\
                    LEFT JOIN account_move m ON (l.move_id=m.id)\
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    JOIN account_journal j ON (l.journal_id=j.id)\
                    WHERE l.account_id IN %s""" + filters + ' GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)
        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = move_line._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace(
            'account_move_line', 'l')

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
                m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
                FROM account_move_line l\
                JOIN account_move m ON (l.move_id=m.id)\
                LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                JOIN account_journal j ON (l.journal_id=j.id)\
                JOIN account_account acc ON (l.account_id = acc.id) \
                WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)
        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(
                    res['balance']):
                account_res.append(res)

        return account_res

    def generate_xlsx_report(self, workbook, data, obj):
        cell_text_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 10})
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
        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = 'movement'
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search(
                         [('id', 'in', data['form']['journal_ids'])])]
        account_ids = data['form']['account_ids']
        accounts = self.env['account.account'].search(
            [('id', 'in', account_ids)])
        accounts_res = self.with_context(
            data['form'].get('used_context', {}))._get_account_move_entry(
            accounts,
            init_balance,
            sortby,
            display_account)

        worksheet.write(row, column, 'Journals:', format1)
        worksheet.write(row, column + 3, 'Display Account', format1)
        worksheet.write(row, column + 5, 'Target Moves:', format1)
        row += 1

        worksheet.write(row, column, ', '.join([lt or '' for lt in codes]), format2)
        if data['form']['display_account'] == 'all':
            worksheet.write(row, column + 3, 'All accounts', format2)
        if data['form']['display_account'] == 'movement':
            worksheet.write(row, column + 3, 'With movements', format2)
        if data['form']['display_account'] == 'not_zero':
            worksheet.write(row, column + 3, 'With balance not equal to zero', format2)
        if data['form']['target_move'] == 'all':
            worksheet.write(row, column + 5, 'All Entries', format2)
        if data['form']['target_move'] == 'posted':
            worksheet.write(row, column + 5, 'All Posted Entries', format2)

        row += 2
        worksheet.write(row, column, 'Sorted By:', format1)
        worksheet.write(row, column + 5, 'Date from:', format1)
        if data['form']['date_from']:
            from_date = fields.Date.from_string(data['form']['date_from']).strftime('%d/%m/%Y')
            worksheet.write(row, column + 6, from_date, format2)

        row += 1
        if data['form']['sortby'] == 'sort_date':
            worksheet.write(row, column, 'Date', format2)
        if data['form']['sortby'] == 'sort_journal_partner':
            worksheet.write(row, column, 'Journal and Partner', format2)
        worksheet.write(row, column + 5, 'Date to:', format1)
        if data['form']['date_to']:
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
        worksheet.write(row, column + 9, 'Currency', cell_text_format)

        for account in accounts_res:
            row += 1
            worksheet.write(row + 1, column, account['code'] + account['name'], format3)
            worksheet.write(row + 1, column + 1, '', format3)
            worksheet.write(row + 1, column + 2, '', format3)
            worksheet.write(row + 1, column + 3, '', format3)
            worksheet.write(row + 1, column + 4, '', format3)
            worksheet.write(row + 1, column + 5, '', format3)
            worksheet.write(row + 1, column + 6, account['debit'], format3)
            worksheet.write(row + 1, column + 7, account['credit'], format3)
            worksheet.write(row + 1, column + 8, account['balance'], format3)
            row += 1
            for line in account['move_lines']:
                if line['ldate']:
                    date = fields.Date.from_string(line['ldate']).strftime('%d/%m/%Y')
                    worksheet.write(row + 1, column, date, format3)
                worksheet.write(row + 1, column + 1, line['lcode'], format3)
                worksheet.write(row + 1, column + 2, line['partner_name'], format3)
                worksheet.write(row + 1, column + 3, line['lref'], format3)
                worksheet.write(row + 1, column + 4, line['move_name'], format3)
                worksheet.write(row + 1, column + 5, line['lname'], format3)
                worksheet.write(row + 1, column + 6, line['debit'], format3)
                worksheet.write(row + 1, column + 7, line['credit'], format3)
                worksheet.write(row + 1, column + 8, line['balance'], format3)
                row += 1
