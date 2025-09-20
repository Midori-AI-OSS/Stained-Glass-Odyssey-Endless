<script>
  import { Swords, Target, Gem, Star } from 'lucide-svelte';
  import LoginRewardsPanel from './LoginRewardsPanel.svelte';
  
  export let userState = { level: 1, exp: 0, next_level_exp: 100, total_playtime: 0 };
  
  // Format playtime in hours and minutes
  function formatPlaytime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }
  
  // Calculate level progress percentage
  $: levelProgress = userState.exp && userState.next_level_exp 
    ? (userState.exp / userState.next_level_exp) * 100 
    : 0;
</script>

<div class="about-panel">
  <!-- About the Game Section -->
  <div class="about-section">
    <h3 class="section-title">About the Game</h3>
    <div class="about-content">
      <p class="game-description">
        Midori AI AutoFighter is an innovative auto-battler where strategy meets automation. 
        Build your team, collect powerful relics, and watch epic battles unfold as your characters 
        fight autonomously through procedurally generated dungeons.
      </p>
      <div class="features">
        <div class="feature">
          <Swords size={16} />
          Strategic Team Building
        </div>
        <div class="feature">
          <Target size={16} />
          Auto-Battle Combat
        </div>
        <div class="feature">
          <Gem size={16} />
          Mystical Relics & Cards
        </div>
        <div class="feature">
          <Star size={16} />
          Character Progression
        </div>
      </div>
    </div>
  </div>

  <!-- Player Stats Section -->
  <div class="stats-section">
    <h3 class="section-title">Player Statistics</h3>
    <div class="stats-content">
      <div class="stat-row">
        <span class="stat-label">Level</span>
        <span class="stat-value">{userState.level}</span>
      </div>
      <div class="level-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: {levelProgress}%"></div>
        </div>
        <span class="progress-text">{userState.exp} / {userState.next_level_exp} EXP</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Total Playtime</span>
        <span class="stat-value">{formatPlaytime(userState.total_playtime || 0)}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Runs Completed</span>
        <span class="stat-value">{userState.runs_completed || 0}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Battles Won</span>
        <span class="stat-value">{userState.battles_won || 0}</span>
      </div>
    </div>
  </div>

  <!-- Daily Login Rewards moved to separate panel -->

</div>

<style>
  .about-panel {
    position: relative;
    width: 320px;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    padding: 1rem;
    box-sizing: border-box;
    overflow-y: auto;
  }

  .about-section {
    flex: 0 0 auto;
  }

  .stats-section {
    flex: 1;
    min-height: 0;
  }

  .internal-divider {
    margin: 0.25rem 0 0.4rem 0;
    height: 0; /* use borders for crisp visibility across backgrounds */
    border-top: 1px solid rgba(255,255,255,0.55);
    border-bottom: 1px solid rgba(0,0,0,0.65);
  }

  .rewards-section {
    /* Place directly under stats with tight spacing */
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    position: relative; /* ensure a new stacking context separate from stats */
    z-index: 0;
  }

  .section-title {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.7);
    margin: 0 0 0.8rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
  }

  .about-content {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
  }

  .game-description {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 0.85rem;
    line-height: 1.4;
    color: rgba(255,255,255,0.9);
    text-shadow: 0 1px 1px rgba(0,0,0,0.5);
    margin: 0;
  }

  .features {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .feature {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 0.8rem;
    color: rgba(255,255,255,0.8);
    text-shadow: 0 1px 1px rgba(0,0,0,0.5);
    padding: 0.2rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .stats-content {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.3rem 0;
  }

  .stat-label {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 0.85rem;
    color: rgba(255,255,255,0.8);
    text-shadow: 0 1px 1px rgba(0,0,0,0.5);
  }

  .stat-value {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.7);
  }

  .level-progress {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    margin-bottom: 0.2rem;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.2);
    position: relative;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50, #8BC34A);
    transition: width 0.3s ease;
  }

  .progress-text {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.7);
    text-shadow: 0 1px 1px rgba(0,0,0,0.5);
    text-align: center;
  }

  @media (max-width: 768px) {
    .about-panel { width: 280px; }
  }

  @media (max-width: 599px) {
    .about-panel {
      position: relative;
      width: 100%;
      height: auto;
      margin: 0.5rem 0 0 0;
    }
    .internal-divider { margin: 0.6rem 0; }
  }
</style>
