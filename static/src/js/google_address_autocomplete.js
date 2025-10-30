/** @odoo-module **/

// Load Google Maps API dynamically
function loadGoogleMapsAPI() {
  return new Promise((resolve, reject) => {
    if (window.google && window.google.maps && window.google.maps.places) {
      console.log("✅ Google Maps already loaded");
      resolve();
      return;
    }

    if (document.querySelector('script[src*="maps.googleapis.com"]')) {
      console.log("⏳ Google Maps script found, waiting for load...");
      const checkInterval = setInterval(() => {
        if (window.google && window.google.maps && window.google.maps.places) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);

      setTimeout(() => {
        clearInterval(checkInterval);
        reject(new Error("Google Maps loading timeout"));
      }, 10000);
      return;
    }

    console.log("📥 Loading Google Maps API...");
    const script = document.createElement("script");
    script.src =
      "https://maps.googleapis.com/maps/api/js?key=AIzaSyB8_jft7R5en3Q4rrnLqsnuGEyg5_W7CHU&libraries=places&callback=initGoogleMapsCallback";
    script.async = true;
    script.defer = true;

    window.initGoogleMapsCallback = () => {
      console.log("✅ Google Maps API loaded successfully");
      resolve();
    };

    script.onerror = () => {
      console.error("❌ Failed to load Google Maps API");
      reject(new Error("Failed to load Google Maps"));
    };

    document.head.appendChild(script);
  });
}

// Fix z-index for modal compatibility
function fixGoogleMapsZIndex() {
  if (document.getElementById('gmap-zindex-fix')) return;
  
  const style = document.createElement('style');
  style.id = 'gmap-zindex-fix';
  style.textContent = `
    .pac-container {
      z-index: 10000 !important;
    }
  `;
  document.head.appendChild(style);
  console.log("✅ Google Maps z-index fix applied");
}

// Initialize after Google Maps is loaded
async function initializeAutocomplete() {
  try {
    await loadGoogleMapsAPI();
    fixGoogleMapsZIndex();

    // Initial check
    initGoogleMapsForAddressFields();

    // Aggressive retry mechanism for modals
    const retryDelays = [300, 800, 1500, 3000, 5000];
    retryDelays.forEach(delay => {
      setTimeout(() => initGoogleMapsForAddressFields(), delay);
    });

    // Method 1: Watch for modal-specific DOM changes
    const observer = new MutationObserver((mutations) => {
      let shouldInit = false;
      
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === 1) {
            // Check for modal containers or form views
            if (node.matches && (
              node.matches('.modal') ||
              node.matches('.o_dialog') ||
              node.matches('.o_dialog_container') ||
              node.matches('.o_form_view') ||
              node.matches('.o_content') ||
              node.querySelector('.modal') ||
              node.querySelector('.o_dialog') ||
              node.querySelector('.o_form_view')
            )) {
              shouldInit = true;
            }
            
            // Check for our specific address fields
            const selectors = [
              'input[name="en_current_address"]',
              'input[name="cc_stage2_business_address"]',
              'input[name="cc_address"]',
              'input[name="in_supply_address"]',
              'input[name="optus_address"]',
              'input[name="dp_site_address_postcode"]',
              'input[name="dp_billing_address"]',
              'input[name="amex_address_1"]',
              'input[name="amex_address_2"]',
              'input[name="in_current_address"]',
              'input[name="do_installation_address"]',
              'input[name="hm_address"]',
              'input[name="hi_current_address"]',
            ];
            
            selectors.forEach(selector => {
              if (node.matches && (node.matches(selector) || node.querySelector(selector))) {
                shouldInit = true;
              }
            });
          }
        });
      });

      if (shouldInit) {
        console.log("🔄 Modal/Form detected via mutation");
        // Multiple retry attempts for modal content
        setTimeout(() => initGoogleMapsForAddressFields(), 100);
        setTimeout(() => initGoogleMapsForAddressFields(), 500);
        setTimeout(() => initGoogleMapsForAddressFields(), 1000);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // Method 2: Click event delegation for modal triggers
    document.addEventListener('click', (e) => {
      const target = e.target.closest('button, a, .o_form_button_edit, .o_form_button_create, [data-bs-toggle="modal"]');
      if (target) {
        console.log("🔄 Click detected, checking for modals...");
        setTimeout(() => initGoogleMapsForAddressFields(), 500);
        setTimeout(() => initGoogleMapsForAddressFields(), 1200);
        setTimeout(() => initGoogleMapsForAddressFields(), 2000);
      }
      
      // Specific handling for quick create "Add" button and record links
      if (e.target.closest('.o_form_button_save') || 
          e.target.closest('.o_list_button_add') ||
          e.target.closest('.o_data_row') ||
          e.target.closest('.o_field_widget')) {
        console.log("🔄 Quick create/record action detected");
        setTimeout(() => initGoogleMapsForAddressFields(), 300);
        setTimeout(() => initGoogleMapsForAddressFields(), 800);
        setTimeout(() => initGoogleMapsForAddressFields(), 1500);
        setTimeout(() => initGoogleMapsForAddressFields(), 2500);
      }
    }, true);

    // Method 3: Focus event as fallback
    document.addEventListener('focus', (e) => {
      const addressFieldNames = [
        'en_current_address',
        'cc_stage2_business_address',
        'cc_address',
        'in_supply_address',
        'optus_address',
        'dp_site_address_postcode',
        'dp_billing_address',
        'amex_address_1',
        'amex_address_2',
        'in_current_address',
        'do_installation_address',
        'hm_address',
        'hi_current_address',
      ];
      
      if (e.target.tagName === 'INPUT' && 
          addressFieldNames.includes(e.target.name) &&
          !e.target.hasAttribute('data-gmap-initialized')) {
        console.log("🔄 Address field focused, initializing...");
        setTimeout(() => initGoogleMapsForAddressFields(), 150);
      }
    }, true);

    // Method 4: Watch for Odoo's dialog/modal rendering
    // Odoo uses owl framework - watch for component updates
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
      originalPushState.apply(this, args);
      console.log("🔄 URL changed, checking fields...");
      setTimeout(() => initGoogleMapsForAddressFields(), 400);
      setTimeout(() => initGoogleMapsForAddressFields(), 1000);
    };
    
    history.replaceState = function(...args) {
      originalReplaceState.apply(this, args);
      setTimeout(() => initGoogleMapsForAddressFields(), 400);
    };

    // Method 5: Periodic check (aggressive for modals)
    setInterval(() => {
      initGoogleMapsForAddressFields();
    }, 2000);

    // Method 5b: Extra aggressive check when modal is visible
    setInterval(() => {
      const hasModal = document.querySelector('.modal.show, .o_dialog, .o_technical_modal');
      if (hasModal) {
        // Modal is open, check more frequently
        initGoogleMapsForAddressFields();
      }
    }, 500); // Check every 500ms when modal might be open

    // Method 6: Hook into Odoo's event bus if available
    if (window.odoo && window.odoo.__DEBUG__ && window.odoo.__DEBUG__.services) {
      console.log("🔄 Attempting to hook Odoo event system...");
      try {
        // Try to intercept dialog/modal events
        const originalOpen = window.DialogManager?.open;
        if (originalOpen) {
          window.DialogManager.open = function(...args) {
            console.log("🔄 Dialog opened via manager");
            const result = originalOpen.apply(this, args);
            setTimeout(() => initGoogleMapsForAddressFields(), 500);
            setTimeout(() => initGoogleMapsForAddressFields(), 1200);
            return result;
          };
        }
      } catch (e) {
        console.log("⚠️ Could not hook DialogManager:", e.message);
      }
    }

    console.log("👁️ All watchers initialized");
  } catch (error) {
    console.error("❌ Google Maps initialization failed:", error);
  }
}

