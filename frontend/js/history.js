/**
 * Historical Analytics Controller
 * Long-term traffic trends, peak rush-hour distributions, and road performance comparisons.
 */

let hourlyTrendsChart = null;
let roadComparisonChart = null;

const TWO_HOUR_SLOTS = ["00:00", "02:00", "04:00", "06:00", "08:00 (Rush)", "10:00", "12:00", "14:00", "16:00", "18:00 (Rush)", "20:00", "22:00"];

document.addEventListener("DOMContentLoaded", async () => {
  initHistoryCharts();
  await loadHistoricalAnalytics();
});

function initHistoryCharts() {
  const chartFont = { family: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" };

  // 1. Peak Traffic Hours Chart
  const ctx1 = document.getElementById("hourlyTrendsChart")?.getContext("2d");
  if (ctx1) {
    hourlyTrendsChart = new Chart(ctx1, {
      type: "bar",
      data: {
        labels: TWO_HOUR_SLOTS,
        datasets: [
          {
            label: "Average Vehicles / Hour",
            data: [25, 18, 15, 45, 135, 95, 78, 82, 110, 142, 88, 52],
            backgroundColor: "#3b82f6",
            borderRadius: 6
          },
          {
            type: "line",
            label: "Average Density (%)",
            data: [15, 12, 10, 28, 78, 55, 48, 51, 68, 85, 54, 32],
            borderColor: "#f97316",
            tension: 0.35,
            fill: false,
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
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } },
          y1: {
            position: "right",
            grid: { drawOnChartArea: false },
            ticks: { color: "#f97316" },
            min: 0,
            max: 100
          }
        }
      }
    });
  }

  // 2. Road-wise Performance Comparison
  const ctx2 = document.getElementById("roadComparisonChart")?.getContext("2d");
  if (ctx2) {
    roadComparisonChart = new Chart(ctx2, {
      type: "bar",
      data: {
        labels: ["ROAD-001", "ROAD-002", "ROAD-003", "ROAD-004", "ROAD-005", "ROAD-006"],
        datasets: [
          {
            label: "Avg Speed (km/h)",
            data: [62, 38, 54, 48, 72, 34],
            backgroundColor: "#06b6d4",
            borderRadius: 6
          },
          {
            label: "Avg Density (%)",
            data: [42, 65, 48, 52, 38, 68],
            backgroundColor: "#8b5cf6",
            borderRadius: 6
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
          x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
          y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#64748b" } }
        }
      }
    });
  }
}

async function loadHistoricalAnalytics() {
  const events = await api.getTrafficHistory("ALL", "ALL", 168, 500);
  if (!events || events.length === 0) return;

  // 1. Group by 2-hour slots for Diurnal Rush-Hour chart
  const slotCounts = new Array(12).fill(0);
  const slotVehicles = new Array(12).fill(0);
  const slotDensity = new Array(12).fill(0);

  // 2. Group by Road for Corridor Benchmark
  const roadStats = {};

  // 3. Compute daily summaries for Table
  const dayBuckets = {};

  events.forEach(e => {
    // Parse time
    const timeParts = e.timestamp.split(" ");
    const dateStr = timeParts[0];
    const timeStr = timeParts[1] || "12:00:00";
    const hour = parseInt(timeStr.split(":")[0]) || 0;

    // Slot index (0 to 11)
    const slotIdx = Math.floor(hour / 2) % 12;
    slotCounts[slotIdx]++;
    slotVehicles[slotIdx] += e.vehicle_count;
    slotDensity[slotIdx] += e.traffic_density;

    // Road stats
    if (!roadStats[e.road_id]) {
      roadStats[e.road_id] = { speeds: [], densities: [] };
    }
    roadStats[e.road_id].speeds.push(e.average_speed);
    roadStats[e.road_id].densities.push(e.traffic_density);

    // Day stats
    if (!dayBuckets[dateStr]) {
      dayBuckets[dateStr] = { count: 0, vehicles: 0, speeds: [], highCongestions: 0 };
    }
    dayBuckets[dateStr].count++;
    dayBuckets[dateStr].vehicles += e.vehicle_count;
    dayBuckets[dateStr].speeds.push(e.average_speed);
    if (e.congestion_level === "HIGH" || e.congestion_level === "SEVERE") {
      dayBuckets[dateStr].highCongestions++;
    }
  });

  // Update Hourly Trends Chart with Real Aggregations
  if (hourlyTrendsChart) {
    const avgVehicles = slotVehicles.map((v, i) => slotCounts[i] ? Math.round(v / slotCounts[i]) : 30);
    const avgDensities = slotDensity.map((d, i) => slotCounts[i] ? Math.round(d / slotCounts[i]) : 20);
    hourlyTrendsChart.data.datasets[0].data = avgVehicles;
    hourlyTrendsChart.data.datasets[1].data = avgDensities;
    hourlyTrendsChart.update("none");
  }

  // Update Road Comparison Chart with Real Aggregations
  if (roadComparisonChart) {
    const roads = ["ROAD-001", "ROAD-002", "ROAD-003", "ROAD-004", "ROAD-005", "ROAD-006"];
    const avgSpds = roads.map(r => {
      const arr = roadStats[r]?.speeds;
      return arr && arr.length ? Math.round(arr.reduce((a,b)=>a+b,0)/arr.length) : 50;
    });
    const avgDens = roads.map(r => {
      const arr = roadStats[r]?.densities;
      return arr && arr.length ? Math.round(arr.reduce((a,b)=>a+b,0)/arr.length) : 40;
    });
    roadComparisonChart.data.datasets[0].data = avgSpds;
    roadComparisonChart.data.datasets[1].data = avgDens;
    roadComparisonChart.update("none");
  }

  // Render Daily Table
  const tbody = document.getElementById("daily-stats-tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  Object.entries(dayBuckets).slice(0, 7).forEach(([date, stats]) => {
    const avgSpeed = (stats.speeds.reduce((a, b) => a + b, 0) / stats.speeds.length).toFixed(1);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${date}</strong></td>
      <td>${stats.vehicles.toLocaleString()} vehicles</td>
      <td>${avgSpeed} km/h</td>
      <td><span class="badge ${stats.highCongestions > 10 ? 'badge-severe' : 'badge-low'}">${stats.highCongestions} occurrences</span></td>
      <td>08:00 - 10:00 &amp; 17:00 - 19:30</td>
    `;
    tbody.appendChild(tr);
  });
}
