/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";

function injectStageNav() {
  console.log("[STAGE NAV] injectStageNav called");

  const wrapper = document.querySelector("[name=services]");
  console.log("[STAGE NAV] Wrapper element:", wrapper);
  if (!wrapper) {
    console.warn("[STAGE NAV] Wrapper not found, exiting");
    return;
  }

  if (wrapper.dataset.stageNavMounted === "1") {
    console.log("[STAGE NAV] Already mounted, skipping");
    return;
  }

  // Create container below services field
  const container = document.createElement("div");
  container.className = "o_stage_nav_container";
  container.style.cssText =
    "margin-top: 15px; display: flex; gap: 10px; padding: 10px; border-top: 1px solid #ddd;";
  wrapper.insertAdjacentElement("afterend", container);
  console.log("[STAGE NAV] Container created and inserted");

  // Create buttons
  const prevBtn = document.createElement("button");
  prevBtn.className = "btn btn-secondary";
  prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';
  prevBtn.style.marginRight = "5px";

  const nextBtn = document.createElement("button");
  nextBtn.className = "btn btn-primary";
  nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';

  console.log("[STAGE NAV] Buttons created");

  // Get record ID - using the hidden id field from your form
  function getActiveLeadId() {
    console.log("[STAGE NAV] getActiveLeadId called");

    const idField = document.querySelector("input[name='id']");
    console.log("[STAGE NAV] ID field found:", idField, "Value:", idField?.value);

    if (idField?.value) {
      const recordId = parseInt(idField.value, 10);
      console.log("[STAGE NAV] Record ID from hidden field:", recordId);
      return recordId;
    }

    const hash = window.location.hash;
    const idMatch = hash.match(/id=(\d+)/);
    if (idMatch) {
      const recordId = parseInt(idMatch[1], 10);
      console.log("[STAGE NAV] Record ID from URL hash:", recordId);
      return recordId;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get("id");
    if (idFromUrl) {
      const recordId = parseInt(idFromUrl, 10);
      console.log("[STAGE NAV] Record ID from URL params:", recordId);
      return recordId;
    }

    console.error("[STAGE NAV] Could not find record ID. URL:", window.location.href);
    return null;
  }

  // Get current stage from lead_stage field
  function getLeadStage() {
    console.log("[STAGE NAV] getLeadStage called");

    let stageInput = document.querySelector("input[name='lead_stage']");
    if (!stageInput) {
      stageInput = document.querySelector("select[name='lead_stage']");
    }

    console.log("[STAGE NAV] Stage field:", stageInput, "Value:", stageInput?.value);

    if (stageInput?.value) {
      const stage = parseInt(stageInput.value, 10);
      console.log("[STAGE NAV] Current stage parsed:", stage);
      return stage;
    }

    console.warn("[STAGE NAV] Stage field empty or not found");
    return null;
  }

  // Update button states based on current stage
  function updateButtonState() {
    console.log("[STAGE NAV] updateButtonState called");

    const stage = getLeadStage();
    console.log("[STAGE NAV] Current stage:", stage);

    prevBtn.disabled = stage === 1;
    nextBtn.disabled = stage === 3;

    console.log(
      "[STAGE NAV] Buttons state - Prev disabled:",
      prevBtn.disabled,
      "Next disabled:",
      nextBtn.disabled
    );
  }

  // Previous button handler
  prevBtn.addEventListener("click", async () => {
    console.log("[STAGE NAV] Previous button clicked");

    const recordId = getActiveLeadId();
    console.log("[STAGE NAV] Previous clicked - Record ID:", recordId);

    if (!recordId) {
      alert("Error: Could not find record ID");
      return;
    }

    try {
      prevBtn.disabled = true;
      prevBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';
      console.log("[STAGE NAV] Calling RPC action_prev_stage");

      await rpc({
        model: "crm.lead",
        method: "action_prev_stage",
        args: [[recordId]],
      });

      console.log("[STAGE NAV] action_prev_stage completed, reloading page");
      location.reload();
    } catch (error) {
      console.error("[STAGE NAV] Error calling action_prev_stage:", error);
      alert("Error moving to previous stage");
      prevBtn.disabled = false;
      prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';
    }
  });

  // Next button handler
  nextBtn.addEventListener("click", async () => {
    console.log("[STAGE NAV] Next button clicked");

    const recordId = getActiveLeadId();
    console.log("[STAGE NAV] Next clicked - Record ID:", recordId);

    if (!recordId) {
      alert("Error: Could not find record ID");
      return;
    }

    try {
      nextBtn.disabled = true;
      nextBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';
      console.log("[STAGE NAV] Calling RPC action_next_stage");

      await rpc({
        model: "crm.lead",
        method: "action_next_stage",
        args: [[recordId]],
      });

      console.log("[STAGE NAV] action_next_stage completed, reloading page");
      location.reload();
    } catch (error) {
      console.error("[STAGE NAV] Error calling action_next_stage:", error);
      alert("Error moving to next stage");
      nextBtn.disabled = false;
      nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
    }
  });

  // Append buttons to container
  container.appendChild(prevBtn);
  container.appendChild(nextBtn);
  console.log("[STAGE NAV] Buttons appended to container");

  // Initial button state update
  updateButtonState();

  // Watch for stage changes (when user manually changes lead_stage field)
  const stageField =
    document.querySelector("input[name='lead_stage']") ||
    document.querySelector("select[name='lead_stage']");
  if (stageField) {
    stageField.addEventListener("change", () => {
      console.log("[STAGE NAV] Stage changed, updating buttons");
      updateButtonState();
    });
  }

  wrapper.dataset.stageNavMounted = "1";
  console.log("[STAGE NAV] Stage navigation mounted successfully");
}

// Keep trying until the form renders
const checkInterval = setInterval(() => {
  console.log("[STAGE NAV] Trying to inject stage nav...");
  injectStageNav();
}, 1000);

// Stop checking after 30 seconds to prevent infinite loop
setTimeout(() => {
  clearInterval(checkInterval);
  console.log("[STAGE NAV] Stage navigation injection stopped after 30 seconds");
}, 30000);
