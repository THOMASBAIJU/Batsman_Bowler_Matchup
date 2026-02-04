document.addEventListener('DOMContentLoaded', function () {
    const batsmanSelect = document.getElementById('batsman');
    const bowlerSelect = document.getElementById('bowler');
    const venueSelect = document.getElementById('venue');
    const ballsFacedInput = document.getElementById('ballsFaced');
    const predictBtn = document.getElementById('predictBtn');
    const predictForm = document.getElementById('predict-form');
    const predictionContainer = document.getElementById('prediction-container');
    const alertContainer = document.getElementById('alert-container');
    const liveModeSwitch = document.getElementById('liveModeSwitch');

    // ✅ NECESSARY CHANGE: Store the button's original HTML content
    const originalBtnHTML = predictBtn.innerHTML;

    const gaugeCharts = { runs: null, strikeRate: null, dismissalRate: null };

    function updateVerdict(data) {
        const container = document.getElementById('verdict-container');
        const risk = data.dismissal_rate * 100;
        const sr = data.strike_rate;

        let verdict = { text: "BALANCED CONTEST", color: "secondary", icon: "bi-scale", desc: "Evenly matched contest." };

        if (risk > 40) {
            verdict = { text: "BOWLER DOMINATES", color: "danger", icon: "bi-exclamation-triangle-fill", desc: "High probability of wicket." };
        } else if (sr > 150 && risk < 25) {
            verdict = { text: "BATSMAN DOMINATES", color: "success", icon: "bi-fire", desc: "High scoring, low risk." };
        } else if (sr > 150 && risk >= 25) {
            verdict = { text: "HIGH VOLATILITY", color: "warning", icon: "bi-activity", desc: "High reward, but high risk." };
        } else if (sr < 110 && risk < 20) {
            verdict = { text: "BATTLE OF ATTRITION", color: "info", icon: "bi-shield-lock-fill", desc: "Defensive play expected." };
        }

        container.innerHTML = `
            <div class="d-inline-block px-4 py-2 border border-${verdict.color} rounded-pill bg-dark bg-opacity-75" 
                 style="box-shadow: 0 0 20px var(--bs-${verdict.color}); backdrop-filter: blur(10px);">
                <div class="d-flex align-items-center gap-3">
                    <i class="bi ${verdict.icon} fs-3 text-${verdict.color}"></i>
                    <div class="text-start">
                        <div class="fw-bold text-${verdict.color} h5 mb-0" style="letter-spacing: 2px;">${verdict.text}</div>
                        <small class="text-light opacity-75">${verdict.desc}</small>
                    </div>
                </div>
            </div>
        `;
        container.style.opacity = '1';
    }

    function createOrUpdateGauge(canvasId, value, max, color) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const key = canvasId.split('-')[0];

        const data = {
            datasets: [{
                data: [value, Math.max(0, max - value)],
                backgroundColor: [color, '#e9ecef'],
                circumference: 180, rotation: 270, cutout: '75%',
                borderWidth: 0, borderRadius: 5
            }]
        };
        const options = {
            responsive: true, maintainAspectRatio: false,
            plugins: { tooltip: { enabled: false } },
            animation: { duration: 1200, easing: 'easeOutCubic' }
        };

        if (gaugeCharts[key]) {
            gaugeCharts[key].data.datasets[0].data = data.datasets[0].data;
            gaugeCharts[key].update();
        } else {
            gaugeCharts[key] = new Chart(ctx, { type: 'doughnut', data, options });
        }
    }

    function populateSelect(selectElement, items, placeholder) {
        selectElement.innerHTML = `<option value="" selected disabled>${placeholder}</option>`;
        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item;
            option.textContent = item;
            selectElement.appendChild(option);
        });
        selectElement.disabled = items.length === 0;
    }

    function checkFormValidity() {
        predictBtn.disabled = !(batsmanSelect.value && bowlerSelect.value && venueSelect.value && ballsFacedInput.value > 0);
    }

    async function displayPlayerCard(playerName, containerId, expectedRole) {
        const container = document.getElementById(containerId);
        container.innerHTML = ''; // Clear previous card content
        try {
            const response = await fetch(`/get_player_card/${playerName}`);
            if (!response.ok) throw new Error('Player data not found');
            const data = await response.json();

            let detailsHtml = '';
            if (expectedRole === 'Batsman' && data.batting_hand && data.batting_hand !== 'N/A') {
                detailsHtml = `<p class="player-detail mb-0">${data.batting_hand}</p>`;
            } else if (expectedRole === 'Bowler' && data.bowling_style && data.bowling_style !== 'N/A') {
                detailsHtml = `<p class="player-detail mb-0">${data.bowling_style}</p>`;
            }

            container.innerHTML = `
                <div class="player-card">
                    <img src="${data.profile_image_url}" alt="${data.player_name}" 
                         onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${data.player_name.replace(' ', '+')}&background=0d6efd&color=fff&size=280';">
                    <div class="player-info">
                        <h5>${data.player_name}</h5>
                        <p class="player-role">${expectedRole}</p>
                        ${detailsHtml}
                    </div>
                </div>`;
        } catch (error) {
            container.innerHTML = `<div class="player-card"><div class="player-info"><p class="text-danger">Could not load data for ${playerName}.</p></div></div>`;
        }
    }

    function showAlert(message) {
        alertContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message} <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>`;
    }

    batsmanSelect.addEventListener('change', async function () {
        if (!this.value) return;

        populateSelect(bowlerSelect, [], 'Loading bowlers...');
        populateSelect(venueSelect, [], 'Select bowler first...');
        bowlerSelect.disabled = true;
        venueSelect.disabled = true;

        const response = await fetch(`/get_bowlers/${this.value}`);
        const bowlers = await response.json();

        populateSelect(bowlerSelect, bowlers, 'Choose a bowler...');
        checkFormValidity();
    });

    bowlerSelect.addEventListener('change', async function () {
        if (!this.value || !batsmanSelect.value) return;

        populateSelect(venueSelect, [], 'Loading venues...');
        venueSelect.disabled = true;

        const response = await fetch(`/get_venues/${batsmanSelect.value}/${this.value}`);
        const venues = await response.json();

        populateSelect(venueSelect, venues, 'Choose a venue...');
        checkFormValidity();
    });

    // --- VENUE INTELLIGENCE LOGIC ---
    const venueBadgeContainer = document.getElementById('venue-badge-container');

    // Knowledge Base: Map venues to their known characteristics (Exact names from dataset)
    const venueInsights = {
        "Wankhede Stadium, Mumbai": { type: "Batting Paradise", color: "success", icon: "bi-graph-up-arrow", text: "Expect High Scores & Boundaries" },
        "M Chinnaswamy Stadium, Bengaluru": { type: "Batting Paradise", color: "success", icon: "bi-lightning-charge", text: "Small Boundaries, High Scoring" },
        "MA Chidambaram Stadium, Chepauk, Chennai": { type: "Spin Friendly", color: "warning", icon: "bi-tornado", text: "Grip & Turn for Spinners" },
        "Eden Gardens, Kolkata": { type: "Balanced", color: "info", icon: "bi-scale", text: "Good Balance between Bat & Ball" },
        "Narendra Modi Stadium, Ahmedabad": { type: "Batting Friendly", color: "success", icon: "bi-trophy", text: "Fast Outfield, Good for Batting" },
        "Arun Jaitley Stadium, Delhi": { type: "Spin Friendly", color: "warning", icon: "bi-tropical-storm", text: "Slow Pitch, Spinners Dominate" },
        "Rajiv Gandhi International Stadium, Uppal, Hyderabad": { type: "Batting Friendly", color: "success", icon: "bi-sunrise", text: "Flat Deck, Good for Chasing" },
        "Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh": { type: "Pace Friendly", color: "primary", icon: "bi-wind", text: "Help for Fast Bowlers early on" },
        "Sawai Mansingh Stadium, Jaipur": { type: "Bowling Friendly", color: "primary", icon: "bi-shield-shaded", text: "Large Boundaries, Low Scoring" }
    };

    function updateVenueBadge(venueName) {
        console.log("Venue changed to:", venueName); // DEBUG

        let info = venueInsights[venueName];

        // Fallback: Fuzzy search if exact match fails
        if (!info && venueName) {
            const lowerName = venueName.toLowerCase();
            if (lowerName.includes("wankhede")) info = venueInsights["Wankhede Stadium, Mumbai"];
            else if (lowerName.includes("chinnaswamy")) info = venueInsights["M Chinnaswamy Stadium, Bengaluru"];
            else if (lowerName.includes("chidambaram") || lowerName.includes("chepauk")) info = venueInsights["MA Chidambaram Stadium, Chepauk, Chennai"];
            else if (lowerName.includes("eden gardens")) info = venueInsights["Eden Gardens, Kolkata"];
            else if (lowerName.includes("narendra modi") || lowerName.includes("motera")) info = venueInsights["Narendra Modi Stadium, Ahmedabad"];
            else if (lowerName.includes("arun jaitley") || lowerName.includes("kotla")) info = venueInsights["Arun Jaitley Stadium, Delhi"];
            else if (lowerName.includes("rajiv gandhi")) info = venueInsights["Rajiv Gandhi International Stadium, Uppal, Hyderabad"];
            else if (lowerName.includes("bindra") || lowerName.includes("mohali")) info = venueInsights["Punjab Cricket Association IS Bindra Stadium, Mohali, Chandigarh"];
            else if (lowerName.includes("mansingh")) info = venueInsights["Sawai Mansingh Stadium, Jaipur"];
        }

        if (!venueName || !info) {
            venueBadgeContainer.innerHTML = '';
            venueBadgeContainer.style.opacity = '0';
            return;
        }

        // Dynamic Badge HTML with Neon Glow
        const badgeHTML = `
            <div class="glass-panel d-flex align-items-center px-3 py-2" 
                 style="border-left: 4px solid var(--bs-${info.color}); background: rgba(255,255,255,0.05); border-radius: 8px; animation: slideInFade 0.5s ease-out;">
                <div class="icon-circle bg-${info.color} bg-opacity-25 text-${info.color} me-3" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <i class="bi ${info.icon} fs-5"></i>
                </div>
                <div>
                    <h6 class="mb-0 fw-bold text-${info.color}" style="text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem;">${info.type}</h6>
                    <small class="text-white-50" style="font-size: 0.75rem;">${info.text}</small>
                </div>
            </div>
        `;

        venueBadgeContainer.style.opacity = '0';
        setTimeout(() => {
            venueBadgeContainer.innerHTML = badgeHTML;
            venueBadgeContainer.style.opacity = '1';
        }, 150);
    }

    // Add CSS for animation if not exists
    if (!document.getElementById('badge-anim-style')) {
        const style = document.createElement('style');
        style.id = 'badge-anim-style';
        style.innerHTML = `
            @keyframes slideInFade {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            #venue-badge-container { transition: opacity 0.3s ease; }
        `;
        document.head.appendChild(style);
    }

    venueSelect.addEventListener('change', function () {
        checkFormValidity();
        updateVenueBadge(this.value);
    });

    ballsFacedInput.addEventListener('input', checkFormValidity);

    predictForm.addEventListener('submit', async function (event) {
        // ... (Existing Submit Logic) ...
        event.preventDefault();
        alertContainer.innerHTML = '';
        predictBtn.disabled = true;
        predictBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...`;

        try {
            const formData = new FormData(predictForm);
            const response = await fetch('/predict', { method: 'POST', body: formData });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Prediction failed.');

            predictionContainer.style.display = 'block';
            setTimeout(() => {
                predictionContainer.style.opacity = 1;
                // ✅ NECESSARY CHANGE: Scroll results to the top of the screen
                predictionContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 10);

            // Update Gauges and Labels
            const balls = parseInt(ballsFacedInput.value) || 20;
            const maxRuns = Math.max(40, balls * 2.5);
            // Royal Blue for Runs
            createOrUpdateGauge('runs-gauge', data.predicted_runs, maxRuns, '#0d6efd');
            document.getElementById('predicted-runs-label').textContent = data.predicted_runs.toFixed(0);

            // Success Green for Strike Rate
            createOrUpdateGauge('strike-rate-gauge', data.strike_rate, 300, '#198754');
            document.getElementById('strike-rate-label').textContent = data.strike_rate.toFixed(1);

            // Warning Amber for Dismissal Rate
            createOrUpdateGauge('dismissal-rate-gauge', data.dismissal_rate * 100, 100, '#ffc107');
            document.getElementById('dismissal-rate-label').textContent = data.dismissal_rate.toFixed(2);

            const dismissalProbEl = document.getElementById('dismissal-prob');
            dismissalProbEl.textContent = data.dismissal_prob;
            // Red for Danger (Yes), Green for Safe (No)
            dismissalProbEl.style.color = data.dismissal_prob === 'Yes' ? '#dc3545' : '#198754';

            // --- THE VERDICT LOGIC ---
            updateVerdict(data);

            displayPlayerCard(batsmanSelect.value, 'batsman-card-container', 'Batsman');
            displayPlayerCard(bowlerSelect.value, 'bowler-card-container', 'Bowler');

            // --- NEXT BALL PREDICTION ---
            try {
                const ballResponse = await fetch('/predict_next_ball', { method: 'POST', body: formData });
                const ballData = await ballResponse.json();

                if (ballResponse.ok) {
                    const container = document.getElementById('outcome-bars');
                    container.innerHTML = '';
                    document.getElementById('ball-probability-section').style.display = 'block';

                    const colors = {
                        '0': '#e2e8f0', // Bright Silver for DOT
                        '1': '#20c997', // Teal
                        '2': '#198754', // Green
                        '3': '#198754', // Green
                        '4': '#0d6efd', // Blue
                        '5': '#fd7e14', // Orange
                        '6': '#d63384', // Pink/Purple
                        'W': '#dc3545'  // Red
                    };

                    Object.entries(ballData).forEach(([outcome, prob]) => {
                        const color = colors[outcome] || '#adb5bd';
                        const label = outcome === 'W' ? 'WICKET' : (outcome === '0' ? 'DOT' : outcome);

                        // Minimum visual height of 5% so bar is always visible if probability > 0
                        const visualHeight = prob > 0 ? Math.max(prob, 5) : 0;

                        container.innerHTML += `
                            <div class="col-md-2 col-4 text-center mb-3">
                                <div class="progress vertical-progress mx-auto position-relative" style="height: 120px; width: 24px; background-color: rgba(255,255,255,0.05); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                                    <div class="progress-bar position-absolute bottom-0 w-100" role="progressbar" 
                                         style="height: ${visualHeight}%; background-color: ${color}; transition: height 1s ease-in-out; border-radius: 12px; box-shadow: 0 0 10px ${color}80;" 
                                         aria-valuenow="${prob}" aria-valuemin="0" aria-valuemax="100"></div>
                                </div>
                                <div class="mt-2 small fw-bold text-white-50 text-uppercase" style="font-size: 0.75rem;">${label}</div>
                                <div class="fw-bold text-white" style="font-size: 0.9rem;">${prob}%</div>
                            </div>
                        `;
                    });
                }
            } catch (e) {
                console.error("Ball prediction failed:", e);
            }

        } catch (error) {
            showAlert(error.message);
        } finally {
            predictBtn.disabled = false;
            // ✅ NECESSARY CHANGE: Restore the button's original HTML
            predictBtn.innerHTML = originalBtnHTML;
        }
    });

    document.querySelector('a[href="#predict-section"]').addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector('#predict-section').scrollIntoView({
            behavior: 'smooth'
        });
    });

    checkFormValidity();
});