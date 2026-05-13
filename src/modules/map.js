import { CONFIG } from '../config.js';
import { state } from '../state.js';
import { ApiService } from './api.js';

export let map;

export function initMap() {
    console.log("Initializing map at center:", CONFIG.MAP_CENTER);
    map = new maplibregl.Map({
        container: 'map',
        style: {
            'version': 8,
            'glyphs': 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
            'sources': {
                'google-satellite': {
                    'type': 'raster',
                    'tiles': ['https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'],
                    'tileSize': 256
                }
            },
            'layers': [
                {
                    'id': 'background',
                    'type': 'background',
                    'paint': { 'background-color': '#0B0F19' }
                },
                { 
                    'id': 'google-satellite-layer', 
                    'type': 'raster', 
                    'source': 'google-satellite',
                    'paint': {
                        'raster-opacity': 0.6
                    }
                }
            ]
        },
        center: CONFIG.MAP_CENTER,
        zoom: CONFIG.MAP_ZOOM,
        pitch: 55,
        bearing: -15,
        antialias: true,
        transformRequest: (url) => {
            if (url.includes('ngrok-free.dev')) {
                return {
                    url: url,
                    headers: { 'ngrok-skip-browser-warning': 'true' }
                };
            }
            return { url: url };
        }
    });

    map.on('error', (e) => console.error("Map error:", e));
    map.on('load', () => console.log("Map style loaded successfully"));

    return map;
}

