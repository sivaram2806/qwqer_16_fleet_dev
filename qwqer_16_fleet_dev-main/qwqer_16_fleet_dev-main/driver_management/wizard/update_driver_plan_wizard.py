from odoo import api, fields, models, _


class UpdateDriverPlanWizard(models.TransientModel):
    _name = "update.driver.plan.wizard"
    _description = "Update Driver Plan Wizard"

    region_id = fields.Many2one('sales.region', readonly=True)
    plan_id = fields.Many2one('driver.payout.plans')
    employee_ids = fields.Many2many('hr.employee', 'emp_plan_wiz_rel', 'wiz_id', 'emp_id', string="Drivers")
    payout_type = fields.Selection([
        ('week', 'Weekly'),
        ('month', 'Monthly'),
    ], string='Payout Type')
    action_type = fields.Selection([
        ('update', 'Update Plan'),
        ('remove', 'Remove Plan'),
    ], string='Action')

    @api.model
    def default_get(self, fields):
        res = super(UpdateDriverPlanWizard, self).default_get(fields)
        if self._context.get('active_model') == 'driver.payout.plans' and self._context.get('active_id', False):
            plan_id = self.env['driver.payout.plans'].browse(self._context.get("active_id"))
            if plan_id and plan_id.region_id:
                res.update({'plan_id': plan_id.id,
                            'region_id': plan_id.region_id and plan_id.region_id.id or False,
                            })
        return res

    @api.onchange('plan_id')
    def onchange_plan_id(self):
        for rec in self:
            if rec.plan_id:
                rec.region_id = rec.plan_id.region_id.id
                if rec.action_type == 'update':
                    data_ids = self.env['hr.employee'].search(
                        [('region_id', '=', rec.region_id.id), ('driver_uid', '!=', False)])
                else:
                    data_ids = self.env['hr.employee'].search(
                        [('region_id', '=', rec.region_id.id), ('plan_detail_id', '=', rec.plan_id.id),
                         ('driver_uid', '!=', False)])
                if data_ids:
                    return {'domain':
                                {'employee_ids': [('id', 'in', data_ids.ids)]}, }
                else:
                    return {'domain':
                                {'employee_ids': [('id', 'in', [])]}, }

            else:
                rec.employee_ids = False
                rec.region_id = False

    def action_submit(self):
        for rec in self:
            if rec.plan_id and rec.employee_ids:
                for line in rec.employee_ids:
                    line.plan_detail_id = rec.plan_id.id
                    line.payout_type = rec.payout_type

    def action_remove(self):
        for rec in self:
            if rec.plan_id and rec.employee_ids:
                for line in rec.employee_ids:
                    line.plan_detail_id = False
                    line.payout_type = False