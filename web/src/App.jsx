import React, { useEffect, useState, useRef } from 'react';
import { Activity, ShieldAlert, Zap, Server, Wifi, Cpu } from 'lucide-react';

import { Sidebar } from './components/Sidebar';
import { StatCard } from './components/StatCard';
import { ProcessTable } from './components/ProcessTable';
import { NetworkGraph } from './components/NetworkGraph';
import { BandwidthChart } from './components/BandwidthChart';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [data, setData] = useState({
    system_status: { strict_mode: false, total_bandwidth_mbps: 0, active_penalties: 0 },
    processes: []
  });
  const [chartData, setChartData] = useState([]);
  const ws = useRef(null);

  useEffect(() => {
    // Reconnection logic could be better, but basic is fine for now
    const connect = () => {
      ws.current = new WebSocket("ws://localhost:8000/ws");

      ws.current.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setData(parsed);
          setChartData(prev => {
            const newData = [...prev, { time: parsed.timestamp, value: parsed.system_status.total_bandwidth_mbps }];
            if (newData.length > 60) newData.shift();
            return newData;
          });
        } catch (e) { console.error(e) }
      };

      ws.current.onclose = () => setTimeout(connect, 1000);
    }
    connect();
    return () => { if (ws.current) ws.current.close(); }
  }, []);

  const { strict_mode, total_bandwidth_mbps, active_penalties } = data.system_status;

  return (
    <div className="flex w-full h-screen bg-slate-950 text-slate-200 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-950">

        {/* Top Header */}
        <header className="h-16 border-b border-slate-800 bg-slate-950 flex items-center justify-between px-6 shrink-0">
          <h1 className="text-xl font-semibold text-slate-100 capitalize">{activeTab} Overview</h1>

          <div className="flex items-center gap-4">
            {/* Status Badge */}
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${strict_mode
                ? "bg-rose-500/10 border-rose-500/20 text-rose-400"
                : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              }`}>
              {strict_mode ? "Strict Enforcement" : "Monitoring Active"}
            </span>
            <div className="w-px h-6 bg-slate-800"></div>
            <span className="text-xs text-slate-500 font-mono">v1.2.0</span>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
          {activeTab === 'dashboard' && (
            <div className="space-y-6 max-w-7xl mx-auto fade-in">
              {/* 1. KPI Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="Total Usage"
                  value={total_bandwidth_mbps.toFixed(1)}
                  unit="Mbps"
                  icon={Zap}
                  color="indigo"
                  trend={12} // Fake trend for demo
                />
                <StatCard
                  title="Active Penalties"
                  value={active_penalties}
                  icon={ShieldAlert}
                  color={active_penalties > 0 ? "rose" : "emerald"}
                  trend={active_penalties > 0 ? 50 : 0}
                />
                <StatCard
                  title="Monitored Apps"
                  value={data.processes.length}
                  icon={Server}
                  color="slate"
                />
                <StatCard
                  title="System Load"
                  value="24%"
                  unit="CPU"
                  icon={Cpu}
                  color="slate"
                />
              </div>

              {/* 2. Main Dashboard Split */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
                {/* Chart Section */}
                <div className="lg:col-span-2 flex flex-col gap-6 h-full">
                  <div className="h-64 bg-slate-900 border border-slate-800 rounded-lg p-4 shadow-sm">
                    <h3 className="text-sm font-medium text-slate-400 mb-4 px-2">Network Traffic History</h3>
                    <div className="h-48 w-full">
                      <BandwidthChart data={chartData} />
                    </div>
                  </div>
                  <div className="flex-1 min-h-0">
                    <ProcessTable processes={data.processes} />
                  </div>
                </div>

                {/* Mini Topology / Status */}
                <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-lg p-1 flex flex-col h-full shadow-sm relative overflow-hidden">
                  <div className="absolute top-3 left-4 z-10 pointer-events-none">
                    <h3 className="text-sm font-medium text-slate-300">Live Map</h3>
                  </div>
                  <div className="w-full h-full opacity-80 hover:opacity-100 transition-opacity cursor-pointer" onClick={() => setActiveTab('topology')}>
                    <NetworkGraph processes={data.processes} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'topology' && (
            <div className="h-full w-full bg-slate-900 border border-slate-800 rounded-lg overflow-hidden fade-in relative">
              <NetworkGraph processes={data.processes} />
              <div className="absolute top-4 right-4 bg-slate-950/80 backdrop-blur border border-slate-800 p-4 rounded-lg max-w-xs text-xs text-slate-400 space-y-2">
                <p className="font-semibold text-slate-200">Grid Controls</p>
                <p>Drag nodes to rearrange.</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span> High Priority
                  <span className="w-2 h-2 rounded-full bg-indigo-500"></span> Medium
                </div>
              </div>
            </div>
          )}

          {activeTab === 'rules' && (
            <div className="flex items-center justify-center h-full text-slate-500 fade-in">
              <div className="text-center">
                <ShieldAlert className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h2 className="text-lg font-semibold text-slate-300">Policy Management</h2>
                <p className="max-w-md mt-2">Advanced rule configuration and strict mode thresholds will be configured here.</p>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="flex items-center justify-center h-full text-slate-500 fade-in">
              <div className="text-center">
                <Settings className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h2 className="text-lg font-semibold text-slate-300">Settings</h2>
                <p>Interface selection and API keys.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
