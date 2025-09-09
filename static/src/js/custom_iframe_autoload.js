/** @odoo-module **/

import { Component, onMounted, onWillUnmount, xml } from "@odoo/owl";
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

// Solution 1: Create record first, then open form

// async function showModalWithLeadData(leadId) {
//   try {
//     const orm = owl.Component.env.services.orm;

//     // Fetch Vicidial lead data
//     const vicidialLeadData = await orm.searchRead(
//       "vicidial.lead",
//       [["id", "=", parseInt(leadId)]],
//       [
//         "id",
//         "first_name",
//         "last_name",
//         "phone_number",
//         "email",
//         "comments",
//         "city",
//         "state",
//         "country_code",
//         "vendor_lead_code",
//         "lead_id",
//       ]
//     );

//     if (!vicidialLeadData.length) {
//       throw new Error("Vicidial lead not found");
//     }

//     const lead = vicidialLeadData[0];

//     console.log(
//       "🎯 [showModalWithLeadData] Opening CRM form with Vicidial lead:",
//       lead
//     );

//     const env = owl.Component.env;
//     const actionService = env.services.action;

//     // First, check what fields actually exist in your crm.lead model
//     const crmLeadFields = await orm.call("crm.lead", "fields_get", []);
//     console.log("Available CRM Lead fields:", Object.keys(crmLeadFields));

//     // Map defaults for CRM form
//     const defaultValues = {
//       // Standard CRM lead defaults
//       default_name:
//         `${lead.first_name || ""} ${lead.last_name || ""}`.trim() ||
//         "Unnamed Lead",
//       default_phone: lead.phone_number || "",
//       default_email_from: lead.email || "",
//       default_description: lead.comments || "",
//       default_city: lead.city || "",
//       default_ref: lead.vendor_lead_code || "",
//       default_vicidial_lead_id: lead.id, // custom field in crm.lead
//       default_services: "false",

//       // --- Custom Forms Mapping ---
//       // Contact Card (cc_)
//       default_cc_first_name: lead.first_name || "",
//       default_cc_last_name: lead.last_name || "",
//       default_cc_job_title: lead.title || "",
//       default_cc_phone: lead.phone_number || "",
//       default_cc_email: lead.email || "",

//       // Home Moving (hm_)
//       default_hm_first_name: lead.first_name,
//       default_hm_last_name: lead.last_name,
//       default_hm_address: lead.address1,
//       default_hm_suburb: lead.city,
//       default_hm_state: lead.state,
//       default_hm_postcode: lead.postal_code,
//       default_hm_mobile: lead.phone_number,
//       default_hm_email: lead.email,

//       // Energy (en_)
//       default_en_name: lead.first_name || lead.last_name,
//       default_en_contact_number: lead.phone_number,
//       default_en_email: lead.email,

//       // Internet (in_)
//       default_in_name: lead.first_name || lead.last_name,
//       default_in_contact_number: lead.phone_number,
//       default_in_email: lead.email,

//       // Billing Services (bs_)
//       default_bs_first_name: lead.first_name,
//       default_bs_last_name: lead.last_name,
//       default_bs_email: lead.email,

//       // Housing Lead (hl_)
//       default_hl_first_name: lead.first_name || "",
//       default_hl_last_name: lead.last_name || "",
//       default_hl_contact: lead.phone_number || "",
//       default_hl_email: lead.email || "",

//       // Home Internet (hi_)
//       default_hi_full_name: lead.first_name || lead.last_name || "",

//       default_hi_contact_number: lead.phone_number || "",
//       default_hi_email: lead.email || "",

//       // Do (do_)
//       default_do_first_name: lead.first_name || "",
//       default_do_last_name: lead.last_name || "",
//       default_do_mobile_no: lead.phone_number || "",
//       default_do_installation_address: lead.address1 || "",
//       default_do_suburb: lead.city || "",
//       default_do_state: lead.state || "",
//       default_do_post_code: lead.postal_code || "",
//       default_do_closer_name: lead.agent_user || "",

//       // Other Plans (op_)
//       default_op_customer_name: lead.first_name || lead.last_name || "",

//       default_op_contact_number: lead.phone_number || "",
//       default_op_email: lead.email || "",
//       default_op_notes: lead.comments || "",

