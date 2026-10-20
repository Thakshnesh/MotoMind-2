import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  AlertOctagon,
  CheckCircle,
  Brain,
  Info,
  Car,
  Bike
} from 'lucide-react';
import { ModelStatus, AnomalyEvent, HealthAssessment, TelemetryData } from '../types';
import { api } from '../api/client';

interface AiIntelligencePageProps {
  telemetry: TelemetryData | null;
  health: HealthAssessment | null;
  activeVehicleId?: string;
}

export const AiIntelligencePage: React.FC<AiIntelligencePageProps> = ({
  telemetry,
  health,
  activeVehicleId = 'E2W-SCOOT-01'
}) => {
  const is4W = activeVehicleId.includes('4W') || telemetry?.vehicle_type === 'four_wheeler';
  const vehicleType = is4W ? 'four_wheeler' : 'two_wheeler';

  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [events, setEvents] = useState<AnomalyEvent[]>([]);
  const [training, setTraining] = useState<boolean>(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);
  const [sampleCount, setSampleCount] = useState<number>(600);

  const fetchStatusAndEvents = useCallback(() => {
    api.getModelStatus(vehicleType, activeVehicleId).then(setModelStatus).catch(() => {});
    api.getAnomalyEvents(activeVehicleId).then(setEvents).catch(() => {});
  }, [vehicleType, activeVehicleId]);

  useEffect(() => {
    fetchStatusAndEvents();
  }, [fetchStatusAndEvents]);

  const handleTrainBaseline = async () => {
    setTraining(true);
    setTrainMessage(null);
    try {
      const res = await api.trainModel(vehicleType, sampleCount, 0.03);
      setTrainMessage(`Model baseline for ${is4W ? 'Four-Wheeler' : 'Two-Wheeler'} successfully trained with ${res.training_sample_count} samples. Filtered ${res.contaminated_samples_filtered} edge/fault samples.`);
      fetchStatusAndEvents();
    } catch {
      setTrainMessage('Model training failed.');
    } finally {
      setTraining(false);
    }
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await api.acknowledgeEvent(id);
      fetchStatusAndEvents();
    } catch {}
  };

  const currentScore = health?.anomaly_score ?? 0.05;
  const isOutlier = currentScore >= 0.65;
  const triggeredDeviations = health?.triggered_values?.ml_deviations || {};

  return (
    <div className="space-y-6">
      {/* Model Overview & Training Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Model Status Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Brain className="w-5 h-5 text-indigo-400" />
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-white text-sm">Self-Learning Isolation Forest Engine</h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-cyan-300 border border-cyan-800 flex items-center gap-1">
                    {is4W ? <Car className="w-3 h-3 text-cyan-400" /> : <Bike className="w-3 h-3 text-emerald-400" />}
                    {is4W ? 'Four-Wheeler Isolation Forest' : 'Two-Wheeler Isolation Forest'}
                  </span>
                </div>
                <p className="text-xs text-slate-400">Independent multivariate statistical baseline per vehicle class (scikit-learn)</p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
              {modelStatus?.operational_state || 'ACTIVE'}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Training Samples</span>
              <span className="text-lg font-bold text-white mt-0.5 block">
                {modelStatus?.training_sample_count || 600}
              </span>
              <span className="text-[10px] text-emerald-400">Synthetic Normal</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Contamination Filtered</span>
              <span className="text-lg font-bold text-amber-400 mt-0.5 block">
                {modelStatus?.contaminated_samples_filtered || 0}
              </span>
              <span className="text-[10px] text-slate-500">Safeguard Excluded</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Feature Dimension</span>
              <span className="text-lg font-bold text-cyan-400 mt-0.5 block">
                {modelStatus?.features_used?.length || (is4W ? 8 : 7)}
              </span>
              <span className="text-[10px] text-slate-500">Scaled Vectors</span>
            </div>

            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">Last Trained At</span>
              <span className="text-xs font-mono font-semibold text-slate-300 mt-1 block truncate">
                {modelStatus?.last_trained_at ? new Date(modelStatus.last_trained_at).toLocaleTimeString() : 'Baseline Staged'}
              </span>
              <span className="text-[10px] text-slate-500">{activeVehicleId}</span>
            </div>
          </div>

          {/* Features in Model Vector */}
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 mb-4">
            <span className="text-[11px] font-semibold text-slate-400 block mb-1.5">
              Monitored Feature Vector ({is4W ? '8 Dimensions with Coolant Loop' : '7 Dimensions Air-Cooled'}):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {modelStatus?.features_used?.map((feat) => (
                <span key={feat} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700/80 text-[11px] font-mono text-slate-300">
                  {feat}
                </span>
              ))}
            </div>
          </div>

          {/* Train Button with Safeguards Explanation */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Baseline Samples:</span>
              <select
                value={sampleCount}
                onChange={(e) => setSampleCount(parseInt(e.target.value))}
                className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-white"
              >
                <option value="400">400 samples</option>
                <option value="600">600 samples</option>
                <option value="1000">1000 samples</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              {trainMessage && <span className="text-xs text-cyan-400 font-medium">{trainMessage}</span>}
              <button
                onClick={handleTrainBaseline}
                disabled={training}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-xs flex items-center gap-1.5 shadow-lg shadow-indigo-600/20 transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${training ? 'animate-spin' : ''}`} />
                {training ? 'Fitting Model...' : `Retrain ${is4W ? '4W' : '2W'} Baseline`}
              </button>
            </div>
          </div>
        </div>

        {/* Real-Time Anomaly Scoring & Attribution Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white text-sm">Instant Anomaly Score</h3>
              <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                isOutlier ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
              }`}>
                {isOutlier ? 'OUTLIER DETECTED' : 'WITHIN BOUNDS'}
              </span>
            </div>

            <div className="text-center py-4">
              <span className={`text-4xl font-extrabold ${isOutlier ? 'text-rose-400' : 'text-emerald-400'}`}>
                {currentScore.toFixed(3)}
              </span>
              <span className="text-xs text-slate-500 block mt-1">Normalized Risk Index [0.0 - 1.0]</span>
            </div>

            {/* Gauge bar */}
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mb-4">
              <div
                className={`h-full transition-all duration-300 ${
                  currentScore > 0.8 ? 'bg-rose-500' : currentScore > 0.65 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(0, currentScore * 100))}%` }}
              />
            </div>

            {/* Feature Attribution (Explainability) */}
            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
              <span className="font-semibold text-slate-300 block mb-1.5">Explainability (Z-Score Deviation):</span>
              {Object.keys(triggeredDeviations).length > 0 ? (
                <div className="space-y-1.5">
                  {Object.entries(triggeredDeviations).map(([feat, details]: [string, any]) => (
                    <div key={feat} className="flex justify-between items-center text-[11px] bg-slate-900 px-2 py-1 rounded">
                      <span className="text-slate-300 font-mono">{feat}</span>
                      <span className="text-rose-400 font-semibold font-mono">
                        {details.direction} (z={details.z_score})
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-slate-500 italic">
                  All monitored dimensions reside inside the baseline 99% confidence ellipsoid for {is4W ? '4W' : '2W'}.
                </p>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500 leading-tight">
            *Safeguard active: Known fault injections and extreme sensor trips are barred from entering the training baseline.
          </div>
        </div>
      </div>

      {/* Anomaly Event Log Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <AlertOctagon className="w-5 h-5 text-rose-400" />
            <h3 className="font-semibold text-white text-sm">Detected Anomaly & Violation Log ({activeVehicleId})</h3>
          </div>
          <span className="text-xs text-slate-400">{events.length} recorded events</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Vehicle</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Title & Description</th>
                <th className="py-2.5 px-3">Score</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 italic">
                    No anomalies logged yet for {activeVehicleId}. Use Live Monitoring to inject a test fault.
                  </td>
                </tr>
              ) : (
                events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[10px] text-cyan-400">
                      {ev.vehicle_id || activeVehicleId}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ev.severity === 'CRITICAL'
                          ? 'bg-rose-950 text-rose-300 border border-rose-800'
                          : 'bg-amber-950 text-amber-300 border border-amber-800'
                      }`}>
                        {ev.severity}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">{ev.category}</td>
                    <td className="py-2.5 px-3 max-w-xs truncate">
                      <div className="font-medium text-slate-100">{ev.title}</div>
                      <div className="text-[11px] text-slate-400 truncate">{ev.description}</div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-cyan-400">{ev.anomaly_score.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right">
                      {ev.acknowledged ? (
                        <span className="text-[11px] text-emerald-400 flex items-center justify-end gap-1">
                          <CheckCircle className="w-3.5 h-3.5" /> Ack
                        </span>
                      ) : (
                        <button
                          onClick={() => handleAcknowledge(ev.id)}
                          className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-medium transition"
                        >
                          Acknowledge
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Limitations Disclaimer Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200 block mb-1">Self-Learning Machine Learning Limitations Statement</strong>
          The Isolation Forest model is an unsupervised anomaly detector trained on synthetic simulation distributions specifically tailored for {is4W ? 'electric four-wheelers (400V dual-motor)' : 'electric two-wheelers (52V commuter)'}.
          An outlier score indicates a statistical deviation from the learned baseline profile, but does not constitute a verified mechanical failure diagnosis.
          In real-world EV deployment, vehicle-specific calibration across varied ambient seasons, battery aging curves (SOH degradation), and physical road dyno testing are strictly required before enabling autonomous decision actions.
        </div>
      </div>
    </div>
  );
};
