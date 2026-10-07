"use client";

import React from "react";
import { MOCK_METRICS } from "@/lib/mock-data";
import { BarChart3, TrendingUp, Eye, Flame, Share2, Heart, MessageCircle } from "lucide-react";

export const AnalyticsDashboard: React.FC = () => {
  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-pink-400" />
            Instagram Graph API Performance Insights
          </h2>
          <p className="text-xs text-slate-400">Real-time engagement, impression metrics and content reach</p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-pink-500/10 text-pink-400 border border-pink-500/20">
          Last 30 Days
        </span>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {MOCK_METRICS.map((item, idx) => (
          <div
            key={idx}
            className="bg-slate-900/80 rounded-xl p-4 border border-slate-800 hover:border-slate-700 transition-colors shadow-sm"
          >
            <span className="text-xs text-slate-400 font-medium block mb-1">{item.label}</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-extrabold text-white tracking-tight">{item.value}</span>
              <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-0.5">
                <TrendingUp className="w-3 h-3" />
                {item.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Performance Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Format breakdown */}
        <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800">
          <h3 className="text-xs font-bold text-slate-200 mb-3 flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5 text-pink-400" />
            Format Engagement Distribution
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">AI Reels (9:16 Video)</span>
                <span className="text-pink-400 font-bold">68.4%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div className="bg-pink-500 h-full rounded-full" style={{ width: "68.4%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">AI Carousels (4:5 Multi-slide)</span>
                <span className="text-amber-400 font-bold">22.1%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: "22.1%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">Single Photo Posts</span>
                <span className="text-sky-400 font-bold">9.5%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div className="bg-sky-500 h-full rounded-full" style={{ width: "9.5%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Top Post Highlights */}
        <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800">
          <h3 className="text-xs font-bold text-slate-200 mb-3 flex items-center gap-1.5">
            <Eye className="w-3.5 h-3.5 text-pink-400" />
            Top Automated Post Highlights
          </h3>
          <div className="space-y-2">
            <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-pink-500" />
                <span className="text-slate-300 font-medium truncate max-w-[180px]">Alphonso Mango Cake Reel</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400">
                <span className="flex items-center gap-1"><Heart className="w-3 h-3 text-rose-400" /> 2.4K</span>
                <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3 text-sky-400" /> 184</span>
              </div>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span className="text-slate-300 font-medium truncate max-w-[180px]">Morning Croissant Drop</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400">
                <span className="flex items-center gap-1"><Heart className="w-3 h-3 text-rose-400" /> 1.8K</span>
                <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3 text-sky-400" /> 92</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
