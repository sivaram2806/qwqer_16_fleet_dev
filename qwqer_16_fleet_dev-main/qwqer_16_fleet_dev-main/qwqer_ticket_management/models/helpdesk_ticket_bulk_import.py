import os
import tempfile
import binascii
import base64
import certifi
import urllib3
import logging
import magic

from odoo.exceptions import UserError,ValidationError
from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class HelpTicketBulkImport(models.Model):
    _name = 'help.ticket.bulk.import'
    _description = 'Fleet Enquiry Bulk Import'
    _rec_name = 'name'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence No')
    state = fields.Selection([('draft', 'Draft'),
                              ('complete_with_fail', 'Completed With Failures'),
                              ('complete', 'Completed')
                              ], default='draft', copy=False, string="Status")
    customer_id = fields.Many2many('res.partner',
                                  string='Customers *',
                                  help='Select the Customers',
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    upload_file = fields.Binary(string='Upload File', attachment=True)
    file_name = fields.Char('File Name')
    bulk_import_line_ids = fields.One2many('help.ticket.bulk.import.line','bulk_import_id',
                                           string='Fleet Enquiry Bulk Import Lines',
                                           domain=[('state','=','fail')])
    success_record_count = fields.Integer(string='Success Records', compute='get_success_record_count')
    ticket_ids = fields.Many2many('help.ticket', 'import_help_ticket_rel', 'import_id', 'ticket_id', string='Tickets')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    upload_type = fields.Selection([("non_existing", "New Customer(s)"), ("existing", "Existing Customer(s)")]
                                   , default="non_existing", string="Upload For")

    @api.model
    def create(self, vals_list):
        """Create a new helpdesk ticket.
        This method is called when creating a new helpdesk ticket. It
        generates a unique name for the ticket using a sequence if no
        name is provided.
        """
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'help.ticket.bulk.import')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'help.ticket.bulk.import')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            vals_list['name'] = new_sequence.next_by_id()
        else:
            vals_list['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('help.ticket.bulk.import')

        res = super().create(vals_list)
        if res.upload_file:
            self.validate_mime_type(res.upload_file)
        return res

    def write(self, vals):
        for rec in self:
            res = super().write(vals)
            if vals.get('upload_file'):
                rec.validate_mime_type(rec.upload_file)
        return res

    def validate_mime_type(self, file):
        file_bytes = base64.b64decode(file)
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_bytes)
        valid_mime_types = ['application/vnd.ms-excel',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        if mime_type not in valid_mime_types:
            raise ValidationError('Invalid file type. Only XLS and XLSX files are allowed.')

    @api.depends('success_record_count')
    def get_success_record_count(self):
        for rec in self:
            rec.success_record_count = self.env['help.ticket.bulk.import.line'].search_count([('bulk_import_id', '=', rec.id),
                                                                                        ('state', '=', 'success')])

    def action_view_success_ticket_data(self):
        for rec in self:
            if rec.ticket_ids:
                return {
                    'name': _('Enquiries'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'help.ticket',
                    'domain': [('id', 'in', rec.ticket_ids.ids)]
                }

    def print_xlsx(self):
        data = {
            'ids': self.env.context.get('active_ids', []),
            'model': 'help.ticket.bulk.import',
        }
        report = self.sudo().env.ref('qwqer_ticket_management.helpdesk_ticket_report_xlsx')
        report = report.report_action(self, data=data, )
        return report

    def create_lines(self, state, row_no, msg=None):
        self.env["help.ticket.bulk.import.line"].create({
            'state': state,
            'row_no': row_no + 1,
            'failure_reason': msg,
            'bulk_import_id': self.id
        })

    def validation_checks(self, line, row_no, row_map):
        """
        Perform validation checks on the given line based on the provided row_map.
        Logs failure or success states accordingly.
        """
        msg = []
        return_vals = {}
        # Validate float fields
        float_fields = {
            'vendor_rate': 'Vendor Rate',
            'tonnage': 'Tonnage',
            'target_rate': 'Target Rate'
        }

        for field_key, field_name in float_fields.items():
            field_value = line[row_map.get(field_key)]
            if field_value and not isinstance(field_value, float):
                msg.append(f'{field_name} must be a float value.')

        # Validate required fields
        required_fields = {
            'opportunity_name': 'Opportunity Name',
            'type_of_vehicle': 'Vehicle Type',
            'source': 'Source',
            'destination': 'Destination',
            'no_of_vehicles': 'No. Of Vehicles',
            'rate_type': 'Rate Type'
        }

        selection_fields = {
            'type_of_vehicle': line[row_map.get('type_of_vehicle')] if row_map.get('type_of_vehicle') else None,
            'source': line[row_map.get('source')] if row_map.get('source') else None,
            'destination': line[row_map.get('destination')] if row_map.get('destination') else None,
            'region_id': line[row_map.get('region_id')] if row_map.get('region_id') else None
        }

        for field_key, field_name in required_fields.items():
            if not line[row_map.get(field_key)]:
                msg.append(f'{field_name} is a required field and is empty.')

        for field_key, field_name in selection_fields.items():
            if field_name:
                if field_key in ['source', 'destination']:
                    source_check = self.get_res_state_city(field_key, field_name)
                    if source_check.get('fail_message'):
                        msg.append(source_check.get('fail_message'))
                    else:
                        if field_key == 'source':
                            return_vals.update({field_key: source_check.get('source')})
                        elif field_key == 'destination':
                            return_vals.update({field_key: source_check.get('destination')})
                elif field_key == 'type_of_vehicle':
                    vehicle_type_check = self.get_vehicle_type(field_key, field_name)
                    if vehicle_type_check.get('fail_message'):
                        msg.append(vehicle_type_check.get('fail_message'))
                    else:
                        return_vals.update({field_key: vehicle_type_check.get('type_of_vehicle')})
                elif field_key == 'region_id':
                    region_id_check = self.get_region_data(field_key, field_name)
                    if region_id_check.get('fail_message'):
                        msg.append(region_id_check.get('fail_message'))
                    else:
                        return_vals.update({field_key: region_id_check.get('region_id')})

        # Validate user details
        users = {'vendor_rate_given_by': line[row_map.get('vendor_rate_given_by') or None],
                 'assigned_user': line[row_map.get('assigned_user') or None],
                 'enquiry_generated_by': line[row_map.get('enquiry_generated_by') or None]}
        for key, user in users.items():
            if user:
                user_check = self.get_users_details(key,user)
                if user_check.get('fail_message'):
                    msg.append(user_check.get('fail_message'))
                else:
                    return_vals.update({key: user_check.get('user_id')})

        if not line[row_map.get('tonnage')] and line[row_map.get('rate_type')] == 'Tonnage Wise':
            msg.append('Tonnage is a required field since Rate Type is selected as Tonnage Wise.')

        customer_name = line[row_map.get('customer_name')]
        if self.upload_type == "existing":
            customer_check = self.get_customer_by_name(customer_name)
            if customer_check.get('fail_message'):
                msg.append(customer_check.get('fail_message'))
            else:
                return_vals.update({"customer_id": customer_check.get('customer_id')})
        else:
            if not customer_name:
                msg.append('Customer Name is a required field and is empty.')
        if msg:
            state = 'fail'
            msg = '\n'.join(msg)
            self.create_lines(state=state, row_no=row_no, msg=msg or None)
            return_vals.update({'error': msg})
        return return_vals

    def update_validation_checks(self, line, row_no, row_map):
        """
        Validates the line data against the provided row_map and customer_obj.
        Returns a dictionary containing validation results.
        """
        return_vals = {}
        errors = []

        ticket_number = row_map.get('ticket_number')
        customer_name = row_map.get('customer_name')
        stage_name = row_map.get('stage')

        # Validate Enquiry Number
        ticket_value = line[ticket_number]
        ticket = None
        if not ticket_value:
            errors.append('Enquiry Number is a required field and is empty.')
        else:
            ticket = self.env['help.ticket'].search([('name', 'ilike', ticket_value)], limit=1)
            lost = self.env.ref('qwqer_ticket_management.ticket_stage_lost').id
            won = self.env.ref('qwqer_ticket_management.ticket_stage_won').id
            if not ticket:
                errors.append('Invalid Enquiry Number')
            elif ticket.stage_id.id not in [lost, won]:
                return_vals['ticket_obj'] = ticket
            else:
                errors.append('Enquiry Is in non editable stage')

        # Validate Customer Name
        customer_value = line[customer_name]
        if not customer_value:
            errors.append('Customer Name is a required field for Update and it is missing.')
        elif (ticket.customer_id and ticket.customer_id.name != customer_value) or (not ticket.customer_id and ticket.customer_name != customer_value):
            errors.append("Customer Name Mismatch")

        stage_value = line[stage_name]
        stage = self.env['ticket.stage'].search([('name', '=', stage_value)], limit=1) if stage_value else False

        if not stage:
            if not stage_value:
                errors.append('Stage is a required field for Update and it is missing.')
            else:
                errors.append("The given stage is not found.")
        else:
            # Cache references to avoid multiple database calls
            ref_stage_rates_given = self.env.ref('qwqer_ticket_management.ticket_stage_rates_given')
            ref_stage_rates_not_given = self.env.ref('qwqer_ticket_management.ticket_stage_rates_not_given')
            ref_stage_won = self.env.ref('qwqer_ticket_management.ticket_stage_won')
            ref_stage_lost = self.env.ref('qwqer_ticket_management.ticket_stage_lost')

            vendor_rate = line[row_map.get('vendor_rate')]

            # Check for stage-specific conditions
            if stage == ref_stage_rates_given and not vendor_rate:
                errors.append("You are not allowed to change the stage since Vendor Rate is not given.")
            elif stage == ref_stage_rates_not_given and vendor_rate:
                errors.append("You are not allowed to change the stage since Vendor Rate is given.")
            elif stage == ref_stage_won and not vendor_rate:
                errors.append("You are not allowed to change to won stage since Vendor Rate is not given.")

            # Determine if the stage is 'won' or 'lost'
            if stage in {ref_stage_won, ref_stage_lost}:
                return_vals['is_won_lost'] = False

        return_vals['stage_name_obj'] = stage

        if errors:
            failure_msg = '\n'.join(errors)
            self.create_lines(state='fail', row_no=row_no, msg=failure_msg)
            return_vals['failure_msg'] = failure_msg

        return return_vals

    def get_vals_position(self, sheet_headers):
        header_positions = {}
        headers = {'Enquiry Number': 'ticket_number', 'Opportunity Name': 'opportunity_name', 'Customer Name': 'customer_name',
                   'Enquiry Generated By': 'enquiry_generated_by',
                   'Type of Vehicle': 'type_of_vehicle', 'Source': 'source', 'Destination': 'destination',
                   'Tonnage': 'tonnage', 'No. Of Vehicles': 'no_of_vehicles', 'Target Rate': 'target_rate', 'Vendor Rate': 'vendor_rate',
                   'Rate Type': 'rate_type', 'Vendor Rate Given By': 'vendor_rate_given_by', 'Assigned User': 'assigned_user', 'Region': 'region_id',
                   'Vehicle Type Comments': 'vehicle_type_comments', 'Traffic Team Comment': 'traffic_team_comment','Stage': 'stage'}
        for name, val in headers.items():
            if name in sheet_headers:
                index = sheet_headers.index(name)
                header_positions[val] = index
        return header_positions

    def get_users_details(self, key, user_name_row):
        users_details_return = {}
        user = self.env['res.users'].search([('name', 'ilike', user_name_row)], limit=1)
        users_details_return.update({'user_id': user.id}) if user else users_details_return.update(
            {'fail_message': f'The given {key} user is not found.'})
        return users_details_return

    def get_customer_by_name(self, name):
        customer_details = {}
        customer_id = self.env['res.partner'].search([('name', '=', name)], limit=1)
        customer_details.update({'customer_id': customer_id.id}) if customer_id else customer_details.update(
            {'fail_message': f'The given customer is not found.'})
        return customer_details

    def get_vehicle_type(self, key, type_of_vehicle):
        vehicle_type_return = {}
        vehicle_type = self.env['vehicle.vehicle.type'].search([('name', 'ilike', type_of_vehicle)], limit=1)
        vehicle_type_return.update({'type_of_vehicle': vehicle_type.id}) if vehicle_type else vehicle_type_return.update(
            {'fail_message': f'The given {key} type of vehicle is not found.'})
        return vehicle_type_return

    def get_res_state_city(self, key, city):
        city_lower = ''.join(city.split()).lower() if city else ''
        state_city = self.env['res.state.city'].search([('normalized_name', 'ilike', city_lower)], limit=1)
        state_city_return = {}
        if state_city:
            state_city_return['source'] = state_city.id
            state_city_return['destination'] = state_city.id
        else:
            state_city_return['fail_message'] = f'The given {key} Source is not found.'
            state_city_return['fail_message'] = f'The given {key} Destination is not found.'
        return state_city_return

    def get_region_data(self, key, region_data):
        regions_data_return = {}
        regions = self.env['sales.region'].search([('name', 'ilike', region_data)], limit=1)
        regions_data_return.update({'region_id': regions.id}) if regions else regions_data_return.update(
            {'fail_message': f'The given {key} user is not found.'})
        return regions_data_return

    def import_file(self):
        """Function to import trip sheet from an xlsx file."""
        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.upload_file))
            book = xlrd.open_workbook(file_string.name)
            sheet = book.sheet_by_index(0)
        except Exception as e:
            raise Warning(_("Please choose the correct file. Error: %s" % str(e)))
        sheet_headers = sheet.row_values(0)
        row_map = self.get_vals_position(sheet_headers)
        if not row_map:
            raise ValidationError('The headers inside the uploaded file is invalid, '
                                  'Please make the downloaded template and the file are same.')
        if sheet.nrows <= 1:
            raise ValidationError('Sheet has no row value, Please add at least one row')
        for i in range(1, sheet.nrows):
            line = list(sheet.row_values(i))
            data_present = any(line)
            if not data_present:
                continue
            validation = self.validation_checks(line, i, row_map)
            if validation.get('error'):
                continue
            try:
                rate_type = 'lane_wise' if line[row_map.get('rate_type')] == 'Lane Wise' \
                    else 'tonnage_wise' if line[row_map.get('rate_type')] == 'Tonnage Wise' else None
                vendor_rate = line[row_map.get('vendor_rate')] or 0.00
                stage_rates_given = self.env.ref('qwqer_ticket_management.ticket_stage_rates_given').id
                stage_open = self.env.ref('qwqer_ticket_management.ticket_stage_open').id
                vals = {
                    'opportunity_name': line[row_map.get('opportunity_name')],
                    'customer_id': validation.get('customer_id'),
                    'is_existing_customer': True if validation.get('customer_id') else False,
                    'customer_name': line[row_map.get('customer_name')] if line[row_map.get('customer_name')] else validation.get('customer_id'),
                    'enquiry_generated_by_id': validation.get('enquiry_generated_by') or self.env.user.id,
                    'vehicle_type_id': validation.get('type_of_vehicle'),
                    'source_id': validation.get('source'),
                    'destination_id': validation.get('destination'),
                    'vendor_rate': vendor_rate or 0.00,
                    'vendor_rate_by_id': validation.get('vendor_rate_given_by') or self.env.user.id if vendor_rate > 0.0 else None,
                    'stage_id': stage_rates_given if vendor_rate > 0.00 else stage_open,
                    'tonnage': line[row_map.get('tonnage')] or 0.0,
                    'no_of_vehicles': line[row_map.get('no_of_vehicles')] or 0,
                    'target_rate': line[row_map.get('target_rate')] or 0.00,
                    'rate_type': rate_type,
                    'assigned_user': validation.get('assigned_user') or self.env.user.id,
                    'region_id':validation.get('region_id') or None,
                    'vehicle_type_comment': line[row_map.get('vehicle_type_comments')] or None,
                    'traffic_team_comment': line[row_map.get('traffic_team_comment')] or None
                }
                if sheet_headers[0] == 'Enquiry Number':
                    update_check = self.update_validation_checks(line, i, row_map)
                    if update_check.get('failure_msg'):
                        continue
                    ticket_id = update_check['ticket_obj']
                    vals.update({
                        'stage_id': update_check.get('stage_name_obj', "Open"),
                        'is_won_lost': update_check.get('is_won_lost', True)
                    })
                    ticket_id.write(vals)
                else:
                    ticket_id = self.env['help.ticket'].create(vals)
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                self.create_lines(state='fail', row_no=i, msg='Error')
            else:
                self.create_lines(state='success', row_no=i)
                self.ticket_ids = [(4, ticket_id.id)]

    def action_submit(self):
        for rec in self:
            if not rec.upload_file:
                raise ValidationError('Upload File is not selected. Please select a file for upload.')
            rec.import_file()
            if 'fail' in rec.bulk_import_line_ids.mapped('state'):
                rec.state = 'complete_with_fail'
            else:
                rec.state = 'complete'


class HelpTicketBulkImportLine(models.Model):
    _name = 'help.ticket.bulk.import.line'
    _description = 'Fleet Enquiry Bulk Import Line'

    bulk_import_id = fields.Many2one('help.ticket.bulk.import')
    name = fields.Char(string="Enquiry No")
    row_no = fields.Integer(string='Row No')
    state = fields.Selection([('success', 'Success'),
                              ('fail', 'Failed')], string="Status")
    failure_reason = fields.Text(string="Failure Reason")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
