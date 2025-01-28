# -*- coding: utf-8 -*-

from odoo import fields, models, _, api


class ResPartner(models.Model):
    """ The model res_partner is inherited to make modifications """
    _inherit = 'res.partner'

    frequency = fields.Selection(selection=[
        ("weekly", "Weekly"),
        ("monthly", "Monthly")],
        default="weekly", copy=False, string="Vehicle Invoice Frequency")
    partner_vehicle_pricing_ids = fields.One2many(comodel_name='partner.vehicle.pricing', inverse_name='partner_id',
                                                  string="Vehicle Pricing", copy=False)
    fleet_hsn_id = fields.Many2one('product.product', string='Fleet HSN')
    vehicle_invoice_tax_ids = fields.Many2many('account.tax', 'vehicle_invoice_tax', 'partner1_id', 'tax1_id',
                                               string='Fleet Tax')
    company_id = fields.Many2one('res.company', 'Company', index=True,
                                 default=lambda self: self.env.company)
    vehicle_count = fields.Integer(string='Vehicle Count', compute='_compute_vehicle_count')
    supplier_invoice_count = fields.Integer(compute='_compute_supplier_invoice_count', string='# Vendor Bills')
    is_fleet_partner = fields.Boolean(string='Is Fleet Partner', default=False)

    @api.onchange('service_type_id')
    def get_service_type_fleet(self):
        if self.service_type_id and self.service_type_id.is_fleet_service:
            self.is_fleet_partner = True
        else:
            self.is_fleet_partner = False

    def _compute_supplier_invoice_count(self):
        """Function to count number of vendor bills associated with this partner"""
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        supplier_invoice_groups = self.env['account.move']._read_group(
            domain=[('partner_id', 'in', all_partners.ids),
                    ('move_type', 'in', ('in_invoice', 'in_refund'))],
            fields=['partner_id'], groupby=['partner_id']
        )
        partners = self.browse()
        for group in supplier_invoice_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.supplier_invoice_count += group['partner_id_count']
                    partners |= partner
                partner = partner.parent_id
        (self - partners).supplier_invoice_count = 0

    def _compute_vehicle_count(self):
        """Function to count number of vehicles associated with this partner"""
        for rec in self:
            rec.vehicle_count = 0
            if rec.customer_rank > 0:
                rec.vehicle_count = self.env['vehicle.pricing.line'].search_count([('customer_id', '=', rec.id)])
            else:
                rec.vehicle_count = self.env['vehicle.pricing.line'].search_count([('vendor_id', '=', rec.id)])

    def action_view_vehicles(self):
        """function to redirect to vehicle.price.line"""
        for rec in self:
            return {
                'name': _('Vehicles'),
                'res_model': 'vehicle.pricing.line',
                'view_mode': 'list,form',
                'context': {'create': False, 'edit': False},
                'domain': ['|', ('customer_id', '=', rec.id), ('vendor_id', '=', rec.id)],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }
