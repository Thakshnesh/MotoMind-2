import React, { useState, useEffect } from 'react';
import {
  BatteryCharging,
  Gauge,
  Thermometer,
  Zap,
  Activity,
  ShieldAlert,
  ShieldCheck,
  Compass,
  ArrowUpRight,
  Info,
  Car,
  Bike,
  CheckCircle2
} from 'lucide-react';
import { TelemetryData, HealthAssessment, RangeEstimate, ValidationRun } from '../types';
import { api } from '../api/client';

interface OverviewPageProps {
  telemetry: TelemetryData | null;
  health: HealthAssessment | null;
  activeVehicleId?: string;
  onNavigateTab: (tab: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  telemetry,
  health,
  activeVehicleId = 'E2W-SCOOT-01',
  onNavigateTab
}) => {
  const is4W = activeVehicleId.includes('4W') || telemetry?.vehicle_type === 'four_wheeler';
  const defaultCapacity = is4W ? 64.0 : 3.2;

  const [rangeEstimate, setRangeEstimate] = useState<RangeEstimate | null>(null);
  const [customCapacity, setCustomCapacity] = useState<number | null>(null);
  const [elevationM, setElevationM] = useState<number>(0);
  const [trafficFactor, setTrafficFactor] = useState<number>(1.0);
  const [latestOtaRun, setLatestOtaRun] = useState<ValidationRun | null>(null);

  const capacityKwh = customCapacity ?? defaultCapacity;

  // Recalculate range whenever parameters or SOC changes
  useEffect(() => {
    let isMounted = true;
    api.estimateRange({
      vehicle_id: activeVehicleId,
      battery_soc: telemetry?.state_of_charge,
      battery_capacity_kwh: capacityKwh,
      average_consumption_wh_km: telemetry?.energy_consumption,
      elevation_gain_m: elevationM,
      traffic_factor: trafficFactor
    }).then(res => {
      if (isMounted) setRangeEstimate(res);
    }).catch(() => {});

    return () => { isMounted = false; };
  }, [activeVehicleId, telemetry?.state_of_charge, telemetry?.energy_consumption, capacityKwh, elevationM, trafficFactor]);

  // Fetch latest OTA run summary for this vehicle type
  useEffect(() => {
    let isMounted = true;
    const targetType = is4W ? 'four_wheeler' : 'two_wheeler';
    api.getValidationRuns(targetType).then(runs => {
      if (isMounted && runs.length > 0) {
        setLatestOtaRun(runs[0]);
      }
    }).catch(() => {});
    return () => { isMounted = false; };
  }, [is4W]);

  const soc = telemetry?.state_of_charge ?? 82.5;
  const soh = telemetry?.state_of_health ?? 96.8;
  const battTemp = telemetry?.battery_temperature ?? (is4W ? 29.5 : 31.0);
  const motorTemp = telemetry?.motor_temperature ?? (is4W ? 36.0 : 38.0);
  const secMotorTemp = telemetry?.secondary_motor_temperature;
  const coolantTemp = telemetry?.coolant_temperature;
  const speed = telemetry?.vehicle_speed ?? 0.0;
  const whKm = telemetry?.energy_consumption ?? (is4W ? 165.0 : 32.0);
  const voltage = telemetry?.battery_voltage ?? (is4W ? 398.0 : 52.0);
  const current = telemetry?.battery_current ?? 0.0;

  const sensorAvail = telemetry?.sensor_availability || {};

  return (
    <div className="space-y-6">
      {/* Synthetic Data Transparency Pill */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="font-semibold text-white">Active Vehicle:</span>
          <span className="text-cyan-400 font-mono font-bold flex items-center gap-1">
            {is4W ? <Car className="w-3.5 h-3.5 text-cyan-400" /> : <Bike className="w-3.5 h-3.5 text-emerald-400" />}
            {is4W ? 'Vanguard GT 4W (400V • 64 kWh)' : 'Apex Urban 2W (52V • 3.2 kWh)'}
          </span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400">Context: {telemetry?.operating_context || 'city_commute'}</span>
        </div>
        <div className="text-slate-400 text-[11px] flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-cyan-400" />
          <span>Vehicle-specific telemetry & sensor availability mapped in real-time.</span>
        </div>
      </div>

      {/* Primary Telemetry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Battery SOC & SOH */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Battery Pack SOC</span>
            <BatteryCharging className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{soc.toFixed(1)}%</span>
            <span className="text-xs text-emerald-400 font-medium">SOH {soh.toFixed(1)}%</span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                soc > 40 ? 'bg-emerald-500' : soc > 20 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, soc))}%` }}
            />
          </div>
          <div className="flex justify-between items-center text-[11px] text-slate-400 mt-2">
            <span className="font-mono text-cyan-300">{voltage.toFixed(1)} V ({is4W ? '400V Pack' : '52V 14S Pack'})</span>
            <span>{current >= 0 ? `${current.toFixed(1)} A Discharge` : `${Math.abs(current).toFixed(1)} A Charge`}</span>
          </div>
        </div>

        {/* Thermal Conditions */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Thermal Conditions</span>
            <Thermometer className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-3xl font-extrabold ${battTemp >= (is4W ? 50 : 48) ? 'text-rose-400' : 'text-white'}`}>
              {battTemp.toFixed(1)}°C
            </span>
            <span className="text-xs text-slate-400">Battery</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs border-t border-slate-800/80 pt-2">
            <span className="text-slate-400">{is4W ? 'Primary / Rear Motor:' : 'Traction Motor:'}</span>
            <span className={`font-semibold ${motorTemp >= (is4W ? 90 : 85) ? 'text-rose-400' : 'text-slate-200'}`}>
              {motorTemp.toFixed(1)}°C {secMotorTemp !== null && secMotorTemp !== undefined && `/ ${secMotorTemp.toFixed(1)}°C`}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
            <span>{is4W ? 'Coolant Loop:' : 'Cooling Mode:'}</span>
            <span className="font-semibold text-cyan-300">
              {is4W && coolantTemp ? `${coolantTemp.toFixed(1)}°C (Liquid)` : 'Air Cooled (Ambient ΔT)'}
            </span>
          </div>
        </div>

        {/* Speed & Dynamics */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Vehicle Speed</span>
            <Gauge className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-white">{speed.toFixed(1)}</span>
            <span className="text-xs text-slate-400">km/h</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs border-t border-slate-800/80 pt-2">
            <span className="text-slate-400">Consumption Rate:</span>
            <span className="font-semibold text-slate-200">{whKm.toFixed(1)} Wh/km</span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
            <span>Total Power Output:</span>
            <span className="font-mono text-cyan-300">{((voltage * Math.max(0, current)) / 1000).toFixed(2)} kW</span>
          </div>
        </div>

        {/* Range Estimate Quick Look */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Estimated Range</span>
            <Compass className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-emerald-400">
              {rangeEstimate?.estimated_range_km?.toFixed(0) || '--'}
            </span>
            <span className="text-xs text-slate-400">km</span>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs border-t border-slate-800/80 pt-2">
            <span className="text-slate-400">Confidence Band:</span>
            <span className="font-semibold text-slate-300">
              {rangeEstimate ? `${rangeEstimate.confidence_interval_min_km} - ${rangeEstimate.confidence_interval_max_km} km` : '--'}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
            <span>Usable Energy:</span>
            <span className="font-mono text-emerald-300">
              {rangeEstimate ? (rangeEstimate.usable_energy_remaining_wh / 1000).toFixed(2) : '--'} kWh
            </span>
          </div>
        </div>
      </div>

      {/* Sensor Availability & Provenance Status Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
            Sensor Availability & Provenance Tagging ({is4W ? '4W Architecture' : '2W Architecture'})
          </span>
          <span className="text-[10px] text-slate-400">
            Complies with explicit sensor verification standards (No synthetic replacement of absent hardware)
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[11px]">
          <div className="bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Pack Voltage</div>
            <div className="font-semibold text-cyan-400 mt-0.5">{sensorAvail.battery_voltage || 'simulated'}</div>
          </div>
          <div className="bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Motor Front/Main</div>
            <div className="font-semibold text-cyan-400 mt-0.5">{sensorAvail.motor_temperature || 'simulated'}</div>
          </div>
          <div className="bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Secondary Motor</div>
            <div className={`font-semibold mt-0.5 ${is4W ? 'text-cyan-400' : 'text-slate-500'}`}>
              {is4W ? (sensorAvail.secondary_motor_temperature || 'simulated') : 'unavailable (Single)'}
            </div>
          </div>
          <div className="bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Coolant Loop</div>
            <div className={`font-semibold mt-0.5 ${is4W ? 'text-cyan-400' : 'text-slate-500'}`}>
              {is4W ? (sensorAvail.coolant_temperature || 'simulated') : 'unavailable (Air)'}
            </div>
          </div>
          <div className="bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">HVIL / Isolation</div>
            <div className={`font-semibold mt-0.5 ${is4W ? 'text-cyan-400' : 'text-slate-500'}`}>
              {is4W ? (sensorAvail.insulation_resistance_kohm || 'simulated') : 'unavailable (LV 52V)'}
            </div>
          </div>
          <div className="bg-slate-950/80 p-2 rounded-lg border border-slate-800">
            <div className="text-slate-400 text-[10px]">Moisture Ingress</div>
            <div className={`font-semibold mt-0.5 ${!is4W ? 'text-cyan-400' : 'text-slate-500'}`}>
              {!is4W ? (sensorAvail.moisture_status || 'simulated') : 'unavailable (Sealed)'}
            </div>
          </div>
        </div>
      </div>

      {/* Middle Row: Subsystem Health & Transparent Range Estimator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Health Scores Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="font-semibold text-white text-sm">Sub-System Health Evaluation</h3>
            </div>
            <button
              onClick={() => onNavigateTab('ai')}
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
            >
              AI Insights <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-slate-300">Battery Subsystem</span>
                <span className="text-emerald-400 font-bold">{health?.battery_health_score ?? 96}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all"
                  style={{ width: `${health?.battery_health_score ?? 96}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-slate-300">Traction Motor {is4W ? '(Dual PMSM)' : '(Single BLDC)'}</span>
                <span className="text-cyan-400 font-bold">{health?.motor_health_score ?? 98}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full transition-all"
                  style={{ width: `${health?.motor_health_score ?? 98}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-slate-300">Electrical & HV Isolation</span>
                <span className="text-indigo-400 font-bold">{health?.electrical_health_score ?? 95}%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all"
                  style={{ width: `${health?.electrical_health_score ?? 95}%` }}
                />
              </div>
            </div>
          </div>

          {/* Active Health Observations / Rule Reasons */}
          <div className="mt-5 border-t border-slate-800 pt-3">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Diagnostics Rationale:
            </span>
            {health?.reasons && health.reasons.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-slate-300">
                {health.reasons.slice(0, 3).map((r, i) => (
                  <li key={i} className="flex items-start gap-1.5 bg-slate-950/60 p-2 rounded border border-slate-800/80">
                    <span className="text-amber-400 font-bold">•</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500 italic bg-slate-950/40 p-2 rounded">
                No active rule violations. Operational parameters align with baseline statistical bounds.
              </p>
            )}
          </div>
        </div>

        {/* Interactive Range Estimator Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Compass className="w-4 h-4 text-emerald-400" />
              <h3 className="font-semibold text-white text-sm">Transparent Range Estimation Model</h3>
            </div>
            <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-950/80 border border-emerald-800/60 px-2 py-0.5 rounded-full">
              Physics Scaling: {is4W ? '4-Wheeler (165 Wh/km)' : '2-Wheeler (32 Wh/km)'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                Usable Capacity (kWh)
              </label>
              <input
                type="number"
                step="0.5"
                min="1.0"
                max="150.0"
                value={capacityKwh}
                onChange={(e) => setCustomCapacity(parseFloat(e.target.value) || null)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                Planned Elevation (meters)
              </label>
              <input
                type="number"
                step="25"
                min="0"
                max="2000"
                value={elevationM}
                onChange={(e) => setElevationM(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">
                Traffic Factor
              </label>
              <select
                value={trafficFactor}
                onChange={(e) => setTrafficFactor(parseFloat(e.target.value))}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="1.0">1.0x (Free flow cruising)</option>
                <option value="1.15">1.15x (Moderate suburban)</option>
                <option value="1.3">1.3x (Heavy stop-and-go)</option>
              </select>
            </div>
          </div>

          {/* Transparent Assumptions Output */}
          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs">
            <span className="font-semibold text-slate-300 block mb-2">Model Calculations & Assumptions:</span>
            <ul className="space-y-1 text-slate-400 text-[11px]">
              {rangeEstimate?.assumptions_explanation.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-cyan-400 font-bold">›</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] text-slate-500">
              {rangeEstimate?.disclaimer}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: OTA Validation Status Card & Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Latest OTA Validation Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              <h3 className="font-semibold text-white text-sm">
                Latest Virtual OTA Validation ({is4W ? 'Four-Wheeler' : 'Two-Wheeler'})
              </h3>
            </div>
            <button
              onClick={() => onNavigateTab('ota')}
              className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1 font-medium"
            >
              OTA Center <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {latestOtaRun ? (
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400">Run ID: </span>
                  <span className="text-xs font-mono text-slate-200">{latestOtaRun.id}</span>
                </div>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  latestOtaRun.overall_result === 'PASS'
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    : 'bg-rose-950 text-rose-300 border border-rose-800'
                }`}>
                  {latestOtaRun.overall_result}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="bg-slate-900 p-2 rounded">
                  <div className="text-slate-400 text-[10px]">Tests Run</div>
                  <div className="font-bold text-white mt-0.5">{latestOtaRun.total_tests}</div>
                </div>
                <div className="bg-slate-900 p-2 rounded">
                  <div className="text-emerald-400 text-[10px]">Passed</div>
                  <div className="font-bold text-emerald-400 mt-0.5">{latestOtaRun.passed_tests}</div>
                </div>
                <div className="bg-slate-900 p-2 rounded">
                  <div className="text-rose-400 text-[10px]">Failed / Block</div>
                  <div className="font-bold text-rose-400 mt-0.5">{latestOtaRun.failed_tests}</div>
                </div>
              </div>
              <p className="text-[11px] text-slate-400 line-clamp-2">
                {latestOtaRun.block_reason || "All safety assertions passed successfully."}
              </p>
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-xs">
              No validation runs executed yet for {is4W ? 'Four-Wheeler' : 'Two-Wheeler'}. Visit OTA Validation Center to run candidate test suite.
            </div>
          )}
        </div>

        {/* Quick Diagnostic Controls */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <h3 className="font-semibold text-white text-sm mb-3">Quick Actions & Workflows</h3>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => onNavigateTab('monitoring')}
              className="p-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-left transition flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-cyan-400 mb-1">
                <Zap className="w-4 h-4" />
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Inject Fault</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{is4W ? 'Pump failure or isolation' : 'Thermal or voltage sag'}</div>
              </div>
            </button>

            <button
              onClick={() => onNavigateTab('ai')}
              className="p-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-left transition flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-indigo-400 mb-1">
                <Activity className="w-4 h-4" />
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Retrain AI Baseline</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Vehicle-specific Isolation Forest</div>
              </div>
            </button>

            <button
              onClick={() => onNavigateTab('service')}
              className="p-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-left transition flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-amber-400 mb-1">
                <Car className="w-4 h-4" />
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Component History</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Track batteries & motors</div>
              </div>
            </button>

            <button
              onClick={() => onNavigateTab('ota')}
              className="p-3 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-left transition flex flex-col justify-between"
            >
              <div className="flex items-center justify-between text-purple-400 mb-1">
                <ShieldAlert className="w-4 h-4" />
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white">OTA Test Suite</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{is4W ? '12 4W High-Voltage tests' : '12 2W Commuter tests'}</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
