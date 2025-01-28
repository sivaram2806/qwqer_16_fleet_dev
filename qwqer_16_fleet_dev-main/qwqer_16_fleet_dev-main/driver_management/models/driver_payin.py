from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
from datetime import datetime


class DriverPayIn(models.Model):
    _name = 'driver.payin'
    _description = 'Driver Payin'
    _order = 'id desc'

    name = fields.Char(string='Driver ID ')
    remit_amount = fields.Float(string='Remit Amount')
    remit_date = fields.Datetime(string='Remit Date')
    remit_remarks = fields.Text(string="Remit Remarks")
    qwqer_ref_no = fields.Char(string='QWQER Ref No ')
    pg_ref_no = fields.Char(string='PG Ref No ')
    operation = fields.Char(string='Operation')
    journal_id = fields.Many2one(comodel_name="account.journal", string='Journal')
    entry_id = fields.Many2one(comodel_name='account.move', string='Entry')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', store=True)
    validated = fields.Boolean(string="validated")
    region_id = fields.Many2one(comodel_name='sales.region', string="Region", store=1)
    employee_id = fields.Many2one(comodel_name="hr.employee", string='Driver Name', store=1)
    state = fields.Selection(selection=[('draft', 'Draft'), ('paid', 'validated')], readonly=True, default='draft',
                             string="State")
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)

    _sql_constraints = [
        ('pg_ref_no_unique', 'unique (pg_ref_no)',
         "PG Ref no  already exists!"),
    ]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.region_id = self.employee_id.region_id.id
            self.name = self.employee_id.driver_uid
            if self.employee_id.related_partner_id.id:
                self.partner_id = self.employee_id.related_partner_id.id
        elif self.name:
            driver = self.env['hr.employee'].search([('driver_uid', '=', self.name)])
            if driver:
                self.employee_id = driver.id
                self.region_id = driver.region_id.id
                if driver.related_partner_id.id:
                    self.partner_id = driver.related_partner_id.id

    @api.model
    def create(self, vals):
        res = super(DriverPayIn, self).create(vals)
        if vals.get("remit_amount") == 0.0:
            raise UserError(_("Remit Amount should be Greater than zero"))
        driver_pay_in_journal_id = self.env.company.journal_id.id
        validate = self.env.company.is_validated
        if driver_pay_in_journal_id:
            if not res.journal_id:
                res.update({
                    'journal_id': driver_pay_in_journal_id or False,
                })
        res.onchange_employee_id()
        if validate:
            res.create_driver_payin_entry()
        return res

    def create_driver_payin_entry(self):
        try:
            vals = {}
            driver_credit_account_id = self.env.company.driver_credit_account
            driver_debit_account_id = self.env.company.driver_debit_account
            if not driver_debit_account_id and driver_credit_account_id:
                raise UserError('Please configure credit and debit accounts of driver')

            vals.update({
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'company_id': self.env.user.company_id.id,
                'currency_id': self.env.user.company_id.currency_id.id,
                'move_type': "entry",
                'region_id':self.region_id.id,
                'ref': self.pg_ref_no,
                'date': self.remit_date,

            })
            move_line_1 = {
                'partner_id': self.partner_id.id,
                'account_id': driver_credit_account_id.id,
                'credit': self.remit_amount,
                'debit': 0.0,
                'journal_id': self.journal_id.id,
                'name': 'Driver Payin',
            }
            move_line_2 = {
                'account_id': driver_debit_account_id.id,
                'credit': 0.0,
                'debit': self.remit_amount,
                'journal_id': self.journal_id.id,
                'name': 'Driver Payin',
            }
            vals.update(
                {'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)]
                 }
            )
            account_move = self.env['account.move'].sudo().create(vals)
            if account_move:
                account_move.sudo().post()
                self.entry_id = account_move.id
                self.state = 'paid'
        except Exception as e:
            raise UserError(e)

    # TODO if cash payin need add this
    # def reset_to_draft_cash_payin(self):
    #     if self.payment_id:
    #         self.payment_id.action_draft()
    #         self.payment_id.cancel()
    #         self.state = 'draft'
    #         self.payment_id = False

    def update_region(self):
        for rec in self:
            driver = self.env['hr.employee'].search([('driver_id', '=', rec.name)])
            if driver and driver.region_id:
                rec.employee_id = driver.id
                rec.region_id = driver.region_id.id
                if rec.payment_id:
                    journal_item = self.env['account.move.line'].search([('payment_id', '=', rec.payment_id.id)])
                    for item in journal_item:
                        item.region_id = driver.region_id.id
                        item.move_id.region_id = driver.region_id.id
