from dateutil.relativedelta import relativedelta
from docutils.nodes import target

from odoo import api, fields, models
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _


class TargetConfiguration(models.Model):
    _name = "target.configuration"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Target Configuration"

    name = fields.Char(tracking=True)
    period = fields.Selection(string="Period", selection='_get_month_year_selection', tracking=True)
    country_id = fields.Many2one(comodel_name="res.country", string="Country",
                                 default=lambda self: self.env.company.country_id,
                                 help="Select the respective country")
    state_id = fields.Many2one('res.country.state', tracking=True)
    create_date = fields.Date(string="Create Date", default=lambda self: fields.Datetime.now(), tracking=True)
    target_list_ids = fields.One2many('salesperson.target.list', 'target_id', string='Target List', tracking=True)
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(TargetConfiguration, self).create(vals_list)
        date_obj = datetime.strptime(str(res.period), "%m-%Y")
        period_year = date_obj.year
        period_month = date_obj.strftime("%b")
        res.name = str(res.state_id.code) + "-" + period_month + "-" + str(period_year)
        return res

    @api.model
    def _get_month_year_selection(self):
        month_year_list = []
        current_year = datetime.now().year
        for year in range(current_year, current_year + 2):
            for month in range(1, 13):
                # To fetch the short month name
                month_name = datetime(year, month, 1).strftime('%b')
                month_year_list.append((f"{month:02d}-{year}", f"{month_name} {year}"))
        return month_year_list

    @api.constrains('state_id', 'period')
    def _check_target_list_unique(self):
        if self.state_id and self.period and self.company_id.id:
            target_config = self.env['target.configuration'].search([('state_id', '=', self.state_id.id),
                                                                     ('period', '=', self.period),
                                                                     ('company_id', '=', self.company_id.id)])
            if len(target_config) > 1:
                raise UserError(_("The Target for the given state and period already exists."))

    @api.onchange('period')
    def onchange_period(self):
        for rec in self:
            if rec.period:
                month_date = datetime.strptime(rec.period, '%m-%Y')
                from_date = month_date.replace(day=1)
                rec.from_date = from_date
                # Find the first day of the next month and subtract one day to get the last day of the current month
                next_month = from_date + relativedelta(months=1)
                to_date = next_month - relativedelta(days=1)
                rec.to_date = to_date

    @api.model
    def get_target_manager_email_to(self):
        created_user = self.user_id
        send_mail = ''
        if self.user_has_groups('sales_person_target.target_manager_all_access'):
            send_mail = created_user.email
        return send_mail

    def reminder_for_set_target_next_month(self):
        """ Reminder for set next month target """
        template_id = self.env.ref('sales_person_target.target_email_template_reminder')
        if template_id:
            template_id.send_mail(self.id, email_values=None, force_send=True)

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.target_list_ids:
            self.target_list_ids = [(5, 0, 0)]

    def write(self, vals):
        for rec in self:
            rec._log_target_updates(vals)
        return super().write(vals)

    def _log_target_updates(self, vals):
        for line in vals.get('target_list_ids') or []:
            if line[0] == 1 and line[2]:  # Update operation
                msg_list = []
                target_list = self.env['salesperson.target.list'].browse(line[1])
                salesperson_name = target_list.sales_person_id.name or 'None'
                region_name = target_list.region_id.name or 'None'
                for field, new_value in line[2].items():
                    field_obj = self.env['salesperson.target.list']._fields[field]
                    field_string = field_obj.string
                    current_value = getattr(target_list, field)

                    if field_obj.type == 'many2one':
                        current_value_name = current_value.name if current_value else 'None'
                        new_value_name = self.env[field_obj.comodel_name].browse(
                            new_value).name if new_value else 'None'

                        if field == 'region_id':
                            msg_list.append(
                                f'Region changed from {current_value_name} to {new_value_name} for Salesperson {salesperson_name}')
                        elif field == 'sales_person_id':
                            msg_list.append(
                                f'Salesperson changed from {current_value_name} to {new_value_name} for Region {region_name}')
                    else:
                        if field != 'sales_person_domain' and field != 'region_domain':
                            msg_list.append(
                                f'{field_string} changed from {current_value} to {new_value} (Region: {region_name}, Salesperson: {salesperson_name})')

                if msg_list:
                    self.message_post(body=", ".join(msg_list))

            elif line[0] == 0:
                if line[2]:
                    sale_person_id = line[2].get("sales_person_id")
                    region_id = line[2].get("region_id")
                    sale_person = self.env["hr.employee"].browse(sale_person_id)
                    region = self.env["sales.region"].browse(region_id)
                    msg = f'Sales Person {sale_person.name} added to Region {region.name} with a Target Revenue of {line[2].get("target_revenue")} and Collection Target of {line[2].get("collection_target")}.'
                    self.message_post(body=msg)

            elif line[0] == 2:
                target_list = self.env['salesperson.target.list'].browse(line[1])
                if target_list:
                    for lines in target_list:
                        msg = f'Sales Person {lines.sales_person_id.name} in Region {lines.region_id.name} has been removed from the list.'
                        self.message_post(body=msg)

    def get_last_target_for_state(self, state_id, company):
        last_target = self.env['target.configuration'].search([
            ('state_id', '=', state_id), ('company_id', '=', company.id)
        ], order='from_date desc', limit=1)
        return last_target

    def check_and_create_next_month_target(self):
        companies = self.env.companies
        for company in companies:
            today = datetime.today()
            from_date = today.date().replace(day=1)
            current_month = today.month
            current_year = today.year
            current_period = f'{current_month:02d}-{current_year}'
            next_month = from_date + relativedelta(months=1)
            to_date = next_month - relativedelta(days=1)
            state_ids = self.env['res.country.state'].search([("country_id", "=", company.country_id.id)]).ids
            for state_id in state_ids:
                last_target_record = self.get_last_target_for_state(state_id, company)
                if last_target_record and last_target_record.from_date:
                    if last_target_record.from_date < from_date:
                        self.env['target.configuration'].with_company(company.id).create(
                            {
                                'period': current_period,
                                'state_id': last_target_record.state_id.id,
                                'user_id': last_target_record.user_id.id,
                                'company_id': company.id,
                                'from_date': from_date,
                                'to_date': to_date,
                                'target_list_ids': [(0, 0,
                                                     {'sales_person_id': line.sales_person_id.id,
                                                      'region_id': line.region_id.id,
                                                      'target_revenue': line.target_revenue,
                                                      'achieved_revenue': line.achieved_revenue,
                                                      'achieved_revenue_percentage': line.achieved_revenue,
                                                      'collection_target': line.collection_target,
                                                      'achieved_collection': line.achieved_collection,
                                                      'achieved_collection_percentage': line.achieved_collection_percentage,
                                                      })
                                                    for line in last_target_record.target_list_ids
                                                    ],
                            })
