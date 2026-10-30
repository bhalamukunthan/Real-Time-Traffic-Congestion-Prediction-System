/**
 * Overview Dashboard Controller
 * Connects KPI cards, Chart.js instances, and real-time tables to live stream.
 */

let speedDensityChart = null;
let vehicleCountChart = null;
let congestionDonutChart = null;
let predictionTrendChart = null;

// Real-time rolling chart buffers
const MAX_TIME_POINTS = 15;
const timeLabels = [];
const speedHistory = [];
const densityHistory = [];

document.addEventListener("DOMContentLoaded", async () => {
  initCharts();
  await loadInitialDashboardData();

  // Subscribe to real-time events from WebSocket
  api.onTrafficEvent((payload) => {
    handleRealtimeUpdate(payload);
  });
});

function initCharts() {
  const chartFont = { family: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" };

  // 1. Live Speed vs Density Chart
  const ctx1 = document.getElementById("speedDensityChart")?.getContext("2d");
  if (ctx1) {
    speedDensityChart = new Chart(ctx1, {
      type: "line",
      data: {
        labels: timeLabels,
        datasets: [
          {
            label: "Average Speed (km/h)",
            data: speedHistory,
            borderColor: "#06b6d4",
            backgroundColor: "rgba(6, 182, 212, 0.1)",
            tension: 0.35,
            fill: true,
            yAxisID: "y"
          },
          {
            label: "Traffic Density (%)",
            data: densityHistory,
            borderColor: "#f97316",
            backgroundColor: "rgba(249, 115, 22, 0.1)",
            tension: 0.35,
            fill: true,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: chartFont } }
        },
        scales: {
          x: {
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#64748b" }
          },
          y: {
            type: "linear",
            position: "left",
            min: 0,
            max: 120,
            grid: { color: "rgba(255, 255, 255, 0.05)" },
            ticks: { color: "#06b6d4" },
            title: { display: true, text: "Speed (km/h)", color: "#06b6d4" }
          },
          y1: {
            type: "linear",
            position: "right",
            min: 0,
            max: 100,
            grid: { drawOnChartArea: false },
            ticks: { color: "#f97316" },
            title: { display: true, text: "Density (%)", color: "#f97316" }
          }
        }
      }
    });
  }

  // 2. Vehicle Count Per Road Chart
  const ctx2 = document.getElementById("vehicleCountChart")?.getContext("2d");
  if (ctx2) {
    vehicleCountChart = new Chart(ctx2, {
      type: "bar",
      data: {
        labels: ["ROAD-001", "ROAD-002", "ROAD-003", "ROAD-004", "ROAD-005", "ROAD-006"],
        datasets: [{
          label: "Active Vehicles",
          data: [0, 0, 0, 0, 0, 0],
          backgroundColor: [
            "#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"
          ],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } }
        }
      }
    });
  }

  // 3. Congestion Distribution Donut Chart
  const ctx3 = document.getElementById("congestionDonutChart")?.getContext("2d");
  if (ctx3) {
    congestionDonutChart = new Chart(ctx3, {
      type: "doughnut",
      data: {
        labels: ["Low Flow", "Moderate", "Heavy", "Severe"],
        datasets: [{
          data: [1, 1, 1, 1],
          backgroundColor: ["#10b981", "#f59e0b", "#f97316", "#ef4444"],
          borderColor: "#16203a",
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { color: "#94a3b8", font: chartFont } }
        },
        cutout: "70%"
      }
    });
  }

  // 4. Traffic Prediction Chart
  const ctx4 = document.getElementById("predictionTrendChart")?.getContext("2d");
  if (ctx4) {
    predictionTrendChart = new Chart(ctx4, {
      type: "line",
      data: {
        labels: ["Current", "+3m", "+6m", "+9m", "+12m", "+15m (RF)"],
        datasets: [{
          label: "Predicted Density (%)",
          data: [35, 40, 48, 52, 58, 62],
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.15)",
          borderDash: [5, 5],
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: chartFont } }
        },
        scales: {
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
          y: { min: 0, max: 100, grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } }
        }
      }
    });
  }
}

async function loadInitialDashboardData() {
  const summary = await api.getDashboardSummary();
  if (!summary) return;
  
  // Pre-populate line chart with recent history points
  if (summary.recent_events && summary.recent_events.length > 0) {
    const sortedEvents = [...summary.recent_events].reverse();
    timeLabels.length = 0;
    speedHistory.length = 0;
    densityHistory.length = 0;

    sortedEvents.forEach(e => {
      const timeStr = e.timestamp.split(" ")[1] || e.timestamp;
      timeLabels.push(timeStr);
      speedHistory.push(e.average_speed);
      densityHistory.push(e.traffic_density);
    });

    if (speedDensityChart) {
      speedDensityChart.update("none");
    }
  }

  updateDashboardUI(summary);
}

function updateDashboardUI(summary) {
  // Update KPI Cards
  document.getElementById("kpi-total-vehicles").textContent = summary.total_vehicles_monitored.toLocaleString();
  document.getElementById("kpi-avg-speed").textContent = `${summary.average_speed_network.toFixed(1)} km/h`;
  document.getElementById("kpi-active-roads").textContent = `${summary.active_roads_count} Roads`;
  document.getElementById("kpi-congested-roads").textContent = summary.congested_roads_count;
  document.getElementById("kpi-avg-density").textContent = `${summary.average_density_network.toFixed(1)}%`;
  document.getElementById("kpi-active-alerts").textContent = summary.active_alerts_count;

  // Update Donut Chart
  if (congestionDonutChart && summary.congestion_distribution) {
    const dist = summary.congestion_distribution;
    congestionDonutChart.data.datasets[0].data = [
      dist.LOW || 0,
      dist.MEDIUM || 0,
      dist.HIGH || 0,
      dist.SEVERE || 0
    ];
    congestionDonutChart.update("none");
  }

  // Update Road Vehicle Counts Chart
  if (vehicleCountChart && summary.roads_status) {
    vehicleCountChart.data.labels = summary.roads_status.map(r => r.road_id);
    vehicleCountChart.data.datasets[0].data = summary.roads_status.map(r => r.vehicle_count);
    vehicleCountChart.update("none");
  }

  // Render Recent Events Table
  renderRecentEventsTable(summary.recent_events || []);

  // Render Recent Anomalies
  renderRecentAnomalies(summary.recent_anomalies || []);
}

