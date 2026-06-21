import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Activity, AlertTriangle, Brain, Cpu, Gauge, Sparkles, Thermometer,
  Waves, Zap, ShieldCheck, TrendingUp, TrendingDown, CircleDot,
  Factory, Wind, Sun, Battery, ArrowRight,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "IEI — Intelligent Energy Intelligence Dashboard" },
      {
        name: "description",
        content:
          "AI-powered enterprise energy monitoring: real-time telemetry, equipment health, anomaly detection, and predictive insights.",
      },
    ],
  }),
  component: Dashboard,
});

const seedSeries = Array.from({ length: 24 }, (_, i) => ({
  t: `${String(i).padStart(2, "0")}:00`,
  power: 280 + Math.sin(i / 2) * 60 + Math.random() * 40,
  load: 220 + Math.cos(i / 3) * 50 + Math.random() * 30,
  forecast: 290 + Math.sin(i / 2 + 0.5) * 55,
}));

const alerts = [
  {
    id: 1,
    sev: "critical",
    title: "Turbine #3 vibration spike",
    time: "2 min ago",
    detail: "RMS 7.2 mm/s exceeds 6.0 threshold",
    color: "warning",
  },
  {
    id: 2,
    sev: "warning",
    title: "Compressor A temp drift",
    time: "18 min ago",
    detail: "+4.1°C above baseline over 30m window",
    color: "warning",
  },
  {
    id: 3,
    sev: "info",
    title: "Grid frequency normalized",
    time: "1h ago",
    detail: "Frequency returned to 50.00 Hz ±0.02",
    color: "energy",
  },
];

const insights = [
  {
    icon: TrendingDown,
    label:
      "Cut HVAC load 12% by shifting setpoint to 22.5°C between 13:00–16:00.",
    impact: "−$1,240/mo",
  },
  {
    icon: Brain,
    label:
      "Predicted bearing failure on Pump P-204 within 9 days. Schedule maintenance.",
    impact: "Avoid 4h downtime",
  },
  {
    icon: Sparkles,
    label:
      "Solar array overproducing — divert 38 kWh to battery bank B for evening peak.",
    impact: "+$86/day",
  },
];

