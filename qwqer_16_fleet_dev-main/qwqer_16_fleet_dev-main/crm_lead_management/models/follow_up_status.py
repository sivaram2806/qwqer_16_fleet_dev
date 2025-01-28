from odoo import models, api, fields, _
from lxml import etree


class FollowUpStatus(models.Model):
    _inherit = 'mail.activity.type'


    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    def get_view(self, view_id=None, view_type='form', **options):
        res = super(FollowUpStatus, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])

        if not self.env.user.has_group('sales_team.group_sale_manager'):
            if view_type == 'tree':
                for node in doc.xpath("//tree"):
                    node.set('create', "0")
                    node.set("delete", "0")
                    node.set("edit", "0")
            if view_type == 'form':
                for node in doc.xpath("//form"):
                    node.set('create', "0")
                    node.set("delete", "0")
                    node.set("edit", "0")

        res['arch'] = etree.tostring(doc)
        return res

