import json
import re
from datetime import datetime
from operator import index

import requests

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import SUPERUSER_ID
from odoo.api import model, _logger


class ChangeRequest(models.Model):
    _inherit = "customer.master.change.request"

    api_details_ids = fields.One2many(comodel_name='create.api.details', inverse_name='change_req_id')
    sync_status = fields.Selection(selection=[('failed','Failed'),('success','Success')],string='Sync Status')


    def action_finance_approval(self):
        res = super().action_finance_approval()
        if self.comment:
            api_datails = self.env['create.api.details']
            api_credentials = self.env['qwqer.api.credentials'].sudo().search([], limit=1)
            if api_credentials and api_credentials.is_partner_update:
                data = res[0]
                customer_update_data = self.update_customer_data(data)
                if customer_update_data:
                    vals = {"params": customer_update_data}
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
                                "data": vals,
                                "status": "SUCCESS",
                                "response": data,
                                "change_req_id": self.id
                            }
                            self.sudo().update({'sync_status':'success'})

                        else:
                            details = {
                                "api_name": "Customer Update Api",
                                "data": vals,
                                "status": "failed",
                                "response": data,
                                "change_req_id": self.id
                            }
                            self.sudo().update({'sync_status': 'failed'})

                        api_datails.create(details)

                    except Exception as e:
                        _logger.info("Error :exception happened : %s", e)
                        details = {
                            "api_name": "Customer Update Api",
                            "data": vals,
                            "status": "failed",
                            "change_req_id": self.id,
                            "response": e
                        }
                        api_datails.create(details)
                    return True

                else:
                    details = {
                        "api_name": "Customer Update Api",
                        "status": "failed",
                        "response": "data not generated",
                        "change_req_id": self.id
                    }
                    api_datails.create(details)
        else:
            _logger.info("Credentials not added or not enabled the Customer Create")
        return res

    def update_customer_data(self, data):
        segment = {
            'QWQER Fleet - FLeet FTL': 'QWQER Fleet - FTL',
            'QWQER Technologies - Fleet FTL': 'QWQER Fleet - FTL',
            'QWQER Technologies - UrbanHaul':'QWQER Fleet - Urban Haul',
            'QWQER Fleet - Urban Haul':'QWQER Fleet - Urban Haul',
            'QWQER Express - Large B2B': 'QWQER Express - Large B2B',
            'QWQER Express - Platform': 'QWQER Express - Platform',
            'QWQER Express - Rental': 'QWQER Express - Rental',
            'QWQER Express - SME': 'QWQER Express - SME',
            'QWQER Express - E-Comm': 'QWQER Express - E-Comm',
        }
        if self.phn_number:
            data['phone'] = self.phn_number
        if data.get('state_id'):
            data['state_id'] = data['state_id'].l10n_in_tin
        if data.get('country_id'):
            data['country_id'] = data['country_id'].code
        if data.get('invoice_frequency_id'):
            data['invoice_frequency_id'] = data['invoice_frequency_id'].name
        if data.get('source_lead_type_id'):
            data['source_lead_type_id'] = data['source_lead_type_id'].name
        if data.get('industry_id'):
            data['industry_id'] = data['industry_id'].name
        if data.get('customer_type'):
            customer_type = data['customer_type']
            if customer_type == 'b2c':
                data['customer_type'] = 'retail'
            else:
                data['customer_type'] = 'b2b'
        if data.get('potential_orders_id'):
            data['potential_orders_id'] = data['potential_orders_id'].name
        if data.get('delivery_type_id'):
            data['delivery_type_id'] = data['delivery_type_id'].name
        if data.get('item_category_id'):
            data['item_category_id'] = data['item_category_id'].code
        if data.get('order_sales_person'):
            data['order_sales_person'] = data['order_sales_person'].work_email
        if data.get('segment_id'):
            segment_name = data.get('segment_id').name
            data['segment_id'] = segment.get(segment_name)
        if data.get('product_line_id'):
            data['product_line_id'] = data['product_line_id'].name
        if data.get('source_type_id'):
            data['source_type_id'] = data['source_type_id'].name
        if data.get('fleet_hsn_id'):
            data['fleet_hsn_id'] = data['fleet_hsn_id'].name
        if data.get('credit_period_id'):
            data['credit_period_id'] = False
        if data.get('followup_status_id'):
            data['followup_status_id'] = data['followup_status_id'].name
        if data.get('settlement_time_id'):
            data['settlement_time_id'] = data['settlement_time_id'].name
        if data.get('payment_mode_ids'):
            data['payment_mode_ids'] = [mode.code for mode in self.payment_mode_ids]
        if self.is_price_plan:
            data["pricing_model"] = self.pricing_model
            update_list = []
            if self.pricing_model == 'KM':
                for km_line in self.new_km_pricing_plan_ids:
                    update_list.append({
                        'from_weight': km_line.minimum_weight,
                        'to_weight': km_line.maximum_weight,
                        'min_distance': km_line.min_distance,
                        'min_cost': km_line.min_cost,
                        'per_km_charge': km_line.per_km_charge,
                        'km_plan_id': km_line.id,
                        'is_original_record': True
                    })
                data['pricing_plan'] = update_list
            if self.pricing_model == 'flat':
                for flat_line in self.new_flat_pricing_plan_ids:
                    update_list.append({
                        'from_weight': flat_line.minimum_weight,
                        'to_weight': flat_line.maximum_weight,
                        'price': flat_line.price,
                    })
                data['pricing_plan'] = update_list
            if self.pricing_model == 'slab':
                for slab_line in self.new_slab_pricing_plan_ids:
                    update_list.append({
                        'from_distance': slab_line.from_distance,
                        'to_distance': slab_line.to_distance,
                        'from_weight': slab_line.minimum_weight,
                        'to_weight': slab_line.maximum_weight,
                        'price': slab_line.price,
                    })
                data['pricing_plan'] = update_list
        if self.is_stop_charge == True:
            additional_charge_list = []
            for additiona_charge_line in self.new_additional_charges_ids:
                additional_charge_list.append({
                    'charge_type_id': additiona_charge_line.charge_type_id.name,
                    'amount_type': additiona_charge_line.amount_type,
                    'amount': additiona_charge_line.amount,
                })
            data['select_stop_charge_ids'] = additional_charge_list
        return data