//       // FE (fe_)
//       default_fe_first_name: lead.first_name || "",
//       default_fe_last_name: lead.last_name || "",
//       default_fe_phone_mobile: lead.phone_number || "",
//       default_fe_email: lead.email || "",

//       // DP (dp_)
//       default_dp_first_name: lead.first_name || "",
//       default_dp_last_name: lead.last_name || "",
//       default_dp_contact_number: lead.phone_number || "",
//       default_dp_email_contact: lead.email || "",
//     };

//     console.log("Default values are ", defaultValues);
//     await actionService.doAction({
//       type: "ir.actions.act_window",
//       res_model: "crm.lead",
//       res_id: false, // always new record
//       views: [[false, "form"]],
//       target: "new",
//       fullscreen: true,
//       context: defaultValues,
//     });

//     console.log(
//       "✅ [showModalWithLeadData] CRM lead form opened with defaults"
//     );
//   } catch (error) {
//     console.error("❌ [showModalWithLeadData] Error:", error);
//     alert("Failed to open lead modal: " + error.message);
//   }
// }

// async function openCustomModal(vicidialLeadId) {
//   console.log(
//     "🎯 [openCustomModal] Starting with vicidialLeadId:",
//     vicidialLeadId
//   );

//   try {
//     const orm = owl.Component.env.services.orm;

//     // Strategy 2: Direct lookup via vicidial.lead -> crm_lead_id
//     console.log("🔍 [openCustomModal] Strategy 2: Direct vicidial lookup");

//     const vicidialLeadData = await orm.searchRead(
//       "vicidial.lead",
//       [["id", "=", parseInt(vicidialLeadId)]],
//       ["id", "crm_lead_id", "first_name", "last_name"]
//     );

//     console.log("📊 [openCustomModal] Vicidial lead data:", vicidialLeadData);

//     if (vicidialLeadData.length > 0) {
//       await showModalWithLeadData(vicidialLeadId);

//       // await showModalWithLeadData(crmLeadId);
//       return;
//     }

//     // If we reach here, something is wrong
//     console.error(
//       "❌ [openCustomModal] No CRM lead found for vicidial ID:",
//       vicidialLeadId
//     );

//     // Debug: Check what's actually in the database
//     const allCrmLeads = await orm.searchRead(
//       "crm.lead",
//       [],
//       ["id", "name", "vicidial_lead_id"],
//       { limit: 5 }
//     );
//     const allVicidialLeads = await orm.searchRead(
//       "vicidial.lead",
//       [],
//       ["id", "crm_lead_id", "first_name"],
//       { limit: 5 }
//     );

//     console.log("🔍 [DEBUG] Sample CRM leads:", allCrmLeads);
//     console.log("🔍 [DEBUG] Sample Vicidial leads:", allVicidialLeads);

//     alert(
//       `Lead cannot be opened in CRM.\nVicidial Lead ID: ${vicidialLeadId}\nCheck browser console for debug info.`
//     );
//   } catch (err) {
//     console.error("❌ [openCustomModal] Critical error:", err);
//     // alert("Error opening lead modal: " + err.message);
//   }
// }

