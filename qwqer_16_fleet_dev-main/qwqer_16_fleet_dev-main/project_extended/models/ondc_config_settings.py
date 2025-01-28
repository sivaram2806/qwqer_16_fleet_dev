from odoo import api, fields, models, _

class OndcProjectConfigSettings(models.Model):
    _name = 'ondc.project.config.settings'
    _description = 'Ondc Project Configuration Settings'
    _rec_name = 'project_name'

    def _group_gro_user_domain(self):
        """We are taking the users with gro groups for giving domain for gros field"""
        group = self.env.ref('project_extended.group_gro_user', raise_if_not_found=False)
        return [('groups_id', 'in', group.ids)] if group else []

    project_name = fields.Many2one('project.project', string="Project")
    source_name = fields.Many2one('sys.source', string="Source")
    gro_user_id = fields.Many2one('res.users', string="Default GRO User", domain=_group_gro_user_domain)


class OndcSubcategoryConfigSettings(models.Model):
    _name = 'ondc.subcategory.config.settings'
    _description = 'Ondc Subcategory Configuration Settings'
    _rec_name = 'subcategory_name'

    subcategory_name = fields.Char(string="Subcategory")
    cause_id = fields.Many2one('cause.config.settings', string='Cause')
