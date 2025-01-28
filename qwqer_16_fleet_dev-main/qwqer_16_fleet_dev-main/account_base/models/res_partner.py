# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """ The model res_partner is inherited to make modifications """
    _inherit = 'res.partner'

    tds_threshold_check = fields.Boolean(string='Check TDS Threshold', default=True)

    virtual_bank_acc = fields.Char(string='Virtual Bank Account')
    
    account_no = fields.Char(string='Account No')
    ifsc_code = fields.Char(string='IFSC Code')
    bank_name = fields.Char(string='Bank Name', copy=False)

    _sql_constraints = [
        ('virtual_bank_acc_unique', 'unique (virtual_bank_acc)',
         "Virtual Bank Account already exists!"),
    ]

# TODO: uncomment the code on jan 31
    # @api.model
    # def create(self, vals):
    #     customer_sequence = self.env['ir.sequence'].search(
    #         [('code', '=', 'customer.ref.key.seq')])
    #     if customer_sequence:
    #         vals['customer_ref_key'] = self.env['ir.sequence'].next_by_code('customer.ref.key.seq')
    #     return super(ResPartner, self).create(vals)


    def generate_virtual_sequence(self):
        company_id = self.company_id
        if company_id.id:
            virtual_sequence = self.env['ir.sequence'].search([('company_id', '=', company_id.id),('code','=','virtual.acc.statement.seq')])
            if not virtual_sequence:
                sequence = self.env['ir.sequence'].search([('code', '=', 'virtual.acc.statement.seq')], limit=1)
                new_sequence = sequence.sudo().copy()
                new_sequence.company_id = company_id
                self.virtual_bank_acc = new_sequence.next_by_id()
            else:
                self.virtual_bank_acc = self.env['ir.sequence'].next_by_code('virtual.acc.statement.seq')



