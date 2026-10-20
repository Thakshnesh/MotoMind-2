import React, { useState, useEffect, useCallback } from 'react';
import {
  Wrench,
  Droplets,
  RotateCcw,
  CheckCircle,
  Plus,
  Battery,
  Calendar
} from 'lucide-react';
import { ComponentRecord, ServiceRecord, WaterExposureRecord, SimulatorStatus } from '../types';
import { api } from '../api/client';

interface VehicleServicePageProps {
  simulator: SimulatorStatus | null;
  activeVehicleId?: string;
}

export const VehicleServicePage: React.FC<VehicleServicePageProps> = ({
  simulator,
  activeVehicleId = 'E2W-SCOOT-01'
}) => {
  const is4W = activeVehicleId.includes('4W') || simulator?.active_vehicle_type === 'four_wheeler';

  const [components, setComponents] = useState<ComponentRecord[]>([]);
  const [services, setServices] = useState<ServiceRecord[]>([]);
  const [exposures, setExposures] = useState<WaterExposureRecord[]>([]);
  const [comparisons, setComparisons] = useState<any[]>([]);
  const [filterByVehicle, setFilterByVehicle] = useState<boolean>(true);

  // Form states
  const [showCompModal, setShowCompModal] = useState(false);
  const [compType, setCompType] = useState('BATTERY_PACK');
  const [compSerial, setCompSerial] = useState('');
  const [resetBaselineOnAdd, setResetBaselineOnAdd] = useState(true);

  const [showWaterModal, setShowWaterModal] = useState(false);
  const [exposureType, setExposureType] = useState('PRESSURE_WASH');
  const [severityLevel, setSeverityLevel] = useState('MODERATE');
  const [exposureDuration, setExposureDuration] = useState(15);
  const [waterNotes, setWaterNotes] = useState('');

  const [showServiceModal, setShowServiceModal] = useState(false);
  const [serviceType, setServiceType] = useState('ROUTINE_MAINTENANCE');
  const [serviceDesc, setServiceDesc] = useState('');
  const [techNotes, setTechNotes] = useState('');
  const [odometerKm, setOdometerKm] = useState(is4W ? 14200 : 5500);

  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadData = useCallback(() => {
    const vid = filterByVehicle ? activeVehicleId : undefined;
    api.getComponents(vid).then(setComponents).catch(() => {});
    api.getServiceRecords(vid).then(setServices).catch(() => {});
    api.getWaterExposureRecords(vid).then(setExposures).catch(() => {});
    api.getBeforeAfterComparison(vid).then(res => setComparisons(res.comparisons || [])).catch(() => {});
  }, [activeVehicleId, filterByVehicle]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleToggleServiceMode = async () => {
    const nextState = !simulator?.service_mode_active;
    try {
      await api.toggleServiceMode(nextState, activeVehicleId);
      setStatusMsg(`Service Mode ${nextState ? 'ENGAGED' : 'DISENGAGED'} for ${activeVehicleId}`);
      setTimeout(() => setStatusMsg(null), 3000);
    } catch {}
  };

  const handleAddComponent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!compSerial) return;
    try {
      await api.addComponent({
        vehicle_id: activeVehicleId,
        component_type: compType,
        serial_number: compSerial,
        nominal_specs: is4W
          ? { capacity_kwh: 64.0, nominal_voltage: 400.0, architecture: "4W 400V Liquid Cooled" }
          : { capacity_kwh: 3.2, nominal_voltage: 52.0, architecture: "2W 52V 14S Air Cooled" },
        reset_baseline: resetBaselineOnAdd,
        notes: `Replacement installed for ${activeVehicleId} via MotoMind service portal.`
      });
      setShowCompModal(false);
      setCompSerial('');
      setStatusMsg('New component registered and baseline recalibrated.');
      setTimeout(() => setStatusMsg(null), 4000);
      loadData();
    } catch {}
  };

  const handleResetBaseline = async (id: number) => {
    try {
      await api.resetComponentBaseline(id);
      setStatusMsg('Component baseline reset initiated.');
      setTimeout(() => setStatusMsg(null), 3000);
      loadData();
    } catch {}
  };

  const handleAddWaterExposure = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addWaterExposure({
        vehicle_id: activeVehicleId,
        exposure_type: exposureType,
        severity_level: severityLevel,
        duration_minutes: exposureDuration,
        moisture_sensor_reading: is4W ? 'chassis_undercarriage_spray' : 'damp',
        notes: waterNotes
      });
      setShowWaterModal(false);
      setWaterNotes('');
      setStatusMsg('Water exposure event logged.');
      setTimeout(() => setStatusMsg(null), 3000);
      loadData();
    } catch {}
  };

  const handleAddService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!serviceDesc) return;
    try {
      await api.addServiceRecord({
        vehicle_id: activeVehicleId,
        service_type: serviceType,
        description: serviceDesc,
        technician_notes: techNotes,
        odometer_km: odometerKm
      });
      setShowServiceModal(false);
      setServiceDesc('');
      setTechNotes('');
      setStatusMsg('Service record saved.');
      setTimeout(() => setStatusMsg(null), 3000);
      loadData();
    } catch {}
  };

  return (
    <div className="space-y-6">
      {/* Service Mode Header Card */}
      <div className={`border rounded-2xl p-5 transition-all ${
        simulator?.service_mode_active
          ? 'bg-amber-950/30 border-amber-800'
          : 'bg-slate-900 border-slate-800'
      }`}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-xl ${
              simulator?.service_mode_active ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-800 text-slate-400'
            }`}>
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-white text-base">Vehicle Service Mode</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-cyan-300 border border-slate-700">
                  {activeVehicleId}
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  simulator?.service_mode_active ? 'bg-amber-500/20 text-amber-300 border border-amber-600' : 'bg-slate-800 text-slate-400'
                }`}>
                  {simulator?.service_mode_active ? 'ACTIVE HOLD' : 'STANDBY'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Suppresses false driving alarms during technician inspection, dyno testing, and wash cycles.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setFilterByVehicle(!filterByVehicle)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-700 bg-slate-950 text-slate-300 hover:text-white"
            >
              {filterByVehicle ? `Showing: ${activeVehicleId}` : 'Showing: All Vehicles'}
            </button>
            {statusMsg && <span className="text-xs text-cyan-400 font-medium animate-pulse">{statusMsg}</span>}
            <button
              onClick={handleToggleServiceMode}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
                simulator?.service_mode_active
                  ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-600/20'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
              }`}
            >
              {simulator?.service_mode_active ? 'Exit Service Mode' : 'Engage Service Mode'}
            </button>
          </div>
        </div>
      </div>

      {/* Replaced Components & Lifecycle */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Battery className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="font-semibold text-white text-sm">Critical Components & Learned Baselines</h3>
              <p className="text-xs text-slate-400">Track replacement dates, serial numbers, and recalibrated baseline profiles</p>
            </div>
          </div>
          <button
            onClick={() => setShowCompModal(true)}
            className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium flex items-center gap-1 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            Register Component
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {components.map((c) => (
            <div key={c.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold text-white tracking-wide">{c.component_type}</span>
                  <div className="flex items-center gap-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono text-cyan-300 bg-slate-900 border border-slate-800">
                      {c.vehicle_id || 'Universal'}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                      Active
                    </span>
                  </div>
                </div>
                <div className="text-xs text-slate-400 space-y-1">
                  <div>Serial: <span className="font-mono text-slate-200">{c.serial_number}</span></div>
                  <div>Installed: <span className="text-slate-300">{new Date(c.installed_at).toLocaleDateString()}</span></div>
                  <div>Baseline: <span className="text-slate-300">{c.baseline_established_at ? new Date(c.baseline_established_at).toLocaleDateString() : 'Auto calibrated'}</span></div>
                  {c.notes && <div className="text-[11px] text-slate-500 italic mt-1">{c.notes}</div>}
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-900 flex justify-end">
                <button
                  onClick={() => handleResetBaseline(c.id)}
                  className="px-2.5 py-1 text-[11px] font-medium text-slate-400 hover:text-cyan-400 hover:bg-slate-900 rounded flex items-center gap-1 transition"
                  title="Recalibrate AI baseline for this component"
                >
                  <RotateCcw className="w-3 h-3" />
                  Recalibrate Baseline
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Dual Section: Service History & Water Exposure */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Record Log */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-indigo-400" />
              <div>
                <h3 className="font-semibold text-white text-sm">Service History Log</h3>
                <p className="text-xs text-slate-400">Inspections, fluids, and maintenance events</p>
              </div>
            </div>
            <button
              onClick={() => setShowServiceModal(true)}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center gap-1 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              Log Service
            </button>
          </div>

          {comparisons.length > 0 && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-300 font-semibold">Post-Service Restorative Delta:</span>
                <span className="text-slate-300">
                  {comparisons[0].service_type} ({comparisons[0].pre_health_score}% → {comparisons[0].post_health_score}%)
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700">
                {comparisons[0].improvement_pct}
              </span>
            </div>
          )}

          <div className="space-y-3">
            {services.map((s) => (
              <div key={s.id} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white">{s.service_type}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-cyan-300 font-mono">{s.vehicle_id || activeVehicleId}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400 font-mono text-[11px]">{new Date(s.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
                <p className="text-slate-300">{s.description}</p>
                {s.technician_notes && (
                  <p className="text-[11px] text-slate-500 mt-1 italic">Tech notes: {s.technician_notes}</p>
                )}
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-900 text-[11px] text-slate-400">
                  <span>Odometer: {s.odometer_km} km</span>
                  {s.pre_service_health_score && (
                    <span className="text-emerald-400">Health: {s.pre_service_health_score}% → {s.post_service_health_score || s.pre_service_health_score}%</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Water Exposure Tracker */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Droplets className="w-5 h-5 text-cyan-400" />
              <div>
                <h3 className="font-semibold text-white text-sm">Water Exposure & Washing Log</h3>
                <p className="text-xs text-slate-400">Monitors post-wash insulation & electrical integrity</p>
              </div>
            </div>
            <button
              onClick={() => setShowWaterModal(true)}
              className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium flex items-center gap-1 transition"
            >
              <Plus className="w-3.5 h-3.5" />
              Log Exposure
            </button>
          </div>

          <div className="space-y-3">
            {exposures.map((w) => (
              <div key={w.id} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white">{w.exposure_type}</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-cyan-300 font-mono">{w.vehicle_id || activeVehicleId}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400 font-mono text-[11px]">{new Date(w.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-400 my-1">
                  <span>Severity: <strong className="text-amber-400">{w.severity_level}</strong></span>
                  <span>•</span>
                  <span>Duration: {w.duration_minutes} min</span>
                  <span>•</span>
                  <span>Sensor: {w.moisture_sensor_reading}</span>
                </div>
                {w.notes && <p className="text-slate-400 text-[11px] italic mt-1">{w.notes}</p>}
                <div className="mt-2 pt-2 border-t border-slate-900 text-[10px] text-slate-500">
                  {w.disclaimer}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Component Registration Modal */}
      {showCompModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-white text-base">Register New Component ({activeVehicleId})</h3>
            <form onSubmit={handleAddComponent} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Component Type</label>
                <select
                  value={compType}
                  onChange={(e) => setCompType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="BATTERY_PACK">{is4W ? '400V 64kWh Traction Battery Pack' : '52V 3.2kWh Battery Pack'}</option>
                  <option value="TRACTION_MOTOR">{is4W ? 'Permanent Magnet Traction Inverter / Motor' : 'Mid-Drive BLDC Motor'}</option>
                  <option value="MOTOR_CONTROLLER">Primary Motor Controller (MCU)</option>
                  {is4W && <option value="SECONDARY_MOTOR">Rear Axle Induction Motor</option>}
                  {is4W && <option value="COOLANT_PUMP">Glycol Thermal Loop Circulation Pump</option>}
                  <option value="ONBOARD_CHARGER">BMS / Onboard Charger Subsystem</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Serial Number</label>
                <input
                  type="text"
                  placeholder="e.g. SN-NMC-2026-9921"
                  value={compSerial}
                  onChange={(e) => setCompSerial(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  required
                />
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="resetBaseline"
                  checked={resetBaselineOnAdd}
                  onChange={(e) => setResetBaselineOnAdd(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-700 text-cyan-500"
                />
                <label htmlFor="resetBaseline" className="text-slate-300">
                  Establish new clean AI baseline for this replacement component
                </label>
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowCompModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
                >
                  Save Component
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Water Exposure Modal */}
      {showWaterModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-white text-base">Record Water Exposure ({activeVehicleId})</h3>
            <form onSubmit={handleAddWaterExposure} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Exposure Type</label>
                <select
                  value={exposureType}
                  onChange={(e) => setExposureType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="PRESSURE_WASH">High-Pressure Wash</option>
                  <option value="HEAVY_RAIN">Heavy Monsoon Rain Ride</option>
                  <option value="WATERLOGGED_ROAD">Waterlogged Street Puddle Crossing</option>
                  <option value="SUBMERSION_TEST">Service Facility Submersion/Spray Test</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Severity Level</label>
                <select
                  value={severityLevel}
                  onChange={(e) => setSeverityLevel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="LOW">Low (Light spray)</option>
                  <option value="MODERATE">Moderate (Standard wash/rain)</option>
                  <option value="HIGH">High (Deep puddle / high pressure)</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Duration (minutes)</label>
                <input
                  type="number"
                  value={exposureDuration}
                  onChange={(e) => setExposureDuration(parseInt(e.target.value) || 15)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Technician Notes</label>
                <textarea
                  placeholder="Notes on wash bay, drying time, or moisture status..."
                  value={waterNotes}
                  onChange={(e) => setWaterNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white h-20"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowWaterModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium"
                >
                  Save Exposure Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Log Service Modal */}
      {showServiceModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-white text-base">Log Maintenance / Service ({activeVehicleId})</h3>
            <form onSubmit={handleAddService} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Service Type</label>
                <select
                  value={serviceType}
                  onChange={(e) => setServiceType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                >
                  <option value="ROUTINE_MAINTENANCE">Routine 5,000 km Maintenance</option>
                  <option value="BATTERY_INSPECTION">BMS & Battery Cell Inspection</option>
                  <option value="COOLING_SYSTEM_SERVICE">Cooling Loop / Radiator Flush</option>
                  <option value="BRAKE_TIRE_SERVICE">Brake Pads & Tire Rotation</option>
                  <option value="MOTOR_INVERTER_CHECK">Motor & Inverter Diagnostics</option>
                </select>
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Description</label>
                <input
                  type="text"
                  placeholder="Summary of service work done..."
                  value={serviceDesc}
                  onChange={(e) => setServiceDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Odometer (km)</label>
                <input
                  type="number"
                  value={odometerKm}
                  onChange={(e) => setOdometerKm(parseInt(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Technician Notes</label>
                <textarea
                  placeholder="Detailed notes from service bay..."
                  value={techNotes}
                  onChange={(e) => setTechNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white h-16"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowServiceModal(false)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium"
                >
                  Save Service Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
