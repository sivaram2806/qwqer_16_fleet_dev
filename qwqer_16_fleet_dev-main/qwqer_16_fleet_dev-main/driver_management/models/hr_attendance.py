# -*- coding:utf-8 -*-

import pytz
from datetime import datetime,timedelta
# from dateutil import tz
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
from odoo import api, fields, models, _

class HrAttendance(models.Model):
    """
    Model modifications based on driver management
    """
    _inherit = 'hr.attendance'
    _description = 'Hr Attendance'

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(HrAttendance, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                     submenu=submenu)
    #     doc = etree.XML(res['arch'])
    #     if view_type == 'form' or view_type == "tree":
    #         if not self.env.user.has_group('zb_qwqer_hr_customization.group_for_edit_delete_attendance'):
    #             for node_form in doc.xpath("//form"):
    #                 node_form.set("delete", 'false')
    #             for node_form in doc.xpath("//tree"):
    #                 node_form.set("delete", 'false')
    #             for node_form in doc.xpath("//tree"):
    #                 node_form.set("create", 'false')
    #             for node_form in doc.xpath("//form"):
    #                 node_form.set("create", 'false')
    #             for node_form in doc.xpath("//form"):
    #                 node_form.set("edit", 'false')
    #     res['arch'] = etree.tostring(doc)
    #     return res

    @api.model
    def create(self, vals):
        if vals.get('employee_code'):
            emp_id = self.env['hr.employee'].sudo().search([('driver_uid', '=', vals.get('employee_code'))])
            if emp_id:
                vals.update({
                    'employee_id': emp_id.id
                })
        return super(HrAttendance, self).create(vals)

    #TODO @api.model
    # def to_utc_datetime(self, datetime_str):
    #     """
    #     Converts the given timestamp to UTC timezone.
    #
    #     :param datetime_str: The datetime value to convert.
    #     :return: Datetime string converted to UTC.
    #     """
    #     # Get the user's timezone or default to UTC
    #     tz_name = self.env.user.tz or self._context.get('tz') or 'UTC'
    #     try:
    #         local_tz = pytz.timezone(tz_name)
    #         local_dt = local_tz.localize(fields.Datetime.from_string(datetime_str), is_dst=None)
    #         utc_dt = local_dt.astimezone(pytz.utc)
    #         return fields.Datetime.to_string(utc_dt)
    #     except Exception as e:
    #         raise UserError(_('Failed to convert datetime to UTC: %s' % str(e)))

    #TODO def get_start_and_end(self, date):
    #     """
    #     Gets the start and end of the day in the user's timezone.
    #
    #     :param date: The date string in '%Y-%m-%d %H:%M:%S' format.
    #     :return: Start and end datetime in the user's timezone.
    #     """
    #     if not date:
    #         raise UserError(_('Date is required.'))
    #
    #     try:
    #         # Parse the input date
    #         time_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    #
    #         # Get user's timezone
    #         tz_name = self._context.get('tz') or self.env.user.tz
    #         if not tz_name:
    #             raise UserError(_('Please configure your time zone in Preferences.'))
    #
    #         # Convert to the user's timezone
    #         user_tz = pytz.timezone(tz_name)
    #         utc_time = pytz.utc.localize(time_obj)
    #         local_time = utc_time.astimezone(user_tz)
    #
    #         # Get start and end of the day
    #         start = local_time.replace(hour=0, minute=0, second=0, microsecond=0)
    #         end = start + timedelta(days=1)
    #
    #         return start, end
    #
    #     except Exception as e:
    #         raise UserError(_('Failed to get start and end of the day: %s' % str(e)))

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        """Optimized _compute_worked_hours"""
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                attendance.worked_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600.0
            else:
                attendance.worked_hours = 0.0

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ overriding _check_validity_check_in_check_out
        Verifies if check_in is earlier than check_out """
        for attendance in self:
            if not attendance.employee_id.driver_uid:
                if attendance.check_in and attendance.check_out and attendance.check_out < attendance.check_in:
                    raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """
         overriding _check_validity
        Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            if not attendance.employee_id.driver_uid:
                # Search for all relevant attendance records in one go to avoid multiple searches
                attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    '|',
                    ('check_in', '<=', attendance.check_in),  # For last attendance before check-in
                    ('check_in', '<', attendance.check_out if attendance.check_out else attendance.check_in),
                    # For last attendance before check-out
                    ('id', '!=', attendance.id),
                ], order='check_in desc')

                # Filter for last attendance before check-in
                last_attendance_before_check_in = next(
                    (att for att in attendances if att.check_in <= attendance.check_in), None)

                # Filter for last attendance before check-out
                last_attendance_before_check_out = next(
                    (att for att in attendances if attendance.check_out and att.check_in < attendance.check_out), None)

                # Validation for overlapping check-in
                if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                    raise ValidationError(
                        _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                            'empl_name': attendance.employee_id.name,
                            'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
                        })

                # Validation for open attendance (no check-out)
                if not attendance.check_out:
                    # Filter for open (no check-out) attendance
                    no_check_out_attendances = next((att for att in attendances if not att.check_out), None)
                    if no_check_out_attendances:
                        raise ValidationError(
                            _("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                                'empl_name': attendance.employee_id.name,
                                'datetime': format_datetime(self.env, no_check_out_attendances.check_in,
                                                            dt_format=False),
                            })

                # Validation for overlapping check-out
                if attendance.check_out and last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise ValidationError(
                        _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                            'empl_name': attendance.employee_id.name,
                            'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in,
                                                        dt_format=False),
                        })

    @api.onchange('employee_code')
    def _compute_employee_code(self):
        for rec in self:
            if rec.employee_code:
                emp_id = self.env['hr.employee'].sudo().search([('driver_uid', '=', rec.employee_code)])
                rec.employee_id = emp_id.id if emp_id else False

    app_total_distance = fields.Float(string='Total Distance')
    app_working_hours = fields.Float(string='App Work Hours')
    attendance_uid = fields.Char("App Ref") #V13_field: attendance_id
    date = fields.Date("Date")
    check_in = fields.Datetime(string="Check In", default=False, required=False)
    employee_id = fields.Many2one('hr.employee', string="Employee", default=False, required=False, ondelete='cascade',
                                  index=True, domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    employee_code = fields.Char(string="Driver ID", compute='_compute_employee_details', store=True)
    region_id = fields.Many2one(comodel_name='sales.region', string='Region', compute='_compute_employee_details', store=True)
    daily_payout_id = fields.Many2one('driver.payout', string="Daily Transaction")
    company_id = fields.Many2one('res.company', string="Company",
                                 compute='_compute_employee_details', store=True)

    _sql_constraints = [
        ('attendance_uid_unique', 'unique (attendance_uid)',
         'The Attendance ID must be unique per Company!')
    ]

    @api.depends('employee_id')
    def _compute_employee_details(self):
        for rec in self:
            rec.employee_code = rec.employee_id.driver_uid
            rec.region_id = rec.employee_id.region_id
            rec.company_id = rec.employee_id.company_id
