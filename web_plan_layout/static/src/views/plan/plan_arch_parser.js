/** @odoo-module **/

import { unique } from "@web/core/utils/arrays";
import { visitXML } from "@web/core/utils/xml";

export class PlanArchParser {
    parse(arch) {
        const archInfo = {
            fieldNames: []
        };

        visitXML(arch, (node) => {
            switch (node.tagName) {
                case "plan":
                    this.visitPlan(node, archInfo);
                    break;
                case "field":
                    this.visitField(node, archInfo);
                    break;
            }
        });

        archInfo.fieldNames = unique(archInfo.fieldNames);
        
        return archInfo;
    }

    visitPlan(node, archInfo) {
        if (node.hasAttribute("layout_image_url")) {
            archInfo.layoutImageUrlField = node.getAttribute("layout_image_url");
            archInfo.fieldNames.push(archInfo.layoutImageUrlField);
        }
        if (node.hasAttribute("mode")) {
            archInfo.mode = node.getAttribute("mode");
        }
        if (node.hasAttribute("layout_data")) {
            archInfo.layoutDataField = node.getAttribute("layout_data");
            archInfo.fieldNames.push(archInfo.layoutDataField);
        }
        if (node.hasAttribute("tooltip_data")) {
            archInfo.tooltipDataField = node.getAttribute("tooltip_data");
            archInfo.fieldNames.push(archInfo.tooltipDataField);
        }
    }

    visitField(node, archInfo) {
        archInfo.fieldNames.push(node.getAttribute("name"));
    }
}
