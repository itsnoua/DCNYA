import { CONFIG } from '../config.js';

export const ApiService = {
    async _get(url) {
        const response = await fetch(url, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        return await response.json();
    },
    async fetchKpis(phase, mun, street) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/kpis?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
    },
    async fetchHistory(phase, mun) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/kpis/history?phase_id=${phase}&municipality=${encodeURIComponent(mun)}`);
    },
    async fetchPoints(phase, mun, street) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/points?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
    },
    async fetchBounds(phase, mun, street) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/bounds?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
    },
    async fetchRoads(phase, mun, street) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/roads?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
    },
    async fetchPriorityRoads(phase) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/priority-roads?phase_id=${phase}`);
    },
    async fetchMunicipalities(phase) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/municipalities?phase_id=${phase}`);
    },
    async fetchStreets(municipality, phase) {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/streets?municipality=${encodeURIComponent(municipality)}&phase_id=${phase}`);
    },
    async fetchPhaseMetadata(phase, mun = 'all', street = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/compliance/phase-metadata?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
    },
    async fetchViolations(municipality) {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/violations?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchDistortionStats() {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/stats`);
    },
    // --- Visual Distortion API ---
    async fetchVdMunicipalities() {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/municipalities`);
    },
    async fetchVdKpis(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/kpis?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdPoints(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/points?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdClassifications(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/classifications?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdBounds(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/bounds?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdTopMunicipalities() {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/top-municipalities`);
    },
    async fetchVdStatusBreakdown(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/status-breakdown?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdMonthlyPerformance(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/monthly-performance?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdFakeClosuresKpi(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/fake-closures-kpi?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdWorstFakeClosures(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/worst-fake-closures?municipality=${encodeURIComponent(municipality)}`);
    },
    async fetchVdFakeClosuresDrilldown(municipality, classification) {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/worst-fake-closures/drilldown?municipality=${encodeURIComponent(municipality)}&classification=${encodeURIComponent(classification)}`);
    },
    async fetchVdGridStats() {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/grid-stats`);
    },
    async fetchVdDashboardSummary(municipality = 'all') {
        return this._get(`${CONFIG.API_BASE_URL}/visual_distortion/dashboard-summary?municipality=${encodeURIComponent(municipality)}`);
    }
};
