"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { X, Calendar, Clock, Repeat, Sparkles, CheckCircle2 } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SchedulerModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { scheduleCurrentAsset, generatedAsset, accounts, activeAccountId } = useStudioStore();
  const [scheduledDate, setScheduledDate] = useState("2026-10-10");
  const [scheduledTime, setScheduledTime] = useState("18:30");
  const [recurrence, setRecurrence] = useState<"none" | "daily" | "weekly" | "monthly">("none");
  const [confirmed, setConfirmed] = useState(false);

  const activeAccount = accounts.find((a) => a.id === activeAccountId) || accounts[0];

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const isoString = new Date(`${scheduledDate}T${scheduledTime}:00`).toISOString();
    scheduleCurrentAsset(isoString, recurrence);
    setConfirmed(true);
    setTimeout(() => {
      setConfirmed(false);
      onClose();
    }, 1200);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-slate-700/80 shadow-2xl overflow-hidden p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Schedule Automated Publish</h3>
            <p className="text-xs text-slate-400">Publish to @{activeAccount.username} automatically via IG Graph API</p>
          </div>
        </div>

        {/* AI Optimal Timing Advice */}
        <div className="bg-gradient-to-r from-pink-500/10 to-amber-500/10 border border-pink-500/20 rounded-xl p-3 mb-5 flex items-start gap-2.5">
          <Sparkles className="w-4 h-4 text-pink-400 mt-0.5 shrink-0" />
          <div className="text-xs">
            <span className="font-bold text-pink-300">AI Smart Timing Recommendation:</span>
            <p className="text-slate-300 mt-0.5">
              Based on your audience analytics, post timing at <strong className="text-white">Friday 6:30 PM</strong> yields +34% higher reel retention.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Date & Time Picker */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-pink-400" />
                Publish Date
              </label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-pink-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-pink-400" />
                Publish Time
              </label>
              <input
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-pink-500"
                required
              />
            </div>
          </div>

          {/* Recurrence Dropdown */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Repeat className="w-3.5 h-3.5 text-pink-400" />
              Recurrence Automation
            </label>
            <select
              value={recurrence}
              onChange={(e) => setRecurrence(e.target.value as any)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-pink-500 cursor-pointer"
            >
              <option value="none">One-Time Publish</option>
              <option value="daily">Daily Evergreen Cycle</option>
              <option value="weekly">Weekly Prime Cadence</option>
              <option value="monthly">Monthly Campaign Push</option>
            </select>
          </div>

          {/* Action Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={confirmed}
              className="w-full py-3 px-4 rounded-xl font-bold text-xs bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 text-white shadow-lg shadow-pink-500/25 flex items-center justify-center gap-2 transition-all"
            >
              {confirmed ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Scheduled Successfully!
                </>
              ) : (
                "Confirm & Add to Auto-Publish Queue"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