function initGoogleMapsForAddressFields() {
  if (!window.google || !window.google.maps || !window.google.maps.places) {
    console.warn("⚠️ Google Maps not available");
    return;
  }

  const selectors = [
    'input[name="en_current_address"]',
    '[name="en_current_address"] input',
    'input[name="cc_stage2_business_address"]',
    '[name="cc_stage2_business_address"] input',
    'input[name="cc_address"]',
    '[name="cc_address"] input',
    'input[name="in_supply_address"]',
    '[name="in_supply_address"] input',
    'input[name="optus_address"]',
    '[name="optus_address"] input',
    'input[name="dp_site_address_postcode"]',
    '[name="dp_site_address_postcode"] input',
    'input[name="dp_billing_address"]',
    '[name="dp_billing_address"] input',
    'input[name="amex_address_1"]',
    '[name="amex_address_1"] input',
    'input[name="amex_address_2"]',
    '[name="amex_address_2"] input',
    'input[name="in_current_address"]',
    '[name="in_current_address"] input',    
    'input[name="do_installation_address"]',
    '[name="do_installation_address"] input',
    'input[name="hm_address"]',
    '[name="hm_address"] input',
    'input[name="hi_current_address"]',
    '[name="hi_current_address"] input',
  ];

  let addressInputs = [];
  for (const selector of selectors) {
    const elements = document.querySelectorAll(
      `${selector}:not([data-gmap-initialized])`
    );
    if (elements.length > 0) {
      addressInputs.push(...Array.from(elements));
    }
  }

  if (addressInputs.length === 0) {
    return;
  }

  console.log(`✅ Found ${addressInputs.length} uninitialized field(s)`);

  addressInputs.forEach((input) => {
    if (input.hasAttribute("data-gmap-initialized")) return;

    // Check if input is visible (important for modal detection)
    const isVisible = input.offsetParent !== null;
    if (!isVisible) {
      console.log("⏭️ Field not visible yet, skipping:", input.name);
      return;
    }

    input.setAttribute("data-gmap-initialized", "true");

    try {
      const autocomplete = new google.maps.places.Autocomplete(input, {
        types: ["address"],
      });

      // Ensure dropdown appears on top
      input.addEventListener('focus', function() {
        setTimeout(() => {
          const containers = document.querySelectorAll('.pac-container');
          containers.forEach(c => c.style.zIndex = '10000');
        }, 100);
      });

      autocomplete.addListener("place_changed", function () {
        const place = autocomplete.getPlace();

        if (!place || !place.formatted_address) {
          console.warn("No valid place selected");
          return;
        }

        console.log("✅ Place selected:", place.formatted_address);

        input.value = place.formatted_address;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));

        fillRelatedAddressFields(place);
      });

      console.log("✅ Google Autocomplete attached to:", input.name);
    } catch (error) {
      console.error("❌ Failed to attach autocomplete:", error);
      input.removeAttribute("data-gmap-initialized");
    }
  });
}

