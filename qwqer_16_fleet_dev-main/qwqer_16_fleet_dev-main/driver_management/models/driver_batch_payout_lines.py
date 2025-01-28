from odoo import api, fields, models, _
from ..models.driver_batch_payout import PAYMENT_STATUS

class DriverBatchPayoutLines(models.Model):

    _name = 'driver.batch.payout.lines'
    _description = 'Payout Lines'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    @api.model
    def _get_employee(self):
        if self.env.context.get('default_is_vendor_payout', False):
            employees = self.env['hr.employee'].search(
                [('driver_uid', '!=', False), ('is_under_vendor', '=', True), ('cashfree_payment', '=', False)])
        else:
            employees = self.env['hr.employee'].search(
                [('driver_uid', '!=', False), '|', ('is_under_vendor', '=', False), ('cashfree_payment', '=', True)])
        return [('id', 'in', employees.ids)]

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    payment_state = fields.Selection(PAYMENT_STATUS, string='Status')
    daily_payout_ids = fields.Many2many('driver.payout', "daily_batch_payout_rel", "daily_payout_id", "batch_id",
                                        "Daily Transaction")
    employee_id = fields.Many2one('hr.employee', string="Driver", domain=_get_employee , store=True)
    region_id = fields.Many2one('sales.region', related='employee_id.region_id', readonly=True, store=True)
    driver_uid = fields.Char('Driver ID', related='employee_id.driver_uid', readonly=True, store=True) #V13_field : driver_code
    daily_payout_amount = fields.Float(string='Daily Payout (A)', digits='Product Price') #V13_field : total_pay
    incentive_amount = fields.Float(string='Incentive (B)', digits='Product Price') #V13_field : incentive
    deduction_amount = fields.Float(string='Deduction (C)', digits='Product Price') #V13_field : balance_amt
    tds_amount = fields.Float(string='TDS (D)', digits='Product Price', store=True) #V13_field : tds_amt
    total_payout = fields.Float(string='Total Payout (A+B-C-D)', compute='get_total_payout', store=True,
                             digits='Product Price') #V13_field : final_pay
    payable_journal_id = fields.Many2one('account.move', string="Payable Journal Entry")
    payment_journal_id = fields.Many2one('account.move', string="Payment Journal Entry")
    cashfree_ref = fields.Char(string="Payment Gateway Ref#", copy=False) #V13_field: cashfree_ref
    avg_order_cost = fields.Float(string='Avg Cost Per Order', digits='Product Price') #V13_field : order_cost
    total_revenue = fields.Float(string='Total Revenue', digits='Product Price')
    transaction_date = fields.Datetime("Transaction Date") # transfer_date
    processed_date = fields.Datetime("Processed Date")
    batch_payout_id = fields.Many2one('driver.batch.payout', string="Payout") #V13_field : payout_id
    transfer_id = fields.Char(string="Transfer ID") #V13_field : transfer_ref
    utr_ref = fields.Char(string="UTR", copy=False)
    remarks = fields.Text(string="Remarks")
    tds_tax_id = fields.Many2one('account.tax', store=True, string='TDS Tax')
    is_reinitiated = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'), ], string='Is Re-initiated') #V13_field : reinitiated

    no_of_orders = fields.Integer("Total No of Orders", compute='get_total_orders') #V13_field : orders
    order_qty = fields.Integer("Total Order Quantity")
    driver_partner_id = fields.Many2one('res.partner', string='Partner')
    payment_vendor_acc = fields.Boolean(string='Payment to Vendor Account') #V13_field : driver_partner
    pan_no = fields.Char(string="PAN No")
    status_description = fields.Text(string="Status Description")
    is_reject = fields.Boolean('Reject')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        company_id = self.env.company.id
        sequence = self.env['ir.sequence'].search(
            [('company_id', '=', company_id), ('code', '=', 'payout.sequence.lines')])
        if not sequence:
            sequence = self.env['ir.sequence'].search([('code', '=', 'payout.sequence.lines')], limit=1)
            new_sequence = sequence.sudo().sudo().copy()
            new_sequence.company_id = company_id
            vals['transfer_id'] = self.env['ir.sequence'].next_by_code('payout.sequence.lines') or '/'
        else:
            vals['transfer_id'] = self.env['ir.sequence'].with_company(company_id).next_by_code('payout.sequence.lines') or '/'
        res = super().create(vals)
        if vals.get('employee_id'):
           res.compute_payment_vals()
        return res

    def write(self, vals):
        if vals.get('employee_id'):
            self.compute_payment_vals()
        res = super().write(vals)
        return res

    def compute_payment_vals(self):
        values = {
            'driver_partner_id': False,
            'payment_vendor_acc': False,
            'pan_no': '',
        }

        if self.employee_id:
            employee = self.employee_id
            if employee.is_under_vendor and employee.driver_partner_id and employee.vendor_tds_tax_id and employee.driver_partner_id.l10n_in_pan:
                values.update({
                    'driver_partner_id': employee.driver_partner_id.id,
                    'payment_vendor_acc': True,
                    'pan_no': employee.driver_partner_id.l10n_in_pan,
                })
            elif employee.pan_no and employee.apply_tds:
                values.update({
                    'driver_partner_id': employee.related_partner_id.id if employee.related_partner_id else False,
                    'pan_no': employee.pan_no,
                })
            else:
                values.update({
                    'driver_partner_id': employee.related_partner_id.id if employee.related_partner_id else False,
                    'pan_no': employee.pan_no or '',
                })

        self.write(values)

    def get_total_orders(self):
        for rec in self:
            rec.no_of_orders = sum(rec.daily_payout_ids.mapped('no_of_orders')) or 0
            rec.order_qty = sum(rec.daily_payout_ids.mapped('order_qty')) or 0

    @api.depends('daily_payout_amount', 'deduction_amount', 'incentive_amount')
    def get_total_payout(self):
        for rec in self:
            rec.total_payout = rec.tds_amount = 0.0
            rec.tds_tax_id = False
            tax_amt = 0
            tax_list = []
            if rec.daily_payout_amount > 0.0 or rec.incentive_amount > 0.0 or rec.deduction_amount > 0.0:
                accounts_data = self.env['driver.payout.accounting.config'].sudo().search([], limit=1)
                tax_base = rec.daily_payout_amount + rec.incentive_amount
                if accounts_data and accounts_data.tds_account_id:
                    if not rec.payment_vendor_acc or (rec.payment_vendor_acc and rec.employee_id.cashfree_payment):
                        if rec.payment_vendor_acc and rec.driver_partner_id and rec.employee_id.vendor_tds_tax_id and rec.driver_partner_id.l10n_in_pan:
                            rec.tds_tax_id = rec.employee_id.vendor_tds_tax_id.id
                            tax_val = rec.employee_id.vendor_tds_tax_id.with_context(
                                round=True).compute_all(tax_base)
                            tax_list = tax_val.get('taxes', [])
                        elif rec.employee_id.pan_no and rec.employee_id.apply_tds and accounts_data.tds_tax_id:
                            rec.tds_tax_id = accounts_data.tds_tax_id.id
                            rec.payment_vendor_acc = False
                            rec.driver_partner_id = rec.employee_id.related_partner_id.id
                            rec.pan_no = rec.employee_id.pan_no
                            tax_val = accounts_data.tds_tax_id.with_context(round=True).compute_all(
                                tax_base)
                            tax_list = tax_val.get('taxes', [])
                        if tax_list:
                            for t in tax_list:
                                tax_amt += round(t.get('amount', 0.0), 2)
                rec.tds_amount = tax_amt
                rec.total_payout = tax_base - rec.deduction_amount - rec.tds_amount

    def unlink(self):
        for rec in self:
            if rec.daily_payout_ids:
                for line in rec.daily_payout_ids:
                    line.batch_payout_id =False
        return super().unlink()

    def action_get_batch_payout_line(self):
        """
        Returns Driver batch payout line
        """
        return {
            'name': _('DRIVER BATCH PAYOUT LINE'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'driver.batch.payout.lines',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }