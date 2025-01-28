import datetime as DT
from odoo import http
from odoo.http import request


class HelpDeskDashboard(http.Controller):
    """Website helpdesk dashboard"""

    def get_dashboard_values(self, days, region_id=None, company_ids=[]):
        """Helper function to generate dashboard values based on the number of days and optional region."""
        today = DT.date.today()
        start_date = today - DT.timedelta(days=days)

        def get_ticket_info(stage_id):
            """Helper function to retrieve ticket count and list of IDs based on stage, user, and region."""
            domain = [('stage_id', '=', stage_id), ('create_date', '>=', start_date), ("company_id", 'in', company_ids)]
            if region_id:
                domain.append(('region_id', '=', int(region_id)))
            if not request.env.user.has_group('qwqer_ticket_management.helpdesk_manager'):
                domain.append(('assigned_user', '=', request.env.user.id))
            tickets = request.env["help.ticket"].search(domain)
            return len(tickets), tickets.ids

        # Retrieve ticket counts and IDs for each stage
        stage_refs = [
            'ticket_stage_open',
            'ticket_stage_rates_given',
            'ticket_stage_rates_not_given',
            'ticket_stage_won',
            'ticket_stage_lost'
        ]
        stage_keys = ['new', 'in_progress', 'canceled', 'done', 'closed']

        dashboard_values = {
            key: get_ticket_info(request.env.ref(f'qwqer_ticket_management.{ref}').id)
            for key, ref in zip(stage_keys, stage_refs)
        }

        # Flatten the dictionary for the response format
        result = {key: value[0] for key, value in dashboard_values.items()}
        result.update({f"{key}_id": value[1] for key, value in dashboard_values.items()})
        return result

    @http.route(['/helpdesk_dashboard',
                 '/helpdesk_dashboard_week',
                 '/helpdesk_dashboard_month',
                 '/helpdesk_dashboard_year'],
                type='json', auth="public")
    def helpdesk_dashboard(self, **kwargs):
        """Helpdesk dashboard controller for different periods"""
        days_mapping = {
            '/helpdesk_dashboard': 0,
            '/helpdesk_dashboard_week': 7,
            '/helpdesk_dashboard_month': 30,
            '/helpdesk_dashboard_year': 360
        }
        days = days_mapping.get(request.httprequest.path, 0)
        region_id = kwargs.get('region_id')
        company_ids = kwargs.get('company_ids')
        return self.get_dashboard_values(days=days, region_id=region_id, company_ids=company_ids)
