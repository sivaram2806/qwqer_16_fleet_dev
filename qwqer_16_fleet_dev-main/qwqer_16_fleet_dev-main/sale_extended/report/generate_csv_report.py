# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
import csv


class SaleOrderCsvReportExport(models.AbstractModel):
    _name = "generate.csv.report"


    def generate_csv_report_file(self, report_file_path,report_fields):
        heading = []
        for field in report_fields:
            heading.append(field.name)
        with open(report_file_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(heading)

    def so_csv_report(self, sale_orders, report_file_path,sale_list):

        with open(report_file_path, 'a+', newline='') as csv_file:
            writer = csv.writer(csv_file)

            for sale in sale_orders:
                csv_list=[]
                for field_name in sale_list:
                    try:
                        field = sale._fields[field_name]
                        value = getattr(sale,field_name)
                        if field.type == 'datetime':
                            value = value.strftime('%Y-%m-%d %H:%M:%S') if value else ''  # Format datetime
                        elif field.type == 'many2one':
                            value = value.name if value else ''
                    except Exception as e:
                        print(e)
                        value = 'field not found'
                    csv_list.append(value)
                writer.writerow(csv_list)
            return {'msg': 'completed'}
