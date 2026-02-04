document.addEventListener('DOMContentLoaded', function () {
    // --- 1. Element Caching & Initial State ---
    const player1Select = document.getElementById('player1');
    const player2Select = document.getElementById('player2');
    const viewBtn = document.getElementById('viewBtn');
    const resultsArea = document.getElementById('results-area');
    const originalBtnHTML = viewBtn.innerHTML; // Store original button content

    let allPlayersWithRoles = {}; // Cache for { name: role }

    // Initialize animations library
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            mirror: false
        });
    }

    // --- 2. Helper Functions ---

    /**
     * Controls the enabled/disabled state of the "View Stats" button.
     */
    function checkFormValidity() {
        viewBtn.disabled = !player1Select.value;
    }

    /**
     * Determines which stats (batting, bowling) to show in a comparison.
     * @param {string} role1 - The role of the first player.
     * @param {string} role2 - The role of the second player.
     * @returns {{showBatting: boolean, showBowling: boolean}}
     */
    function determineStatVisibility(role1, role2) {
        const battingRoles = new Set(['Batsman', 'All-Rounder']);
        const bowlingRoles = new Set(['Bowler', 'All-Rounder']);

        // Show a stat type only if BOTH players are eligible for it.
        return {
            showBatting: battingRoles.has(role1) && battingRoles.has(role2),
            showBowling: bowlingRoles.has(role1) && bowlingRoles.has(role2)
        };
    }

    /**
     * Fetches the complete profile (stats and card data) for a given player.
     * @param {string} playerName - The name of the player to fetch.
     * @returns {Promise<object|null>} A promise that resolves to the player's profile data.
     */
    async function getFullProfileData(playerName) {
        if (!playerName) return null;
        try {
            const [statsRes, cardRes] = await Promise.all([
                fetch(`/get_player_stats/${playerName}`),
                fetch(`/get_player_card/${playerName}`)
            ]);
            if (!statsRes.ok || !cardRes.ok) throw new Error(`Could not load complete data for ${playerName}.`);

            const stats = await statsRes.json();
            const card = await cardRes.json();
            return { stats, card, name: playerName };
        } catch (error) {
            console.error(`Error fetching data for ${playerName}:`, error);
            return { error: error.message, name: playerName };
        }
    }

    /**
     * Helper to render the Hero Card (Image + Name)
     */
    function buildHeroCard(profile) {
        if (!profile) return '';
        const { card, error, name } = profile;
        if (error || !card) return `<div class="alert alert-danger p-2 small">Error loading ${name}</div>`;

        return `
            <div class="player-card glass-panel border-0 mb-0 h-100 transform-hover">
                <div class="position-relative d-inline-block mx-auto">
                    <img src="${card.profile_image_url}" class="rounded-circle border border-4 border-white shadow my-3" 
                            width="120" height="120" style="object-fit: cover;"
                            onerror="this.src='https://ui-avatars.com/api/?name=${card.player_name.replace(' ', '+')}&size=120';">
                    <span class="position-absolute bottom-0 start-50 translate-middle-x badge bg-primary rounded-pill text-uppercase small shadow-sm"
                            style="font-size: 0.7rem; letter-spacing: 1px;">
                        ${card.role}
                    </span>
                </div>
                <h3 class="fw-bold mt-2 mb-1" style="color: var(--heading-color);">${card.player_name}</h3>
                <p class="text-muted small mb-0">${card.batting_hand} • ${card.bowling_style}</p>
            </div>`;
    }

    /**
     * Renders a Horizontal Bar Chart comparing two players.
     */
    function renderComparisonChart(profile1, profile2, showBatting, showBowling) {
        // Data Normalization Helper
        const normalize = (val, max) => Math.min((parseFloat(val) || 0) / max * 100, 100);

        const labels = [];
        const data1 = [];
        const data2 = [];
        const statsRows = []; // To store rows for the text stats table

        const s1 = profile1.stats;
        const s2 = profile2 ? profile2.stats : null;

        // Helper to safe-get value
        const val = (obj, key) => obj && obj[key] !== undefined && obj[key] !== null ? obj[key] : '-';
        const floatVal = (v) => v !== '-' ? parseFloat(v).toFixed(2) : '-';

        if (showBatting && s1.batting) {
            labels.push('Runs', 'Average', 'Strike Rate');

            // Normalized Data for Chart
            data1.push(normalize(s1.batting.total_runs, 10000));
            data1.push(normalize(s1.batting.average, 60));
            data1.push(normalize(s1.batting.strike_rate, 180));

            // Text Stats
            statsRows.push({ label: 'Total Runs', v1: val(s1.batting, 'total_runs'), v2: s2 ? val(s2.batting, 'total_runs') : '-' });
            statsRows.push({ label: 'Batting Avg', v1: floatVal(val(s1.batting, 'average')), v2: s2 ? floatVal(val(s2.batting, 'average')) : '-' });
            statsRows.push({ label: 'Strike Rate', v1: floatVal(val(s1.batting, 'strike_rate')), v2: s2 ? floatVal(val(s2.batting, 'strike_rate')) : '-' });

            if (s2 && s2.batting) {
                data2.push(normalize(s2.batting.total_runs, 10000));
                data2.push(normalize(s2.batting.average, 60));
                data2.push(normalize(s2.batting.strike_rate, 180));
            }
        }

        if (showBowling && s1.bowling) {
            labels.push('Wickets', 'Economy', 'Bowling Avg');

            // For Bar Chart: Higher is better logic for visual consistency
            // Inverting Economy and Bowling Avg for the visual score
            const normInv = (val, max) => Math.max(0, (max - (parseFloat(val) || 0)) / max * 100);

            data1.push(normalize(s1.bowling.total_wickets, 500));
            data1.push(normInv(s1.bowling.economy_rate, 12));
            data1.push(normInv(s1.bowling.bowling_average, 50));

            // Text Stats
            statsRows.push({ label: 'Wickets', v1: val(s1.bowling, 'total_wickets'), v2: s2 ? val(s2.bowling, 'total_wickets') : '-' });
            statsRows.push({ label: 'Economy', v1: floatVal(val(s1.bowling, 'economy_rate')), v2: s2 ? floatVal(val(s2.bowling, 'economy_rate')) : '-' });
            statsRows.push({ label: 'Bowling Avg', v1: floatVal(val(s1.bowling, 'bowling_average')), v2: s2 ? floatVal(val(s2.bowling, 'bowling_average')) : '-' });

            if (s2 && s2.bowling) {
                data2.push(normalize(s2.bowling.total_wickets, 500));
                data2.push(normInv(s2.bowling.economy_rate, 12));
                data2.push(normInv(s2.bowling.bowling_average, 50));
            }
        }

        const canvasId = 'comparisonChart';
        // Delay chart creation slightly to ensure DOM is ready
        setTimeout(() => {
            const ctx = document.getElementById(canvasId).getContext('2d');
            new Chart(ctx, {
                type: 'bar', // Horizontal Bar Chart
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: profile1.card.player_name,
                            data: data1,
                            backgroundColor: '#0d6efd', // Solid Blue
                            barPercentage: 0.6,
                            categoryPercentage: 0.8,
                            borderRadius: 4
                        },
                        profile2 ? {
                            label: profile2.card.player_name,
                            data: data2,
                            backgroundColor: '#198754', // Solid Green
                            barPercentage: 0.6,
                            categoryPercentage: 0.8,
                            borderRadius: 4
                        } : null
                    ].filter(Boolean)
                },
                options: {
                    indexAxis: 'y', // Horizontal bars
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            display: false,
                            max: 100,
                            grid: { display: false }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: {
                                color: '#e2e8f0',
                                font: { family: 'Exo 2', size: 14, weight: '600' }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#e2e8f0', font: { family: 'Inter' } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    return context.dataset.label + ': ' + Math.round(context.raw) + ' / 100';
                                }
                            }
                        }
                    }
                }
            });
        }, 100);

        // Generate Stats Table HTML
        const rowsHtml = statsRows.map(row => `
            <div class="row mb-3 border-bottom border-dark pb-2">
                <div class="col-4 text-start small text-uppercase fw-bold text-secondary text-truncate" title="${row.label}">${row.label}</div>
                <div class="col-4 text-center fw-bold fs-5 text-primary">${row.v1}</div>
                <div class="col-4 text-end fw-bold fs-5 ${profile2 ? 'text-success' : 'text-muted'}">${row.v2}</div>
            </div>
        `).join('');

        return `
            <div class="glass-panel border-0 p-4 h-100 position-relative">
                <div class="d-flex justify-content-between align-items-center mb-5 border-bottom border-secondary pb-3">
                    <h4 class="mb-0 text-white"><i class="bi bi-bar-chart-fill me-2 text-primary"></i>Matchup Intel</h4>
                    ${profile2 ? '<span class="badge bg-primary">VS MODE</span>' : '<span class="badge bg-secondary">SINGLE MODE</span>'}
                </div>

                <div class="row">
                    <!-- Left: Horizontal Bar Chart -->
                    <div class="col-lg-7 mb-4 mb-lg-0 border-end border-secondary pe-lg-4">
                         <div style="height: 350px;">
                            <canvas id="${canvasId}"></canvas>
                        </div>
                        <p class="text-center text-muted small mt-2">Performance Rating (0-100)</p>
                    </div>

                    <!-- Right: Written Stats -->
                    <div class="col-lg-5 ps-lg-4 d-flex flex-column justify-content-center">
                        <div class="d-flex justify-content-between mb-4 text-uppercase fw-bold text-white-50 border-bottom border-secondary pb-2">
                            <span>Metric</span>
                            <span class="text-end text-primary text-truncate" style="max-width: 35%;">${profile1.card.player_name}</span>
                            <span class="text-end text-success text-truncate" style="max-width: 35%;">${profile2 ? profile2.card.player_name : '-'}</span>
                        </div>
                        ${rowsHtml}
                    </div>
                </div>
            </div>`;
    }

    // --- 3. Event Listeners ---

    /**
     * Updates the avatar preview for a selected player.
     * @param {string} playerName - Selected player name.
     * @param {string} imgId - ID of the image element to update.
     */
    async function updateAvatarPreview(playerName, imgId) {
        const imgEl = document.getElementById(imgId);
        if (!playerName) {
            imgEl.src = `https://ui-avatars.com/api/?name=${imgId.includes('p1') ? 'P1' : 'P2'}&background=e9ecef&color=adb5bd&size=150`;
            imgEl.classList.remove('active');
            return;
        }

        try {
            const response = await fetch(`/get_player_card/${playerName}`);
            if (response.ok) {
                const data = await response.json();
                imgEl.src = data.profile_image_url;
                imgEl.classList.add('active');
            }
        } catch (e) {
            console.error("Failed to fetch avatar preview", e);
        }
    }

    /**
     * Filters Player 2 dropdown based on Player 1's role for a relevant comparison.
     */
    player1Select.addEventListener('change', function () {
        const player1Name = this.value;
        updateAvatarPreview(player1Name, 'p1-preview'); // Update Avatar

        const player1Role = allPlayersWithRoles[player1Name];

        player2Select.value = '';
        updateAvatarPreview('', 'p2-preview'); // Reset P2 Avatar

        if (!player1Name) {
            player2Select.innerHTML = '<option value="">Choose player 1 first...</option>';
            player2Select.disabled = true;
            checkFormValidity();
            return;
        }

        let eligibleRoles;
        if (player1Role === 'Batsman') {
            eligibleRoles = ['Batsman', 'All-Rounder'];
        } else if (player1Role === 'Bowler') {
            eligibleRoles = ['Bowler', 'All-Rounder'];
        } else {
            eligibleRoles = ['Batsman', 'Bowler', 'All-Rounder'];
        }

        const filteredPlayers = Object.keys(allPlayersWithRoles)
            .filter(p => p !== player1Name && eligibleRoles.includes(allPlayersWithRoles[p]))
            .sort();

        let optionsHtml = '<option value="">Choose for comparison...</option>';
        filteredPlayers.forEach(player => {
            optionsHtml += `<option value="${player}">${player}</option>`;
        });

        player2Select.innerHTML = optionsHtml;
        player2Select.disabled = false;
        checkFormValidity();
    });

    player2Select.addEventListener('change', function () {
        updateAvatarPreview(this.value, 'p2-preview');
        checkFormValidity();
    });

    /**
     * Main handler for the "View Stats" button click.
     */
    viewBtn.addEventListener('click', async function () {
        const player1Name = player1Select.value;
        const player2Name = player2Select.value;

        viewBtn.disabled = true;
        viewBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Loading...`;
        resultsArea.innerHTML = `<div class="col-12 text-center p-5"><div class="spinner-border text-primary" style="width: 3rem; height: 3rem;"></div></div>`;

        try {
            if (player1Name && player2Name) {
                const { showBatting, showBowling } = determineStatVisibility(
                    allPlayersWithRoles[player1Name],
                    allPlayersWithRoles[player2Name]
                );
                const [p1Profile, p2Profile] = await Promise.all([
                    getFullProfileData(player1Name),
                    getFullProfileData(player2Name)
                ]);

                // Chart Layout:
                // Only render the Chart Card, removing redundant Hero Cards
                resultsArea.innerHTML = `
                    <div class="col-lg-11 mx-auto" data-aos="fade-up">
                         ${renderComparisonChart(p1Profile, p2Profile, showBatting, showBowling)}
                    </div>`;
            } else {
                // Single Player View
                const profile = await getFullProfileData(player1Name);
                resultsArea.innerHTML = `
                    <div class="col-lg-10 mx-auto" data-aos="fade-up">
                         ${renderComparisonChart(profile, null, true, true)}
                    </div>`;
            }

            // Auto-scroll to the results section after content is rendered
            resultsArea.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (e) {
            console.error("A critical error occurred:", e);
            resultsArea.innerHTML = `<div class="col-12"><div class="alert alert-danger">An unexpected error occurred. Please try again.</div></div>`;
        } finally {
            viewBtn.disabled = false;
            viewBtn.innerHTML = originalBtnHTML;
            checkFormValidity();
            if (typeof AOS !== 'undefined') setTimeout(() => AOS.refresh(), 50);
        }
    });

    // --- 4. Initialization ---

    /**
     * Fetches all player roles when the page loads to populate the dropdowns.
     */
    async function initializePage() {
        try {
            const response = await fetch('/get_all_player_roles');
            if (!response.ok) throw new Error('Failed to load player data.');
            allPlayersWithRoles = await response.json();
            player1Select.disabled = false;
        } catch (error) {
            console.error(error);
            resultsArea.innerHTML = `<div class="col-12"><div class="alert alert-danger">${error.message}</div></div>`;
        }
    }

    // Set initial form state and fetch player data
    checkFormValidity();
    initializePage();
});