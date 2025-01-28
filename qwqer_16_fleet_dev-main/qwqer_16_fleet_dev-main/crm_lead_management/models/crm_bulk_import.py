import tempfile
import binascii
import base64
import re
import logging
import magic

from odoo.exceptions import ValidationError, UserError
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


class CrmBulkImport(models.Model):
    _name = 'crm.bulk.import'
    _description = 'Crm Bulk Import'
    _rec_name = 'name'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence No', default='Draft')
    state = fields.Selection([('draft', 'Draft'),
                              ('complete_with_fail', 'Completed With Failures'),
                              ('complete', 'Completed')
                              ], default='draft', copy=False, string="Status")
    upload_file = fields.Binary(string='Upload File', attachment=True)
    file_name = fields.Char('File Name')
    bulk_import_line_ids = fields.One2many('crm.bulk.import.line', 'bulk_import_id',
                                           string='Crm Bulk Import Lines', domain=[('state', '=', 'fail')], readonly=1)
    success_record_count = fields.Integer(string='Success Records', compute='get_success_record_count')
    crm_ids = fields.Many2many('crm.lead', 'import_crm_rel', 'import_id', 'crm_id', string='Leads')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model
    def create(self, vals_list):
        res = super(CrmBulkImport, self).create(vals_list)
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
            rec.success_record_count = self.env['crm.bulk.import.line'].search_count(
                [('bulk_import_id', '=', rec.id),
                 ('state', '=', 'success')])

    def action_view_success_leads(self):
        for rec in self:
            if rec.crm_ids:
                return {
                    'name': _('Leads'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'crm.lead',
                    'domain': [('id', 'in', rec.crm_ids.ids)]
                }

    def print_xlsx(self):
        for rec in self:
            data = {
                'ids': self.env.context.get('active_ids', []),
                'model': 'crm.lead',
            }
            report = self.sudo().env.ref('crm_lead_management.crm_report_action')
            report.report_file = "Crm_Bulk_Import - %s" % (rec.file_name or '')
            return report.report_action(rec, data)

    def data_validation(self, sheet, row, line):
        msg = []
        for rec in self:
            if line[0] == '':
                msg.append('Lead name is required when importing data.')
            if line[1] == '':
                msg.append('Contact name is required when importing data.')
            if line[4] == '':
                msg.append('Service Type is required when importing data.')
            if line[5] == '':
                msg.append('Region is required when importing data.')
            if line[6] == '':
                msg.append('Source is required when importing data.')
            if line[7] == '':
                msg.append('Customer Type is required when importing data.')
            if line[8] == '':
                msg.append('Customer Segment is required when importing data.')
            if line[9] == '':
                msg.append('Follow Up Status is required when importing data.')
            if line[3]:
                email_exist = self.env['crm.lead'].search([('email_from', '=', line[3]), ('company_id', '=', self.company_id.id)])
                if email_exist:
                    msg.append('Email ID Already Exist')
            if line[2] == '':
                msg.append('Phone is required when importing data.')
            else:
                phone_number = sheet.cell_value(row, 2)
                if isinstance(phone_number, float):
                    phone_number = str(int(phone_number))
                phone_number = re.sub(r'\s+', '', phone_number)
                # Validate phone number: must contain exactly 10 digits
                if len(phone_number) != 10 or not phone_number.isdigit():
                    msg.append('Import valid 10 digits Mobile number')
                elif phone_number:
                    phone_exist = self.env['crm.lead'].search([('phone', '=', phone_number), ('company_id', '=', self.company_id.id)])
                    partner_exist = self.env['res.partner'].search(['|',('phone', 'like',phone_number),('mobile','like',phone_number), ('company_id', '=', self.company_id.id)])
                    if phone_exist or partner_exist:
                        msg.append('You Cannot import lead with duplicate phone number')
            if line[4] and line[8]:
                service_type = self.get_service_type_by_name(line[4])
                segment = self.get_customer_segment_by_name(line[8])
                if not service_type.is_fleet_service and segment.is_fleet_service:
                    msg.append('You Cannot import lead with service type as Express and segment as fleet')
                if service_type.is_fleet_service and not segment.is_fleet_service:
                    msg.append('You Cannot import lead with service type as Fleet and segment as Express')

            if msg:
                self.env["crm.bulk.import.line"].create({'state': 'fail',
                                                         'row_no': row,
                                                         'failure_reason': ", ".join(msg),
                                                         'bulk_import_id': rec.id})
            else:
                self.env["crm.bulk.import.line"].create({'state': 'success',
                                                         'row_no': row,
                                                         'bulk_import_id': rec.id})
        return msg

    def get_phone(self, sheet, row):
        phone_number = sheet.cell_value(row, 2)
        if isinstance(phone_number, float):
            phone_number = str(int(phone_number))
        phone_number = re.sub(r'\s+', '', phone_number)
        return phone_number

    def get_service_type_by_name(self, name):
        service = self.env['partner.service.type'].search([('name', 'ilike', name),
                                                           ('company_id', '=', self.company_id.id),
                                                           ('is_customer', '=', True)], limit=1)
        return service

    def get_lead_type_by_name(self, name):
        lead_type = self.env['utm.source'].search([('name', 'ilike', name)], limit=1)
        return lead_type.id

    def get_customer_type(self, customer_type):
        if customer_type.lower() in ["b2b", "b2c"]:
            return customer_type.lower()
        return "b2c"

    def get_region_by_name(self, name):
        region_id = self.env['sales.region'].search([('name', 'ilike', name), ('company_id', '=', self.company_id.id)], limit=1)
        return region_id

    def get_customer_segment_by_name(self, segment):
        segment_id = self.env['partner.segment'].search([('name', 'ilike', segment), ('company_id', '=', self.company_id.id)], limit=1)
        return segment_id

    def get_follow_up_status(self, status):
        follow_id = self.env['mail.activity.type'].sudo().search([('res_model', '=', 'crm.lead'),
                                                                  ('name', 'ilike', status), ('company_id', '=', self.company_id.id)], limit=1)
        return follow_id.id

    def get_sales_person(self, name):
        sale_person_id = self.env['res.users'].sudo().search([('name', 'ilike', name)], limit=1)
        return sale_person_id

    def get_customer_industry(self, name):
        industry_id = self.env['res.partner.industry'].sudo().search([('name', 'ilike', name)], limit=1)
        return industry_id

    def import_file(self):
        """ function to import leads xlsx file """
        try:
            file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
            file_string.write(binascii.a2b_base64(self.upload_file))
            book = xlrd.open_workbook(file_string.name)
            sheet = book.sheet_by_index(0)
        except Exception as e:
            raise Warning(_("Please choose the correct file. Error: %s" % str(e)))
        # Expected headers
        expected_headers = ['Lead', 'Contact Name', 'Phone', 'Email',
                            'Service Type', 'Region', 'Source/ Lead Type', 'Customer Type', 'Customer Segment',
                            'Follow Up Status','Sales Person','Customer Industry', 'Comments'
                            ]
        # Read the actual headers from the first row
        actual_headers = [cell.value for cell in sheet.row(0)]
        # Validate the headers
        if actual_headers != expected_headers:
            raise ValidationError(_("The uploaded file has incorrect headers."))
        if sheet.nrows <= 1:
            raise ValidationError('Sheet has no row value. Please add at least one row')
        for row in range(1, sheet.nrows):
            line = list(sheet.row_values(row))
            if not any(line):
                continue
            data_validate = self.data_validation(sheet, row, line)
            if not data_validate:
                segment = self.get_customer_segment_by_name(line[8])
                region = self.get_region_by_name(line[5])
                user_id = self.get_sales_person(line[10])
                industry_id = self.get_customer_industry(line[11])
                vals = {
                    'name': line[0],
                    'contact_name': line[1],
                    'phone': self.get_phone(sheet, row),
                    'email_from': line[3],
                    'company_id': self.company_id.id,
                    'customer_service_type': self.get_service_type_by_name(line[4]).id,
                    'region_id': region.id,
                    'source_id': self.get_lead_type_by_name(line[6]),
                    'customer_type': self.get_customer_type(line[7]),
                    'customer_segment_id': segment.id,
                    'followup_status_id': self.get_follow_up_status(line[9]),
                    'user_id': user_id.id ,
                    'industry_id': industry_id.id,
                    'comments': line[12],
                    "state_id": region.state_id.id
                }
                if segment.is_fleet_service:
                    vals['customer_segment_id'] = segment.id
                else:
                    vals['delivery_customer_segment_id'] = segment.id

                crm = self.env['crm.lead'].sudo().create(vals)
                self.crm_ids = [(4, crm.id)]


    def action_submit(self):
        for rec in self:
            if not rec.upload_file:
                raise ValidationError('Upload File is not selected. Please select a file for upload.')
            rec.import_file()
            if 'fail' in rec.bulk_import_line_ids.mapped('state'):
                rec.state = 'complete_with_fail'
            else:
                rec.state = 'complete'

            company_id = self.company_id.id
            sequence = self.env['ir.sequence'].search([('company_id', '=', company_id),
                                                       ('code', '=', 'crm.bulk.import.sequence')])
            if not sequence:
                sequence = self.env['ir.sequence'].search([('code', '=', 'crm.bulk.import.sequence')], limit=1)
                new_sequence = sequence.sudo().copy()
                new_sequence.company_id = company_id
                rec.name = new_sequence.next_by_id()
            else:
                rec.name = self.env['ir.sequence'].with_company(company_id).next_by_code('crm.bulk.import.sequence')


# For Fail Reason
class CrmBulkImportLine(models.Model):
    _name = 'crm.bulk.import.line'
    _description = 'Crm Bulk Import Line'

    bulk_import_id = fields.Many2one('crm.bulk.import')
    name = fields.Char(string="Lead")
    row_no = fields.Integer(string='Row No')
    state = fields.Selection([('success', 'Success'),
                              ('fail', 'Failed')], string="Status")
    failure_reason = fields.Text(string="Failure Reason")
