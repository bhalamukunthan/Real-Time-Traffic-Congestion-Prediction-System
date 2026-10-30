/**
 * System Status & Architecture Health Controller
 * Inspects the live status of all 6 layers of the Data Stream Analytics system.
 */

document.addEventListener("DOMContentLoaded", async () => {
  await refreshSystemStatus();
  // Poll system status every 3 seconds
  setInterval(refreshSystemStatus, 3000);
});

async function refreshSystemStatus() {
  const status = await api.getSystemStatus();
  if (!status) return;

  // 1. Kafka Producer Status
  updateStatusBadge("status-kafka-producer", status.kafka_producer_status, status.kafka_producer_status.includes("ACTIVE") ? "ONLINE" : "READY");

  // 2. Kafka Consumer Status
  updateStatusBadge("status-kafka-consumer", status.kafka_consumer_status, status.kafka_consumer_status.includes("ACTIVE") ? "ONLINE" : "READY");

  // 3. FastAPI Backend Status
  updateStatusBadge("status-backend", status.backend_status, "ONLINE");

  // 4. Database Status
  const dbText = `${status.database_status} (${status.database_type})`;
  updateStatusBadge("status-database", dbText, status.database_status);

  // 5. ML Models Status
  updateStatusBadge("status-ml-models", status.ml_model_status, status.ml_model_status.includes("ONLINE") ? "ONLINE" : "DEGRADED");

  // 6. Metrics & Timestamps
  document.getElementById("status-last-event").textContent = status.last_received_event_time || "Awaiting stream...";
  document.getElementById("status-total-events").textContent = (status.events_processed_count || 0).toLocaleString();
  document.getElementById("status-total-anomalies").textContent = (status.anomalies_detected_count || 0).toLocaleString();

  // Uptime formatting
  const uptimeSec = Math.floor(status.uptime_seconds || 0);
  const mins = Math.floor(uptimeSec / 60);
  const secs = uptimeSec % 60;
  document.getElementById("status-uptime").textContent = `${mins}m ${secs}s`;
}

function updateStatusBadge(elementId, text, health) {
  const el = document.getElementById(elementId);
  if (!el) return;

  el.textContent = text;
  if (health === "ONLINE") {
    el.className = "badge badge-low";
  } else if (health === "READY") {
    el.className = "badge badge-medium";
  } else {
    el.className = "badge badge-severe";
  }
}

