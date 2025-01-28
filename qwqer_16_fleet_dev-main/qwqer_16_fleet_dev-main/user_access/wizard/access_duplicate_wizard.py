# -*- coding: utf-8 -*-

from odoo import fields, models


class UserDuplicateWizard(models.TransientModel):
    _name = 'user.access.duplicate.wizard'
    

    reference_user = fields.Many2one('res.users', required=True)
    
    def set_access_to_user_based_on_reference_user(self):
        """
            Method to copy access right to user based on reference user
        """
        if self.reference_user:
            active_model = self.env.context.get('active_model')
            if active_model and active_model == 'res.users':
                reference_group_ids = self.reference_user.groups_id
                       
                selected_users = self.env['res.users'].browse(self.env.context.get('active_ids'))
                for selected_user in selected_users:
                    selected_user.sudo().write({
                        'substate_id' : self.reference_user.substate_id,
                        'region_ids' : self.reference_user.region_ids,
                        'action_id' : self.reference_user.action_id,
                        'displayed_regions_ids' :  self.reference_user.displayed_regions_ids,
                        'region_id' : self.reference_user.region_id,
                        'state_id' : self.reference_user.state_id
                        })

                    if selected_user.groups_id:
                        selected_user.groups_id.sudo().write({'users' : [(3,selected_user.id)]})
                        
                    if reference_group_ids:
                        reference_group_ids.sudo().write({'users' : [(4,selected_user.id)]})