async function showModalWithLeadData(leadId, selectedService = null) {
  try {
    const orm = owl.Component.env.services.orm;

    // Fetch Vicidial lead data
    const vicidialLeadData = await orm.searchRead(
      "vicidial.lead",
      [["id", "=", parseInt(leadId)]],
      [
        "id", "first_name", "last_name", "phone_number", "email",
        "comments", "city", "state", "address1", "postal_code", "title", "alt_phone"
      ]
    );

    if (!vicidialLeadData.length) {
      throw new Error("Vicidial lead not found");
    }

    const lead = vicidialLeadData[0];

    // If no service specified, show service selection modal first
    if (!selectedService) {
      await showServiceSelectionModal(leadId, lead);
      return;
    }

    console.log(`Opening CRM form for service: ${selectedService} with lead:`, lead);

    // Base defaults (always set)
    let defaultValues = {
      // Standard CRM fields
      default_name: `${lead.first_name || ""} ${lead.last_name || ""}`.trim() || "Unnamed Lead",
      default_phone: lead.phone_number || "",
      default_email_from: lead.email || "",
      default_description: lead.comments || "",
      default_city: lead.city || "",
      default_street: lead.address1 || "",
      default_zip: lead.postal_code || "",
      default_title: lead.title || "",
      default_mobile: lead.alt_phone || "",
      default_vicidial_lead_id: lead.id,

      // Set the selected service
      default_services: selectedService,

      // Hide all forms by default
      default_show_nothing_tab: false,
      default_show_credit_card_tab: false,
      default_show_home_moving_tab: false,
      default_show_energy_tab: false,
      default_show_internet_tab: false,
      default_show_business_loan_tab: false,
      default_show_home_loan_tab: false,
      default_show_health_insurance_tab: false,
      default_show_dodo_nbn_tab: false,
      default_show_optus_nbn_tab: false,
      default_show_first_energy_tab: false,
      default_show_dodo_power_tab: false,
    };

    // Service-specific logic
    switch (selectedService) {
      case 'credit_card':
        defaultValues = {
          ...defaultValues,
          default_show_credit_card_tab: true,
          // Credit card specific defaults
          default_cc_first_name: lead.first_name || "",
          default_cc_last_name: lead.last_name || "",
          default_cc_job_title: lead.title || "",
          default_cc_phone: lead.phone_number || "",
          default_cc_email: lead.email || "",
        };
        break;

      case 'home_moving':
        defaultValues = {
          ...defaultValues,
          default_show_home_moving_tab: true,
          // Home moving specific defaults
          default_hm_first_name: lead.first_name || "",
          default_hm_last_name: lead.last_name || "",
          default_hm_address: lead.address1 || "",
          default_hm_suburb: lead.city || "",
          default_hm_state: lead.state || "",
          default_hm_postcode: lead.postal_code || "",
          default_hm_mobile: lead.phone_number || "",
          default_hm_email: lead.email || "",
        };
        break;

      case 'energy':
        defaultValues = {
          ...defaultValues,
          default_show_energy_tab: true,
          // Energy specific defaults
          default_en_name: `${lead.first_name || ""} ${lead.last_name || ""}`.trim() || "Unnamed",
          default_en_contact_number: lead.phone_number || "",
          default_en_email: lead.email || "",
        };
        break;

      case 'internet':
        defaultValues = {
          ...defaultValues,
          default_show_internet_tab: true,
          // Internet specific defaults
          default_in_name: `${lead.first_name || ""} ${lead.last_name || ""}`.trim() || "Unnamed",
          default_in_contact_number: lead.phone_number || "",
          default_in_email: lead.email || "",
        };
        break;

      // Add more cases for other services
      case 'business_loan':
        defaultValues = {
          ...defaultValues,
          default_show_business_loan_tab: true,
          default_bs_first_name: lead.first_name || "",
          default_bs_last_name: lead.last_name || "",
          default_bs_email: lead.email || "",
        };
        break;

      case 'home_loan':
        defaultValues = {
          ...defaultValues,
          default_show_home_loan_tab: true,
          default_hl_first_name: lead.first_name || "",
          default_hl_last_name: lead.last_name || "",
          default_hl_contact: lead.phone_number || "",
          default_hl_email: lead.email || "",
        };
        break;

      default:
        // Show nothing tab if service not recognized
        defaultValues.default_show_nothing_tab = true;
        console.warn(`Unknown service: ${selectedService}`);
    }

    console.log("Setting context defaults:", defaultValues);

    const env = owl.Component.env;
    const actionService = env.services.action;

    await actionService.doAction({
      type: "ir.actions.act_window",
      res_model: "crm.lead",
      res_id: false,
      views: [[false, "form"]],
      target: "new",
      fullscreen: true,
      context: defaultValues,
    });

    console.log(`CRM lead form opened for ${selectedService} service`);
  } catch (error) {
    console.error("Error opening modal:", error);
    alert("Failed to open lead modal: " + error.message);
  }
}

