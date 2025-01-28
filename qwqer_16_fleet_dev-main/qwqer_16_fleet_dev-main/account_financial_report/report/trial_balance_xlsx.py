# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import _, models


class TrialBalanceXslx(models.AbstractModel):
    _name = "report.a_f_r.report_trial_balance_xlsx"
    _description = "Trial Balance XLSX Report"
    _inherit = "report.account_financial_report.abstract_report_xlsx"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Trial Balance")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = " - {} - {}".format(company.name, company.currency_id.name)
            report_name = report_name + suffix
        return report_name

    def _get_report_columns(self, report):
        if not report.show_partner_details:
            if report.hierarchy_on == 'relation':
                res = {
                    0: {"header": _("Group Code"), "field": "code", "width": 15},
                    1: {"header": _("Group"), "field": "name", "width": 30},
                    2: {"header": _("Account Code"), "field": "code", "width": 15},
                    3: {"header": _("Account"), "field": "name", "width": 40},
                    4: {
                        "main_header": _("Initial Balance"),
                        "header": _("Debit"),
                        "field": "initial_balance",
                        "sub_field_l": "initial_balance_debit",
                        "sub_field_r": "initial_balance_credit",
                        "type": "amount",
                        "width": 14,
                    },
                    6: {
                        "main_header": _("Period Transactions"),
                        "header": _("Debit"),
                        "field": "debit",
                        "type": "amount",
                        "width": 14,
                    },
                    7: {
                        "main_header": _(" "),
                        "header": _("Credit"),
                        "field": "credit",
                        "type": "amount",
                        "width": 14,
                    },
                    # 8: {
                    #     "main_header": _("Period Balance"),
                    #     "header": _("Debit"),
                    #     "field": "balance",
                    #     "sub_field_l": "balance_debit",
                    #     "sub_field_r": "balance_credit",
                    #     "type": "amount",
                    #     "width": 14,
                    # },
                    8: {
                        "main_header": _("Ending Balance"),
                        "header": _("Debit"),
                        "field": "ending_balance",
                        "sub_field_l": "ending_balance_debit",
                        "sub_field_r": "ending_balance_credit",
                        "type": "amount",
                        "width": 14,
                    },
                }
                if report.foreign_currency:
                    foreign_currency = {
                        12: {
                            "header": _("Cur."),
                            "field": "currency_id",
                            "field_currency_balance": "currency_id",
                            "type": "many2one",
                            "width": 7,
                        },
                        13: {
                            "header": _("Initial balance"),
                            "field": "initial_currency_balance",
                            "type": "amount_currency",
                            "width": 14,
                        },
                        14: {
                            "header": _("Ending balance"),
                            "field": "ending_currency_balance",
                            "type": "amount_currency",
                            "width": 14,
                        },
                    }
                    res = {**res, **foreign_currency}
            elif report.hierarchy_on == 'internal_type':
                res = {
                    0: {"header": _("Type"), "field": "name", "width": 30},
                    1: {"header": _("Account Code"), "field": "code", "width": 15},
                    2: {"header": _("Account"), "field": "name", "width": 40},
                    3: {
                        "main_header": _("Initial Balance"),
                        "header": _("Debit"),
                        "field": "initial_balance",
                        "sub_field_l": "initial_balance_debit",
                        "sub_field_r": "initial_balance_credit",
                        "type": "amount",
                        "width": 14,
                    },
                    5: {
                        "main_header": _("Period Transactions"),
                        "header": _("Debit"),
                        "field": "debit",
                        "type": "amount",
                        "width": 14,
                    },
                    6: {
                        "main_header": _(" "),
                        "header": _("Credit"),
                        "field": "credit",
                        "type": "amount",
                        "width": 14,
                    },
                    # 7: {
                    #     "main_header": _("Period Balance"),
                    #     "header": _("Debit"),
                    #     "field": "balance",
                    #     "sub_field_l": "balance_debit",
                    #     "sub_field_r": "balance_credit",
                    #     "type": "amount",
                    #     "width": 14,
                    # },
                    7: {
                        "main_header": _("Ending Balance"),
                        "header": _("Debit"),
                        "field": "ending_balance",
                        "sub_field_l": "ending_balance_debit",
                        "sub_field_r": "ending_balance_credit",
                        "type": "amount",
                        "width": 14,
                    },
                }
                if report.foreign_currency:
                    foreign_currency = {
                        11: {
                            "header": _("Cur."),
                            "field": "currency_id",
                            "field_currency_balance": "currency_id",
                            "type": "many2one",
                            "width": 7,
                        },
                        12: {
                            "header": _("Initial balance"),
                            "field": "initial_currency_balance",
                            "type": "amount_currency",
                            "width": 14,
                        },
                        13: {
                            "header": _("Ending balance"),
                            "field": "ending_currency_balance",
                            "type": "amount_currency",
                            "width": 14,
                        },
                    }
                    res = {**res, **foreign_currency}
            else:
                res = {
                    0: {"header": _("Code"), "field": "code", "width": 10},
                    1: {"header": _("Account"), "field": "name", "width": 60},
                    2: {
                        "main_header": _("Initial Balance"),
                        "header": _("Debit"),
                        "field": "initial_balance",
                        "sub_field_l": "initial_balance_debit",
                        "sub_field_r": "initial_balance_credit",
                        "type": "amount",
                        "width": 14,
                    },
                    4: {
                        "main_header": _("Period Transactions"),
                        "header": _("Debit"),
                        "field": "debit",
                        "type": "amount",
                        "width": 14,
                    },
                    5: {
                        "main_header": _(" "),
                        "header": _("Credit"),
                        "field": "credit",
                        "type": "amount",
                        "width": 14,
                    },
                    # 6: {
                    #     "main_header": _("Period Balance"),
                    #     "header": _("Debit"),
                    #     "field": "balance",
                    #     "sub_field_l": "balance_debit",
                    #     "sub_field_r": "balance_credit",
                    #     "type": "amount",
                    #     "width": 14,
                    # },
                    6: {
                        "main_header": _("Ending Balance"),
                        "header": _("Debit"),
                        "field": "ending_balance",
                        "sub_field_l": "ending_balance_debit",
                        "sub_field_r": "ending_balance_credit",
                        "type": "amount",
                        "width": 14,
                    },
                }
                if report.foreign_currency:
                    foreign_currency = {
                        10: {
                            "header": _("Cur."),
                            "field": "currency_id",
                            "field_currency_balance": "currency_id",
                            "type": "many2one",
                            "width": 7,
                        },
                        11: {
                            "header": _("Initial balance"),
                            "field": "initial_currency_balance",
                            "type": "amount_currency",
                            "width": 14,
                        },
                        12: {
                            "header": _("Ending balance"),
                            "field": "ending_currency_balance",
                            "type": "amount_currency",
                            "width": 14,
                        },
                    }
                    res = {**res, **foreign_currency}
            return res
        else:
            res = {
                0: {"header": _("Partner"), "field": "name", "width": 70},
                1: {
                    "header": _("Initial balance"),
                    "field": "initial_balance",
                    "type": "amount",
                    "width": 14,
                },
                2: {
                    "header": _("Debit"),
                    "field": "debit",
                    "type": "amount",
                    "width": 14,
                },
                3: {
                    "header": _("Credit"),
                    "field": "credit",
                    "type": "amount",
                    "width": 14,
                },
                # 4: {
                #     "header": _("Period balance"),
                #     "field": "balance",
                #     "type": "amount",
                #     "width": 14,
                # },
                4: {
                    "header": _("Ending balance"),
                    "field": "ending_balance",
                    "type": "amount",
                    "width": 14,
                },
            }
            if report.foreign_currency:
                foreign_currency = {
                    5: {
                        "header": _("Cur."),
                        "field": "currency_id",
                        "field_currency_balance": "currency_id",
                        "type": "many2one",
                        "width": 7,
                    },
                    6: {
                        "header": _("Initial balance"),
                        "field": "initial_currency_balance",
                        "type": "amount_currency",
                        "width": 14,
                    },
                    7: {
                        "header": _("Ending balance"),
                        "field": "ending_currency_balance",
                        "type": "amount_currency",
                        "width": 14,
                    },
                }
                res = {**res, **foreign_currency}
            return res

    def _get_report_filters(self, report):
        return [
            [
                _("Date range filter"),
                _("From: %s To: %s") % (report.date_from, report.date_to),
            ],
            [
                _("Target moves filter"),
                _("All posted entries")
                if report.target_move == "all"
                else _("All entries"),
            ],
            [
                _("Account at 0 filter"),
                _("Hide") if report.hide_account_at_0 else _("Show"),
            ],
            [
                _("Show foreign currency"),
                _("Yes") if report.foreign_currency else _("No"),
            ],
            [
                _("Limit hierarchy levels"),
                _("Level %s" % report.show_hierarchy_level)
                if report.limit_hierarchy_level
                else _("No limit"),
            ],
        ]

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _generate_report_content(self, workbook, report, data, report_data):
        res_data = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(report, data)
        trial_balance = res_data["trial_balance"]
        total_amount = res_data["total_amount"]
        partners_data = res_data["partners_data"]
        accounts_data = res_data["accounts_data"]
        hierarchy_on = res_data["hierarchy_on"]
        show_partner_details = res_data["show_partner_details"]
        show_hierarchy_level = res_data["show_hierarchy_level"]
        foreign_currency = res_data["foreign_currency"]
        limit_hierarchy_level = res_data["limit_hierarchy_level"]
        total_data = res_data["total_data"]
        context = self._context.copy()
        context['show_partner_details'] = show_partner_details
        self.env.context = context
        if not show_partner_details:
            for col_pos, column in report_data["columns"].items():
                report_data["sheet"].write(
                    report_data["row_pos"], col_pos, '', report_data["formats"]["format_header_center"]
                )
                if column.get('field') in ('initial_balance', 'balance', 'debit', 'credit', 'ending_balance'):
                    report_data["sheet"].write(
                        report_data["row_pos"], col_pos , column.get('main_header', ''), report_data["formats"]["format_header_left"]
                    )
                if column.get('field') in ('initial_balance', 'balance', 'ending_balance'):
                    report_data["sheet"].write(
                        report_data["row_pos"], col_pos + 1, '', report_data["formats"]["format_header_left"]
                    )
            report_data["row_pos"] += 1
            # Display array header for account lines
            self.write_array_header(report_data)

        # For each account
        if not show_partner_details:
            for balance in trial_balance:
                if hierarchy_on == "relation":
                    if limit_hierarchy_level:
                        if show_hierarchy_level > balance["level"]:
                            # Display account lines
                            self.write_line_from_dict(balance, report_data)
                    else:
                        self.write_line_from_dict(balance, report_data)
                elif hierarchy_on == "computed":
                    if balance["type"] == "account_type":
                        if limit_hierarchy_level:
                            if show_hierarchy_level > balance["level"]:
                                # Display account lines
                                self.write_line_from_dict(balance, report_data)
                        else:
                            self.write_line_from_dict(balance, report_data)
                else:
                    self.write_line_from_dict(balance, report_data)

            self.write_account_footer(
                total_data,
                'Total:',report_data
            )
        else:
            for account_id in total_amount:
                # Write account title
                self.write_array_title(
                    accounts_data[account_id]["code"]
                    + "- "
                    + accounts_data[account_id]["name"]
                )
                # Display array header for partner lines
                self.write_array_header(report_data )

                # For each partner
                for partner_id in total_amount[account_id]:
                    if isinstance(partner_id, int):
                        # Display partner lines
                        self.write_line_from_dict_order(
                            total_amount[account_id][partner_id],
                            partners_data[partner_id], report_data
                        )

                # Display account footer line
                accounts_data[account_id].update(
                    {
                        "initial_balance": total_amount[account_id]["initial_balance"],
                        "credit": total_amount[account_id]["credit"],
                        "debit": total_amount[account_id]["debit"],
                        "balance": total_amount[account_id]["balance"],
                        "ending_balance": total_amount[account_id]["ending_balance"],
                    }
                )
                if foreign_currency:
                    accounts_data[account_id].update(
                        {
                            "initial_currency_balance": total_amount[account_id][
                                "initial_currency_balance"
                            ],
                            "ending_currency_balance": total_amount[account_id][
                                "ending_currency_balance"
                            ],
                        }
                    )
                self.write_account_footer(
                    accounts_data[account_id],
                    accounts_data[account_id]["code"]
                    + "- "
                    + accounts_data[account_id]["name"],
                report_data)

                # Line break
                report_data["row_pos"] += 2

    def write_line_from_dict_order(self, total_amount, partner_data, report_data):
        total_amount.update({"name": str(partner_data["name"])})
        self.write_line_from_dict(total_amount, report_data)

    def write_line(self, line_object, type_object):
        """Write a line on current line using all defined columns field name.
        Columns are defined with `_get_report_columns` method.
        """
        if type_object == "partner":
            line_object.currency_id = line_object.report_account_id.currency_id
        elif type_object == "account":
            line_object.currency_id = line_object.currency_id
        super(TrialBalanceXslx, self).write_line(line_object)

    def write_account_footer(self, account, name_value, report_data):
        """Specific function to write account footer for Trial Balance"""
        if not account.get("currency_id"):
            account.update({"currency_id": self.env.company.currency_id.id})
            account.update({"currency_name": self.env.company.currency_id.name})
        format_amt = self._get_currency_amt_header_format_dict(account, report_data)
        for col_pos, column in report_data["columns"].items():
            if column.get('header') == 'Account':
                report_data["sheet"].write_string(
                    report_data["row_pos"], col_pos, name_value, report_data["formats"]["format_header_left"]
                )
                continue
            if column.get('header') in ['Group', 'Group Code', 'Type','Account Code']:
                report_data["sheet"].write_string(
                    report_data["row_pos"], col_pos, '', report_data["formats"]["format_header_left"]
                )
                continue
            if column["field"] == "name":
                value = name_value
            elif account.get(column["field"]):
                value = account[column["field"]]
            else:
                value = ''
            cell_type = column.get("type", "string")
            if cell_type == "string":
                report_data["sheet"].write_string(
                    report_data["row_pos"], col_pos, value or "", report_data["formats"]["format_header_left"]
                )
            elif cell_type == "amount":
                if column['field'] not in account.keys():
                    debit = 0
                    credit = 0
                    if 'sub_field_l' in column.keys():
                        debit = float(account.get(column["sub_field_l"]))
                    if 'sub_field_r' in column.keys():
                        credit = float(account.get(column["sub_field_r"]))
                    report_data["sheet"].write_number(
                        report_data["row_pos"], col_pos, abs(debit), report_data["formats"]["format_header_amount"]
                    )
                    report_data["sheet"].write_number(
                        report_data["row_pos"], col_pos + 1, abs(credit), report_data["formats"]["format_header_amount"]
                    )
                else:
                    value = account[column["field"]]
                    report_data["sheet"].write_number(
                        report_data["row_pos"], col_pos, float(value), report_data["formats"]["format_header_amount"]
                    )
            elif cell_type == "many2one" and account.get("currency_id"):
                report_data["sheet"].write_string(
                    report_data["row_pos"], col_pos, value.name or "", report_data["formats"]["format_header_right"]
                )
            elif cell_type == "amount_currency" and account.get("currency_id"):
                report_data["sheet"].write_number(report_data["row_pos"], col_pos, float(value), format_amt)
            else:
                report_data["sheet"].write_string(
                    report_data["row_pos"], col_pos, "", report_data["formats"]["format_header_right"]
                )
        report_data["row_pos"] += 1

    def write_line_from_dict(self, line_dict, report_data):
        """Write a line on current line ,override for trial balance
        """
        if self.env.context.get('show_partner_details'):
            return super(TrialBalanceXslx, self).write_line_from_dict(line_dict, report_data)
        for col_pos, column in report_data["columns"].items():
            value = line_dict.get(column["field"], False)
            cell_type = column.get("type", "string")
            if cell_type == "string":
                if line_dict.get("type", 'account_type') == 'group_type':
                    if column.get('header') in ['Group', 'Group Code']:
                        report_data["sheet"].write_string(
                            report_data["row_pos"], col_pos, value or "", report_data["formats"]["format_bold"]
                        )
                    continue
                if line_dict.get("type", 'account_type') == 'internal_type':
                    if column.get('header') in ['Type']:
                        report_data["sheet"].write_string(
                            report_data["row_pos"], col_pos, value or "", report_data["formats"]["format_bold"]
                        )
                    continue
                if line_dict.get("type", 'account_type') == 'account_type':
                    if (
                            not isinstance(value, str)
                            and not isinstance(value, bool)
                            and not isinstance(value, int)
                    ):
                        value = value and value.strftime("%d/%m/%Y")
                    if column.get('header') not in ['Group', 'Group Code', 'Type']:
                        report_data["sheet"].write_string(report_data["row_pos"], col_pos, value or "")
                    continue
            elif cell_type == "amount":
                if (
                        line_dict.get("account_group_id", False)
                        and line_dict["account_group_id"]
                ) or line_dict.get("type", 'account_type') in ['group_type', 'internal_type']:
                    cell_format = report_data["formats"]["format_amount_bold"]
                else:
                    cell_format = report_data["formats"]["format_amount"]
                if column.get('field') in ('initial_balance', 'balance', 'ending_balance'):
                    if value < 0:
                        report_data["sheet"].write_number(
                            report_data["row_pos"], col_pos, 0.00, cell_format
                        )
                        report_data["sheet"].write_number(
                            report_data["row_pos"], col_pos + 1, abs(float(value)), cell_format
                        )
                    else:
                        report_data["sheet"].write_number(
                            report_data["row_pos"], col_pos, float(value), cell_format
                        )
                        report_data["sheet"].write_number(
                            report_data["row_pos"], col_pos + 1, 0.00, cell_format
                        )
                else:
                    report_data["sheet"].write_number(
                        report_data["row_pos"], col_pos, float(value), cell_format
                    )
            elif cell_type == "amount_currency":
                if line_dict.get("currency_name", False):
                    format_amt = self._get_currency_amt_format_dict(line_dict)
                    report_data["sheet"].write_number(
                        report_data["row_pos"], col_pos, float(value), format_amt
                    )
            elif cell_type == "currency_name":
                report_data["sheet"].write_string(
                    report_data["row_pos"], col_pos, value or "", report_data["formats"]["format_right"]
                )
        report_data["row_pos"] += 1

    def _set_column_width(self, report_data):
        """Set width for all defined columns.
        Columns are defined with `_get_report_columns` method.
        """
        if self.env.context.get('show_partner_details'):
            return super(TrialBalanceXslx, self)._set_column_width(report_data)
        for position, column in report_data["columns"].items():
            report_data["sheet"].set_column(position, position, column["width"])
            if column.get('field') in ('initial_balance', 'balance', 'ending_balance'):
                report_data["sheet"].set_column(position + 1, position + 1, column["width"])

    def write_array_header(self, report_data):
        """Write array header on current line using all defined columns name.
        Columns are defined with `_get_report_columns` method.
        """
        if self.env.context.get('show_partner_details'):
            return super(TrialBalanceXslx, self).write_array_header()
        for col_pos, column in report_data["columns"].items():
            report_data["sheet"].write(
                report_data["row_pos"], col_pos, column["header"], report_data["formats"]["format_header_center"]
            )
            if column.get('field') in ('initial_balance', 'balance', 'ending_balance'):
                report_data["sheet"].write(
                    report_data["row_pos"], col_pos + 1, 'Credit', report_data["formats"]["format_header_center"]
                )
        report_data["row_pos"] += 1
