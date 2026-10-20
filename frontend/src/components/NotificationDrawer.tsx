import React from 'react';
import { X, AlertTriangle, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { AnomalyEvent } from '../types';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  events: AnomalyEvent[];
  onAcknowledge: (id: number) => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  events,
  onAcknowledge
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col backdrop-blur-lg">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-cyan-400" />
          <h3 className="font-semibold text-white text-sm">System Alerts & Notifications</h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {events.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <CheckCircle className="w-10 h-10 mx-auto mb-2 text-slate-600" />
            <p className="text-sm font-medium">No active warnings or anomalies</p>
            <p className="text-xs text-slate-600 mt-1">Vehicle sub-systems operating within safe parameters.</p>
          </div>
        ) : (
          events.map((event) => {
            const isCritical = event.severity === 'CRITICAL';
            return (
              <div
                key={event.id}
                className={`p-3.5 rounded-xl border text-xs transition-all ${
                  isCritical
                    ? 'bg-rose-950/40 border-rose-800/80 text-rose-200'
                    : 'bg-amber-950/30 border-amber-800/60 text-amber-200'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px]">
                    {isCritical ? (
                      <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                    ) : (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    )}
                    <span>{event.severity}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400">{event.category}</span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div className="font-semibold text-slate-100 text-xs mt-1.5">{event.title}</div>
                <div className="text-slate-300 mt-1 text-[11px] leading-relaxed">{event.description}</div>

                {event.features_involved && Object.keys(event.features_involved).length > 0 && (
                  <div className="mt-2 bg-slate-950/50 p-2 rounded border border-slate-800 text-[10px] text-slate-400 font-mono">
                    {JSON.stringify(event.features_involved)}
                  </div>
                )}

                <div className="mt-3 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500">
                    {event.acknowledged ? '✓ Acknowledged' : '• Unacknowledged'}
                  </span>
                  {!event.acknowledged && (
                    <button
                      onClick={() => onAcknowledge(event.id)}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-[10px] transition"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="p-3 border-t border-slate-800 bg-slate-950 text-slate-500 text-[10px] text-center">
        Informational prototype alerts • Does not replace instrument cluster warnings
      </div>
    </div>
  );
};
