import json

from . import models
from . import exceptions

import logging

logger = logging.getLogger(__name__)

from functools import wraps
from odoo.http import request, Response


def check_auth_validity(func):
    """Decorator to check API key authentication."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if request.env.user == request.env['res.users']:
                raise exceptions.APIError("Access Denied: Missing or Invalid API Key", "REJECTED",
                                          status_code=403)
            api_raw_log = request.env['api.request.response.raw.log'].sudo().create({
                'data': request.params and str(request.params),
                'request_url': request.httprequest.full_path,
                'remote_addr': request.httprequest.remote_addr
            })
            request.env.cr.commit()
            return func(*args, api_raw_log=api_raw_log, **kwargs)
        except exceptions.APIError as e:
            return json.dumps(e.to_response())
    return wrapper


