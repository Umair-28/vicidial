/** @odoo-module **/

// Load Google Maps API dynamically
function loadGoogleMapsAPI() {
  return new Promise((resolve, reject) => {
    // Check if already loaded
    if (window.google && window.google.maps && window.google.maps.places) {
      console.log("✅ Google Maps already loaded");
      resolve();
      return;
    }

    // Check if script is already being loaded
    if (document.querySelector('script[src*="maps.googleapis.com"]')) {
      console.log("⏳ Google Maps script found, waiting for load...");
      const checkInterval = setInterval(() => {
        if (window.google && window.google.maps && window.google.maps.places) {
          clearInterval(checkInterval);
          // console.log("✅ Google Maps loaded");
          resolve();
        }
      }, 100);

      // Timeout after 10 seconds
      setTimeout(() => {
        clearInterval(checkInterval);
        reject(new Error("Google Maps loading timeout"));
      }, 10000);
      return;
    }

    // Load the script dynamically
    console.log("📥 Loading Google Maps API...");
    const script = document.createElement("script");
    script.src =
      "https://maps.googleapis.com/maps/api/js?key=AIzaSyB8_jft7R5en3Q4rrnLqsnuGEyg5_W7CHU&libraries=places&callback=initGoogleMapsCallback";
    script.async = true;
    script.defer = true;

    // Global callback for Google Maps
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

// Initialize after Google Maps is loaded
async function initializeAutocomplete() {
  try {
    await loadGoogleMapsAPI();

    // Try immediate initialization
    initGoogleMapsForAddressFields();

    // Retry after short delay (for Odoo's async rendering)
    setTimeout(() => {
      console.log("🔄 Retrying field detection...");  
      initGoogleMapsForAddressFields();
    }, 1000);

    // Another retry after longer delay
    setInterval(() => {
      // console.log("🔄 Second retry...");
      initGoogleMapsForAddressFields();
    }, 3000);

    // Watch for dynamically added fields
    const observer = new MutationObserver((mutations) => {
      // Check if mutations affect our target field
      const shouldCheck = mutations.some((mutation) => {
        return Array.from(mutation.addedNodes).some((node) => {
          if (node.nodeType === 1) {
            // Element node
            return (
              node.matches &&
              (node.matches('input[name="en_current_address"]') ||
                node.matches('textarea[name="en_current_address"]') ||
                node.querySelector(
                  'input[name="en_current_address"], textarea[name="en_current_address"]'
                ))
            );
          }
          return false;
        });
      });

      if (shouldCheck) {
        // console.log("🔄 Field detected in DOM mutation");
        initGoogleMapsForAddressFields();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    console.log("👁️ Observer watching for field changes");
  } catch (error) {
    console.error("❌ Google Maps initialization failed:", error);
  }
}

function initGoogleMapsForAddressFields() {
  // Double check Google Maps is loaded
  if (!window.google || !window.google.maps || !window.google.maps.places) {
    console.warn("⚠️ Google Maps not available");
    return;
  }

  // Try multiple selectors for Odoo 18 field structure
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
      addressInputs = Array.from(elements);
      console.log(
        // `✅ Found ${elements.length} field(s) with selector: ${selector}`
      );
      break;
    }
  }

  if (addressInputs.length === 0) {
    // console.log("⏳ No address fields found yet, will retry on DOM changes...");
    return;
  }

  addressInputs.forEach((input) => {
    if (input.hasAttribute("data-gmap-initialized")) return;

    input.setAttribute("data-gmap-initialized", "true");

    try {
      const autocomplete = new google.maps.places.Autocomplete(input, {
        types: ["address"],
        // componentRestrictions: { country: "pk" },
      });

      autocomplete.addListener("place_changed", function () {
        const place = autocomplete.getPlace();

        if (!place || !place.formatted_address) {
          console.warn("No valid place selected");
          return;
        }

        console.log("✅ Place selected:", place.formatted_address);

        // Update the address field
        input.value = place.formatted_address;

        // Trigger Odoo's change event
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));

        // Extract and fill related fields
        fillRelatedAddressFields(place);
      });

      console.log("✅ Google Autocomplete attached to:", input.name);
    } catch (error) {
      console.error("❌ Failed to attach autocomplete:", error);
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

  // Find and update related fields
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
    // console.log(`✅ Updated ${fieldName}:`, value);
  }
}

// Start initialization when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeAutocomplete);
} else {
  initializeAutocomplete();
}

console.log("🔍 Google Maps Autocomplete module loaded");

// Debug helper - expose function globally to test manually
window.debugGoogleMapsFields = function () {
  // console.log("=== Debug Info ===");
  // console.log(
  //   "Google Maps loaded?",
  //   !!(window.google && window.google.maps && window.google.maps.places)
  // );

  const allInputs = document.querySelectorAll(
    'input[name*="address"], textarea[name*="address"]'
  );
  console.log(
    `Found ${allInputs.length} address-related fields:`,
    Array.from(allInputs).map((i) => i.name)
  );

  const targetField = document.querySelector(
    'input[name="en_current_address"], textarea[name="en_current_address"]'
  );
  console.log("Target field found?", !!targetField);

  if (targetField) {
    console.log("Field details:", {
      tag: targetField.tagName,
      name: targetField.name,
      type: targetField.type,
      initialized: targetField.hasAttribute("data-gmap-initialized"),
    });
  }

  // Try to force initialization
  console.log("Attempting to initialize...");
  initGoogleMapsForAddressFields();
};
