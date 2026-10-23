/** @odoo-module **/

import { Model } from "@web/model/model";

export class PlanModel extends Model {
    setup(params) {
        this.metaData = params;

        this.data = {
            'layoutImageUrl': this.metaData.layoutImageUrl
        }
    }

    async load(params) {
        const metaData = {
            ...this.metaData,
            ...params,
        };

        this.data = await this._fetchData(metaData);
        this.metaData = metaData;
    }

    async _fetchData(metaData) {
        const data = {
            record: null,
            layoutImageUrl: null
        }

        const res = await this._fetchRecordData(metaData);
        data.record = res[0];
        data.isParentLocation = res[0].is_plot_view;
        data.parentLocationId = res[0].location_id[0];
        data.displayName = res[0].name;
        data.layoutImageUrl = res[0][metaData.layoutImageUrlField];
        data.layoutData = JSON.parse(res[0][metaData.layoutDataField]);
        data.tooltipData = JSON.parse(res[0][metaData.tooltipDataField]);

        return data
    }

    _fetchRecordData(metaData) {
        const domain = [
            ["id", "=", metaData.resId]
        ];
        const fields = [
            'name', 
            'location_id',
            'is_plot_view',
            metaData.layoutImageUrlField, 
            metaData.layoutDataField,
            metaData.tooltipDataField
        ];

        return this.orm.searchRead(metaData.resModel, domain, fields, {
            limit: 1
        })
    }

    async saveLayoutData(layoutData) {
        const toWriteLocationId = this.data.isParentLocation ? this.metaData.resId : this.data.parentLocationId;
        await this.orm.write(this.metaData.resModel, [toWriteLocationId], {
            [this.metaData.layoutDataField]: layoutData
        })

    }
}