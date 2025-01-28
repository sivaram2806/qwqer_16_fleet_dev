from odoo import api, fields, models


class HelpTeam(models.Model):
    """ This class represents a Helpdesk Team in the system, providing
     information about the team members, leader, and related project."""
    _name = 'help.team'
    _description = 'Ticket Management Team'

    name = fields.Char(string='Name', help='Name of the Helpdesk Team. It '
                                           'identify the helpdesk team')
    team_lead_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        help='Name of the Helpdesk Team Leader.',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'qwqer_ticket_management.helpdesk_team_leader').id)])
    member_ids = fields.Many2many(
        'res.users',
        string='Members',
        help='Users who belong to that Helpdesk Team',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'qwqer_ticket_management.helpdesk_user').id)])
    email = fields.Char(string='Email', help='Email')
    create_task = fields.Boolean(string="Create Task",
                                 help="Enable for allowing team to "
                                      "create tasks from tickets")

    @api.onchange('team_lead_id')
    def members_choose(self):
        """ This method is triggered when the Team Leader is changed. It
        updates the available team members based on the selected leader and
        filters out the leader from the list of potential members."""
        fetch_members = self.env['res.users'].search([])
        filtered_members = fetch_members.filtered(
            lambda x: x.id != self.team_lead_id.id)
        return {'domain': {'member_ids': [
            ('id', '=', filtered_members.ids),
            ('groups_id', 'in', self.env.ref('base.group_user').id),
            ('groups_id', 'not in', self.env.ref(
                'qwqer_ticket_management.helpdesk_team_leader').id)]}}
