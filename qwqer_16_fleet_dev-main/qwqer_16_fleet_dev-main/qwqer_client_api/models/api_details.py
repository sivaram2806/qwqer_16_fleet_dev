import json
import re
from datetime import datetime
from operator import index

import requests

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import SUPERUSER_ID
from odoo.api import model, _logger
import ast

class CreateApiDetails(models.Model):
    _name = 'create.api.details'

    api_name = fields.Char(string='Api')
    data = fields.Text(string="Data")
    status = fields.Selection(selection=[('success','Success'),('failed','Failed')],string='Status')
    response = fields.Text()
    onboard_id = fields.Many2one(comodel_name='customer.onboard')
    change_req_id = fields.Many2one(comodel_name='customer.master.change.request')
    customer_sync_id = fields.Many2one(comodel_name='partner.sync.api')
    partner_id = fields.Many2one(comodel_name='res.partner')



    def resync_update_customer(self):
        vals= ast.literal_eval(self.data)
        if vals:
            api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
            if api_credentials:
                headers = {
                    'SecretKey': api_credentials.authorization,
                    'content-type': "application/json",
                }
                url = api_credentials.server_url + '/api/update/customers'
                try:
                    response = requests.request("POST", url, json=vals,
                                                headers=headers)
                    response_data = response.json()['result']
                    data = json.loads(response_data)

                    if data['status_code'] == 200:
                        details = {
                            "api_name": "Customer Update Api",
                            "data": self.data,
                            "status": "success",
                            "response": data,
                        }

                    else:
                        details = {
                            "api_name": "Customer Update Api",
                            "data": self.data,
                            "status": "failed",
                            "response": data,
                        }
                    self.write(details)

                except Exception as e:
                    _logger.info("Error :exception happened : %s", e)
                    details = {
                        "api_name": "Customer Update Api",
                        "data": vals,
                        "status": "failed",
                        "response": e
                    }
                    self.write(details)
                return True
        else:
            details = {
                "api_name": "Customer Update Api",
                "status": "failed",
                "response": "data not generated",
                "change_req_id": self.id
            }
            self.create(details)
        return True

    def resync_create_customer(self):
        vals= ast.literal_eval(self.data)
        api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
        if api_credentials:

            headers = {
                'SecretKey': api_credentials.authorization,
                'content-type': "application/json",
            }
            url = api_credentials.server_url + '/api/create/customers'
            try:
                response = requests.request("POST", url, json=vals,
                                            headers=headers)
                response_data = response.json()['result']
                data = json.loads(response_data)

                if data['status_code'] == 200:
                    details = {
                        "api_name": "Customer Creation Api",
                        "data": self.data,
                        "status": "success",
                        "response": data,
                    }
                    if self.onboard_id:
                        customer_id = self.onboard_id.partner_id
                        self.onboard_id.v13_partner_id = data['customer_id']
                        if customer_id:
                            customer_id.customer_ref_key = data['customer_id']
                else:
                    details = {
                        "api_name": "Customer Creation Api",
                        "data": self.data,
                        "status": "failed",
                        "response": data,
                    }
                self.write(details)

            except Exception as e:
                _logger.info("Error :exception happened : %s", e)
                details = {
                    "api_name": "Customer Creation Api",
                    "data": self.data,
                    "status": "failed",
                    "response": e
                }
                self.write(details)
            return True


    def resync_customer(self):
        data = self.data
        if data:
            data_dict = ast.literal_eval(data)
            if data_dict.get('phone'):
                phone = data_dict.get('phone')
                existing_partner = self.env['res.partner'].search([('phone','=',phone)])
                if not existing_partner:
                    try:
                        partner = self.env['res.partner'].create(data_dict)
                        if partner:
                            self.write({
                                'api_name': 'Customer Sync Api',
                                'status': 'success',
                                'data': data_dict,
                                'response': "Customer Created",
                                'partner_id': partner.id,

                            })
                    except Exception as e:
                        _logger.info("Error :exception happened : %s", e)
                        self.write({
                            'api_name': 'Customer Sync Api',
                            'status': 'failed',
                            'data': data_dict,
                            'response': e,
                        })
                else:
                    self.write({
                        'api_name': 'Customer Sync Api',
                        'status': 'failed',
                        'data': data_dict,
                        'response': "Already a customer created with this {cus_phone} phone number : customer name is {customer}".format(
                            cus_phone=phone, customer=existing_partner),
                    })

            else:
                self.write({
                    'api_name': 'Customer Sync Api',
                    'status': 'failed',
                    'data': data_dict,
                    'response': 'Phone Number Not Found',
                })

        if self.customer_sync_id.api_details_ids:
            failed_rec = self.customer_sync_id.api_details_ids.filtered(lambda s:s.status=='failed')
            if failed_rec:
                self.customer_sync_id.state = 'incomplete'
            else:
                self.customer_sync_id.state = 'completed'

