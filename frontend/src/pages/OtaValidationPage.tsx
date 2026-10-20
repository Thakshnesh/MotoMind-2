import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Play,
  RotateCcw,
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Layers,
  ArrowRight,
  Info,
  Bug,
  FileText,
  Car,
  Bike
} from 'lucide-react';
import { SoftwareVersion, ValidationRun } from '../types';
import { api } from '../api/client';

interface OtaValidationPageProps {
  activeVehicleId?: string;
}

export const OtaValidationPage: React.FC<OtaValidationPageProps> = ({
  activeVehicleId = 'E2W-SCOOT-01'
}) => {
  const defaultIs4W = activeVehicleId.includes('4W');
  const [selectedVehicleType, setSelectedVehicleType] = useState<string>(
    defaultIs4W ? 'four_wheeler' : 'two_wheeler'
  );

  const [versions, setVersions] = useState<SoftwareVersion[]>([]);
  const [selectedRefId, setSelectedRefId] = useState<number | null>(null);
  const [selectedCandId, setSelectedCandId] = useState<number | null>(null);
  const [activeRun, setActiveRun] = useState<ValidationRun | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [pastRuns, setPastRuns] = useState<ValidationRun[]>([]);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Sync selected suite if activeVehicleId changes
  useEffect(() => {
    setSelectedVehicleType(activeVehicleId.includes('4W') ? 'four_wheeler' : 'two_wheeler');
  }, [activeVehicleId]);

  const loadData = () => {
    api.getSoftwareVersions(selectedVehicleType).then((v) => {
      setVersions(v);
      const ref = v.find((x) => x.is_active_reference) || v[0];
      const cand = v.find((x) => x.version_string.includes('regressed')) || v[1];
      if (ref) setSelectedRefId(ref.id);
      if (cand) setSelectedCandId(cand.id);
    }).catch(() => {});

    api.getValidationRuns(selectedVehicleType).then((runs) => {
      setPastRuns(runs);
      if (runs.length > 0 && !activeRun) {
        api.getValidationRun(runs[0].id).then(setActiveRun).catch(() => {});
      }
    }).catch(() => {});
  };

  useEffect(() => {
    loadData();
  }, [selectedVehicleType]);

  const handleStartCustomRun = async () => {
    if (!selectedRefId || !selectedCandId) return;
    setIsRunning(true);
    setStatusMessage(`Executing virtual BMS test harness for ${selectedVehicleType === 'four_wheeler' ? 'Four-Wheeler' : 'Two-Wheeler'}...`);
    try {
      const summary = await api.startValidationRun(
        selectedRefId,
        selectedCandId,
        selectedVehicleType,
        activeVehicleId
      );
      setActiveRun(summary);
      setStatusMessage(`Validation completed: ${summary.overall_result}`);
      setTimeout(() => setStatusMessage(null), 3000);
      api.getValidationRuns(selectedVehicleType).then(setPastRuns).catch(() => {});
    } catch (e) {
      setStatusMessage('Validation run failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunRegressionDemo = async () => {
    setIsRunning(true);
    const label = selectedVehicleType === 'four_wheeler'
      ? '4W Sedan regression (high-temp cutoff bypass & HVIL safety)'
      : '2W Scooter regression (thermal cutoff bypass)';
    setStatusMessage(`Running Deliberate Regression Demonstration: ${label}...`);
    try {
      const summary = await api.runDemoRegression(selectedVehicleType);
      setActiveRun(summary);
      setStatusMessage(`Demo Completed: Deliberate regression caught -> BLOCK for ${selectedVehicleType}`);
      setTimeout(() => setStatusMessage(null), 4000);
      api.getValidationRuns(selectedVehicleType).then(setPastRuns).catch(() => {});
    } catch (e) {
      setStatusMessage('Demo execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunPassingDemo = async () => {
    setIsRunning(true);
    const label = selectedVehicleType === 'four_wheeler'
      ? 'Clean 4W Candidate (All 12 400V high-voltage assertions)'
      : 'Clean 2W Candidate (All 12 commuter safety assertions)';
    setStatusMessage(`Running Clean Passing Candidate: ${label}...`);
    try {
      const summary = await api.runDemoPassing(selectedVehicleType);
      setActiveRun(summary);
      setStatusMessage(`Validation Completed: All 12 Safety Assertions Passed -> PASS for ${selectedVehicleType}`);
      setTimeout(() => setStatusMessage(null), 4000);
      api.getValidationRuns(selectedVehicleType).then(setPastRuns).catch(() => {});
    } catch (e) {
      setStatusMessage('Demo execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSelectRun = async (id: string) => {
    try {
      const run = await api.getValidationRun(id);
      setActiveRun(run);
    } catch (e) {}
  };

  const isCurrent4W = selectedVehicleType === 'four_wheeler';

  return (
    <div className="space-y-6">
      {/* Top Banner: Built-in Demonstrations & Version Selection */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-purple-500/20 text-purple-400 rounded-xl">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-white text-base">Virtual OTA Firmware Testbed</h3>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-cyan-300 border border-slate-700">
                  Target: {isCurrent4W ? 'Four-Wheeler Suite' : 'Two-Wheeler Suite'}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Isolated virtual validation environment. Evaluates candidate firmware profiles against certified safety baselines.
              </p>
            </div>
          </div>

          {/* Vehicle Category Switcher Buttons */}
          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setSelectedVehicleType('two_wheeler')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                !isCurrent4W ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Bike className="w-3.5 h-3.5" />
              Two-Wheeler Suite
            </button>
            <button
              onClick={() => setSelectedVehicleType('four_wheeler')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                isCurrent4W ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Car className="w-3.5 h-3.5" />
              Four-Wheeler Suite
            </button>
          </div>
        </div>

        {/* Quick Demo Launchers */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
          <div className="text-xs text-slate-400">
            Automated virtual scenarios for <strong>{isCurrent4W ? '4W 400V Sedan' : '2W 52V Scooter'}</strong>:
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleRunRegressionDemo}
              disabled={isRunning}
              className="px-3.5 py-2 bg-rose-950/80 hover:bg-rose-900 text-rose-200 border border-rose-800 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
              title={`Runs reference vs regressed candidate for ${selectedVehicleType}`}
            >
              <Bug className="w-3.5 h-3.5 text-rose-400" />
              Run Deliberate Regression Demo (BLOCK)
            </button>

            <button
              onClick={handleRunPassingDemo}
              disabled={isRunning}
              className="px-3.5 py-2 bg-emerald-950/80 hover:bg-emerald-900 text-emerald-200 border border-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shadow-sm"
              title={`Runs clean candidate satisfying all 12 assertions for ${selectedVehicleType}`}
            >
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              Run Clean Candidate (PASS)
            </button>
          </div>
        </div>

        {/* Custom Version Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-800 mt-4">
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Reference Baseline Firmware ({isCurrent4W ? '4W' : '2W'})
            </label>
            <select
              value={selectedRefId || ''}
              onChange={(e) => setSelectedRefId(parseInt(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white"
            >
              {versions.filter((v) => v.version_type === 'REFERENCE' || v.is_active_reference).map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_string} (Certified Reference)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Candidate Firmware Update ({isCurrent4W ? '4W' : '2W'})
            </label>
            <select
              value={selectedCandId || ''}
              onChange={(e) => setSelectedCandId(parseInt(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white"
            >
              {versions.filter((v) => !v.is_active_reference).map((v) => (
                <option key={v.id} value={v.id}>
                  {v.version_string} ({v.version_type})
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col justify-end">
            <button
              onClick={handleStartCustomRun}
              disabled={isRunning}
              className="w-full py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition shadow-lg shadow-purple-600/20 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              {isRunning ? 'Running Test Suite...' : `Execute Full 12-Test Suite (${isCurrent4W ? '4W' : '2W'})`}
            </button>
          </div>
        </div>

        {statusMessage && (
          <div className="mt-3 text-xs text-cyan-400 font-medium animate-pulse text-center">
            {statusMessage}
          </div>
        )}
      </div>

      {/* Main Validation Report View */}
      {activeRun && (
        <div className="space-y-6">
          {/* Summary Metric Ribbon */}
          <div className={`p-5 rounded-2xl border transition-all ${
            activeRun.overall_result === 'PASS'
              ? 'bg-emerald-950/20 border-emerald-800/80 text-emerald-200'
              : 'bg-rose-950/25 border-rose-800/80 text-rose-200'
          }`}>
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded-full ${
                    activeRun.overall_result === 'PASS'
                      ? 'bg-emerald-900 text-emerald-300 border border-emerald-700'
                      : 'bg-rose-900 text-rose-300 border border-rose-700'
                  }`}>
                    VALIDATION VERDICT: {activeRun.overall_result}
                  </span>
                  <span className="text-xs text-slate-400">
                    Run ID: <strong className="font-mono text-slate-200">{activeRun.id}</strong>
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-900 text-cyan-300 font-mono">
                    {activeRun.target_vehicle_type || selectedVehicleType}
                  </span>
                </div>
                <div className="text-sm font-semibold text-white mt-2">
                  Comparing Reference <strong>{activeRun.reference_version_string}</strong> against Candidate <strong>{activeRun.candidate_version_string}</strong>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <a
                  href={`/api/export/ota-report/${activeRun.id}`}
                  download
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download JSON Report
                </a>
              </div>
            </div>

            {/* Decision explanation */}
            <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs text-slate-300 mb-4">
              <strong className="text-slate-100 block mb-1">Validation Analysis & Reason:</strong>
              {activeRun.block_reason || "All deterministic assertions and safety bounds successfully verified. No regression against reference envelope detected."}
            </div>

            {/* Scorecard */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center text-xs">
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400 text-[10px] block">Total Scenarios</span>
                <span className="text-lg font-bold text-white mt-0.5 block">{activeRun.total_tests}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-emerald-400 text-[10px] block">Passed</span>
                <span className="text-lg font-bold text-emerald-400 mt-0.5 block">{activeRun.passed_tests}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-rose-400 text-[10px] block">Failed Assertions</span>
                <span className="text-lg font-bold text-rose-400 mt-0.5 block">{activeRun.failed_tests}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-amber-400 text-[10px] block">Regression Flag</span>
                <span className={`text-lg font-bold mt-0.5 block ${activeRun.regression_detected ? 'text-amber-400' : 'text-slate-400'}`}>
                  {activeRun.regression_detected ? 'DETECTED' : 'NONE'}
                </span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-cyan-400 text-[10px] block">Suite Coverage</span>
                <span className="text-lg font-bold text-cyan-400 mt-0.5 block">{activeRun.coverage_percentage}%</span>
              </div>
            </div>
          </div>

          {/* Test Scenarios Detailed Results Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="font-semibold text-white text-sm mb-4">
              Detailed Test Scenarios & Assertions Matrix ({activeRun.target_vehicle_type || selectedVehicleType})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Scenario ID</th>
                    <th className="py-2.5 px-3">Name & Category</th>
                    <th className="py-2.5 px-3">Severity</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Expected Behavior</th>
                    <th className="py-2.5 px-3">Actual Candidate Response</th>
                    <th className="py-2.5 px-3 text-right">Regression</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {activeRun.results?.map((item) => (
                    <tr
                      key={item.scenario_id}
                      className={`hover:bg-slate-800/40 transition ${
                        item.status === 'FAIL' ? 'bg-rose-950/20' : ''
                      }`}
                    >
                      <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                        {item.scenario_id}
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="font-semibold text-slate-200">{item.scenario_name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{item.category}</div>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-slate-800 text-slate-300'
                        }`}>
                          {item.severity}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.status === 'PASS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'
                        }`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-[11px] text-slate-400 max-w-xs">{item.expected_behavior}</td>
                      <td className="py-2.5 px-3 text-[11px] font-medium text-slate-200 max-w-xs">{item.actual_behavior}</td>
                      <td className="py-2.5 px-3 text-right">
                        {item.is_regression ? (
                          <span className="text-[10px] font-bold text-rose-400 bg-rose-950 px-2 py-0.5 rounded border border-rose-800">
                            YES (FAIL)
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-500">NO</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Historical Runs List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h3 className="font-semibold text-white text-sm mb-3">Historical Validation Runs</h3>
        <div className="divide-y divide-slate-800/80 text-xs">
          {pastRuns.map((r) => (
            <div
              key={r.id}
              onClick={() => handleSelectRun(r.id)}
              className="py-3 flex items-center justify-between hover:bg-slate-800/50 px-3 rounded-lg cursor-pointer transition"
            >
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  r.overall_result === 'PASS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'
                }`}>
                  {r.overall_result}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-200 font-semibold">{r.id}</span>
                    <span className="text-[10px] font-mono text-cyan-400 px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800">
                      {r.target_vehicle_type || 'two_wheeler'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Ref: {r.reference_version_string} vs Cand: {r.candidate_version_string}
                  </div>
                </div>
              </div>

              <div className="text-right text-slate-400 text-[11px]">
                <div>{new Date(r.timestamp).toLocaleString()}</div>
                <div className="text-slate-500">{r.passed_tests}/{r.total_tests} passed • {r.execution_duration_sec}s</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* OTA Virtual Safety Disclaimer */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200 block mb-1">OTA Virtual Testing Boundary Statement</strong>
          This software update validation module executes exclusively in a virtual simulated ECU/BMS test harness for both Two-Wheeler and Four-Wheeler profiles.
          It does not attempt to flash real microcontroller firmware or deploy remote binary payloads over the air.
          A simulation verdict of PASS certifies compatibility with configured automated unit/integration test specifications only, and does not constitute real-vehicle physical safety compliance or road certification.
        </div>
      </div>
    </div>
  );
};
