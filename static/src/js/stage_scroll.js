/** @odoo-module **/

import { registry } from "@web/core/registry";

// Custom client action
function scrollAndReload(env, action) {
    const stageNumber = action.params?.stage_number;
    const unlock = action.params?.unlock;
    
    if (stageNumber) {
        console.log("✅ Storing stage for scroll:", stageNumber, "unlock:", unlock);
        sessionStorage.setItem("scroll_to_stage", stageNumber);
    }
    
    // Trigger reload
    return env.services.action.doAction({
        type: "ir.actions.client",
        tag: "reload",
    });
}

registry.category("actions").add("scroll_and_reload", scrollAndReload);

// Main scroll function
function checkAndScrollToStage() {
    const stageToScroll = sessionStorage.getItem("scroll_to_stage");
    if (!stageToScroll) {
        return false;
    }

    console.log("🔍 Looking for stage:", stageToScroll);
    
    // Try to find the section
    const section = document.querySelector(`.stage-section.stage-${stageToScroll}`);
    
    if (!section) {
        console.log("⚠️ Section .stage-" + stageToScroll + " not found");
        
        // Debug: show what exists
        const allSections = document.querySelectorAll('[class*="stage-"]');
        console.log("📊 Found stage elements:", allSections.length);
        allSections.forEach(el => {
            console.log("  -", el.className);
        });
        
        return false;
    }

    console.log("✅ Found section! Scrolling...");
    
    // Scroll into view
    section.scrollIntoView({ 
        behavior: "smooth", 
        block: "start",
        inline: "nearest"
    });
    
    // Highlight effect
    const originalBg = section.style.backgroundColor;
    const originalBorder = section.style.border;
    const originalShadow = section.style.boxShadow;
    
    section.style.transition = "all 0.5s ease";
    section.style.backgroundColor = "#fff3cd";
    section.style.boxShadow = "0 0 20px rgba(255, 193, 7, 0.8)";
    section.style.border = "3px solid #ffc107";
    section.style.borderRadius = "8px";
    section.style.padding = "15px";
    
    setTimeout(() => {
        section.style.backgroundColor = originalBg;
        section.style.boxShadow = originalShadow;
        section.style.border = originalBorder;
    }, 3000);
    
    // Clear the flag
    sessionStorage.removeItem("scroll_to_stage");
    console.log("🧹 Cleared scroll_to_stage");
    
    return true;
}

// Retry mechanism with multiple attempts
let attemptCount = 0;
const maxAttempts = 10;

function tryScroll() {
    attemptCount++;
    console.log(`🔄 Scroll attempt ${attemptCount}/${maxAttempts}`);
    
    const success = checkAndScrollToStage();
    
    if (success) {
        console.log("✅ Scroll successful!");
        attemptCount = 0;
        return;
    }
    
    if (attemptCount < maxAttempts) {
        setTimeout(tryScroll, 500);
    } else {
        console.log("❌ Max attempts reached, giving up");
        attemptCount = 0;
        sessionStorage.removeItem("scroll_to_stage");
    }
}

// Watch for when Odoo renders the page
const observer = new MutationObserver((mutations) => {
    // Only check if we have a stage to scroll to
    if (sessionStorage.getItem("scroll_to_stage")) {
        // Debounce
        clearTimeout(window.scrollDebounce);
        window.scrollDebounce = setTimeout(() => {
            checkAndScrollToStage();
        }, 3000);
    }
});

// Start observing
function startObserving() {
    console.log("👀 Starting observer");
    
    if (document.body) {
        observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
        
        // Initial check
        if (sessionStorage.getItem("scroll_to_stage")) {
            console.log("🚀 Initial scroll check");
            setTimeout(tryScroll, 3000);
        }
    }
}

// Initialize when ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startObserving);
} else {
    startObserving();
}

console.log("🎯 Stage Scroll Helper loaded");

// /** @odoo-module **/

// import { registry } from "@web/core/registry";

// // Custom client action
// function scrollAndReload(env, action) {
//     const stageNumber = action.params?.stage_number;
    
