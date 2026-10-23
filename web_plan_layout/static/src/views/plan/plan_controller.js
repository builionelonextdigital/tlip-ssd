/** @odoo-module **/

import { loadJS, loadCSS } from "@web/core/assets";
import { Layout } from "@web/search/layout";
import { useModel } from "@web/model/model";
import { standardViewProps } from "@web/views/standard_view_props";
import { Component, onWillStart, onRendered, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class PlanController extends Component {
    setup() {
        this.model = useModel(this.props.Model, this.props.modelParams);
        this.state = useState({
            isEditing: false,
            isSaving: false,
            isDiscard: false
        });

        onWillStart(async () => {
            await Promise.all([this.loadJsFiles(), this.loadCssFiles()]);
            await this.model.load();
        });

        onRendered(() => {
            this.env.config.setDisplayName(this.displayName());
        });
    }

    async loadJsFiles() {
        const files = [
            "/web_plan_layout/static/src/lib/leaflet/leaflet.js",
            "/web_plan_layout/static/src/lib/leaflet_draw/leaflet.draw.js",
        ];

        for (const file of files) {
            await loadJS(file);
        }
    }

    async loadCssFiles() {
        await Promise.all(
            [
                "/web_plan_layout/static/src/lib/leaflet/leaflet.css",
                "/web_plan_layout/static/src/lib/leaflet_draw/leaflet.draw.css",
            ].map((file) => loadCSS(file))
        );
    }

    get rendererProps() {
        return {
            model: this.model,
            locationList: this.getLocationList(),
            isParentLocation: this.model.data.isParentLocation,
            resModel: this.model.metaData.resModel,
            enableDrawControl: this.model.metaData.mode === 'editable' && this.state.isEditing,
            isSaving: this.state.isSaving,
            discard: this.state.isDiscard,
            onEdit: this.onClickEdit.bind(this),
            onSave: this.saveLayoutData.bind(this)
        };
    }

    get display() {
        const { controlPanel } = this.props.display;
        return {
            ...this.props.display,
            controlPanel: {
                ...controlPanel,
                "top-left": true,
                "bottom-left": true,
            },
        };
    }

    displayName() {
        return this.model.data.displayName || _t("New");
    }

    get isEditing() {
        return this.state.isEditing;
    }

    async onClickEdit() {
        this.state.isEditing = true;
        this.state.isDiscard = false;
        this.state.isSaving = false;
    }

    async onClickSave() {
        this.state.isEditing = false;
        this.state.isSaving = true;
    }

    async onClickDiscard() {
        this.state.isEditing = false;
        this.state.isDiscard = true;
    }

    getLocationList() {
        if (!this.model.data.tooltipData) return [];
        return this.model.data.tooltipData.map((locationData) => {
            return {
                id: locationData.location_id, 
                name: locationData.location_name
            }
        });
    }

    async saveLayoutData(layoutData) {
        await this.model.saveLayoutData(layoutData);
    }
}

PlanController.template = "web_plan_layout.PlanView";

PlanController.components = { Layout };

PlanController.props = {
    ...standardViewProps,
    showButtons: { type: Boolean, optional: true },
    Model: Function,
    modelParams: Object,
    Renderer: Function,
    buttonTemplate: String
};

PlanController.defaultProps = {
    showButtons: true
};
