import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'


    order_line_ids = fields.Many2many(comodel_name='sale.order', string='Order Lines')
    consolidated_invoice_id = fields.Many2one(comodel_name='consolidate.sale.invoice',string="Consolidated Invoice")
    driver_id = fields.Many2one(comodel_name='hr.employee', string='Driver ID')
    driver_uid = fields.Char(related='driver_id.driver_uid',string='Driver ID',store=True)
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone')
    order_id = fields.Char(string='Order ID')
    line_count = fields.Float(compute='_get_line_count', store=True)
    selling_partner_id = fields.Many2one('res.partner',string="Sold By")

    def button_cancel(self):
        for move in self:
            if 'from_api' in self._context.keys() and self._context['from_api'] == True:
                reconciled_invoice = move._get_all_reconciled_invoice_partials()
                move_lines = self.env["account.move.line"].search([("id", "in", [x["aml_id"] for x in reconciled_invoice])])
                for aml in move_lines:
                    aml.move_id.payment_id.action_draft()
                    aml.move_id.payment_id.action_cancel()
        return super(AccountMove, self).button_cancel()

    def _get_line_count(self):
        for rec in self:
            rec.line_count = len(rec.consolidated_invoice_id.order_ids.ids)

    def button_draft(self):
        if self.consolidated_invoice_id and self.state == 'cancel':
            raise UserError(_("Reset to draft is restricted in cancelled consolidated invoice. Please create a new consolidated invoice"))
        else:
            res = super().button_draft()
            if self.consolidated_invoice_id:
                self.consolidated_invoice_id.order_ids.invoice_status = "invoiced"
            if self.order_line_ids:
                self.order_line_ids.invoice_status = "invoiced"
            return res

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.consolidated_invoice_id:
            self.consolidated_invoice_id.order_ids.invoice_status = "invoiced"
        return res

    def button_draft(self):
        if self.consolidated_invoice_id and self.state == 'cancel':
            raise UserError(_("Reset to draft is restricted in cancelled consolidated invoice. Please create a new consolidated invoice"))
        else:
            res = super().button_draft()
            if self.consolidated_invoice_id:
                self.consolidated_invoice_id.order_ids.invoice_status = "invoiced"
            if self.order_line_ids:
                self.order_line_ids.invoice_status = "invoiced"
            return res

    def update_sale_order_status(self):
        for inv in self:
            if inv.consolidated_invoice_id:
                for rec in inv.consolidated_invoice_id.order_ids:
                    if rec.invoice_status == "to invoice":
                        rec.invoice_status = "invoiced"
            if inv.order_line_ids:
                for rec in inv.order_line_ids:
                    if rec.invoice_status == "to invoice":
                        rec.invoice_status = "invoiced"

    def _manage_customer_balance(self, partner):
        """Handle customer balance creation if not exists."""
        try:
            customer_balance = self.env['application.customer.balance'].search(
                [('partner_id', '=', partner.id)], limit=1
            )
            if not customer_balance:
                self.env['application.customer.balance'].create({
                    'partner_id': partner.id,
                    'time_balance_update': fields.datetime.now(),
                    'cus_id': partner.customer_ref_key,
                })
        except Exception as e:
            _logger.error("Error in Customer Balance Management: %s", str(e))

    def check_data_invoice_post(self, account_move, move_line):
        cf_conf = self.env['cash.free.configuration'].search([('payment_type', '=', 'inbound')], limit=1)
        if 'mode' in self._context.keys() and self._context['mode'] == 'online':
            if cf_conf.partner_id:
                move_line.partner_id = cf_conf.partner_id
        elif 'driver' in self._context.keys() and self._context['driver']:
            driver_id = self.env['hr.employee'].search([('id', '=', self._context['driver'])])
            if driver_id.related_partner_id.id:
                move_line.partner_id = driver_id.related_partner_id.id
        elif 'payin' in self._context.keys() and self._context['payin']:
            move_line.partner_id = cf_conf.partner_id
        return move_line

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        try:
            if vals.get('order_id') or vals.get('consolidated_invoice_id'):
                if (
                    res.partner_id and
                    res.partner_id.customer_rank > 0 and
                    res.partner_id.customer_type == 'b2b' and
                    res.partner_id.service_type_id.is_delivery_service
                ):
                    self._manage_customer_balance(res.partner_id)
        except Exception as e:
            _logger.error("Error in AccountMove Create: %s", str(e))
        return res

    def write(self, vals):
        def process_line(line, region_id):
            """Process individual lines for updates."""
            if line.debit > 0.00:
                rec.check_data_invoice_post(rec, line)

            if region_id:
                if line.move_id:
                    line.move_id.region_id = region_id
                line.region_id = region_id

            if line.move_id and line.move_id.region_id:
                line.region_id = line.move_id.region_id.id or False

            if line.partner_id:
                emp_pool = self.env['hr.employee'].search([('related_partner_id', '=', line.partner_id.id)], limit=1)
                if emp_pool:
                    line.driver_uid = emp_pool.driver_uid
                    line.driver_region_id = emp_pool.region_id.id

        region_id = self._context.get('region_id')
        for rec in self:
            if vals.get('state') in ('posted', 'cancel'):
                if (
                        rec.partner_id
                        and rec.partner_id.customer_rank > 0
                        and rec.partner_id.customer_type == 'b2b'
                        and rec.partner_id.service_type_id.is_delivery_service
                ):
                    self._manage_customer_balance(rec.partner_id)

            if vals.get('state') == 'posted':
                for line in rec.line_ids:
                    process_line(line, region_id)

        return super(AccountMove, self).write(vals)


    def action_update_order_sales_person(self):
        for inv in self:
            if inv.partner_id and inv.partner_id.order_sales_person:
                inv.sales_person_id = inv.partner_id.order_sales_person.id


    def action_update_customer_segment(self):
        for inv in self:
            if inv.segment_id and inv.partner_id.segment_id:
                inv.segment_id = inv.partner_id.segment_id.id

    def sync_tax_config_change(self):
        for rec in self:
            for line in rec.invoice_line_ids:
                line.price_unit += 0.01
            rec.invoice_line_ids._compute_totals()
        self.sudo()._compute_tax_totals()
        for rec in self:
            for line in rec.invoice_line_ids:
                line.price_unit -= 0.01
            rec.invoice_line_ids._compute_totals()
        self.sudo()._compute_tax_totals()
