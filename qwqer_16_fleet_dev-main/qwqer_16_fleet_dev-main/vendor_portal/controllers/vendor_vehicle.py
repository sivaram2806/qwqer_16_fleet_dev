# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class VendorPortalVehicle(CustomerPortal):

    @http.route(['/my/vehicles', '/my/vehicles/page/<int:page>'], type='http', auth="user", website=True, sitemap=True)
    def vp_vehicles_list_view(self, page=1):
        """function to get vehicles record list and render the list view template"""
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        vehicles_count = request.env['vehicle.pricing.line'].sudo().search_count(
            [('vendor_id', '=', partner.id), ('company_id', '=', company_id)])
        page_details = pager(url='/my/vehicles',
                             total=vehicles_count,
                             page=page,
                             step=21)
        vehicles = request.env['vehicle.pricing.line'].sudo().search(
            [('vendor_id', '=', partner.id), ('company_id', '=', company_id)], limit=21,
            offset=page_details['offset'])
        vals = {'vehicles': vehicles, 'page_name': 'vendor_vehicle', 'pager': page_details}
        return request.render('vendor_portal.portal_vendor_vehicles', vals)
