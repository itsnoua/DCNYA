import { CONFIG } from './config.js';
import { state } from './state.js';
import { ApiService } from './modules/api.js';
import { UIController } from './modules/ui.js';
import { initMap, addMapLayers, map, toggleLayers, setVdMapView, loadPriorityRoads } from './modules/map.js';

async function updatePhaseInfo(phaseId) {
    const dateEl  = document.getElementById('display-phase-date');
    const updateEl = document.getElementById('display-phase-update');

    // Hardcoded as requested by the user to ensure consistency across all filters
    if (dateEl)   dateEl.innerText  = 'فبراير 2024 - 9/5/2026';
    if (updateEl) updateEl.innerText = '13/5/2026';
}

const DashboardManager = {
    async refreshData() {
        console.log(`Refreshing data for department: ${state.currentDept}...`);
        if (!state.isMapLayersLoaded) {
            console.warn("Refresh cancelled: Map layers not loaded yet.");
            return;
        }
        try {
            if (state.currentDept === 'compliance') {
                console.log("Fetching Compliance data...");
                const historyPromise = state.currentPhase === 1 
                    ? Promise.resolve({}) 
                    : ApiService.fetchHistory(state.currentPhase, state.selectedMunicipality);

                const roadPromise = state.selectedStreet !== 'all' 
                    ? ApiService.fetchRoads(state.currentPhase, state.selectedMunicipality, state.selectedStreet)
                    : Promise.resolve({ type: 'FeatureCollection', features: [] });

                const [kpis, points, history, roadGeo] = await Promise.all([
                    ApiService.fetchKpis(state.currentPhase, state.selectedMunicipality, state.selectedStreet),
                    ApiService.fetchPoints(state.currentPhase, state.selectedMunicipality, state.selectedStreet),
                    historyPromise,
                    roadPromise
                ]);
                console.log("Compliance data received:", { kpis, pointsCount: points.length });
                
                UIController.updateKPIs(kpis);
                UIController.updateChart(history);
                if (map.getSource('compliance-points')) {
                    let specialCount = 0;
                    const geojson = { 
                        type: 'FeatureCollection', 
                        features: points.map(p => {
                            let geom = p.geom_geojson;
                            if (typeof geom === 'string') {
                                try { geom = JSON.parse(geom); } catch(e) { return null; }
                            }
                            
                            const coords = geom.coordinates;
                            // Check if this point matches any in our special list (using 0.001 tolerance ~100m)
                            const isSpecial = CONFIG.SPECIAL_COORDS.some(c => 
                                Math.abs(coords[0] - c.x) < 0.001 && 
                                Math.abs(coords[1] - c.y) < 0.001
                            );
                            
                            if (isSpecial) {
                                specialCount++;
                                console.log(`MATCH FOUND: Point ${p.id} at [${coords[0]}, ${coords[1]}] matched a special coordinate.`);
                            }
                            
                            return { 
                                type: 'Feature', 
                                geometry: geom, 
                                properties: { ...p, is_special: isSpecial } 
                            };
                        }).filter(f => f !== null)
                    };
                    console.log(`Compliance data mapped: ${geojson.features.length} total points, ${specialCount} special points found.`);
                    kpis.gov_count = specialCount;
                    UIController.updateKPIs(kpis);
                    map.getSource('compliance-points').setData(geojson);
                }
                if (map.getSource('selected-road')) {
                    map.getSource('selected-road').setData(roadGeo || { type: 'FeatureCollection', features: [] });
                }
            } else {
                console.log("Loading Visual Distortion Dashboard (Fast Mode)...");
                
                // تحديث الواجهة فوراً بالبيانات التي استخرجناها من الملف لضمان السرعة
                UIController.updateVdUI({}, []); 
                
                // تحميل النقاط على الخريطة في النهاية لأنها الأثقل
                ApiService.fetchVdPoints(state.selectedMunicipality).then(points => {
                    if (map.getSource('vd-points')) {
                        const geojson = { 
                            type: 'FeatureCollection', 
                            features: points.map(p => {
                                let geom = p.geom_geojson;
                                if (typeof geom === 'string') {
                                    try { geom = JSON.parse(geom); } catch(e) { return null; }
                                }
                                return { 
                                    type: 'Feature', 
                                    geometry: geom, 
                                    properties: { status: p.status, classification: p.classification, group: p.group } 
                                };
                            }).filter(f => f && f.geometry)
                        };
                        map.getSource('vd-points').setData(geojson);
                    }
                });
            }
            console.log("Dashboard refresh successful.");
        } catch (e) { 
            console.error('Dashboard Refresh Error:', e); 
        }
    },
    async focusOnSelection() {
        try {
            if (state.selectedMunicipality === 'all') {
                map.flyTo({ 
                    center: CONFIG.MAP_CENTER, 
                    zoom: CONFIG.MAP_ZOOM, 
                    pitch: 55, 
                    bearing: -15, 
                    duration: 2000 
                });
                return;
            }

            // في الامتثال نستخدم API خاص بالحدود، في التشوه البصري نستخدم API الخاص به
            if (state.currentDept === 'compliance') {
                const data = await ApiService.fetchBounds(state.currentPhase, state.selectedMunicipality, state.selectedStreet);
                if (data && data.bounds) {
                    map.fitBounds(data.bounds, { padding: 150, duration: 2000, pitch: 55 });
                }
            } else {
                const data = await ApiService.fetchVdBounds(state.selectedMunicipality);
                if (data) {
                    map.fitBounds(data, { padding: 150, duration: 2000, pitch: 55 });
                }
            }
        } catch (e) { console.error('Error focusing:', e); }
    }
};

