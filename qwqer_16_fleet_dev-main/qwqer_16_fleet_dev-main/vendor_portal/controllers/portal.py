# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class UserLoginController(Home):

    @http.route('/', type='http', auth="none", website=True, sitemap=True)
    def index(self, **kw):
        """override to render the /my path on calling / on website"""
        user_id = request.session.uid
        if request.db and user_id:
            return request.redirect_query('/web')
        else:
            return self.web_login()

    @http.route('/web/login', type='http', auth="none", csrf=False)
    def web_login(self, redirect=None, *args, **kw):
        """override to render custom login screen """
        response = super(UserLoginController, self).web_login(redirect=redirect, *args, **kw)
        # Get the base url from the parameters
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        # Retrieve the active vendor portal URL
        vendor_portal_url = request.env['ir.config_parameter'].sudo().get_param('web_fleet_url')
        # Take the current url from the root
        current_url = request.httprequest.url_root.rstrip('/')
        # checking the condition whether current url is equal to the vendor portal url
        if current_url == vendor_portal_url:
            if request.params['login_success']:
                uid = request.session.authenticate(request.session.db, request.params['login'],
                                                   request.params['password'])
                return request.redirect(self._login_redirect(uid, redirect=redirect))
            return http.request.render('vendor_portal.qwqer_fleet_login_page')
        elif current_url == base_url:
            return response
            return http.request.render('web.login')
        return response



class VendorPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """extend for preparing record count for menu item"""
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        partner = user.partner_id
        company_id = partner.company_id.id
        # remove all other menu for portal user
        if request.env.user._has_group('base.group_portal'):
            values = {}
        if 'trip_count' in counters:
            values['trip_count'] = request.env['batch.trip.uh'].sudo().search_count(
                [('batch_trip_uh_line_ids.vendor_id', 'in', [partner.id]), ('is_vendor_trip', '=', True),
                 ('company_id', '=', company_id)]) or 0
        if 'bulk_upload_count' in counters:
            values['bulk_upload_count'] = request.env['bulk.upload.trip'].sudo().search_count(
                [('create_uid', '=', user.id), ('company_id', '=', company_id)]) or 0
        if 'bill_count' in counters:
            values['bill_count'] = request.env['account.move'].sudo().search_count(
                [('partner_id', '=', partner.id), ('state', 'not in', ('cancel', 'draft')),
                 ('move_type', '=', 'in_invoice'), ('company_id', '=', company_id)]) or 0
        if 'vehicle_count' in counters:
            values['vehicle_count'] = request.env['vehicle.vehicle'].sudo().search_count(
                [('vehicle_pricing_lines.vendor_id', '=', partner.id), ('company_id', '=', company_id)]) or 0
        return values
