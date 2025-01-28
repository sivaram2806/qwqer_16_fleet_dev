# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResUsers(models.Model):
    """ The model res_users is inherited to make modifications """
    _inherit = 'res.users'
    # Field to assign substate(s) to user
    substate_id = fields.Many2many(comodel_name='sales.zone', string='Sales Zones')
    # Field which decides records of whichever regions shall be visible for the user.
    displayed_regions_ids = fields.Many2many('sales.region', 'displayed_regions', string='Displayed Regions')
    region_ids = fields.Many2many('sales.region', string='Associated Region')
    manager_user_id = fields.Many2one('res.users', string="Subordinate Manager User ID", index=True)
    subordinate_count = fields.Integer('# Subordinates', help='Number of Subordinates under current user',
                                  compute='_compute_subordinate_count')
    #TODO parent, child in same model is not working
    # subordinate_emp_user_ids = fields.One2many('res.users', 'manager_user_id', string='Subordinates')  # V13_field: employee_relation_ids

    def _compute_subordinate_count(self):
        for user in self:
            user.subordinate_count = len(self.env['res.users'].search([('manager_user_id', '=', user.id)]))

    """ Onchange function to assign regions of user's substates if present.
     Otherwise, regions from region field is taken."""

    @api.onchange('substate_id')
    def onchange_substate_id(self):
        for rec in self:

            # List of assigned substates is taken.
            substates = list(rec.substate_id.ids)

            # If list is not empty, regions under those substates are overwritten to displayed_regions_ids
            if substates:
                regions = list(rec.env['sales.region'].search([('sale_zone_id.id', 'in', substates)]).ids)
                rec.write({'displayed_regions_ids': [(6, 0, regions)]})
            # If no substate is assigned, regions currently in region field are taken.
            else:
                # Field displayed_regions_ids is emptied first.
                rec.write({'displayed_regions_ids': [(5, 0, 0)]})
                # Regions currently in region field are assigned to displayed_regions_ids.
                regions = list(rec.region_ids.ids)
                rec.write({'displayed_regions_ids': [(6, 0, regions)]})


    """Onchange function to update displayed_regions_ids with changes in region field.
    This affects only when the substate field is empty."""
    @api.onchange('region_ids')
    def onchange_region_ids(self):

        substates = list(self.substate_id.ids)
        if not substates:
            regions = list(self.region_ids.ids)
            self.write({'displayed_regions_ids': [(6, 0, regions)]})

    def action_show_subordinates(self):
        self.ensure_one()
        return {
            'name': _('Subordinates'),
            'view_mode': 'tree,form',
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'delete': False},
            'domain': [('manager_user_id', '=', self.id)],
            'target': 'current',
        }
