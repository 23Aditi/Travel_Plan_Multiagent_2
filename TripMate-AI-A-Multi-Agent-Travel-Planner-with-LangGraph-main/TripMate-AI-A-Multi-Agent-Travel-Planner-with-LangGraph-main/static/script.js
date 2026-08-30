let currentThreadId = localStorage.getItem("travel_thread_id") || null;
let latestDossierMarkdown = "";
let latestData = null;

const AGENT_KEYS = [
    "intent_agent",
    "flight_agent",
    "hotel_agent",
    "itinerary_agent",
    "budget_agent",
    "final_agent"
];

// Theme Toggle Logic
window.initTheme = function() {
    const savedTheme = localStorage.getItem("tripmate_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
};

window.toggleTheme = function() {
    const currentTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("tripmate_theme", newTheme);
    updateThemeIcon(newTheme);
};

function updateThemeIcon(theme) {
    const iconSpan = document.getElementById("themeIcon");
    if (iconSpan) {
        iconSpan.innerHTML = theme === "dark"
            ? `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
            : `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
    }
}

// Run theme initialization immediately
initTheme();

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    loadUserTrips();
});

// Guided Questionnaire State
let guidedState = {
    duration: "7 days",
    travelers: "Solo traveler",
    budgetTier: "Moderate (₹40,000 - ₹1.2 Lakh)",
    interests: new Set(["Food & Culinary", "History & Culture"])
};

function setPlannerMode(mode) {
    const guidedMode = document.getElementById("guidedMode");
    const freeformMode = document.getElementById("freeformMode");
    const btnGuided = document.getElementById("btnModeGuided");
    const btnFreeform = document.getElementById("btnModeFreeform");

    if (mode === "guided") {
        guidedMode.classList.remove("hidden");
        freeformMode.classList.add("hidden");
        btnGuided.classList.add("active");
        btnFreeform.classList.remove("active");
        const destInput = document.getElementById("guideDestination");
        if (destInput) destInput.focus();
    } else {
        guidedMode.classList.add("hidden");
        freeformMode.classList.remove("hidden");
        btnGuided.classList.remove("active");
        btnFreeform.classList.add("active");
        const userInput = document.getElementById("userInput");
        if (userInput) userInput.focus();
    }
}

function selectSinglePill(containerId, element, value) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll(".pill-btn").forEach(btn => btn.classList.remove("active"));
    element.classList.add("active");

    if (containerId === "durationPills") guidedState.duration = value;
    if (containerId === "travelerPills") guidedState.travelers = value;
}

function selectBudgetPill(element, value) {
    const container = document.getElementById("budgetPills");
    if (container) {
        container.querySelectorAll(".pill-btn").forEach(btn => btn.classList.remove("active"));
    }
    element.classList.add("active");
    guidedState.budgetTier = value;
}

function toggleMultiPill(element, value) {
    if (guidedState.interests.has(value)) {
        guidedState.interests.delete(value);
        element.classList.remove("active");
    } else {
        guidedState.interests.add(value);
        element.classList.add("active");
    }
}

function submitGuidedForm() {
    hideError();
    const destInput = document.getElementById("guideDestination");
    const dest = destInput.value.trim();
    if (!dest) {
        showError("Please specify a destination (e.g. Tokyo, Paris, Bali) to begin planning!");
        destInput.focus();
        return;
    }

    const origin = document.getElementById("guideOrigin").value.trim() || "DEL";
    const customBudget = document.getElementById("guideCustomBudget").value.trim();
    const budget = customBudget ? customBudget : guidedState.budgetTier;
    const notes = document.getElementById("guideNotes").value.trim();
    const interests = Array.from(guidedState.interests).join(", ") || "General Sightseeing";

    let prompt = `Plan a complete ${guidedState.duration} trip to ${dest} from ${origin} for ${guidedState.travelers} with a ${budget} budget. Key focus: ${interests}.`;
    if (notes) {
        prompt += ` Special preferences: ${notes}.`;
    }

    document.getElementById("userInput").value = prompt;
    sendMessage();
}

