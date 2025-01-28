# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from datetime import datetime
import base64
from odoo.exceptions import ValidationError, UserError
from dateutil import parser

class PortalDailyTrip(CustomerPortal):

    def convert_time_string_to_float_time(self, time_string):
        """convert time string to float_time value for the backed float_time widget field
            @params time_string:value form portal start_time and end_time
        """
        if time_string:
            hours, minutes = map(int, time_string.split('.') if "." in time_string else [time_string, "00"])
            return hours + minutes / 60.0
        else:
            return False

    def float_time_to_time_str(self, float_value):
        """convert float_time value from the backed float_time widget field to string time for display in portal
           @params time_string:start_time and end_time value form backed daily_batch_trip_uh object
        """
        if float_value:
            hours = int(float_value)
            minutes = int(round((float_value - hours) * 60, 2))
            return f"{hours:02d}.{minutes:02d}"
        else:
            return False

    def _validate_trip_form(self, form_data):
        """"trip form validation"""
        fields = {'vendor_id': 'vendor', 'region': 'Region', 'trip_date': 'Trip Date', 'vehicle_number': 'Vehicle',
                  'start_time': 'Start Time', 'end_time': 'End Date', 'start_odo': 'Start Odo', 'end_odo': 'End Odo'}
        for field, name in fields.items():
            if not form_data.get(field):
                raise ValidationError(f'{name} is required.')
        if float(form_data.get('start_time')) >= float(form_data.get('end_time')):
            raise ValidationError('End time must be greater than Start time.')
        if float(form_data.get('start_odo')) >= float(form_data.get('end_odo')):
            raise ValidationError('End Odo must be greater than Start Odo.')

    @http.route('/trip', type='http', methods=['GET', 'POST'], auth="user", website=True, sitemap=True)
    def vp_trip(self, **kwargs):
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        vehicles = request.env['vehicle.pricing.line'].sudo().search(
            [('vendor_id', '=', partner.id), ('company_id', '=', company_id)])
        error = None
        default_kwargs = kwargs.copy()
        if request.httprequest.method == 'POST':
            try:
                with request.env.cr.savepoint():
                    self._validate_trip_form(kwargs)
                    kwargs.update({
                        'start_time': self.convert_time_string_to_float_time(kwargs.get('start_time')),
                        'end_time': self.convert_time_string_to_float_time(kwargs.get('end_time')),
                        'trip_date': datetime.strptime(kwargs.get('trip_date'), '%Y-%m-%d').date()
                    })

                    vehicle_pricing_line = vehicles.sudo().browse(int(kwargs.get('vehicle_number')))
                    vals = {
                        'vehicle_pricing_line_id': vehicle_pricing_line.id or False,
                        'vehicle_pricing_id': vehicle_pricing_line.vehicle_pricing_id.id or False,
                        'driver_name': vehicle_pricing_line.driver_name or False,
                        'vendor_id': int(kwargs.get('vendor_id')) or False,
                        'start_time': kwargs.get('start_time') or False,
                        'end_time': kwargs.get('end_time') or False,
                        'start_km': kwargs.get('start_odo') or False,
                        'end_km': kwargs.get('end_odo') or False,
                        'region_id': kwargs.get('region') or False,
                        'company_id': company_id or False
                    }
                    daily_trip = request.env['batch.trip.uh'].sudo().create({
                        'trip_date': kwargs.get('trip_date'),
                        'region_id': kwargs.get('region') or None,
                        'customer_id': vehicle_pricing_line.customer_id.id or None,
                        'frequency': vehicle_pricing_line.customer_id.frequency or None,
                        'sales_person_id': vehicle_pricing_line.customer_id.order_sales_person.id or None,
                        'is_vendor_trip': True,
                        'comments': kwargs.get('comment') or False,
                        'company_id': company_id or False,
                        'batch_trip_uh_line_ids': [(0, 0, vals)] or False,
                    })

                    if 'attachment_files' in request.httprequest.files:
                        attachments = request.httprequest.files.getlist('attachment_files')
                        for file_storage in attachments:
                            if file_storage.filename:
                                attachment_data = file_storage.read()
                                attachment_vals = {
                                    'name': file_storage.filename,
                                    'datas': base64.b64encode(attachment_data).decode('utf-8'),
                                    'res_model': 'batch.trip.uh',
                                    'res_id': daily_trip.id,
                                }
                                attachment = request.env['ir.attachment'].sudo().create(attachment_vals)

                                if attachment:
                                    daily_trip.write({'attachment_ids': [(4, attachment.id)]})
                                else:
                                    daily_trip.write({'attachment_ids': False})

                    if daily_trip:
                        return request.redirect(f'/my/trip/{daily_trip.id}')

            except ValidationError as e:
                error = str(e)
            except UserError as e:
                error = str(e)
            except Exception as e:
                error = 'somthing went wrong'
        if request.httprequest.method == 'GET':
            if not default_kwargs.get("trip_date"):
                default_kwargs["trip_date"] = datetime.today().strftime("%Y-%m-%d")
        regions = request.env['sales.region'].sudo().search([('company_id', '=', company_id)])
        vals = {
            'regions': regions,
            'vehicles': vehicles,
            'page_name': 'trip_sheet',
            'error': error,
            'form_data': default_kwargs
        }

        return request.render('vendor_portal.create_daily_trip_form', vals)

    @http.route(['/my/trips', '/my/trips/page/<int:page>'], type='http', auth="user", website=True, sitemap=True)
    def vp_daily_trips_list_view(self, page=1, search="", search_in=""):
        """function to get trips list and render the list view template"""
        trip_date = None
        status = None
        if search_in == 'Trip Date' and search:
            try:
                date_obj = datetime.strptime(search, "%d/%m/%Y")
                trip_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                trip_date = None
            if not trip_date:
                date_obj = parser.parse(search, fuzzy=True)
                trip_date = date_obj.strftime("%Y-%m-%d")
        if search_in == 'Status':
            if search.lower() == 'draft':
                status = 'new'
            else:
                status = search

        searchbar_inputs = {
            # 'All': {'domain': [("name", "ilike", search)], 'input': 'All', 'label': _('Search in All')},
            'Vehicle Request No': {'domain': [("name", "ilike", search)], 'input': 'Vehicle Request No', 'label': _('Vehicle Request No')},
            'Trip Date': {'domain': [("trip_date", "=", trip_date)], 'input': 'Trip Date', 'label': _('Trip Date')},
            'Status': {'domain': [("state", "ilike", status)], 'input': 'Status', 'label': _('Status')},
            'Region': {'domain': [("region_id.name", "ilike", search)], 'input': 'Region', 'label': _('Region')},
        }
        search_domain = searchbar_inputs[search_in]["domain"] if search_in else []
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        domain = [('is_vendor_trip', '=', True), (
            'batch_trip_uh_line_ids.vendor_id', '=', partner.id), ('company_id', '=', company_id)]
        domain += search_domain
        total_trip_count = request.env['batch.trip.uh'].sudo().search_count(domain)
        page_details = pager(url='/my/trips',
                             total=total_trip_count,
                             page=page,
                             step=21)
        trips = request.env['batch.trip.uh'].sudo().search(domain, limit=21, offset=page_details['offset'])
        vals = {'trips': trips, 'page_name': 'daily_trips', 'pager': page_details, 'search': search,
                'searchbar_inputs': searchbar_inputs,
                'search_in': search_in}
        return request.render('vendor_portal.portal_vendor_daily_trip', vals)

    @http.route(['/my/trip/<model("batch.trip.uh"):trip_id>'], type='http', auth="user", website=True, sitemap=True,
                methods=['GET', 'POST'])
    def vp_daily_trips_form_view(self, trip_id, **post):
        """function to render trip detail form view in GET and edit trip details on POST"""
        partner = request.env.user.partner_id
        company_id = partner.company_id.id
        error = None
        if request.httprequest.method == 'POST':
            try:
                with request.env.cr.savepoint():
                    write_values = {}
                    # Convert relevant post values to float
                    post.update({
                        'start_time': self.convert_time_string_to_float_time((post.get('start_time'))),
                        'end_time': self.convert_time_string_to_float_time((post.get('end_time'))),
                        'region': int(post.get('region', 0)),
                        'trip_date': datetime.strptime(post.get('trip_date', ''), '%Y-%m-%d').date() if post.get(
                            'trip_date') else False
                    })
                    self._validate_trip_form(post)
                    vehicle_number = int(post.get('vehicle_number', 0))
                    for trip_line in trip_id.batch_trip_uh_line_ids:
                        line_values = {}
                        if trip_line.vehicle_pricing_line_id.id != vehicle_number:
                            vehicle_pricing_line = request.env['vehicle.pricing.line'].sudo().browse(vehicle_number)
                            if vehicle_pricing_line:
                                write_values = {'frequency': trip_id.customer_id.sudo().frequency,
                                                'sales_person_id': trip_id.customer_id.sudo().order_sales_person.id}
                                line_values = {
                                    'vehicle_pricing_line_id': vehicle_pricing_line.id,
                                    'vehicle_pricing_id': vehicle_pricing_line.vehicle_pricing_id.id,
                                    'driver_name': vehicle_pricing_line.driver_name,
                                }
                                # trip_line.sudo().write(line_values)
                        for line_key, post_key in {'region_id': 'region', 'start_time': 'start_time',
                                                   'end_time': 'end_time',
                                                   'start_km': 'start_odo', 'end_km': 'end_odo'}.items():
                            current_value = getattr(trip_line, line_key, '')
                            if post.get(post_key) and str(current_value) != str(post[post_key]):
                                line_values.update({line_key: post[post_key]})
                        trip_line.sudo().write(line_values)
                        break
                    # Collect field updates
                    for key, post_key in {'region_id': 'region', 'trip_date': 'trip_date',
                                          'comments': 'comment'}.items():
                        if key in ['region_id']:
                            current_value = getattr(trip_id, key).id
                        else:
                            current_value = getattr(trip_id, key, '')
                        if post.get(post_key) and str(current_value) != str(post[post_key]):
                            write_values[key] = post[post_key]
                    # Handle attachments
                    self._handle_attachments(post, trip_id, write_values)

                    if write_values:
                        trip_id.sudo().write(write_values)
                    return request.redirect(f'/my/trip/{trip_id.id}')
            except ValidationError as e:
                error = str(e)
            except UserError as e:
                error = str(e)
            except Exception:
                error = 'somthing went wrong'
        is_bill_paid = False
        vendor_batch_trip_line = trip_id.batch_trip_uh_line_ids.filtered(
            lambda s: s.trip_summary_vendor_id.state != 'paid')
        if not vendor_batch_trip_line:
            is_bill_paid = True
        regions = request.env['sales.region'].sudo().search([('company_id', '=', company_id)])
        vehicles = request.env['vehicle.pricing.line'].sudo().search(
            [('vendor_id', '=', partner.id), ('company_id', '=', company_id)])
        trip_time = {}
        for trip_line in trip_id.batch_trip_uh_line_ids:
            trip_time.update(
                {trip_line.id: {'start_time': self.float_time_to_time_str(trip_line.start_time or False),
                                'end_time': self.float_time_to_time_str(trip_line.end_time or False)}})
        vals = {'trip': trip_id, 'trip_time': trip_time, 'page_name': 'daily_trips', 'vehicles': vehicles,
                'regions': regions,
                'is_bill_paid': is_bill_paid,
                'error': error}
        trip_records = request.env['batch.trip.uh'].sudo().search([('is_vendor_trip', '=', True), (
            'batch_trip_uh_line_ids.vendor_id', '=', partner.id), ('company_id', '=', company_id)])
        trip_ids = trip_records.ids
        current_trip_index = trip_ids.index(trip_id.id)
        if current_trip_index != 0:
            vals['prev_record'] = f'/my/trip/{trip_ids[current_trip_index - 1]}'
        if current_trip_index < len(trip_ids) - 1:
            vals['next_record'] = f'/my/trip/{trip_ids[current_trip_index + 1]}'
        return request.render('vendor_portal.portal_vendor_daily_trip_page', vals)

    def _handle_attachments(self, post, trip_id, write_values):
        """function to handel attachment in trip POST request
        @params post:
        @params trip_id:
        @params write_values:
        """
        # Process file uploads
        if 'attachments' in request.httprequest.files:
            attachments = request.httprequest.files.getlist('attachments')
            for file_storage in attachments:
                if file_storage.filename:
                    attachment_data = file_storage.read()
                    attachment_vals = {
                        'name': file_storage.filename,
                        'datas': base64.b64encode(attachment_data).decode('utf-8'),
                        'res_model': 'batch.trip.uh',
                        'res_id': trip_id.id,
                    }
                    attachment = request.env['ir.attachment'].sudo().create(attachment_vals)
                    if attachment:
                        write_values.setdefault('attachment_ids', []).append((4, attachment.id))

        # Handle removed attachments
        removed_attachments_ids = post.get('removed_attachments', '').split(',')
        for attachment_id in removed_attachments_ids:
            if attachment_id:
                attachment = request.env['ir.attachment'].sudo().browse(int(attachment_id))
                if attachment.exists():
                    attachment.sudo().unlink()

    @http.route(['/my/download_attachment/<int:attachment_id>'], type='http', auth="user", website=True)
    def download_attachment(self, attachment_id):
        """function to handel the downloading of the trip attachment
        @params attachment_id: id of ir.attachment to download
        """
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        if not attachment.exists():
            return request.not_found()

        file_content = base64.b64decode(attachment.datas)
        headers = [
            ('Content-Type', attachment.mimetype),
            ('Content-Disposition', content_disposition(attachment.name))
        ]
        return request.make_response(file_content, headers)

