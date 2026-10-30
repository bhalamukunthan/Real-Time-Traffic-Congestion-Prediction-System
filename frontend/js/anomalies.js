/**
 * Anomaly Detection Controller
 * Visualizes unusual traffic patterns identified by Isolation Forest and heuristic filters.
 */

document.addEventListener("DOMContentLoaded", async () => {
  setupAnomalyFilters();
  await loadRoadsFilter();
  await refreshAnomalies();

  // Listen to WebSocket stream for incoming anomaly events
  api.onTrafficEvent((payload) => {
    if (payload.type === "traffic_update" && payload.anomaly && payload.anomaly.is_anomaly) {
      prependLiveAnomaly(payload.event, payload.anomaly);
    }
  });
});

async function loadRoadsFilter() {
  const roads = await api.getRoads();
  const select = document.getElementById("filter-anomaly-road");
  if (!roads || !select) return;

  roads.forEach(r => {
    const opt = document.createElement("option");
    opt.value = r.road_id;
    opt.textContent = `${r.road_id} - ${r.road_name}`;
    select.appendChild(opt);
  });
}

function setupAnomalyFilters() {
  document.getElementById("btn-filter-anomalies")?.addEventListener("click", () => {
    refreshAnomalies();
  });
}

async function refreshAnomalies() {
  const roadId = document.getElementById("filter-anomaly-road")?.value || "ALL";
  const status = document.getElementById("filter-anomaly-status")?.value || "ALL";

  const anomalies = await api.getAnomalies(roadId, status, 100);
  renderAnomaliesTable(anomalies || []);
  updateAnomalyKPIs(anomalies || []);
}

function updateAnomalyKPIs(anomalies) {
  const total = anomalies.length;
  const standstills = anomalies.filter(a => a.anomaly_reason.toLowerCase().includes("bottleneck") || a.anomaly_reason.toLowerCase().includes("standstill")).length;
  const surges = anomalies.filter(a => a.anomaly_reason.toLowerCase().includes("surge") || a.anomaly_reason.toLowerCase().includes("volume")).length;
  const speedDrops = anomalies.filter(a => a.anomaly_reason.toLowerCase().includes("speed drop") || a.anomaly_reason.toLowerCase().includes("speeding")).length;

  document.getElementById("kpi-total-anomalies").textContent = total;
  document.getElementById("kpi-standstills").textContent = standstills;
  document.getElementById("kpi-surges").textContent = surges;
  document.getElementById("kpi-speed-drops").textContent = speedDrops;
}

function renderAnomaliesTable(anomalies) {
  const tbody = document.getElementById("anomalies-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (anomalies.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#64748b; padding:1.5rem;">No anomalous events recorded for current filters.</td></tr>`;
    return;
  }

  anomalies.forEach(a => tbody.appendChild(createAnomalyTableRow(a)));
}

function prependLiveAnomaly(event, anomaly) {
  const tbody = document.getElementById("anomalies-tbody");
  if (!tbody) return;

  const item = {
    event_id: event.event_id,
    timestamp: event.timestamp,
    road_id: event.road_id,
    road_name: event.road_name,
    vehicle_count: event.vehicle_count,
    average_speed: event.average_speed,
    traffic_density: event.traffic_density,
    anomaly_score: anomaly.anomaly_score,
    anomaly_reason: anomaly.anomaly_reason,
    status: "ACTIVE"
  };

  const row = createAnomalyTableRow(item);
  tbody.insertBefore(row, tbody.firstChild);

  // Increment KPI count
  const kpiEl = document.getElementById("kpi-total-anomalies");
  if (kpiEl) kpiEl.textContent = parseInt(kpiEl.textContent || "0") + 1;
}

function createAnomalyTableRow(a) {
  const tr = document.createElement("tr");
  const scorePct = Math.round((a.anomaly_score || 0.75) * 100);

  tr.innerHTML = `
    <td><strong>${escapeHtml(a.road_id)}</strong></td>
    <td>${escapeHtml(a.road_name)}</td>
    <td>${a.timestamp}</td>
    <td><strong style="color:#ef4444;">${a.vehicle_count}</strong></td>
    <td>${a.average_speed} km/h</td>
    <td>${a.traffic_density}%</td>
    <td>
      <span class="badge badge-anomaly">${scorePct}% Outlier</span>
      <div style="font-size:0.75rem; color:#cbd5e1; margin-top:3px;">${escapeHtml(a.anomaly_reason)}</div>
    </td>
    <td><span class="badge" style="background:rgba(239,68,68,0.15); color:#ff6b6b; border:1px solid #ef4444;">${a.status || 'ACTIVE'}</span></td>
  `;
  return tr;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

