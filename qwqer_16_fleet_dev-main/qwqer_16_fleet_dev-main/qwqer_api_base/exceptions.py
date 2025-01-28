# custom_exceptions.py
import json

from werkzeug import Response

from odoo import fields
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import html_escape


class APIError(UserError):
    """
    Custom exception for API errors, allowing for structured JSON responses.
    """
    def __init__(self, message, status, status_code=400, error_code=None, additional_params=None):
        """
        Initialize the APIError with a custom message, HTTP status code, and error code.

        Parameters:
        - message: The error message for the API response.
        - status_code: The HTTP status code to return (default: 400).
        - error_code: Optional custom error code to provide additional context.
        """
        super().__init__(message)
        self.message = message
        self.status = status
        self.status_code = status_code
        self.error_code = error_code
        self.additional_params = additional_params or {}

    def to_response(self, api_raw_log=None, name="Not Given"):
        """
        Converts the exception details to a JSON-friendly response.

        Returns:
        - dict: Contains the error message, status code, and optional error code.
        """
        response = {
            'status': self.status,
            'status_code': self.status_code,
            'error': self.message,
            **self.additional_params
            
        }
        if api_raw_log:
            try:
                request.env.cr.rollback()
            except:
                pass
            api_raw_log.update({"response": json.dumps(response),
                        'response_date': fields.Datetime.now(),
                        'name': name,
                        'key': "",
                        'status': response['status']})
        return json.dumps(response)