function Dashboard() {
  const [series, setSeries] = useState(seedSeries);
  const [now, setNow] = useState(new Date());

  const [dashboard, setDashboard] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);

  // Keeps the system clock and fallback demo chart moving
  useEffect(() => {
    const id = setInterval(() => {
      setNow(new Date());

      setSeries((prev) => {
        const next = prev.slice(1);
        const last = prev[prev.length - 1];

        next.push({
          t: last.t,
          power: Math.max(
            150,
            Math.min(420, last.power + (Math.random() - 0.5) * 30)
          ),
          load: Math.max(
            120,
            Math.min(360, last.load + (Math.random() - 0.5) * 25)
          ),
          forecast: last.forecast + (Math.random() - 0.5) * 10,
        });

        return next;
      });
    }, 2000);

    return () => clearInterval(id);
  }, []);

  // Pulls real data from your FastAPI backend
  useEffect(() => {
    const fetchBackendData = async () => {
      try {
        const dashboardResponse = await fetch(
          "http://127.0.0.1:8000/dashboard"
        );

        const historyResponse = await fetch(
          "http://127.0.0.1:8000/history"
        );

        const dashboardData = await dashboardResponse.json();
        const historyData = await historyResponse.json();

        setDashboard(dashboardData);
        setHistory(historyData);
      } catch (error) {
        console.error("Error connecting to FastAPI backend:", error);
      }
    };

    fetchBackendData();

    const interval = setInterval(fetchBackendData, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-obsidian text-slate-200 font-sans">
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute -top-40 -left-40 size-[520px] rounded-full bg-neon/15 blur-3xl" />
        <div className="absolute top-40 -right-40 size-[520px] rounded-full bg-energy/10 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 size-[420px] rounded-full bg-warning/10 blur-3xl" />
      </div>

      <Header now={now} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        <KPIs dashboard={dashboard} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <TelemetryCard data={history.length > 0 ? history : series} />
          <AlertsCard dashboard={dashboard} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <InsightsCard />
          <FlowCard />
          <HealthGauge dashboard={dashboard} />
        </div>
      </main>
    </div>
  );
}

/* ───────────────────────── Header ───────────────────────── */

function Header({ now }: { now: Date }) {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 backdrop-blur-xl bg-obsidian/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative size-9 rounded-xl bg-gradient-to-br from-neon to-energy grid place-items-center shadow-[0_0_24px_rgba(59,130,246,0.45)]">
            <Zap className="size-4 text-obsidian" strokeWidth={3} />
          </div>
          <div className="min-w-0">
            <div className="font-display font-bold text-white text-lg tracking-tight leading-none">IEI</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400 leading-none mt-1">Intelligent Energy</div>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-1 text-sm">
          {["Overview", "Telemetry", "Equipment", "Alerts", "Reports"].map((n, i) => (
            <a key={n} href="#" className={`px-3 py-1.5 rounded-lg transition-colors ${i === 0 ? "bg-white/5 text-white" : "text-slate-400 hover:text-white"}`}>{n}</a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <StatusBadge />
          <div className="hidden sm:flex flex-col items-end text-right">
            <div className="text-[10px] uppercase tracking-widest text-slate-500">System time</div>
            <div className="text-xs font-mono text-slate-300">{now.toLocaleTimeString()}</div>
          </div>
        </div>
      </div>
    </header>
  );
}

function StatusBadge() {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-energy/10 border border-energy/30">
      <span className="relative flex size-2">
        <span className="absolute inline-flex h-full w-full rounded-full bg-energy opacity-75 animate-ping" />
        <span className="relative inline-flex size-2 rounded-full bg-energy" />
      </span>
      <span className="text-[10px] font-bold uppercase tracking-widest text-energy">All Systems Nominal</span>
    </div>
  );
}

/* ───────────────────────── Glass shell ───────────────────────── */

function Glass({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={`relative rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-xl shadow-[0_8px_32px_-12px_rgba(0,0,0,0.5)] ${className}`}>
      <div className="absolute inset-x-6 -top-px h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      {children}
    </div>
  );
}

/* ───────────────────────── KPIs ───────────────────────── */
function KPIs({ dashboard }: { dashboard: any }) {
  const kpis = [
    {
      label: "Temperature",
      value: dashboard?.temperature ?? "--",
      unit: "°F",
      delta: "+1.2°",
      trend: "up",
      icon: Thermometer,
      color: "warning" as const,
      bar: 68,
    },
    {
      label: "Pressure",
      value: dashboard?.pressure ?? "--",
      unit: "PSI",
      delta: "-0.05",
      trend: "down",
      icon: Gauge,
      color: "neon" as const,
      bar: 48,
    },
    {
      label: "Frequency",
      value: dashboard?.frequency ?? "--",
      unit: "Hz",
      delta: "stable",
      trend: "flat",
      icon: Waves,
      color: "energy" as const,
      bar: 60,
    },

  ];

  const colorStyles = {
    warning: {
      bg: "bg-warning/10",
      text: "text-warning",
      border: "border-warning/20",
      bar: "bg-warning",
    },
    neon: {
      bg: "bg-neon/10",
      text: "text-neon",
      border: "border-neon/20",
      bar: "bg-neon",
    },
    energy: {
      bg: "bg-energy/10",
      text: "text-energy",
      border: "border-energy/20",
      bar: "bg-energy",
    },
  };

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((k) => (
        <Glass key={k.label} className="p-5">
          <div className="flex items-start justify-between mb-4">
            <div
              className={`size-10 rounded-xl grid place-items-center border
              ${colorStyles[k.color].bg}
              ${colorStyles[k.color].text}
              ${colorStyles[k.color].border}`}
            >
              <k.icon className="size-5" />
            </div>

            <div
              className={`flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider ${
                k.trend === "up"
                  ? "text-energy"
                  : k.trend === "down"
                  ? "text-warning"
                  : "text-slate-400"
              }`}
            >
              {k.trend === "up" && <TrendingUp className="size-3" />}
              {k.trend === "down" && <TrendingDown className="size-3" />}
              {k.trend === "flat" && <CircleDot className="size-3" />}
              {k.delta}
            </div>
          </div>

          <div className="text-[10px] uppercase tracking-[0.18em] text-slate-400 font-bold">
            {k.label}
          </div>

          <div className="mt-1 flex items-baseline gap-1.5">
            <div className="font-display text-3xl font-bold text-white tabular-nums">
              {k.value}
            </div>

            <div className="text-sm text-slate-500">
              {k.unit}
            </div>
          </div>

          <div className="mt-4 h-1 rounded-full bg-white/5 overflow-hidden">
            <div
              className={`h-full ${colorStyles[k.color].bar}`}
              style={{ width: `${k.bar}%` }}
            />
          </div>
        </Glass>
      ))}
    </div>
  );
}

