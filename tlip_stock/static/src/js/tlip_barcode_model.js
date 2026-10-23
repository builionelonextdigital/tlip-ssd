/** @odoo-module **/
import BarcodeModel from '@stock_barcode/models/barcode_model';
import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(BarcodeModel.prototype, {
    async _processBarcode(barcode) {
        if (this.record.picking_internal_code === 'inspect') {
            await this._processStockSerialBarcode(barcode);
        }
        else{
            return await super._processBarcode(barcode);
        }
    },

    async _processStockSerialBarcode(barcode) {
        let self = this;
        let record = this.record;
        
        let stock_serial_lines = this.currentState.lines.filter(
            line => line.barcode == barcode
        )
        if (stock_serial_lines.length > 0){
            let unfinished_qty_lines = stock_serial_lines.filter(
                line => line.qty_done < line.reserved_uom_qty
            );
            if (unfinished_qty_lines.length > 0) {
                let currentLine = unfinished_qty_lines[0];
                let qty_done = currentLine.qty_done + 1;
                await self.updateLine(currentLine, {"qty_done": qty_done});
                self.save();

                self.trigger("playSound", "success");
                self.trigger('flash');
            }
        } else {
            return this.notification(_t("Barcode in Operations cannot not be found"), { type: "danger" });
        }
    }
});