// Service selection modal
async function showServiceSelectionModal(leadId, lead) {
  const serviceOptions = [
    { key: 'credit_card', label: 'Credit Card' },
    { key: 'home_moving', label: 'Home Moving' },
    { key: 'energy', label: 'Energy' },
    { key: 'internet', label: 'Internet' },
    { key: 'business_loan', label: 'Business Loan' },
    { key: 'home_loan', label: 'Home Loan' },
    { key: 'health_insurance', label: 'Health Insurance' },
    { key: 'dodo_nbn', label: 'Dodo NBN' },
    { key: 'optus_nbn', label: 'Optus NBN' },
    { key: 'first_energy', label: 'First Energy' },
    { key: 'dodo_power', label: 'Dodo Power' }
  ];

  // Create modal HTML
  const modalHTML = `
    <div id="serviceSelectionModal" style="
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
      z-index: 10000;
    ">
      <div style="
        background: white; padding: 30px; border-radius: 8px; 
        max-width: 500px; width: 90%;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      ">
        <h3 style="margin-top: 0; color: #333;">Select Service for Lead</h3>
        <p style="margin-bottom: 20px; color: #666;">
          Lead: ${lead.first_name} ${lead.last_name}<br>
          Phone: ${lead.phone_number || 'N/A'}
        </p>
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 8px; font-weight: 500;">Choose Service:</label>
          <select id="serviceSelect" style="
            width: 100%; padding: 8px; border: 1px solid #ddd; 
            border-radius: 4px; font-size: 14px;
          ">
            <option value="">-- Select Service --</option>
            ${serviceOptions.map(option => 
              `<option value="${option.key}">${option.label}</option>`
            ).join('')}
          </select>
        </div>
        <div style="text-align: right;">
          <button id="cancelBtn" style="
            padding: 8px 16px; margin-right: 10px; border: 1px solid #ddd;
            background: #f5f5f5; border-radius: 4px; cursor: pointer;
          ">Cancel</button>
          <button id="continueBtn" style="
            padding: 8px 16px; background: #007cba; color: white;
            border: none; border-radius: 4px; cursor: pointer;
          ">Continue</button>
        </div>
      </div>
    </div>
  `;

  // Add modal to page
  document.body.insertAdjacentHTML('beforeend', modalHTML);

  // Handle modal interactions
  const modal = document.getElementById('serviceSelectionModal');
  const serviceSelect = document.getElementById('serviceSelect');
  const cancelBtn = document.getElementById('cancelBtn');
  const continueBtn = document.getElementById('continueBtn');

  cancelBtn.addEventListener('click', () => {
    modal.remove();
  });

  continueBtn.addEventListener('click', () => {
    const selectedService = serviceSelect.value;
    if (!selectedService) {
      alert('Please select a service');
      return;
    }
    
    modal.remove();
    // Open form with selected service
    showModalWithLeadData(leadId, selectedService);
  });

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

// Update your existing openCustomModal function
async function openCustomModal(vicidialLeadId) {
  console.log("Starting custom modal for vicidial lead:", vicidialLeadId);
  
  try {
    const orm = owl.Component.env.services.orm;

    const vicidialLeadData = await orm.searchRead(
      "vicidial.lead",
      [["id", "=", parseInt(vicidialLeadId)]],
      ["id", "first_name", "last_name"]
    );

    console.log("Vicidial lead data:", vicidialLeadData);

    if (vicidialLeadData.length > 0) {
      // Call without selectedService to show service selection first
      await showModalWithLeadData(vicidialLeadId);
      return;
    }

    console.error("No CRM lead found for vicidial ID:", vicidialLeadId);
    alert(`Lead cannot be opened in CRM.\nVicidial Lead ID: ${vicidialLeadId}`);
  } catch (err) {
    console.error("Critical error:", err);
  }
}

document.addEventListener("click", async function (e) {
  const isDeleteBtn = e.target.closest(".o_list_record_remove [name='delete']");

  if (!isDeleteBtn) {
    const row = e.target.closest(".o_data_row");
    if (row && row.dataset.id) {
      console.log("🖱️ [click] Row clicked with dataset:", row.dataset);

      const rawId = row.dataset.id;
      const vicidialLeadId = rawId.replace("datapoint_", "");

      console.log("🎯 [click] Extracted vicidialLeadId:", vicidialLeadId);

      if (!vicidialLeadId || vicidialLeadId === "undefined") {
        console.error("❌ [click] Invalid vicidial lead ID");
        alert("Invalid lead ID. Cannot open modal.");
        return;
      }

      await openCustomModal(vicidialLeadId);
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

      previousRenderedHTML = "";
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

    const stages = await owl.Component.env.services.orm.searchRead(
      "crm.stage",
      [],
      ["name"]
    );
    const stageMap = {};
    stages.forEach((s) => (stageMap[s.id] = s.name));

    const enrichedLeads = leads.map((lead) => ({
      ...lead,
      stage_id: { id: lead.stage_id, name: stageMap[lead.stage_id] || "New" },
    }));

    console.log("enrich leads are ", enrichedLeads);

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
