# -*- coding: utf-8 -*-

from odoo import api, fields, models
from lxml import etree


class ResPartner(models.Model):
    """ The model res_partner is inherited to make modifications """
    _inherit = 'res.partner'
    
    
    def get_view(self, view_id=None, view_type='form', **options):
        res = super(ResPartner, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])
        
        if not self.env.user.has_group('qwqer_base.enable_to_create_partner_group'):
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "0")
            if view_type == 'kanban':
                for node in doc.xpath("//kanban"):
                    node.set('create', "0")
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "0")
                    
        if not self.env.user.has_group('qwqer_base.enable_to_edit_partner_group'):           
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('edit', "0")
                    
        res['arch'] = etree.tostring(doc)
        return res
    
    @api.model
    def _get_segment(self):
        company_id = self.company_id.id or self.env.company.id

        if self.env.context.get('default_supplier_rank',0) >= 1:
            return [('is_vendor','=', True),('company_id','=',company_id)]
        elif self.env.context.get('default_customer_rank',0) >= 1:
            return [('is_customer','=', True),('company_id','=',company_id)]
        else:
            return []
    
    @api.model
    def _get_service_type(self):
        company_id = self.company_id.id or self.env.company.id
        if self.env.context.get('default_supplier_rank',0) >= 1:
            return [('is_vendor','=', True),('company_id','=',company_id)]
        elif self.env.context.get('default_customer_rank',0) >= 1:
            return [('is_customer','=', True),('company_id','=',company_id)]
        else:
            return []

    order_sales_person = fields.Many2one('hr.employee', string='Sales Person')
    region_id = fields.Many2one('sales.region', string='Region')
    service_type_id = fields.Many2one(comodel_name='partner.service.type', string='Service Type', domain=_get_service_type)
    segment_id = fields.Many2one(comodel_name='partner.segment', string='Segment', domain=_get_segment)
    customer_type = fields.Selection([('b2c', 'B2C'), ('b2b', 'B2B')], string='Customer Type', default="b2b", index=True)
    document_ids = fields.One2many('partner.document.line', 'partner_id', 'Documents')
    customer_ref_key = fields.Integer(string='Customer Ref Key', index=True)
    state_region_id = fields.Many2one('res.country.state', string="State Region")


    @api.onchange('region_id')
    def onchange_region(self):
        if self.region_id:
            self.state_region_id = self.region_id.state_id.id
