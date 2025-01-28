# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class SaleOrderCsvReportExportWizard(models.Model):
    _name = 'sale.order.csv.report.export.wizard'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    state_ids = fields.Many2many(comodel_name='res.country.state', string="State")
    region_ids = fields.Many2many(comodel_name='sales.region', string="Region")
    fields_to_export = fields.Many2many(
        comodel_name="export.csv.fields", string='Fields to Export')

    @api.onchange('from_date')
    def _onchange_from_date(self):
        if self.to_date and self.to_date < self.from_date:
            self.reset_fields()
            self.display_warning()

    @api.onchange('to_date')
    def _onchange_to_date(self):
        if self.from_date:
            if self.to_date and self.to_date < self.from_date:
                self.reset_fields()
                self.display_warning()

    def reset_fields(self):
        self.from_date = False
        self.to_date = False

    def display_warning(self):
        warning_message = _("Enter valid Date Range")
        raise UserError(warning_message)

    @api.onchange('state_ids')
    def onchange_state(self):
        state_ids = self.state_ids.ids
        for wiz in self:
            if not wiz.state_ids:
                state_ids = self.env['res.country.state'].search([]).ids
            return {'domain': {'region_ids': [('state_id', 'in', state_ids)]}}

    @api.onchange('region_ids')
    def onchange_region(self):
        region_ids = self.region_ids.ids
        for wiz in self:
            if not wiz.region_ids:
                region_ids = self.env['sales.region'].search([]).ids
            return {'domain': {'state_ids': [('regions_ids', 'in', region_ids)]}}


    @api.model
    def default_get(self, fields):
        res = super(SaleOrderCsvReportExportWizard, self).default_get(fields)
        visible_fields = self.env['export.csv.fields'].search([('is_default','=',True)]).ids
        res['fields_to_export'] = [(6, 0, visible_fields)]
        return res

    def export_csv_sale_order(self):
        vals = {"from_date": self.from_date, "to_date": self.to_date}
        if self.state_ids:
            vals["state_ids"] = self.state_ids
        if self.region_ids:
            vals["region_ids"] = self.region_ids
        if self.fields_to_export:
            vals["fields_to_export"] = self.fields_to_export


        csv_batch_limit = self.env.company.csv_fetch_batch_limit
        csv_file_path = self.env.company.report_download_file_path
        module_name = self.env.company.path
        if not csv_batch_limit and not csv_file_path:
            raise UserError('Batch limit or File Path Not Found')
        file_date = self.from_date.strftime('%Y-%m-%d') + '_' + self.to_date.strftime('%Y-%m-%d')

        vals["report_file_path"] = str(f'{csv_file_path}/{file_date}_sale_order{datetime.today()}.csv')
        # generating an empty csv report
        obj = self.env["generate.csv.report"]
        obj.generate_csv_report_file(vals["report_file_path"],self.fields_to_export)
        full_path = vals["report_file_path"]
        custom_addons_dir = str(module_name)
        index = full_path.find(custom_addons_dir)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', False)
        relative_path = full_path[index + len(custom_addons_dir):]
        vals["file"] = str(f'{base_url}/{relative_path}')
        self.env["so.csv.report"].create(vals)
        return {
            'name': 'Sale Order Export',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'so.csv.report',
            'context': {'tree_view_ref': 'sale_extended.so_csv_report_export_view', 'create': False, 'edit': False,
                        },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


