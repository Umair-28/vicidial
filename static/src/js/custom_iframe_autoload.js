/** @odoo-module **/

import { Component, onMounted, onWillUnmount, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

console.log("[VICIDIAL] Loading custom_iframe_autoload.js module...");

// ---------------- Widget Class ----------------

export class LeadAutoRefreshMany2Many extends Component {
  static template = xml`
    <div class="o_field_widget">
      <span>Auto-refresh active</span>
    </div>
  `;

  setup() {}

  reloadField() {
    console.log("[lead_auto_refresh_m2m] Reloading field...");
    try {
      if (this.env && this.env.model) {
        this.env.model.load();
        console.log("[lead_auto_refresh_m2m] Field reloaded successfully");
      }
    } catch (error) {
      console.error("[lead_auto_refresh_m2m] Error reloading field:", error);
    }
  }
}

// ---------------- Table Renderer ----------------

const renderer = (item) => `
<tr class="o_data_row" data-id="datapoint_${item.id}" data-vicidial-id="${item.crm_lead_id}">
  <td class="o_data_cell cursor-pointer o_field_cell o_list_char o_required_modifier" name="name">${
    item.first_name || item.opportunity || item.comments || ""
  }</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="partner_name">${
    item.companyName || "K N K TRADERS"
  }</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="phone">${
    item.phone_number || item.alt_phone || ""
  }</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="stage_id">${
    item.stage_id ? item.stage_id.name : "New"
  }</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="user_id">${
    item.user || ""
  }</td>
  <td class="o_list_record_remove w-print-0 p-print-0 text-center">
    <button class="fa d-print-none fa-times" name="delete" aria-label="Delete row"></button>
  </td>
</tr>
`;

// ---------------- Modal Logic ----------------

async function showModalWithLeadData(leadId) {
  try {
    const env = owl.Component.env;
    const actionService = env.services.action;

    console.log("[showModalWithLeadData] Opening CRM lead with ID:", leadId);

    await actionService.doAction({
      type: "ir.actions.act_window",
      res_model: "crm.lead",
      res_id: parseInt(leadId),
      views: [[false, "form"]],
      target: "new",
      fullscreen: true,
      context: {
        default_services: "false",
      },
    });

    // Wait a bit for the modal to load before trying to set field values
    setTimeout(() => {
      const waitForFieldAndSetValue = () => {
        const select = document.querySelector("#services_0");
        if (select) {
          select.value = "false";
          select.dispatchEvent(new Event("change", { bubbles: true }));
          console.info("✅ 'services' field forcibly reset to 'false'");
        } else {
          console.warn("⏳ Waiting for services field...");
          setTimeout(waitForFieldAndSetValue, 100);
        }
      };
      waitForFieldAndSetValue();
    }, 500);

  } catch (error) {
    console.error("[lead_modal] Error loading form modal:", error);
    alert("Failed to open lead modal. Please check the console for details.");
  }
}

// 🎯 FIXED: Corrected function to properly find and open CRM lead
async function openCustomModal(vicidialLeadId) {
  console.log("[openCustomModal] Starting with vicidialLeadId:", vicidialLeadId);
  
  try {
    const orm = owl.Component.env.services.orm;
    
    // 🎯 FIX 1: Search the crm.lead model using the vicidial_lead_id field
    console.log("[openCustomModal] Searching for CRM lead with vicidial_lead_id:", vicidialLeadId);
    
    const crmLeadData = await orm.searchRead(
      'crm.lead', 
      [['vicidial_lead_id', '=', parseInt(vicidialLeadId)]], 
      ['id', 'name', 'vicidial_lead_id']
    );

    console.log("[openCustomModal] CRM lead search result:", crmLeadData);
    
    // Check if the record was found
    if (crmLeadData.length === 0) {
        console.error("[openCustomModal] No corresponding CRM lead found for vicidial_lead_id:", vicidialLeadId);
        
        // 🎯 FIX 2: Try to find the vicidial lead to get more info
        const vicidialLeadData = await orm.searchRead(
          'vicidial.lead', 
          [['id', '=', parseInt(vicidialLeadId)]], 
          ['id', 'lead_id', 'crm_lead_id']
        );
        
        console.log("[openCustomModal] Vicidial lead data:", vicidialLeadData);
        
        if (vicidialLeadData.length > 0 && vicidialLeadData[0].crm_lead_id) {
          // Try using the crm_lead_id directly
          const crmLeadId = vicidialLeadData[0].crm_lead_id[0]; // Many2one field returns [id, name]
          console.log("[openCustomModal] Found CRM lead ID via crm_lead_id field:", crmLeadId);
          await showModalWithLeadData(crmLeadId);
          return;
        }
        
        alert("This lead cannot be opened in CRM. The corresponding record is missing or deleted.");
        return;
    }
    
    // Extract the integer ID of the CRM lead
    const crmLeadId = crmLeadData[0].id;
    console.log("[openCustomModal] Found CRM lead ID:", crmLeadId);
    
    await showModalWithLeadData(crmLeadId);

  } catch (err) {
    console.error("[openCustomModal] Failed to open lead modal:", err);
    alert("Error opening lead modal: " + err.message);
  }
}

// ---------------- Event Handlers ----------------

document.addEventListener("click", async function (e) {
  console.log("[click handler] Click detected on:", e.target);
  
  const isDeleteBtn = e.target.closest(".o_list_record_remove [name='delete']");

  if (!isDeleteBtn) {
    const row = e.target.closest(".o_data_row");
    if (row && row.dataset.id) {
      console.log("[click handler] Row clicked, dataset:", row.dataset);
      
      const rawId = row.dataset.id;
      const vicidialLeadId = rawId.replace("datapoint_", "");
      
      console.log("[click handler] Extracted vicidial lead ID:", vicidialLeadId);
      
      // 🎯 FIX 3: Add validation and better error handling
      if (!vicidialLeadId) {
        console.error("[click handler] Invalid vicidial lead ID:", vicidialLeadId);
        alert("Invalid lead ID. Cannot open modal.");
        return;
      }
      
      // Call the corrected function
      await openCustomModal(vicidialLeadId); 
      return;
    }
  }

  // ✅ Delete functionality
  const row = e.target.closest(".o_data_row");
  if (isDeleteBtn && row && row.dataset.id) {
    const leadId = row.dataset.id.replace("datapoint_", "");
    
    console.log("[delete handler] Attempting to delete lead ID:", leadId);
    
    const confirmDelete = confirm("Are you sure you want to delete this lead?");
    if (!confirmDelete) return;

    try {
      const env = owl.Component.env;
      const orm = env.services.orm;
      
      // 🎯 FIX 4: Delete from vicidial.lead model instead of crm.lead
      await orm.call("vicidial.lead", "unlink", [[parseInt(leadId)]]);
      console.log(`[delete handler] Vicidial lead ${leadId} deleted successfully`);

      // Remove the row from UI
      row.remove();
      previousRenderedHTML = "";
      
    } catch (err) {
      console.error(`[delete handler] Failed to delete lead ${leadId}`, err);
      alert("Failed to delete lead. Check server logs for details.");
    }
  }
});

// ---------------- Polling Refresh ----------------

let previousRenderedHTML = "";

const interval = setInterval(async () => {
  const leadIdsTable = document.querySelector("[name=lead_ids]");
  if (!leadIdsTable) {
    console.log("[polling] Lead table not found, skipping refresh");
    return;
  }

  try {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    const res = await fetch(`${baseUrl}/vici/iframe/session`);

    if (!res.ok) {
      console.error("[polling] Fetch failed with status:", res.status);
      return;
    }

    const responseData = await res.json();
    const { leads } = responseData;
    
    console.log("[polling] Fetched leads are : ", leads);

    if (!leads || leads.length === 0) {
      console.log("[polling] No leads found, clearing table");
      const tbody = leadIdsTable.querySelector("tbody");
      if (tbody) {
        tbody.innerHTML = "";
        previousRenderedHTML = "";
      }
      return;
    }

    // Get stage information
    const stages = await owl.Component.env.services.orm.searchRead(
      "crm.stage",
      [],
      ["name"]
    );
    const stageMap = {};
    stages.forEach((s) => (stageMap[s.id] = s.name));

    // Enrich leads with stage names
    const enrichedLeads = leads.map((lead) => ({
      ...lead,
      stage_id: { id: lead.stage_id, name: stageMap[lead.stage_id] || "New" },
    }));

    const newRenderedHTML = enrichedLeads.map(renderer).join("\n");

    if (newRenderedHTML !== previousRenderedHTML) {
      console.log("[polling] UI updated due to data changes");
      const tbody = leadIdsTable.querySelector("tbody");
      if (tbody) {
        tbody.innerHTML = newRenderedHTML;
        previousRenderedHTML = newRenderedHTML;
      }
    } else {
      console.log("[polling] No UI update needed - data unchanged");
    }
  } catch (error) {
    console.error("[polling] Fetch/render error:", error);
  }
}, 5000);

// Cleanup interval when page unloads
window.addEventListener('beforeunload', () => {
  if (interval) {
    clearInterval(interval);
    console.log("[cleanup] Polling interval cleared");
  }
});
// /** @odoo-module **/

// import { Component, onMounted, onWillUnmount, xml } from "@odoo/owl";
// import { registry } from "@web/core/registry";
// import { useService } from "@web/core/utils/hooks";
// import { Dialog } from "@web/core/dialog/dialog";

// console.log("[VICIDIAL] Loading custom_iframe_autoload.js module...");

// // ---------------- Widget Class ----------------

// export class LeadAutoRefreshMany2Many extends Component {
//   static template = xml`
//     <div class="o_field_widget">
//       <span>Auto-refresh active</span>
//     </div>
//   `;

//   setup() {}

//   reloadField() {
//     console.log("[lead_auto_refresh_m2m] Reloading field...");
//     try {
//       if (this.env && this.env.model) {
//         this.env.model.load();
//         console.log("[lead_auto_refresh_m2m] Field reloaded successfully");
//       }
//     } catch (error) {
//       console.error("[lead_auto_refresh_m2m] Error reloading field:", error);
//     }
//   }
// }

// // registry.category('fields').add('lead_auto_refresh_m2m', LeadAutoRefreshMany2Many);

// // ---------------- Table Renderer ----------------

// const renderer = (item) => `
// <tr class="o_data_row" data-id="datapoint_${item.id}">
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_char o_required_modifier" name="name">${
//     item.first_name || item.opportunity || item.comments || ""
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="partner_name">${
//     item.companyName || "K N K TRADERS"
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="phone">${
//     item.phone_number || item.alt_phone || ""
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="stage_id">${
//     item.stage_id ? item.stage_id.name : "New"
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="user_id">${
//     item.user
//   }</td>
//   <td class="o_list_record_remove w-print-0 p-print-0 text-center">
//     <button class="fa d-print-none fa-times" name="delete" aria-label="Delete row"></button>
//   </td>
// </tr>
// `;

// // ---------------- Modal Logic ----------------

// async function showModalWithLeadData(leadId) {
//   console.log("lead issssssssssssss ", leadId);

//   try {
//     const env = owl.Component.env;
//     const actionService = env.services.action;

//     await actionService.doAction({
//       type: "ir.actions.act_window",
//       res_model: "crm.lead",
//       res_id: parseInt(leadId),
//       views: [[false, "form"]],
//       target: "new",
//       fullscreen: true,
//       context: {
//         default_services: "false",
//       },
//     });

//     // Use recursive retry to wait for field to appear
//     const waitForFieldAndSetValue = () => {
//       const select = document.querySelector("#services_0");

//       if (select) {
//         select.value = "false";
//         select.dispatchEvent(new Event("change", { bubbles: true }));
//         console.info("✅ 'services' field forcibly reset to 'false'");
//       } else {
//         console.warn("⏳ Waiting for services field...");
//         setTimeout(waitForFieldAndSetValue, 100); // keep retrying every 100ms
//       }
//     };

//     waitForFieldAndSetValue();
//   } catch (error) {
//     console.error("[lead_modal] Error loading form modal:", error);
//   }
// }

// async function openCustomModal(leadId) {
//   try {
//     await showModalWithLeadData(leadId);
//   } catch (err) {
//     console.error("[modal] Failed to open lead modal:", err);
//   }
// }

// document.addEventListener("click", async function (e) {
//   const isDeleteBtn = e.target.closest(".o_list_record_remove [name='delete']");

//   // 🚫 Skip row click if delete button is clicked
//   if (!isDeleteBtn) {
//     const row = e.target.closest(".o_data_row");
//     if (row && row.dataset.id) {
//       const rawId = row.dataset.id;
//       const leadId = rawId.replace("datapoint_", "");
//       openCustomModal(leadId);
//       return;
//     }
//   }

//   // ✅ Delete functionality
//   const row = e.target.closest(".o_data_row");
//   if (isDeleteBtn && row && row.dataset.id) {
//     const leadId = row.dataset.id.replace("datapoint_", "");
//     const confirmDelete = confirm("Are you sure you want to delete this lead?");
//     if (!confirmDelete) return;

//     try {
//       const env = owl.Component.env;
//       const orm = env.services.orm;
//       removeItem(parseInt(leadId));
//       await orm.call("crm.lead", "unlink", [[parseInt(leadId)]]);
//       console.log(`[lead_auto_refresh] Lead ${leadId} deleted successfully`);

//       previousRenderedHTML = ""; // trigger UI refresh
//     } catch (err) {
//       console.error(`[lead_auto_refresh] Failed to delete lead ${leadId}`, err);
//       alert("Failed to delete lead. Check server logs.");
//     }
//   }
// });

// // ---------------- Polling Refresh ----------------

// let previousRenderedHTML = "";

// const interval = setInterval(async () => {
//   const leadIdsTable = document.querySelector("[name=lead_ids]");
//   if (!leadIdsTable) return;

//   try {
//     const baseUrl = `${window.location.protocol}//${window.location.host}`;
//     const res = await fetch(`${baseUrl}/vici/iframe/session`);

//     const { leads } = await res.json();
//     console.log("leads IDS are ", leads.length, leads);

//     // Fetch the stage names and their IDs using searchRead
//     const stages = await owl.Component.env.services.orm.searchRead(
//       "crm.stage",
//       [],
//       ["name"]
//     );
//     const stageMap = {};
//     stages.forEach((s) => (stageMap[s.id] = s.name));

//     // Enrich the lead data with stage names
//     const enrichedLeads = leads.map((lead) => ({
//       ...lead,
//       stage_id: { id: lead.stage_id, name: stageMap[lead.stage_id] || "New" },
//     }));

//     const newRenderedHTML = enrichedLeads.map(renderer).join("\n");

//     if (newRenderedHTML !== previousRenderedHTML) {
//       console.log("[lead_auto_refresh] UI updated due to change...");
//       const tbody = leadIdsTable.querySelector("tbody");
//       if (tbody) {
//         tbody.innerHTML = newRenderedHTML;
//         previousRenderedHTML = newRenderedHTML;
//       }
//     } else {
//       console.log("[lead_auto_refresh] No update needed.");
//     }
//   } catch (error) {
//     console.error("[lead_auto_refresh] Fetch/render error:", error);
//   }

// }, 5000);

// /** @odoo-module **/

// import { Component, onMounted, onWillUnmount, xml } from "@odoo/owl";
// import { registry } from "@web/core/registry";
// import { useService } from "@web/core/utils/hooks";
// import { Dialog } from "@web/core/dialog/dialog";

// console.log("[VICIDIAL] Loading custom_iframe_autoload.js module...");

// // ---------------- Widget Class ----------------

// export class LeadAutoRefreshMany2Many extends Component {
//   static template = xml`
//     <div class="o_field_widget">
//       <span>Auto-refresh active</span>
//     </div>
//   `;

//   setup() {}

//   reloadField() {
//     console.log("[lead_auto_refresh_m2m] Reloading field...");
//     try {
//       if (this.env && this.env.model) {
//         this.env.model.load();
//         console.log("[lead_auto_refresh_m2m] Field reloaded successfully");
//       }
//     } catch (error) {
//       console.error("[lead_auto_refresh_m2m] Error reloading field:", error);
//     }
//   }
// }

// // registry.category('fields').add('lead_auto_refresh_m2m', LeadAutoRefreshMany2Many);

// // ---------------- Table Renderer ----------------

// const renderer = (item) => `
// <tr class="o_data_row" data-id="datapoint_${
//   item.lead_id
// }" data-full-data='${JSON.stringify(item).replace(/'/g, "&apos;")}'>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_char o_required_modifier" name="name">${
//     item.opportunity || item.comments || ""
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="partner_name">${
//     item.companyName ||
//     (item.first_name && item.last_name
//       ? `${item.first_name} ${item.last_name}`
//       : "") ||
//     ""
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="phone">${
//     item.phone_number || item.alt_phone || ""
//   }</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="stage_id">${1}</td>
//   <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="user_id">${
//     item.user || ""
//   }</td>
//   <td class="o_list_record_remove w-print-0 p-print-0 text-center">
//     <button class="fa d-print-none fa-times" name="delete" aria-label="Delete row"></button>
//   </td>
// </tr>
// `;

// // ---------------- Modal Logic ----------------

// async function showModalWithLeadData(leadData) {
//   try {
//     const env = owl.Component.env;
//     const actionService = env.services.action;

//     // Prepare context with lead data for form pre-population
//     const formContext = {
//       default_name: leadData.opportunity || leadData.comments || "",
//       default_contact_name:
//         leadData.first_name && leadData.last_name
//           ? `${leadData.first_name} ${leadData.last_name}`
//           : "",
//       default_partner_name: leadData.company_name || "",
//       default_phone: leadData.phone_number || leadData.alt_phone || "",
//       default_mobile: leadData.alt_phone || "",
//       default_email_from: leadData.email || "",
//       default_street: leadData.address1 || "",
//       default_street2: leadData.address2 || "",
//       default_city: leadData.city || "",
//       default_state_id: leadData.state || "",
//       default_zip: leadData.postal_code || "",
//       default_country_id: leadData.country_code || "",
//       default_description: leadData.comments || "",
//       // Additional custom fields if they exist in your CRM
//       default_title: leadData.title || "",
//       default_date_of_birth: leadData.date_of_birth || "",
//       default_security_phrase: leadData.security_phrase || "",
//       default_vicidial_lead_id: leadData.lead_id || "",
//       default_vendor_lead_code: leadData.vendor_lead_code || "",
//       default_source_id: leadData.source_id || "",
//       default_list_id: leadData.list_id || "",
//       default_called_count: leadData.called_count || 0,
//       default_last_local_call_time: leadData.last_local_call_time || "",
//     };

//     // Create new lead or open existing one
//     const actionConfig = leadData.existing_crm_id
//       ? {
//           type: "ir.actions.act_window",
//           res_model: "crm.lead",
//           res_id: parseInt(leadData.existing_crm_id),
//           views: [[false, "form"]],
//           target: "new",
//           context: formContext,
//         }
//       : {
//           type: "ir.actions.act_window",
//           res_model: "crm.lead",
//           views: [[false, "form"]],
//           target: "new",
//           context: formContext,
//         };

//     await actionService.doAction(actionConfig);
//     // Use recursive retry to wait for field to appear
//     const waitForFieldAndSetValue = () => {
//       const select = document.querySelector("#services_0");

//       if (select) {
//         select.value = "false";
//         select.dispatchEvent(new Event("change", { bubbles: true }));
//         console.info("✅ 'services' field forcibly reset to 'false'");
//       } else {
//         console.warn("⏳ Waiting for services field...");
//         setTimeout(waitForFieldAndSetValue, 100); // keep retrying every 100ms
//       }
//     };

//     waitForFieldAndSetValue();
//   } catch (error) {
//     console.error("[lead_modal] Error loading form modal:", error);
//   }
// }

// async function openCustomModal(leadId) {
//   try {
//     // Get the full lead data from the row
//     const row = document.querySelector(`[data-id="datapoint_${leadId}"]`);
//     if (!row) {
//       console.error("[modal] Could not find row data for lead:", leadId);
//       return;
//     }

//     const fullDataAttr = row.getAttribute("data-full-data");
//     if (!fullDataAttr) {
//       console.error("[modal] No full data attribute found for lead:", leadId);
//       return;
//     }

//     try {
//       const leadData = JSON.parse(fullDataAttr.replace(/&apos;/g, "'"));
//       await showModalWithLeadData(leadData);
//     } catch (parseError) {
//       console.error("[modal] Error parsing lead data:", parseError);
//       // Fallback to basic modal opening
//       await showModalWithLeadData({ lead_id: leadId });
//     }
//   } catch (err) {
//     console.error("[modal] Failed to open lead modal:", err);
//   }
// }

// document.addEventListener("click", async function (e) {
//   const isDeleteBtn = e.target.closest(".o_list_record_remove [name='delete']");

//   // 🚫 Skip row click if delete button is clicked
//   if (!isDeleteBtn) {
//     const row = e.target.closest(".o_data_row");
//     if (row && row.dataset.id) {
//       const rawId = row.dataset.id;
//       const leadId = rawId.replace("datapoint_", "");
//       openCustomModal(leadId);
//       return;
//     }
//   }

//   // ✅ Delete functionality
//   const row = e.target.closest(".o_data_row");
//   if (isDeleteBtn && row && row.dataset.id) {
//     const leadId = row.dataset.id.replace("datapoint_", "");
//     const confirmDelete = confirm("Are you sure you want to delete this lead?");
//     if (!confirmDelete) return;

//     try {
//       const env = owl.Component.env;
//       const orm = env.services.orm;
//       removeItem(parseInt(leadId));
//       await orm.call("crm.lead", "unlink", [[parseInt(leadId)]]);
//       console.log(`[lead_auto_refresh] Lead ${leadId} deleted successfully`);

//       previousRenderedHTML = ""; // trigger UI refresh
//     } catch (err) {
//       console.error(`[lead_auto_refresh] Failed to delete lead ${leadId}`, err);
//       alert("Failed to delete lead. Check server logs.");
//     }
//   }
// });

// // ---------------- Polling Refresh ----------------

// let previousRenderedHTML = "";

// const interval = setInterval(async () => {
//   const leadIdsTable = document.querySelector("[name=lead_ids]");
//   if (!leadIdsTable) return;

//   try {
//     const baseUrl = `${window.location.protocol}//${window.location.host}`;
//     const res = await fetch(`${baseUrl}/vici/iframe/session`);
//     const { leads } = await res.json();

//     const newRenderedHTML = leads.map(renderer).join("\n");

//     if (newRenderedHTML !== previousRenderedHTML) {
//       console.log("[lead_auto_refresh] UI updated due to change...");
//       const tbody = leadIdsTable.querySelector("tbody");
//       if (tbody) {
//         tbody.innerHTML = newRenderedHTML;
//         previousRenderedHTML = newRenderedHTML;
//       }
//     } else {
//       console.log("[lead_auto_refresh] No update needed.");
//     }
//   } catch (error) {
//     console.error("[lead_auto_refresh] Fetch/render error:", error);
//   }
// }, 5000);
