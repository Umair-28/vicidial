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
  <td class="o_data_cell cursor-pointer o_field_cell o_list_char o_required_modifier" name="name">${item.opportunity}</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="partner_name">${item.company_name}</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_char" name="phone">${item.phone}</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="stage_id">${item.stage}</td>
  <td class="o_data_cell cursor-pointer o_field_cell o_list_many2one" name="user_id">${item.sales_person}</td>
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

    await actionService.doAction({
      type: "ir.actions.act_window",
      res_model: "crm.lead",
      res_id: parseInt(leadId), // works for both new & existing leads
      views: [[false, "form"]],
      target: "new",
      fullscreen: true,
      context: {
        default_services: "empty_value",
        force_reset_services: true,
      },
    });

    setTimeout(() => {
      console.log("running settimeout methods!!!!!!!");

      const select = document.querySelector('select[name="services"]');
      if (select) {
        select.value = "empty_value";
        select.dispatchEvent(new Event("change", { bubbles: true }));
        console.info("✅ Service dropdown forcibly reset to 'empty_value'");
      } else {
        console.warn("⚠️ Dropdown field not found");
      }
    }, 2000); // may increase to 700ms if needed
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

// ---------------- Click Listener ----------------

// document.addEventListener("click", function (e) {
//   const row = e.target.closest(".o_data_row");
//   if (row && row.dataset.id) {
//     const rawId = row.dataset.id;
//     const leadId = rawId.replace("datapoint_", "");
//     openCustomModal(leadId);
//   }
// });

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
    const res = await fetch(
      `${baseUrl}/vici/iframe/session?sip_exten=${
        document.querySelector("[name=sip_exten]").innerText
      }`
    );

    const { lead_ids } = await res.json();

    const newRenderedHTML = lead_ids.map(renderer).join("\n");

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
