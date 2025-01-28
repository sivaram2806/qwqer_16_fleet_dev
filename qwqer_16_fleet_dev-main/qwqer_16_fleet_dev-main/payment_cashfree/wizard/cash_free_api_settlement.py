# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CashFreeApiSettlement(models.TransientModel):
    _name = 'cash.free.api.settlement'
    _description = 'Cash Free API Settlement'

    date_from = fields.Date(string='Date From', requred=True)

    @api.model
    def default_get(self, field_list):
        res = super(CashFreeApiSettlement, self).default_get(field_list)
        credential = self.env['cash.free.credentials'].search([('company_id', '=', self.env.company.id)],limit=1)
        res.update({
            'date_from': credential.api_date
            })
        return res
    
    def action_cashfree_settlement(self):
        record = self.env['cash.free.settlement'].cash_free_api_import(self.env.company.id, self.date_from)
        return {
            'name': "Cash Free Settlement",
            'view_mode': 'tree,form',
            'res_model': 'cash.free.settlement',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }