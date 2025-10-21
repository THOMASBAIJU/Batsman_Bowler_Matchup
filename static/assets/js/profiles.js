document.addEventListener('DOMContentLoaded', function() {
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
     * Builds the complete HTML content for a single player's profile column.
     * @param {object} profile - The player's profile data from getFullProfileData.
     * @param {boolean} showBatting - Flag to determine if batting stats should be rendered.
     * @param {boolean} showBowling - Flag to determine if bowling stats should be rendered.
     * @returns {string} The HTML string for the profile.
     */
    function buildProfileContent(profile, showBatting, showBowling) {
        if (!profile) return `<div class="alert alert-warning">Player data could not be loaded.</div>`;
        const { card, stats, error, name } = profile;

        if (error) return `<div class="alert alert-danger">Error for ${name}: ${error}</div>`;
        if (!card || !stats) return `<div class="alert alert-danger">Incomplete data for ${name}.</div>`;

        let cardDetailsHtml = '';
        if (card.batting_hand && card.batting_hand !== 'N/A') cardDetailsHtml += `<p class="player-detail mb-0">${card.batting_hand}</p>`;
        if (card.bowling_style && card.bowling_style !== 'N/A') cardDetailsHtml += `<p class="player-detail mb-0">${card.bowling_style}</p>`;

        const cardHtml = `
            <div class="col-12">
                <div class="player-card">
                    <img src="${card.profile_image_url}" alt="${card.player_name}" onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${card.player_name.replace(' ', '+')}&background=0d6efd&color=fff&size=150';">
                    <h5>${card.player_name}</h5>
                    <p class="player-role">${card.role}</p>
                    ${cardDetailsHtml}
                </div>
            </div>`;

        let battingStatsHtml = '';
        if (showBatting && stats.batting) {
            const s = stats.batting;
            battingStatsHtml = `
                <div class="col-12 mt-4">
                    <div class="stat-card">
                        <h4>Batting Stats</h4>
                        <div class="stat-item"><span class="label">Total Runs</span><span class="value">${s.total_runs}</span></div>
                        <div class="stat-item"><span class="label">Balls Faced</span><span class="value">${s.total_balls_faced}</span></div>
                        <div class="stat-item"><span class="label">Average</span><span class="value">${s.average.toFixed(2)}</span></div>
                        <div class="stat-item"><span class="label">Strike Rate</span><span class="value">${s.strike_rate.toFixed(2)}</span></div>
                    </div>
                </div>`;
        }

        let bowlingStatsHtml = '';
        if (showBowling && stats.bowling) {
            const s = stats.bowling;
            bowlingStatsHtml = `
                <div class="col-12 mt-4">
                    <div class="stat-card">
                        <h4>Bowling Stats</h4>
                        <div class="stat-item"><span class="label">Wickets</span><span class="value">${s.total_wickets}</span></div>
                        <div class="stat-item"><span class="label">Runs Conceded</span><span class="value">${s.total_runs_conceded}</span></div>
                        <div class="stat-item"><span class="label">Average</span><span class="value">${s.bowling_average.toFixed(2)}</span></div>
                        <div class="stat-item"><span class="label">Economy</span><span class="value">${s.economy_rate.toFixed(2)}</span></div>
                    </div>
                </div>`;
        }
        
        return cardHtml + battingStatsHtml + bowlingStatsHtml;
    }

    // --- 3. Event Listeners ---

    /**
     * Filters Player 2 dropdown based on Player 1's role for a relevant comparison.
     */
    player1Select.addEventListener('change', function() {
        const player1Name = this.value;
        const player1Role = allPlayersWithRoles[player1Name];
        
        player2Select.value = '';
        
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
    
    player2Select.addEventListener('change', checkFormValidity);

    /**
     * Main handler for the "View Stats" button click.
     */
    viewBtn.addEventListener('click', async function() {
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
                resultsArea.innerHTML = `
                    <div class="col-lg-6" data-aos="fade-up">
                        <div class="row g-4">${buildProfileContent(p1Profile, showBatting, showBowling)}</div>
                    </div>
                    <div class="col-lg-6" data-aos="fade-up" data-aos-delay="100">
                        <div class="row g-4">${buildProfileContent(p2Profile, showBatting, showBowling)}</div>
                    </div>`;
            } else {
                const profile = await getFullProfileData(player1Name);
                resultsArea.innerHTML = `
                    <div class="col-lg-8 mx-auto" data-aos="fade-up">
                        <div class="row g-4">${buildProfileContent(profile, true, true)}</div>
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