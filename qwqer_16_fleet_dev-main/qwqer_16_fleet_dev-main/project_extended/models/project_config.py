from odoo import api, fields, models, _

class Source(models.Model):

    _name = "sys.source"
    _description = "System Sources"

    name = fields.Char(string='Name')

class Category(models.Model):

    _name = "sys.category"
    _description = "System categories"

    name = fields.Char(string='Issue Category *')
    project_id = fields.Many2one('project.project', string='Project')

class CauseConfigSettings(models.Model):
    _name = 'cause.config.settings'
    _description = 'Cause Configuration Settings'
    _rec_name = 'cause_name'

    cause_name = fields.Char(string="Cause", required=True)
