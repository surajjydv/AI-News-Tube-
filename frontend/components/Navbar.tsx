"use client";

import React from "react";
import { useStudioStore } from "@/lib/store";
import { Wand2, Calendar, BarChart3, Palette, CheckCircle2, AlertCircle } from "lucide-react";

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
    <rect x="2" y="2" width="20" height="20" rx="1" ry="1"></rect>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
  </svg>
);

const YouTubeLogoIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
);

export const Navbar: React.FC = () => {
  const { accounts, activeAccountId, setActiveAccount, toggleAccountConnect, activeTab, setActiveTab } = useStudioStore();
  const activeAccount = accounts.find((a) => a.id === activeAccountId) || accounts[0];

  return (
    <header className="sticky top-0 z-50 w-full glass-panel-premium border-b border-slate-800 px-4 md:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => setActiveTab("studio")}>
            <div className="h-8 w-8 rounded-sm bg-rose-600 flex items-center justify-center">
              <InstagramIcon className="w-4 h-4 text-white stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-white">AutoInsta</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">Prompt-to-Publish Studio</p>
            </div>
          </div>

          {/* Account Switcher */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-sm px-2.5 py-1.5">
            <img
              src={activeAccount.avatarUrl}
              alt={activeAccount.displayName}
              className="w-6 h-6 rounded-sm object-cover border border-slate-700"
            />
            <select
              value={activeAccountId}
              onChange={(e) => setActiveAccount(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-200 outline-none cursor-pointer pr-1"
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
        <nav className="flex items-center gap-1 bg-slate-900 p-1 rounded-sm border border-slate-800">
          <button
            onClick={() => setActiveTab("studio")}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeTab === "studio"
                ? "bg-rose-600 text-white"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Wand2 className="w-3.5 h-3.5" />
            Studio
          </button>

          <button
            onClick={() => setActiveTab("schedule")}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeTab === "schedule"
                ? "bg-rose-600 text-white"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Scheduler
          </button>

          <button
            onClick={() => setActiveTab("analytics")}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeTab === "analytics"
                ? "bg-rose-600 text-white"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Analytics
          </button>

          <button
            onClick={() => setActiveTab("youtube")}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeTab === "youtube"
                ? "bg-red-600 text-white"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
            }`}
          >
            <YouTubeLogoIcon className="w-3.5 h-3.5 text-white" />
            YouTube Studio
          </button>

          <button
            onClick={() => setActiveTab("brandkit")}
            className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeTab === "brandkit"
                ? "bg-rose-600 text-white"
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
            className={`flex items-center gap-2 px-3 py-1.5 rounded-sm border text-xs font-medium transition-colors ${
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
