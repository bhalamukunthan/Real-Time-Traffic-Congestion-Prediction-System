/**
 * Interactive Leaflet.js Traffic Map Controller
 * Visualizes simulated urban road corridors with dynamic color-coded congestion states.
 */

let map = null;
const markers = {};
const polylines = {};

const COLOR_MAP = {
  LOW: "#10b981",       // Green
  MEDIUM: "#f59e0b",    // Yellow
  HIGH: "#f97316",      // Orange
  SEVERE: "#ef4444"     // Red
};

document.addEventListener("DOMContentLoaded", async () => {
  initMap();
  await loadMapRoads();

  // Listen to WebSocket stream to dynamically update map marker colors & tooltips
  api.onTrafficEvent((payload) => {
    if (payload.type === "traffic_update") {
      updateMapMarker(payload.event, payload.prediction);
    }
  });
});

function initMap() {
  // Center near Delhi NCR urban coordinates (simulated urban testbed)
  map = L.map("traffic-map").setView([28.6139, 77.2090], 12);

  // CartoDB Dark Matter tiles for professional dark-navy theme
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 19
  }).addTo(map);
}

async function loadMapRoads() {
  const liveRoads = await api.getLiveTraffic();
  if (!liveRoads || !map) return;

  liveRoads.forEach(road => {
    const lat = road.latitude;
    const lng = road.longitude;
    const color = COLOR_MAP[road.congestion_level] || COLOR_MAP.LOW;

    // Glowing circle marker
    const marker = L.circleMarker([lat, lng], {
      radius: 12,
      fillColor: color,
      color: "#ffffff",
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.85
    }).addTo(map);

    // Bind popup with simulated telemetry details
    marker.bindPopup(buildPopupContent(road));
    markers[road.road_id] = marker;

    // Add corridor directional polyline segment (simulated corridor span ~2km)
    const poly = L.polyline([
      [lat - 0.015, lng - 0.012],
      [lat, lng],
      [lat + 0.015, lng + 0.012]
    ], {
      color: color,
      weight: 4,
      opacity: 0.75,
      dashArray: "6, 8"
    }).addTo(map);
    polylines[road.road_id] = poly;
  });
}

function updateMapMarker(event, prediction) {
  const marker = markers[event.road_id];
  const poly = polylines[event.road_id];
  const newColor = COLOR_MAP[event.congestion_level] || COLOR_MAP.LOW;

  if (marker) {
    marker.setStyle({ fillColor: newColor });
    const dummyRoad = {
      road_id: event.road_id,
      road_name: event.road_name,
      location: event.location,
      vehicle_count: event.vehicle_count,
      average_speed: event.average_speed,
      traffic_density: event.traffic_density,
      congestion_level: event.congestion_level,
      predicted_congestion: prediction ? prediction.predicted_congestion : "LOW",
      last_updated: event.timestamp
    };
    marker.setPopupContent(buildPopupContent(dummyRoad));
  }

  if (poly) {
    poly.setStyle({ color: newColor });
  }
}

function buildPopupContent(road) {
  const badgeClass = getBadgeClass(road.congestion_level);
  return `
    <div style="font-family:sans-serif; min-width:210px; padding:4px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
        <strong style="color:#38bdf8; font-size:1rem;">${escapeHtml(road.road_id)}</strong>
        <span class="badge ${badgeClass}" style="font-size:0.68rem;">${road.congestion_level}</span>
      </div>
      <div style="font-weight:600; font-size:0.85rem; margin-bottom:2px;">${escapeHtml(road.road_name)}</div>
      <div style="font-size:0.75rem; color:#94a3b8; margin-bottom:8px;">${escapeHtml(road.location)}</div>
      
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; font-size:0.75rem; background:rgba(255,255,255,0.05); padding:6px; border-radius:6px; margin-bottom:8px;">
        <div>Vehicles: <strong>${road.vehicle_count}</strong></div>
        <div>Avg Speed: <strong>${road.average_speed} km/h</strong></div>
        <div>Density: <strong>${road.traffic_density}%</strong></div>
        <div>15-Min ML: <strong>${road.predicted_congestion || 'LOW'}</strong></div>
      </div>
      
      <div style="font-size:0.65rem; color:#64748b; border-top:1px solid rgba(255,255,255,0.1); padding-top:4px;">
        * Simulated Sensor Telemetry Node
      </div>
    </div>
  `;
}

function getBadgeClass(level) {
  switch (level?.toUpperCase()) {
    case "LOW": return "badge-low";
    case "MEDIUM": return "badge-medium";
    case "HIGH": return "badge-high";
    case "SEVERE": return "badge-severe";
    default: return "badge-low";
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

