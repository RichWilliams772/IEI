import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const dashboardResponse = await axios.get(
          "http://127.0.0.1:8000/dashboard"
        );

        const historyResponse = await axios.get(
          "http://127.0.0.1:8000/history"
        );

        setDashboard(dashboardResponse.data);
        setHistory(historyResponse.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();

    const interval = setInterval(fetchData, 5000);

    return () => clearInterval(interval);
  }, []);

  if (!dashboard) {
    return <h1 className="loading">Loading dashboard...</h1>;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">⚡ IEI</div>

        <nav className="sidebar-nav">
          <span>Dashboard</span>
          <span>Live Monitoring</span>
          <span>Analytics</span>
          <span>Predictions</span>
          <span>Equipment</span>
          <span>Alerts</span>
          <span>Reports</span>
          <span>Settings</span>
        </nav>
      </aside>

      <main className="dashboard">
        <div className="topbar">
          <div>
            <p className="topbar-label">Energy Intelligence Console</p>
            <h2>Real-Time Grid & Equipment Monitoring</h2>
          </div>

          <div className="topbar-right">
            <span className="status-dot"></span>
            <span>Live System</span>
          </div>
        </div>

        <div className="dashboard-header">
          <h1 className="logo-title">IEI</h1>

          <p className="platform-title">
            Intelligent Energy Monitoring Platform
          </p>

          <p className="subtitle">
            Real-Time Infrastructure Intelligence Dashboard
          </p>

          <p className="live-indicator">● LIVE MONITORING</p>
        </div>

        <div className="cards">
          <div className="card">
            <div className="card-label">🌡 Temperature</div>
            <div className="card-value amber">
              {dashboard.temperature}°F
            </div>
            <p className="card-trend">▲ +3.2% today</p>
          </div>

          <div className="card">
            <div className="card-label">⚙ Pressure</div>
            <div className="card-value blue">
              {dashboard.pressure} PSI
            </div>
            <p className="card-trend">Normal operating range</p>
          </div>

          <div className="card">
            <div className="card-label">〰 Frequency</div>
            <div className="card-value green">
              {dashboard.frequency} Hz
            </div>
            <p className="card-trend">Grid stability active</p>
          </div>

          <div className="card">
            <div className="card-label">🛡 Equipment Health</div>
            <div className="card-value amber">
              {dashboard.equipment_health}%
            </div>
            <p className="card-trend">Predictive maintenance watch</p>
          </div>
        </div>

        <div className="status-panel">
          <div className="card-label">System Status</div>

          <div className={`status-badge ${dashboard.status}`}>
            {dashboard.status.toUpperCase()}
          </div>
        </div>

        <div className="main-grid">
          <div className="chart-section">
            <div className="section-header">
              <h2>System Performance Trends</h2>

              <div className="time-toggle">
                <span>1H</span>
                <span>24H</span>
                <span>7D</span>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="id" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />

                <Line
                  type="monotone"
                  dataKey="temperature"
                  stroke="#F59E0B"
                  strokeWidth={3}
                />

                <Line
                  type="monotone"
                  dataKey="pressure"
                  stroke="#3B82F6"
                  strokeWidth={3}
                />

                <Line
                  type="monotone"
                  dataKey="equipment_health"
                  stroke="#10B981"
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="right-column">
            <div className="alert-panel">
              <h2>Active Alerts</h2>

              {dashboard.alerts.map((alert, index) => (
                <div className="alert-item" key={index}>
                  ⚠️ {alert}
                </div>
              ))}
            </div>

            <div className="ai-panel">
              <h2>🤖 AI Insights</h2>

              <p className="ai-text">
                Temperature and pressure are trending above the normal range.
                Equipment efficiency may decrease within the next 24 hours.
              </p>

              <div className="recommendation">
                <strong>Recommended Action:</strong> Inspect Cooling System A
                and review pressure valves.
              </div>
            </div>
          </div>
        </div>

        <div className="bottom-grid">
          <div className="energy-flow-panel">
            <h2>Energy Flow</h2>

            <div className="energy-flow">
              <div className="flow-node">Power Source</div>
              <div className="flow-arrow">→</div>
              <div className="flow-node">Transformer</div>
              <div className="flow-arrow">→</div>
              <div className="flow-node">Facility Load</div>
              <div className="flow-arrow">→</div>
              <div className="flow-node">Grid Output</div>
            </div>
          </div>

          <div className="health-gauge-panel">
            <h2>System Health Score</h2>

            <div className="gauge">
              <div className="gauge-inner">
                <div className="gauge-value">
                  {dashboard.equipment_health}%
                </div>
                <div className="gauge-label">Operational</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;