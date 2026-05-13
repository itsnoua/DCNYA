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

    // 1. Compliance Layers
    console.log(`Adding map layers for phase ${phaseId}...`);
    const buildingsTilesUrl = `${CONFIG.API_BASE_URL}/compliance/buildings/tiles/{z}/{x}/{y}?phase_id=${phaseId}&v=${Date.now()}`;
    
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
    }

    if (!map.getSource('compliance-points')) {
        map.addSource('compliance-points', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        
        // 1. Normal Buildings (Yellow)
        map.addLayer({ 
            'id': 'compliance-points-layer', 
            'type': 'circle', 
            'source': 'compliance-points', 
            'filter': ['!=', ['get', 'is_special'], true],
            'paint': { 
                'circle-radius': 4, 
                'circle-color': '#D4AF37', // Yellow/Gold
                'circle-opacity': 0.8,
                'circle-stroke-width': 1,
                'circle-stroke-color': '#ffffff'
            } 
        });

        // 2. Governmental Buildings (Red - Special)
        map.addLayer({ 
            'id': 'special-points-layer', 
            'type': 'circle', 
            'source': 'compliance-points', 
            'filter': ['==', ['get', 'is_special'], true],
            'paint': { 
                'circle-radius': 10, 
                'circle-color': '#E11D48', // Red
                'circle-stroke-width': 3,
                'circle-stroke-color': '#ffffff',
                'circle-stroke-opacity': 1.0,
                'circle-blur': 0.1
            } 
        });
    }

    if (!map.getSource('selected-road')) {
        map.addSource('selected-road', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({ 'id': 'road-layer', 'type': 'line', 'source': 'selected-road', 'paint': { 'line-color': '#D4AF37', 'line-width': 6, 'line-opacity': 0.8 } });
    }

    if (!map.getSource('priority-roads')) {
        map.addSource('priority-roads', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
        map.addLayer({
            'id': 'priority-roads-layer',
            'type': 'line',
            'source': 'priority-roads',
            'layout': { 'line-join': 'round', 'line-cap': 'round' },
            'paint': {
                'line-color': [
                    'match', ['get', 'name'],
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
                'line-width': ['interpolate', ['linear'], ['zoom'], 10, 3, 15, 10],
                'line-opacity': 0.9
            }
        });
    }

    if (!map.getSource('vd-points')) {
        map.addSource('vd-points', { 
            type: 'geojson', 
            data: { type: 'FeatureCollection', features: [] },
            cluster: true, clusterMaxZoom: 14, clusterRadius: 50
        });

        map.addLayer({
            id: 'vd-clusters', type: 'circle', source: 'vd-points',
            filter: ['has', 'point_count'],
            paint: {
                'circle-color': ['step', ['get', 'point_count'], '#D4AF37', 100, '#F59E0B', 750, '#E11D48'],
                'circle-radius': ['step', ['get', 'point_count'], 20, 100, 30, 750, 40],
                'circle-stroke-width': 2, 'circle-stroke-color': '#fff'
            }
        });

        map.addLayer({
            id: 'vd-cluster-count', type: 'symbol', source: 'vd-points',
            filter: ['has', 'point_count'],
            layout: { 'text-field': '{point_count_abbreviated}', 'text-size': 14 },
            paint: { 'text-color': '#ffffff' }
        });

        map.addLayer({
            id: 'vd-points-layer', type: 'circle', source: 'vd-points',
            filter: ['!', ['has', 'point_count']],
            paint: {
                'circle-radius': 6,
                'circle-color': ['match', ['get', 'status'], 'مغلق', '#059669', '#E11D48'],
                'circle-opacity': 0.9, 'circle-stroke-width': 1, 'circle-stroke-color': '#fff'
            }
        });

        map.addLayer({
            id: 'vd-heatmap', type: 'heatmap', source: 'vd-points',
            maxzoom: 15,
            paint: {
                'heatmap-weight': 1,
                'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 15, 3],
                'heatmap-color': [
                    'interpolate', ['linear'], ['heatmap-density'],
                    0, 'rgba(212, 175, 55, 0)',
                    0.2, 'rgba(212, 175, 55, 0.4)',
                    1, '#E11D48'
                ],
                'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 5, 15, 30]
            }
        }, 'vd-clusters');
    }
}

export async function loadPriorityRoads(phaseId) {
    if (!map) return;
    try {
        const data = await ApiService.fetchPriorityRoads(phaseId);
        if (map.getSource('priority-roads')) map.getSource('priority-roads').setData(data);
        const visibility = (state.currentDept === 'visual_distortion' || phaseId === 3) ? 'visible' : 'none';
        if (map.getLayer('priority-roads-layer')) map.setLayoutProperty('priority-roads-layer', 'visibility', visibility);
    } catch (err) { console.error("Error loading priority roads:", err); }
}

export function toggleLayers(dept) {
    if (!map) return;
    const complianceLayers = ['compliance-points-layer', 'special-points-layer', 'road-layer'];
    const vdLayers = ['vd-points-layer', 'vd-clusters', 'vd-cluster-count', 'vd-heatmap'];

    if (dept === 'compliance') {
        complianceLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'visible'); });
        vdLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'none'); });
    } else {
        complianceLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'none'); });
        vdLayers.forEach(l => { if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'visible'); });
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