function fillRelatedAddressFields(place) {
  const components = place.address_components || [];

  let city = "",
    state = "",
    country = "",
    zip = "";

  components.forEach((component) => {
    const types = component.types;

    if (types.includes("locality")) {
      city = component.long_name;
    }
    if (types.includes("administrative_area_level_1")) {
      state = component.long_name;
    }
    if (types.includes("country")) {
      country = component.long_name;
    }
    if (types.includes("postal_code")) {
      zip = component.long_name;
    }
  });

  updateFieldIfExists("en_current_city", city);
  updateFieldIfExists("en_current_state", state);
  updateFieldIfExists("en_current_country", country);
  updateFieldIfExists("en_current_zip", zip);
}

function updateFieldIfExists(fieldName, value) {
  if (!value) return;

  const field = document.querySelector(
    `input[name="${fieldName}"], select[name="${fieldName}"]`
  );

  if (field) {
    field.value = value;
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  }
}

// Start initialization
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeAutocomplete);
} else {
  initializeAutocomplete();
}

console.log("🔍 Google Maps Autocomplete module loaded");

// Debug helper
window.debugGoogleMapsFields = function () {
  console.log("=== Debug Info ===");
  console.log(
    "Google Maps loaded?",
    !!(window.google && window.google.maps && window.google.maps.places)
  );

  const allInputs = document.querySelectorAll(
    'input[name*="address"]'
  );
  console.log(
    `Found ${allInputs.length} address-related fields:`,
    Array.from(allInputs).map((i) => ({
      name: i.name,
      visible: i.offsetParent !== null,
      initialized: i.hasAttribute("data-gmap-initialized")
    }))
  );

  console.log("Attempting force initialization...");
  initGoogleMapsForAddressFields();
};
// /** @odoo-module **/

