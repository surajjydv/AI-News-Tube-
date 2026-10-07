"use client";

import React from "react";
import { useStudioStore } from "@/lib/store";
import { Sparkles, Calendar, BarChart3, Palette, CheckCircle2, AlertCircle } from "lucide-react";

const InstagramIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
  </svg>
);

export const Navbar: React.FC = () => {
  const { accounts, activeAccountId, setActiveAccount, toggleAccountConnect, activeTab, setActiveTab } = useStudioStore();
  const activeAccount = accounts.find((a) => a.id === activeAccountId) || accounts[0];

  return (
    <header className="sticky top-0 z-50 w-full glass-panel border-b border-slate-800/80 px-4 md:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => setActiveTab("studio")}>
            <div className="h-10 w-10 rounded-xl bg-ig-gradient flex items-center justify-center shadow-lg shadow-pink-500/20">
              <InstagramIcon className="w-5 h-5 text-white stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-lg tracking-tight text-white">AutoInsta</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">
                  B2B Pro
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Prompt-to-Publish AI Studio</p>
            </div>
          </div>

          {/* Account Switcher for B2B Agencies */}
          <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-xl px-3 py-1.5 shadow-inner">
            <img
              src={activeAccount.avatarUrl}
              alt={activeAccount.displayName}
              className="w-7 h-7 rounded-full object-cover ring-2 ring-pink-500/40"
            />
            <select
              value={activeAccountId}
              onChange={(e) => setActiveAccount(e.target.value)}
              className="bg-transparent text-sm font-semibold text-slate-200 outline-none cursor-pointer pr-2"
            >
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id} className="bg-slate-900 text-slate-100">
                  @{acc.username} ({acc.category})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("studio")}
            className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === "studio"
                ? "bg-gradient-to-r from-pink-500 to-rose-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            AI Studio
          </button>

          <button
            onClick={() => setActiveTab("schedule")}
            className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === "schedule"
                ? "bg-gradient-to-r from-pink-500 to-rose-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Scheduler
          </button>

          <button
            onClick={() => setActiveTab("analytics")}
            className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === "analytics"
                ? "bg-gradient-to-r from-pink-500 to-rose-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Analytics
          </button>

          <button
            onClick={() => setActiveTab("brandkit")}
            className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeTab === "brandkit"
                ? "bg-gradient-to-r from-pink-500 to-rose-600 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            Brand Kit
          </button>
        </nav>

        {/* IG OAuth Connect / Status */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => toggleAccountConnect(activeAccount.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
              activeAccount.isConnected
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                : "bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
            }`}
          >
            {activeAccount.isConnected ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                IG Connected (@{activeAccount.username})
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                Connect Instagram
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
