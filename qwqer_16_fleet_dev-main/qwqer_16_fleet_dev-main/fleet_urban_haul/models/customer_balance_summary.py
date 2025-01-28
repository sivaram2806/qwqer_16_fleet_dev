# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerBalance(models.Model):
    _inherit = "partner.balance"
    _description = "Partner Balance"

    to_invoice_uh_trips = fields.Float(string="In progress UH Trips")

    @api.model
    def _sum_due_amount(self):
        rec = super()._sum_due_amount()
        rec += '''+ COALESCE(btu.to_inv_trip,0)'''
        return rec

    @api.model
    def _select(self):
        rec = super()._select()
        rec+=''',
        btu.to_inv_trip as to_invoice_uh_trips'''
        return rec

    @api.model
    def _from(self):
        rec = super()._from()
        rec+='''
        LEFT JOIN (
        SELECT
            btu.customer_id AS partner_id,
            SUM(btul.customer_amount) AS to_inv_trip
        FROM 
            batch_trip_uh AS btu
        JOIN 
            batch_trip_uh_line AS btul ON btu.id = btul.batch_trip_uh_id
        LEFT JOIN 
            (
                SELECT DISTINCT
                    mi.batch_trip_uh_id,
                    mi.batch_trip_uh_line_id
                FROM 
                    model_id AS mi
                LEFT JOIN 
                    trip_summary_line_uh AS tsul ON mi.batch_trip_uh_id = tsul.id
                LEFT JOIN 
                    trip_summary_uh AS tsu ON tsul.trip_summary_id = tsu.id
                WHERE 
                    tsu.state IN ('new', 'draft')
                    AND tsu.partner_type = 'customer'
            ) AS filtered_mi ON btul.id = filtered_mi.batch_trip_uh_line_id
        WHERE 
            btu.state NOT IN ('completed', 'rejected')
        GROUP BY
            btu.customer_id
        ORDER BY
            btu.customer_id) btu ON rp.id=btu.partner_id'''
        return rec

    @api.model
    def _group_by(self):
        rec = super()._group_by()
        rec+=''',
        btu.partner_id,
        btu.to_inv_trip'''
        return rec