export function addMapLayers(phaseId) {
    if (!map) return;

    // 1. طبقات الامتثال
    console.log(`Adding map layers for phase ${phaseId}...`);
    const buildingsTilesUrl = `${CONFIG.API_BASE_URL}/compliance/buildings/tiles/{z}/{x}/{y}?phase_id=${phaseId}&v=${Date.now()}`;
    console.log(`Buildings Tiles URL: ${buildingsTilesUrl}`);
    
    if (!map.getSource('buildings')) {
        map.addSource('buildings', {
            type: 'vector',
            tiles: [buildingsTilesUrl],
            minzoom: 6, maxzoom: 19
        });
    } else {
        map.getSource('buildings').setTiles([buildingsTilesUrl]);
    }

    if (!map.getLayer('buildings-3d')) {
        console.log("Creating buildings-3d layer...");
        map.addLayer({
            'id': 'buildings-3d', 
            'type': 'fill-extrusion', 
            'source': 'buildings', 
            'source-layer': 'buildings',
            'paint': {
                'fill-extrusion-color': ['match', ['get', 'compliance_status'], 
                    'ممتثل', CONFIG.PALETTE.compliant, 
                    'ممتثل (تقريبي)', CONFIG.PALETTE.compliantBuffer, 
                    'غير ممتثل', CONFIG.PALETTE.nonCompliant, 
                    CONFIG.PALETTE.default
                ],
                'fill-extrusion-height': 15,
                'fill-extrusion-base': 0,
                'fill-extrusion-opacity': 0.8
            }
        });
    } else {
        console.log("buildings-3d layer already exists.");
    }

    if (!map.getSource('compliance-points')) {
        map.addSource('compliance-points', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        
        // 1. Original Compliance Points Layer (Circles)
        map.addLayer({ 
            'id': 'compliance-points-layer', 
            'type': 'circle', 
            'source': 'compliance-points', 
            'filter': ['!=', ['get', 'is_special'], true], // Show everything EXCEPT special points
            'paint': { 
                'circle-radius': 5, 
                'circle-color': '#D4AF37',
                'circle-opacity': 0.8,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff',
                'circle-stroke-opacity': 0.5
            } 
        });

        // 2. Special Points Layer (Red Pins with Circle Fallback)
        map.loadImage('https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png', (error, image) => {
            if (error) {
                console.error("Error loading red pin icon, using circle fallback:", error);
                // Fallback: Show as red circles if icon fails
                map.addLayer({ 
                    'id': 'special-points-layer', 
                    'type': 'circle', 
                    'source': 'compliance-points', 
                    'filter': ['==', ['get', 'is_special'], true],
                    'paint': { 
                        'circle-radius': 8, 
                        'circle-color': '#ff0000',
                        'circle-stroke-width': 3,
                        'circle-stroke-color': '#ffffff'
                    } 
                });
                return;
            }
            if (!map.hasImage('red-pin')) map.addImage('red-pin', image);
            
            map.addLayer({ 
                'id': 'special-points-layer', 
                'type': 'symbol', 
                'source': 'compliance-points', 
                'filter': ['==', ['get', 'is_special'], true],
                'layout': {
                    'icon-image': 'red-pin',
                    'icon-size': 1.0, // This icon is smaller, so size 1.0 is better
                    'icon-allow-overlap': true,
                    'icon-anchor': 'bottom'
                }
            });
        });
    }

    if (!map.getSource('selected-road')) {
        map.addSource('selected-road', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({ 'id': 'road-layer', 'type': 'line', 'source': 'selected-road', 'paint': { 'line-color': '#D4AF37', 'line-width': 6, 'line-opacity': 0.8 } });
    }

    // 1.5. Priority Roads Layer (Requested by USER)
    if (!map.getSource('priority-roads')) {
        map.addSource('priority-roads', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            'id': 'priority-roads-layer',
            'type': 'line',
            'source': 'priority-roads',
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': [
                    'match',
                    ['get', 'name'],
                    'طريق المطار', '#FF3D00',
                    'طريق الملك فهد', '#00E676',
                    'طريق الملك خالد', '#2979FF',
                    'طريق الملك عبدالله', '#FFEA00',
                    'طريق الأمير سلطان', '#D500F9',
                    'طريق ابها الخميس', '#00B0FF',
                    'ابها-الخميس', '#00B0FF',
                    'طريق الحزام', '#F44336',
                    'شارع الفن', '#E91E63',
                    'طريق الفن', '#E91E63',
                    'طريق المحالة', '#4CAF50',
                    'جامعة الملك خالد', '#9C27B0',
                    '#00F3FF' // Default Cyan
                ],
                'line-width': ['interpolate', ['linear'], ['zoom'], 10, 3, 15, 10],
                'line-opacity': 0.9,
                'line-blur': 0.5
            }
        });

        // Add a secondary glow layer for premium look
        map.addLayer({
            'id': 'priority-roads-glow',
            'type': 'line',
            'source': 'priority-roads',
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': [
                    'match',
                    ['get', 'name'],
                    'طريق المطار', '#FF3D00',
                    'طريق الملك فهد', '#00E676',
                    'طريق الملك خالد', '#2979FF',
                    'طريق الملك عبدالله', '#FFEA00',
                    'طريق الأمير سلطان', '#D500F9',
                    'طريق ابها الخميس', '#00B0FF',
                    'ابها-الخميس', '#00B0FF',
                    'طريق الحزام', '#F44336',
                    'شارع الفن', '#E91E63',
                    'طريق الفن', '#E91E63',
                    'طريق المحالة', '#4CAF50',
                    'جامعة الملك خالد', '#9C27B0',
                    '#00F3FF'
                ],
                'line-width': ['interpolate', ['linear'], ['zoom'], 10, 6, 15, 20],
                'line-opacity': 0.4,
                'line-blur': 5
            }
        }, 'priority-roads-layer');
    }

    // 2. طبقات التشوه البصري
    if (!map.getSource('vd-points')) {
        map.addSource('vd-points', { 
            type: 'geojson', 
            data: { type: 'FeatureCollection', features: [] },
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 50
        });

        map.addLayer({
            id: 'vd-clusters',
            type: 'circle',
            source: 'vd-points',
            filter: ['has', 'point_count'],
            paint: {
                'circle-color': ['step', ['get', 'point_count'], '#D4AF37', 100, '#F59E0B', 750, '#E11D48'],
                'circle-radius': ['step', ['get', 'point_count'], 20, 100, 30, 750, 40],
                'circle-stroke-width': 2,
                'circle-stroke-color': '#fff'
            }
        });

        map.addLayer({
            id: 'vd-cluster-count',
            type: 'symbol',
            source: 'vd-points',
            filter: ['has', 'point_count'],
            layout: {
                'text-field': '{point_count_abbreviated}',
                'text-font': ['Open Sans Regular'],
                'text-size': 14
            },
            paint: { 'text-color': '#ffffff' }
        });

        map.addLayer({
            id: 'vd-points-layer',
            type: 'circle',
            source: 'vd-points',
            filter: ['!', ['has', 'point_count']],
            paint: {
                'circle-radius': 6,
                'circle-color': ['match', ['get', 'status'], 'مغلق', '#059669', '#E11D48'],
                'circle-opacity': 0.9,
                'circle-stroke-width': 1,
                'circle-stroke-color': '#fff'
            }
        });

        map.addLayer({
            id: 'vd-heatmap',
            type: 'heatmap',
            source: 'vd-points',
            maxzoom: 15,
            paint: {
                'heatmap-weight': 1,
                'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 15, 3],
                'heatmap-color': [
                    'interpolate', ['linear'], ['heatmap-density'],
                    0, 'rgba(212, 175, 55, 0)',
                    0.2, 'rgba(212, 175, 55, 0.4)',
                    0.4, 'rgba(245, 158, 11, 0.6)',
                    0.6, 'rgba(225, 29, 72, 0.7)',
                    1, '#E11D48'
                ],
                'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 5, 15, 30],
                'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 14, 0.8, 15, 0]
            }
        }, 'vd-clusters');

        map.on('click', 'vd-clusters', (e) => {
            const features = map.queryRenderedFeatures(e.point, { layers: ['vd-clusters'] });
            const clusterId = features[0].properties.cluster_id;
            map.getSource('vd-points').getClusterExpansionZoom(clusterId, (err, zoom) => {
                if (err) return;
                map.easeTo({ center: features[0].geometry.coordinates, zoom: zoom });
            });
        });

        map.on('mouseenter', 'vd-clusters', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'vd-clusters', () => { map.getCanvas().style.cursor = ''; });
    }
}

