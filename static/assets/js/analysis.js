document.addEventListener('DOMContentLoaded', function() {
    const batsmanSelect = document.getElementById('batsman');
    const bowlerSelect = document.getElementById('bowler');
    const venueSelect = document.getElementById('venue');
    const ballsFacedInput = document.getElementById('ballsFaced');
    const predictBtn = document.getElementById('predictBtn');
    const predictForm = document.getElementById('predict-form');
    const predictionContainer = document.getElementById('prediction-container');
    const alertContainer = document.getElementById('alert-container');
    
    // ✅ NECESSARY CHANGE: Store the button's original HTML content
    const originalBtnHTML = predictBtn.innerHTML;

    const gaugeCharts = { runs: null, strikeRate: null, dismissalRate: null };

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

    batsmanSelect.addEventListener('change', async function() {
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

    bowlerSelect.addEventListener('change', async function() {
        if (!this.value || !batsmanSelect.value) return;

        populateSelect(venueSelect, [], 'Loading venues...');
        venueSelect.disabled = true;

        const response = await fetch(`/get_venues/${batsmanSelect.value}/${this.value}`);
        const venues = await response.json();

        populateSelect(venueSelect, venues, 'Choose a venue...');
        checkFormValidity();
    });

    venueSelect.addEventListener('change', checkFormValidity);
    ballsFacedInput.addEventListener('input', checkFormValidity);

    predictForm.addEventListener('submit', async function(event) {
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
            createOrUpdateGauge('runs-gauge', data.predicted_runs, maxRuns, '#0d6efd');
            document.getElementById('predicted-runs-label').textContent = data.predicted_runs.toFixed(0);

            createOrUpdateGauge('strike-rate-gauge', data.strike_rate, 300, '#198754');
            document.getElementById('strike-rate-label').textContent = data.strike_rate.toFixed(1);
            
            createOrUpdateGauge('dismissal-rate-gauge', data.dismissal_rate * 100, 100, '#ffc107');
            document.getElementById('dismissal-rate-label').textContent = data.dismissal_rate.toFixed(2);
            
            const dismissalProbEl = document.getElementById('dismissal-prob');
            dismissalProbEl.textContent = data.dismissal_prob;
            dismissalProbEl.style.color = data.dismissal_prob === 'Yes' ? '#dc3545' : '#198754';
            
            displayPlayerCard(batsmanSelect.value, 'batsman-card-container', 'Batsman');
            displayPlayerCard(bowlerSelect.value, 'bowler-card-container', 'Bowler');

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