function setPrompt(text) {
    setPlannerMode('freeform');
    const input = document.getElementById("userInput");
    input.value = text;
    input.focus();
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById("sendBtn");
    const btnText = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");

    if (sendBtn) sendBtn.disabled = isLoading;
    if (btnText) btnText.classList.toggle("hidden", isLoading);
    if (btnLoader) btnLoader.classList.toggle("hidden", !isLoading);

    const guideBtn = document.getElementById("guideSubmitBtn");
    const guideBtnText = document.getElementById("guideBtnText");
    const guideBtnLoader = document.getElementById("guideBtnLoader");

    if (guideBtn) guideBtn.disabled = isLoading;
    if (guideBtnText) guideBtnText.classList.toggle("hidden", isLoading);
    if (guideBtnLoader) guideBtnLoader.classList.toggle("hidden", !isLoading);
}

function showError(message) {
    const errorBox = document.getElementById("errorBox");
    const errorMessage = document.getElementById("errorMessage");
    errorMessage.textContent = message;
    errorBox.classList.remove("hidden");
    errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideError() {
    const errorBox = document.getElementById("errorBox");
    errorBox.classList.add("hidden");
}

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
    document.getElementById("userInput").focus();
}

function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));

    // Find clicked tab button
    const targetBtn = Array.from(document.querySelectorAll(".tab-btn")).find(btn => 
        btn.getAttribute("onclick").includes(`'${tabId}'`)
    );
    if (targetBtn) targetBtn.classList.add("active");

    const targetPanel = document.getElementById(`tab_${tabId}`);
    if (targetPanel) targetPanel.classList.add("active");
}

function resetTracker() {
    const trackerSection = document.getElementById("trackerSection");
    trackerSection.classList.remove("hidden");

    AGENT_KEYS.forEach(key => {
        const card = document.getElementById(`card_${key}`);
        const badge = document.getElementById(`badge_${key}`);
        const desc = document.getElementById(`desc_${key}`);
        if (!card) return;

        card.className = "agent-card";
        if (badge) badge.textContent = "Queued";
        if (desc) {
            if (key === "intent_agent") desc.textContent = "Parsing trip specifications...";
            if (key === "flight_agent") desc.textContent = "Searching aviation databases...";
            if (key === "hotel_agent") desc.textContent = "Discovering top hotels...";
            if (key === "itinerary_agent") desc.textContent = "Building daily plan...";
            if (key === "budget_agent") desc.textContent = "Estimating itemized expenses...";
            if (key === "final_agent") desc.textContent = "Compiling executive dossier...";
        }
    });

    document.getElementById("trackerStatus").textContent = "Initializing LangGraph workflow...";
}

function updateAgentState(agentKey, state, customDesc = null) {
    const card = document.getElementById(`card_${agentKey}`);
    const badge = document.getElementById(`badge_${agentKey}`);
    const desc = document.getElementById(`desc_${agentKey}`);
    if (!card) return;

    card.className = `agent-card ${state}`;

    if (state === "running") {
        if (badge) badge.textContent = "Active...";
        if (customDesc && desc) desc.textContent = customDesc;
    } else if (state === "completed") {
        if (badge) badge.textContent = "Done ✓";
        if (customDesc && desc) desc.textContent = customDesc;
    } else if (state === "error") {
        if (badge) badge.textContent = "Failed";
    }
}

function renderMarkdownSafely(text) {
    if (!text) return "<p class='empty-note'>No data available for this section.</p>";
    if (typeof marked !== "undefined") {
        return marked.parse(text);
    }
    return `<pre>${text}</pre>`;
}

function populateResults(data) {
    latestData = data;
    latestDossierMarkdown = data.answer || "";

    const intent = data.intent || {};
    const destination = intent.destination || "Trip Destination";
    const duration = intent.duration_days ? `${intent.duration_days} Days` : "Flexible";
    const travelers = intent.travelers ? `${intent.travelers} Traveler${intent.travelers > 1 ? 's' : ''}` : "1 Traveler";
    const budget = intent.budget || "Moderate";
    const llmCalls = data.llm_calls ? `${data.llm_calls} Agent Calls` : "Completed";

    // Update Hero Snapshot
    document.getElementById("heroDestination").textContent = destination;
    document.getElementById("heroDuration").textContent = duration;
    document.getElementById("heroTravelers").textContent = travelers;
    document.getElementById("heroBudget").textContent = budget;
    document.getElementById("heroLlmCalls").textContent = llmCalls;

    const latencyVal = data.execution_time_seconds ? `${data.execution_time_seconds}s` : "Fast";
    const cacheVal = (data.cache_stats && data.cache_stats.hits > 0) ? `${data.cache_stats.hits} Hits` : "Active";
    const latencyEl = document.getElementById("heroLatency");
    const cacheEl = document.getElementById("heroCache");
    if (latencyEl) latencyEl.textContent = latencyVal;
    if (cacheEl) cacheEl.textContent = cacheVal;

    // Helper to extract markdown sections
    function extractSection(fullText, titleKeywords) {
        if (!fullText) return null;
        const regex = new RegExp(`##?\\s*(?:\\d+\\.)?\\s*.*?(?:${titleKeywords}).*?\\n([\\s\\S]*?)(?=\\n##?\\s|$)`, "i");
        const match = fullText.match(regex);
        return match ? match[1].trim() : null;
    }

    const overviewText = extractSection(latestDossierMarkdown, "Executive Trip Summary|Trip Summary|Overview") || latestDossierMarkdown;
    const itineraryText = data.itinerary || extractSection(latestDossierMarkdown, "Day-by-Day|Itinerary") || latestDossierMarkdown;
    const budgetText = data.budget_breakdown || extractSection(latestDossierMarkdown, "Financial Breakdown|Budget") || latestDossierMarkdown;
    const flightText = data.flight_results || extractSection(latestDossierMarkdown, "Flight Options|Flight") || "Flight details are included in the full dossier.";
    const hotelText = data.hotel_results || extractSection(latestDossierMarkdown, "Recommended Stays|Hotel") || "Accommodation details are included in the full dossier.";

    document.getElementById("overviewBox").innerHTML = renderMarkdownSafely(overviewText);
    document.getElementById("itineraryBox").innerHTML = renderMarkdownSafely(itineraryText);
    document.getElementById("budgetBox").innerHTML = renderMarkdownSafely(budgetText);
    document.getElementById("flightBox").innerHTML = renderMarkdownSafely(flightText);
    document.getElementById("hotelBox").innerHTML = renderMarkdownSafely(hotelText);
    document.getElementById("dossierBox").innerHTML = renderMarkdownSafely(latestDossierMarkdown);

    // Thread tag
    document.getElementById("threadInfo").textContent = `Session ID: ${data.thread_id || currentThreadId || 'active'}`;

    // Reveal result section
    const resultSection = document.getElementById("resultSection");
    resultSection.classList.remove("hidden");
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

    // Auto-save generated trip to user profile
    autoSaveCurrentTrip(data);
}

async function sendMessage() {
    hideError();

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please provide a destination or travel details first.");
        return;
    }

    setLoading(true);
    resetTracker();

    // Set initial agent to active
    updateAgentState("intent_agent", "running", "Analyzing travel destination & budget...");

    try {
        // Attempt SSE Streaming endpoint first
        const response = await fetch("/api/travel/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message, thread_id: currentThreadId })
        });

        if (!response.ok) {
            throw new Error(`Server returned HTTP ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let finalDataReceived = null;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop(); // keep last incomplete chunk in buffer

            for (const chunk of lines) {
                if (!chunk.startsWith("data: ")) continue;
                const jsonStr = chunk.replace(/^data:\s*/, "").trim();
                if (!jsonStr) continue;

                try {
                    const payload = JSON.parse(jsonStr);

                    if (payload.event === "agent_complete") {
                        const agent = payload.agent;
                        updateAgentState(agent, "completed");

                        // Update tracker status text
                        if (agent === "intent_agent") {
                            document.getElementById("trackerStatus").textContent = "Running Flight & Hotel agents in parallel...";
                            updateAgentState("flight_agent", "running", "Connecting to live flight data...");
                            updateAgentState("hotel_agent", "running", "Searching top accommodations...");
                        } else if (agent === "flight_agent" || agent === "hotel_agent") {
                            const flightCard = document.getElementById("card_flight_agent");
                            const hotelCard = document.getElementById("card_hotel_agent");
                            const bothDone = flightCard.classList.contains("completed") && hotelCard.classList.contains("completed");
                            if (bothDone) {
                                document.getElementById("trackerStatus").textContent = "Synthesizing customized day-by-day itinerary...";
                                updateAgentState("itinerary_agent", "running");
                            }
                        } else if (agent === "itinerary_agent") {
                            document.getElementById("trackerStatus").textContent = "Auditing itemized budget & expenses...";
                            updateAgentState("budget_agent", "running");
                        } else if (agent === "budget_agent") {
                            document.getElementById("trackerStatus").textContent = "Drafting final executive travel dossier...";
                            updateAgentState("final_agent", "running");
                        }
                    } else if (payload.event === "done") {
                        updateAgentState("final_agent", "completed");
                        document.getElementById("trackerStatus").textContent = "✓ Complete travel plan generated successfully!";
                        finalDataReceived = payload;
                    } else if (payload.event === "error") {
                        throw new Error(payload.message || "Pipeline error");
                    }
                } catch (parseErr) {
                    console.warn("Could not parse stream event:", jsonStr, parseErr);
                }
            }
        }

        if (finalDataReceived) {
            currentThreadId = finalDataReceived.thread_id;
            localStorage.setItem("travel_thread_id", currentThreadId);
            populateResults(finalDataReceived);
        } else {
            // Fallback to standard synchronous endpoint if stream didn't yield done event
            await fallbackSyncFetch(message);
        }

    } catch (streamError) {
        console.warn("Streaming fetch failed, falling back to standard endpoint:", streamError);
        try {
            await fallbackSyncFetch(message);
        } catch (syncError) {
            showError(syncError.message || "Failed to generate travel plan.");
        }
    } finally {
        setLoading(false);
    }
}

async function fallbackSyncFetch(message) {
    const response = await fetch("/api/travel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, thread_id: currentThreadId })
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to generate travel plan.");
    }

    AGENT_KEYS.forEach(k => updateAgentState(k, "completed"));
    document.getElementById("trackerStatus").textContent = "✓ Plan generated successfully!";

    currentThreadId = data.thread_id;
    localStorage.setItem("travel_thread_id", currentThreadId);
    populateResults(data);
}

function copyResult() {
    if (!latestDossierMarkdown) {
        showError("No travel plan available to copy.");
        return;
    }

    navigator.clipboard.writeText(latestDossierMarkdown)
        .then(() => {
            const btnText = document.getElementById("copyBtnText");
            const old = btnText.textContent;
            btnText.textContent = "Copied!";
            setTimeout(() => { btnText.textContent = old; }, 1800);
        })
        .catch(() => {
            showError("Unable to copy to clipboard.");
        });
}

function downloadPDF() {
    const element = document.getElementById("pdfContent");
    if (!latestDossierMarkdown || !element) {
        showError("No travel plan available to download.");
        return;
    }

    const opt = {
        margin: 0.5,
        filename: 'TripMate-AI-Travel-Plan.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: '#0f172a' },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();
}

function setRefinePrompt(text) {
    const input = document.getElementById("refineInput");
    if (input) {
        input.value = text;
        input.focus();
    }
}

async function sendRefinement() {
    const input = document.getElementById("refineInput");
    const refineText = input.value.trim();
    if (!refineText) {
        showError("Please enter your adjustment or refinement request.");
        return;
    }

    const refineBtn = document.getElementById("refineBtn");
    const refineBtnText = document.getElementById("refineBtnText");
    const refineBtnLoader = document.getElementById("refineBtnLoader");

    if (refineBtn) refineBtn.disabled = true;
    if (refineBtnText) refineBtnText.classList.add("hidden");
    if (refineBtnLoader) refineBtnLoader.classList.remove("hidden");

    document.getElementById("userInput").value = refineText;
    input.value = "";

    try {
        await sendMessage();
    } finally {
        if (refineBtn) refineBtn.disabled = false;
        if (refineBtnText) refineBtnText.classList.remove("hidden");
        if (refineBtnLoader) refineBtnLoader.classList.add("hidden");
    }
}

document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closePastTripsModal();
    }
    if (event.ctrlKey && event.key === "Enter") {
        sendMessage();
    }
});

// --- Past Trips Management ---

async function autoSaveCurrentTrip(data) {
    if (!data) return;
    try {
        const intent = data.intent || {};
        const destination = intent.destination || (document.getElementById("heroDestination") ? document.getElementById("heroDestination").textContent : "Trip Destination");
        const duration = intent.duration_days ? `${intent.duration_days} Days` : (document.getElementById("heroDuration") ? document.getElementById("heroDuration").textContent : "Flexible");
        const budget = intent.budget || (document.getElementById("heroBudget") ? document.getElementById("heroBudget").textContent : "Moderate");
        const travelers = intent.travelers ? `${intent.travelers} Traveler${intent.travelers > 1 ? 's' : ''}` : (document.getElementById("heroTravelers") ? document.getElementById("heroTravelers").textContent : "1 Traveler");
        const thread_id = data.thread_id || currentThreadId;
        const prompt = document.getElementById("userInput") ? document.getElementById("userInput").value : "";

        const res = await fetch("/api/trips/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                destination: destination,
                duration: duration,
                budget: budget,
                travelers: travelers,
                prompt: prompt,
                thread_id: thread_id,
                plan_data: data
            })
        });

        if (res.ok) {
            loadUserTrips();
        }
    } catch (err) {
        console.warn("Could not auto-save trip to profile:", err);
    }
}

window.openPastTripsModal = function() {
    const overlay = document.getElementById("tripsDrawerOverlay");
    if (overlay) {
        overlay.classList.remove("hidden");
        loadUserTrips();
    }
};

window.closePastTripsModal = function() {
    const overlay = document.getElementById("tripsDrawerOverlay");
    if (overlay) {
        overlay.classList.add("hidden");
    }
};

async function loadUserTrips() {
    const badge = document.getElementById("tripCountBadge");
    const container = document.getElementById("pastTripsList");

    try {
        const res = await fetch("/api/trips");
        if (!res.ok) {
            if (badge) badge.textContent = "0";
            return;
        }

        const data = await res.json();
        const trips = data.trips || [];

        if (badge) badge.textContent = trips.length;

        if (!container) return;

        if (trips.length === 0) {
            container.innerHTML = `
                <div class="drawer-empty">
                    <div class="drawer-empty-icon">🗺️</div>
                    <strong>No saved journeys yet</strong>
                    <p>When you generate a travel itinerary, it will automatically be saved here.</p>
                </div>
            `;
            return;
        }

        let html = "";
        trips.forEach(t => {
            html += `
                <div class="saved-trip-card" id="saved_trip_${t.id}">
                    <div class="saved-trip-top">
                        <div class="saved-trip-dest">${escapeHtml(t.destination)}</div>
                        <div class="saved-trip-date">${escapeHtml(t.created_at)}</div>
                    </div>
                    <div class="saved-trip-chips">
                        <span class="saved-chip">${escapeHtml(t.duration)}</span>
                        <span class="saved-chip">${escapeHtml(t.budget)}</span>
                        <span class="saved-chip">${escapeHtml(t.travelers)}</span>
                    </div>
                    <div class="saved-trip-actions">
                        <button type="button" class="view-trip-btn" onclick="viewSavedTrip(${t.id})">
                            <span>View Plan</span>
                            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="9 18 15 12 9 6"></polyline>
                            </svg>
                        </button>
                        <button type="button" class="delete-trip-btn" onclick="deleteSavedTrip(${t.id})" title="Delete saved trip">
                            Delete
                        </button>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;

    } catch (err) {
        console.warn("Error loading saved trips:", err);
        if (container) {
            container.innerHTML = `<div class="drawer-loading">Unable to load past trips.</div>`;
        }
    }
}

async function viewSavedTrip(tripId) {
    try {
        const res = await fetch(`/api/trips/${tripId}`);
        if (!res.ok) {
            showError("Could not retrieve saved trip.");
            return;
        }

        const data = await res.json();
        if (data.success && data.trip && data.trip.plan_data) {
            currentThreadId = data.trip.thread_id;
            localStorage.setItem("travel_thread_id", currentThreadId);
            populateResults(data.trip.plan_data);
            closePastTripsModal();
        } else {
            showError("Trip data is invalid or empty.");
        }
    } catch (err) {
        showError("Failed to load saved trip: " + err.message);
    }
}

async function deleteSavedTrip(tripId) {
    if (!confirm("Are you sure you want to remove this saved journey?")) {
        return;
    }

    try {
        const res = await fetch(`/api/trips/${tripId}`, { method: "DELETE" });
        if (res.ok) {
            const card = document.getElementById(`saved_trip_${tripId}`);
            if (card) {
                card.remove();
            }
            loadUserTrips();
        } else {
            showError("Failed to delete trip.");
        }
    } catch (err) {
        showError("Error deleting trip: " + err.message);
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}