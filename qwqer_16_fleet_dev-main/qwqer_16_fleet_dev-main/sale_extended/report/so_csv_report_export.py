import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)
from datetime import date, timedelta, datetime
from dateutil import tz
import pytz
import os



class SoCsvReportExport(models.Model):
    _name = "so.csv.report"
    _description = "export  sale_order report "

    _rec_name = 'report_file_path'
    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    state_ids = fields.Many2many(comodel_name='res.country.state', string="State")
    region_ids = fields.Many2many(comodel_name='sales.region', string="Region")
    fields_to_export = fields.Many2many(
        comodel_name="export.csv.fields", string='Fields to Export')
    report_status = fields.Selection(
        selection=[('new', 'New'), ('processing', 'Processing'), ('completed', 'Completed')],
        default='new')
    report_file_path = fields.Char(string='Report File')
    batch_start = fields.Integer(string="Batch Start", default=0)
    batch_end = fields.Integer(string="Batch End")
    file = fields.Char(string="File")
    process_start_date = fields.Datetime("Process Start")
    process_end_date = fields.Datetime("Process End")

    def prepare_csv_sale_orders(self):
        processing_record = []
        if self.search([('report_status', '=', 'processing')]):
            processing_record = self.search([('report_status', '=', 'processing')], limit=1)
        elif self.search([('report_status', '=', 'new')]):
            processing_record = self.search([('report_status', '=', 'new')], limit=1)

        if processing_record:
            exec_record = processing_record[0]
            if exec_record.batch_start == 0:
                exec_record.process_start_date = (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
                _logger.info(f"Sale Order Start Processing @{exec_record.process_start_date}")
            region_lst = []
            if exec_record.state_ids:
                if not exec_record.region_ids:
                    reg = self.env['sales.region'].search([('state_id', 'in', exec_record.state_ids.ids)])
                    for rec in reg:
                        region_lst.append(rec.id)
                else:
                    reg_lst = exec_record.region_ids.ids
            else:
                if exec_record.region_ids:
                    for rec in exec_record.region_ids:
                        region_lst.append(rec.id)
            local_process_start_date = self.utc_date_to_user_local(exec_record.process_start_date).strftime('%Y-%m-%d')
            format_from_date = exec_record.from_date.strftime('%Y-%m-%d') + ' ' + '00:00:00'
            format_to_date = exec_record.process_start_date if local_process_start_date == exec_record.to_date.strftime(
                '%Y-%m-%d') else self.date_to_utc(exec_record.to_date.strftime('%Y-%m-%d') + ' ' + '23:59:59')
            from_date = self.date_to_utc(format_from_date)
            to_date = format_to_date
            domain_filter = [('create_date', '>', from_date), ('create_date', '<', to_date)]
            if exec_record.state_ids or exec_record.region_ids:
                domain_filter.append(('region_id', 'in', region_lst))
                if len(region_lst) == 1:
                    domain_filter.append(('region_id', '=', region_lst[0]))
            exec_record.report_status = 'processing'
            sale_list_len = self.env['sale.order'].search_count(domain_filter)
            if sale_list_len < exec_record.batch_end:
                exec_record.batch_end = sale_list_len
            _logger.info(f"{sale_list_len} Sale Orders...... ")
            _logger.info(f"Batch start : {exec_record.batch_start} BatchEnd:{exec_record.batch_end}")
            obj = self.env["generate.csv.report"]
            sale_list = []
            for rec in exec_record.fields_to_export:
                sale_list.append(rec.field_name)

            write_func = obj.so_csv_report(self.env['sale.order'].search(domain_filter, order='create_date ASC')[
                                           exec_record.batch_start:exec_record.batch_end if exec_record.batch_end < sale_list_len else sale_list_len],
                                           exec_record.report_file_path,sale_list)
            if write_func['msg'] == 'completed':
                if exec_record.batch_end == sale_list_len:
                    exec_record.report_status = 'completed'
                    _logger.info(f"Sale Orders Report {exec_record.report_status}")

                    _logger.info(f"Batch start : {exec_record.batch_start} BatchEnd:{exec_record.batch_end}")
                    exec_record.process_end_date = (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
                    _logger.info(f"Processing Finished @{exec_record.process_end_date} ")

                update_batch_start = exec_record.batch_end
                update_batch_end = exec_record.batch_end + self.env.company.csv_fetch_batch_limit

                exec_record.batch_start = update_batch_start if update_batch_start < sale_list_len else sale_list_len
                exec_record.batch_end = update_batch_end if update_batch_end < sale_list_len else sale_list_len

            if exec_record.batch_start == sale_list_len:
                exec_record.report_status = 'completed'






    def utc_date_to_user_local(self, utc_date_to_convert):
        user_zone = tz.gettz(self.env.user.tz or pytz.utc)
        try:
            utc_date_to_convert = utc_date_to_convert.strftime('%Y-%m-%d %H:%M:%S')
            utc = datetime.strptime(str(utc_date_to_convert), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            utc_date_to_convert = utc_date_to_convert.strftime('%Y-%m-%d')
            utc = datetime.strptime(str(utc_date_to_convert), '%Y-%m-%d')
        user_local_date = utc.astimezone(user_zone)
        return user_local_date

    def date_to_utc(self, date_to_convert):
        utc_zone = tz.gettz('UTC')
        print(utc_zone)
        local = tz.gettz(self.env.user.tz or pytz.utc)
        try:
            date_to_convert = datetime.strptime(str(date_to_convert), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            date_to_convert = datetime.strptime(str(date_to_convert), '%Y-%m-%d')
        print(date_to_convert, 'date_to_convertdate_to_convertdate_to_convertdate_to_convert')
        date_to_convert = date_to_convert.replace(tzinfo=local)
        print(date_to_convert)
        utc_date = date_to_convert.astimezone(utc_zone)
        print(utc_date, 'utc_dateutc_dateutc_dateutc_dateutc_dateutc_dateutc_dateutc_date')
        return utc_date


    def delete_so_csv_reports(self):
        _logger.info(f"Delete Scheduler : Deleting Process Started")
        flush_date = date.today() - timedelta(days=3)
        record = self.search([('create_date', '<=', flush_date.strftime('%Y-%m-%d') + ' ' + '00:00:00')])
        if record:
            for rec in record:
                if os.path.exists(rec.report_file_path):
                    os.remove(rec.report_file_path)
                _logger.info(f"Delete Scheduler : Deleting 3 days Ago Records")
                rec.unlink()
        else:
            _logger.info(f"CSV Delete Scheduler : No Record found for Deleting ")
