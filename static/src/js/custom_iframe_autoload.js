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

// registry.category('fields').add('lead_auto_refresh_m2m', LeadAutoRefreshMany2Many);

// ---------------- Table Renderer ----------------

const renderer = (item) => `
<tr class="o_data_row" data-id="datapoint_${item.id}">
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
    item.user
  }</td>
  <td class="o_list_record_remove w-print-0 p-print-0 text-center">
    <button class="fa d-print-none fa-times" name="delete" aria-label="Delete row"></button>
  </td>
</tr>
`;

// ---------------- Modal Logic ----------------

async function showModalWithLeadData(leadId) {
  console.log("lead issssssssssssss ", leadId);
  
  try {
    const env = owl.Component.env;
    const actionService = env.services.action;

    

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

    // Use recursive retry to wait for field to appear
    const waitForFieldAndSetValue = () => {
      const select = document.querySelector("#services_0");

      if (select) {
        select.value = "false";
        select.dispatchEvent(new Event("change", { bubbles: true }));
        console.info("✅ 'services' field forcibly reset to 'false'");
      } else {
        console.warn("⏳ Waiting for services field...");
        setTimeout(waitForFieldAndSetValue, 100); // keep retrying every 100ms
      }
    };

    waitForFieldAndSetValue();
  } catch (error) {
    console.error("[lead_modal] Error loading form modal:", error);
  }
}

async function openCustomModal(leadId) {
  try {
    await showModalWithLeadData(leadId);
  } catch (err) {
    console.error("[modal] Failed to open lead modal:", err);
  }
}

document.addEventListener("click", async function (e) {
  const isDeleteBtn = e.target.closest(".o_list_record_remove [name='delete']");

  // 🚫 Skip row click if delete button is clicked
  if (!isDeleteBtn) {
    const row = e.target.closest(".o_data_row");
    if (row && row.dataset.id) {
      const rawId = row.dataset.id;
      const leadId = rawId.replace("datapoint_", "");
      openCustomModal(leadId);
      return;
    }
  }

  // ✅ Delete functionality
  const row = e.target.closest(".o_data_row");
  if (isDeleteBtn && row && row.dataset.id) {
    const leadId = row.dataset.id.replace("datapoint_", "");
    const confirmDelete = confirm("Are you sure you want to delete this lead?");
    if (!confirmDelete) return;

    try {
      const env = owl.Component.env;
      const orm = env.services.orm;
      removeItem(parseInt(leadId));
      await orm.call("crm.lead", "unlink", [[parseInt(leadId)]]);
      console.log(`[lead_auto_refresh] Lead ${leadId} deleted successfully`);

      previousRenderedHTML = ""; // trigger UI refresh
    } catch (err) {
      console.error(`[lead_auto_refresh] Failed to delete lead ${leadId}`, err);
      alert("Failed to delete lead. Check server logs.");
    }
  }
});

// ---------------- Polling Refresh ----------------

let previousRenderedHTML = "";

const interval = setInterval(async () => {
  const leadIdsTable = document.querySelector("[name=lead_ids]");
  if (!leadIdsTable) return;

  try {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    const res = await fetch(`${baseUrl}/vici/iframe/session`);

    const { leads } = await res.json();
    console.log("leads IDS are ", leads.length, leads);

    // Fetch the stage names and their IDs using searchRead
    const stages = await owl.Component.env.services.orm.searchRead(
      "crm.stage",
      [],
      ["name"]
    );
    const stageMap = {};
    stages.forEach((s) => (stageMap[s.id] = s.name));

    // Enrich the lead data with stage names
    const enrichedLeads = leads.map((lead) => ({
      ...lead,
      stage_id: { id: lead.stage_id, name: stageMap[lead.stage_id] || "New" },
    }));

    const newRenderedHTML = enrichedLeads.map(renderer).join("\n");

    if (newRenderedHTML !== previousRenderedHTML) {
      console.log("[lead_auto_refresh] UI updated due to change...");
      const tbody = leadIdsTable.querySelector("tbody");
      if (tbody) {
        tbody.innerHTML = newRenderedHTML;
        previousRenderedHTML = newRenderedHTML;
      }
    } else {
      console.log("[lead_auto_refresh] No update needed.");
    }
  } catch (error) {
    console.error("[lead_auto_refresh] Fetch/render error:", error);
  }

}, 5000);

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

//     // Enhanced field population after modal opens
//     // const waitForFieldsAndSetValues = () => {
//     //   const fieldsToSet = [
//     //     // { selector: "#services_0", value: "false", type: "select" },
//     //     {
//     //       selector: "input[name='name']",
//     //       value: leadData.opportunity || leadData.comments || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='contact_name']",
//     //       value:
//     //         leadData.first_name && leadData.last_name
//     //           ? `${leadData.first_name} ${leadData.last_name}`
//     //           : "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='partner_name']",
//     //       value: leadData.company_name || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='phone']",
//     //       value: leadData.phone_number || leadData.alt_phone || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='mobile']",
//     //       value: leadData.alt_phone || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='email_from']",
//     //       value: leadData.email || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='street']",
//     //       value: leadData.address1 || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='street2']",
//     //       value: leadData.address2 || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='city']",
//     //       value: leadData.city || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "input[name='zip']",
//     //       value: leadData.postal_code || "",
//     //       type: "input",
//     //     },
//     //     {
//     //       selector: "textarea[name='description']",
//     //       value: leadData.comments || "",
//     //       type: "textarea",
//     //     },
//     //   ];

//     //   let fieldsSet = 0;
//     //   let totalFields = fieldsToSet.filter((field) => field.value).length;

//     //   fieldsToSet.forEach((field) => {
//     //     if (!field.value) return; // Skip empty values

//     //     const element = document.querySelector(field.selector);
//     //     if (element) {
//     //       if (field.type === "input" || field.type === "textarea") {
//     //         element.value = field.value;
//     //         element.dispatchEvent(new Event("input", { bubbles: true }));
//     //         element.dispatchEvent(new Event("change", { bubbles: true }));
//     //       } else if (field.type === "select") {
//     //         element.value = field.value;
//     //         element.dispatchEvent(new Event("change", { bubbles: true }));
//     //       }
//     //       fieldsSet++;
//     //       console.log(`✅ Set ${field.selector} to: ${field.value}`);
//     //     }
//     //   });

//     //   if (fieldsSet < totalFields) {
//     //     console.warn(
//     //       `⏳ Waiting for more fields... (${fieldsSet}/${totalFields})`
//     //     );
//     //     setTimeout(waitForFieldsAndSetValues, 200); // keep retrying every 200ms
//     //   } else {
//     //     console.info(`✅ All ${fieldsSet} fields populated successfully`);
//     //   }
//     // };

//     // // Start field population after a brief delay
//     // setTimeout(waitForFieldsAndSetValues, 300);
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
