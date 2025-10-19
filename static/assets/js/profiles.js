document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations if AOS is available
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            mirror: false
        });
    }

    const player1Select = document.getElementById('player1');
    const player2Select = document.getElementById('player2');
    const viewBtn = document.getElementById('viewBtn');
    const resultsArea = document.getElementById('results-area');

    let allPlayersWithRoles = {}; // To store { name: role }

    // --- 1. Fetch all player roles on page load ---
    async function initializePlayerRoles() {
        try {
            const response = await fetch('/get_all_player_roles');
            if (!response.ok) throw new Error('Failed to load player roles from the server.');
            allPlayersWithRoles = await response.json();
            player1Select.disabled = false; // Enable the first dropdown once data is ready
        } catch (error) {
            console.error(error);
            resultsArea.innerHTML = `<div class="col-12"><div class="alert alert-danger">${error.message}</div></div>`;
        }
    }

    // --- 2. Filter Player 2 dropdown based on Player 1's role ---
    player1Select.addEventListener('change', function() {
        const player1Name = this.value;
        const player1Role = allPlayersWithRoles[player1Name];
        
        player2Select.value = '';
        
        if (!player1Name) {
            player2Select.innerHTML = '<option value="">Choose a player...</option>';
            player2Select.disabled = true;
            return;
        }

        let eligibleRoles;
        if (player1Role === 'Batsman') {
            eligibleRoles = ['Batsman', 'All-Rounder'];
        } else if (player1Role === 'Bowler') {
            eligibleRoles = ['Bowler', 'All-Rounder'];
        } else { // All-Rounder
            eligibleRoles = ['Batsman', 'Bowler', 'All-Rounder'];
        }

        const filteredPlayers = Object.keys(allPlayersWithRoles).filter(p => eligibleRoles.includes(allPlayersWithRoles[p]));

        let optionsHtml = '<option value="">Choose a player...</option>';
        filteredPlayers.sort().forEach(player => {
            if (player !== player1Name) { // Exclude the player already selected
                optionsHtml += `<option value="${player}">${player}</option>`;
            }
        });
        player2Select.innerHTML = optionsHtml;
        player2Select.disabled = false;
    });

    // --- 3. Fetches stats and card data for a player ---
    async function getFullProfileData(playerName) {
        if (!playerName) return null;
        try {
            const [statsRes, cardRes] = await Promise.all([
                fetch(`/get_player_stats/${playerName}`),
                fetch(`/get_player_card/${playerName}`)
            ]);
            if (!statsRes.ok || !cardRes.ok) {
                const errorData = await (statsRes.ok ? cardRes.json() : statsRes.json());
                throw new Error(errorData.error || `Could not load data for ${playerName}.`);
            }
            const stats = await statsRes.json();
            const card = await cardRes.json();
            return { stats, card, name: playerName };
        } catch (error) {
            console.error(`Error fetching data for ${playerName}:`, error);
            return { error: error.message, name: playerName };
        }
    }
    
    // --- 4. Builds the HTML for a single player's profile ---
    function buildProfileContent(profile, showBatting, showBowling) {
        try {
            if (!profile) return `<div class="alert alert-warning">Player data could not be loaded.</div>`;
            const { card, stats, error, name } = profile;
            if (error) { return `<div class="alert alert-danger">Error for ${name}: ${error}</div>`; }
            if (!card || !stats) { return `<div class="alert alert-danger">Incomplete data for ${name}.</div>`; }

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
            
            // ✅ LAYOUT FIX: Always return a vertical stack.
            return cardHtml + battingStatsHtml + bowlingStatsHtml;

        } catch(e) { 
            console.error("Error building profile HTML:", e);
            return `<div class="col-12"><div class="alert alert-danger">An error occurred while displaying the profile.</div></div>`;
        }
    }
    
    // --- 5. Main event listener for the "View Stats" button ---
    viewBtn.addEventListener('click', async function() {
        const player1Name = player1Select.value;
        const player2Name = player2Select.value;

        if (!player1Name && !player2Name) {
            resultsArea.innerHTML = `<div class="col-12"><div class="alert alert-info">Please select at least one player.</div></div>`;
            return;
        }

        viewBtn.disabled = true;
        viewBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Loading...`;
        resultsArea.innerHTML = `<div class="col-12 text-center p-5"><div class="spinner-border text-primary"></div></div>`;

        try {
            let showBatting = true;
            let showBowling = true;

            if (player1Name && player2Name && player1Name !== player2Name) { 
                const p1Role = allPlayersWithRoles[player1Name];
                const p2Role = allPlayersWithRoles[player2Name];
                
                if (p1Role === 'All-Rounder' && p2Role === 'All-Rounder') {
                    showBatting = true;
                    showBowling = true;
                } else if ((p1Role === 'Batsman' && p2Role === 'All-Rounder') || (p2Role === 'Batsman' && p1Role === 'All-Rounder') || (p1Role === 'Batsman' && p2Role === 'Batsman')) {
                    showBowling = false;
                } else if ((p1Role === 'Bowler' && p2Role === 'All-Rounder') || (p2Role === 'Bowler' && p1Role === 'All-Rounder') || (p1Role === 'Bowler' && p2Role === 'Bowler')) {
                    showBatting = false;
                }
            }

            if (player1Name && player2Name && player1Name !== player2Name) {
                const [p1Profile, p2Profile] = await Promise.all([getFullProfileData(player1Name), getFullProfileData(player2Name)]);
                resultsArea.innerHTML = `
                    <div class="col-lg-6" data-aos="fade-up"><div class="row g-4">${buildProfileContent(p1Profile, showBatting, showBowling)}</div></div>
                    <div class="col-lg-6" data-aos="fade-up" data-aos-delay="100"><div class="row g-4">${buildProfileContent(p2Profile, showBatting, showBowling)}</div></div>`;
            } else {
                const playerName = player1Name || player2Name;
                const profile = await getFullProfileData(playerName);
                // For a single player, always show all available stats.
                resultsArea.innerHTML = `<div class="col-lg-8 mx-auto" data-aos="fade-up"><div class="row g-4">${buildProfileContent(profile, true, true)}</div></div>`;
            }
        } catch (e) {
            console.error("A critical error occurred:", e);
            resultsArea.innerHTML = `<div class="col-12"><div class="alert alert-danger">An unexpected error occurred.</div></div>`;
        } finally {
            viewBtn.disabled = false;
            viewBtn.innerHTML = 'View Stats';
            if (typeof AOS !== 'undefined') setTimeout(() => AOS.refresh(), 50);
        }
    });
    
    // --- 6. Initial call to load the player roles ---
    initializePlayerRoles();
});

