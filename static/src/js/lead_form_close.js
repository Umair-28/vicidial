/** @odoo-module **/

import { registry } from "@web/core/registry";

function closeLeadFormAction(env, action) {
    const { title, message, messages } = action.params || {};

    const displayDuration = 4000; // 8 seconds

    // Show single or multiple notifications
    if (Array.isArray(messages)) {
        messages.forEach((msg) => {
            env.services.notification.add(msg, {
                title: title || "Success",
                type: "success",
                duration:displayDuration
            });
        });
    } else {
        env.services.notification.add(message || "Lead saved successfully!", {
            title: title || "Success",
            type: "success",
        });
    }

    // Close form after short delay
    setTimeout(() => {
        window.history.back();
    }, 1200);
}

console.log("✅ closeLeadFormAction loaded");

registry.category("actions").add("close_lead_form", closeLeadFormAction);

// /** @odoo-module **/

// import { registry } from "@web/core/registry";

// function closeLeadFormAction(env, action) {
//     const { title, message } = action.params || {};

//     // Show notification
//     env.services.notification.add(message || "Lead saved successfully!", {
//         title: title || "Success",
//         type: "success",
//     });

//     // Close form after short delay
//         setTimeout(() => {
//         window.history.back();
//     }, 800);
// }

// console.log("✅ closeLeadFormAction loaded");

// registry.category("actions").add("close_lead_form", closeLeadFormAction);
