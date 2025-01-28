
from abc import ABC, abstractmethod

class BaseTrackingProvider(ABC):

    def __init__(self, **kwargs):
        self.user_name = kwargs.get("user_name")
        self.user_pass = kwargs.get("user_password")
        self.base_url = "https://dashboard.traqo.in"
        self.create_trip_end_point = "/api/v3/trip/create/"
        self.check_consent = "/api/v3/check_consent/"
        self.fetch_trip = "/api/v4/trip/fetch/"
        self.route_history = "/api/v4/trip/fetch_route_history/"
        self.end_trip = "/api/v3/trip/end/"

    @abstractmethod
    def track_api_get_headers(self, data):
        raise NotImplemented()

    @abstractmethod
    def create_trip(self, trip_data, *kwarg):
        raise NotImplemented()

    @abstractmethod
    def fetch_trip_details(self, trip_id, *kwarg):
        raise NotImplemented()

    @abstractmethod
    def check_consent_status(self, phone_no, *kwarg):
        raise NotImplemented()

    @abstractmethod
    def get_route_history(self, trip_id, *kwarg):
        raise NotImplemented()

    @abstractmethod
    def action_end_trip(self, trip_id, **kwarg):
        raise NotImplemented
