/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { FinancialReportLiveAPI } from "./report_service";

class FinancialReportLiveAction extends Component {
    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            options: {},
            lines: [],
            reports: [],
            journals: [],
        });

        onWillStart(async () => {
            const boot = await FinancialReportLiveAPI.bootstrap();
            this.state.options = boot.default_options;
            this.state.reports = boot.reports;
            this.state.journals = boot.journals;

            const res = await FinancialReportLiveAPI.getLines(this.state.options);
            this.state.options = res.options;
            this.state.lines = res.lines;
            this.state.loading = false;
        });
    }

    async refresh() {
        this.state.loading = true;
        const res = await FinancialReportLiveAPI.getLines(this.state.options);
        this.state.options = res.options;
        this.state.lines = res.lines;
        this.state.loading = false;
    }

    async onToggleUnfold(line) {
        if (!line.unfoldable) return;
        const res = await FinancialReportLiveAPI.toggleUnfold(this.state.options, line.id);
        this.state.options = res.options;
        this.state.lines = res.lines;
    }

    async onOpenJournalItems(line) {
        if (!line.domain || !line.domain.length) {
            this.notification.add("No drilldown on this line.", { type: "warning" });
            return;
        }
        const action = await FinancialReportLiveAPI.openMoveLines(this.state.options, line.domain);
        await this.actionService.doAction(action);
    }
}

FinancialReportLiveAction.template = "account_financial_report_live.ReportAction";
registry.category("actions").add("financial_report_live.action", FinancialReportLiveAction);