// // Load Google Maps API dynamically
// function loadGoogleMapsAPI() {
//   return new Promise((resolve, reject) => {
//     // Check if already loaded
//     if (window.google && window.google.maps && window.google.maps.places) {
//       console.log("✅ Google Maps already loaded");
//       resolve();
//       return;
//     }

//     // Check if script is already being loaded
//     if (document.querySelector('script[src*="maps.googleapis.com"]')) {
//       console.log("⏳ Google Maps script found, waiting for load...");
//       const checkInterval = setInterval(() => {
//         if (window.google && window.google.maps && window.google.maps.places) {
//           clearInterval(checkInterval);
//           // console.log("✅ Google Maps loaded");
//           resolve();
//         }
//       }, 100);

//       // Timeout after 10 seconds
//       setTimeout(() => {
//         clearInterval(checkInterval);
//         reject(new Error("Google Maps loading timeout"));
//       }, 10000);
//       return;
//     }

//     // Load the script dynamically
//     console.log("📥 Loading Google Maps API...");
//     const script = document.createElement("script");
//     script.src =
//       "https://maps.googleapis.com/maps/api/js?key=AIzaSyB8_jft7R5en3Q4rrnLqsnuGEyg5_W7CHU&libraries=places&callback=initGoogleMapsCallback";
//     script.async = true;
//     script.defer = true;

//     // Global callback for Google Maps
//     window.initGoogleMapsCallback = () => {
//       console.log("✅ Google Maps API loaded successfully");
//       resolve();
//     };

//     script.onerror = () => {
//       console.error("❌ Failed to load Google Maps API");
//       reject(new Error("Failed to load Google Maps"));
//     };

//     document.head.appendChild(script);
//   });
// }

// async function initializeAutocomplete() {
//   try {
//     await loadGoogleMapsAPI();

//     // Initial check
//     initGoogleMapsForAddressFields();

//     // Retry mechanism
//     [500, 1500, 3000].forEach(delay => {
//       setTimeout(() => initGoogleMapsForAddressFields(), delay);
//     });

//     // Modal open detection
//     document.addEventListener('click', (e) => {
//       if (e.target.closest('[data-bs-toggle="modal"]') || 
//           e.target.closest('.o_form_button_edit') ||
//           e.target.closest('.o_form_button_create')) {
//         setTimeout(() => initGoogleMapsForAddressFields(), 500);
//         setTimeout(() => initGoogleMapsForAddressFields(), 1500);
//       }
//     });

//     // Field focus fallback
//     document.addEventListener('focus', (e) => {
//       const addressSelectors = [
//         'input[name="en_current_address"]',
//         'input[name="cc_stage2_business_address"]',
//         // ... add your other selectors
//       ];
      
//       if (addressSelectors.some(sel => e.target.matches(sel)) &&
//           !e.target.hasAttribute('data-gmap-initialized')) {
//         setTimeout(() => initGoogleMapsForAddressFields(), 100);
//       }
//     }, true);

//     // Enhanced MutationObserver
//     const observer = new MutationObserver((mutations) => {
//       const hasRelevantChanges = mutations.some((mutation) => {
//         return Array.from(mutation.addedNodes).some((node) => {
//           if (node.nodeType === 1) {
//             return node.matches && (
//               node.matches('.modal, .o_dialog, .o_form_view') ||
//               node.querySelector('input[name="en_current_address"]')
//             );
//           }
//           return false;
//         });
//       });

//       if (hasRelevantChanges) {
//         setTimeout(() => initGoogleMapsForAddressFields(), 300);
//       }
//     });

//     observer.observe(document.body, {
//       childList: true,
//       subtree: true,
//     });

//   } catch (error) {
//     console.error("❌ Google Maps initialization failed:", error);
//   }
// }

// // Initialize after Google Maps is loaded
// // async function initializeAutocomplete() {
// //   try {
// //     await loadGoogleMapsAPI();

// //     // Try immediate initialization
// //     initGoogleMapsForAddressFields();

// //     // Retry after short delay (for Odoo's async rendering)
// //     setTimeout(() => {
// //       console.log("🔄 Retrying field detection...");  
// //       initGoogleMapsForAddressFields();
// //     }, 1000);

