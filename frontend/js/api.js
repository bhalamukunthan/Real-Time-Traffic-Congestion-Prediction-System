/**
 * Centralized API & Real-Time Telemetry Client
 * Handles FastAPI REST endpoints and resilient WebSocket connection.
 */

const API_BASE = (window.location.port === "8000" || window.location.pathname.startsWith("/frontend")) ? window.location.origin : "http://127.0.0.1:8000";
const WS_PROTOCOL = window.location.protocol === "https:" ? "wss:" : "ws:";
const WS_HOST = (window.location.port === "8000" || window.location.pathname.startsWith("/frontend")) ? window.location.host : "127.0.0.1:8000";
const WS_BASE = `${WS_PROTOCOL}//${WS_HOST}/ws/traffic`;

class TrafficApiClient {
  constructor() {
    this.ws = null;
    this.eventListeners = [];
    this.connectionListeners = [];
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 20;
    this.reconnectDelay = 2000;
    this.pollingInterval = null;

    // Initialize real-time streaming
    this.initWebSocket();
  }

  // -------------------------------------------------------------
  // REST API Methods
  // -------------------------------------------------------------
  async fetchJson(endpoint, options = {}) {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json"
        },
        ...options
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.warn(`API Error [${endpoint}]:`, error.message);
      return null;
    }
  }

  async getDashboardSummary() {
    return await this.fetchJson("/api/dashboard/summary");
  }

  async getLiveTraffic() {
    return await this.fetchJson("/api/traffic/live");
  }

  async getRoads() {
    return await this.fetchJson("/api/traffic/roads");
  }

  async getTrafficHistory(roadId = "ALL", congestion = "ALL", hours = 24, limit = 200) {
    const params = new URLSearchParams();
    if (roadId && roadId !== "ALL") params.append("road_id", roadId);
    if (congestion && congestion !== "ALL") params.append("congestion_level", congestion);
    if (hours) params.append("hours", hours);
    if (limit) params.append("limit", limit);
    return await this.fetchJson(`/api/traffic/history?${params.toString()}`);
  }

  async getPredictions(roadId = "ALL", limit = 50) {
    const params = new URLSearchParams();
    if (roadId && roadId !== "ALL") params.append("road_id", roadId);
    if (limit) params.append("limit", limit);
    return await this.fetchJson(`/api/predictions?${params.toString()}`);
  }

  async getModelEvaluation() {
    return await this.fetchJson("/api/predictions/evaluation");
  }

  async getAnomalies(roadId = "ALL", status = "ALL", limit = 100) {
    const params = new URLSearchParams();
    if (roadId && roadId !== "ALL") params.append("road_id", roadId);
    if (status && status !== "ALL") params.append("status", status);
    if (limit) params.append("limit", limit);
    return await this.fetchJson(`/api/anomalies?${params.toString()}`);
  }

  async getSystemStatus() {
    return await this.fetchJson("/api/system/status");
  }

  // -------------------------------------------------------------
  // WebSocket Streaming & Resilience
  // -------------------------------------------------------------
  initWebSocket() {
    try {
      this.ws = new WebSocket(WS_BASE);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log("WebSocket connected to FastAPI stream at:", WS_BASE);
        this.notifyConnectionChange(true);
        this.stopPollingFallback();
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.notifyEventListeners(payload);
        } catch (e) {
          console.debug("Non-JSON message received:", event.data);
        }
      };

      this.ws.onerror = (err) => {
        console.warn("WebSocket stream error, attempting recovery...");
        this.ws.close();
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.notifyConnectionChange(false);
        this.scheduleReconnect();
        this.startPollingFallback();
      };
    } catch (err) {
      console.warn("Could not initiate WebSocket:", err);
      this.startPollingFallback();
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const timeout = Math.min(10000, this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1));
      setTimeout(() => {
        console.log(`Reconnecting to WebSocket (attempt ${this.reconnectAttempts})...`);
        this.initWebSocket();
      }, timeout);
    }
  }

  startPollingFallback() {
    if (!this.pollingInterval) {
      console.log("Activating periodic HTTP polling fallback (every 4s)...");
      this.pollingInterval = setInterval(async () => {
        const summary = await this.getDashboardSummary();
        if (summary) {
          this.notifyEventListeners({
            type: "polling_summary",
            data: summary
          });
        }
      }, 4000);
    }
  }

  stopPollingFallback() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  // -------------------------------------------------------------
  // Event Subscriptions
  // -------------------------------------------------------------
  onTrafficEvent(callback) {
    this.eventListeners.push(callback);
  }

  onConnectionChange(callback) {
    this.connectionListeners.push(callback);
    // Notify immediate initial state
    callback(this.isConnected);
  }

  notifyEventListeners(payload) {
    this.eventListeners.forEach(cb => {
      try { cb(payload); } catch (e) { console.error("Event listener error:", e); }
    });
  }

  notifyConnectionChange(status) {
    // Update UI status pill if present on page
    const pill = document.getElementById("stream-status-pill");
    const text = document.getElementById("stream-status-text");
    if (pill && text) {
      if (status) {
        pill.classList.remove("offline");
        text.textContent = "LIVE STREAMING";
      } else {
        pill.classList.add("offline");
        text.textContent = "RECONNECTING";
      }
    }

    this.connectionListeners.forEach(cb => {
      try { cb(status); } catch (e) { console.error("Connection listener error:", e); }
    });
  }
}

// Global API singleton instance
const api = new TrafficApiClient();

