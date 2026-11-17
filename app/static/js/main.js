/**
 * ZeroPlate: Core Frontend Logic & Interactivity
 */

// Light / dark appearance preference
function applyAppTheme(theme, persist = true) {
    const selectedTheme = theme === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = selectedTheme;
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) themeMeta.setAttribute("content", selectedTheme === "dark" ? "#161c25" : "#f4f6f8");

    const toggle = document.getElementById("theme-toggle");
    if (toggle) {
        const nextLabel = selectedTheme === "dark" ? "Light mode" : "Dark mode";
        const nextIcon = selectedTheme === "dark" ? "sun" : "moon";
        toggle.setAttribute("aria-label", `Switch to ${nextLabel.toLowerCase()}`);
        toggle.setAttribute("title", `Switch to ${nextLabel.toLowerCase()}`);
        toggle.innerHTML = `<i data-lucide="${nextIcon}" class="w-4 h-4"></i><span class="theme-toggle-label">${nextLabel}</span>`;
        if (window.lucide) window.lucide.createIcons();
    }

    if (window.Chart) {
        const palette = getComputedStyle(document.documentElement);
        const textColor = palette.getPropertyValue("--muted").trim();
        const borderColor = palette.getPropertyValue("--border").trim();
        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = borderColor;

        // Restyle charts that are already visible when the user changes theme.
        Object.values(Chart.instances || {}).forEach((chart) => {
            chart.options.color = textColor;
            if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                chart.options.plugins.legend.labels.color = textColor;
            }
            if (chart.options.scales) {
                Object.values(chart.options.scales).forEach((scale) => {
                    if (scale.ticks) scale.ticks.color = textColor;
                    if (scale.grid) scale.grid.color = borderColor;
                });
            }
            chart.update("none");
        });
    }

    if (persist) {
        try { localStorage.setItem("zeroplate-theme", selectedTheme); } catch (_) {}
    }
}

function initAppTheme() {
    const currentTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    applyAppTheme(currentTheme, false);
    const toggle = document.getElementById("theme-toggle");
    if (toggle) {
        toggle.addEventListener("click", () => {
            const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            applyAppTheme(nextTheme);
        });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAppTheme, { once: true });
} else {
    initAppTheme();
}

// Toast notification helper
function showToast(message, type = "success") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "fixed bottom-5 right-5 z-50 flex flex-col space-y-2 pointer-events-none";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    const bgClass = type === "success" ? "bg-emerald-600 text-white" : 
                    type === "error" ? "bg-rose-600 text-white" : "bg-slate-800 text-white";

    toast.className = `pointer-events-auto flex items-center px-4 py-3 rounded-xl shadow-xl transform transition-all duration-300 translate-y-4 opacity-0 ${bgClass}`;
    toast.innerHTML = `
        <span class="mr-2 text-lg">${type === "success" ? "✓" : type === "error" ? "✕" : "ℹ"}</span>
        <span class="text-sm font-medium">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove("translate-y-4", "opacity-0");
    }, 20);

    setTimeout(() => {
        toast.classList.add("translate-y-4", "opacity-0");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Student Marketplace Reservation
async function claimSurpriseBox(listingId, title, price) {
    const studentName = prompt("Enter your name for the reservation:", "Student");
    if (!studentName) return;

    const studentRoll = prompt("Enter Student ID:", "STU-" + Math.floor(1000 + Math.random() * 9000));
    if (!studentRoll) return;

    try {
        const response = await fetch("/api/marketplace/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                listing_id: listingId,
                student_name: studentName,
                student_roll: studentRoll,
                quantity: 1
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert(`Reservation confirmed.\n\nCollection token: ${data.token}\nTotal: ₹${data.total_price}\nCollect by: ${data.pickup_until}\n\nShow this token to canteen staff when you collect your meal.`);
            window.location.reload();
        } else {
            alert("Error: " + (data.error || "Could not complete reservation"));
        }
    } catch (err) {
        alert("Failed to communicate with server: " + err.message);
    }
}

// NGO Claim Dispatch
async function claimNgoDonation(donationId, itemName, ngoId) {
    const volunteerName = prompt(`Assign volunteer name for picking up ${itemName}:`, "Volunteer Officer");
    if (!volunteerName) return;

    try {
        const response = await fetch("/api/ngo/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                donation_id: donationId,
                ngo_id: ngoId,
                volunteer_name: volunteerName
            })
        });

        const data = await response.json();
        if (response.ok) {
            showToast("Donation dispatch claimed! Ready for pickup verification.");
            setTimeout(() => window.location.reload(), 1000);
        } else {
            alert("Error: " + (data.error || "Failed to claim donation"));
        }
    } catch (err) {
        alert("Network error: " + err.message);
    }
}

// NGO Handover PIN Verification
async function verifyNgoPickup(donationId) {
    const enteredPin = prompt("Enter the 4-digit collection PIN provided by canteen staff:");
    if (!enteredPin) return;

    try {
        const response = await fetch("/api/ngo/verify-pickup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                donation_id: donationId,
                pin: enteredPin
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert("✅ " + data.message);
            window.location.reload();
        } else {
            alert("❌ " + (data.error || "PIN verification failed"));
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// Kitchen Production Status Update
async function updatePrepStatus(planId, newStatus) {
    try {
        const response = await fetch("/api/production/update-status", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                plan_id: planId,
                status: newStatus
            })
        });

        const data = await response.json();
        if (response.ok) {
            showToast(data.message);
            setTimeout(() => window.location.reload(), 800);
        } else {
            alert(data.error);
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// Demo clock controls are kept separate from the normal customer navigation.
async function setSimulationClock(timeStr, weather = "mild", closingWindow = 90) {
    let temp = 23.5;
    let rain = 0.0;
    if (weather === "rain") {
        temp = 20.0;
        rain = 18.0;
    } else if (weather === "hot") {
        temp = 34.0;
        rain = 0.0;
    }

    try {
        const response = await fetch("/api/simulation/update-state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                simulated_time: timeStr,
                is_exam_day: 0,
                temperature_c: temp,
                rainfall_mm: rain,
                closing_window_mins: Number(closingWindow) || 90
            })
        });

        const data = await response.json();
        if (response.ok) {
            showToast(data.message);
            if (data.escalation_actions && data.escalation_actions.length > 0) {
                alert(`⚡ Escalation Cycle Triggered at ${timeStr}:\n\n` + data.escalation_actions.join("\n"));
            }
            setTimeout(() => window.location.reload(), 1000);
        }
    } catch (err) {
        alert("Simulation error: " + err.message);
    }
}
