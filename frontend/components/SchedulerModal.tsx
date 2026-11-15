"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { X, Calendar, Clock, Repeat, CheckCircle2 } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SchedulerModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { scheduleCurrentAsset, accounts, activeAccountId } = useStudioStore();
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="bg-white w-full max-w-lg rounded-sm border border-slate-200 p-6 relative shadow-xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-sm text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="p-2 rounded-sm bg-slate-100 border border-slate-200 text-rose-600">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Schedule Automated Publish</h3>
            <p className="text-xs text-slate-500">Publish to @{activeAccount.username} automatically via IG Graph API</p>
          </div>
        </div>

        {/* Informational Timing Note */}
        <div className="bg-slate-50 border border-slate-200 rounded-sm p-3 mb-5 text-xs text-slate-600">
          Automated scheduling publishes directly to your connected social channels at the specified time.
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Date & Time Picker */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-rose-600" />
                Publish Date
              </label>
              <input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-sm p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-rose-600" />
                Publish Time
              </label>
              <input
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
                className="w-full bg-white border border-slate-300 rounded-sm p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
                required
              />
            </div>
          </div>

          {/* Recurrence Dropdown */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
              <Repeat className="w-3.5 h-3.5 text-rose-600" />
              Recurrence Automation
            </label>
            <select
              value={recurrence}
              onChange={(e) => setRecurrence(e.target.value as any)}
              className="w-full bg-white border border-slate-300 rounded-sm p-2 text-xs text-slate-800 focus:outline-none focus:border-rose-500 cursor-pointer"
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
              className="w-full py-2.5 px-4 rounded-sm font-semibold text-xs bg-rose-600 hover:bg-rose-700 text-white flex items-center justify-center gap-2 transition-colors shadow-xs"
            >
              {confirmed ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-200" />
                  Scheduled Successfully
                </>
              ) : (
                "Confirm & Add to Queue"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