function setupEventListeners() {
    // مبدل الإدارات
    document.querySelectorAll('.dept-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const dept = e.currentTarget.getAttribute('data-dept');
            if (dept === state.currentDept) return;
            
            document.querySelectorAll('.dept-btn').forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            
            state.currentDept = dept;
            state.selectedMunicipality = state.selectedStreet = 'all';
            
            // التبديل بين وضع "الامتثال" ووضع "لوحة القيادة التنفيذية"
            const body = document.body;
            const mapEl = document.getElementById('map');
            
            if (dept === 'visual_distortion') {
                body.classList.add('executive-mode');
                document.getElementById('compliance-content').style.display = 'none';
                document.getElementById('compliance-map-container').style.display = 'none';
                
                document.getElementById('vd-sidebar-content').style.display = 'block';
                document.getElementById('visual-distortion-dashboard').style.display = 'flex';
                
                // نقل الخريطة إلى لوحة القيادة
                // document.getElementById('map-placeholder').appendChild(mapEl);
                
                loadVdMunicipalities();
                // Force UI update
                setTimeout(() => {
                    UIController.updateVdUI({}, []);
                }, 500);
            } else {
                body.classList.remove('executive-mode');
                document.getElementById('vd-sidebar-content').style.display = 'none';
                document.getElementById('visual-distortion-dashboard').style.display = 'none';
                
                document.getElementById('compliance-content').style.display = 'block';
                document.getElementById('compliance-map-container').style.display = 'block';
                
                // إعادة الخريطة لوضعها الطبيعي
                document.getElementById('compliance-map-container').appendChild(mapEl);
                
                loadComplianceMunicipalities();
            }
            
            // تنبيه الخريطة بتغيير الحجم وإعادة ضبط الأبعاد
            setTimeout(() => {
                map.resize();
                console.log("Map resized after dept switch to", dept);
                // إذا كنا في وضع الامتثال، نتأكد أن الخريطة تأخذ الارتفاع الكامل
                if (dept === 'compliance') {
                    map.getContainer().style.height = '100%';
                    map.getContainer().style.width = '100%';
                } else {
                    // في وضع التشوه البصري، نتأكد أنها تأخذ كامل مساحة Placeholder
                    map.getContainer().style.height = '100%';
                    map.getContainer().style.width = '100%';
                    map.getContainer().style.margin = '0'; // إزالة الهوامش لتملأ الـ Placeholder
                }
            }, 100);

            toggleLayers(dept);
            DashboardManager.refreshData();
            DashboardManager.focusOnSelection();
        });
    });

    document.getElementById('municipality-select')?.addEventListener('change', async (e) => {
        state.selectedMunicipality = e.target.value;
        state.selectedStreet = 'all';
        await updateStreets(state.selectedMunicipality, state.currentPhase);
        DashboardManager.refreshData();
        DashboardManager.focusOnSelection();
        updatePhaseInfo(state.currentPhase);
    });

    document.getElementById('street-select')?.addEventListener('change', (e) => {
        state.selectedStreet = e.target.value;
        DashboardManager.refreshData();
        DashboardManager.focusOnSelection();
        updatePhaseInfo(state.currentPhase);
    });

    document.getElementById('vd-municipality-select')?.addEventListener('change', (e) => {
        state.selectedMunicipality = e.target.value;
        DashboardManager.refreshData();
        DashboardManager.focusOnSelection();
    });

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', async (e) => {
            const phase = parseInt(e.currentTarget.getAttribute('data-phase'));
            if (phase === state.currentPhase) return;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            e.currentTarget.classList.add('active');
            state.currentPhase = phase;
            state.selectedMunicipality = state.selectedStreet = 'all';
            
            // إعادة تحميل البلديات بناءً على المرحلة المختارة (مهم لشوارع الأنسنة)
            await loadComplianceMunicipalities();
            await updateStreets('all', phase);

            addMapLayers(phase);
            loadPriorityRoads(phase);
            updatePhaseInfo(phase);
            DashboardManager.refreshData();
            DashboardManager.focusOnSelection();
        });
    });

    // مبدل وضع الخريطة في التشوه البصري
    document.getElementById('vd-map-heatmap')?.addEventListener('click', (e) => {
        setVdMapView('heatmap');
        document.getElementById('vd-map-heatmap').classList.add('active');
        document.getElementById('vd-map-clusters').classList.remove('active');
    });

    document.getElementById('vd-map-clusters')?.addEventListener('click', (e) => {
        setVdMapView('clusters');
        document.getElementById('vd-map-clusters').classList.add('active');
        document.getElementById('vd-map-heatmap').classList.remove('active');
    });
}

