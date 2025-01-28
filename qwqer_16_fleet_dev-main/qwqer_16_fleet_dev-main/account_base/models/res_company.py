# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    image_signature = fields.Binary("Signature")
    image_seal = fields.Binary("Seal")

    record_limit = fields.Integer("Record Fetch Limit")
    days_limit = fields.Integer("Days Fetch Limit")
    post_invoice_with_cron = fields.Boolean(string="Post Invoices")
    skip_start_time = fields.Selection([("0", "0"), ("1", "1"), ("2", "2"),
                                        ("3", "3"),
                                        ("4", "4"),
                                        ("5", "5"),
                                        ("6", "6"),
                                        ("7", "7"),
                                        ("8", "8"),
                                        ("9", "9"),
                                        ("10", "10"),
                                        ("11", "11"),
                                        ("12", "12"),
                                        ("13", "13"),
                                        ("14", "14"),
                                        ("15", "15"),
                                        ("16", "16"),
                                        ("17", "17"),
                                        ("18", "18"),
                                        ("19", "19"),
                                        ("20", "20"),
                                        ("21", "21"),
                                        ("22", "22"),
                                        ("23", "23")], "Skip Start Hour")

    skip_end_time = fields.Selection([("0", "0"), ("1", "1"), ("2", "2"),
                                        ("3", "3"),
                                        ("4", "4"),
                                        ("5", "5"),
                                        ("6", "6"),
                                        ("7", "7"),
                                        ("8", "8"),
                                        ("9", "9"),
                                        ("10", "10"),
                                        ("11", "11"),
                                        ("12", "12"),
                                        ("13", "13"),
                                        ("14", "14"),
                                        ("15", "15"),
                                        ("16", "16"),
                                        ("17", "17"),
                                        ("18", "18"),
                                        ("19", "19"),
                                        ("20", "20"),
                                        ("21", "21"),
                                        ("22", "22"),
                                        ("23", "23")], "Skip End Hour")

