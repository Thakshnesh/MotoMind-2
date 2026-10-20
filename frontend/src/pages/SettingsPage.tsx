import React, { useState } from 'react';
import {
  Sliders,
  FileSpreadsheet,
  Database,
  Info
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [maxBattTemp, setMaxBattTemp] = useState<number>(48.0);
  const [critBattTemp, setCritBattTemp] = useState<number>(55.0);
  const [maxMotorTemp, setMaxMotorTemp] = useState<number>(85.0);
  const [maxCurrent, setMaxCurrent] = useState<number>(65.0);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const handleSaveConfig = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveMsg('Configuration updated in local runtime session.');
    setTimeout(() => setSaveMsg(null), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Safety Thresholds Configuration Form */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center space-x-2 mb-4">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="font-semibold text-white text-sm">Configurable EV Safety & Thermal Thresholds</h3>
            <p className="text-xs text-slate-400">Configurable profile parameters for Electric Two-Wheeler and Four-Wheeler physics evaluation</p>
          </div>
        </div>

        <form onSubmit={handleSaveConfig} className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="text-slate-400 block mb-1 font-medium">
              Battery Warning Temperature (°C)
            </label>
            <input
              type="number"
              step="0.5"
              value={maxBattTemp}
              onChange={(e) => setMaxBattTemp(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Nominal threshold before thermal derating flags</span>
          </div>

          <div>
            <label className="text-slate-400 block mb-1 font-medium">
              Battery Critical Cutoff Temperature (°C)
            </label>
            <input
              type="number"
              step="0.5"
              value={critBattTemp}
              onChange={(e) => setCritBattTemp(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Mandatory Emergency Cutoff assertion limit in BMS</span>
          </div>

          <div>
            <label className="text-slate-400 block mb-1 font-medium">
              Motor Stator Warning Temp (°C)
            </label>
            <input
              type="number"
              step="1"
              value={maxMotorTemp}
              onChange={(e) => setMaxMotorTemp(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Trigger threshold for motor thermal warnings</span>
          </div>

          <div>
            <label className="text-slate-400 block mb-1 font-medium">
              Rated Peak Discharge Current (Amps)
            </label>
            <input
              type="number"
              step="1"
              value={maxCurrent}
              onChange={(e) => setMaxCurrent(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-white"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">Overcurrent trip threshold for main contactor</span>
          </div>

          <div className="md:col-span-2 flex items-center justify-between pt-3 border-t border-slate-800">
            {saveMsg && <span className="text-xs text-emerald-400 font-medium">{saveMsg}</span>}
            <button
              type="submit"
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-semibold text-xs transition"
            >
              Save Parameters
            </button>
          </div>
        </form>
      </div>

      {/* Export & Data Management */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center space-x-2 mb-4">
          <Database className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="font-semibold text-white text-sm">Data Export & Diagnostic Telemetry Logs</h3>
            <p className="text-xs text-slate-400">Download captured time-series records for external post-processing</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-950 border border-slate-800">
          <div>
            <div className="text-xs font-semibold text-slate-200">Export Telemetry as CSV</div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Includes timestamped voltage, current, battery & motor temps, speed, and consumption.
            </p>
          </div>
          <a
            href="/api/export/telemetry-csv"
            download
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            Download CSV Log
          </a>
        </div>
      </div>

      {/* Unavailable External Services Clear Disclosure */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center space-x-2 mb-3">
          <Info className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-white text-sm">Hardware & Cloud Boundary Disclosures</h3>
        </div>

        <div className="space-y-2.5 text-xs text-slate-300">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <strong className="text-white block mb-0.5">Physical Sensor & CAN Bus Isolation</strong>
            This deployment is a self-contained prototype utilizing synthetic vehicle physics. No physical CAN transceiver, OBD-II dongle, or high-voltage wiring is attached.
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <strong className="text-white block mb-0.5">External Live Traffic & Cloud Maps</strong>
            Range calculations utilize physics-based coulomb counting and dynamic consumption math without external map API queries.
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <strong className="text-white block mb-0.5">Remote Firmware Flashing</strong>
            OTA testing takes place strictly in a virtual ECU/BMS mock environment. No remote firmware binaries are transmitted over the air to a physical vehicle.
          </div>
        </div>
      </div>
    </div>
  );
};
