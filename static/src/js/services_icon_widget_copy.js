/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";

console.log("[SERVICES] widget bootstrap…");

let stageNavContainer = null; // Track the footer globally

function injectServicesWidget() {
  // Find wrapper
  const wrapper = document.querySelector("[name=services]");
  
  // If wrapper doesn't exist, remove the footer if it exists
  if (!wrapper) {
    if (stageNavContainer && stageNavContainer.parentNode) {
      stageNavContainer.remove();
      stageNavContainer = null;
      console.log("[SERVICES] Footer removed - no wrapper found");
    }
    return;
  }

  if (wrapper.dataset.widgetMounted === "1") {
    console.log("[SERVICES] Already mounted, skipping.");
    return;
  }

  const formEl = wrapper.closest(".o_form_view");

  // --- Fetch Lead by Phone ---
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
        setupStageNav(wrapper, data); // build stage nav after lead loaded
      } else {
        console.warn("[SERVICES] No lead found:", data.error);
      }
    } catch (err) {
      console.error("[SERVICES] Error fetching lead:", err);
    }
  }

  // --- Stage Navigation ---
  function setupStageNav(wrapper, lead) {
    // Remove existing container if it exists
    if (stageNavContainer && stageNavContainer.parentNode) {
      stageNavContainer.remove();
    }

    const container = document.createElement("div");
    container.className = "o_stage_nav_container";
    container.style.cssText = `
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      gap: 20px;
      display: flex;
      justify-content: center;
      padding: 12px 24px;
      background: #fff;
      border-top: 1px solid #ddd;
      z-index: 1050;
    `;

    const prevBtn = document.createElement("button");
    prevBtn.className = "btn btn-secondary";
    prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';

    const nextBtn = document.createElement("button");
    nextBtn.className = "btn btn-primary";
    nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';

    container.appendChild(prevBtn);
    container.appendChild(nextBtn);

    // Add to body and store reference
    document.body.appendChild(container);
    stageNavContainer = container;

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
        nextBtn.disabled = true;
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
          prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';
        } else {
          window.location.reload();
        }
      } catch (err) {
        console.error("[SERVICES] Prev stage error:", err);
        alert("Failed to move to previous stage: " + (err.message || err));
        prevBtn.disabled = false;
        nextBtn.disabled = false;
        prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';
      }
    });

    // Next click
    nextBtn.addEventListener("click", async () => {
      try {
        nextBtn.disabled = true;
        prevBtn.disabled = true;
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
          window.location.reload();
        }
      } catch (err) {
        console.error("[SERVICES] Next stage error:", err);
        alert("Failed to move to next stage: " + (err.message || err));
        nextBtn.disabled = false;
        prevBtn.disabled = false;
        nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
      }
    });
  }

  // --- Existing Service Selector ---
  const select = wrapper.querySelector("select");
  if (!select) {
    console.error("[SERVICES] No <select> found inside wrapper!");
    return;
  }
  select.style.display = "none";

  const container = document.createElement("div");
  container.classList.add("o_service_selector");
  select.insertAdjacentElement("afterend", container);

  Array.from(select.options).forEach((opt) => {
    if (!opt.value || opt.style.display === "none") return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.value = opt.value;
    const ICON_MAP = {
      credit_card: "/vicidial/static/src/img/credit_card.png",
      energy: "/vicidial/static/src/img/electricty_and_gas.png",
      optus_nbn: "/vicidial/static/src/img/broadband.png",
      home_moving: "/vicidial/static/src/img/home_moving.png",
      business_loan: "https://utilityhub.com.au/wp-content/uploads/2025/05/interest.svg",
      home_loan: "https://utilityhub.com.au/wp-content/uploads/2025/05/home.svg",
      insurance: "/vicidial/static/src/img/insurance.png",
      veu: `<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" xmlns:svgjs="http://svgjs.dev/svgjs" xmlns:xlink="http://www.w3.org/1999/xlink" id="svg678" width="300" height="300" viewBox="0 0 300 300"><defs><style>      .st0, .st1 {        fill: none;      }      .st2 {        fill: #e36e1c;      }      .st1 {        stroke: #e36e1c;        stroke-linecap: round;        stroke-linejoin: round;        stroke-width: 7.6px;      }      .st3 {        clip-path: url(#clippath);      }    </style><clipPath id="clippath"><rect class="st0" y="0" width="300" height="300"></rect></clipPath></defs><g id="g684"><g id="g686"><g class="st3"><g id="g688"><g id="g694"><path id="path696" class="st2" d="M229.4,111.5c0,3.4-2.7,6.1-6.1,6.1s-6.1-2.7-6.1-6.1,2.7-6.1,6.1-6.1,6.1,2.7,6.1,6.1"></path></g><g id="g698"><path id="path700" class="st2" d="M205.1,111.5c0,3.4-2.7,6.1-6.1,6.1s-6.1-2.7-6.1-6.1,2.7-6.1,6.1-6.1,6.1,2.7,6.1,6.1"></path></g><g id="g702"><path id="path704" class="st1" d="M247.6,135.8H52.4v-56.7c0-4.5,3.6-8.1,8.1-8.1h179.1c4.5,0,8.1,3.6,8.1,8.1v56.7Z"></path></g><g id="g706"><path id="path708" class="st1" d="M239.5,160.1H60.5c-4.5,0-8.1-3.6-8.1-8.1v-16.2h195.3v16.2c0,4.5-3.6,8.1-8.1,8.1Z"></path></g><g id="g710"><path id="path712" class="st1" d="M150,192.5v36.5"></path></g><g id="g714"><path id="path716" class="st1" d="M211.2,192.5c0,20.2,16.3,36.5,36.5,36.5"></path></g><g id="g718"><path id="path720" class="st1" d="M88.8,192.5c0,20.2-16.3,36.5-36.5,36.5"></path></g></g></g></g></g></svg>`
    };

    function getIcon(value) {
      const icon = ICON_MAP[value];
      if (!icon) return '<i class="fa fa-circle"></i>';
      if (icon.startsWith("<svg")) return icon;
      if (icon.startsWith("http://") || icon.startsWith("https://") || icon.startsWith("/")) {
        return `<img src="${icon}" alt="${value}" style="width:34px;height:34px;">`;
      }
      return `<i class="fa ${icon}"></i>`;
    }

    const cleanValue = opt.value.replace(/['"]+/g, "").trim();
    btn.innerHTML = `<div class="icon-container">${getIcon(cleanValue)}</div><span>${opt.text}</span>`;
    btn.classList.add("o_service_btn");

    btn.addEventListener("click", () => {
      select.value = opt.value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
      container.querySelectorAll("button").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
    });

    if (opt.selected) {
      btn.classList.add("selected");
    }

    container.appendChild(btn);
  });

  // --- Get phone field & fetch lead ---
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

  wrapper.dataset.widgetMounted = "1";
  console.log("[SERVICES] Widget + StageNav mounted ✅");
}

// Keep checking until mounted
const interval = setInterval(() => {
  injectServicesWidget();
}, 1000);
// /** @odoo-module **/
// import { rpc } from "@web/core/network/rpc";

// console.log("[SERVICES] widget bootstrap…");

// function injectServicesWidget() {
//   // Find wrapper
//   const wrapper = document.querySelector(" [name=services]");
//   if (!wrapper) return;

//   if (wrapper.dataset.widgetMounted === "1") {
//     console.log("[SERVICES] Already mounted, skipping.");
//     return;
//   }

//   const formEl = wrapper.closest(".o_form_view");

//   // --- Fetch Lead by Phone ---
//   async function fetchLeadByPhone(phone) {
//     try {
//       const response = await fetch(
//         `/vicidial/lead/${encodeURIComponent(phone)}`,
//         {
//           method: "GET",
//           headers: { "Content-Type": "application/json" },
//         }
//       );
//       const data = await response.json();
//       console.log("[SERVICES] Lead by phone:", data);

//       if (!data.error) {
//         setupStageNav(wrapper, data); // build stage nav after lead loaded
//       } else {
//         console.warn("[SERVICES] No lead found:", data.error);
//       }
//     } catch (err) {
//       console.error("[SERVICES] Error fetching lead:", err);
//     }
//   }

//   // --- Stage Navigation ---
//   function setupStageNav(wrapper, lead) {
//     const container = document.createElement("div");
//     container.className = "o_stage_nav_container";
//     container.style.cssText = `
//   position: fixed;
//   bottom: 0;
//   left: 0;
//   right: 0;
//   gap:20px;
//   display: flex;
//   justify-content: center; /* keeps prev left, next right */
//   padding: 12px 24px;
//   background: #fff;
//   border-top: 1px solid #ddd;
//   z-index: 1050; /* make sure it’s above Odoo UI */
// `;

//     const prevBtn = document.createElement("button");
//     prevBtn.className = "btn btn-secondary";
//     prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';

//     const nextBtn = document.createElement("button");
//     nextBtn.className = "btn btn-primary";
//     nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';

//     container.appendChild(prevBtn);
//     container.appendChild(nextBtn);

//     // Add to body instead of after the wrapper
//     document.body.appendChild(container);

//     function updateButtonState() {
//       const stage = parseInt(lead.lead_stage || "1");
//       prevBtn.disabled = stage <= 1;
//       nextBtn.disabled = stage >= 3;
//     }
//     updateButtonState();

//     // Prev click
//     prevBtn.addEventListener("click", async () => {
//       try {
//         prevBtn.disabled = true;
//         nextBtn.disabled = true; // Disable both during operation
//         prevBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';

//         console.log("Calling prev stage for lead:", lead.id);

//         const res = await rpc(
//           "/web/dataset/call_kw/crm.lead/action_prev_stage",
//           {
//             model: "crm.lead",
//             method: "action_prev_stage",
//             args: [[lead.id]],
//             kwargs: {},
//           }
//         );

//         console.log("Previous button response:", res);
//         if (res?.error) {
//           alert(res.error);
//           nextBtn.disabled = false;
//           prevBtn.disabled = false;
//           nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
//         } else {
//           // Reload the page to reflect changes in invisible fields
//           window.location.reload();
//         }

//         // Reload the page to reflect changes in invisible fields
//       } catch (err) {
//         console.error("[SERVICES] Prev stage error:", err);
//         alert("Failed to move to previous stage: " + (err.message || err));

//         // Re-enable buttons on error
//         prevBtn.disabled = false;
//         nextBtn.disabled = false;
//         prevBtn.innerHTML = '<i class="fa fa-arrow-left"></i> Previous';
//       }
//     });

//     // Next click
//     nextBtn.addEventListener("click", async () => {
//       try {
//         nextBtn.disabled = true;
//         prevBtn.disabled = true; // Disable both during operation
//         nextBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';

//         console.log("Calling next stage for lead:", lead.id);

//         const res = await rpc(
//           "/web/dataset/call_kw/crm.lead/action_next_stage",
//           {
//             model: "crm.lead",
//             method: "action_next_stage",
//             args: [[lead.id]],
//             kwargs: {},
//           }
//         );

//         console.log("Next button response:", res);

//         if (res?.error) {
//           alert(res.error);
//           nextBtn.disabled = false;
//           prevBtn.disabled = false;
//           nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
//         } else {
//           // Reload the page to reflect changes in invisible fields
//           window.location.reload();
//         }
//       } catch (err) {
//         console.error("[SERVICES] Next stage error:", err);
//         alert("Failed to move to next stage: " + (err.message || err));

//         // Re-enable buttons on error
//         nextBtn.disabled = false;
//         prevBtn.disabled = false;
//         nextBtn.innerHTML = 'Next <i class="fa fa-arrow-right"></i>';
//       }
//     });
//   }


//   // --- Existing Service Selector ---
//   const select = wrapper.querySelector("select");
//   if (!select) {
//     console.error("[SERVICES] No <select> found inside wrapper!");
//     return;
//   }
//   select.style.display = "none";

//   const container = document.createElement("div");
//   container.classList.add("o_service_selector");
//   select.insertAdjacentElement("afterend", container);

//   Array.from(select.options).forEach((opt) => {
//     if (!opt.value || opt.style.display === "none") return;

//     const btn = document.createElement("button");
//     btn.type = "button";
//     btn.dataset.value = opt.value;
//     const ICON_MAP = {
//       credit_card:"/vicidial/static/src/img/credit_card.png",
//       energy:"/vicidial/static/src/img/electricty_and_gas.png",
//       optus_nbn:"/vicidial/static/src/img/broadband.png",
//       home_moving:"/vicidial/static/src/img/home_moving.png",
//       business_loan:"https://utilityhub.com.au/wp-content/uploads/2025/05/interest.svg",
//       home_loan:"https://utilityhub.com.au/wp-content/uploads/2025/05/home.svg",
//       insurance:"/vicidial/static/src/img/insurance.png",
//       veu:`<svg xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg" xmlns:svgjs="http://svgjs.dev/svgjs" xmlns:xlink="http://www.w3.org/1999/xlink" id="svg678" width="300" height="300" viewBox="0 0 300 300"><defs><style>      .st0, .st1 {        fill: none;      }      .st2 {        fill: #e36e1c;      }      .st1 {        stroke: #e36e1c;        stroke-linecap: round;        stroke-linejoin: round;        stroke-width: 7.6px;      }      .st3 {        clip-path: url(#clippath);      }    </style><clipPath id="clippath"><rect class="st0" y="0" width="300" height="300"></rect></clipPath></defs><g id="g684"><g id="g686"><g class="st3"><g id="g688"><g id="g694"><path id="path696" class="st2" d="M229.4,111.5c0,3.4-2.7,6.1-6.1,6.1s-6.1-2.7-6.1-6.1,2.7-6.1,6.1-6.1,6.1,2.7,6.1,6.1"></path></g><g id="g698"><path id="path700" class="st2" d="M205.1,111.5c0,3.4-2.7,6.1-6.1,6.1s-6.1-2.7-6.1-6.1,2.7-6.1,6.1-6.1,6.1,2.7,6.1,6.1"></path></g><g id="g702"><path id="path704" class="st1" d="M247.6,135.8H52.4v-56.7c0-4.5,3.6-8.1,8.1-8.1h179.1c4.5,0,8.1,3.6,8.1,8.1v56.7Z"></path></g><g id="g706"><path id="path708" class="st1" d="M239.5,160.1H60.5c-4.5,0-8.1-3.6-8.1-8.1v-16.2h195.3v16.2c0,4.5-3.6,8.1-8.1,8.1Z"></path></g><g id="g710"><path id="path712" class="st1" d="M150,192.5v36.5"></path></g><g id="g714"><path id="path716" class="st1" d="M211.2,192.5c0,20.2,16.3,36.5,36.5,36.5"></path></g><g id="g718"><path id="path720" class="st1" d="M88.8,192.5c0,20.2-16.3,36.5-36.5,36.5"></path></g></g></g></g></g></svg>`
//     }

//     function getIcon(value) {
//       const icon = ICON_MAP[value];
//       if (!icon) return '<i class="fa fa-circle"></i>';
//       if (icon.startsWith("<svg")) return icon;
//       if (icon.startsWith("http://") || icon.startsWith("https://") || icon.startsWith("/"))  {
//         return `<img src="${icon}" alt="${value}" style="width:34px;height:34px;">`;
//       }
//       return `<i class="fa ${icon}"></i>`;
//     }

//     const cleanValue = opt.value.replace(/['"]+/g, "").trim();
//     btn.innerHTML = `<div class="icon-container">${getIcon(
//       cleanValue
//     )}</div><span>${opt.text}</span>`;
//     btn.classList.add("o_service_btn");

//     btn.addEventListener("click", () => {
//       select.value = opt.value;
//       select.dispatchEvent(new Event("change", { bubbles: true }));
//       container
//         .querySelectorAll("button")
//         .forEach((b) => b.classList.remove("selected"));
//       btn.classList.add("selected");
//     });

//     if (opt.selected) {
//       btn.classList.add("selected");
//     }

//     container.appendChild(btn);
//   });

//   // --- Get phone field & fetch lead ---
//   const phoneWrapper = formEl?.querySelector("[name=phone]");
//   const phoneValue =
//     phoneWrapper?.querySelector("input")?.value ||
//     phoneWrapper?.textContent?.trim();

//   if (phoneValue) {
//     console.log("Phone value:", phoneValue);
//     fetchLeadByPhone(phoneValue);
//   } else {
//     console.warn("[SERVICES] No phone found in form.");
//   }

//   wrapper.dataset.widgetMounted = "1";
//   console.log("[SERVICES] Widget + StageNav mounted ✅");
// }

// // Keep checking until mounted
// const interval = setInterval(() => {
//   injectServicesWidget();
// }, 1000);
