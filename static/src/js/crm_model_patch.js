/** @odoo-module **/

import { RelationalModel } from "@web/model/relational_model/relational_model";
import { patch } from "@web/core/utils/patch";

console.log("=== CRM Model Patch Loaded ===");

// Store the data from quick create
let pendingQuickCreateData = null;

patch(RelationalModel.prototype, {
    
    async load(params = {}) {
        console.log("=== RelationalModel load ===");
        console.log("ResModel:", this.config?.resModel);
        console.log("Params:", params);
        console.log("Context:", this.config?.context);
        console.log("Pending quick create data:", pendingQuickCreateData);
        
        // If we're loading a CRM lead form and have pending data, inject it into context
        if (this.config?.resModel === 'crm.lead' && pendingQuickCreateData) {
            console.log("!!! INJECTING PENDING DATA INTO LOAD CONTEXT !!!");
            
            // Modify the config context to include default values
            if (!this.config.context) {
                this.config.context = {};
            }
            
            this.config.context.default_contact_name = pendingQuickCreateData.contact_name;
            this.config.context.default_email_from = pendingQuickCreateData.email_from;
            this.config.context.default_phone = pendingQuickCreateData.phone;
            
            console.log("Modified config context:", this.config.context);
            
            // Clear the pending data
            pendingQuickCreateData = null;
        }
        
        const result = await super.load(params);
        console.log("Load completed");
        return result;
    },
    
    async save(recordId, { reload = true, onError, stayInEdition } = {}) {
        console.log("=== RelationalModel save called ===");
        console.log("Record ID:", recordId);
        
        const record = this.root.data?.records?.[recordId] || this.root;
        console.log("Record being saved:", record);
        console.log("Record data:", record?.data);
        
        // If this is a CRM lead being saved from quick create
        if (this.config?.resModel === 'crm.lead' && record?.data) {
            console.log("CRM Lead is being saved!");
            console.log("Contact:", record.data.contact_name);
            console.log("Email:", record.data.email_from);
            console.log("Phone:", record.data.phone);
            
            // Store the data for when form opens
            if (record.data.contact_name || record.data.email_from || record.data.phone) {
                pendingQuickCreateData = {
                    contact_name: record.data.contact_name,
                    email_from: record.data.email_from,
                    phone: record.data.phone,
                };
                console.log("Stored pending quick create data:", pendingQuickCreateData);
                
                // Set a timeout to clear it after 10 seconds
                setTimeout(() => {
                    console.log("Clearing pending quick create data (timeout)");
                    pendingQuickCreateData = null;
                }, 10000);
            }
        }
        
        const result = await super.save(recordId, { reload, onError, stayInEdition });
        console.log("Save completed, result:", result);
        
        return result;
    }
});

// Export for use by other patches
export function getPendingQuickCreateData() {
    return pendingQuickCreateData;
}

export function setPendingQuickCreateData(data) {
    console.log("=== setPendingQuickCreateData called ===");
    console.log("Data:", data);
    pendingQuickCreateData = data;
}

export function clearPendingQuickCreateData() {
    pendingQuickCreateData = null;
}