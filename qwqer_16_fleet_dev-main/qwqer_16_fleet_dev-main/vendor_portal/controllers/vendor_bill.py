# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class VendorPortalBill(CustomerPortal):

    @http.route(['/my/bills', '/my/bills/page/<int:page>'], type='http', auth="user", website=True, sitemap=True)
    def vp_bills_list_view(self, page=1):
        """function to get bill record list and render the list view template"""
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        bills_count = request.env['account.move'].sudo().search_count(
            [('partner_id', '=', partner.id), ('state', 'not in', ('cancel', 'draft')),
             ('move_type', '=', 'in_invoice'), ('company_id', '=', company_id)])
        page_details = pager(url='/my/bills',
                             total=bills_count,
                             page=page,
                             step=21)
        bills = request.env['account.move'].sudo().search(
            [('partner_id', '=', partner.id), ('state', 'not in', ('cancel', 'draft')),
             ('move_type', '=', 'in_invoice'), ('company_id', '=', company_id)], limit=21,
            offset=page_details['offset'])
        return request.render('vendor_portal.portal_vendor_bill_page',
                              {'bills': bills, 'pager': page_details, "page_name": 'bill'})

    def _invoice_get_page_view_values(self, invoice, access_token, **kwargs):
        """extend the function to change the breadcrumbs"""
        res = super(VendorPortalBill, self)._invoice_get_page_view_values(invoice, access_token, **kwargs)
        if request.env.user._has_group('base.group_portal'):
            res.update({'page_name': 'bill'})
        return res
