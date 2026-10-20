import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import {
  Activity,
  AlertTriangle,
  Flame,
  Zap,
  Droplets,
  Radio,
  Gauge,
  Cpu,
  ShieldAlert
} from 'lucide-react';
import { TelemetryData, SimulatorStatus } from '../types';
import { api } from '../api/client';

interface LiveMonitoringPageProps {
  telemetry: TelemetryData | null;
  simulator: SimulatorStatus | null;
  history: TelemetryData[];
  activeVehicleId?: string;
}

export const LiveMonitoringPage: React.FC<LiveMonitoringPageProps> = ({
  telemetry,
  simulator,
  history,
  activeVehicleId
}) => {
  const is4W = activeVehicleId?.includes('4W') || telemetry?.vehicle_type === 'four_wheeler' || (telemetry?.battery_voltage ?? 0) > 100;
  const [selectedFault, setSelectedFault] = useState<string>('over_temp_battery');
  const [faultDuration, setFaultDuration] = useState<number>(30);
  const [injecting, setInjecting] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  const baseFaultOptions = [
    { id: 'over_temp_battery', label: 'Battery Over-Temperature (>55°C)', icon: Flame, desc: 'Thermal runaway simulation' },
    { id: 'motor_overheat', label: 'Motor Severe Overheat (>100°C)', icon: Flame, desc: 'Primary stator winding high-temp' },
    { id: 'sudden_voltage_sag', label: 'Deep Voltage Sag (Cell Dip)', icon: Zap, desc: 'Sudden pack drop under load' },
    { id: 'high_discharge_current', label: 'Overcurrent Surge', icon: Zap, desc: is4W ? 'Exceeds 320A inverter rating' : 'Exceeds 65A peak limit' },
    { id: 'sensor_drift', label: 'Analog Sensor Drift', icon: Radio, desc: 'Sensor calibration deviation' },
    { id: 'sensor_disconnect', label: 'CAN Sensor Signal Disconnect', icon: Radio, desc: 'Missing packets / Unavailable' },
  ];

  const fourWheelerFaults = [
    { id: 'coolant_pump_failure', label: 'Coolant Pump Thermal Failure', icon: Droplets, desc: 'Liquid loop exceeds 70°C' },
    { id: 'secondary_motor_overheat', label: 'Rear Motor Thermal Overheat', icon: Cpu, desc: 'Dual-drive torque imbalance' },
    { id: 'insulation_loss', label: 'HV Chassis Isolation Loss', icon: ShieldAlert, desc: 'Resistance falls below 100kΩ' }
  ];

  const twoWheelerFaults = [
    { id: 'moisture_detected', label: 'Moisture Ingress Sensor (Wet)', icon: Droplets, desc: '2W Chassis floor seal breach' },
    { id: 'cell_imbalance', label: 'BMS Cell Delta-V Imbalance', icon: Activity, desc: 'Cell series mismatch' }
  ];

  const faultOptions = is4W
    ? [...baseFaultOptions, ...fourWheelerFaults]
    : [...baseFaultOptions, ...twoWheelerFaults];

  const handleInjectFault = async () => {
    setInjecting(true);
    try {
      await api.injectFault(selectedFault, faultDuration, activeVehicleId);
      setMessage(`Injected fault: ${selectedFault} for ${faultDuration}s`);
      setTimeout(() => setMessage(null), 4000);
    } catch {
      setMessage('Failed to inject fault.');
    } finally {
      setInjecting(false);
    }
  };

  const handleClearFault = async () => {
    try {
      await api.clearFault(activeVehicleId);
      setMessage('Active faults cleared.');
      setTimeout(() => setMessage(null), 3000);
    } catch {}
  };

  // Dynamic axis domains depending on vehicle architecture
  const vDomain = is4W ? [320, 460] : [38, 62];
  const aDomain = is4W ? [-220, 340] : [-20, 85];
  const spdDomain = is4W ? [0, 160] : [0, 90];
  const whDomain = is4W ? [40, 360] : [10, 80];

  // Format data for Recharts
  const chartData = history.map((pt) => ({
    time: new Date(pt.timestamp).toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' }),
    voltage: pt.battery_voltage,
    current: pt.battery_current,
    batteryTemp: pt.battery_temperature,
    motorTemp: pt.motor_temperature,
    secondaryMotorTemp: pt.secondary_motor_temperature ?? null,
    coolantTemp: pt.coolant_temperature ?? null,
    ambientTemp: pt.ambient_temperature,
    speed: pt.vehicle_speed,
    power: pt.power_kw,
    consumption: pt.energy_consumption
  }));

  return (
    <div className="space-y-6">
      {/* Fault Injection Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="font-semibold text-white text-sm">
                Synthetic Fault Injection Testbench ({is4W ? '4W Sedan Architecture' : '2W Scooter Architecture'})
              </h3>
              <p className="text-xs text-slate-400">
                Inject controlled anomalies into vehicle physics stream to evaluate detection response in real-time
              </p>
            </div>
          </div>
          {simulator?.active_injected_fault && (
            <div className="flex items-center gap-2 bg-rose-950/80 border border-rose-800 text-rose-300 text-xs px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span>Active: <strong>{simulator.active_injected_fault}</strong></span>
              <button
                onClick={handleClearFault}
                className="ml-2 hover:bg-rose-900 px-2 py-0.5 rounded text-white font-semibold transition"
              >
                Clear
              </button>
            </div>
          )}
        </div>

        {/* Fault Selector Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5 mb-4">
          {faultOptions.map((f) => {
            const Icon = f.icon;
            const isSelected = selectedFault === f.id;
            return (
              <button
                key={f.id}
                onClick={() => setSelectedFault(f.id)}
                className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                  isSelected
                    ? 'bg-amber-500/15 border-amber-500 text-amber-300 shadow-sm shadow-amber-500/10'
                    : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-amber-400' : 'text-slate-500'}`} />
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />}
                </div>
                <div>
                  <div className="text-xs font-semibold leading-tight text-slate-200">{f.label}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{f.desc}</div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Action Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <div className="flex items-center space-x-3 text-xs">
            <span className="text-slate-400">Duration:</span>
            {[10, 30, 60].map((dur) => (
              <button
                key={dur}
                onClick={() => setFaultDuration(dur)}
                className={`px-2.5 py-1 rounded text-xs font-medium border ${
                  faultDuration === dur
                    ? 'bg-slate-700 text-white border-slate-600'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {dur}s
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2">
            {message && <span className="text-xs text-cyan-400 font-medium animate-pulse">{message}</span>}
            <button
              onClick={handleInjectFault}
              disabled={injecting}
              className="px-4 py-2 bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white font-semibold rounded-xl text-xs shadow-lg shadow-amber-500/20 transition disabled:opacity-50"
            >
              {injecting ? 'Injecting...' : 'Inject Selected Fault'}
            </button>
          </div>
        </div>
      </div>

      {/* Real-Time Trends Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Voltage & Current Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              <h3 className="font-semibold text-white text-sm">
                Battery Pack Electrical ({is4W ? '400V Nominal Range' : '52V Nominal Range'})
              </h3>
            </div>
            <div className="text-[11px] font-mono text-cyan-400">
              {telemetry?.battery_voltage?.toFixed(1)}V • {telemetry?.battery_current?.toFixed(1)}A
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis yAxisId="v" domain={vDomain} stroke="#06b6d4" fontSize={10} unit="V" />
                <YAxis yAxisId="a" orientation="right" domain={aDomain} stroke="#f59e0b" fontSize={10} unit="A" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line yAxisId="v" type="monotone" dataKey="voltage" stroke="#06b6d4" name="Voltage (V)" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Line yAxisId="a" type="monotone" dataKey="current" stroke="#f59e0b" name="Current (A)" dot={false} strokeWidth={2} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Thermal Dissipation Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Flame className="w-4 h-4 text-rose-400" />
              <h3 className="font-semibold text-white text-sm">Thermal Profile (°C)</h3>
            </div>
            <div className="text-[11px] font-mono text-rose-400">
              Batt: {telemetry?.battery_temperature?.toFixed(1)}°C • Motor: {telemetry?.motor_temperature?.toFixed(1)}°C
              {is4W && telemetry?.coolant_temperature && ` • Coolant: ${telemetry.coolant_temperature.toFixed(1)}°C`}
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis domain={[15, 120]} stroke="#f43f5e" fontSize={10} unit="°C" />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line type="monotone" dataKey="batteryTemp" stroke="#f43f5e" name="Battery Temp (°C)" dot={false} strokeWidth={2} isAnimationActive={false} />
                <Line type="monotone" dataKey="motorTemp" stroke="#fb923c" name={is4W ? "Front Motor (°C)" : "Motor Temp (°C)"} dot={false} strokeWidth={2} isAnimationActive={false} />
                {is4W && (
                  <Line type="monotone" dataKey="secondaryMotorTemp" stroke="#c084fc" name="Rear Motor (°C)" dot={false} strokeWidth={1.5} isAnimationActive={false} />
                )}
                {is4W && (
                  <Line type="monotone" dataKey="coolantTemp" stroke="#38bdf8" name="Coolant Loop (°C)" dot={false} strokeWidth={2} isAnimationActive={false} />
                )}
                <Line type="monotone" dataKey="ambientTemp" stroke="#64748b" strokeDasharray="4 4" name="Ambient (°C)" dot={false} strokeWidth={1.5} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Speed & Energy Consumption Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Gauge className="w-4 h-4 text-emerald-400" />
            <h3 className="font-semibold text-white text-sm">Speed & Dynamic Energy Consumption (Wh/km)</h3>
          </div>
          <div className="text-[11px] font-mono text-emerald-400">
            {telemetry?.vehicle_speed?.toFixed(1)} km/h • {telemetry?.energy_consumption?.toFixed(1)} Wh/km
          </div>
        </div>
        <div className="h-60 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="time" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis yAxisId="spd" domain={spdDomain} stroke="#10b981" fontSize={10} unit="km/h" />
              <YAxis yAxisId="wh" orientation="right" domain={whDomain} stroke="#a855f7" fontSize={10} unit="Wh/km" />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Line yAxisId="spd" type="monotone" dataKey="speed" stroke="#10b981" name="Speed (km/h)" dot={false} strokeWidth={2} isAnimationActive={false} />
              <Line yAxisId="wh" type="monotone" dataKey="consumption" stroke="#a855f7" name="Energy (Wh/km)" dot={false} strokeWidth={2} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
