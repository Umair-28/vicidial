/** @odoo-module **/

setInterval(() => {
    const chatter = document.querySelector(".o-mail-ChatterContainer");

    // Do nothing if chatter doesn't exist yet
    if (!chatter) return;

    // Create collapse/expand button if not present
    let btn = document.querySelector("#chatterToggleButton");

    if (!btn) {
        console.log("Chatter detected — injecting collapsible button");

        // Create button
        btn = document.createElement("button");
        btn.id = "chatterToggleButton";
        btn.className = "btn btn-secondary mb-2";
        btn.innerText = "Expand Chatter";  // because default is collapsed

        // Collapse chatter by default
        chatter.style.display = "none";

        // Click handler
        btn.addEventListener("click", () => {
            const isCollapsed = chatter.style.display === "none";
            chatter.style.display = isCollapsed ? "block" : "none";
            btn.innerText = isCollapsed ? "Collapse Chatter" : "Expand Chatter";
        });

        // Insert before chatter
        chatter.parentNode.insertBefore(btn, chatter);

        return;
    }

}, 500);  // Faster and lighter interval

// /** @odoo-module **/

// // Run when backend is ready
// setInterval(() => {
//     // Select chatter container
//     const chatter = document.querySelector(".o-mail-ChatterContainer");

//     // If chatter exists AND button not already added
//     if (chatter && !document.querySelector("#chatterToggleButton")) {

//         console.log("Chatter detected — injecting collapse button");

//         // Create button
//         const btn = document.createElement("button");
//         btn.id = "chatterToggleButton";
//         btn.className = "btn btn-secondary mb-2";
//         btn.innerText = "Collapse Chatter";

//         // Add functionality
//         btn.addEventListener("click", () => {
//             const isCollapsed = chatter.style.display === "none";
//             chatter.style.display = isCollapsed ? "block" : "none";
//             btn.innerText = isCollapsed ? "Collapse Chatter" : "Expand Chatter";
//         });

//         // Insert button BEFORE chatter
//         chatter.parentNode.insertBefore(btn, chatter);
//     }

// }, 800);  // Runs every 0.8 seconds
// console.log("chatter collapssed >>>>>>>>>>>>>>>")