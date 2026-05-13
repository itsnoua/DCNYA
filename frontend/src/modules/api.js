import { CONFIG } from '../config.js';
import { STATIC_COMPLIANCE_DATA } from './compliance_data.js';
import { STATIC_POINTS } from './map_data.js';

export const ApiService = {
    async _get(url) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); 

        try {
            const response = await fetch(url, {
                headers: { 'ngrok-skip-browser-warning': 'true' },
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            if (!response.ok) throw new Error("Network error");
            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    },

    async fetchKpis(phase, mun, street) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/kpis?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
        } catch (e) {
            let munKey = mun;
            if (mun !== 'all' && !STATIC_COMPLIANCE_DATA.municipalities[munKey]) {
                munKey = mun.replace('بلدية ', '');
                if (!STATIC_COMPLIANCE_DATA.municipalities[munKey]) munKey = 'بلدية ' + mun;
            }
            const munData = (mun === 'all' || !STATIC_COMPLIANCE_DATA.municipalities[munKey]) 
                ? STATIC_COMPLIANCE_DATA.all 
                : STATIC_COMPLIANCE_DATA.municipalities[munKey];
            
            return {
                target: munData.target,
                total: munData.total,
                issued: munData.issued,
                gov_count: munData.gov,
                pending: munData.pending,
                coverage: munData.match_percent,
                spatial_gap: munData.pending,
                spatial_match_percent: munData.match_percent,
                period_stats: { current_week: 0, prev_week: 0 }
            };
        }
    },

    async fetchPoints(phase, mun, street) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/points?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
        } catch (e) {
            // Fallback to static extracted points
            return STATIC_POINTS.map(p => ({
                id: p.id,
                status: p.status,
                geom_geojson: {
                    type: "Point",
                    coordinates: [p.lng, p.lat]
                }
            }));
        }
    },

    async fetchMunicipalities(phase) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/municipalities?phase_id=${phase}`);
        } catch (e) {
            return Object.keys(STATIC_COMPLIANCE_DATA.municipalities).sort();
        }
    },

    async fetchPhaseMetadata(phase, mun = 'all', street = 'all') {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/phase-metadata?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
        } catch (e) {
            return {
                date_range: "فبراير 2024 - 9/5/2026",
                last_update: "13/5/2026"
            };
        }
    },

    async fetchVdKpis(municipality = 'all') {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/visual_distortion/kpis?municipality=${encodeURIComponent(municipality)}`);
        } catch (e) { return null; }
    },

    async fetchVdMunicipalities() { 
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/visual_distortion/municipalities`);
        } catch(e) {
            return ["خميس مشيط", "نطاق خدمة مدينة أبها", "بيشه", "محايل عسير", "أحد رفيدة", "تثليث", "سراة عبيده", "ظهران الجنوب"];
        }
    },

    async fetchHistory() { 
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/history`);
        } catch(e) { return { history: { labels: [], current: [], previous: [] } }; }
    },

    async fetchBounds(phase, mun, street) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/bounds?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
        } catch(e) { return null; }
    },

    async fetchVdBounds(mun) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/visual_distortion/bounds?municipality=${encodeURIComponent(mun)}`);
        } catch(e) { return null; }
    },

    async fetchRoads(phase, mun, street) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/roads?phase_id=${phase}&municipality=${encodeURIComponent(mun)}&street=${encodeURIComponent(street)}`);
        } catch(e) { return { type: 'FeatureCollection', features: [] }; }
    },

    async fetchPriorityRoads(phase) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/priority-roads?phase_id=${phase}`);
        } catch(e) { return { type: 'FeatureCollection', features: [] }; }
    },

    async fetchStreets(mun, phase) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/compliance/streets?phase_id=${phase}&municipality=${encodeURIComponent(mun)}`);
        } catch(e) { return []; }
    },

    async fetchVdPoints(mun) {
        try {
            return await this._get(`${CONFIG.API_BASE_URL}/visual_distortion/points?municipality=${encodeURIComponent(mun)}`);
        } catch(e) { return []; }
    }
};