//     if (stageNumber) {
//         console.log("✅ Storing stage for scroll:", stageNumber);
//         sessionStorage.setItem("scroll_to_stage", stageNumber);
//     }
    
//     // Trigger reload
//     return env.services.action.doAction({
//         type: "ir.actions.client",
//         tag: "reload",
//     });
// }

// registry.category("actions").add("scroll_and_reload", scrollAndReload);

// // Main scroll function
// function checkAndScrollToStage() {
//     const stageToScroll = sessionStorage.getItem("scroll_to_stage");
//     if (!stageToScroll) {
//         return false;
//     }

//     console.log("🔍 Looking for stage:", stageToScroll);
    
//     // Try to find the section
//     const section = document.querySelector(`.stage-section.stage-${stageToScroll}`);
    
//     if (!section) {
//         console.log("⚠️ Section .stage-" + stageToScroll + " not found");
        
//         // Debug: show what exists
//         const allSections = document.querySelectorAll('[class*="stage-"]');
//         console.log("📊 Found stage elements:", allSections.length);
//         allSections.forEach(el => {
//             console.log("  -", el.className);
//         });
        
//         return false;
//     }

//     console.log("✅ Found section! Scrolling...");
    
//     // Scroll into view
//     section.scrollIntoView({ 
//         behavior: "smooth", 
//         block: "center",
//         inline: "nearest"
//     });
    
//     // Highlight effect
//     const originalBg = section.style.backgroundColor;
//     const originalBorder = section.style.border;
//     const originalShadow = section.style.boxShadow;
    
//     section.style.transition = "all 0.5s ease";
//     section.style.backgroundColor = "#fff3cd";
//     section.style.boxShadow = "0 0 20px rgba(255, 193, 7, 0.8)";
//     section.style.border = "3px solid #ffc107";
//     section.style.borderRadius = "8px";
//     section.style.padding = "15px";
    
//     setTimeout(() => {
//         section.style.backgroundColor = originalBg;
//         section.style.boxShadow = originalShadow;
//         section.style.border = originalBorder;
//     }, 5000);
    
//     // Clear the flag
//     sessionStorage.removeItem("scroll_to_stage");
//     console.log("🧹 Cleared scroll_to_stage");
    
//     return true;
// }

// // Retry mechanism with multiple attempts
// let attemptCount = 0;
// const maxAttempts = 10;

// function tryScroll() {
//     attemptCount++;
//     console.log(`🔄 Scroll attempt ${attemptCount}/${maxAttempts}`);
    
//     const success = checkAndScrollToStage();
    
//     if (success) {
//         console.log("✅ Scroll successful!");
//         attemptCount = 0;
//         return;
//     }
    
//     if (attemptCount < maxAttempts) {
//         setTimeout(tryScroll, 500);
//     } else {
//         console.log("❌ Max attempts reached, giving up");
//         attemptCount = 0;
//         sessionStorage.removeItem("scroll_to_stage");
//     }
// }

// // Watch for when Odoo renders the page
// const observer = new MutationObserver((mutations) => {
//     // Only check if we have a stage to scroll to
//     if (sessionStorage.getItem("scroll_to_stage")) {
//         // Debounce
//         clearTimeout(window.scrollDebounce);
//         window.scrollDebounce = setTimeout(() => {
//             checkAndScrollToStage();
//         }, 200);
//     }
// });

// // Start observing
// function startObserving() {
//     console.log("👀 Starting observer");
    
//     if (document.body) {
//         observer.observe(document.body, { 
//             childList: true, 
//             subtree: true 
//         });
        
//         // Initial check
//         if (sessionStorage.getItem("scroll_to_stage")) {
//             console.log("🚀 Initial scroll check");
//             setInterval(tryScroll, 500);
//         }
//     }
// }

// // Initialize when ready
// if (document.readyState === "loading") {
//     document.addEventListener("DOMContentLoaded", startObserving);
// } else {
//     startObserving();
// }

// console.log("🎯 Stage Scroll Helper loaded");