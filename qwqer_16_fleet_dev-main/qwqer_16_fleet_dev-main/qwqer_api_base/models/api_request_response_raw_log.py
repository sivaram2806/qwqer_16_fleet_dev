import ast
import json
import logging
from datetime import timedelta

import requests

logger = logging.getLogger(__name__)
from odoo import models, fields

class ApiRequestResponseRawLog(models.Model):
    _name = "api.request.response.raw.log"
    _description = "API Request Response Raw Log"
    _rec_name = "access_date"
    _order = "id desc"

    name = fields.Char(string="API name")
    access_date = fields.Datetime(string='Access Date',
                                  default=fields.Datetime.now)
    response_date = fields.Datetime(string='Response Date')
    access_user_id = fields.Many2one('res.users', string='Accessed By')
    access_user_name = fields.Char(string='Username')
    request_url = fields.Char(string='URL')
    remote_addr = fields.Char(string='Remote Address')
    data = fields.Text(string='Data Received')
    response = fields.Text(string='Response')
    key = fields.Char(string="Key")
    status = fields.Char(string="Status")

    def clear_api_log_cron(self):
        """Cron for clearing api log created before 90 days"""
        before_ninty_days = (fields.Datetime.now(self) + timedelta(days=-90)).strftime("%Y-%m-%d 18:30:00")
        logger.info("Clearing API row logs created before --------------------------------- ", before_ninty_days)
        self.env.cr.execute("""
            delete from api_request_response_raw_log where access_date <= %(access_date)s;
        """, {'access_date': before_ninty_days})

    def sync_data(self, base_url="http://localhost:8016/", api_key='56f6e5a7128781f93468b2761bf0bfc9d4dc49b7'):
        api_key = api_key or "your_api_key_here"  # Replace with environment variable or secure storage

        headers = {
            "Content-Type": "application/json",
            "Authorization": api_key
        }

        for rec in self:
            try:
                # Parse the JSON data
                json_object  = ast.literal_eval(rec.data)
                logger.info(f"Parsed JSON data: {json_object}")

                # Determine the URL
                url = rec.request_url.replace('?', "")
                if url == "internal/service/request" and (
                    "merchant_total_amount" in json_object or "products" in json_object
                ):
                    url = "qshop/service/request"

                # Make the POST request
                response = requests.post(base_url + url, headers=headers, json={"params": json_object})

                if response.status_code in [200, 201]:  # Check for success
                    rec.unlink()
                    logger.info(f"Sync completed for record ID {rec.id}")
                else:
                    logger.error(
                        f"Failed to sync record ID {rec.id}. "
                        f"Status Code: {response.status_code}, Response: {response.text}"
                    )
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed for record ID {rec.id}: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP request failed for record ID {rec.id}: {e}")
            except Exception as e:
                logger.err

    def update_failed_records_cron(self, domain, base_url="http://localhost:8016/", api_key='56f6e5a7128781f93468b2761bf0bfc9d4dc49b7', limit=200):
        records = self.search(domain, limit=limit or 100, order='access_date ASC')
        records.sync_data(base_url, api_key)