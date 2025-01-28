import json
from datetime import datetime
import logging

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError


class DriverCreationController(http.Controller):

    @http.route(['/internal/drivercreation/request/'], type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def create_driver(self, api_raw_log=None, **kwargs):
        """API to Create/Update driver and related partner"""
        try:
            driver_id = kwargs.get('driver_id', False)
            if not driver_id:
                raise APIError(status="REJECTED", status_code=500,
                               message="Mandatory Parameter Driver ID Missing!")
            params = {k: (False if v is None else v) for k, v in kwargs.items()}
            _logger.info("Driver Creation API : Request Received, Processing ......%s", str(driver_id))
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")
            if params:
                if params.get('document_details'):
                    doc_list = []
                    for i in params.get('document_details'):
                        doc = {k: (False if v is None else v) for k, v in i.items()}
                        doc_list.append(doc)
                    params['document_details'] = doc_list
                response = self.create_or_update_driver(params)

                api_raw_log.update({"response": json.dumps(response),
                                    'response_date': fields.Datetime.now(),
                                    'name': "Driver Creation API",
                                    'key': driver_id and str(driver_id),
                                    'status': response['status']})
                return json.dumps(response)

            else:
                _logger.info("Driver Creation API : No Data Received or Incorrect Data Format!")
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")
        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Driver Creation API")
        except Exception as e:
            _logger.error(f"Driver Creation API : No Data Received or Incorrect Data Format!{str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later")
            response = error.to_response(api_raw_log=api_raw_log, name="Driver Creation API")
            return response

    def create_or_update_driver(self, params):
        """
        Create or update driver details based on provided parameters.
        """
        vals = {}
        driver_ifsc = False
        driver_account = False
        driver_rec = request.env['hr.employee'].sudo().search(
            [('driver_uid', '=', params['driver_id'])], limit=1)

        if not driver_rec:
            vals.update({'driver_uid': params['driver_id']})
        if driver_rec:
            driver_ifsc = driver_rec.ifsc_code
            driver_account = driver_rec.account_no
        # Validate required fields
        required_fields = {
            'name': "Name Missing",
            'mobile_phone': "Mobile Number Missing",
        }
        for field, error_msg in required_fields.items():
            if not params.get(field):
                raise APIError(status="REJECTED", status_code=500,
                               message=error_msg)
            vals[field] = params[field]
        if params.get('region_id'):
            region_id = request.env['sales.region'].search([('region_code', '=', params['region_id']), ('company_id', '=', request.env.company.id)], limit=1)
            if not region_id:
                raise APIError(status="REJECTED", status_code=500, message="Region Missing")
            if region_id and (not driver_rec or driver_rec.region_id != region_id):
                    vals.update({'region_id': region_id.id})
            if region_id:
                work_location =  request.env["hr.work.location"].search([("name", "ilike", region_id.name)],limit=1)
                if work_location:
                    vals.update({'work_location_id': work_location.id})
        else:
            raise APIError(status="REJECTED", status_code=500,  message="Region ID Missing")
        # Optional fields with defaults
        vals['employee_status'] = params.get('employee_status', 'active')
        vals['work_email'] = params.get('work_email', '')
        vals['work_phone'] = params.get('mobile_phone', '')
        vals['mobile_phone'] = params.get('mobile_phone', '')

        # TDS validation
        if params.get('tds_apply') in ('y', 'Y'):
            vals['apply_tds'] = True
            if not params.get('pan_no'):
                raise APIError(status="REJECTED", status_code=500,
                               message="PAN no is required if TDS is applicable")
        elif params.get('tds_apply') in ('n', 'N'):
            vals['apply_tds'] = False

        # Additional fields
        self._process_additional_fields(params, vals)

        if params.get('gender'):
            gender = params['gender'].strip().lower()
            gender = 'male' if gender in ['m', 'male'] else 'female' if gender in ['f', 'female'] else ''
            vals.update({'gender': gender})

        if params.get("de_shift"):
            shift_id = request.env['hr.employee.shift.type'].search([('code', '=', params.get('de_shift'))], limit=1)
            vals.update({'shift_type_id': shift_id and shift_id.id or False})
        if params.get("vehicle_cteg"):
            vehicle_category_id = request.env['driver.vehicle.category'].search([('code', '=', params.get('vehicle_cteg'))],limit=1)
            if vehicle_category_id:
                if  not driver_rec or  (driver_rec and driver_rec.vehicle_category_id != vehicle_category_id):
                    vals.update({'vehicle_category_id': vehicle_category_id and vehicle_category_id.id or False})
            else:
                raise APIError(status="REJECTED", status_code=500, message="Vehicle Category not available")
        if params.get('driver_category'):
            # driver_vals = {}
            vals.update({'driver_category': params.get('driver_category').lower()})
            if driver_rec:
                dedicated_customer_ids = driver_rec.dedicated_customer_ids
                if dedicated_customer_ids:
                    dedicated_customer_ids.emp_id = False
        else:
            vals.update({'driver_category': False})


        if params.get('is_dedicated_orders') and params.get('is_dedicated_orders').lower() == 'true':
            vals.update({'is_dedicated_orders': True})
        else:
            vals.update({'is_dedicated_orders': False})
        # Handle document details
        if params.get('document_details'):
            if driver_rec:
                driver_rec.update({'vehicle_attachment_ids': False})

            document_list = self._process_documents(params['document_details'])
            if isinstance(document_list, str):  # Error message returned
                raise APIError(status="REJECTED", status_code=500, message=document_list)
            vals['vehicle_attachment_ids'] = document_list

        # Create or update the driver record
        if not driver_rec:
            vals['job_id'] = request.env.ref("qwqer_base.hr_job_delivery_executive").id  # Default job ID
            driver_rec = request.env['hr.employee'].sudo().create(vals)
            create_flag = True
        else:
            driver_rec.write(vals)
            create_flag = False
        if request.env.company.cashfree_env and request.env.company.cashfree_env.lower() == "prod":
            if driver_ifsc != params.get('ifsc_code', False) or driver_account != params.get('account_no', False):
                _logger.info("Driver Creation Api Before Beneficiary.**Driver ID:%s, **Time:%s", params.get('driver_id', False),
                             fields.datetime.now())
                if params.get('ifsc_code', False) and params.get('account_no', False):
                    driver_rec.get_add_driver_beneficiary()
                elif params.get('ifsc_code', False) and driver_rec.account_no:
                    driver_rec.get_add_driver_beneficiary()
                elif params.get('account_no', False) and driver_rec.ifsc_code:
                    driver_rec.get_add_driver_beneficiary()
                _logger.info("Driver Creation Api After Beneficiary. **Driver ID:%s, **Time:%s", params.get('driver_id', False),
                             fields.datetime.now())

        # Success response
        msg = "Driver Created Successfully" if create_flag else "Driver Data Updated Successfully"
        return {
            'status': "SUCCESS",
            'status_code': 200,
            'msg': msg,
        }

    @staticmethod
    def _process_additional_fields(params, vals):
        """
        Process additional fields for the driver.
        """
        field_mapping = {
            'vehicle_type': 'vehicle_type',
            'joining_date': 'join_date',
            'ifsc_code': 'ifsc_code',
            'account_no': 'account_no',
            'upi_id': 'upi_id',
            'vehicle_no': 'vehicle_no',
            'vendor_name': 'employee_vendor_name',
            'referred_by': 'employee_referred_by',
            'address': 'emp_address',
            'emergency_phone': 'emergency_phone',
            'reporting_location': 'employee_reporting_location',
            'reporting_pincode': 'employee_reporting_pin_code',
            'blood_group': 'blood_group',
            'dob': 'birthday',
            'nominee_name': 'nominee',
            'nominee_relation': 'nominee_relation',
            'nominee_dob': 'employee_nominee_dob',
            'blocked_reason': 'blocked_reason',
            'pan_no': 'pan_no',
                }
        for param_key, model_field in field_mapping.items():
            if param_key in params.keys():
                        vals.update(
                            {model_field: params.get(param_key) or False if isinstance(params.get(param_key), str) else False})

    @staticmethod
    def _process_documents(documents):
        """
        Process document details and return a list of attachment values.
        """
        document_list = []
        for idx, doc in enumerate(documents):
            try:
                exp_date = datetime.strptime(doc.get('exp_date'), "%Y-%m-%d").date() if doc.get(
                    'exp_date') else False
            except:
                raise APIError(status="REJECTED", status_code=500, message="Date format is incorrect")

            if not doc.get('document_code') or not doc.get('document_type'):
                raise APIError(status="REJECTED", status_code=500, message="Document type or Name not found")

            doc_type = request.env['driver.document.type'].sudo().search(
                [('code', '=', doc['document_code']), ('type', '=', doc['document_type'].lower())], limit=1)

            if not doc_type:
                raise APIError(status="REJECTED", status_code=500, message=f"Document type is not available for document {doc['document_code']}")

            document_list.append((0, idx, {
                'doc_type_id': doc_type.id,
                'exp_date': exp_date,
                'doc_file': doc.get('document_link', False),
                'document_number': doc.get('document_number', False),
            }))
        return document_list


