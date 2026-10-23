/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";


class WaitingDialog extends Component {
    static template = "pcv_mysign.WaitingDialog";
    static components = { Dialog };
    static props = ["title", "body", "close"];
}


class MySignPopup extends Component {
    static template = "pcv_mysign.MySignPopup";
    static components = { WaitingDialog, Dialog };
    static props = ["action", "actionStack?", "*"];

    setup() {
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.signerIds = this.props.action.context.signer_ids || [];
    }

    _closePopup() {
        this.actionService.doAction({ type: "ir.actions.act_window_close" });
    }

    _cancel() {
        this._closePopup();
    }

    async _confirm() {
        this._closePopup();

        let closeWaiting;
        const waitingClosed = new Promise((resolve) => {
            closeWaiting = this.dialogService.add(
                WaitingDialog,
                {
                    title: _t("MySign Authentication"),
                    body: _t("Waiting for MySign authentication..."),
                },
                { onClose: resolve }
            );
        });

        await Promise.all(
            this.signerIds.map((id) =>
                rpc("/web/dataset/call_kw", {
                    model: "sign.ticket.signer",
                    method: "send_request_to_mysign",
                    args: [id],
                    kwargs: {},
                })
            )
        );

        let result;
        try {
            result = await rpc("/mysign/sign", { signer_ids: this.signerIds });
        } catch (err) {
            result = { error: err.message || String(err) };
            rpc("/mysign/log", { signer_ids: this.signerIds, error: result.error }).catch(() => {});
        }

        closeWaiting();
        await waitingClosed;
    }
}

registry.category("actions").add("mysign_popup", MySignPopup);
