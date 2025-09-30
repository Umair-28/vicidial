/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";

function injectStageNav() {
  const wrapper = document.querySelector(" [name=services]");

  const formEl = wrapper.closest(".o_form_view");
  if(!formEl){
    return
  }
  const phoneWrapper = formEl?.querySelector("[name=phone]");
  const phoneValue =
    phoneWrapper?.querySelector("input")?.value ||
    phoneWrapper?.textContent?.trim();

  if (phoneValue) {
    console.log("Phone value:", phoneValue);
    fetchLeadByPhone(phoneValue);
  } else {
    console.warn("[SERVICES] No phone found in form.");
  }
  async function fetchLeadByPhone(phone) {
    try {
      const response = await fetch(
        `/vicidial/lead/${encodeURIComponent(phone)}`,
        {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        }
      );
      const data = await response.json();
      console.log("[SERVICES] Lead by phone:", data);

      if (!data.error) {
        if (showFooter) {
          setupStageNav(wrapper, data);
        }
      } else {
        console.warn("[SERVICES] No lead found:", data.error);
      }
    } catch (err) {
      console.error("[SERVICES] Error fetching lead:", err);
    }
  }

  function setupStageNav(wrapper, lead) {
    const container = document.createElement("div");
    container.className = "o_stage_nav_container";
    container.style.cssText = `
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  gap:20px;
  display: flex;
  justify-content: center; /* keeps prev left, next right */
  padding: 12px 24px;
  background: #fff;
  border-top: 1px solid #ddd;
  z-index: 1050; /* make sure it’s above Odoo UI */
`;

    const prevBtn = document.createElement("button");
    prevBtn.className = "btn btn-secondary";
    prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';

    const nextBtn = document.createElement("button");
    nextBtn.className = "btn btn-primary";
    nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';

    container.appendChild(prevBtn);
    container.appendChild(nextBtn);

    // Add to body instead of after the wrapper
    if (showFooter) {
      document.body.appendChild(container);
    }

    function updateButtonState() {
      const stage = parseInt(lead.lead_stage || "1");
      prevBtn.disabled = stage <= 1;
      nextBtn.disabled = stage >= 3;
    }
    updateButtonState();

    // Prev click
    prevBtn.addEventListener("click", async () => {
      try {
        prevBtn.disabled = true;
        nextBtn.disabled = true; // Disable both during operation
        prevBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';

        console.log("Calling prev stage for lead:", lead.id);

        const res = await rpc(
          "/web/dataset/call_kw/crm.lead/action_prev_stage",
          {
            model: "crm.lead",
            method: "action_prev_stage",
            args: [[lead.id]],
            kwargs: {},
          }
        );

        console.log("Previous button response:", res);
        if (res?.error) {
          alert(res.error);
          nextBtn.disabled = false;
          prevBtn.disabled = false;
          nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
        } else {
          // Reload the page to reflect changes in invisible fields
          window.location.reload();
        }

        // Reload the page to reflect changes in invisible fields
      } catch (err) {
        console.error("[SERVICES] Prev stage error:", err);
        alert("Failed to move to previous stage: " + (err.message || err));

        // Re-enable buttons on error
        prevBtn.disabled = false;
        nextBtn.disabled = false;
        prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';
      }
    });

    // Next click
    nextBtn.addEventListener("click", async () => {
      try {
        nextBtn.disabled = true;
        prevBtn.disabled = true; // Disable both during operation
        nextBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';

        console.log("Calling next stage for lead:", lead.id);

        const res = await rpc(
          "/web/dataset/call_kw/crm.lead/action_next_stage",
          {
            model: "crm.lead",
            method: "action_next_stage",
            args: [[lead.id]],
            kwargs: {},
          }
        );

        console.log("Next button response:", res);

        if (res?.error) {
          alert(res.error);
          nextBtn.disabled = false;
          prevBtn.disabled = false;
          nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
        } else {
          // Reload the page to reflect changes in invisible fields
          window.location.reload();
        }
      } catch (err) {
        console.error("[SERVICES] Next stage error:", err);
        alert("Failed to move to next stage: " + (err.message || err));

        // Re-enable buttons on error
        nextBtn.disabled = false;
        prevBtn.disabled = false;
        nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
      }
    });
  }
}

const interval = setInterval(() => {
  injectStageNav();
}, 1000);
