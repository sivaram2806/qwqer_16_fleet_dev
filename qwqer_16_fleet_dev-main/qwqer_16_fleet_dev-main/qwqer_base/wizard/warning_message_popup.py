from odoo import api, fields, models 

class hr_wizard(models.TransientModel):

    _name = 'warning.message.popup'

    _description = 'Message Popup Wizard'

    message = fields.Text(string="", readonly=True, store=True)