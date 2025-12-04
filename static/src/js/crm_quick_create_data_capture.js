/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { browser } from "@web/core/browser/browser"; 

console.log("=== CRM Quick Create Data Capture v12 (FETCH API) Loaded ===");

// Global storage (DOM Hack remains the same)
let quickCreateDataStore = { latest: null };

// --- 1. DOM HACK: Capture data on 'Add' button click (Same as before) ---
// [NOTE: Keep the function body from your previous working code here]
function captureQuickCreateData(ev) {
    // ... (Your existing captureQuickCreateData function) ...
    const target = ev.target.closest('.o_kanban_add'); 
    
    if (target) {
        const partnerInput = document.getElementById('partner_id_0');
        const emailInput = document.getElementById('email_from_0');
        const phoneInput = document.getElementById('phone_0');
        let contactName = partnerInput ? partnerInput.value : ''; 
        let email = emailInput ? emailInput.value : '';
        let phone = phoneInput ? phoneInput.value : '';

        if (contactName || email || phone) {
            console.log("!!! HACK: CAPTURING DATA VIA DOM CLICK LISTENER SUCCESS !!!");
            quickCreateDataStore.latest = {
                contact_name: contactName,
                email_from: email,
                phone: phone,
                timestamp: Date.now()
            };
            console.log("Captured data:", quickCreateDataStore.latest);
        }
    }
}

document.addEventListener('click', captureQuickCreateData, true); 


// --- 2. Patch RelationalModel to inject stored data and perform FETCH API search ---

patch(RelationalModel.prototype, {
    async load(params = {}) {
        console.log("=== RelationalModel.load Called ===");
        
        const result = await super.load(params);
        
        if (this.config?.resModel === 'crm.lead' && this.root?.data && !this.root.resId) {
            
            if (quickCreateDataStore.latest) {
                
                const dataToInject = quickCreateDataStore.latest;
                const recencyThreshold = 3000;
                const isRecent = (Date.now() - dataToInject.timestamp) < recencyThreshold; 

                if (isRecent) {
                    console.log("!!! INJECTING DATA AND SEARCHING FOR PARTNER VIA FETCH API !!!");
                    
                    const changes = {};
                    let partnerId = false;
                    const contactName = dataToInject.contact_name;

                    // 1. FETCH API SEARCH for existing Partner
                    if (contactName) {
                        try {
                            const payload = {
                                jsonrpc: "2.0",
                                method: "call",
                                params: {
                                    model: "res.partner",
                                    method: "search_read",
                                    args: [[['name', '=', contactName]]],
                                    kwargs: { fields: ['id', 'display_name'], limit: 1 },
                                },
                            };

                            const response = await fetch("/web/dataset/call_kw", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify(payload),
                            });
                            
                            const data = await response.json();
                            
                            if (data.result && data.result.length > 0) {
                                partnerId = data.result[0].id;
                                console.log(`Partner found via FETCH! ID: ${partnerId}`);
                            } else {
                                console.log("Partner not found via FETCH. Lead Name will be used.");
                            }
                        } catch (e) {
                            console.error("FETCH API Search failed:", e);
                        }
                    }

                    // 2. Prepare Model Updates
                    if (partnerId) {
                        // Set the Many2One field with the [ID, NAME] tuple
                        changes.partner_id = [partnerId, contactName];
                    }
                    
                    // Always set the primary lead name field
                    if (!this.root.data.name) { changes.name = contactName; }
                    
                    // Set Email and Phone
                    if (!this.root.data.email_from) { changes.email_from = dataToInject.email_from; }
                    if (!this.root.data.phone) { changes.phone = dataToInject.phone; }
                    
                    // 3. Apply changes and wait for framework updates
                    if (Object.keys(changes).length > 0) {
                        console.log("Applying changes:", changes);
                        await this.root.update(changes); 
                        this.notify(); 
                        console.log("Injection and Model update complete.");
                    }
                    
                    quickCreateDataStore.latest = null;
                } else {
                    quickCreateDataStore.latest = null;
                }
            }
        }
        
        return result;
    }
});
// /** @odoo-module **/

// import { patch } from "@web/core/utils/patch";
// import { RelationalModel } from "@web/model/relational_model/relational_model";

// console.log("=== CRM Quick Create Data Capture v9 (Final Fix) Loaded ===");


// let quickCreateDataStore = { latest: null };

// function captureQuickCreateData(ev) {
    
//     const target = ev.target.closest('.o_kanban_add'); 
    
//     if (target) {
        
        
//         const partnerInput = document.getElementById('partner_id_0');
//         const emailInput = document.getElementById('email_from_0');
//         const phoneInput = document.getElementById('phone_0');

//         let contactName = ''; 
//         let email = '';
//         let phone = '';

//         if (partnerInput) {
//             contactName = partnerInput.value;
//         }
//         if (emailInput) {
//             email = emailInput.value;
//         }
//         if (phoneInput) {
//             phone = phoneInput.value;
//         }

//         if (contactName || email || phone) {
//             console.log("!!! HACK: CAPTURING DATA VIA DOM CLICK LISTENER SUCCESS !!!");
            
//             quickCreateDataStore.latest = {
//                 contact_name: contactName,
//                 email_from: email,
//                 phone: phone,
//                 timestamp: Date.now()
//             };
            
//             console.log("Captured data:", quickCreateDataStore.latest);
//         }
//     }
// }

// document.addEventListener('click', captureQuickCreateData, true); 


// patch(RelationalModel.prototype, {
//     async load(params = {}) {
//         console.log("=== RelationalModel.load Called ===");
        
//         const result = await super.load(params);
        
//         if (this.config?.resModel === 'crm.lead' && this.root?.data && !this.root.resId) {
            
//             if (quickCreateDataStore.latest) {
                
//                 const dataToInject = quickCreateDataStore.latest;
//                 const recencyThreshold = 3000;
//                 const isRecent = (Date.now() - dataToInject.timestamp) < recencyThreshold; 

//                 if (isRecent) {
//                     console.log("!!! INJECTING DATA VIA MODEL.CHANGE (FINAL ATTEMPT) !!!");
                    
//                     const changes = {};

//                     if (!this.root.data.partner_name) {
//                         changes.partner_name = dataToInject.contact_name;
//                         changes.partner_id = dataToInject.contact_name
//                     }
//                     if (!this.root.data.phone) {
//                         changes.phone = dataToInject.phone;
//                     }
//                     if (!this.root.data.email_from) {
//                         changes.email_from = dataToInject.email_from;
//                     }
                    
//                     if (Object.keys(changes).length > 0) {
//                         console.log("Applying changes via this.root.update (or change):", changes);

//                         await this.root.update(changes); 
                        
//                         console.log("Update complete. Checking final values:");
//                         console.log("Partner Name (Source):", this.root.data.partner_name);
//                         console.log("Email From (Source):", this.root.data.email_from);
  
//                         this.notify(); 
//                     }
                    
//                     quickCreateDataStore.latest = null;
//                     console.log("Injection and Model update complete.");
//                 } else {
//                     quickCreateDataStore.latest = null;
//                 }
//             }
//         }
        
//         return result;
//     }
// });
// console.log("=== CRM Quick Create Data Capture Module Ready (Fixed Source) ===");
