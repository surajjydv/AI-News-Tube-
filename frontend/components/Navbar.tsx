"use client";

import React from "react";
import { useStudioStore } from "@/lib/store";
import { Wand2, Calendar, BarChart3, Palette, CheckCircle2, AlertCircle, Key, Radio, Tv } from "lucide-react";

const YouTubeLogoIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
);

export const Navbar: React.FC = () => {
  const { accounts, activeAccountId, setActiveAccount, toggleAccountConnect, activeTab, setActiveTab } = useStudioStore();
  const activeAccount = accounts.find((a) => a.id === activeAccountId) || accounts[0];

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-slate-200 px-4 md:px-8 py-3 shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-start">
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => setActiveTab("youtube")}>
            <div className="h-8 w-8 rounded-sm bg-red-600 flex items-center justify-center shadow-xs">
              <Tv className="w-4 h-4 text-white stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-lg tracking-tight text-slate-950 flex items-center">
                  NEWS<span className="text-red-600">TUBE</span>
                </span>
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm bg-red-50 text-[10px] font-bold text-red-700 border border-red-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
                  LIVE 24/7
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-semibold tracking-tight">AI Broadcast Studio • @SRJUNDERRATED</p>
            </div>
          </div>

          {/* Account Switcher */}
          <div className="flex items-center gap-2 bg-slate-100 border border-slate-200 rounded-sm px-2.5 py-1.5">
            <img
              src={activeAccount.avatarUrl}
              alt={activeAccount.displayName}
              className="w-6 h-6 rounded-sm object-cover border border-slate-300"
            />
            <select
              value={activeAccountId}
              onChange={(e) => setActiveAccount(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-800 outline-none cursor-pointer pr-1"
            >
              {accounts.map((acc) => (
                <option key={acc.id} value={acc.id} className="bg-white text-slate-800">
                  @{acc.username} ({acc.category})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-sm border border-slate-200 overflow-x-auto max-w-full">
          <button
            onClick={() => setActiveTab("youtube")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors whitespace-nowrap ${
              activeTab === "youtube"
                ? "bg-red-600 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            <YouTubeLogoIcon className="w-3.5 h-3.5" />
            YouTube Studio
          </button>

          <button
            onClick={() => setActiveTab("studio")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors whitespace-nowrap ${
              activeTab === "studio"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            <Wand2 className="w-3.5 h-3.5" />
            Content Studio
          </button>

          <button
            onClick={() => setActiveTab("platforms")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors whitespace-nowrap ${
              activeTab === "platforms"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-700 hover:text-slate-900 hover:bg-slate-200/80 font-bold"
            }`}
          >
            <Key className="w-3.5 h-3.5 text-amber-500" />
            API Keys & Platforms
          </button>

          <button
            onClick={() => setActiveTab("schedule")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors whitespace-nowrap ${
              activeTab === "schedule"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Scheduler
          </button>

          <button
            onClick={() => setActiveTab("analytics")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors whitespace-nowrap ${
              activeTab === "analytics"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Analytics
          </button>

          <button
            onClick={() => setActiveTab("brandkit")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors whitespace-nowrap ${
              activeTab === "brandkit"
                ? "bg-slate-900 text-white shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            Brand Kit
          </button>
        </nav>

        {/* Status / Connect */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setActiveTab("platforms")}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-sm border border-slate-300 bg-white hover:bg-slate-100 text-xs font-medium text-slate-700 shadow-2xs"
            title="Configure platform API keys"
          >
            <Key className="w-3.5 h-3.5 text-amber-600" />
            Keys & Config
          </button>

          <button
            onClick={() => toggleAccountConnect(activeAccount.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-sm border text-xs font-medium transition-colors ${
              activeAccount.isConnected
                ? "bg-emerald-50 border-emerald-300 text-emerald-700 hover:bg-emerald-100"
                : "bg-amber-50 border-amber-300 text-amber-700 hover:bg-amber-100"
            }`}
          >
            {activeAccount.isConnected ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Connected (@{activeAccount.username})
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                Connect Channel
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
