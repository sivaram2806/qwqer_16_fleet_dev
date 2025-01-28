from odoo import fields, models
from lxml import etree


class VehicleContract(models.Model):
    """extended the model to add ftl field and changes"""
    _inherit = 'vehicle.contract'

    wo_ids = fields.Many2many(comodel_name='work.order', inverse_name='contract_id', string='Work Orders', store=True)
    wo_count = fields.Integer(compute='_compute_wo_count')

    def get_view(self, view_id=None, view_type='form', **options):
        """extended to hide work order smart button for non ftl contract"""
        result = super().get_view(view_id, view_type, **options)
        context = self._context
        if view_type == 'form':
            if context.get('default_contract_classification') and context.get(
                    'default_contract_classification') != 'ftl':
                # hiding wo_ids field  and smart button on contrat other than ftl contrat
                doc = etree.XML(result['arch'])
                for node in doc.xpath("//field[@name='wo_ids']"):
                    node.getparent().remove(node)
                for button in doc.xpath("//button[@name='get_work_orders']"):
                    button.getparent().remove(button)
                result['arch'] = etree.tostring(doc)
        return result

    def _compute_wo_count(self):
        """compute work order count """
        wo_len = len(self.wo_ids.ids)
        self.wo_count = wo_len

    def get_work_orders(self):
        """render work order view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Work Orders',
            'view_mode': 'tree,form',
            'res_model': 'work.order',
            'domain': [('id', 'in', self.wo_ids.ids)],
            'context': "{'create': False}"
        }
