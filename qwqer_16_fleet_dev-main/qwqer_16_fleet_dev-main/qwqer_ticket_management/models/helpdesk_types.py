from odoo import fields, models


class HelpdeskTypes(models.Model):
    """Its handle to control helpdesk ticket types """
    _name = 'helpdesk.types'
    _description = 'Helpdesk Types'

    name = fields.Char(string='Type', help='Types helpdesk tickets')
