import React from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  AlertTriangle,
  Bell,
  Wrench,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Sliders,
  X,
  Bike,
  Car
} from 'lucide-react';
import { HealthAssessment, SimulatorStatus, VehicleProfileSummary } from '../types';

interface HeaderProps {
  currentTab: string;
  health: HealthAssessment | null;
  simulator: SimulatorStatus | null;
  unreadAlertCount: number;
  availableVehicles?: VehicleProfileSummary[];
  activeVehicleId?: string;
  onSwitchVehicle?: (vehicleId: string) => void;
  onToggleNotifications: () => void;
  onStartSimulation: () => void;
  onPauseSimulation: () => void;
  onResetSimulation: () => void;
  onClearFault: () => void;
  onChangeProfile: (profile: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  health,
  simulator,
  unreadAlertCount,
  availableVehicles = [],
  activeVehicleId,
  onSwitchVehicle,
  onToggleNotifications,
  onStartSimulation,
  onPauseSimulation,
  onResetSimulation,
  onClearFault,
  onChangeProfile
}) => {
  const getTabTitle = () => {
    switch (currentTab) {
      case 'overview': return 'EV Health Overview';
      case 'monitoring': return 'Live Telemetry & Diagnostics';
      case 'ai': return 'Self-Learning AI Health Intelligence';
      case 'service': return 'Component Lifecycle & Service Records';
      case 'ota': return 'OTA Software Update Validation Center';
      case 'settings': return 'System Settings & Config';
      default: return 'MotoMind EV Dashboard';
    }
  };

  const status = health?.overall_status || 'Normal';
  const currentVehicleId = activeVehicleId || simulator?.active_vehicle_id || 'E2W-SCOOT-01';
  const is4W = currentVehicleId.includes('4W') || simulator?.active_vehicle_type === 'four_wheeler';

  const activeProfile: VehicleProfileSummary = availableVehicles.find(v => v.vehicle_id === currentVehicleId) || {
    vehicle_id: currentVehicleId,
    vehicle_type: is4W ? 'four_wheeler' : 'two_wheeler',
    display_name: is4W ? 'Vanguard GT 4W (Sedan)' : 'Apex Urban 2W (Scooter)',
    category_label: is4W ? 'Electric Four-Wheeler' : 'Electric Two-Wheeler',
    battery_voltage: is4W ? 400.0 : 52.0,
    capacity_kwh: is4W ? 64.0 : 3.2,
    battery: {
      nominal_voltage: is4W ? 400.0 : 52.0,
      usable_capacity_kwh: is4W ? 64.0 : 3.2
    }
  };

  const activeVoltage = activeProfile.battery?.nominal_voltage ?? activeProfile.battery_voltage ?? (is4W ? 400.0 : 52.0);

  const getStatusBadge = () => {
    switch (status) {
      case 'High Anomaly':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            High Anomaly
          </span>
        );
      case 'Warning':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Warning Alert
          </span>
        );
      case 'Insufficient Data':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-700/50 text-slate-300 border border-slate-600">
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            Sensor Bus Fault
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Vehicle Healthy
          </span>
        );
    }
  };

  return (
    <header className="h-16 bg-slate-900/90 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between z-10 sticky top-0">
      {/* Title & Status */}
      <div className="flex items-center space-x-3">
        <h2 className="text-base font-semibold text-white tracking-tight">{getTabTitle()}</h2>
        {getStatusBadge()}

        {/* Vehicle Selector Pill */}
        <div className="flex items-center gap-1.5 bg-slate-800/90 border border-cyan-500/40 px-2.5 py-1 rounded-lg text-xs shadow-sm">
          {is4W ? (
            <Car className="w-4 h-4 text-cyan-400" />
          ) : (
            <Bike className="w-4 h-4 text-emerald-400" />
          )}
          <select
            value={currentVehicleId}
            onChange={(e) => onSwitchVehicle && onSwitchVehicle(e.target.value)}
            className="bg-transparent text-slate-100 font-semibold text-xs focus:outline-none cursor-pointer"
            title="Switch Active EV Vehicle Profile"
          >
            {availableVehicles.length > 0 ? (
              availableVehicles.map((v) => {
                const volt = v.battery?.nominal_voltage ?? v.battery_voltage ?? 52.0;
                const cap = v.battery?.usable_capacity_kwh ?? v.capacity_kwh ?? 3.2;
                return (
                  <option key={v.vehicle_id} value={v.vehicle_id} className="bg-slate-900 text-slate-200">
                    {v.display_name} ({volt}V • {cap}kWh)
                  </option>
                );
              })
            ) : (
              <>
                <option value="E2W-SCOOT-01" className="bg-slate-900 text-slate-200">
                  Apex Urban 2W (Scooter - 52V • 3.2kWh)
                </option>
                <option value="E4W-SEDAN-01" className="bg-slate-900 text-slate-200">
                  Vanguard GT 4W (Sedan - 400V • 64kWh)
                </option>
              </>
            )}
          </select>
          <span className="hidden md:inline-block px-1.5 py-0.2 rounded bg-slate-700/60 text-[10px] text-cyan-300 font-mono">
            {activeVoltage}V
          </span>
        </div>

        {simulator?.service_mode_active && (
          <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-950/60 text-amber-400 border border-amber-800">
            <Wrench className="w-3 h-3" />
            Service Mode
          </span>
        )}

        {simulator?.active_injected_fault && (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950 text-rose-300 border border-rose-800">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            Fault: {simulator.active_injected_fault}
            <button
              onClick={onClearFault}
              title="Clear injected fault"
              className="ml-1 hover:text-white"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        )}
      </div>

      {/* Action Controls */}
      <div className="flex items-center space-x-3">
        {/* Profile Selector */}
        <div className="flex items-center space-x-1 bg-slate-800/80 border border-slate-700 rounded-lg p-1 text-xs">
          <Sliders className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
          <select
            value={simulator?.current_profile || 'city_commute'}
            onChange={(e) => onChangeProfile(e.target.value)}
            className="bg-transparent text-slate-200 text-xs px-2 py-0.5 font-medium focus:outline-none cursor-pointer"
          >
            <option value="city_commute" className="bg-slate-900 text-slate-200">City Commute</option>
            <option value="aggressive_sport" className="bg-slate-900 text-slate-200">Aggressive Sport</option>
            <option value="eco_cruising" className="bg-slate-900 text-slate-200">Eco Cruising</option>
            <option value="idle_charging" className="bg-slate-900 text-slate-200">AC Charging (Grid)</option>
            {is4W && (
              <option value="dc_fast_charging" className="bg-slate-900 text-slate-200">CCS2 DC Fast Charge</option>
            )}
          </select>
        </div>

        {/* Simulation Play / Pause / Reset */}
        <div className="flex items-center bg-slate-800/80 border border-slate-700 rounded-lg p-0.5">
          {simulator?.is_running ? (
            <button
              onClick={onPauseSimulation}
              title="Pause Simulation"
              className="px-2.5 py-1 text-slate-300 hover:text-white hover:bg-slate-700/60 rounded flex items-center gap-1 text-xs font-medium transition"
            >
              <Pause className="w-3.5 h-3.5 text-amber-400" />
              Pause
            </button>
          ) : (
            <button
              onClick={onStartSimulation}
              title="Resume Simulation"
              className="px-2.5 py-1 text-slate-300 hover:text-white hover:bg-slate-700/60 rounded flex items-center gap-1 text-xs font-medium transition"
            >
              <Play className="w-3.5 h-3.5 text-emerald-400" />
              Start
            </button>
          )}

          <div className="w-[1px] h-4 bg-slate-700 mx-0.5" />

          <button
            onClick={onResetSimulation}
            title="Reset Simulation"
            className="px-2 py-1 text-slate-400 hover:text-slate-200 hover:bg-slate-700/60 rounded transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Notification Bell */}
        <button
          onClick={onToggleNotifications}
          className="relative p-2 text-slate-400 hover:text-slate-100 bg-slate-800/80 border border-slate-700 rounded-lg transition"
          title="Notifications and In-App Alerts"
        >
          <Bell className="w-4 h-4" />
          {unreadAlertCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center animate-pulse">
              {unreadAlertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
