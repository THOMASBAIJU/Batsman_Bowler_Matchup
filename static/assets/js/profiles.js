document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 1000,
        easing: 'ease-in-out',
        once: true,
        mirror: false
    });

    const player1Select = document.getElementById('player1');
    const player2Select = document.getElementById('player2');
    const viewBtn = document.getElementById('viewBtn');
    const resultsArea = document.getElementById('results-area');

    async function getFullProfileData(playerName) {
        try {
            const [statsRes, cardRes] = await Promise.all([
                fetch(`/get_player_stats/${playerName}`),
                fetch(`/get_player_card/${playerName}`)
            ]);

            if (!statsRes.ok || !cardRes.ok) throw new Error(`Could not load full data for ${playerName}.`);
            
            const statsData = await statsRes.json();
            const cardData = await cardRes.json();
            statsData.name = playerName;

            return { stats: statsData, card: cardData };
        } catch (error) {
            console.error("Error creating full profile for", playerName, error);
            return { error: `<div class="alert alert-warning">${error.message}</div>` };
        }
    }
    
    function buildProfileHtml(profileData) {
        const { stats, card } = profileData;
        
        let cardDetailsHtml = '';
        if (card.batting_hand && card.batting_hand !== 'N/A') cardDetailsHtml += `<p class="player-detail mb-0">${card.batting_hand}</p>`;
        if (card.bowling_style && card.bowling_style !== 'N/A') cardDetailsHtml += `<p class="player-detail mb-0">${card.bowling_style}</p>`;

        const cardHtml = `
            <div class="player-card" data-aos="fade-up">
                <img src="${card.profile_image_url}" alt="${card.player_name}" onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${card.player_name.replace(' ', '+')}&background=0d6efd&color=fff&size=150';">
                <h5>${card.player_name}</h5>
                <p class="player-role">${card.role}</p>
                ${cardDetailsHtml}
            </div>`;
        
        let careerStatsHtml = '', chartsHtml = '';
        if (stats.batting) {
            const s = stats.batting;
            careerStatsHtml += `<div class="stat-card" data-aos="fade-up" data-aos-delay="100"><h4>Batting Career</h4><div class="stat-item"><span class="label">Total Runs</span><span class="value">${s.total_runs}</span></div><div class="stat-item"><span class="label">Total Balls Faced</span><span class="value">${s.total_balls_faced}</span></div><div class="stat-item"><span class="label">Dismissals</span><span class="value">${s.total_dismissals}</span></div><div class="stat-item"><span class="label">Strike Rate</span><span class="value">${s.strike_rate}</span></div><div class="stat-item"><span class="label">Average</span><span class="value">${s.average}</span></div></div>`;
            chartsHtml += `<div class="col-md-6 d-flex"><div class="stat-card w-100" data-aos="fade-up" data-aos-delay="200"><h4>vs Bowling Style (SR)</h4><canvas id="battingChart-${stats.name.replace(/ /g, '')}"></canvas></div></div>`;
        }
        if (stats.bowling) {
            const s = stats.bowling;
            careerStatsHtml += `<div class="stat-card" data-aos="fade-up" data-aos-delay="100"><h4>Bowling Career</h4><div class="stat-item"><span class="label">Wickets</span><span class="value">${s.total_wickets}</span></div><div class="stat-item"><span class="label">Runs Conceded</span><span class="value">${s.total_runs_conceded}</span></div><div class="stat-item"><span class="label">Balls Bowled</span><span class="value">${s.total_balls_bowled}</span></div><div class="stat-item"><span class="label">Economy</span><span class="value">${s.economy_rate}</span></div><div class="stat-item"><span class="label">Average</span><span class="value">${s.bowling_average}</span></div></div>`;
            chartsHtml += `<div class="col-md-6 d-flex"><div class="stat-card w-100" data-aos="fade-up" data-aos-delay="200"><h4>vs Batting Hand (Wickets)</h4><canvas id="bowlingChart-${stats.name.replace(/ /g, '')}"></canvas></div></div>`;
        }

        return `
            <div class="row mb-4 align-items-stretch">
                <div class="col-md-5 d-flex">${cardHtml}</div>
                <div class="col-md-7 d-flex flex-column">${careerStatsHtml}</div>
            </div>
            <div class="row">${chartsHtml}</div>`;
    }

    function createCharts(playerData, playerName) {
        if (playerData.batting && playerData.batting.perf_vs_bowling_style) {
            const ctx = document.getElementById(`battingChart-${playerName.replace(/ /g, '')}`);
            if (ctx) new Chart(ctx.getContext('2d'), { type: 'bar', data: { labels: playerData.batting.perf_vs_bowling_style.map(d => d.bowling_style_str), datasets: [{ label: 'Strike Rate', data: playerData.batting.perf_vs_bowling_style.map(d => d.strike_rate), backgroundColor: '#0d6efd' }] }, options: { indexAxis: 'y', responsive: true } });
        }
        if (playerData.bowling && playerData.bowling.perf_vs_batting_hand) {
            const ctx = document.getElementById(`bowlingChart-${playerName.replace(/ /g, '')}`);
            if (ctx) new Chart(ctx.getContext('2d'), { type: 'bar', data: { labels: playerData.bowling.perf_vs_batting_hand.map(d => d.batting_hand_str), datasets: [{ label: 'Wickets', data: playerData.bowling.perf_vs_batting_hand.map(d => d.wickets), backgroundColor: '#198754' }] }, options: { indexAxis: 'y', responsive: true } });
        }
    }
    
    viewBtn.addEventListener('click', async function() {
        const player1Name = player1Select.value;
        const player2Name = player2Select.value;
        resultsArea.innerHTML = '';
        
        if (!player1Name && !player2Name) return;

        // ✅ NECESSARY CHANGE: Disable button and show loading states
        viewBtn.disabled = true;
        viewBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...`;
        resultsArea.innerHTML = `<div class="col-12 text-center p-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

        try {
            if (player1Name && player2Name) {
                resultsArea.innerHTML = `<div class="col-lg-6" id="player1-col"></div><div class="col-lg-6" id="player2-col"></div>`;

                const [p1Profile, p2Profile] = await Promise.all([
                    getFullProfileData(player1Name),
                    getFullProfileData(player2Name)
                ]);
                
                document.getElementById('player1-col').innerHTML = p1Profile.error || buildProfileHtml(p1Profile);
                document.getElementById('player2-col').innerHTML = p2Profile.error || buildProfileHtml(p2Profile);

                setTimeout(() => {
                    if (!p1Profile.error) createCharts(p1Profile.stats, player1Name);
                    if (!p2Profile.error) createCharts(p2Profile.stats, player2Name);
                }, 100);

            } else {
                const playerName = player1Name || player2Name;
                const profile = await getFullProfileData(playerName);
                
                if (profile.error) {
                    resultsArea.innerHTML = profile.error;
                } else {
                    resultsArea.innerHTML = `<div class="col-12">${buildProfileHtml(profile)}</div>`;
                    setTimeout(() => createCharts(profile.stats, playerName), 100);
                }
            }
        } finally {
            // ✅ NECESSARY CHANGE: Re-enable button and restore its text
            viewBtn.disabled = false;
            viewBtn.innerHTML = 'View';

            setTimeout(() => {
                if (typeof AOS !== 'undefined') AOS.refresh();
            }, 50);
        }
    });
});