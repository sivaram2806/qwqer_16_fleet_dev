import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
]
RATING = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'Extreme High')
]


class HelpTicket(models.Model):
    """This model represents the Helpdesk Ticket, which allows users to raise
    tickets related to products, services or any other issues. Each ticket has a
    name, customer information, description, team responsible for handling
    requests, associated project, priority level, stage, cost per hour, service
    product, start and end dates, and related tasks and invoices."""

    _name = 'help.ticket'
    _description = 'Fleet Enquiry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Enquiry Number', default=lambda self: _('New'),
                       help='The name of the fleet enquiry. By default, a new '
                            'unique sequence number is assigned to each '
                            'fleet enquiry, unless a name is provided.',
                       index=True,
                       readonly=True)
    active = fields.Boolean(default=True, help='Active', string='Active')
    customer_id = fields.Many2one('res.partner',
                                  string='Customer Name',
                                  help='Select the Customer Name', tracking=True,
                                domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    customer_name = fields.Char(string='Customer Name', tracking=True)
    is_existing_customer = fields.Boolean(string='Is Existing Customer', default=False, tracking=True)
    opportunity_name = fields.Text(string='Opportunity Name', required=True,
                          help='Opportunity Name', tracking=True)
    description = fields.Text(string='Description',
                              help='Issue Description')
    email = fields.Char(string='Email', help='Email of the User.', tracking=True)
    phone = fields.Char(string='Phone', help='Phone Number of the user', tracking=True)
    region_id = fields.Many2one('sales.region', string='Region', tracking=True)
    team_id = fields.Many2one('help.team', string='Helpdesk Team',
                              help='The helpdesk team responsible for '
                                   'handling requests related to this '
                                   'record')
    priority = fields.Selection(PRIORITIES,
                                default='1',
                                help='Set the priority level',
                                string='Priority', tracking=True)
    stage_id = fields.Many2one('ticket.stage', string='Stage',
                               default=lambda self: self.env[
                                   'ticket.stage'].search(
                                   [('name', '=', 'Open')], limit=1).id,
                               tracking=True,
                               group_expand='_read_group_stage_ids',
                               help='Stages of the Enquiry.')
    user_id = fields.Many2one('res.users',
                              default=lambda self: self.env.user,
                              check_company=True,
                              index=True, tracking=True,
                              help='Login User')
    create_date = fields.Datetime(string='Enquiry Date and Time', readonly="True", help='Created date of'
                                                               'the Enquiry')
    start_date = fields.Datetime(string='Start Date', help='Start Date of the '
                                                           'Enquiry')
    end_date = fields.Datetime(string='End Date', help='End Date of the Enquiry')
    color = fields.Integer(string="Color", help='Color')
    replied_date = fields.Datetime(string='Replied date',
                                   help='Replied Date of the Enquiry', tracking=True)
    last_update_date = fields.Datetime(string='Last Update Date',
                                       readonly='True',
                                       default=lambda self: self.write_date,
                                       help='Last Update Date of Enquiry')
    ticket_type = fields.Many2one('helpdesk.types',
                                  string='Enquiry Type', help='Enquiry Type')
    team_head = fields.Many2one('res.users', string='Team Leader',
                                compute='_compute_team_head',
                                help='Team Leader Name')
    assigned_user = fields.Many2one(
        'res.users',
        string='Assigned User',
        domain=lambda self: [('groups_id', 'in', self.env.ref(
            'qwqer_ticket_management.helpdesk_user').id)],
        default=lambda self: self.env.user,
        help='Choose the Assigned User Name', tracking=True)
    category_id = fields.Many2one('helpdesk.categories',
                                  help='Choose the Category', string='Category')
    tags = fields.Many2many('helpdesk.tag', help='Choose the Tags',
                            string='Tag')
    assign_user = fields.Boolean(string='Assigned User', help='Assign User')
    attachment_ids = fields.One2many('ir.attachment',
                                     'res_id',
                                     help='Attachment Line',
                                     string='Attachment')
    enquiry_generated_by_id = fields.Many2one('res.users', required='True', string='Enquiry Generated By',
                                              default=lambda self:self.env.user, tracking=True)
    no_of_vehicles = fields.Integer(string='No. Of Vehicles', required='True', tracking=True)
    rate_type = fields.Selection([('lane_wise','Lane Wise'),('tonnage_wise','Tonnage Wise')], string='Rate Type',
                                 required='True', tracking=True)
    source_id = fields.Many2one('res.state.city', required='True', string='Source', tracking=True)
    destination_id = fields.Many2one('res.state.city', required='True', string='Destination', tracking=True)
    tonnage = fields.Float(string='Tonnage', tracking=True)
    vehicle_type_id = fields.Many2one('vehicle.vehicle.type', required='True', tracking=True, string='Type of Vehicle')
    vehicle_type_comment = fields.Char(string='Vehicle Type Comments', tracking=True)
    target_rate = fields.Float(string='Target Rate', tracking=True)
    vendor_rate = fields.Float(string='Vendor Rate', tracking=True)
    traffic_team_comment = fields.Text(string='Traffic Team Comment', tracking=True)
    rate_date_time = fields.Datetime(string="Rate Update Date and Time", readonly="True", tracking=True)
    vendor_rate_by_id = fields.Many2one('res.users', string='Vendor Rate Given By', tracking=True)
    is_rate_given = fields.Boolean('Is rate given', default=False)
    is_won_lost = fields.Boolean('Is Won/Lost Stage', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.onchange('team_id', 'team_head')
    def team_leader_domain(self):
        """Update the domain for the assigned user based on the selected team.

        This onchange method is triggered when the helpdesk team or team leader
        is changed. It updates the domain for the assigned user field to include
        only the members of the selected team."""
        teams = []
        for rec in self.team_id.member_ids:
            teams.append(rec.id)
        return {'domain': {'assigned_user': [('id', 'in', teams)]}}

    @api.depends('team_id')
    def _compute_team_head(self):
        """Compute the team head based on the selected team.

        This method is triggered when the helpdesk team is changed. It computes
        and updates the team head field based on the team's lead.
       """
        self.team_head = self.team_id.team_lead_id.id

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        """Handle changes in ticket stage, update relevant dates, and send an email if necessary."""
        self.last_update_date = fields.Datetime.now()

        if self.stage_id.starting_stage:
            self.start_date = fields.Datetime.now()

        if self.stage_id.closing_stage or self.stage_id.cancel_stage:
            self.end_date = fields.Datetime.now()

        if self.stage_id.template_id:
            self.stage_id.template_id.send_mail(self.id, force_send=True)

        stage_refs = {
            'not_given': self.env.ref('qwqer_ticket_management.ticket_stage_rates_not_given'),
            'given': self.env.ref('qwqer_ticket_management.ticket_stage_rates_given'),
            'open': self.env.ref('qwqer_ticket_management.ticket_stage_open'),
            'won': self.env.ref('qwqer_ticket_management.ticket_stage_won'),
            'lost': self.env.ref('qwqer_ticket_management.ticket_stage_lost')
        }

        for rec in self:
            if (rec.vendor_rate == 0.0 and
                    rec.stage_id.id not in [stage_refs['open'].id, stage_refs['not_given'].id, stage_refs['lost'].id] and
                    rec.create_date):
                raise UserError('You are not allowed to change the stage since Vendor Rate is not given.')

            if rec.stage_id.id == stage_refs['not_given'].id and rec.vendor_rate > 0.0 and rec.stage_id.id != stage_refs['lost'].id:
                raise UserError('You are not allowed to change the stage since Vendor Rate is already given.')

            if rec._origin.stage_id.id in [stage_refs['won'].id] and rec.stage_id.id in [stage_refs['open'].id,
                                                                                     stage_refs['not_given'].id,
                                                                                     stage_refs['lost'].id,
                                                                                     stage_refs['given'].id]:
                raise UserError('You are not allowed to change the stage since Enquiry is in Won stage.')
            if rec._origin.stage_id.id in [stage_refs['lost'].id] and rec.stage_id.id in [stage_refs['won'].id,
                                                                                     stage_refs['not_given'].id,
                                                                                     stage_refs['given'].id]:
                raise UserError('You are not allowed to change the stage since Enquiry is in Lost stage. '
                                'Enquiry can only moved to Open stage.')

            if rec.stage_id.id in [stage_refs['won'].id, stage_refs['lost'].id]:
                rec.is_won_lost = False
            else:
                rec.is_won_lost = True

    @api.onchange('vendor_rate')
    def onchange_rate_given_time(self):
        """
        Onchange of the Vendor Rate
        """
        rates_given_stage = self.env.ref(
                'qwqer_ticket_management.ticket_stage_rates_given')
        for rec in self:
            if rec.vendor_rate > 0.0:
                rec.rate_date_time = datetime.now()
                rec.is_rate_given = True
                rec.stage_id = rates_given_stage.id
                rec.vendor_rate_by_id = rec.env.user.id
            else:
                rec.is_rate_given = False

    def assign_to_teamleader(self):
        """Assign the ticket to the team leader and send a notification.

        This function checks if a helpdesk team is selected and assigns the
        team leader to the ticket. It then sends a notification email to the
        team leader."""
        if self.team_id:
            self.team_head = self.team_id.team_lead_id.id
            mail_template = self.env.ref(
                'qwqer_ticket_management.'
                'mail_template_odoo_website_helpdesk_assign')
            mail_template.sudo().write({
                'email_to': self.team_head.email,
                'opportunity_name': self.name
            })
            mail_template.sudo().send_mail(self.id, force_send=True)
        else:
            raise ValidationError("Please choose a Helpdesk Team")

    def _default_show_create_task(self):
        """Get the default value for the 'show_create_task' field.

        This method retrieves the default value for the 'show_create_task'
        field from the configuration settings."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'qwqer_ticket_management.show_create_task')

    show_create_task = fields.Boolean(string="Create Task",
                                      default=_default_show_create_task,
                                      compute='_compute_show_create_task',
                                      help='Determines whether the Create Task'
                                           ' button should be shown for this '
                                           'ticket.')
    create_task = fields.Boolean(string="Create Task", readonly=False,
                                 related='team_id.create_task',
                                 store=True,
                                 help='Defines if a task should be created when'
                                      ' this ticket is created.')

    def _default_show_category(self):
        """Its display the default category"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'qwqer_ticket_management.show_category')

    show_category = fields.Boolean(default=_default_show_category,
                                   compute='_compute_show_category',
                                   help='Display the default category')
    customer_rating = fields.Selection(RATING, default='0', readonly=True,
                                       string='Customer Rating',
                                       help='Display the customer rating.')

    review = fields.Char(string='Review', readonly=True,
                         help='Customer review of the Enquiry.')
    kanban_state = fields.Selection([
        ('normal', 'Ready'),
        ('done', 'In Progress'),
        ('blocked', 'Blocked'), ], readonly='True', default='normal')

    def _compute_show_category(self):
        """Compute show category"""
        show_category = self._default_show_category()
        for rec in self:
            rec.show_category = show_category

    def _compute_show_create_task(self):
        """Compute the value of the 'show_create_task' field for each record in
        the current recordset."""
        show_create_task = self._default_show_create_task()
        for record in self:
            record.show_create_task = show_create_task

    def rates_not_given_stage_update(self):
        date_time_now = fields.Datetime.now() - relativedelta(hours=48)
        stage_open_id = self.env.ref(
                'qwqer_ticket_management.ticket_stage_open').id
        records = self.env['help.ticket'].search([('vendor_rate', '=', 0), ('stage_id', '=', stage_open_id),
                                                  ('create_date', '<=', date_time_now)])
        rates_not_given_stage = self.env.ref(
                'qwqer_ticket_management.ticket_stage_rates_not_given').id
        records.write({"stage_id": rates_not_given_stage})

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """
        Return the available stages for grouping.

        This static method is used to provide the available stages for
        grouping when displaying records in a grouped view.

        """
        stage_ids = self.env['ticket.stage'].search([])
        return stage_ids

    @api.model
    def create(self, vals_list):
        """Create a new helpdesk ticket.
        This method is called when creating a new helpdesk ticket. It
        generates a unique name for the ticket using a sequence if no
        name is provided.
        """
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'help.ticket')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'help.ticket')], limit=1)
            new_sequence = sequence.sudo().copy()
            new_sequence.company_id = company_id
            vals_list['name'] = new_sequence.next_by_id()
        else:
            vals_list['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code('help.ticket')
        if vals_list.get('rate_type') == 'tonnage_wise' and not vals_list.get('tonnage') and not isinstance(vals_list.get('tonnage'), float):
            raise ValidationError('Tonnage is a required field since Rate Type is selected as Tonnage Wise.')
        res = super().create(vals_list)
        return res

    def write(self, vals):
        for rec in self:
            if vals:
                vals['last_update_date'] = fields.Datetime.now()
                if (vals.get('rate_type') and vals.get('rate_type') == 'tonnage_wise') or (not vals.get("rate_type") and rec.rate_type == "tonnage_wise"):
                    if ("tonnage" in vals and not vals.get("tonnage")) or (not vals.get("tonnage") and not rec.tonnage):
                        raise ValidationError('Tonnage is a required field since Rate Type is selected as Tonnage Wise.')
        return super().write(vals)

    @api.onchange('customer_id')
    def customer_name_save(self):
        for rec in self:
            if rec.customer_id:
                rec.customer_name = rec.customer_id.name

    def action_send_reply(self):
        """Compose and send a reply to the customer.
        This function opens a window for composing and sending a reply to
        the customer. It uses the configured email template for replies.
       """
        template_id = self.env['ir.config_parameter'].sudo().get_param(
            'qwqer_ticket_management.reply_template_id'
        )
        template_id = self.env['mail.template'].browse(int(template_id))
        if template_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'mail',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'target': 'new',
                'views': [[False, 'form']],
                'context': {
                    'default_model': 'help.ticket',
                    'default_res_id': self.id,
                    'default_template_id': template_id.id
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'mail',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_model': 'help.ticket',
                'default_res_id': self.id,
            }
        }
