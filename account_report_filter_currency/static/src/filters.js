/** @odoo-module **/

import { RecordSelector } from "@web/core/record_selectors/record_selector";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { patch } from "@web/core/utils/patch";

patch(AccountReportFilters, {
    components: { ...AccountReportFilters.components,RecordSelector }  
})
patch(AccountReportFilters.prototype, {
    getValueRecordSelectorProps(resModel, optionKey) {
        return {
            resModel,
            resId: this.controller.options[optionKey],
            update: (resId) => {
                this.filterClicked({ optionKey: optionKey, optionValue: resId, reload: true});
            },
        };
    }
})