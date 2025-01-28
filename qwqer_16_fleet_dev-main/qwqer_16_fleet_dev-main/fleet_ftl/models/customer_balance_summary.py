# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class PartnerBalance(models.Model):
    _inherit = "partner.balance"
    _description = "Partner Balance"

    to_invoice_wo = fields.Float(string="Inprogress FTL Trips")

    @api.model
    def _sum_due_amount(self):
        rec = super()._sum_due_amount()
        rec += '''+ COALESCE(wo.to_invoice_wo,0)'''
        return rec

    @api.model
    def _select(self):
        rec = super()._select()
        rec += ''',
        wo.to_invoice_wo'''
        return rec

    @api.model
    def _from(self):
        rec = super()._from()
        rec+='''
        LEFT JOIN (
        SELECT
            wo.customer_id AS partner_id,
            COALESCE(SUM(
                CASE
                    WHEN wo.invoice_amount > 0 THEN abs(wo.total_amount - wo.invoice_amount)
                    ELSE total_amount
                END
            ), 0.00) AS to_invoice_wo
        FROM 
            work_order wo 
        WHERE
            invoice_amount > total_amount OR invoice_amount = total_amount or invoice_amount = 0.0
        GROUP BY
            partner_id
        ORDER BY
        	partner_id) wo ON rp.id=wo.partner_id'''
        return rec

    @api.model
    def _group_by(self):
        rec = super()._group_by()
        rec+=''',
        wo.to_invoice_wo'''
        return rec