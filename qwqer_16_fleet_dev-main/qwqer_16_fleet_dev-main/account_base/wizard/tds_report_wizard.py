# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError


class TdsReportWizard(models.TransientModel):
    _name = "tds.report.wizard"
    _description = "Tds Report Wizard"

    from_date = fields.Date(string="From Date", default=fields.Date.today())
    to_date = fields.Date(string="To Date", default=fields.Date.today())
    type = fields.Selection([('out_invoice', 'TDS Customer'),
                             ('in_invoice', 'TDS Vendor')], string="Type", default="in_invoice")
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.company)
    account_tax_ids = fields.Many2many('account.tax', 'rel_account_tax',
                                'account_id', 'account_tax_id', string='Section')
    sections = fields.Char(string="Sections")


    @api.onchange('account_tax_ids')
    def onchange_account_tax_ids(self):
        for rec in self:
            s = ""
            rec.sections = ""
            if rec.account_tax_ids:
                for section in rec.account_tax_ids:
                    if section.name:
                        s = s + section.name + ' ' + '/'
                        rec.sections = s

    def action_print(self):
        for rec in self:
            if rec.from_date > rec.to_date:
                raise ValidationError('From Date must be less than To Date')

            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'tds.report.wizard',
                }
            return self.env.ref('account_base.tds_export_xlsx_report').report_action(self, data=data)



