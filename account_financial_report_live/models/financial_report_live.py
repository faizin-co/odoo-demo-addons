# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import io
import base64

try:
    import xlsxwriter
except Exception:
    xlsxwriter = None


class FinancialReportLive(models.Model):
    _name = "financial.report.live"
    _description = "Financial Report Live (Viewer)"
    _rec_name = "id"

    # ===========
    # Options
    # ===========
    @api.model
    def get_default_options(self):
        """Default options for UI."""
        today = fields.Date.context_today(self)
        first = today.replace(day=1)
        journals = self.env["account.journal"].search(
            [("company_id", "=", self.env.company.id)]
        ).ids

        report = self._resolve_default_report_from_context()

        return {
            "company_id": self.env.company.id,
            "report_id": report.id if report else False,
            "date_from": first.isoformat(),
            "date_to": today.isoformat(),
            "journal_ids": journals,
            "target_move": "posted",  # posted / all
            "unfolded_line_ids": [],
            "comparison": None,  # future
        }

    def _resolve_default_report_from_context(self):
        """
        Resolve default report based on menu action context:
        - default_report_key = 'pl'  => Profit & Loss / Laba Rugi
        - default_report_key = 'bs'  => Balance Sheet / Neraca

        No XMLID dependency.
        """
        Report = self.env["account.financial.report"]
        key = (self.env.context.get("default_report_key") or "").lower().strip()

        def _pick_by_keywords(keywords):
            # OR domain for ilike keywords
            if not keywords:
                return Report.browse()
            domain = ["|"] * (len(keywords) - 1) + [("name", "ilike", kw) for kw in keywords]
            return Report.search(domain, order="sequence,id", limit=1)

        if key == "pl":
            rec = _pick_by_keywords(["Profit and Loss", "Profit & Loss", "P&L", "Laba Rugi", "Laporan Laba"])
            if rec:
                return rec

        if key == "bs":
            rec = _pick_by_keywords(["Balance Sheet", "Neraca"])
            if rec:
                return rec

        # Fallback:
        # - jika hanya 1 root dan punya children: pilih child pertama
        # - kalau tidak: pilih root pertama
        roots = Report.search([("parent_id", "=", False)], order="sequence,id")
        if len(roots) == 1 and roots.children_ids:
            return roots.children_ids.sorted(key=lambda r: (r.sequence, r.id))[0]
        return roots[:1]

    # ===========
    # Public API called by controller
    # ===========
    @api.model
    def get_reports_list(self):
        """
        List available reports for dropdown.
        Banyak setup OCA punya 1 root "Financial Reports" dan report sebenarnya ada di children.
        """
        Report = self.env["account.financial.report"]
        roots = Report.search([("parent_id", "=", False)], order="sequence,id")

        if len(roots) == 1 and roots.children_ids:
            reps = roots.children_ids.sorted(key=lambda r: (r.sequence, r.id))
        else:
            reps = roots

        return [{"id": r.id, "name": r.display_name or r.name} for r in reps]

    @api.model
    def get_journals_list(self):
        jnls = self.env["account.journal"].search([("company_id", "=", self.env.company.id)])
        return [{"id": j.id, "name": j.display_name} for j in jnls]

    @api.model
    def get_lines(self, options):
        """Return full lines with current unfolded state."""
        options = self._sanitize_options(options)
        lines = self._compute_lines_from_oca(options)
        return {
            "options": options,
            "lines": lines,
        }

    @api.model
    def toggle_unfold(self, options, line_id):
        """Toggle fold/unfold and return refreshed lines."""
        options = self._sanitize_options(options)
        unfolded = set(options.get("unfolded_line_ids") or [])
        if line_id in unfolded:
            unfolded.remove(line_id)
        else:
            unfolded.add(line_id)
        options["unfolded_line_ids"] = list(unfolded)
        lines = self._compute_lines_from_oca(options)
        return {"options": options, "lines": lines}

    @api.model
    def get_move_lines_action(self, options, line_domain):
        """
        Return action to open journal items filtered by the line domain + options.
        line_domain: domain list from line (JSON) that points to account.move.line
        """
        options = self._sanitize_options(options)
        domain = list(line_domain or [])
        domain += self._aml_domain_from_options(options)

        return {
            "type": "ir.actions.act_window",
            "name": _("Journal Items"),
            "res_model": "account.move.line",
            "view_mode": "tree,form",
            "target": "current",
            "domain": domain,
            "context": {"search_default_group_by_move": 1},
        }

    @api.model
    def export_xlsx(self, options):
        """Return xlsx file content (base64) + filename."""
        if not xlsxwriter:
            raise UserError(_("xlsxwriter not installed on server."))

        options = self._sanitize_options(options)
        lines = self._compute_lines_from_oca(options)

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {"in_memory": True})
        ws = wb.add_worksheet("Report")

        row = 0
        ws.write(row, 0, "Report")
        ws.write(row, 1, self._report_name(options))
        row += 2

        ws.write(row, 0, "Date From")
        ws.write(row, 1, options["date_from"])
        row += 1
        ws.write(row, 0, "Date To")
        ws.write(row, 1, options["date_to"])
        row += 2

        ws.write(row, 0, "Name")
        ws.write(row, 1, "Balance")
        row += 1

        for ln in lines:
            indent = " " * (ln.get("level", 0) * 2)
            ws.write(row, 0, f"{indent}{ln.get('name', '')}")
            ws.write(row, 1, ln.get("balance", 0.0))
            row += 1

        wb.close()
        output.seek(0)

        content = base64.b64encode(output.read()).decode("ascii")
        filename = f"{self._report_name(options)}_{options['date_from']}_{options['date_to']}.xlsx"
        return {"filename": filename, "content": content}

    # ===========
    # Helpers
    # ===========
    def _sanitize_options(self, options):
        options = dict(options or {})
        if not options.get("company_id"):
            options["company_id"] = self.env.company.id

        # ensure report_id exists (respect menu context when missing)
        if not options.get("report_id"):
            report = self._resolve_default_report_from_context()
            options["report_id"] = report.id if report else False

        if not options.get("date_from") or not options.get("date_to"):
            dflt = self.get_default_options()
            options.setdefault("date_from", dflt["date_from"])
            options.setdefault("date_to", dflt["date_to"])

        options.setdefault("journal_ids", [])
        options.setdefault("target_move", "posted")
        options.setdefault("unfolded_line_ids", [])
        return options

    def _report_name(self, options):
        rep = self.env["account.financial.report"].browse(options["report_id"])
        return rep.display_name or "Financial Report"

    def _aml_domain_from_options(self, options):
        dom = []
        if options.get("date_from"):
            dom.append(("date", ">=", options["date_from"]))
        if options.get("date_to"):
            dom.append(("date", "<=", options["date_to"]))
        if options.get("journal_ids"):
            dom.append(("journal_id", "in", options["journal_ids"]))
        if options.get("target_move") == "posted":
            dom.append(("parent_state", "=", "posted"))
        return dom

    # ==========================================================
    # CORE: compute lines using OCA engine (adapter point)
    # ==========================================================
    def _compute_lines_from_oca(self, options):
        report = self.env["account.financial.report"].browse(options["report_id"])
        if not report.exists():
            return []

        ctx = dict(self.env.context)
        ctx.update({
            "date_from": options.get("date_from"),
            "date_to": options.get("date_to"),
            "journal_ids": options.get("journal_ids", []),
            "target_move": options.get("target_move", "posted"),
            "company_id": options.get("company_id") or self.env.company.id,
        })

        raw_lines = None
        report_ctx = report.with_context(ctx)

        if hasattr(report_ctx, "_get_lines"):
            try:
                raw_lines = report_ctx._get_lines()
            except TypeError:
                raw_lines = None

        if raw_lines is None and hasattr(report_ctx, "get_lines"):
            try:
                raw_lines = report_ctx.get_lines()
            except TypeError:
                raw_lines = None

        if raw_lines:
            ui_lines = []
            for line in raw_lines:
                ui_lines.append({
                    "id": f"oca_{line.get('id')}",
                    "name": line.get("name"),
                    "level": line.get("level", 0),
                    "balance": line.get("balance", 0.0),
                    "unfoldable": bool(line.get("unfoldable", False)),
                    "unfolded": False,
                    "parent_id": f"oca_{line.get('parent_id')}" if line.get("parent_id") else None,
                    "domain": line.get("domain", []) or [],
                })
            return self._apply_unfold_and_expand(options, ui_lines)

        ui_lines = self._compute_lines_fallback(report, options)
        return self._apply_unfold_and_expand(options, ui_lines)

    def _apply_unfold_and_expand(self, options, lines):
        unfolded_ids = set(options.get("unfolded_line_ids") or [])

        for ln in lines:
            ln["unfolded"] = ln.get("id") in unfolded_ids

        line_map = {ln["id"]: ln for ln in lines}
        children_by_parent = {}
        for ln in lines:
            pid = ln.get("parent_id")
            if pid:
                children_by_parent.setdefault(pid, []).append(ln)

        def append_line(lid, out):
            ln = line_map[lid]
            out.append(ln)
            if ln.get("unfoldable") and ln.get("unfolded"):
                for ch in children_by_parent.get(lid, []):
                    append_line(ch["id"], out)

        roots = [ln for ln in lines if not ln.get("parent_id")]
        expanded = []
        for r in roots:
            append_line(r["id"], expanded)
        return expanded

    def _compute_lines_fallback(self, report, options):
        aml = self.env["account.move.line"].with_company(self.env.company)
        base_domain = self._aml_domain_from_options(options)

        def sum_balance(account_ids):
            if not account_ids:
                return 0.0
            dom = base_domain + [("account_id", "in", account_ids)]
            res = aml.read_group(dom, ["balance:sum"], [])
            return res[0]["balance_sum"] if res else 0.0

        all_nodes = report.search([("id", "child_of", report.id)], order="sequence,id")

        children = {}
        for n in all_nodes:
            if n.parent_id:
                children.setdefault(n.parent_id.id, []).append(n)

        def get_node_account_ids(node):
            if hasattr(node, "account_ids") and node.account_ids:
                return node.account_ids.ids
            return []

        computed = {}

        def compute_node(node):
            if node.id in computed:
                return computed[node.id]

            acc_ids = get_node_account_ids(node)
            bal = sum_balance(acc_ids) if acc_ids else 0.0

            for ch in children.get(node.id, []):
                bal += compute_node(ch)

            # sign bisa string/selection di beberapa versi OCA
            if hasattr(node, "sign") and node.sign not in (False, None, "", 0):
                try:
                    bal *= float(node.sign)
                except (TypeError, ValueError):
                    pass

            computed[node.id] = bal
            return bal

        for n in all_nodes:
            compute_node(n)

        def make_domain(node):
            acc_ids = get_node_account_ids(node)
            if acc_ids:
                return [("account_id", "in", acc_ids)]
            return []

        def line_id(node):
            return f"fr_{node.id}"

        roots = children.get(report.id, []) or [report]
        ui_lines = []

        def walk(node, level, parent_line_id=None):
            lid = line_id(node)
            has_children = bool(children.get(node.id))

            ui_lines.append({
                "id": lid,
                "node_id": node.id,
                "parent_id": parent_line_id,
                "name": node.name,
                "level": level,
                "balance": float(computed.get(node.id, 0.0)),
                "unfoldable": has_children,
                "unfolded": False,
                "domain": make_domain(node),
            })

            for ch in children.get(node.id, []):
                walk(ch, level + 1, lid)

        for r in roots:
            walk(r, 0, None)

        return ui_lines
