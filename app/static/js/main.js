/**
 * ZeroPlate: Core Frontend Logic & Interactivity
 */

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
    const studentName = prompt("Enter Student Full Name:", "Student");
    if (!studentName) return;

    const studentRoll = prompt("Enter University Roll No / Student ID:", "GEU/2026/BCADS/" + Math.floor(100 + Math.random() * 900));
    if (!studentRoll) return;

    try {
        const response = await fetch("/api/marketplace/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                listing_id: listingId,
                student_name: studentName,
                student_id_roll: studentRoll,
                quantity: 1
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert(`🎉 Success! Surprise Box Reserved.\n\nRedemption Token: ${data.token}\nTotal Price: ₹${data.total_price}\nPickup Until: ${data.pickup_until}\n\nPlease show this token at the canteen collection counter.`);
            window.location.reload();
        } else {
            alert("Error: " + (data.error || "Could not complete reservation"));
        }
    } catch (err) {
        alert("Failed to communicate with server: " + err.message);
    }
}

// NGO Claim Dispatch
async function claimNgoDonation(donationId, itemName) {
    const volunteerName = prompt(`Assign volunteer name for picking up ${itemName}:`, "Volunteer Officer");
    if (!volunteerName) return;

    try {
        const response = await fetch("/api/ngo/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                donation_id: donationId,
                ngo_id: 1,
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
async function verifyNgoPickup(donationId, expectedPinHint) {
    const enteredPin = prompt(`Enter Canteen Verification PIN (Staff Hint: ${expectedPinHint}):`);
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

// Simulation Clock Warp
async function setSimulationClock(timeStr, examDay = 1, weather = "mild") {
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
                is_exam_day: examDay,
                temperature_c: temp,
                rainfall_mm: rain
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
