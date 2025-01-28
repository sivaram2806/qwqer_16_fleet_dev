from odoo import api, fields, models, tools, _, SUPERUSER_ID
from lxml import etree


class DriverPayoutPlanChangeWizard(models.TransientModel):
    _name = 'driver.payout.plan.change.wizard'

    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)

        doc = etree.XML(res['arch'])
        if view_type == 'form':
            if self.env.context['already_set_plan'] and self.env.context['region']:
                node = doc.xpath("//div/p")[0]
                message = (f"{self.env.context['already_set_plan']}is already set as default DE pricing plan "
                           f"for the region {self.env.context['region']}."
                           f"Confirm if you want to change it ?")
                node.text = message
        res['arch'] = etree.tostring(doc)
        return res

    def change_driver_payout_plan(self):
        active_id = self.env['driver.payout.plans'].browse(self.env.context.get('active_id'))
        default_driver_payout_plan = active_id.region_id.sudo().default_driver_payout_plan or None
        default_driver_payout_plan.sudo().is_default_region_plan = False
        active_id.region_id.sudo().default_driver_payout_plan = active_id.id
        active_id.is_default_region_plan = True
