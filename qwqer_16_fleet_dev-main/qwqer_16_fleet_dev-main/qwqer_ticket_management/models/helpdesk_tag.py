from odoo import fields, models


class HelpdeskTag(models.Model):
    """ Its handle to control the helpdesk ticket tags"""
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'

    name = fields.Char(string='Tag', help='Choose the tags')
