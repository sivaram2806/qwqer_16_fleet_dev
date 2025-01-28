# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResStateCity(models.Model):
    _name = 'res.state.city'
    _description = 'City'
    _rec_name = 'name'
    _order = 'name asc'

    country_id = fields.Many2one(related='state_id.country_id')
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    name = fields.Char(string='City Name', required=True,
                       help='City in a STATE')

    normalized_name = fields.Char(compute='_compute_normalized_name', store=True)

    @api.depends('name')
    def _compute_normalized_name(self):
        for record in self:
            record.normalized_name = ''.join(record.name.split()).lower()

    @api.constrains('normalized_name', 'state_id')
    def _check_unique_normalized_name(self):
        for record in self:
            existing_rec = self.search([('id', '!=', record.id), ('state_id', '=', record.state_id.id),
                                        ('normalized_name', '=', record.normalized_name)])
            if existing_rec:
                raise ValidationError("The name must be unique within state, ignoring case and whitespaces.")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if self.env.context.get('state_id'):
            args = expression.AND([args, [('state_id', '=', self.env.context.get('state_id'))]])

        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|',('name', operator, name), ('state_id.name', operator, name), ('state_id.code', operator, name)]

        return self._search(expression.AND([domain, args]),
                            limit=limit, access_rights_uid=name_get_uid) or []

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name, record.state_id.code)))
        return result