// //     // Another retry after longer delay
// //     setInterval(() => {
// //       // console.log("🔄 Second retry...");
// //       initGoogleMapsForAddressFields();
// //     }, 3000);

// //     // Watch for dynamically added fields
// //     const observer = new MutationObserver((mutations) => {
// //       // Check if mutations affect our target field
// //       const shouldCheck = mutations.some((mutation) => {
// //         return Array.from(mutation.addedNodes).some((node) => {
// //           if (node.nodeType === 1) {
// //             // Element node
// //             return (
// //               node.matches &&
// //               (node.matches('input[name="en_current_address"]') ||
// //                 node.matches('textarea[name="en_current_address"]') ||
// //                 node.querySelector(
// //                   'input[name="en_current_address"], textarea[name="en_current_address"]'
// //                 ))
// //             );
// //           }
// //           return false;
// //         });
// //       });

// //       if (shouldCheck) {
// //         // console.log("🔄 Field detected in DOM mutation");
// //         initGoogleMapsForAddressFields();
// //       }
// //     });

// //     observer.observe(document.body, {
// //       childList: true,
// //       subtree: true,
// //     });

// //     console.log("👁️ Observer watching for field changes");
// //   } catch (error) {
// //     console.error("❌ Google Maps initialization failed:", error);
// //   }
// // }

// function initGoogleMapsForAddressFields() {
//   // Double check Google Maps is loaded
//   if (!window.google || !window.google.maps || !window.google.maps.places) {
//     console.warn("⚠️ Google Maps not available");
//     return;
//   }

//   // Try multiple selectors for Odoo 18 field structure
//   const selectors = [
//     'input[name="en_current_address"]',
//     '[name="en_current_address"] input',
//     'input[name="cc_stage2_business_address"]',
//     '[name="cc_stage2_business_address"] input',
//     'input[name="cc_address"]',
//     '[name="cc_address"] input',
//     'input[name="in_supply_address"]',
//     '[name="in_supply_address"] input',
//     'input[name="optus_address"]',
//     '[name="optus_address"] input',
//     'input[name="dp_site_address_postcode"]',
//     '[name="dp_site_address_postcode"] input',
//     'input[name="dp_billing_address"]',
//     '[name="dp_billing_address"] input',
//     'input[name="amex_address_1"]',
//     '[name="amex_address_1"] input',
//     'input[name="amex_address_2"]',
//     '[name="amex_address_2"] input',
//     'input[name="in_current_address"]',
//     '[name="in_current_address"] input',    
//     'input[name="do_installation_address"]',
//     '[name="do_installation_address"] input',
//     'input[name="hm_address"]',
//     '[name="hm_address"] input',
//     'input[name="hi_current_address"]',
//     '[name="hi_current_address"] input',
//   ];

//   let addressInputs = [];
//   for (const selector of selectors) {
//     const elements = document.querySelectorAll(
//       `${selector}:not([data-gmap-initialized])`
//     );
//     if (elements.length > 0) {
//       addressInputs = Array.from(elements);
//       console.log(
//         // `✅ Found ${elements.length} field(s) with selector: ${selector}`
//       );
//       break;
//     }
//   }

//   if (addressInputs.length === 0) {
//     // console.log("⏳ No address fields found yet, will retry on DOM changes...");
//     return;
//   }

//   addressInputs.forEach((input) => {
//   if (input.hasAttribute("data-gmap-initialized")) return;

//   input.setAttribute("data-gmap-initialized", "true");

//   try {
//     const autocomplete = new google.maps.places.Autocomplete(input, {
//       types: ["address"],
//     });

//     // Set z-index after autocomplete is created
//     google.maps.event.addListenerOnce(autocomplete, 'place_changed', function() {
//       const pacContainers = document.querySelectorAll('.pac-container');
//       pacContainers.forEach(container => {
//         container.style.zIndex = '10000';
//       });
//     });
    
//     // Also set it when dropdown opens
//     input.addEventListener('focus', function() {
//       setTimeout(() => {
//         const pacContainers = document.querySelectorAll('.pac-container');
//         pacContainers.forEach(container => {
//           container.style.zIndex = '10000';
//         });
//       }, 100);
//     });

