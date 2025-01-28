# -*- coding: utf-8 -*-
import requests
from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError
import pytz
from odoo.addons.qwqer_sim_based_tracking.models import TRACKING_CONFIG




class BatchTripFTLInherit(models.Model):
    """
    Model contains records from batch trip, #V13_model name: batch.trip
    """
    _inherit = 'batch.trip.ftl'

    track_ids = fields.One2many(comodel_name='ftl.track.history', inverse_name='ftl_trip_id', copy=False, store=True)
    driver_phone = fields.Char(string='Driver Phone')
    eta_hrs = fields.Float(string='Estimated Time (Hours)', compute='_compute_estimated_time_of_arrival', store=True)

    from_city = fields.Char(store=True)
    from_city_lat = fields.Char(store=True)
    from_city_long = fields.Char(store=True)
    to_city_lat = fields.Char(store=True)
    to_city_long = fields.Char(store=True)
    to_city = fields.Char(store=True)
    track_trip_id = fields.Char(string='Track ID', store=True)
    track_trip_uid = fields.Char(string='Track UID', store=True)
    track_url = fields.Char(string='Track URL', store=True)
    consent_status = fields.Char(string="Consent Status", store=True)
    track_trip_status = fields.Char(string="Track Status", store=True)
    track_invoice_no = fields.Char(string="Track Invoice No", readonly=False, store=True)
    total_distance = fields.Char(string="Total Distance", readonly=False, store=True)
    distance_traveled = fields.Char(string="Distance Traveled", readonly=False, store=True)


    @api.depends('start_date', 'end_date')
    def _compute_estimated_time_of_arrival(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                start_dt = datetime.combine(rec.start_date, datetime.min.time())
                end_dt = datetime.combine(rec.end_date, datetime.min.time())
                duration = end_dt - start_dt
                if duration != 0:
                    rec.eta_hrs = duration.days * 24
                else:
                    rec.eta_hrs = 24
        return True


    @api.model
    def create(self, vals):
        """Inherits create function to generate ftl daily trip sequence"""
        res = super(BatchTripFTLInherit, self).create(vals)
        if res.name:
            res.write({'track_invoice_no': res.name})
        return res

    def action_ftl_trip_complete(self):
        """Function to change state from finance_approved to completed"""
        for rec in self:
            if rec.track_trip_id and rec.track_trip_status == 'RUNNING':
                rec.action_end_trip()
            return super(BatchTripFTLInherit, self).action_ftl_trip_complete()

    # FTL Track Route History

    def track_trip_creation(self, **kwargs):
        """ Method to create trip in traqo (Tracking Service Provider)"""
        if not self.from_city or not self.to_city:
            raise UserError("Please provide both the from city and to city.")
        try:
            source_coordinates = f"{self.from_city_lat},{self.from_city_long}" if self.from_city_lat and self.from_city_long else None
            destination_coordinates = f"{self.to_city_lat},{self.to_city_long}" if self.to_city_lat and self.to_city_long else None
            data = {
                "tel": self.driver_phone if self.driver_phone else None,
                "src": source_coordinates if source_coordinates else None,
                "dest": destination_coordinates if destination_coordinates else None,
                "srcname": self.from_city if self.from_city else None,
                "destname": self.to_city if self.to_city else None,
                "truck_number": self.vehicle_id.vehicle_no if self.vehicle_id else None,
                "invoice": self.track_invoice_no if self.track_invoice_no else None,
                "eta_hrs": int(self.eta_hrs) if self.eta_hrs else None
            }
            track_service = self.company_id.tracking_provider
            service_provider = TRACKING_CONFIG.get(track_service)
            if not service_provider:
                raise UserError("Service Provider Not Available")
            auth_headers = service_provider.track_api_get_headers(self.company_id)
            if not auth_headers:
                raise UserError("Authorization Failed")
            response = service_provider.create_trip(auth_headers, **data)
            if response:
                if response.get('status') == "success":
                    trip_id = response.get('tripId')
                    if trip_id:
                        self.track_trip_uid = trip_id
                        self.track_trip_status = "success"
                else:
                    raise UserError(response.get('status'))
        except requests.exceptions.RequestException as e:
            return {'error': 'An error occurred during the API call.', 'details': str(e)}

    def fetch_trip_tracking_details(self):
        """ Method to fetch the route history """
        track_update_records = self
        if 'from_cron' in self.env.context:
            track_update_records = self.env['batch.trip.ftl'].search([('state', '=','finance_approved'),('track_trip_uid', '!=', False),
                                                                      ('track_trip_status', '!=', 'STOPPED')])
        for rec in track_update_records:
            track_service = rec.company_id.tracking_provider
            service_provider = TRACKING_CONFIG.get(track_service)
            if service_provider:
                headers = service_provider.track_api_get_headers(rec.company_id)
                if not (headers and rec.track_trip_uid):
                    continue
                try:
                    trip_body = {
                        "id": rec.track_trip_uid
                    }
                    track_service = rec.company_id.tracking_provider
                    service_provider = TRACKING_CONFIG.get(track_service)
                    fetch_trip_response = service_provider.fetch_trip_details(headers, **trip_body)
                    if not fetch_trip_response:
                        continue
                    trip_data = fetch_trip_response.get('trips', {}).get('0', {})
                    trip_id = trip_data.get('trip_id')
                    if not trip_id:
                        continue
                    track_url = trip_data.get('share_url')
                    track_trip_status = trip_data.get('trip_status').upper()
                    location_details = []
                    rec.track_trip_id = trip_id
                    rec.track_url = track_url
                    rec.track_trip_status = track_trip_status
                    rec.total_distance = trip_data.get('total_distance')
                    rec.distance_traveled = trip_data.get('distance_travel')
                    # Fetch Route History
                    trip_id = {'id': trip_id}
                    route_history_response = service_provider.get_route_history(headers, **trip_id)
                    if not route_history_response:
                        continue
                    locations = route_history_response.get('locations', {})
                    for index, loc_data in locations.items():
                        time_recorded = loc_data.get('time_recorded')
                        time_recorded = datetime.strptime(time_recorded,
                                                          '%d-%m-%Y %H:%M:%S') if time_recorded else None
                        if time_recorded:
                            local_tz = pytz.timezone('Asia/Kolkata')
                            time_recorded_localized = local_tz.localize(time_recorded)
                            time_recorded = time_recorded_localized.astimezone(pytz.utc).replace(
                                tzinfo=None)
                            location_details.append((0, 0, {
                                'company_id': rec.company_id.id,
                                'location_sequence': index,
                                'ftl_trip_id': rec.id,
                                'latitude': loc_data.get('latitude'),
                                'longitude': loc_data.get('longitude'),
                                'location': loc_data.get('place'),
                                'time_recorded': str(time_recorded)
                            }))
                    if location_details:
                        rec.track_ids.sudo().unlink()
                        rec.track_ids = location_details
                except requests.exceptions.RequestException as e:
                    return {'error': 'An error occurred during the API call.', 'details': str(e)}

    def action_end_trip(self):
        """ Method to close the trip"""
        if not self.track_trip_uid:
            raise UserError("Tracking has not been initiated yet")

        track_service = self.company_id.tracking_provider
        service_provider = TRACKING_CONFIG.get(track_service)

        if not service_provider:
            raise UserError("Service Provider Not Found")

        headers = service_provider.track_api_get_headers(self.company_id)
        if not headers:
            raise UserError("Authorization Failed")

        trip_uid_data = {"id": self.track_trip_uid}
        end_trip_response = service_provider.action_end_trip(headers, **trip_uid_data)
        if end_trip_response.get('status') == 'success':
            self.track_trip_status = "STOPPED"
        else:
            raise UserError(end_trip_response.get('status'))

    def check_consent_status(self):
        """ Method to Check the consent status by using the refresh button in form view """
        track_service = self.company_id.tracking_provider
        service_provider = TRACKING_CONFIG.get(track_service)
        if not service_provider:
            raise UserError("Service Provider Not Found")
        headers = service_provider.track_api_get_headers(self.company_id)
        if not headers:
            raise UserError("Authorization Failed")
        if not self.driver_phone:
            raise UserError("Mobile is not registered for tracking")
        consent_body = {"tel": self.driver_phone}
        consent_response_data = service_provider.check_consent_status(headers, **consent_body)
        if not consent_response_data:
            raise UserError("Please register first, then check consent status.")
        if not self.track_trip_uid:
            raise UserError("Please create the trip first before checking the consent status for tracking.")
        # Update consent status
        new_consent_status = consent_response_data.get('consent')
        if self.consent_status != new_consent_status:
            self.consent_status = str(new_consent_status)

    def action_view_tracking_details(self):
        """ FTL Track History """
        # for rec in self:
        return {
            'name': "Track History",
            'res_model': 'ftl.track.history',
            'view_mode': 'tree',
            'context': {'create': False, 'edit': False},
            'domain': ['|', ('ftl_trip_id', '=', self.id), ('ftl_trip_id', '=', False)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }
