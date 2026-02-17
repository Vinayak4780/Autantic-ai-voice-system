/**
 * VoiceStyle — Frontend Application
 * 
 * Communicates with the FastAPI backend (port 8000) to:
 * 1. Onboard users by submitting writing samples
 * 2. Rewrite text using saved style profiles
 * 3. Manage style profiles
 */

const API_BASE = "http://localhost:8000";

// ── State ────────────────────────────────────────────────────────────────

let sampleCount = 0;
const MIN_SAMPLES = 3;
const MAX_SAMPLES = 10;
const MIN_SAMPLE_LENGTH = 50;

// ── DOM Elements ─────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ── Navigation ───────────────────────────────────────────────────────────

$$(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        $$(".nav-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        $$(".tab-content").forEach((tab) => tab.classList.remove("active"));
        $(`#tab-${btn.dataset.tab}`).classList.add("active");

        // Refresh profiles when switching to profiles/rewrite tab
        if (btn.dataset.tab === "profiles") loadProfiles();
        if (btn.dataset.tab === "rewrite") loadProfileSelect();
    });
});

// ── Sample Management ────────────────────────────────────────────────────

function addSampleInput(prefill = "") {
    if (sampleCount >= MAX_SAMPLES) return;
    sampleCount++;

    const container = $("#samples-container");
    const div = document.createElement("div");
    div.className = "sample-group";
    div.dataset.index = sampleCount;
    div.innerHTML = `
        <div class="sample-header">
            <label>Sample ${sampleCount}</label>
            <button class="remove-btn" title="Remove sample">&times;</button>
        </div>
        <textarea rows="4" 
            placeholder="Paste a writing sample here (min ${MIN_SAMPLE_LENGTH} characters)..."
            class="sample-textarea">${escapeHtml(prefill)}</textarea>
    `;

    div.querySelector(".remove-btn").addEventListener("click", () => {
        div.remove();
        sampleCount--;
        renumberSamples();
        updateSampleCount();
        updateAnalyzeButton();
    });

    div.querySelector("textarea").addEventListener("input", () => {
        updateAnalyzeButton();
    });

    container.appendChild(div);
    updateSampleCount();
    updateAnalyzeButton();
}

function renumberSamples() {
    const groups = $$("#samples-container .sample-group");
    groups.forEach((g, i) => {
        g.dataset.index = i + 1;
        g.querySelector("label").textContent = `Sample ${i + 1}`;
    });
    sampleCount = groups.length;
}

function updateSampleCount() {
    let counter = $(".sample-count");
    if (!counter) {
        counter = document.createElement("p");
        counter.className = "sample-count";
        const container = $("#samples-container");
        container.parentNode.insertBefore(counter, container);
    }
    counter.innerHTML = `<span class="count">${sampleCount}</span> / ${MAX_SAMPLES} samples (min ${MIN_SAMPLES})`;
}

function updateAnalyzeButton() {
    const btn = $("#analyze-btn");
    const name = $("#user-name").value.trim();
    const textareas = $$("#samples-container textarea");
    const validSamples = [...textareas].filter(
        (t) => t.value.trim().length >= MIN_SAMPLE_LENGTH
    );
    btn.disabled = !name || validSamples.length < MIN_SAMPLES;
}

// Initialize with 5 empty sample inputs
for (let i = 0; i < 5; i++) addSampleInput();

// User name input listener
$("#user-name").addEventListener("input", updateAnalyzeButton);

// Add sample button
$("#add-sample-btn").addEventListener("click", () => addSampleInput());

// ── Onboarding / Analysis ────────────────────────────────────────────────

$("#analyze-btn").addEventListener("click", async () => {
    const userName = $("#user-name").value.trim();
    const textareas = $$("#samples-container textarea");
    const samples = [...textareas]
        .map((t) => t.value.trim())
        .filter((t) => t.length >= MIN_SAMPLE_LENGTH);

    if (samples.length < MIN_SAMPLES) {
        alert(`Please provide at least ${MIN_SAMPLES} writing samples.`);
        return;
    }

    showLoading("Analyzing your writing style...");

    try {
        const response = await fetch(`${API_BASE}/api/onboard`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_name: userName,
                samples: samples.map((text) => ({ text })),
            }),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to analyze");
        }

        const profile = await response.json();
        displayAnalysisResults(profile);
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        hideLoading();
    }
});

function displayAnalysisResults(profile) {
    const resultsDiv = $("#analysis-results");
    resultsDiv.classList.remove("hidden");

    // Style summary
    $("#style-summary").textContent = profile.raw_style_summary;

    // Metrics grid
    const m = profile.metrics;
    const metricsHtml = `
        <div class="metric-card">
            <div class="metric-label">Avg Sentence Length</div>
            <div class="metric-value">${m.avg_sentence_length} words</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Question Ratio</div>
            <div class="metric-value">${(m.question_ratio * 100).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Exclamation Ratio</div>
            <div class="metric-value">${(m.exclamation_ratio * 100).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Vocabulary Richness</div>
            <div class="metric-value">${(m.vocabulary_richness * 100).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Contraction Usage</div>
            <div class="metric-value">${(m.contraction_ratio * 100).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Short Sentences</div>
            <div class="metric-value">${(m.short_sentence_ratio * 100).toFixed(1)}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Emoji Frequency</div>
            <div class="metric-value">${m.emoji_frequency.toFixed(2)}/100w</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Length Variation</div>
            <div class="metric-value small">${m.sentence_length_variation}</div>
        </div>
    `;
    $("#style-metrics").innerHTML = metricsHtml;

    // Style details
    let detailsHtml = "";

    if (profile.signature_phrases.length) {
        detailsHtml += `
            <div class="detail-section">
                <h4>Signature Phrases</h4>
                <div class="tag-list">
                    ${profile.signature_phrases.map((p) => `<span class="tag">${escapeHtml(p)}</span>`).join("")}
                </div>
            </div>`;
    }

    if (profile.vocabulary_preferences.length) {
        detailsHtml += `
            <div class="detail-section">
                <h4>Vocabulary Preferences</h4>
                <div class="tag-list">
                    ${profile.vocabulary_preferences.map((p) => `<span class="tag">${escapeHtml(p)}</span>`).join("")}
                </div>
            </div>`;
    }

    if (profile.sentence_starters.length) {
        detailsHtml += `
            <div class="detail-section">
                <h4>Common Sentence Starters</h4>
                <div class="tag-list">
                    ${profile.sentence_starters.map((p) => `<span class="tag">${escapeHtml(p)}</span>`).join("")}
                </div>
            </div>`;
    }

    if (profile.transition_words.length) {
        detailsHtml += `
            <div class="detail-section">
                <h4>Transition Words</h4>
                <div class="tag-list">
                    ${profile.transition_words.map((p) => `<span class="tag">${escapeHtml(p)}</span>`).join("")}
                </div>
            </div>`;
    }

    $("#style-details").innerHTML = detailsHtml;

    // Scroll to results
    resultsDiv.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Rewrite ──────────────────────────────────────────────────────────────

async function loadProfileSelect() {
    try {
        const response = await fetch(`${API_BASE}/api/profiles`);
        const profiles = await response.json();

        const select = $("#profile-select");
        const currentValue = select.value;
        select.innerHTML = '<option value="">— Select a profile —</option>';

        profiles.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = `${p.user_name} (${p.sample_count} samples)`;
            select.appendChild(opt);
        });

        if (currentValue) select.value = currentValue;
        updateRewriteButton();
    } catch (err) {
        console.error("Failed to load profiles:", err);
    }
}

function updateRewriteButton() {
    const btn = $("#rewrite-btn");
    const profileId = $("#profile-select").value;
    const draftText = $("#draft-input").value.trim();
    btn.disabled = !profileId || draftText.length < 20;
}

$("#profile-select").addEventListener("change", updateRewriteButton);
$("#draft-input").addEventListener("input", updateRewriteButton);

$("#rewrite-btn").addEventListener("click", async () => {
    const profileId = $("#profile-select").value;
    const draftText = $("#draft-input").value.trim();

    if (!profileId || draftText.length < 20) return;

    showLoading("Rewriting in your voice...");

    try {
        const response = await fetch(`${API_BASE}/api/rewrite`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                profile_id: profileId,
                draft_text: draftText,
            }),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to rewrite");
        }

        const result = await response.json();
        displayRewriteResults(result);
    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        hideLoading();
    }
});

function displayRewriteResults(result) {
    const resultsDiv = $("#rewrite-results");
    resultsDiv.classList.remove("hidden");

    $("#original-text").textContent = result.original_text;
    $("#rewritten-text").textContent = result.rewritten_text;

    // Style notes
    const notesDiv = $("#style-notes");
    if (result.style_notes && result.style_notes.length) {
        notesDiv.innerHTML = `
            <h4>Style Adjustments Made</h4>
            <ul>${result.style_notes.map((n) => `<li>${escapeHtml(n)}</li>`).join("")}</ul>
        `;
    }

    resultsDiv.scrollIntoView({ behavior: "smooth", block: "start" });
}

