# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class FinancialReportLiveController(http.Controller):

    @http.route("/financial_report_live/bootstrap", type="json", auth="user")
    def bootstrap(self):
        srv = request.env["financial.report.live"]
        return {
            "default_options": srv.get_default_options(),
            "reports": srv.get_reports_list(),
            "journals": srv.get_journals_list(),
        }

    @http.route("/financial_report_live/lines", type="json", auth="user")
    def lines(self, options):
        srv = request.env["financial.report.live"]
        return srv.get_lines(options)

    @http.route("/financial_report_live/toggle_unfold", type="json", auth="user")
    def toggle_unfold(self, options, line_id):
        srv = request.env["financial.report.live"]
        return srv.toggle_unfold(options, line_id)

    @http.route("/financial_report_live/move_lines_action", type="json", auth="user")
    def move_lines_action(self, options, line_domain):
        srv = request.env["financial.report.live"]
        return srv.get_move_lines_action(options, line_domain)
