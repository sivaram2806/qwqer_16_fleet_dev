# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountMoveInherited(models.Model):
    """ The model account_move is inherited to make modifications """
    _inherit = 'account.move'

    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')
    segment_id = fields.Many2one(comodel_name='partner.segment', string='Customer Segment')
    journal_gstin_partner_id = fields.Many2one("res.partner", related="journal_id.l10n_in_gstin_partner_id")
    region_id = fields.Many2one(comodel_name='sales.region', string="Region", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    customer_type = fields.Selection([('b2c', 'B2C'), ('b2b', 'B2B')],string='Customer Type', store=True, readonly=True)
    sales_person_id = fields.Many2one('hr.employee', string='Sales Person')

    company_name = fields.Char(string="Company Name")
    company_street = fields.Char(string="Company Street")
    company_street2 = fields.Char(string="Company Street2")
    company_city = fields.Char(string="Company City")
    company_state_id = fields.Many2one(comodel_name='res.country.state', string='Company State')
    company_zip = fields.Char(string="Company Zip")
    company_country_id = fields.Many2one(comodel_name='res.country', string='Company Country')
    company_gst_no = fields.Char(string="Company GSTIN", store=True)

    customer_street = fields.Char(string="Customer Street")
    customer_street2 = fields.Char(string="Customer Street2")
    customer_city = fields.Char(string="Customer City")
    customer_state_id = fields.Many2one(comodel_name='res.country.state', string='Customer State')
    customer_zip = fields.Char(string="Customer Zip")
    customer_email = fields.Char(string="Customer Email")
    customer_country_id = fields.Many2one(comodel_name='res.country', string='Customer Country')
    customer_phone = fields.Char(string="Customer Phone")
    customer_mobile = fields.Char(string="Customer Mobile")
    customer_website = fields.Char(string="Customer Website")



    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMoveInherited, self)._onchange_partner_id()
        self.update({
            'region_id': self.partner_id.region_id.id,
            'segment_id': self.partner_id.segment_id.id,
            'service_type_id': self.partner_id.service_type_id.id,
            'customer_type': self.partner_id.customer_type
        })
        return res

    @api.model
    def create(self, values):
        if not values.get('region_id') and values.get('partner_id'):
            partner = self.env['res.partner'].search([('id', '=', values.get('partner_id'))])
            values.update({
                'region_id': partner.region_id.id,
                'segment_id': partner.segment_id.id,
                'service_type_id': partner.service_type_id.id,

            })
        res = super(AccountMoveInherited, self).create(values)

        for item in res.line_ids:
            if item.move_id and item.move_id.region_id:
                item.region_id = item.move_id.region_id.id or False
        return res

    def write(self, vals):
        if self.state == 'draft':
            if self.partner_id:
                vals.update({
                    'customer_type': self.partner_id.customer_type,
                    'customer_street': self.partner_id.street,
                    'customer_street2': self.partner_id.street2,
                    'customer_city': self.partner_id.city,
                    'customer_state_id': self.partner_id.state_id.id,
                    'customer_country_id': self.partner_id.country_id.id,
                    'customer_zip': self.partner_id.zip,
                    'customer_email': self.partner_id.email,
                    'customer_phone': self.partner_id.phone,
                    'customer_mobile': self.partner_id.mobile,
                    'customer_website': self.partner_id.website,
                    'l10n_in_gstin': self.partner_id.vat,

                })
                if not self.sales_person_id:
                    vals.update({
                        'sales_person_id': self.partner_id.order_sales_person.id
                    })

            if self.journal_gstin_partner_id:
                vals.update({
                    'company_name': self.journal_gstin_partner_id.name,
                    'company_street': self.journal_gstin_partner_id.street,
                    'company_street2': self.journal_gstin_partner_id.street2,
                    'company_city': self.journal_gstin_partner_id.city,
                    'company_state_id': self.journal_gstin_partner_id.state_id.id,
                    'company_zip': self.journal_gstin_partner_id.zip,
                    'company_country_id': self.journal_gstin_partner_id.country_id.id,
                    'company_gst_no': self.journal_gstin_partner_id.vat
                })

        res = super(AccountMoveInherited, self).write(vals)
        return res


class AccountMoveLineInherit(models.Model):
    """ The model account_move_line is inherited to make modifications """
    _inherit = 'account.move.line'

    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')
    region_id = fields.Many2one(comodel_name='sales.region', string="Region", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")


class AccountPaymentInherit(models.Model):
    """ The model account_payment is inherited to make modifications """
    _inherit = 'account.payment'

    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')


class AccountPaymentRegisterInherit(models.TransientModel):
    """ The model account_payment is inherited to make modifications """
    _inherit = 'account.payment.register'

    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')


class AccountInvoiceReport(models.Model):
    """ The model account_move is inherited to make modifications """
    _inherit = 'account.invoice.report'

    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type')
