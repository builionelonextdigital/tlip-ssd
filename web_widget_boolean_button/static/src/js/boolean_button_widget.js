/** @odoo-module */

import { BooleanField } from "@web/views/fields/boolean/boolean_field";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";

export class BooleanButtonField extends Component {
    static template = "web_widget_boolean_button.FieldBooleanButton";
    static components = { BooleanField };

    static defaultProps = {
        ...BooleanField.defaultProps,
        terminology: {},
        multiLines: false,
    };

    setup() {
        super.setup();
    }

    get text() {
        const term = this.props.terminology;
        return this.getTermFor(term.stringTrue, term.stringFalse);
    }

    get hover() {
        const term = this.props.terminology;
        return this.getTermFor(term.hoverTrue, term.hoverFalse);
    }

    getTermFor(termTrue, termFalse) {
        let res = this.props.value ? termTrue : termFalse;
        if (this.props.multiLines) {
            res = String(res).split('\n');
        }
        return res;
    }

    get textColor() {
        return this.props.value 
            ? this.props.terminology.textColorTrue 
            : this.props.terminology.textColorFalse;
    }

    get hoverColor() {
        return this.props.value 
            ? this.props.terminology.hoverColorTrue 
            : this.props.terminology.hoverColorFalse;
    }
}

export const booleanButtonField = {
    component: BooleanButtonField,
    extractProps: ({ attrs, options }) => {
        let terminology = options.terminology || {};
        
        switch (terminology) {
            case "active":
                terminology = {
                    string_true: _t("Active"),
                    string_false: _t("Inactive"),
                    hover_true: _t("Deactivate"),
                    hover_false: _t("Activate")
                };
                break;
            case "archive":
                terminology = {
                    string_true: _t("Active"),
                    string_false: _t("Archived"),
                    hover_true: _t("Archive"),
                    hover_false: _t("Restore")
                };
                break;
            case "close":
                terminology = {
                    string_true: _t("Active"),
                    string_false: _t("Closed"),
                    hover_true: _t("Close"),
                    hover_false: _t("Open")
                };
                break;
        }

        if (typeof terminology === 'string') {
            terminology = {};  // Unsupported terminology
        }

        terminology = {
            stringTrue: terminology.string_true || _t("Active"),
            stringFalse: terminology.string_false || _t("Off"),
            hoverTrue: terminology.hover_true || _t("Switch Off"),
            hoverFalse: terminology.hover_false || _t("Switch On"),
            textColorTrue: 'text-success',
            textColorFalse: 'text-danger',
            hoverColorTrue: 'text-danger',
            hoverColorFalse: 'text-success'
        };

        return {
            terminology,
            multiLines: options.multi_lines || false
        };
    }
};

registry.category("fields").add("boolean_button", booleanButtonField);