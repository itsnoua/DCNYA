import { state } from '../state.js';
import { ApiService } from './api.js';
import { Utils } from './utils.js';
import { VdUIController } from './vd_ui.js';

export const UIController = {
    updateKPIs(data) {
        document.getElementById('kpi-target').innerText = (data.target || 0).toLocaleString();
        document.getElementById('kpi-total').innerText = (data.total || 0).toLocaleString();
        document.getElementById('kpi-issued').innerText = (data.issued || 0).toLocaleString();
        document.getElementById('kpi-pending').innerText = (data.pending || 0).toLocaleString();
        
        const govEl = document.getElementById('kpi-gov');
        if (govEl) govEl.innerText = (data.gov_count || 0).toLocaleString();
        
        // إظهار بطاقة "شهادات غير صادرة" للمرحلة الأولى والثانية فقط حسب طلب المستخدم
        const pendingCard = document.getElementById('kpi-pending').parentElement;
        const issuedCard = document.getElementById('kpi-issued').parentElement;
        
        if (pendingCard) {
            const isPhase1or2 = (state.currentPhase === 1 || state.currentPhase === 2);
            pendingCard.style.display = isPhase1or2 ? 'block' : 'none';
            
            // إذا كانت البطاقة مخفية (المرحلة 3)، نجعل بطاقة "شهادات صادرة" تأخذ العرض الكامل
            if (issuedCard) {
                if (isPhase1or2) {
                    issuedCard.classList.remove('full-width');
                } else {
                    issuedCard.classList.add('full-width');
                }
            }
        }
        
        const coverage = data.coverage || 0;
        document.getElementById('coverage-percent').innerText = coverage + '%';
        
        const arc = document.getElementById('gauge-arc');
        const statusLabel = document.getElementById('gauge-status');
        if (arc) {
            const circumference = 126; 
            const fillValue = (coverage / 100) * circumference;
            arc.style.strokeDasharray = `${fillValue} ${circumference}`;
            
            if (coverage >= 75) {
                arc.style.stroke = 'var(--color-success)';
                if (statusLabel) { statusLabel.innerText = 'ممتاز'; statusLabel.className = 'gauge-status-label status-excellent'; }
            } else if (coverage >= 40) {
                arc.style.stroke = 'var(--color-warning)';
                if (statusLabel) { statusLabel.innerText = 'متوسط'; statusLabel.className = 'gauge-status-label status-average'; }
            } else {
                arc.style.stroke = 'var(--color-danger)';
                if (statusLabel) { statusLabel.innerText = 'ضعيف'; statusLabel.className = 'gauge-status-label status-weak'; }
            }
        }

        const gap = document.getElementById('kpi-gap-v2');
        if (gap) gap.innerText = (data.spatial_gap || 0).toLocaleString();

        let spatialPercent = data.spatial_match_percent;
        if (spatialPercent === undefined) {
            spatialPercent = data.total > 0 ? Math.round((data.issued / data.total) * 100) : 0;
        }
        spatialPercent = Math.max(0, Math.min(100, spatialPercent)); 

        const spatialFill = document.getElementById('spatial-progress-fill');
        const spatialPercentText = document.getElementById('spatial-match-percent');
        if (spatialFill) spatialFill.style.width = spatialPercent + '%';
        if (spatialPercentText) spatialPercentText.innerText = spatialPercent + '% مطابقة مكانية';
        
        const stats = data.period_stats;
        
        // تحديث مؤشر النمو الأسبوعي في بطاقة الشهادات الصادرة
        const trendEl = document.getElementById('kpi-issued-trend');
        if (trendEl && stats) {
            const currentWeekCount = stats.current_week || 0;
            
            if (currentWeekCount > 0) {
                trendEl.innerText = `${currentWeekCount.toLocaleString()}+ شهادة جديدة هذا الأسبوع`;
                trendEl.className = 'kpi-trend trend-up';
                trendEl.style.display = 'flex';
            } else {
                trendEl.style.display = 'none'; // إخفاء إذا لم يكن هناك جديد
            }
        }

        const summary = document.getElementById('chart-stats-summary');
        if (summary && stats) {
            summary.innerHTML = `<div style="display:flex;gap:16px;font-size:14px;font-weight:700;color:var(--text-secondary)">
                <span>الأسبوع السابق: ${stats.prev_week}</span>
                <span>الأسبوع الحالي: ${stats.current_week}</span>
            </div>`;
        }
    },
    updateChart(data) {
        const ctx = document.getElementById('growthLineChart');
        const container = document.getElementById('growth-chart-container');
        
        if (state.currentPhase === 1 || !data || !data.history || !data.history.labels) { 
            if (container) container.style.display = 'none'; 
            return; 
        }
        
        if (container) container.style.display = 'block';
        if (state.growthChart) state.growthChart.destroy();
        state.growthChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.history.labels,
                datasets: [
                    { 
                        label: 'الحالي', 
                        data: data.history.current, 
                        borderColor: 'var(--color-danger)', 
                        backgroundColor: 'rgba(166, 63, 75, 0.1)',
                        tension: 0.4, 
                        fill: true,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: 'var(--color-danger)'
                    },
                    { 
                        label: 'المستهدف', 
                        data: data.history.previous, 
                        borderColor: '#aaa', 
                        borderDash: [5, 5], 
                        tension: 0.4, 
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 0
                    }
                ]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        rtl: true,
                        labels: {
                            font: { family: 'Quiverleaf Arabic CF', size: 12 }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#EBE1D8' } },
                    x: { grid: { display: false } }
                }
            }
        });
    },

    // Delegate Visual Distortion calls to specialized controller
    updateVdUI(data, classifications) {
        VdUIController.updateVdUI(data, classifications);
    },
    
    renderVdTopMunicipalitiesChart(data) {
        VdUIController.renderVdTopMunicipalitiesChart(data);
    },
    
    renderVdStatusBreakdownChart(data) {
        VdUIController.renderVdStatusBreakdownChart(data);
    },
    
    renderVdMonthlyPerformanceChart(data) {
        VdUIController.renderVdMonthlyPerformanceChart(data);
    }
};