/* ───────────────────────── Telemetry ───────────────────────── */
function TelemetryCard({ data }: { data: any[] }) {
  const chartData = data.map((item) => ({
    t: item.timestamp
      ? new Date(item.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })
      : item.t,
    active_power: Number(item.active_power ?? item.power ?? 0),
    reactive_power: Number(item.reactive_power ?? item.load ?? 0),
  }));

  return (
    <Glass className="p-5">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">
          Real-Time Telemetry
        </h3>

        <p className="text-sm text-slate-400">
          Active power and reactive power trends
        </p>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData}>
          <XAxis dataKey="t" />
          <YAxis />
          <Tooltip />

          <Area
            type="monotone"
            dataKey="active_power"
            name="Active Power"
          />

          <Area
            type="monotone"
            dataKey="reactive_power"
            name="Reactive Power"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Glass>
  );
}


/* ───────────────────────── Alerts ───────────────────────── */
function AlertsCard({ dashboard }: { dashboard: any }) {
  const backendAlerts = dashboard?.alerts ?? [];

  const alertTitles: Record<string, string> = {
    "High temperature detected": "High Temperature",
    "High pressure detected": "Pressure Spike",
    "Equipment health warning": "Equipment Health Warning",
    "Frequency instability detected": "Frequency Instability",
  };

  return (
    <Glass className="p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-lg bg-warning/10 border border-warning/20 grid place-items-center text-warning">
            <AlertTriangle className="size-4" />
          </div>

          <div>
            <h2 className="font-display font-bold text-white">
              Active Alerts
            </h2>

            <p className="text-xs text-slate-400">
              {backendAlerts.length} requiring attention
            </p>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full bg-warning/15 text-warning text-[10px] font-bold uppercase tracking-wider">
          Live
        </span>
      </div>

      {backendAlerts.length === 0 ? (
        <div className="p-4 rounded-xl bg-energy/10 border border-energy/20">
          <div className="text-sm font-semibold text-white">
            No Active Alerts
          </div>

          <div className="text-xs text-slate-400 mt-1">
            System operating normally
          </div>
        </div>
      ) : (
        <ul className="space-y-3">
          {backendAlerts.map((alert: string, index: number) => (
            <li
              key={index}
              className="group p-3 rounded-xl bg-white/[0.02] border border-warning/20 hover:border-warning/40 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 size-2 rounded-full bg-warning shrink-0" />

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold text-white truncate">
                      {alertTitles[alert] ?? "System Alert"}
                    </div>

                    <div className="text-[10px] text-slate-500">
                      Live
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 mt-1">
                    {alert}
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-warning/15 text-warning">
                      Warning
                    </span>

                    <button className="text-[10px] text-slate-400 hover:text-white font-medium">
                      Acknowledge
                    </button>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Glass>
  );
}


/* ───────────────────────── AI Insights ───────────────────────── */

function InsightsCard() {
  return (
    <Glass className="p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="size-9 rounded-lg bg-gradient-to-br from-neon to-energy grid place-items-center text-obsidian">
          <Brain className="size-4" strokeWidth={2.5} />
        </div>
        <div className="flex-1">
          <h2 className="font-display font-bold text-white">AI Insights</h2>
          <p className="text-xs text-slate-400">Predictive optimization · updated 30s ago</p>
        </div>
      </div>

      <ul className="space-y-3">
        {insights.map((it, i) => (
          <li key={i} className="p-3 rounded-xl bg-gradient-to-br from-white/[0.04] to-transparent border border-white/5">
            <div className="flex gap-3">
              <it.icon className="size-4 text-neon mt-0.5 shrink-0" />
              <div className="text-xs text-slate-300 leading-relaxed">{it.label}</div>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-energy">{it.impact}</span>
              <button className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1">
                Apply <ArrowRight className="size-3" />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </Glass>
  );
}

/* ───────────────────────── Energy Flow ───────────────────────── */

function FlowCard() {
  const nodes = [
    { label: "Solar Array", value: "186 kW", icon: Sun, color: "warning" as const },
    { label: "Grid Import", value: "82 kW", icon: Zap, color: "neon" as const },
    { label: "Wind", value: "44 kW", icon: Wind, color: "energy" as const },
  ];
  const loads = [
    { label: "Factory Floor", value: "201 kW", icon: Factory },
    { label: "HVAC", value: "78 kW", icon: Wind },
    { label: "Battery Store", value: "33 kW", icon: Battery },
  ];
  return (
    <Glass className="p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="size-9 rounded-lg bg-energy/10 border border-energy/20 grid place-items-center text-energy">
          <Zap className="size-4" />
        </div>
        <div>
          <h2 className="font-display font-bold text-white">Energy Flow</h2>
          <p className="text-xs text-slate-400">Source → Distribution</p>
        </div>
      </div>

      <div className="relative grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">Sources</div>
          {nodes.map((n) => (
            <FlowRow key={n.label} icon={n.icon} label={n.label} value={n.value} color={n.color} />
          ))}
        </div>
        <div className="space-y-2">
          <div className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mb-1">Loads</div>
          {loads.map((n) => (
            <FlowRow key={n.label} icon={n.icon} label={n.label} value={n.value} />
          ))}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-slate-500">Net Export</div>
          <div className="font-display font-bold text-energy text-lg">+24.6 kW</div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-widest text-slate-500">Efficiency</div>
          <div className="font-display font-bold text-white text-lg">96.4%</div>
        </div>
      </div>
    </Glass>
  );
}

function FlowRow({ icon: Icon, label, value, color = "neon" }: { icon: any; label: string; value: string; color?: "neon" | "energy" | "warning" }) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02] border border-white/5">
      <Icon className={`size-3.5 text-${color}`} />
      <div className="flex-1 min-w-0">
        <div className="text-[11px] text-slate-300 truncate">{label}</div>
        <div className="text-[10px] font-bold text-white tabular-nums">{value}</div>
      </div>
    </div>
  );
}

/* ───────────────────────── Equipment Health Gauge ───────────────────────── */

function HealthGauge({ dashboard }: { dashboard: any }) {
  const healthValue = dashboard?.equipment_health ?? 94;

  const data = [
    {
      name: "Health",
      value: healthValue,
      fill: "oklch(0.72 0.18 160)",
    },
  ];

  const components = [
    { name: "Turbines", v: Math.min(100, healthValue + 7) },
    { name: "Compressors", v: Math.min(100, healthValue + 1) },
    { name: "Pumps", v: Math.max(0, healthValue - 2) },
    { name: "Inverters", v: Math.min(100, healthValue + 9) },
  ];

  const healthStatus =
    healthValue >= 90 ? "Optimal" : healthValue >= 75 ? "Warning" : "Critical";

  return (
    <Glass className="p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className="size-9 rounded-lg bg-energy/10 border border-energy/20 grid place-items-center text-energy">
          <Cpu className="size-4" />
        </div>

        <div>
          <h2 className="font-display font-bold text-white">
            Equipment Health
          </h2>
          <p className="text-xs text-slate-400">
            Composite reliability index
          </p>
        </div>
      </div>

      <div className="relative h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="75%"
            outerRadius="100%"
            data={data}
            startAngle={220}
            endAngle={-40}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              tick={false}
            />

            <RadialBar
              background={{ fill: "rgba(255,255,255,0.05)" }}
              dataKey="value"
              cornerRadius={20}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="font-display font-bold text-4xl text-white tabular-nums">
            {healthValue}
            <span className="text-lg text-slate-500">%</span>
          </div>

          <div className="text-[10px] uppercase tracking-widest text-energy font-bold">
            {healthStatus}
          </div>
        </div>
      </div>

      <div className="space-y-2 mt-2">
        {components.map((c) => (
          <div key={c.name} className="flex items-center gap-3">
            <div className="text-[11px] text-slate-400 w-20 shrink-0">
              {c.name}
            </div>

            <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div
                className={
                  c.v >= 95
                    ? "h-full bg-energy"
                    : c.v >= 90
                    ? "h-full bg-neon"
                    : "h-full bg-warning"
                }
                style={{ width: `${c.v}%` }}
              />
            </div>

            <div className="text-[11px] font-bold text-white tabular-nums w-8 text-right">
              {c.v}
            </div>
          </div>
        ))}
      </div>
    </Glass>
  );
}