// Copy button
$("#copy-btn").addEventListener("click", () => {
    const text = $("#rewritten-text").textContent;
    navigator.clipboard.writeText(text).then(() => {
        const btn = $("#copy-btn");
        btn.textContent = "✓ Copied!";
        setTimeout(() => (btn.textContent = "Copy Rewritten Text"), 2000);
    });
});

// ── Profiles ─────────────────────────────────────────────────────────────

async function loadProfiles() {
    try {
        const response = await fetch(`${API_BASE}/api/profiles`);
        const profiles = await response.json();

        const list = $("#profiles-list");

        if (profiles.length === 0) {
            list.innerHTML = '<p class="empty-state">No profiles yet. Create one in the Onboard tab.</p>';
            return;
        }

        list.innerHTML = profiles
            .map(
                (p) => `
            <div class="profile-item" data-id="${p.id}">
                <div class="profile-info">
                    <h3>${escapeHtml(p.user_name)}</h3>
                    <p>${p.sample_count} samples · Created ${formatDate(p.created_at)}</p>
                </div>
                <div class="profile-actions">
                    <button class="btn btn-secondary view-profile-btn" data-id="${p.id}">View</button>
                    <button class="btn btn-danger delete-profile-btn" data-id="${p.id}">Delete</button>
                </div>
            </div>
        `
            )
            .join("");

        // Attach event listeners
        list.querySelectorAll(".view-profile-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                viewProfile(btn.dataset.id);
            });
        });

        list.querySelectorAll(".delete-profile-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteProfile(btn.dataset.id);
            });
        });
    } catch (err) {
        console.error("Failed to load profiles:", err);
        $("#profiles-list").innerHTML =
            '<p class="empty-state">Could not connect to the API. Is the backend running on port 8000?</p>';
    }
}

async function viewProfile(profileId) {
    try {
        const response = await fetch(`${API_BASE}/api/profiles/${profileId}`);
        const profile = await response.json();

        const detailDiv = $("#profile-detail");
        detailDiv.classList.remove("hidden");
        $("#detail-name").textContent = profile.user_name;

        const m = profile.metrics;
        let html = `
            <div class="style-summary">${escapeHtml(profile.raw_style_summary)}</div>
            <div class="style-details">
        `;

        if (profile.signature_phrases.length) {
            html += `<div class="detail-section"><h4>Signature Phrases</h4>
                <div class="tag-list">${profile.signature_phrases.map((p) => `<span class="tag">${escapeHtml(p)}</span>`).join("")}</div></div>`;
        }
        if (profile.vocabulary_preferences.length) {
            html += `<div class="detail-section"><h4>Vocabulary</h4>
                <div class="tag-list">${profile.vocabulary_preferences.map((p) => `<span class="tag">${escapeHtml(p)}</span>`).join("")}</div></div>`;
        }
        if (profile.sample_excerpts.length) {
            html += `<div class="detail-section"><h4>Sample Excerpts</h4>
                ${profile.sample_excerpts.map((e) => `<p style="font-size:13px;color:var(--text-dim);margin-bottom:8px;font-style:italic">"${escapeHtml(e)}"</p>`).join("")}</div>`;
        }

        html += "</div>";
        $("#detail-content").innerHTML = html;

        detailDiv.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
        alert("Failed to load profile details.");
    }
}

async function deleteProfile(profileId) {
    if (!confirm("Delete this profile? This cannot be undone.")) return;

    try {
        await fetch(`${API_BASE}/api/profiles/${profileId}`, { method: "DELETE" });
        loadProfiles();
    } catch (err) {
        alert("Failed to delete profile.");
    }
}

// ── Helpers ──────────────────────────────────────────────────────────────

function showLoading(text) {
    $("#loading-text").textContent = text;
    $("#loading").classList.remove("hidden");
}

function hideLoading() {
    $("#loading").classList.add("hidden");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function formatDate(isoString) {
    try {
        const d = new Date(isoString);
        return d.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    } catch {
        return isoString;
    }
}

// ── Init ─────────────────────────────────────────────────────────────────

// Load profiles for the rewrite tab on startup
loadProfileSelect();
