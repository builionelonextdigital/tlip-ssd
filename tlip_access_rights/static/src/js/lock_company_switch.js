/** @odoo-module **/

import { onWillStart } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";

/**
 * -------------------------------------------------------------------------
 * Patch SwitchCompanyMenu
 * -------------------------------------------------------------------------
 * Goal:
 *  - Admin: normal behavior
 *  - Non-admin:
 *      • NO dropdown
 *      • NO list
 *      • NO click
 *      • ONLY show current company name
 * -------------------------------------------------------------------------
 */
patch(SwitchCompanyMenu.prototype, {
    async setup() {
        super.setup();

        this.companyService = useService("company");
        onWillStart(async () => {
            // Resolve admin flag ONCE
            this.isAdmin = await user.hasGroup("base.group_system");
            this.canSwitchCompany = await user.hasGroup(
                "tlip_access_rights.group_tlip_allow_multi_company"
            );
        });
    },

    /**
     * Force single-company UI for users without permission
     */
    get isSingleCompany() {
        if (!this.isAdmin && !this.canSwitchCompany) {
            return true; // forces non-dropdown rendering
        }
        return super.isSingleCompany;
    },

    /**
     * NON-ADMIN: block dropdown open
     */
    handleDropdownChange(isOpen) {
        if (!this.isAdmin) {
            return;
        }
        return super.handleDropdownChange(isOpen);
    },
});
