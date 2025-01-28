# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import operator
from datetime import date, datetime, timedelta

from odoo import api, models
from odoo.tools import float_is_zero


class AgedPartnerBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.aged_partner_balance"
    _description = "Aged Partner Balance Report"
    _inherit = "report.account_financial_report.abstract_report"

    @api.model
    def _initialize_account(self, ag_pb_data, acc_id):
        ag_pb_data[acc_id] = {}
        ag_pb_data[acc_id]["id"] = acc_id
        ag_pb_data[acc_id]["residual"] = 0.0
        ag_pb_data[acc_id]["current"] = 0.0
        ag_pb_data[acc_id]["30_days"] = 0.0
        ag_pb_data[acc_id]["60_days"] = 0.0
        ag_pb_data[acc_id]["90_days"] = 0.0
        ag_pb_data[acc_id]["120_days"] = 0.0
        ag_pb_data[acc_id]["older"] = 0.0
        for interval_line in self.env.context["age_partner_config"].line_ids:
            ag_pb_data[acc_id][interval_line] = 0.0
        return ag_pb_data

    @api.model
    def _initialize_partner(self, ag_pb_data, acc_id, prt_id):
        ag_pb_data[acc_id][prt_id] = {}
        ag_pb_data[acc_id][prt_id]["id"] = acc_id
        ag_pb_data[acc_id][prt_id]["residual"] = 0.0
        ag_pb_data[acc_id][prt_id]["current"] = 0.0
        ag_pb_data[acc_id][prt_id]["30_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["60_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["90_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["120_days"] = 0.0
        ag_pb_data[acc_id][prt_id]["older"] = 0.0
        ag_pb_data[acc_id][prt_id]["move_lines"] = []
        for interval_line in self.env.context["age_partner_config"].line_ids:
            ag_pb_data[acc_id][prt_id][interval_line] = 0.0
        return ag_pb_data

    def _get_journals_data(self, journals_ids):
        journals = self.env["account.journal"].browse(journals_ids)
        journals_data = {}
        for journal in journals:
            journals_data.update({journal.id: {"id": journal.id, "code": journal.code}})
        return journals_data

    def _get_accounts_data(self, accounts_ids):
        accounts = self.env["account.account"].browse(accounts_ids)
        accounts_data = {}
        for account in accounts:
            accounts_data.update(
                {
                    account.id: {
                        "id": account.id,
                        "code": account.code,
                        "name": account.name,
                    }
                }
            )
        return accounts_data

    @api.model
    def _get_move_lines_domain(
        self, company_id, account_ids, partner_ids, only_posted_moves, date_from, customer_type, state_ids, region_ids,service_type
    ):
        domain = [
            ("account_id", "in", account_ids),
            ("company_id", "=", company_id),
            ("reconciled", "=", False),
        ]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        else:
            domain += [("partner_id", "!=", False)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        if date_from:
            domain += [("date", ">", date_from)]
        if customer_type:
            domain += [("partner_id.customer_type", "=", customer_type)]
        if state_ids:
            domain += [('partner_id.region_id.state_id', 'in', state_ids.ids)]
        if region_ids:
            domain += [('partner_id.region_id', 'in', region_ids.ids)]
        if service_type:
            domain += [('partner_id.service_type_id', '=', service_type.id)]
        return domain

    @api.model
    def _calculate_amounts(
        self, ag_pb_data, acc_id, prt_id, residual, due_date, date_at_object
    ):
        ag_pb_data[acc_id]["residual"] += residual
        ag_pb_data[acc_id][prt_id]["residual"] += residual
        interval_lines = self.env.context["age_partner_config"].line_ids
        today = date_at_object
        if not due_date or today <= due_date:
            ag_pb_data[acc_id]["current"] += residual
            ag_pb_data[acc_id][prt_id]["current"] += residual
            due_date = today
        elif today <= due_date + timedelta(days=30):
            ag_pb_data[acc_id]["30_days"] += residual
            ag_pb_data[acc_id][prt_id]["30_days"] += residual
        elif today <= due_date + timedelta(days=60):
            ag_pb_data[acc_id]["60_days"] += residual
            ag_pb_data[acc_id][prt_id]["60_days"] += residual
        elif today <= due_date + timedelta(days=90):
            ag_pb_data[acc_id]["90_days"] += residual
            ag_pb_data[acc_id][prt_id]["90_days"] += residual
        elif today <= due_date + timedelta(days=120):
            ag_pb_data[acc_id]["120_days"] += residual
            ag_pb_data[acc_id][prt_id]["120_days"] += residual
        else:
            ag_pb_data[acc_id]["older"] += residual
            ag_pb_data[acc_id][prt_id]["older"] += residual
        days_difference = abs((today - due_date).days)
        for index, line in enumerate(interval_lines):
            lower_limit = 0 if not index else interval_lines[index - 1].inferior_limit
            next_line = interval_lines[index] if index < len(interval_lines) else None
            interval_range = self._get_values_for_range_intervals(
                lower_limit, next_line.inferior_limit
            )
            if (
                days_difference in interval_range
                or days_difference == line.inferior_limit
            ):
                ag_pb_data[acc_id][line] += residual
                ag_pb_data[acc_id][prt_id][line] += residual
                break
        return ag_pb_data

    def _get_values_for_range_intervals(self, num1, num2):
        min_num = min(num1, num2)
        max_num = max(num1, num2)
        if abs(num2 - num1) == 1:
            return [max_num]
        return list(range(min_num + 1, max_num))

    def _get_account_partial_reconciled(self, company_id, date_at_object):
        domain = [("max_date", ">", date_at_object), ("company_id", "=", company_id)]
        fields = [
            "debit_move_id",
            "credit_move_id",
            "amount",
            "debit_amount_currency",
            "credit_amount_currency",
        ]
        accounts_partial_reconcile = self.env["account.partial.reconcile"].search_read(
            domain=domain, fields=fields
        )
        debit_amount = {}
        debit_amount_currency = {}
        credit_amount = {}
        credit_amount_currency = {}
        for account_partial_reconcile_data in accounts_partial_reconcile:
            debit_move_id = account_partial_reconcile_data["debit_move_id"][0]
            credit_move_id = account_partial_reconcile_data["credit_move_id"][0]
            if debit_move_id not in debit_amount.keys():
                debit_amount[debit_move_id] = 0.0
                debit_amount_currency[debit_move_id] = 0.0
            debit_amount_currency[debit_move_id] += account_partial_reconcile_data[
                "debit_amount_currency"
            ]
            debit_amount[debit_move_id] += account_partial_reconcile_data["amount"]
            if credit_move_id not in credit_amount.keys():
                credit_amount[credit_move_id] = 0.0
                credit_amount_currency[credit_move_id] = 0.0
            credit_amount[credit_move_id] += account_partial_reconcile_data["amount"]
            credit_amount_currency[credit_move_id] += account_partial_reconcile_data[
                "credit_amount_currency"
            ]
            account_partial_reconcile_data.update(
                {"debit_move_id": debit_move_id, "credit_move_id": credit_move_id}
            )
        return (
            accounts_partial_reconcile,
            debit_amount,
            credit_amount,
            debit_amount_currency,
            credit_amount_currency,
        )

    @api.model
    def _get_new_move_lines_domain(
        self, new_ml_ids, account_ids, company_id, partner_ids, only_posted_moves
    ):
        domain = [
            ("account_id", "in", account_ids),
            ("company_id", "=", company_id),
            ("id", "in", new_ml_ids),
        ]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        else:
            domain += [("partner_id", "!=", False)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        return domain

    def _recalculate_move_lines(
        self,
        move_lines,
        debit_ids,
        credit_ids,
        debit_amount,
        credit_amount,
        ml_ids,
        account_ids,
        company_id,
        partner_ids,
        only_posted_moves,
        debit_amount_currency,
        credit_amount_currency,
    ):
        debit_ids = set(debit_ids)
        credit_ids = set(credit_ids)
        in_credit_but_not_in_debit = credit_ids - debit_ids
#         print("------------debit_ids---credit_ids---in_credit_but_not_in_debit",credit_ids,debit_ids,in_credit_but_not_in_debit)
        reconciled_ids = list(debit_ids) + list(in_credit_but_not_in_debit)
#         print("------------reconciled_ids",reconciled_ids)
        reconciled_ids = set(reconciled_ids)
#         print("-------set-----reconciled_ids",reconciled_ids)
        ml_ids = set(ml_ids)
        new_ml_ids = reconciled_ids - ml_ids
#         print("------------new_ml_ids",new_ml_ids)
        new_ml_ids = list(new_ml_ids)
#         print("-------list-----new_ml_ids",new_ml_ids)
        new_domain = self._get_new_move_lines_domain(
            new_ml_ids, account_ids, company_id, partner_ids, only_posted_moves
        )
        ml_fields = [
            "id",
            "name",
            "date",
            "move_id",
            "journal_id",
            "account_id",
            "partner_id",
            "amount_residual",
            "date_maturity",
            "ref",
            "reconciled",
        ]
        new_move_lines_qry = self.env["account.move.line"]._where_calc(domain=new_domain)
        from_clause, where_clause, where_clause_params = new_move_lines_qry.get_sql()
        mvl_sql = """
                SELECT account_move_line.id,account_move_line.name,account_move_line.date,account_move_line.move_id,account_move_line.move_name,account_move_line.journal_id,
                account_move_line.account_id,account_move_line.partner_id,account_move_line.amount_residual,account_move_line.date_maturity,account_move_line.ref,account_move_line.reconciled
                 FROM %(from)s WHERE %(where)s 
                """ % {'from': from_clause, 'where': where_clause}
        self.env.cr.execute(mvl_sql, where_clause_params)
        new_move_lines =self.env.cr.dictfetchall()
        move_lines = move_lines + new_move_lines
        for move_line in move_lines:
            ml_id = move_line["id"]
            if ml_id in debit_ids:
                move_line["amount_residual"] += debit_amount[ml_id]
            if ml_id in credit_ids:
                move_line["amount_residual"] -= credit_amount[ml_id]
        return move_lines

    def _get_move_lines_data(
        self,
        company_id,
        account_ids,
        partner_ids,
        date_at_object,
        date_from,
        only_posted_moves,
        show_move_line_details,customer_type, state_ids, region_ids, service_type
    ):
        domain = self._get_move_lines_domain(
            company_id, account_ids, partner_ids, only_posted_moves, date_from, customer_type, state_ids, region_ids, service_type
        )
        ml_fields = self._get_ml_fields()
        line_model = self.env["account.move.line"]
        move_lines = line_model.search_read(domain=domain, fields=ml_fields)
        journals_ids = set()
        partners_ids = set()
        partners_data = {}
        ag_pb_data = {}
        if date_at_object < date.today():
            (
                acc_partial_rec,
                debit_amount,
                credit_amount,
                debit_amount_currency,
                credit_amount_currency,
            ) = self._get_account_partial_reconciled(company_id, date_at_object)
            if acc_partial_rec:
                ml_ids = list(map(operator.itemgetter("id"), move_lines))
                debit_ids = list(
                    map(operator.itemgetter("debit_move_id"), acc_partial_rec)
                )
                credit_ids = list(
                    map(operator.itemgetter("credit_move_id"), acc_partial_rec)
                )
                move_lines = self._recalculate_move_lines(
                    move_lines,
                    debit_ids,
                    credit_ids,
                    debit_amount,
                    credit_amount,
                    ml_ids,
                    account_ids,
                    company_id,
                    partner_ids,
                    only_posted_moves,
                    debit_amount_currency,
                    credit_amount_currency,
                )
        move_lines = [
            move_line
            for move_line in move_lines
            if move_line["date"] <= date_at_object
            and not float_is_zero(move_line["amount_residual"], precision_digits=2)
        ]
        for move_line in move_lines:
            print(move_line)
            journal_id = move_line["journal_id"][0] if isinstance(move_line["journal_id"], tuple) else  move_line["journal_id"]
            partner_id = move_line["partner_id"][0] if isinstance(move_line["partner_id"], tuple) else  move_line["partner_id"]
            acc_id = move_line["account_id"][0] if isinstance(move_line["account_id"], tuple) else  move_line["account_id"]
            move_name = move_line["move_id"][1] if isinstance(move_line["move_id"], tuple) else  move_line["move_name"]
            journals_ids.add(journal_id)
            if partner_id:
                prt_region = ''
                prt_sales_person = ''
                prt_partner_id = ''
                prt_service_type = ''
                customer_ref_key = ''

                res_partner = self.env['res.partner'].browse(partner_id)
                customer_ref_key =res_partner.customer_ref_key
                if res_partner and res_partner.region_id:
                    prt_region = res_partner.region_id.name or False
                if res_partner and res_partner.sudo().order_sales_person:
                    prt_sales_person = res_partner.sudo().order_sales_person.name or False
                if res_partner and res_partner.id:
                    prt_partner_id = str(res_partner.id) or False
                if res_partner and res_partner.service_type_id:
                    prt_service_type = res_partner.service_type_id.name or False
                prt_id = partner_id
                prt_name = (res_partner and res_partner.name) or ""
            else:
                prt_id = 0
                prt_name = ""
                prt_partner_id = ""
                prt_region= ""
                prt_sales_person= ""
                prt_service_type = ""
                customer_ref_key = ''
            if prt_id not in partners_ids:
                partners_data.update({prt_id: {"id": prt_id, "name": prt_name,
                                               "partner_id" : prt_partner_id,
                                               "region_id":prt_region,
                                               "sales_person":prt_sales_person,
                                               "service_type_id":prt_service_type,
                                               "customer_ref_key":customer_ref_key
                                               }})
                partners_ids.add(prt_id)
            if acc_id not in ag_pb_data.keys():
                ag_pb_data = self._initialize_account(ag_pb_data, acc_id)
            if prt_id not in ag_pb_data[acc_id]:
                ag_pb_data = self._initialize_partner(ag_pb_data, acc_id, prt_id)
            move_line_data = {}
            if show_move_line_details:
                if move_line["ref"] == move_line["name"]:
                    if move_line["ref"]:
                        ref_label = move_line["ref"]
                    else:
                        ref_label = ""
                elif not move_line["ref"]:
                    ref_label = move_line["name"]
                elif not move_line["name"]:
                    ref_label = move_line["ref"]
                else:
                    ref_label = move_line["ref"] + str(" - ") + move_line["name"]
                move_line_data.update(
                    {
                        "line_rec": line_model.browse(move_line["id"]),
                        "date": move_line["date"],
                        "entry": move_name,
                        "jnl_id": journal_id,
                        "acc_id": acc_id,
                        "partner": prt_name,
                        "ref_label": ref_label,
                        "due_date": move_line["date_maturity"] or move_line["date"],
                        "residual": move_line["amount_residual"],
                        "region_id":prt_region,
                        "partner_id" : prt_partner_id,
                        "sales_person":prt_sales_person,
                        "service_type_id":prt_service_type
                    }
                )
                ag_pb_data[acc_id][prt_id]["move_lines"].append(move_line_data)
            ag_pb_data = self._calculate_amounts(
                ag_pb_data,
                acc_id,
                prt_id,
                move_line["amount_residual"],
                move_line["date_maturity"] or move_line['date'],
                date_at_object,
            )
        journals_data = self._get_journals_data(list(journals_ids))
        accounts_data = self._get_accounts_data(ag_pb_data.keys())
        return ag_pb_data, accounts_data, partners_data, journals_data

    @api.model
    def _compute_maturity_date(self, ml, date_at_object):
        ml.update(
            {
                "current": 0.0,
                "30_days": 0.0,
                "60_days": 0.0,
                "90_days": 0.0,
                "120_days": 0.0,
                "older": 0.0,
            }
        )
        interval_lines = self.env.context["age_partner_config"].line_ids
        for interval_line in interval_lines:
            ml[interval_line] = 0.0
        due_date = ml["due_date"]
        amount = ml["residual"]
        today = date_at_object
        if not due_date or today <= due_date:
            ml["current"] += amount
            due_date = today
        elif today <= due_date + timedelta(days=30):
            ml["30_days"] += amount
        elif today <= due_date + timedelta(days=60):
            ml["60_days"] += amount
        elif today <= due_date + timedelta(days=90):
            ml["90_days"] += amount
        elif today <= due_date + timedelta(days=120):
            ml["120_days"] += amount
        else:
            ml["older"] += amount
        days_difference = abs((today - due_date).days)
        for index, interval_line in enumerate(interval_lines):
            lower_limit = 0 if not index else interval_lines[index - 1].inferior_limit
            next_line = interval_lines[index] if index < len(interval_lines) else None
            interval_range = self._get_values_for_range_intervals(
                lower_limit, next_line.inferior_limit
            )
            if (
                days_difference in interval_range
                or days_difference == interval_line.inferior_limit
            ):
                ml[interval_line] += amount
                break

    def _create_account_list(
        self,
        ag_pb_data,
        accounts_data,
        partners_data,
        journals_data,
        show_move_line_details,
        date_at_oject,
    ):
        aged_partner_data = []
        interval_lines = self.env.context["age_partner_config"].line_ids
        for account in accounts_data.values():
            acc_id = account["id"]
            account.update(
                {
                    "residual": ag_pb_data[acc_id]["residual"],
                    "current": ag_pb_data[acc_id]["current"],
                    "30_days": ag_pb_data[acc_id]["30_days"],
                    "60_days": ag_pb_data[acc_id]["60_days"],
                    "90_days": ag_pb_data[acc_id]["90_days"],
                    "120_days": ag_pb_data[acc_id]["120_days"],
                    "older": ag_pb_data[acc_id]["older"],
                    "partners": [],
                }
            )
            for interval_line in interval_lines:
                account[interval_line] = ag_pb_data[acc_id][interval_line]
            for prt_id in ag_pb_data[acc_id]:
                if isinstance(prt_id, int):
                    partner = {
                        "name": partners_data[prt_id]["name"],
                        "residual": ag_pb_data[acc_id][prt_id]["residual"],
                        "current": ag_pb_data[acc_id][prt_id]["current"],
                        "30_days": ag_pb_data[acc_id][prt_id]["30_days"],
                        "60_days": ag_pb_data[acc_id][prt_id]["60_days"],
                        "90_days": ag_pb_data[acc_id][prt_id]["90_days"],
                        "120_days": ag_pb_data[acc_id][prt_id]["120_days"],
                        "older": ag_pb_data[acc_id][prt_id]["older"],
                        "region_id": partners_data[prt_id]["region_id"],
                        "partner_id" : partners_data[prt_id]["partner_id"],
                        "service_type_id":partners_data[prt_id]["service_type_id"],
                        "sales_person": partners_data[prt_id]["sales_person"],
                        "customer_ref_key": str(partners_data[prt_id]["customer_ref_key"] or ""),

                    }
                    for interval_line in interval_lines:
                        partner[interval_line] = ag_pb_data[acc_id][prt_id][
                            interval_line
                        ]
                    if show_move_line_details:
                        move_lines = []
                        for ml in ag_pb_data[acc_id][prt_id]["move_lines"]:
                            ml.update(
                                {
                                    "journal": journals_data[ml["jnl_id"]]["code"],
                                    "account": accounts_data[ml["acc_id"]]["code"],
                                }
                            )
                            self._compute_maturity_date(ml, date_at_oject)
                            move_lines.append(ml)
                        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                        partner.update({"move_lines": move_lines})
                    account["partners"].append(partner)
            aged_partner_data.append(account)
        return aged_partner_data

    @api.model
    def _calculate_percent(self, aged_partner_data):
        interval_lines = self.env.context["age_partner_config"].line_ids
        for account in aged_partner_data:
            if abs(account["residual"]) > 0.01:
                total = account["residual"]
                account.update(
                    {
                        "percent_current": abs(
                            round((account["current"] / total) * 100, 2)
                        ),
                        "percent_30_days": abs(
                            round((account["30_days"] / total) * 100, 2)
                        ),
                        "percent_60_days": abs(
                            round((account["60_days"] / total) * 100, 2)
                        ),
                        "percent_90_days": abs(
                            round((account["90_days"] / total) * 100, 2)
                        ),
                        "percent_120_days": abs(
                            round((account["120_days"] / total) * 100, 2)
                        ),
                        "percent_older": abs(
                            round((account["older"] / total) * 100, 2)
                        ),
                    }
                )
                for interval_line in interval_lines:
                    account[f"percent_{interval_line.id}"] = abs(
                        round((account[interval_line] / total) * 100, 2)
                    )
            else:
                account.update(
                    {
                        "percent_current": 0.0,
                        "percent_30_days": 0.0,
                        "percent_60_days": 0.0,
                        "percent_90_days": 0.0,
                        "percent_120_days": 0.0,
                        "percent_older": 0.0,
                    }
                )
                for interval_line in interval_lines:
                    account[f"percent_{interval_line.id}"] = 0.0
        return aged_partner_data

    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        account_ids = data["account_ids"]
        partner_ids = data["partner_ids"]
        date_at = data["date_at"]
        date_at_object = datetime.strptime(date_at, "%Y-%m-%d").date()
        date_from = data["date_from"]
        only_posted_moves = data["only_posted_moves"]
        show_move_line_details = data["show_move_line_details"]
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        customer_type = docs.customer_type
        state_ids = docs.state_ids
        region_ids = docs.region_ids
        service_type = docs.service_type_id
        aged_partner_configuration = self.env[
            "account.age.report.configuration"
        ].browse(data["age_partner_config_id"])
        (ag_pb_data, accounts_data, partners_data, journals_data,) = self.with_context(
            age_partner_config=aged_partner_configuration
        )._get_move_lines_data(
            company_id,
            account_ids,
            partner_ids,
            date_at_object,
            date_from,
            only_posted_moves,
            show_move_line_details,customer_type, state_ids, region_ids, service_type
        )
        aged_partner_data = self.with_context(
            age_partner_config=aged_partner_configuration
        )._create_account_list(
            ag_pb_data,
            accounts_data,
            partners_data,
            journals_data,
            show_move_line_details,
            date_at_object,
        )
        aged_partner_data = self.with_context(
            age_partner_config=aged_partner_configuration
        )._calculate_percent(aged_partner_data)
        return {
            "doc_ids": [wizard_id],
            "doc_model": "aged.partner.balance.report.wizard",
            "docs": self.env["aged.partner.balance.report.wizard"].browse(wizard_id),
            "company_name": company.display_name,
            "currency_name": company.currency_id.name,
            "date_at": date_at,
            "only_posted_moves": only_posted_moves,
            "aged_partner_balance": aged_partner_data,
            "show_move_lines_details": show_move_line_details,
            "age_partner_config": aged_partner_configuration,
        }

    def _get_ml_fields(self):
        return self.COMMON_ML_FIELDS + [
            "amount_residual",
            "reconciled",
            "date_maturity",
        ]
