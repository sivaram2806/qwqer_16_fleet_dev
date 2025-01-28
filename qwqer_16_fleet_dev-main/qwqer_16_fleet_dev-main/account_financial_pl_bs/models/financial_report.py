# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import datetime, timedelta

class AccountingReport(models.Model):
    _inherit = 'account.financial.report'
    
    trial_balance = fields.Boolean('Trial Balance?')
    trial_bal_retained_ear = fields.Boolean('Trial Balance Retained Earning?')
    hide_head = fields.Boolean('Hide Head in Report?')
    hide_report_total = fields.Boolean('Hide Total in Report?')
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ('opening_balance','Opening Balance'),
        ('closing_balance','Closing Balance')
        ], 'Type', default='sum')

    
class ReportFinancial(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_financial'

    def _compute_account_balance(self, accounts, service):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
        }
        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line__account_id', 'aa').replace('account_move_line', 'l')
            request = "SELECT l.account_id as id, " + ', '.join(mapping.values()) + \
                               " FROM account_move_line AS l JOIN account_move AS m  on l.move_id = m.id " + \
                      "INNER JOIN account_account AS aa ON l.account_id = aa.id " \
                      " WHERE l.account_id IN %s" \
                                + filters + \
                           " GROUP BY l.account_id"
            params = (tuple(accounts.ids),) + tuple(where_params)
            if service:
                service_obj = self.env["partner.service.type"].browse(service[0])

                if service_obj.is_delivery_service:
                    request = "SELECT l.account_id as id, " + ', '.join(mapping.values()) + \
                               " FROM account_move_line AS l JOIN account_move AS m  on l.move_id = m.id " + \
                      "INNER JOIN account_account AS aa ON l.account_id = aa.id " \
                               " WHERE l.account_id IN %s" \
                               " AND ( m.service_type_id IS NULL OR m.service_type_id = %s)" \
                                    + filters + \
                               " GROUP BY l.account_id"       
                elif service_obj.is_qshop_service:
                    request = "SELECT l.account_id as id, " + ', '.join(mapping.values()) + \
                               " FROM account_move_line AS l JOIN account_move AS m  on l.move_id = m.id " + \
                      "INNER JOIN account_account AS aa ON l.account_id = aa.id " \
                               " WHERE l.account_id IN %s" \
                               " AND m.service_type_id = %s" \
                                    + filters + \
                               " GROUP BY l.account_id"  
                               
                elif service_obj.is_fleet_service:
                    request = "SELECT l.account_id as id, " + ', '.join(mapping.values()) + \
                               " FROM account_move_line AS l JOIN account_move AS m  on l.move_id = m.id " + \
                      "INNER JOIN account_account AS aa ON l.account_id = aa.id " \
                               " WHERE l.account_id IN %s" \
                               " AND m.service_type_id = %s" \
                                    + filters + \
                               " GROUP BY l.account_id"  
                               
                params = (tuple(accounts.ids),) + tuple([service_obj.id]) + tuple(where_params)  #"AND l.service_type != 'qwqershop'" \
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res
    
    def _compute_analytic_account_balance(self, accounts,analytic_id_ist,service):
        """ compute the balance, debit and credit for the provided accounts
        """
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
        }
        
        if not analytic_id_ist:
            analytic_id_ist = self.env['account.analytic.account'].search([]).ids
        
        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            filters = filters.replace('account_move_line__move_id', 'm').replace(
                'account_move_line__account_id', 'aa').replace('account_move_line', 'l')
            request =  (
                    "SELECT l.account_id AS id, amlaa.account_analytic_account_id as analytic_account_id, "
                    + ", ".join(mapping.values())
                    + " FROM account_move_line AS l "
                    + "INNER JOIN account_move AS m ON m.id = l.move_id "
                    + "INNER JOIN account_account AS aa ON l.account_id = aa.id "
                    + "LEFT JOIN account_analytic_account_account_move_line_rel AS amlaa ON (l.id = amlaa.account_move_line_id) "
                    + "WHERE l.account_id IN %s AND amlaa.account_analytic_account_id IN %s "
                    + filters
                    + " GROUP BY l.account_id, amlaa.account_analytic_account_id"
            )
            params = (tuple(accounts.ids),)+ (tuple(analytic_id_ist),) + tuple(where_params)
            if service:
                service_obj = self.env["partner.service.type"].browse(service[0])
                if service_obj.is_delivery_service:
                    request = (
                        "SELECT l.account_id AS id, amlaa.account_analytic_account_id as analytic_account_id, "
                        + ", ".join(mapping.values())
                        + " FROM account_move_line AS l "
                        + "INNER JOIN account_move AS m ON m.id = l.move_id "
                        + "INNER JOIN account_account AS aa ON l.account_id = aa.id "
                        + "LEFT JOIN account_analytic_account_account_move_line_rel AS amlaa ON (l.id = amlaa.account_move_line_id) "
                        + "WHERE l.account_id IN %s AND amlaa.account_analytic_account_id IN %s "
                        + f" AND ( m.service_type_id IS NULL OR m.service_type_id = {service_obj.id} )"
                        + filters
                        + " GROUP BY l.account_id, amlaa.account_analytic_account_id")
                else:
                    request = (
                        "SELECT l.account_id AS id, amlaa.account_analytic_account_id as analytic_account_id, "
                        + ", ".join(mapping.values())
                        + " FROM account_move_line AS l "
                        + "INNER JOIN account_move AS m ON m.id = l.move_id "
                        + "INNER JOIN account_account AS aa ON l.account_id = aa.id "
                        + "LEFT JOIN account_analytic_account_account_move_line_rel AS amlaa ON (l.id = amlaa.account_move_line_id) "
                        + "WHERE l.account_id IN %s AND amlaa.account_analytic_account_id IN %s "
                        + f" AND m.service_type_id = {service_obj.id} "
                        + filters
                        + " GROUP BY l.account_id, amlaa.account_analytic_account_id")

                print(request)
                params = (tuple(accounts.ids),)  + (tuple(analytic_id_ist),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                analytic_account = self.env['account.analytic.account'].browse(row['analytic_account_id'])
                if row['id'] not in res.keys():
                    new_dict = {}
                    #if because None analytic account value in row
                    if analytic_account:
                        new_dict.update({row['analytic_account_id']:row['balance']})
                    else:
                        row['balance'] = 0.0
                    row['analytic_account_id'] = new_dict
                    res[row['id']] = row
                else:
                    temp = res[row['id']]
                    if analytic_account:
                        if temp.get('analytic_account_id'):
                            temp['analytic_account_id'].update({row['analytic_account_id']:row['balance']})
                        else:
                            temp['analytic_account_id'] = {row['analytic_account_id']:row['balance']}
                        temp['balance'] += row['balance']
        return res
    
    def _compute_report_balance(self, reports,display_analytic_acc,state_list,region_list,data):
        '''returns a dictionary with key=the ID of a record and value=the credit, debit and balance amount
           computed for this record. If the record is of type :
               'accounts' : it's the sum of the linked accounts
               'account_type' : it's the sum of leaf accounts with such an account_type
               'account_report' : it's the amount of the related report
               'sum' : it's the sum of the children of this record (aka a 'view' record)'''
        res = {}
        analytic_id_ist = []
        service=data['service_type_id']
        state = self.env['res.country.state'].search([('id','in',state_list)])
        region = self.env['sales.region'].search([('id','in',region_list)])
        if region_list:
                analytic_id_ist += region.mapped('analytic_account_id').ids
        elif state_list:
            for i in state:
                analytic_id_ist += i.regions_ids.mapped('analytic_account_id').ids
        
        analytic_domain = []
        if analytic_id_ist:
            analytic_domain = [('id','in',analytic_id_ist)]
        analytic_account = self.env['account.analytic.account'].search(analytic_domain)
        fields = ['credit', 'debit', 'analytic_values', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.trial_bal_retained_ear:
                continue
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                if not display_analytic_acc:
                    res[report.id]['account'] = self._compute_account_balance(report.account_ids,service)
                else:
                    res[report.id]['account'] = self._compute_analytic_account_balance(report.account_ids,analytic_id_ist,service)
                new_dict = {}
                for analytic in analytic_account:
                    new_dict.update({analytic.id:0.0})
                for value in res[report.id]['account'].values():
                    for field in fields:
                        if field == 'analytic_values':
                            if 'analytic_account_id' in value:
                                for analytic_id, analytic_value in value['analytic_account_id'].items():
                                    if analytic_id in new_dict:
                                        balance = new_dict.get(analytic_id) + analytic_value
                                        
                                        new_dict.update({analytic_id :balance})
                                    else:
                                        new_dict.update({analytic_id :analytic_value})
                            
                            res[report.id][field] = new_dict
                        else:
                            res[report.id][field] += value.get(field)
                        
            elif report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('account_type', 'in', report.account_type_ids.mapped("type"))])
                if not display_analytic_acc:
                    res[report.id]['account'] = self._compute_account_balance(accounts,service)
                else:
                    res[report.id]['account'] = self._compute_analytic_account_balance(accounts,analytic_id_ist,service)
                
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field, 0.0)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id,display_analytic_acc,state_list,region_list,data)
                new_dict = {}
                for analytic in analytic_account:
                    new_dict.update({analytic.id:0.0})
                for key, value in res2.items():
                    for field in fields:
                        if field == 'analytic_values':
                            if 'analytic_account_id' in value:
                                for analytic_id, analytic_value in value['analytic_account_id'].items():
                                    if analytic_id in new_dict:
                                        balance = new_dict.get(analytic_id) + analytic_value
                                        
                                        new_dict.update({analytic_id :balance})
                                    else:
                                        new_dict.update({analytic_id :analytic_value})
                            if 'analytic_values' in value and type(value['analytic_values']) != float:
                                for analytic_id, analytic_value in value['analytic_values'].items():
                                    if analytic_id in new_dict:
                                        balance = new_dict.get(analytic_id) + analytic_value
                                        
                                        new_dict.update({analytic_id :balance})
                                    else:
                                        new_dict.update({analytic_id :analytic_value})
                            
                            res[report.id][field] = new_dict
                        else:
                            res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids,display_analytic_acc,state_list,region_list,data)
                new_dict = {}
                for analytic in analytic_account:
                    new_dict.update({analytic.id:0.0})
                for key, value in res2.items():
                    for field in fields:
                        if field == 'analytic_values':
                            if 'analytic_account_id' in value:
                                for analytic_id, analytic_value in value['analytic_account_id'].items():
                                    if analytic_id in new_dict:
                                        balance = new_dict.get(analytic_id) + analytic_value
                                        
                                        new_dict.update({analytic_id :balance})
                                    else:
                                        new_dict.update({analytic_id :analytic_value})
                            if 'analytic_values' in value and type(value['analytic_values']) != float:
                                for analytic_id, analytic_value in value['analytic_values'].items():
                                    if analytic_id in new_dict:
                                        balance = new_dict.get(analytic_id) + analytic_value
                                        
                                        new_dict.update({analytic_id :balance})
                                    else:
                                        new_dict.update({analytic_id :analytic_value})
                            
                            res[report.id][field] = new_dict
                        else:
                            res[report.id][field] += value.get(field)
                            
            elif report.type == 'opening_balance':
                if not display_analytic_acc:
                    res[report.id]['account'] = self._compute_account_balance(report.account_ids,service)
                else:
                    res[report.id]['account'] = self._compute_analytic_account_balance(report.account_ids,analytic_id_ist,service)
                new_dict = {}
                for analytic in analytic_account:
                    new_dict.update({analytic.id:0.0})
                if res[report.id].get('account'):
                    acc_ope_balance = 0.0
                    acc_ope_credit = 0.0 
                    acc_ope_debit = 0.0
                    for account_id, value in res[report.id]['account'].items():
                        acc_id = self.env['account.account'].browse(account_id)
                        data['comparison_context']['from_tb'] = True
                        data['comparison_context']['date_from'] = self._context.get('date_from')
                        result = self.with_context(data.get('comparison_context')).get_opening_bal(account_id,report,service)
                        acc_ope_balance += result['balance'] 
                        acc_ope_credit += result['credit'] 
                        acc_ope_debit += result['debit']
                for field in fields:
                    if field == 'analytic_values':
                        
                        res[report.id][field] = new_dict
                    elif field == 'balance':
                        res[report.id][field] = acc_ope_balance
                    elif field == 'credit' :
                        res[report.id][field] = acc_ope_credit
                    elif field == 'debit' :
                        res[report.id][field] = acc_ope_debit
                    else:
                        res[report.id][field] += value.get(field)
            
            elif report.type == 'closing_balance':
                if not display_analytic_acc:
                    res[report.id]['account'] = self._compute_account_balance(report.account_ids,service)
                else:
                    res[report.id]['account'] = self._compute_analytic_account_balance(report.account_ids,analytic_id_ist,service)
                new_dict = {}
                for analytic in analytic_account:
                    new_dict.update({analytic.id:0.0})
                    
                acc_clo_balance = 0.0
                acc_clo_credit = 0.0 
                acc_clo_debit = 0.0
                if res[report.id].get('account'):
                    for account_id, value in res[report.id]['account'].items():
                        data['comparison_context']['from_tb'] = True
                        to_date = datetime.strptime(self._context.get('date_to'), "%Y-%m-%d") +timedelta(days=1)
                        data['comparison_context']['date_from'] = to_date
                        result = self.with_context(data.get('comparison_context')).get_opening_bal(account_id,report,service)
                        acc_clo_balance += result['balance'] 
                        acc_clo_credit += result['credit'] 
                        acc_clo_debit += result['debit']
                for field in fields:
                    if field == 'analytic_values':
                        res[report.id][field] = new_dict
                    elif field == 'balance':
                        res[report.id][field] = acc_clo_balance
                    elif field == 'credit' :
                        res[report.id][field] = acc_clo_credit
                    elif field == 'debit' :
                        res[report.id][field] += acc_clo_debit
                    else:
                        res[report.id][field] += value.get(field)
                        
        return res
    
    
    def get_opening_bal(self, account_id,report,service):
        res = {}
        fields = ['credit', 'debit', 'balance']
        date_from = self._context.get('date_from')
        if date_from:
            where_cond = "where am.state='posted' and aml.account_id = %s and aml.date < '%s' and aml.company_id = %s"%(
                                    account_id, date_from, self.env.company.id)
            if service:
                service_obj = self.env["partner.service.type"].browse(service[0])
                if service_obj.is_delivery_service:
                    where_cond = "where am.state='posted' and aml.account_id = %s and aml.date < '%s' and aml.company_id = %s and (aml.service_type_id IS NULL or aml.service_type_id ='%s')"%(
                                    account_id, date_from, self.env.company.id, service_obj.id)
                elif service_obj.is_qshop_service:
                    where_cond = "where am.state='posted' and aml.account_id = %s and aml.date < '%s' and aml.company_id = %s and aml.service_type_id ='%s'"%(
                                    account_id, date_from, self.env.company.id, service_obj.id)

                elif service_obj.is_fleet_service:
                    where_cond = "where am.state='posted' and aml.account_id = %s and aml.date < '%s' and aml.company_id = %s and aml.service_type_id ='%s'"%(
                                    account_id, date_from, self.env.company.id, service_obj.id)
                    
        else:
            where_cond = "where am.state='posted' and aml.account_id = %s  and aml.company_id = %s"%(account_id,
                                                                                                  self.env.company.id)
            if service:
                service_obj = self.env["partner.service.type"].browse(service[0])
                if service_obj.is_delivery_service:
                    where_cond = "where am.state='posted' and aml.account_id = %s  and aml.company_id = %s and (aml.service_type_id IS NULL or aml.service_type_id ='%s')"%(account_id,
                                                                                                  self.env.company.id, service_obj.id)
                elif service_obj.is_qshop_service:
                    where_cond = "where am.state='posted' and aml.account_id = %s  and aml.company_id = %s and aml.service_type_id = '%s'"%(account_id,
                                                                                                  self.env.company.id, service_obj.id)

                elif service_obj.is_fleet_service:
                    where_cond = "where am.state='posted' and aml.account_id = %s  and aml.company_id = %s and aml.service_type_id = '%s'"%(account_id,
                                                                                                  self.env.company.id, service_obj.id)
                    
        sql = """SELECT COALESCE(sum(aml.debit), 0.00) as debit, COALESCE(sum(aml.credit), 0.00) as credit,
                    COALESCE(sum(aml.amount_currency), 0.00) as amount_currency
                    from account_move_line aml
                    left join account_move am on am.id = aml.move_id %s"""%(where_cond)
        self.env.cr.execute(sql)
        sql_data = self.env.cr.dictfetchall()
        ret_debit = sql_data[0]['debit']
        ret_credit = sql_data[0]['credit']
        balance = ret_debit - ret_credit
        res['debit'] = (balance >= 0.00 and balance or 0.00) * float(report.sign)
        res['credit'] = (balance < 0.00 and balance or 0.00) * float(report.sign)
        res['balance'] = balance * float(report.sign)
        return res
    
    
    def get_account_lines(self, data):
        lines = []
        is_trial_balance_retained_earning = False
        trial_balance_retained_total = 0.0
        service=data['service_type_id']
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports,data['display_analytic_acc'],data['state_ids'],data['region_ids'],data)
        analytic_id_ist = []
        state = self.env['res.country.state'].search([('id','in',data['state_ids'])])
        region = self.env['sales.region'].search([('id','in',data['region_ids'])])
        if data['region_ids']:
            analytic_id_ist += region.mapped('analytic_account_id').ids
        elif data['state_ids']:
            for i in state:
                analytic_id_ist += i.regions_ids.mapped('analytic_account_id').ids
        
        analytic_domain = []
        if analytic_id_ist:
            analytic_domain = [('id','in',analytic_id_ist)]
        analytic_account = self.env['account.analytic.account'].search(analytic_domain)
        show_zero_bal = data['show_zero_bal']
        if account_report.trial_bal_retained_ear == True:
            is_trial_balance_retained_earning = True
        
        if data['enable_filter']:
            if account_report.trial_balance:
                data['comparison_context']['strict_range'] = False
                data['comparison_context']['initial_bal'] = True
                data['comparison_context']['date_from'] = data['date_from']
                data['comparison_context']['date_to'] = data['date_to']
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports,data['display_analytic_acc'],data['state_ids'],data['region_ids'],data)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                res[report_id]['comp_bal_debit'] = value['debit']
                res[report_id]['comp_bal_credit'] = value['credit']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']
                        report_acc[account_id]['comp_bal_debit'] = val['debit']
                        report_acc[account_id]['comp_bal_credit'] = val['credit']
        elif data['include_opening']:
            data['comparison_context']['strict_range'] = False
            data['comparison_context']['date_from'] = data['date_from']
            data['comparison_context']['initial_bal'] = True
            data['comparison_context']['date_to'] = data['date_to']
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports,data['display_analytic_acc'],data['state_ids'],data['region_ids'],data)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                res[report_id]['comp_bal_debit'] = value['debit']
                res[report_id]['comp_bal_credit'] = value['credit']
                report_acc = res[report_id].get('account')
                if report_acc:
                    if comparison_res[report_id].get('account'):
                        for account_id, val in comparison_res[report_id].get('account').items():
                            report_acc[account_id]['comp_bal'] = val['balance']
                            report_acc[account_id]['comp_bal_debit'] = val['debit']
                            report_acc[account_id]['comp_bal_credit'] = val['credit']
        if child_reports and child_reports.filtered(lambda cr:cr.trial_bal_retained_ear == True):
            is_trial_balance_retained_earning = True
        for report in child_reports: # TODO
            include_balance = False
            opening_balance = 0.0
            opening_credit = 0.0
            opening_debit = 0.0
            analytic_opening = {}
            for analytic in analytic_account:
                analytic_opening.update({analytic.id:0.0})
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * float(report.sign),
                'type': 'report',
                'level': report.level,
                'account_type': report.type or False,
                'hide_report_head':report.hide_head,
                'hide_total_report' : report.hide_report_total
            }
            if res[report.id]['analytic_values']:
                for i,i_val in res[report.id]['analytic_values'].items():
                    res[report.id]['analytic_values'][i] = i_val* float(report.sign)
                vals['analytic_values'] = res[report.id]['analytic_values']
            else:
                new_dict = {}
                for analytic in analytic_account:
                    new_dict.update({analytic.id:0.0})
                vals['analytic_values'] = new_dict
                # vals['analytic_values'] = value['debit']
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']
            if report.trial_bal_retained_ear:
                is_trial_balance_retained_earning = True
                date_to = data['date_from']
                domain = [('account_id.include_initial_balance', '=', False),
                          ('date', '<', date_to),
                          ('move_id.state', '=', data['target_move']),
                         ]
                query = self.env['account.move.line']._where_calc(domain)
                tables, where_clause, where_clause_params = query.get_sql()
                sql = """
                select
                    COALESCE(sum(account_move_line.debit), 0.00) as debit,
                    COALESCE(sum(account_move_line.credit), 0.00) as credit
                from
                    %s
                where
                    %s
                """%(tables, where_clause)
                self.env.cr.execute(sql, where_clause_params)
                sql_data = self.env.cr.dictfetchall()
                ret_debit = sql_data[0]['debit']
                ret_credit = sql_data[0]['credit']
                balance = ret_debit - ret_credit
                vals['debit'] = 0.0
                vals['credit'] = 0.0
                vals['balance'] = 0.0
                include_balance = True
                opening_balance +=  balance #* report.sign
                opening_credit += (balance < 0.00 and balance or 0.00) #* report.sign
                opening_debit += (balance >= 0.00 and balance or 0.00) #* report.sign
            if data['enable_filter'] or report.type =='sum':
                vals['balance_cmp_debit'] = res[report.id].get('comp_bal_debit',0) * float(report.sign)
                vals['balance_cmp_credit'] = res[report.id].get('comp_bal_credit',0) * float(report.sign)
                vals['balance_cmp'] = res[report.id].get('comp_bal',0) * float(report.sign)
            if res[report.id].get('account'):
                for account_id, value in res[report.id]['account'].items():
                    acc_id = self.env['account.account'].browse(account_id)
                    if data['include_opening'] and acc_id.include_initial_balance:
                        data['comparison_context']['from_tb'] = True
                        result = self.with_context(data.get('comparison_context')).get_opening_bal(account_id,report,service)
                        opening_balance += result['balance'] 
                        opening_credit += result['credit'] 
                        opening_debit += result['debit']
                    if acc_id.include_initial_balance:
                        include_balance = True
            if data['include_opening'] and report.type !='sum':
                vals['balance_cmp_debit'] = abs(opening_debit) * float(report.sign)
                vals['balance_cmp_credit'] = abs(opening_credit) * float(report.sign)
                vals['balance_cmp'] = abs(opening_balance) * float(report.sign)
            
            if data['include_opening'] and report.type =='account_report':
                profit_loss_id = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0').id
                account_ids = []
                if report.account_report_id.id == profit_loss_id:
                    account_ids = self.env['account.account'].search([('is_pl_account', '=', True)])
                for account_id in account_ids:
                    if data['include_opening'] and account_id.include_initial_balance:
                        data['comparison_context']['from_tb'] = True
                        result = self.with_context(data.get('comparison_context')).get_opening_bal(account_id.id,report,service)
                        opening_balance += result['balance'] 
                        opening_credit += result['credit'] 
                        opening_debit += result['debit']
                vals['balance_cmp_debit'] = abs(opening_debit) * float(report.sign)
                vals['balance_cmp_credit'] = abs(opening_credit) * float(report.sign)
                vals['balance_cmp'] = abs(opening_balance) * float(report.sign)
            
            vals.update({'include_balance':include_balance})
            lines.append(vals)
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value in res[report.id]['account'].items():
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    vals = {
                        'name': account.code + ' ' + account.name,
                             'balance': value['balance'] * float(report.sign) or 0.0,
                             'type': 'account',
                             'level': report.display_detail == 'detail_with_hierarchy' and 7,
                             'account_type': account.account_type,
                             'account_id':account and account.id or False,
                             'include_balance':account and account.include_initial_balance or \
                                         False
                    }
                    if data['display_analytic_acc']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if value.get('analytic_account_id'):
                            for i,i_val in value['analytic_account_id'].items():
                                value['analytic_account_id'][i] = i_val* float(report.sign)
                                
                            vals['analytic_values'] = value['analytic_account_id']
                        else:
                            new_dict = {}
                            for analytic in analytic_account:
                                new_dict.update({analytic.id:0.0})
                            vals['analytic_values'] = new_dict
                        if not account.company_id.currency_id.is_zero(vals['balance']):
                            flag = True
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = float(value['comp_bal']) * float(report.sign)
                        vals['balance_cmp_debit'] = value['comp_bal_debit'] * float(report.sign)
                        vals['balance_cmp_credit'] = value['comp_bal_credit'] * float(report.sign)
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']) or \
                            not account.company_id.currency_id.is_zero(vals['balance_cmp_debit']) or \
                            not account.company_id.currency_id.is_zero(vals['balance_cmp_credit']):
                            flag = True
                    if data['include_opening']:
                        result = self.with_context(data.get('comparison_context')).get_opening_bal(account_id,report,service)
                        print(result)
                        vals['balance_cmp'] = abs(result['balance']) * float(report.sign)
                        vals['balance_cmp_debit'] = abs(result['debit']) * float(report.sign)
                        vals['balance_cmp_credit'] = abs(result['credit']) * float(report.sign) 
                        opening_balance += vals['balance_cmp']
                        opening_credit += vals['balance_cmp_credit']
                        opening_debit += vals['balance_cmp_debit']
                        
                        analytic_opening = {}
                        for analytic in analytic_account:
                            analytic_opening.update({analytic.id:0.0})
                               
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']) or \
                            not account.company_id.currency_id.is_zero(vals['balance_cmp_debit']) or \
                            not account.company_id.currency_id.is_zero(vals['balance_cmp_credit']):
                            flag = True
                            
                    if vals.get('include_balance',False) == True  and vals.get('level',0) > 3 and is_trial_balance_retained_earning == True:
                        trial_balance_retained_total += (vals.get('balance_cmp_debit',0)-vals.get('balance_cmp_credit',0))
                    
                    if flag:
                        if not show_zero_bal:
                            if value.get('comp_bal',0) !=0.0 or value['debit'] !=0.0 or  value['credit'] !=0.0 or value['balance'] !=0.0:
                                sub_lines.append(vals)
                        else:
                            sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
                
                
        if lines and is_trial_balance_retained_earning == True:
            if lines[0].get('balance_cmp',0) > 0.0:
                if  trial_balance_retained_total < 0.0:
                    trial_balance_retained_total = -1 *trial_balance_retained_total
                if  trial_balance_retained_total > 0.0:
                    trial_balance_retained_total =  trial_balance_retained_total
            elif lines[0].get('balance_cmp',0) < 0.0:
                if  trial_balance_retained_total < 0.0:
                    trial_balance_retained_total = -1 *trial_balance_retained_total
                if  trial_balance_retained_total > 0.0:
                    trial_balance_retained_total =  trial_balance_retained_total
            lines[0].update({'balance_cmp':lines[0].get('balance_cmp',0) + trial_balance_retained_total})
                
        return lines