function handleRealtimeUpdate(payload) {
  if (payload.type === "polling_summary") {
    updateDashboardUI(payload.data);
    return;
  }

  if (payload.type !== "traffic_update") return;

  const event = payload.event;
  const metrics = payload.metrics;
  const prediction = payload.prediction;
  const anomaly = payload.anomaly;

  // 1. Push to Live Line Chart
  const timeStr = event.timestamp.split(" ")[1] || event.timestamp;
  timeLabels.push(timeStr);
  speedHistory.push(metrics.rolling_avg_speed);
  densityHistory.push(metrics.avg_density);

  if (timeLabels.length > MAX_TIME_POINTS) {
    timeLabels.shift();
    speedHistory.shift();
    densityHistory.shift();
  }

  if (speedDensityChart) {
    speedDensityChart.update("none");
  }

  // 2. Update Prediction chart with latest RF forecast
  if (predictionTrendChart && prediction) {
    const currD = event.traffic_density;
    const predD = prediction.predicted_density;
    predictionTrendChart.data.datasets[0].data = [
      currD,
      Math.round(currD + (predD - currD) * 0.2),
      Math.round(currD + (predD - currD) * 0.4),
      Math.round(currD + (predD - currD) * 0.6),
      Math.round(currD + (predD - currD) * 0.8),
      predD
    ];
    predictionTrendChart.update("none");
  }

  // 3. Prepend into Recent Events Table dynamically
  prependEventToTable(event);

  // 4. If Anomaly, prepend alert banner
  if (anomaly && anomaly.is_anomaly) {
    prependAnomalyAlert(event, anomaly);
    const alertKpi = document.getElementById("kpi-active-alerts");
    if (alertKpi) {
      alertKpi.textContent = parseInt(alertKpi.textContent || "0") + 1;
    }
  }
}

function renderRecentEventsTable(events) {
  const tbody = document.getElementById("recent-events-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  events.slice(0, 8).forEach(event => {
    tbody.appendChild(createEventRow(event));
  });
}

function prependEventToTable(event) {
  const tbody = document.getElementById("recent-events-tbody");
  if (!tbody) return;
  const row = createEventRow(event);
  tbody.insertBefore(row, tbody.firstChild);
  if (tbody.children.length > 8) {
    tbody.removeChild(tbody.lastChild);
  }
}

function createEventRow(event) {
  const tr = document.createElement("tr");
  const badgeClass = getBadgeClass(event.congestion_level);
  
  tr.innerHTML = `
    <td><strong>${escapeHtml(event.road_id)}</strong><br><small style="color:#64748b">${escapeHtml(event.road_name)}</small></td>
    <td>${event.timestamp.split(" ")[1] || event.timestamp}</td>
    <td>${event.vehicle_count}</td>
    <td>${event.average_speed} km/h</td>
    <td>${event.traffic_density}%</td>
    <td><span class="badge ${badgeClass}">${event.congestion_level}</span></td>
  `;
  return tr;
}

function renderRecentAnomalies(anomalies) {
  const container = document.getElementById("recent-anomalies-container");
  if (!container) return;
  container.innerHTML = "";

  if (anomalies.length === 0) {
    container.innerHTML = `<div style="color:#64748b; font-size:0.85rem; padding: 1rem 0;">No active anomalies detected in current monitoring stream.</div>`;
    return;
  }

  anomalies.slice(0, 5).forEach(a => {
    container.appendChild(createAnomalyCard(a));
  });
}

function prependAnomalyAlert(event, anomaly) {
  const container = document.getElementById("recent-anomalies-container");
  if (!container) return;

  const dummyAnomaly = {
    road_id: event.road_id,
    road_name: event.road_name,
    timestamp: event.timestamp,
    vehicle_count: event.vehicle_count,
    average_speed: event.average_speed,
    anomaly_score: anomaly.anomaly_score,
    anomaly_reason: anomaly.anomaly_reason
  };

  const card = createAnomalyCard(dummyAnomaly);
  container.insertBefore(card, container.firstChild);
  if (container.children.length > 5) {
    container.removeChild(container.lastChild);
  }
}

function createAnomalyCard(a) {
  const div = document.createElement("div");
  div.style.cssText = "background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.65rem;";
  
  div.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
      <span style="font-weight:700; color:#ff6b6b; font-size:0.82rem;">⚠ ${escapeHtml(a.road_id)}: ${escapeHtml(a.road_name)}</span>
      <span style="font-size:0.7rem; color:#94a3b8;">${a.timestamp}</span>
    </div>
    <div style="font-size:0.78rem; color:#f8fafc; margin-bottom:0.25rem;">${escapeHtml(a.anomaly_reason)}</div>
    <div style="font-size:0.72rem; color:#64748b;">Vehicles: ${a.vehicle_count} | Speed: ${a.average_speed} km/h | Anomaly Score: ${a.anomaly_score}</div>
  `;
  return div;
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

