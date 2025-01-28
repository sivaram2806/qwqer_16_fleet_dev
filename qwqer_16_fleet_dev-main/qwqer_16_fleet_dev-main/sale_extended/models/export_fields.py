from odoo import models, fields, api, _


class ExportCsvFields(models.Model):
    _name = 'export.csv.fields'

    name = fields.Char(string='Name')
    field_name = fields.Char(string='Field Name')
    is_default = fields.Boolean(string="Is Default")