//     autocomplete.addListener("place_changed", function () {
//       // ... your existing place_changed code
//     });

//   } catch (error) {
//     console.error("❌ Failed to attach autocomplete:", error);
//   }
// });

//   // addressInputs.forEach((input) => {
//   //   if (input.hasAttribute("data-gmap-initialized")) return;

//   //   input.setAttribute("data-gmap-initialized", "true");

//   //   try {
//   //     const autocomplete = new google.maps.places.Autocomplete(input, {
//   //       types: ["address"],
//   //       // componentRestrictions: { country: "pk" },
//   //     });

//   //     autocomplete.addListener("place_changed", function () {
//   //       const place = autocomplete.getPlace();

//   //       if (!place || !place.formatted_address) {
//   //         console.warn("No valid place selected");
//   //         return;
//   //       }

//   //       console.log("✅ Place selected:", place.formatted_address);

//   //       // Update the address field
//   //       input.value = place.formatted_address;

//   //       // Trigger Odoo's change event
//   //       input.dispatchEvent(new Event("input", { bubbles: true }));
//   //       input.dispatchEvent(new Event("change", { bubbles: true }));

//   //       // Extract and fill related fields
//   //       fillRelatedAddressFields(place);
//   //     });

//   //     console.log("✅ Google Autocomplete attached to:", input.name);
//   //   } catch (error) {
//   //     console.error("❌ Failed to attach autocomplete:", error);
//   //   }
//   // });
// }

// function fillRelatedAddressFields(place) {
//   const components = place.address_components || [];

//   let city = "",
//     state = "",
//     country = "",
//     zip = "";

//   components.forEach((component) => {
//     const types = component.types;

//     if (types.includes("locality")) {
//       city = component.long_name;
//     }
//     if (types.includes("administrative_area_level_1")) {
//       state = component.long_name;
//     }
//     if (types.includes("country")) {
//       country = component.long_name;
//     }
//     if (types.includes("postal_code")) {
//       zip = component.long_name;
//     }
//   });

//   // Find and update related fields
//   updateFieldIfExists("en_current_city", city);
//   updateFieldIfExists("en_current_state", state);
//   updateFieldIfExists("en_current_country", country);
//   updateFieldIfExists("en_current_zip", zip);
// }

// function updateFieldIfExists(fieldName, value) {
//   if (!value) return;

//   const field = document.querySelector(
//     `input[name="${fieldName}"], select[name="${fieldName}"]`
//   );

//   if (field) {
//     field.value = value;
//     field.dispatchEvent(new Event("input", { bubbles: true }));
//     field.dispatchEvent(new Event("change", { bubbles: true }));
//     // console.log(`✅ Updated ${fieldName}:`, value);
//   }
// }

// // Start initialization when DOM is ready
// if (document.readyState === "loading") {
//   document.addEventListener("DOMContentLoaded", initializeAutocomplete);
// } else {
//   initializeAutocomplete();
// }

// console.log("🔍 Google Maps Autocomplete module loaded");

// // Debug helper - expose function globally to test manually
// window.debugGoogleMapsFields = function () {
//   // console.log("=== Debug Info ===");
//   // console.log(
//   //   "Google Maps loaded?",
//   //   !!(window.google && window.google.maps && window.google.maps.places)
//   // );

//   const allInputs = document.querySelectorAll(
//     'input[name*="address"], textarea[name*="address"]'
//   );
//   console.log(
//     `Found ${allInputs.length} address-related fields:`,
//     Array.from(allInputs).map((i) => i.name)
//   );

//   const targetField = document.querySelector(
//     'input[name="en_current_address"], textarea[name="en_current_address"]'
//   );
//   console.log("Target field found?", !!targetField);

//   if (targetField) {
//     console.log("Field details:", {
//       tag: targetField.tagName,
//       name: targetField.name,
//       type: targetField.type,
//       initialized: targetField.hasAttribute("data-gmap-initialized"),
//     });
//   }

//   // Try to force initialization
//   console.log("Attempting to initialize...");
//   initGoogleMapsForAddressFields();
// };
