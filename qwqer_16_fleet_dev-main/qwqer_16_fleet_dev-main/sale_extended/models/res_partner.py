# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

from dateutil.relativedelta import relativedelta


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_age = fields.Integer(string="Customer Age")
    age_updated_date = fields.Date(string="Age Updated on", default=fields.Date.context_today)
    is_new_customer = fields.Boolean("Is New Customer",default=False)
    sale_order_age = fields.Integer(string="Sale Order Age")
    joining_date = fields.Datetime(string='Joining Date')


    @api.model
    def create(self, values):
        res = super(ResPartner, self).create(values)
        res.is_new_customer = True
        res.joining_date = res.create_date
        return res



    def new_partner_or_not(self):
        config_rec = self.env['qwqer.age.configurations'].search([], limit=1)
        today = date.today()
        res_date = today - relativedelta(days=config_rec.no_of_days)
        existing_new = self.env['res.partner'].search([('is_new_customer', '=', True)])
        for partner in existing_new:
            partner.is_new_customer = False

        partner_rec = self.env['res.partner'].search([('joining_date', '>=', res_date)])
        print(partner_rec)
        for rec in partner_rec:
            rec.is_new_customer = True

# TODO: Not required when using compute_customer_sale_order_age() funtion
    def customer_age_calculator(self):
        today = fields.Date.today()
        partner_rec = self.env['res.partner'].search([('age_updated_date', '!=', today)], limit=2000)
        for rec in partner_rec:
            if rec.joining_date:
                age = str((today - rec.joining_date.date()).days)
            else:
                age = str((today - rec.create_date.date()).days)
            rec.partner_age = age
            rec.age_updated_date = today

    def set_age_updated_date(self):
        partner_rec = self.env['res.partner'].search([])
        for rec in partner_rec:
            rec.age_updated_date = rec.create_date

    def compute_customer_sale_order_age(self):
        today = fields.Date.today()
        partners = self.env['res.partner'].search([('age_updated_date', '!=', today)], limit=2000)

        if not partners:
            return

        for partner in partners:
            # Calculate partner_age
            if partner.joining_date:
                partner_joining_date = partner.joining_date.date()
                partner.partner_age = (today - partner_joining_date).days
            else:
                partner.partner_age = 0

            # Get the most recent sale order and calculate sale_order_age
            recent_sale_order = self.env['sale.order'].search(
                [('partner_id', '=', partner.id)],
                order='create_date DESC',
                limit=1
            )
            if recent_sale_order:
                sale_order_create_date = recent_sale_order.create_date.date()
                partner.sale_order_age = (today - sale_order_create_date).days
            else:
                partner.sale_order_age = 0

            # Update the age_updated_date
            partner.age_updated_date = today




