/**
 * API Client for Kouei Backend
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor(baseUrl = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API Error: ${endpoint}`, error);
      throw error;
    }
  }

  // Status & System
  async getStatus() {
    return this.request('/api/status');
  }

  async getConfig() {
    return this.request('/api/config');
  }

  async updateConfig(config) {
    return this.request('/api/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Races
  async getStadiums() {
    return this.request('/api/stadiums');
  }

  async getRaces(date, jyo) {
    return this.request(`/api/races?date=${date}&jyo=${jyo}`);
  }

  async getTodayRaces() {
    return this.request('/api/today');
  }

  // Predictions
  async getPrediction(date, jyo, race) {
    return this.request(`/api/prediction?date=${date}&jyo=${jyo}&race=${race}`);
  }

  async simulateWhatIf(modifications) {
    return this.request('/api/simulate-what-if', {
      method: 'POST',
      body: JSON.stringify({ modifications }),
    });
  }

  async getSimilarRaces(jyoCd, wind, wave, temp = 20, waterTemp = 18) {
    return this.request(
      `/api/similar-races?jyo_cd=${jyoCd}&wind=${wind}&wave=${wave}&temp=${temp}&water_temp=${waterTemp}`
    );
  }

  // Betting
  async getOdds(date, jyo, race) {
    return this.request(`/api/odds?date=${date}&jyo=${jyo}&race=${race}`);
  }

  async optimizeBetting(params) {
    return this.request('/api/betting/optimize', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  async optimizeFormation(date, jyo, race, budget = 10000, formationType = 'box') {
    return this.request(
      `/api/betting/formation?date=${date}&jyo=${jyo}&race=${race}&budget=${budget}&formation_type=${formationType}`,
      { method: 'POST' }
    );
  }

  // Portfolio & Simulation
  async getPortfolio() {
    return this.request('/api/portfolio');
  }

  async getSimulation(threshold = 0.4) {
    return this.request(`/api/simulation?threshold=${threshold}`);
  }

  async runBacktest(filters) {
    return this.request('/api/backtest', {
      method: 'POST',
      body: JSON.stringify(filters),
    });
  }

  async runMonteCarlo(strategyName, nSimulations = 1000) {
    return this.request(`/api/monte-carlo/${strategyName}?n_simulations=${nSimulations}`);
  }

  // Strategies
  async getStrategies() {
    return this.request('/api/strategies');
  }

  async discoverStrategies() {
    return this.request('/api/strategy/discover', { method: 'POST' });
  }

  // Analysis
  async getRacerStats(racerId, nRaces = 10) {
    return this.request(`/api/racer/${racerId}?n_races=${nRaces}`);
  }

  async getCompatibility(racerId, motorNo, stadium, course) {
    return this.request(
      `/api/compatibility?racer_id=${racerId}&motor_no=${motorNo}&stadium=${stadium}&course=${course}`
    );
  }

  async getStadiumMatrix(stadium) {
    return this.request(`/api/stadium-matrix/${stadium}`);
  }

  async getSimilarRacers(racerId, topK = 5) {
    return this.request(`/api/similar-racers/${racerId}?top_k=${topK}`);
  }

  async chat(query, context = null) {
    return this.request('/api/concierge/chat', {
      method: 'POST',
      body: JSON.stringify({ query, context }),
    });
  }

  // Sync
  async sync() {
    return this.request('/api/sync');
  }

  async fetchData(date) {
    return this.request(`/api/fetch?date=${date}`, { method: 'POST' });
  }

  async triggerOptimization(trials = 50) {
    return this.request(`/api/optimize?trials=${trials}`, { method: 'POST' });
  }

  async triggerRetraining() {
    return this.request('/api/mlops/retrain', { method: 'POST' });
  }

  async checkDrift() {
    return this.request('/api/drift-check');
  }
}

// Singleton instance
export const api = new ApiClient();
export default api;