async function updateStreets(municipality, phase) {
    const select = document.getElementById('street-select');
    if (!select) return;
    select.innerHTML = '<option value="all">الكل</option>';
    if (municipality === 'all' && phase !== 3) return; 

    try {
        const streets = await ApiService.fetchStreets(municipality, phase);
        streets.forEach(s => {
            const opt = document.createElement('option');
            opt.value = opt.textContent = s;
            select.appendChild(opt);
        });
    } catch (e) { console.error('Error fetching streets:', e); }
}

async function loadComplianceMunicipalities() {
    try {
        const muns = await ApiService.fetchMunicipalities(state.currentPhase);
        const select = document.getElementById('municipality-select');
        if (select) {
            select.innerHTML = '<option value="all">الكل</option>';
            muns.forEach(m => select.innerHTML += `<option value="${m}">${m}</option>`);
        }
    } catch (e) { console.error('Error loading compliance municipalities:', e); }
}

async function loadVdMunicipalities() {
    try {
        const muns = await ApiService.fetchVdMunicipalities();
        const select = document.getElementById('vd-municipality-select');
        if (select) {
            select.innerHTML = '<option value="all">الكل</option>';
            muns.forEach(m => select.innerHTML += `<option value="${m}">${m}</option>`);
        }
    } catch (e) { console.error('Error loading vd municipalities:', e); }
}

async function init() {
    console.log("Starting Dashboard Initialization...");
    try {
        const mapInstance = initMap();
        setupEventListeners();

        mapInstance.on('load', () => {
            console.log("Map instance loaded, adding layers...");
            try {
                addMapLayers(state.currentPhase);
                loadPriorityRoads(state.currentPhase);
                toggleLayers(state.currentDept);
                state.isMapLayersLoaded = true;
                console.log("Map layers ready.");
                document.dispatchEvent(new Event('mapLayersReady'));
            } catch (layerErr) {
                console.error("Error adding map layers:", layerErr);
            }
        });

        console.log("Loading initial municipalities...");
        await loadComplianceMunicipalities();
        updatePhaseInfo(state.currentPhase);

        if (state.isMapLayersLoaded) {
            console.log("Map already loaded, refreshing data...");
            DashboardManager.refreshData();
        } else {
            console.log("Waiting for map layers to be ready...");
            document.addEventListener('mapLayersReady', () => {
                console.log("Map layers ready event received, refreshing data...");
                DashboardManager.refreshData();
            }, { once: true });
        }
        
        console.log("Initialization complete.");
    } catch (e) {
        console.error("CRITICAL: Dashboard Initialization Failed:", e);
    }
}

// Make DashboardManager accessible for debugging
window.DashboardManager = DashboardManager;

init();

