/**
 * Live Traffic Monitoring Controller
 * Real-time road cards, comprehensive live telemetry table, and multi-parameter filters.
 */

let allRoadsData = [];

document.addEventListener("DOMContentLoaded", async () => {
  setupFilterListeners();
  await loadRoadsFilterOptions();
  await refreshTrafficData();

  // Listen to WebSocket events for real-time updates
  api.onTrafficEvent((payload) => {
    if (payload.type === "traffic_update") {
      updateRoadCard(payload.event);
      // Prepend to table if matches current filter
      if (matchesCurrentFilters(payload.event)) {
        prependTrafficRow(payload.event);
      }
    }
  });
});

async function loadRoadsFilterOptions() {
  const roads = await api.getRoads();
  const select = document.getElementById("filter-road");
  if (!roads || !select) return;

  roads.forEach(r => {
    const opt = document.createElement("option");
    opt.value = r.road_id;
    opt.textContent = `${r.road_id} - ${r.road_name}`;
    select.appendChild(opt);
  });
}

function setupFilterListeners() {
  document.getElementById("btn-apply-filter")?.addEventListener("click", () => {
    refreshTrafficData();
  });
  document.getElementById("btn-reset-filter")?.addEventListener("click", () => {
    document.getElementById("filter-road").value = "ALL";
    document.getElementById("filter-congestion").value = "ALL";
    document.getElementById("filter-hours").value = "24";
    refreshTrafficData();
  });
}

async function refreshTrafficData() {
  const roadId = document.getElementById("filter-road")?.value || "ALL";
  const congestion = document.getElementById("filter-congestion")?.value || "ALL";
  const hours = parseInt(document.getElementById("filter-hours")?.value || "24");

  // 1. Fetch Road Summaries for Cards
  const liveRoads = await api.getLiveTraffic();
  if (liveRoads) {
    allRoadsData = liveRoads;
    renderRoadCards(liveRoads);
  }

  // 2. Fetch History Events according to filter
  const historyEvents = await api.getTrafficHistory(roadId, congestion, hours, 100);
  renderTrafficTable(historyEvents || []);
}

function renderRoadCards(roads) {
  const container = document.getElementById("road-cards-grid");
  if (!container) return;
  container.innerHTML = "";

  roads.forEach(road => {
    const card = document.createElement("div");
    card.className = "kpi-card";
    card.id = `road-card-${road.road_id}`;
    
    const badgeClass = getBadgeClass(road.congestion_level);
    card.innerHTML = `
      <div class="kpi-header">
        <span>${escapeHtml(road.road_id)}</span>
        <span class="badge ${badgeClass}" id="badge-${road.road_id}">${road.congestion_level}</span>
      </div>
      <div style="font-weight:700; font-size:1.05rem; color:#f8fafc; margin-top:2px;">
        ${escapeHtml(road.road_name)}
      </div>
      <div style="font-size:0.75rem; color:#64748b;">${escapeHtml(road.location)}</div>
      
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-top:0.75rem; font-size:0.8rem; background:rgba(255,255,255,0.02); padding:0.6rem; border-radius:6px;">
        <div>
          <span style="color:#64748b; font-size:0.7rem;">VEHICLES</span><br>
          <strong id="val-vehicles-${road.road_id}" style="color:#38bdf8;">${road.vehicle_count}</strong>
        </div>
        <div>
          <span style="color:#64748b; font-size:0.7rem;">AVG SPEED</span><br>
          <strong id="val-speed-${road.road_id}">${road.average_speed} km/h</strong>
        </div>
        <div>
          <span style="color:#64748b; font-size:0.7rem;">DENSITY</span><br>
          <strong id="val-density-${road.road_id}">${road.traffic_density}%</strong>
        </div>
        <div>
          <span style="color:#64748b; font-size:0.7rem;">15-MIN ML</span><br>
          <span class="badge ${getBadgeClass(road.predicted_congestion)}" style="font-size:0.65rem; padding:0.15rem 0.4rem;">${road.predicted_congestion || 'LOW'}</span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function updateRoadCard(event) {
  const badge = document.getElementById(`badge-${event.road_id}`);
  const vehicles = document.getElementById(`val-vehicles-${event.road_id}`);
  const speed = document.getElementById(`val-speed-${event.road_id}`);
  const density = document.getElementById(`val-density-${event.road_id}`);

  if (badge) {
    badge.className = `badge ${getBadgeClass(event.congestion_level)}`;
    badge.textContent = event.congestion_level;
  }
  if (vehicles) vehicles.textContent = event.vehicle_count;
  if (speed) speed.textContent = `${event.average_speed} km/h`;
  if (density) density.textContent = `${event.traffic_density}%`;
}

function renderTrafficTable(events) {
  const tbody = document.getElementById("traffic-telemetry-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (events.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#64748b; padding:1.5rem;">No events match the selected filters.</td></tr>`;
    return;
  }

  events.forEach(e => tbody.appendChild(createTrafficRow(e)));
}

function prependTrafficRow(event) {
  const tbody = document.getElementById("traffic-telemetry-tbody");
  if (!tbody) return;
  const row = createTrafficRow(event);
  tbody.insertBefore(row, tbody.firstChild);
  if (tbody.children.length > 100) {
    tbody.removeChild(tbody.lastChild);
  }
}

function createTrafficRow(event) {
  const tr = document.createElement("tr");
  const badgeClass = getBadgeClass(event.congestion_level);
  
  tr.innerHTML = `
    <td><strong>${escapeHtml(event.road_id)}</strong></td>
    <td>${escapeHtml(event.road_name)}<br><small style="color:#64748b;">${escapeHtml(event.location)}</small></td>
    <td>${event.timestamp}</td>
    <td><strong>${event.vehicle_count}</strong></td>
    <td>${event.average_speed} km/h</td>
    <td>${event.traffic_density}%</td>
    <td><span class="badge ${badgeClass}">${event.congestion_level}</span></td>
  `;
  return tr;
}

function matchesCurrentFilters(event) {
  const roadId = document.getElementById("filter-road")?.value || "ALL";
  const congestion = document.getElementById("filter-congestion")?.value || "ALL";

  if (roadId !== "ALL" && event.road_id !== roadId) return false;
  if (congestion !== "ALL" && event.congestion_level !== congestion) return false;
  return true;
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

