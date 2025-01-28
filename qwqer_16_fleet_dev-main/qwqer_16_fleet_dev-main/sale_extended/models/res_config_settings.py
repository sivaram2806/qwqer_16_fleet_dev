# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CompanyExtended(models.Model):
    _inherit = 'res.company'

    credit_journal_date = fields.Date(string="Credit Journal Creation")
    credit_journal_limit = fields.Integer(string="Credit Journal Creation Limit")
    credit_journal_id = fields.Many2one('account.journal',string='Journal')
    product_id = fields.Many2one('product.template')
    csv_fetch_batch_limit = fields.Integer(string="Batch Limit")
    report_download_file_path = fields.Char(string="File Path")
    path = fields.Char(string="Module Name")
    customer_balance_sync_api_auth = fields.Char('Authorization Token')
    customer_balance_sync_api_url = fields.Char('URL')
    customer_balance_sync_api_limit = fields.Integer('Limit')




class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    credit_journal_date = fields.Date(related='company_id.credit_journal_date', string="Credit Journal Creation",readonly=False)
    credit_journal_limit = fields.Integer(related='company_id.credit_journal_limit',
                                          string="Credit Journal Creation Limit",readonly=False)
    credit_journal_id = fields.Many2one(related='company_id.credit_journal_id',readonly=False,string='Journal')
    product_id = fields.Many2one(related='company_id.product_id',readonly=False)
    csv_fetch_batch_limit = fields.Integer(related="company_id.csv_fetch_batch_limit",readonly=False)
    report_download_file_path = fields.Char(related="company_id.report_download_file_path",readonly=False)
    path = fields.Char(related="company_id.path",string="Module Name",readonly=False)

    customer_balance_sync_api_auth = fields.Char(related='company_id.customer_balance_sync_api_auth', readonly=False, string='Authorization Token')
    customer_balance_sync_api_url = fields.Char(related='company_id.customer_balance_sync_api_url', readonly=False, string='URL')
    customer_balance_sync_api_limit = fields.Integer(related='company_id.customer_balance_sync_api_limit', readonly=False, string='Limit')


