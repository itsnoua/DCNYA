import { state } from '../state.js';
import { ApiService } from './api.js';
import { Utils } from './utils.js';
import { ALL_RECURRENCES } from './recurrence_data.js';
import { MUN_STATS } from './municipality_data.js';

export const VdUIController = {
    VERSION: "1.3.0_LIVE_KPIS",
    
    updateVdUI(data, classifications) {
        console.log("VD Dashboard Loaded - Version:", this.VERSION, "Filter:", state.selectedMunicipality);
        this._updateSmartInsights(data);
        this._updateVdKPIs(data);
        this._updateClassifications(classifications);
    },

    _updateSmartInsights(data) {
        const container = document.getElementById('vd-smart-insight-summary');
        if (!container) return;
        const mun = state.selectedMunicipality === 'all' ? 'عسير' : state.selectedMunicipality;
        container.innerHTML = `
            <div class="vd-insight-pill pulse">
                <span class="icon">🎯</span>
                <span class="text">نطاق التحليل الحالي: ${mun}</span>
            </div>
        `;
    },

    _updateVdKPIs(data) {
        const targetMun = state.selectedMunicipality;
        const stats = MUN_STATS[targetMun] || MUN_STATS['all'];

        // DYNAMIC KPI UPDATES
        Utils.animateValue('vd-kpi-total', 0, stats.total, 1000);
        Utils.animateValue('vd-kpi-policy', 0, stats.policy, 1000);
        Utils.animateValue('vd-kpi-resource', 0, stats.resource, 1000);

        const slaVal = stats.sla || 57.8;
        const slaEl = document.getElementById('vd-kpi-sla');
        if (slaEl) slaEl.innerText = slaVal + '%';
        const slaProgress = document.getElementById('vd-sla-progress');
        if (slaProgress) slaProgress.style.width = slaVal + '%';

        // Calculate specific counts for the selected municipality
        let filteredRecurrencesCount = 0;
        if (targetMun === 'all') {
            for (const m in ALL_RECURRENCES) {
                for (const cat in ALL_RECURRENCES[m]) {
                    filteredRecurrencesCount += ALL_RECURRENCES[m][cat].reduce((acc, curr) => acc + curr.count, 0);
                }
            }
        } else if (ALL_RECURRENCES[targetMun]) {
            for (const cat in ALL_RECURRENCES[targetMun]) {
                filteredRecurrencesCount += ALL_RECURRENCES[targetMun][cat].reduce((acc, curr) => acc + curr.count, 0);
            }
        }

        const integrityEl = document.getElementById('vd-kpi-integrity');
        if (integrityEl) integrityEl.innerText = '99%';
        
        const fakeDesc = document.getElementById('vd-kpi-fake-desc');
        if (fakeDesc) {
            fakeDesc.innerHTML = `<span style="color:var(--vd-danger); font-weight:700;">${filteredRecurrencesCount.toLocaleString()}</span> تكرار مريب تم رصده`;
        }
        
        // Define matrix structure
        let municipalities = ["خميس مشيط", "نطاق خدمة مدينة أبها", "تثليث", "سراة عبيده", "الثنية و تبالة", "بيشه"];
        const categories = ["عدم دهان الشوارع", "الحواجز الخرسانية", "الأرصفة المتهالكة", "الهناجر المخالفة فوق السطوح", "تسوير المباني تحت الإنشاء", "نظافة الأماكن العامة"];
        
        // Filter municipalities for matrix
        if (targetMun !== 'all' && municipalities.includes(targetMun)) {
            municipalities = [targetMun];
        }

        const matrix = municipalities.map(mun => {
            return categories.map(cat => {
                if (ALL_RECURRENCES[mun] && ALL_RECURRENCES[mun][cat]) {
                    return ALL_RECURRENCES[mun][cat].length;
                }
                return 0;
            });
        });

        this.renderVdHeatmapMatrix({
            municipalities: municipalities,
            classifications: categories,
            matrix: matrix
        });

        this._displayDrillDown(municipalities[0], categories[0], matrix[0][0]);
    },

    _displayDrillDown(mun, cls, total) {
        const list = document.getElementById('vd-worst-locations-list');
        const title = document.getElementById('vd-rankings-title');
        if (!list) return;

        if (title) title.innerText = `المواقع المزمنة: ${mun}`;

        let chronicSpots = [];
        if (ALL_RECURRENCES[mun] && ALL_RECURRENCES[mun][cls]) {
            chronicSpots = ALL_RECURRENCES[mun][cls];
        }

        list.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="background:rgba(166,63,75,0.1); padding:10px; border-radius:8px; border-right:4px solid var(--vd-danger);">
                    <div style="font-weight:700; font-size:14px;">${mun}</div>
                    <div style="font-size:12px; color:var(--vd-text-dim);">${cls}</div>
                </div>
                
                <div style="max-height: 500px; overflow-y: auto; padding-right: 5px;">
                    ${chronicSpots.length > 0 ? chronicSpots.map((spot, idx) => `
                        <div class="vd-ranking-item" style="flex-direction: column; align-items: stretch; margin-bottom: 12px; padding: 12px; background: #fff; border: 1px solid rgba(0,0,0,0.05); border-radius: 10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                                <span style="font-weight:700; color:var(--vd-text-main); font-size:13px;">📍 موقع مزمن #${idx + 1}</span>
                                <span style="background:var(--vd-danger); color:#fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight:900;">${spot.count} بلاغ تراكمي</span>
                            </div>
                            <div style="font-size: 11px; color: var(--vd-text-dim); margin-bottom: 6px;">الأرقام المرتبطة:</div>
                            <div style="display:flex; flex-wrap:wrap; gap:4px;">
                                ${spot.details.slice(0, 5).map(id => `
                                    <span style="font-family:monospace; font-size:10px; background:rgba(0,0,0,0.03); padding:2px 4px; border-radius:3px;">#${id.split('_')[0]}</span>
                                `).join('')}
                                ${spot.details.length > 5 ? `<span style="font-size:10px; color:var(--vd-accent);">+${spot.details.length - 5}</span>` : ''}
                            </div>
                        </div>
                    `).join('') : '<div style="text-align:center; padding:20px; color:var(--vd-text-dim);">لا توجد بلاغات مكررة في هذا النطاق</div>'}
                </div>
            </div>
        `;
    },

    _updateClassifications(classifications) {
        const container = document.getElementById('vd-classifications-list');
        if (!container) return;
        const newData = [
            { name: "عدم دهان الشوارع", count: 197, group: "Service" },
            { name: "تسوير المباني تحت الإنشاء", count: 144, group: "Regulatory & Policy" },
            { name: "الحواجز الخرسانية", count: 131, group: "Regulatory & Policy" },
            { name: "الأرصفة المتهالكة", count: 118, group: "Service" },
            { name: "الهناجر المخالفة فوق السطوح", count: 116, group: "Regulatory & Policy" },
            { name: "نظافة الأماكن العامة", count: 98, group: "Service" }
        ];
        const maxCount = 197;
        container.innerHTML = newData.map(c => {
            const percentage = (c.count / maxCount) * 100;
            const barColor = c.group === 'Regulatory & Policy' ? '#A63F4B' : '#D4AF37';
            return `
                <div class="vd-bar-item" style="margin-bottom: 20px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:13px;">
                        <span style="font-weight:700;">${c.name}</span>
                        <span style="color:${barColor}; font-weight:900;">${c.count.toLocaleString()}</span>
                    </div>
                    <div style="height:10px; background:rgba(0,0,0,0.03); border-radius:10px; overflow:hidden;">
                        <div style="width: ${percentage}%; height:100%; background:${barColor};"></div>
                    </div>
                </div>
            `;
        }).join('');
    },

    renderVdHeatmapMatrix(data) {
        const container = document.getElementById('vd-heatmap-container');
        if (!container || !data) return;
        const maxVal = Math.max(...data.matrix.flat(), 1);
        let html = `<table style="width:100%; border-collapse: separate; border-spacing: 4px; font-size: 11px;">`;
        html += `<thead><tr><th></th>`;
        data.classifications.forEach(cls => {
            html += `<th style="writing-mode: vertical-rl; transform: rotate(180deg); padding: 8px 4px; color: var(--vd-text-dim); font-weight: 500;">${cls}</th>`;
        });
        html += `</tr></thead><tbody>`;
        data.municipalities.forEach((mun, i) => {
            html += `<tr><td style="padding: 4px 8px; font-weight: 700; color: var(--vd-text-main); white-space: nowrap;">${mun}</td>`;
            data.matrix[i].forEach((val, j) => {
                const cls = data.classifications[j];
                const opacity = (val / maxVal);
                const bgColor = val > 0 ? `rgba(166, 63, 75, ${0.1 + opacity * 0.9})` : 'rgba(0,0,0,0.02)';
                const textColor = opacity > 0.5 ? '#fff' : 'var(--vd-text-main)';
                html += `<td class="heatmap-cell" data-mun="${mun}" data-cls="${cls}" data-val="${val}"
                            style="background: ${bgColor}; color: ${textColor}; text-align: center; padding: 12px 4px; border-radius: 4px; font-weight: 700; cursor: pointer; transition: transform 0.2s;" title="${val} بؤرة مزمنة">
                    ${val > 0 ? val : '-'}
                </td>`;
            });
            html += `</tr>`;
        });
        html += `</tbody></table>`;
        container.innerHTML = html;
        container.querySelectorAll('.heatmap-cell').forEach(cell => {
            cell.addEventListener('click', (e) => {
                const mun = e.currentTarget.getAttribute('data-mun');
                const cls = e.currentTarget.getAttribute('data-cls');
                const val = e.currentTarget.getAttribute('data-val');
                container.querySelectorAll('.heatmap-cell').forEach(c => c.style.border = 'none');
                e.currentTarget.style.border = '2px solid #D4AF37';
                this._displayDrillDown(mun, cls, parseInt(val));
            });
        });
    }
};
