/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";
import { setPendingQuickCreateData } from "./crm_model_patch";

console.log("=== CRM Kanban Quick Create Patch Loaded ===");

// Patch Kanban Controller
patch(KanbanController.prototype, {
    setup() {
        console.log("=== KanbanController setup called ===");
        super.setup(...arguments);
    },
    
    async openRecord(record, mode) {
        console.log("=== KanbanController openRecord called ===");
        console.log("Record:", record);
        console.log("Record resId:", record?.resId);
        console.log("Record data:", record?.data);
        console.log("Mode:", mode);
        
        // If this is a new record (no resId or negative resId) from CRM
        if (this.props.resModel === 'crm.lead' && record?.data) {
            const isNewRecord = !record.resId || record.resId < 0;
            console.log("Is new record:", isNewRecord);
            
            if (isNewRecord) {
                // Capture the quick create data
                const quickData = {
                    contact_name: record.data.contact_name,
                    email_from: record.data.email_from,
                    phone: record.data.phone,
                };
                
                console.log("!!! CAPTURING QUICK CREATE DATA !!!");
                console.log("Quick data:", quickData);
                
                // Store it for the next form load
                setPendingQuickCreateData(quickData);
            }
        }
        
        return super.openRecord(record, mode);
    },
    
    async createRecord(params = {}) {
        console.log("=== KanbanController createRecord called ===");
        console.log("Params:", params);
        console.log("Props:", this.props);
        console.log("Model:", this.model);
        
        // Try to capture data from model if available
        if (this.model && this.model.root && this.props.resModel === 'crm.lead') {
            console.log("Model root:", this.model.root);
            console.log("Model root data:", this.model.root.data);
        }
        
        const result = await super.createRecord(params);
        console.log("createRecord result:", result);
        
        return result;
    }
});