export async function loadPriorityRoads(phaseId) {
    if (!map) return;
    try {
        const data = await ApiService.fetchPriorityRoads(phaseId);
        if (map.getSource('priority-roads')) {
            map.getSource('priority-roads').setData(data);
            console.log(`Loaded ${data.features.length} priority roads`);
        }
        
        // Show for Phase 3 (Humanization) OR when in Visual Distortion department
        const visibility = (state.currentDept === 'visual_distortion' || phaseId === 3) ? 'visible' : 'none';
        if (map.getLayer('priority-roads-layer')) map.setLayoutProperty('priority-roads-layer', 'visibility', visibility);
        if (map.getLayer('priority-roads-glow')) map.setLayoutProperty('priority-roads-glow', 'visibility', visibility);
        
    } catch (err) {
        console.error("Error loading priority roads:", err);
    }
}

export function toggleLayers(dept) {
    if (!map) return;
    const complianceLayers = ['compliance-points-layer', 'special-points-layer', 'road-layer'];
    const vdLayers = ['vd-points-layer', 'vd-clusters', 'vd-cluster-count', 'vd-heatmap'];

    if (dept === 'compliance') {
        complianceLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'visible'); });
        vdLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'none'); });
        
        // Manage priority roads based on phase
        const priorityVis = (state.currentPhase === 3) ? 'visible' : 'none';
        if (map.getLayer('priority-roads-layer')) map.setLayoutProperty('priority-roads-layer', 'visibility', priorityVis);
        if (map.getLayer('priority-roads-glow')) map.setLayoutProperty('priority-roads-glow', 'visibility', priorityVis);

        // Hide 3D buildings in Phase 3 (Humanization) to focus on roads, show in other phases
        if (map.getLayer('buildings-3d')) map.setLayoutProperty('buildings-3d', 'visibility', (state.currentPhase === 3) ? 'none' : 'visible');
    } else {
        complianceLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'none'); });
        
        // Show priority roads in VD mode OR Compliance Phase 3 (Humanization)
        if (map.getLayer('priority-roads-layer')) map.setLayoutProperty('priority-roads-layer', 'visibility', (state.currentDept === 'visual_distortion' || state.currentPhase === 3) ? 'visible' : 'none');
        if (map.getLayer('priority-roads-glow')) map.setLayoutProperty('priority-roads-glow', 'visibility', (state.currentDept === 'visual_distortion' || state.currentPhase === 3) ? 'visible' : 'none');

        // Hide 3D buildings in VD mode OR Compliance Phase 3 to avoid confusion and focus on roads
        if (map.getLayer('buildings-3d')) map.setLayoutProperty('buildings-3d', 'visibility', (state.currentDept === 'visual_distortion' || state.currentPhase === 3) ? 'none' : 'visible');
        
        setVdMapView('heatmap');
    }
}

export function setVdMapView(viewType) {
    if (!map) return;
    if (viewType === 'heatmap') {
        if (map.getLayer('vd-heatmap')) map.setLayoutProperty('vd-heatmap', 'visibility', 'visible');
        if (map.getLayer('vd-clusters')) map.setLayoutProperty('vd-clusters', 'visibility', 'none');
        if (map.getLayer('vd-cluster-count')) map.setLayoutProperty('vd-cluster-count', 'visibility', 'none');
        if (map.getLayer('vd-points-layer')) map.setLayoutProperty('vd-points-layer', 'visibility', 'none');
    } else {
        if (map.getLayer('vd-heatmap')) map.setLayoutProperty('vd-heatmap', 'visibility', 'none');
        if (map.getLayer('vd-clusters')) map.setLayoutProperty('vd-clusters', 'visibility', 'visible');
        if (map.getLayer('vd-cluster-count')) map.setLayoutProperty('vd-cluster-count', 'visibility', 'visible');
        if (map.getLayer('vd-points-layer')) map.setLayoutProperty('vd-points-layer', 'visibility', 'visible');
    }
}

