/** @odoo-module */

import { registry } from "@web/core/registry";
import { PlanController } from "./plan_controller";
import { PlanRenderer } from "./plan_renderer";
import { PlanModel } from "./plan_model";
import { PlanArchParser } from "./plan_arch_parser";

export const PlanView = {
    type: "plan",
    display_name: "Plan",
    multiRecord: false,
    Controller: PlanController,
    Renderer: PlanRenderer,
    ArchParser: PlanArchParser,
    Model: PlanModel,
    buttonTemplate: "web_plan_layout.PlanView.Buttons",

    props: (genericProps, view) => {
        let modelParams;
        if (genericProps.state) {
            modelParams = genericProps.state.metaData;
        } else {
            const { arch, fields, resModel } = genericProps;
            const parser = new view.ArchParser();
            const archInfo = parser.parse(arch, fields);

            modelParams = {
                ...genericProps,
                resModel: resModel,
                fields: fields,
                layoutImageUrlField: archInfo.layoutImageUrlField,
                layoutDataField: archInfo.layoutDataField,
                tooltipDataField: archInfo.tooltipDataField,
                mode: archInfo.mode,
            }
        }

       
        return {
            ...genericProps,
            Model: view.Model,
            modelParams,
            Renderer: view.Renderer,
            buttonTemplate: genericProps.buttonTemplate || view.buttonTemplate,
            display: { controlPanel: true },
        };
    },
};

registry.category("views").add("plan", PlanView);
