import logging
import sys

import pytz
import json
from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.addons.qwqer_api_base import check_auth_validity
from odoo.addons.qwqer_api_base.exceptions import APIError

_logger = logging.getLogger(__name__)


class AccountMoveAPI(http.Controller):

    @http.route('/account/move/create/', type='json', methods=['POST'], auth="qwy_api_key", csrf=False)
    @check_auth_validity
    def account_move_entry(self, api_raw_log=None, **kwargs):
        """API to create account move"""
        print('hello')
        try:
            params = {k: (False if v is None else v) for k, v in kwargs.items()}
            if not kwargs:
                raise APIError(status="REJECTED", status_code=500,
                               message="No Data Received or Incorrect Data Format!")
            _logger.info("Account Move Entry API : Request Received, Processing ...")
            response = self._prepare_and_create_move(params)
            api_raw_log.update({
                "response": json.dumps(response),
                'response_date': fields.Datetime.now(),
                'name': "Move Created",
                'status': response['status']
            })
            return json.dumps(response)

        except APIError as e:
            return e.to_response(api_raw_log=api_raw_log, name="Account Entry Create API")
        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}")
            error = APIError(status="error", status_code=500,
                             message="An unexpected error occurred. Please try again later.")
            return error.to_response(api_raw_log=api_raw_log, name="Account Entry Create API")

    def validate_required_fields(self, params):
        required_fields = ['journal_id', 'move_type', 'line_ids', 'date']
        missing_fields = [field for field in required_fields if not params.get(field)]
        if missing_fields:
            raise APIError(
                status="REJECTED",
                status_code=400,
                message=f"Missing required fields: {', '.join(missing_fields)}"
            )


    def validate_journal(self, journal_name):
        journal = request.env['account.journal'].sudo().search([('name', '=', journal_name),('company_id','=',request.env.company.id)], limit=1)
        if not journal:
            raise APIError(
                status="REJECTED",
                status_code=400,
                message=f"Journal with name {journal_name} does not exist."
            )
        return journal

    def get_service_type(self, service_type):
        service_type_id = False
        if service_type:
            if service_type == 'delivery':
                service_type_id = request.env['partner.service.type'].search(
                    [('is_delivery_service', '=', True), ('company_id', '=', request.env.company.id)], limit=1)
            elif service_type == 'qwqershop':
                service_type_id = request.env['partner.service.type'].search(
                    [('is_qshop_service', '=', True), ('company_id', '=', request.env.company.id)], limit=1)
            elif service_type == 'vehicle':
                service_type_id = request.env['partner.service.type'].search(
                    [('is_fleet_service', '=', True), ('company_id', '=', request.env.company.id)], limit=1)
        return service_type_id

    def get_segment(self, segment):
        segment_name = {
            'QWQER Fleet - FLeet FTL': 'QWQER Fleet - FTL',
            'QWQER Technologies - Fleet FTL': 'QWQER Fleet - FTL',
            'QWQER Technologies - UrbanHaul': 'QWQER Fleet - Urban Haul',
            'QWQER Fleet - Urban Haul': 'QWQER Fleet - Urban Haul',
            'QWQER Express - Large B2B': 'QWQER Express - Large B2B',
            'QWQER Express - Platform': 'QWQER Express - Platform',
            'QWQER Express - Rental': 'QWQER Express - Rental',
            'QWQER Express - SME': 'QWQER Express - SME',
            'QWQER Express - E-Comm': 'QWQER Express - E-Comm',
        }

        if segment:
            move_segment = segment_name.get(segment)
            if move_segment:
                segment_id = request.env['partner.segment'].search([('name', '=', move_segment),('company_id','=',request.env.company.id)])
                if segment_id:
                    return segment_id
        return False

    def validate_account(self, account_code):
        account = request.env['account.account'].sudo().search([('code', '=', account_code),('company_id','=',request.env.company.id)], limit=1)
        if not account:
            raise APIError(
                status="REJECTED",
                status_code=400,
                message=f"Account with code {account_code} does not exist."
            )
        return account

    def prepare_line_items(self, params):
        line_items = []
        for line in params['line_ids']:
            # required_line_fields = []
            if params['move_type'] in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                required_line_fields = ['product_id', 'quantity','account_id']
            else:
                required_line_fields = ['debit','credit','account_id']

            missing_line_fields = [field for field in required_line_fields if line.get(field) is None]
            if missing_line_fields:
                raise APIError(
                    status="REJECTED",
                    status_code=400,
                    message=f"Missing required fields in line: {', '.join(missing_line_fields)}"
                )

            account = self.validate_account(line['account_id'])
            partner_id = False
            if line.get("partner_id"):
                partner_id = request.env['res.partner'].search(
                    [('customer_ref_key', '=', int(line.get("partner_id")))])
            product = None
            if line.get('product_id'):
                product = request.env['product.template'].sudo().search([('name', '=', line['product_id']),('company_id','=',request.env.company.id)], limit=1)
                print(line.get('product_id'))
                print(product.id)
                if not product:
                    raise APIError(
                        status="REJECTED",
                        status_code=400,
                        message=f"Product with ID {line['product_id']} does not exist."
                    )

            taxes = []
            if line.get('tax_ids'):
                for tax_id in line['tax_ids']:
                    tax = request.env['account.tax'].sudo().search([('name', '=', tax_id),('company_id','=',request.env.company.id)], limit=1)
                    if not tax:
                        raise APIError(
                            status="REJECTED",
                            status_code=400,
                            message=f"Tax with ID {tax_id} does not exist."
                        )
                    taxes.append(tax.id)
            if params['move_type'] in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                line_data = {
                    'account_id': account.id,
                    'name': line.get('name',''),
                    'partner_id': partner_id and partner_id.id,
                    'product_id': product.id if product else False,
                    'quantity': line.get('quantity', 1.0),
                    'price_unit': line.get('pricing_unit', 0.0),
                    'tax_ids': [(6, 0, taxes)] if taxes else False,
                }
            else:
                line_data = {
                    'account_id': account.id,
                    'partner_id': partner_id and partner_id.id,
                    'debit': line['debit'],
                    'date': params['date'],
                    'credit': line['credit'],
                    'name': line.get('name', ''),
                }

            if line.get('analytic_account_id'):
                analytic_account = request.env['account.analytic.account'].search([('name','=',line.get('analytic_account_id')),('company_id','=',request.env.company.id)],limit=1)
                if analytic_account:
                    line_data.update({'analytic_distribution' : {
                    analytic_account.id: 100
                }})

            line_items.append((0, 0, line_data))

        return line_items

    def create_account_move(self, params, journal, line_items, service_type_id, segment, region_id):
        partner_id = request.env['res.partner'].search([('customer_ref_key','=',int(params.get('partner_id')))]) if int(params.get('partner_id')) else None
        move_data = {
            'journal_id': journal.id,
            'move_type': params['move_type'],
            'date': params['date'],
            'ref': params.get('ref', ''),
            'narration': params.get('narration', ''),
            'partner_id': partner_id.id if partner_id else False,
            'service_type_id': service_type_id.id if service_type_id else False,
            'segment_id': segment.id if segment else False,
            'region_id': region_id.id if region_id else False,
        }

        if params['move_type'] in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
            move_data.update({
                'invoice_date': params.get('invoice_date'),
                'invoice_date_due': params.get('invoice_date_due'),
            })
            move_data['invoice_line_ids'] = line_items
        else:
            move_data['line_ids'] = line_items

        account_move = request.env['account.move'].sudo().create(move_data)

        if params.get('post', False):
            account_move.action_post()

        return account_move

    def _prepare_and_create_move(self, params):
        try:
            # Validate required fields
            self.validate_required_fields(params)

            # Validate journal]
            journal = self.validate_journal(params['journal_id'])

            # Get service type and segment if applicable
            service_type_id = self.get_service_type(params.get('service_type_id'))
            segment = self.get_segment(params.get('segment_id'))
            region_id = request.env['sales.region'].search([('region_code', '=', params.get('region_id')),('company_id','=',request.env.company.id)])

            # Prepare line items
            line_items = self.prepare_line_items(params)

            # Create the account move
            account_move = self.create_account_move(params, journal, line_items, service_type_id, segment, region_id)

            _logger.info(f"Account move created successfully with ID: {account_move.id}")
            return {
                'status': 'SUCCESS',
                'status_code': 200,
                'message': 'Account move created successfully.',
                'move_id': account_move.id,
            }

        except Exception as e:
            _logger.error(f"Error creating account move: {str(e)}")
            raise APIError(
                status="error",
                status_code=500,
                message="An error occurred while creating the account move."
            )



