import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NotificationDrawer } from './components/NotificationDrawer';
import { OverviewPage } from './pages/OverviewPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { AiIntelligencePage } from './pages/AiIntelligencePage';
import { VehicleServicePage } from './pages/VehicleServicePage';
import { OtaValidationPage } from './pages/OtaValidationPage';
import { SettingsPage } from './pages/SettingsPage';
import {
  TelemetryData,
  SimulatorStatus,
  HealthAssessment,
  AnomalyEvent,
  VehicleProfileSummary
} from './types';
import { api } from './api/client';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [activeVehicleId, setActiveVehicleId] = useState<string>('E2W-SCOOT-01');
  const [availableVehicles, setAvailableVehicles] = useState<VehicleProfileSummary[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [simulator, setSimulator] = useState<SimulatorStatus | null>(null);
  const [health, setHealth] = useState<HealthAssessment | null>(null);
  const [history, setHistory] = useState<TelemetryData[]>([]);
  const [events, setEvents] = useState<AnomalyEvent[]>([]);
  const [showNotifications, setShowNotifications] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);

  // Load profiles on mount
  useEffect(() => {
    api.listVehicles().then((profiles) => {
      if (profiles && profiles.length > 0) {
        setAvailableVehicles(profiles);
      }
    }).catch(() => {});
  }, []);

  // Poll fallback / initial fetch
  const fetchAllData = (vehicleId: string = activeVehicleId) => {
    api.getCurrentTelemetry(vehicleId).then((pt) => {
      setTelemetry(pt);
      setHistory((prev) => [...prev.slice(-59), pt]);
    }).catch(() => {});

    api.getSimulatorStatus(vehicleId).then((sim) => {
      setSimulator(sim);
      if (sim.available_vehicles && sim.available_vehicles.length > 0) {
        setAvailableVehicles(sim.available_vehicles);
      }
      if (sim.active_vehicle_id) {
        setActiveVehicleId(sim.active_vehicle_id);
      }
    }).catch(() => {});

    api.getHealthStatus(vehicleId).then(setHealth).catch(() => {});
    api.getAnomalyEvents(vehicleId).then(setEvents).catch(() => {});
  };

  useEffect(() => {
    // Initial fetch of history
    api.getTelemetryHistory(60, activeVehicleId).then((hist) => {
      if (hist && hist.length > 0) {
        setHistory(hist);
        setTelemetry(hist[hist.length - 1]);
      }
    }).catch(() => {});

    fetchAllData(activeVehicleId);

    // Setup live WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/telemetry`;

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.telemetry) {
            setTelemetry(data.telemetry);
            setHistory((prev) => [...prev.slice(-59), data.telemetry]);
          }
          if (data.simulator) {
            setSimulator(data.simulator);
            if (data.simulator.active_vehicle_id) {
              setActiveVehicleId(data.simulator.active_vehicle_id);
            }
          }
          if (data.health) setHealth(data.health);
        } catch {}
      };

      ws.onerror = () => {
        // Fallback to polling
      };
    } catch {}

    // Backup polling timer every 2 seconds
    const interval = setInterval(() => fetchAllData(activeVehicleId), 2000);

    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [activeVehicleId]);

  const handleSwitchVehicle = async (vehicleId: string) => {
    setActiveVehicleId(vehicleId);
    setHistory([]);
    try {
      await api.switchVehicle(vehicleId);
      fetchAllData(vehicleId);
      api.getTelemetryHistory(60, vehicleId).then((hist) => {
        if (hist && hist.length > 0) {
          setHistory(hist);
          setTelemetry(hist[hist.length - 1]);
        }
      }).catch(() => {});
    } catch {}
  };

  const handleStartSimulation = async () => {
    await api.startSimulation(activeVehicleId);
    api.getSimulatorStatus(activeVehicleId).then(setSimulator).catch(() => {});
  };

  const handlePauseSimulation = async () => {
    await api.pauseSimulation(activeVehicleId);
    api.getSimulatorStatus(activeVehicleId).then(setSimulator).catch(() => {});
  };

  const handleResetSimulation = async () => {
    await api.resetSimulation(activeVehicleId);
    setHistory([]);
    fetchAllData(activeVehicleId);
  };

  const handleClearFault = async () => {
    await api.clearFault(activeVehicleId);
    api.getSimulatorStatus(activeVehicleId).then(setSimulator).catch(() => {});
  };

  const handleChangeProfile = async (profile: string) => {
    await api.setProfile(profile, activeVehicleId);
    api.getSimulatorStatus(activeVehicleId).then(setSimulator).catch(() => {});
  };

  const handleAcknowledgeAlert = async (id: number) => {
    await api.acknowledgeEvent(id);
    api.getAnomalyEvents(activeVehicleId).then(setEvents).catch(() => {});
  };

  const unreadAlerts = events.filter((e) => !e.acknowledged).length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 antialiased font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        isSimulating={simulator?.is_running ?? true}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header
          currentTab={currentTab}
          health={health}
          simulator={simulator}
          unreadAlertCount={unreadAlerts}
          availableVehicles={availableVehicles}
          activeVehicleId={activeVehicleId}
          onSwitchVehicle={handleSwitchVehicle}
          onToggleNotifications={() => setShowNotifications(!showNotifications)}
          onStartSimulation={handleStartSimulation}
          onPauseSimulation={handlePauseSimulation}
          onResetSimulation={handleResetSimulation}
          onClearFault={handleClearFault}
          onChangeProfile={handleChangeProfile}
        />

        <main className="flex-1 overflow-y-auto p-6">
          {currentTab === 'overview' && (
            <OverviewPage
              telemetry={telemetry}
              health={health}
              activeVehicleId={activeVehicleId}
              onNavigateTab={setCurrentTab}
            />
          )}

          {currentTab === 'monitoring' && (
            <LiveMonitoringPage
              telemetry={telemetry}
              simulator={simulator}
              history={history}
              activeVehicleId={activeVehicleId}
            />
          )}

          {currentTab === 'ai' && (
            <AiIntelligencePage
              telemetry={telemetry}
              health={health}
              activeVehicleId={activeVehicleId}
            />
          )}

          {currentTab === 'service' && (
            <VehicleServicePage
              simulator={simulator}
              activeVehicleId={activeVehicleId}
            />
          )}

          {currentTab === 'ota' && (
            <OtaValidationPage
              activeVehicleId={activeVehicleId}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>

      {/* Notifications Drawer */}
      <NotificationDrawer
        isOpen={showNotifications}
        onClose={() => setShowNotifications(false)}
        events={events}
        onAcknowledge={handleAcknowledgeAlert}
      />
    </div>
  );
};

export default App;
