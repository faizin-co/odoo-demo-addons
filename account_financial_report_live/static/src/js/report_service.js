/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

export const FinancialReportLiveAPI = {
    bootstrap() {
        return rpc("/financial_report_live/bootstrap", {});
    },
    getLines(options) {
        return rpc("/financial_report_live/lines", { options });
    },
    toggleUnfold(options, lineId) {
        return rpc("/financial_report_live/toggle_unfold", { options, line_id: lineId });
    },
    openMoveLines(options, lineDomain) {
        return rpc("/financial_report_live/move_lines_action", { options, line_domain: lineDomain });
    },
};
