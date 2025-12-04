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
        
        return super.load(params);
    },
    
    async save(recordId, { reload = true, onError, stayInEdition } = {}) {
        console.log("=== RelationalModel save called ===");
        console.log("Record ID:", recordId);
        
        const record = this.root.data.records?.[recordId] || this.root;
        console.log("Record being saved:", record);
        console.log("Record data:", record.data);
        
        // If this is a CRM lead being saved from quick create
        if (this.config?.resModel === 'crm.lead' && record.data) {
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
                
                // Set a timeout to clear it after 5 seconds
                setTimeout(() => {
                    console.log("Clearing pending quick create data");
                    pendingQuickCreateData = null;
                }, 5000);
            }
        }
        
        const result = await super.save(recordId, { reload, onError, stayInEdition });
        console.log("Save completed, result:", result);
        
        return result;
    },
    
    async createNewRecord(params = {}) {
        console.log("=== createNewRecord called ===");
        console.log("Params:", params);
        console.log("Pending data:", pendingQuickCreateData);
        
        // If we have pending quick create data, add it to context
        if (pendingQuickCreateData && this.config?.resModel === 'crm.lead') {
            console.log("Injecting quick create data into new record context");
            
            params.context = {
                ...params.context,
                default_contact_name: pendingQuickCreateData.contact_name,
                default_email_from: pendingQuickCreateData.email_from,
                default_phone: pendingQuickCreateData.phone,
            };
            
            console.log("Modified params:", params);
        }
        
        return super.createNewRecord(params);
    }
});

// Export for use by other patches
export function getPendingQuickCreateData() {
    return pendingQuickCreateData;
}

export function clearPendingQuickCreateData() {
    pendingQuickCreateData = null;
}