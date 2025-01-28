import base64
import json

import requests
from odoo.addons.qwqer_sim_based_tracking.models.tracking_abstarct import BaseTrackingProvider


class TraqoServiceProvider(BaseTrackingProvider):

    def __init__(self, **kwargs):
        super(TraqoServiceProvider, self).__init__(**kwargs)
        self.base_url = "https://dashboard.traqo.in"
        self.create_trip_end_point = "/api/v3/trip/create/"
        self.check_consent = "/api/v3/check_consent/"
        self.fetch_trip = "/api/v4/trip/fetch/"
        self.route_history = "/api/v4/trip/fetch_route_history/"
        self.end_trip = "/api/v3/trip/end/"

    def track_api_get_headers(self, comp_id):
        """ To fetch the headers for Authorization  """
        track_username = comp_id.track_username
        track_password = comp_id.track_password
        if track_username and track_password:
            auth_string = f"{track_username}:{track_password}"
            auth_bytes = auth_string.encode('utf-8')
            base64_auth = base64.b64encode(auth_bytes).decode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Basic {base64_auth}'
            }
            return headers


    def create_trip(self,headers, **kwargs):
        API_ENDPOINT = f"{self.base_url}{self.create_trip_end_point}"
        try:
            data = {
                "tel": str(kwargs.get('tel')) if kwargs.get('tel') else None,
                "src": kwargs.get('src') if kwargs.get('src') else None,
                "dest": kwargs.get('dest') if kwargs.get('dest') else None,
                "srcname": kwargs.get('srcname') if kwargs.get('srcname') else None,
                "destname": kwargs.get('destname') if kwargs.get('destname') else None,
                "truck_number": kwargs.get('truck_number') if kwargs.get('truck_number') else None,
                "invoice": kwargs.get('invoice') if kwargs.get('invoice') else None,
                "eta_hrs": int(kwargs.get('eta_hrs')) if kwargs.get('eta_hrs') else None
            }
            trip_data = json.dumps(data)
            create_trip_data = requests.post(url=API_ENDPOINT, headers=headers , data=trip_data)
            response_data = create_trip_data.json()
            if create_trip_data.status_code == 200:
                return response_data
            return None
        except requests.exceptions.RequestException as e:
            return {'error': 'An error occurred during the API call.'}

    # raise ValidationError("Before starting the trip, add the 'from' city and 'to' city")

    def check_consent_status(self, headers, **kwargs):
        CONSENT_API_ENDPOINT = f"{self.base_url}{self.check_consent}"
        try:
            consent_body = {
                "tel": kwargs.get('tel') if kwargs.get('tel') else None,
            }
            consent_body_data = json.dumps(consent_body)
            consent_response = requests.get(url=CONSENT_API_ENDPOINT, headers=headers, data=consent_body_data)
            response_data = consent_response.json()
            if consent_response.status_code == 200:
                return response_data
            return None
        except requests.exceptions.RequestException as e:
            return {'error': 'An error occurred during the API call.'}

    def fetch_trip_details(self,  headers, **kwargs):
        API_ENDPOINT = f"{self.base_url}{self.fetch_trip}"
        try:
            trip_body = {
                "id": kwargs.get('id') if kwargs.get('id') else None,
            }
            trip_data = json.dumps(trip_body)
            fetch_trip_data = requests.post(url=API_ENDPOINT, headers=headers, data=trip_data)
            response_data = fetch_trip_data.json()
            if fetch_trip_data.status_code == 200:
                return response_data
            return None
        except requests.exceptions.RequestException as e:
            return {'error': 'An error occurred during the API call.'}

    def get_route_history(self, headers, **kwargs):
        API_ENDPOINT = f"{self.base_url}{self.route_history}"
        try:
            trip_body = {
                "id": kwargs.get('id') if kwargs.get('id') else None,
            }
            trip_data = json.dumps(trip_body)
            route_history = requests.post(url=API_ENDPOINT, headers=headers, data=trip_data)
            response_data = route_history.json()
            if route_history.status_code == 200:
                return response_data
            return None
        except requests.exceptions.RequestException as e:
            return {'error': 'An error occurred during the API call.'}

    def action_end_trip(self, headers, **kwargs):
        API_ENDPOINT = f"{self.base_url}{self.end_trip}"
        try:
            trip_uid_data = {
                "id":  kwargs.get('id') if kwargs.get('id') else None,
            }
            trip_data = json.dumps(trip_uid_data)
            end_trip = requests.post(url=API_ENDPOINT, headers=headers, data=trip_data)
            response_data = end_trip.json()
            if end_trip.status_code == 200:
                return response_data
            return None
        except requests.exceptions.RequestException as e:
            return {'error': 'An error occurred during the API call.'}