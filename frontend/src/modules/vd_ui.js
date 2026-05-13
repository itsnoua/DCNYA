import { state } from '../state.js';
import { ApiService } from './api.js';
import { Utils } from './utils.js';
import { ALL_RECURRENCES } from './recurrence_data.js';
import { MUN_STATS } from './municipality_data.js';

export const VdUIController = {
    VERSION: "2.0.0_MASTER_EXECUTIVE",
    _pieChart: null,
    
    updateVdUI(data, classifications) {
        console.log("VD Dashboard Loaded - Version:", this.VERSION, "Filter:", state.selectedMunicipality);
        this._updateSmartInsights(data);
        this._updateVdKPIs(data);
        this._renderCausesPieChart();
    },

    _updateSmartInsights(data) {
        const container = document.getElementById('vd-smart-insight-summary');
        if (!container) return;
        const mun = (state.selectedMunicipality === 'all' || !state.selectedMunicipality) ? 'عسير' : state.selectedMunicipality;
        container.innerHTML = `
            <div class="vd-insight-pill pulse">
                <span class="icon">🎯</span>
                <span class="text">نطاق التحليل الاستراتيجي الحالي: ${mun}</span>
            </div>
        `;
    },

    _updateVdKPIs(data) {
        const targetMun = state.selectedMunicipality || 'all';
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
        let municipalities = ["خميس مشيط", "نطاق خدمة مدينة أبها", "بيشه", "محايل عسير", "أحد رفيدة", "تثليث", "سراة عبيده", "ظهران الجنوب"];
        const categories = ["عدم دهان الشوارع", "الحواجز الخرسانية", "الأرصفة المتهالكة", "الهناجر المخالفة فوق السطوح", "تسوير المباني تحت الإنشاء", "نظافة الأماكن العامة"];
        
        // Filter municipalities for matrix
        let activeMuns = municipalities;
        if (targetMun !== 'all' && municipalities.includes(targetMun)) {
            activeMuns = [targetMun];
        }

        const matrix = activeMuns.map(mun => {
            return categories.map(cat => {
                if (ALL_RECURRENCES[mun] && ALL_RECURRENCES[mun][cat]) {
                    return ALL_RECURRENCES[mun][cat].length;
                }
                return 0;
            });
        });

        this.renderVdHeatmapMatrix({
            municipalities: activeMuns,
            classifications: categories,
            matrix: matrix
        });

        this._displayDrillDown(activeMuns[0], categories[0], matrix[0][0]);
    },

    _renderCausesPieChart() {
        const ctx = document.getElementById('vdCausesPieChart');
        if (!ctx) return;

        // Cleanup previous chart
        if (this._pieChart) {
            this._pieChart.destroy();
        }

        const targetMun = state.selectedMunicipality || 'all';
        const stats = MUN_STATS[targetMun] || MUN_STATS['all'];

        this._pieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['التصنيف الرقابي', 'التصنيف الخدمي'],
                datasets: [{
                    data: [stats.policy, stats.resource],
                    backgroundColor: ['#A63F4B', '#D4AF37'],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0',
                            font: { family: 'Outfit', size: 12 },
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const val = context.raw;
                                const perc = ((val / total) * 100).toFixed(1);
                                return ` ${context.label}: ${val.toLocaleString()} (${perc}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    },

    _displayDrillDown(mun, cls, total) {
        const list = document.getElementById('vd-worst-locations-list');
        const title = document.getElementById('vd-rankings-title');
        if (!list) return;

        if (title) title.innerText = `تفاصيل التكرار: ${mun}`;

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
                
                <div style="max-height: 450px; overflow-y: auto; padding-right: 5px;">
                    ${chronicSpots.length > 0 ? chronicSpots.map((spot, idx) => `
                        <div class="vd-ranking-item" style="flex-direction: column; align-items: stretch; margin-bottom: 12px; padding: 12px; background: #fff; border: 1px solid rgba(0,0,0,0.05); border-radius: 10px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                                <span style="font-weight:700; color:var(--vd-text-main); font-size:13px;">📍 #${idx + 1}</span>
                                <span style="background:var(--vd-danger); color:#fff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight:900;">${spot.count} بلاغ تراكمي</span>
                            </div>
                            <div style="display:flex; flex-wrap:wrap; gap:4px;">
                                ${spot.details.slice(0, 3).map(id => `
                                    <span style="font-family:monospace; font-size:10px; background:rgba(0,0,0,0.03); padding:2px 4px; border-radius:3px;">#${id.split('_')[0]}</span>
                                `).join('')}
                                ${spot.details.length > 3 ? `<span style="font-size:10px; color:var(--vd-accent);">+${spot.details.length - 3}</span>` : ''}
                            </div>
                        </div>
                    `).join('') : '<div style="text-align:center; padding:20px; color:var(--vd-text-dim);">لا توجد بؤر تكرار مريبة في هذا النطاق</div>'}
                </div>
            </div>
        `;
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
