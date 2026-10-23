/** @odoo-module */

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

async function executeAccountReportDownload({ env, action }) {
    console.log("Custom download")
    env.services.ui.block();
    const url = "/account_public_diary";
    const data = action.data;
    try {
        await download({ url, data });
    } finally {
        env.services.ui.unblock();
    }
}

registry.category("action_handlers").add('ir_actions_account_public_diary', executeAccountReportDownload);
