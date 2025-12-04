/** @odoo-module **/

import { CharField } from "@web/views/fields/char/char_field";
import { patch } from "@web/core/utils/patch";
import { setPendingQuickCreateData, getPendingQuickCreateData } from "./crm_model_patch";

console.log("=== CRM Field Monitor Patch Loaded ===");

// Monitor when fields are updated
patch(CharField.prototype, {
    async commitChanges() {
        const fieldName = this.props.name;
        const fieldValue = this.props.record.data[fieldName];
        const resModel = this.props.record.resModel;
        
        // Only log for CRM lead fields we care about
        if (resModel === 'crm.lead' && 
            (fieldName === 'contact_name' || fieldName === 'email_from' || fieldName === 'phone')) {
            console.log(`=== Field ${fieldName} changed ===`);
            console.log("New value:", fieldValue);
            console.log("Record data:", this.props.record.data);
            console.log("Record resId:", this.props.record.resId);
            
            // If this is a new record (no resId), capture the data
            if (!this.props.record.resId || this.props.record.resId < 0) {
                console.log("!!! This is a new record, capturing data !!!");
                
                // Get current pending data or create new
                const currentData = getPendingQuickCreateData() || {};
                
                // Update with new value
                const updatedData = {
                    ...currentData,
                    contact_name: this.props.record.data.contact_name,
                    email_from: this.props.record.data.email_from,
                    phone: this.props.record.data.phone,
                };
                
                console.log("Updated pending data:", updatedData);
                setPendingQuickCreateData(updatedData);
            }
        }
        
        return super.commitChanges();
    }
});