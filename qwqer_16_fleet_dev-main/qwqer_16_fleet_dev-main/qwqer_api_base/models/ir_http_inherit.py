import logging

from odoo import models
logger = logging.getLogger(__name__)

from odoo.http import request
class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_qwy_api_key(cls):
        """Custom API key authentication."""
        api_key = request.httprequest.headers.get("Authorization") or request.httprequest.headers.get("secretKey")
        if not api_key:
            logger.error("Authorization key is missing")
            return None

        api_key = api_key.replace('Bearer ', '')
        user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=api_key)

        if not user_id:
            logger.error("Invalid Authorization key")
            return None

        # Update request environment with authenticated user
        request.update_env(user_id)
