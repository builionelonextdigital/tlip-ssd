import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
import { patch } from "@web/core/utils/patch";
import { downloadReport } from "@web/webclient/actions/reports/utils";
import { user } from "@web/core/user";
import { download } from "@web/core/network/download";


patch(PivotRenderer.prototype, {
    setup() {
        super.setup(...arguments);
    },

    onDownloadSpecificReport() {
        if (this.model.getTableWidth() > 16384) {
            throw new Error(
                _t(
                    "For Excel compatibility, data cannot be exported if there are more than 16384 columns.\n\nTip: try to flip axis, filter further or reduce the number of measures."
                )
            );
        }
        let table = this.model.exportData();
        table.title = this.getSpecificReportName()
        download({
            url: "/budget/export/export_xlsx",
            data: { data: JSON.stringify(table) },
        });
    },

    // async downloadSpecificReport() {
    //     let actionContext = this.model.searchParams.context;
    //     let analyticReportName = actionContext.analytic_report_name;
    //     let analyticReportXML = actionContext.analytic_report_xml; 
    //     if (analyticReportXML === undefined) {return;}
    //     try {
    //         await download({
    //             url: '/budget/export/analytic/',
    //             data: {
    //                 report_data: JSON.stringify({
    //                     'analytic_report_name': analyticReportName,
    //                     'analytic_report_xml': analyticReportXML
    //                 }),
    //             }
    //         });
    //     } catch (error) {
    //         console.error(`Error exporting ${format.toUpperCase()} file:`, error);
    //         await this.action.doAction(
    //             sendCustomNotification(
    //                 "danger",
    //                 _t("Error exporting file. Please try again.")
    //             )
    //         );
    //     }
    // },

    showDownloadBudgetReport() {
        return (this.model.searchParams.context.download_analytic_report !== undefined);
    },

    getSpecificReportName() {
        return this.model.searchParams.context.analytic_report_name;
    },
});
