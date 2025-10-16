/** @odoo-module **/

import { registry } from "@web/core/registry";

function closeLeadFormAction(env, action) {
    const { title, message } = action.params || {};

    // Show notification
    env.services.notification.add(message || "Lead saved successfully!", {
        title: title || "Success",
        type: "success",
    });

    // Close form after short delay
        setTimeout(() => {
        window.history.back();
    }, 800);
}

console.log("✅ closeLeadFormAction loaded");

registry.category("actions").add("close_lead_form", closeLeadFormAction);
