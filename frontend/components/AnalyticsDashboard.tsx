"use client";

import React from "react";
import { MOCK_METRICS } from "@/lib/mock-data";
import { BarChart3, TrendingUp, Eye, Flame, Heart, MessageCircle } from "lucide-react";

export const AnalyticsDashboard: React.FC = () => {
  return (
    <div className="bg-white rounded-sm p-5 border border-slate-200 space-y-6 shadow-xs">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-rose-600" />
            Instagram Performance Insights
          </h2>
          <p className="text-xs text-slate-500">Engagement, impression metrics and content reach</p>
        </div>
        <span className="text-xs text-slate-500 font-medium">Last 30 Days</span>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {MOCK_METRICS.map((item, idx) => (
          <div
            key={idx}
            className="bg-slate-50 rounded-sm p-3.5 border border-slate-200 hover:border-slate-300 transition-colors"
          >
            <span className="text-xs text-slate-500 font-medium block mb-1">{item.label}</span>
            <div className="flex items-baseline justify-between">
              <span className="text-xl font-bold text-slate-900 tracking-tight">{item.value}</span>
              <span className="text-[11px] font-medium text-emerald-600 flex items-center gap-0.5">
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
        <div className="bg-slate-50 rounded-sm p-4 border border-slate-200">
          <h3 className="text-xs font-bold text-slate-800 mb-3 flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5 text-rose-600" />
            Format Engagement Distribution
          </h3>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-700">Reels (9:16 Video)</span>
                <span className="text-rose-600 font-bold">68.4%</span>
              </div>
              <div className="w-full bg-slate-200 h-1.5 rounded-none overflow-hidden">
                <div className="bg-rose-500 h-full rounded-none" style={{ width: "68.4%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-700">Carousels (4:5 Multi-slide)</span>
                <span className="text-amber-600 font-bold">22.1%</span>
              </div>
              <div className="w-full bg-slate-200 h-1.5 rounded-none overflow-hidden">
                <div className="bg-amber-500 h-full rounded-none" style={{ width: "22.1%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-700">Single Photo Posts</span>
                <span className="text-sky-600 font-bold">9.5%</span>
              </div>
              <div className="w-full bg-slate-200 h-1.5 rounded-none overflow-hidden">
                <div className="bg-sky-500 h-full rounded-none" style={{ width: "9.5%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Post Highlights */}
        <div className="bg-slate-50 rounded-sm p-4 border border-slate-200">
          <h3 className="text-xs font-bold text-slate-800 mb-3 flex items-center gap-1.5">
            <Eye className="w-3.5 h-3.5 text-rose-600" />
            Top Post Highlights
          </h3>
          <div className="space-y-2">
            <div className="p-2.5 rounded-sm bg-white border border-slate-200 flex items-center justify-between text-xs shadow-2xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-none bg-rose-500" />
                <span className="text-slate-800 font-medium truncate max-w-[180px]">Alphonso Mango Cake Reel</span>
              </div>
              <div className="flex items-center gap-3 text-slate-500">
                <span className="flex items-center gap-1"><Heart className="w-3 h-3 text-rose-600" /> 2.4K</span>
                <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3 text-sky-600" /> 184</span>
              </div>
            </div>

            <div className="p-2.5 rounded-sm bg-white border border-slate-200 flex items-center justify-between text-xs shadow-2xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-none bg-amber-500" />
                <span className="text-slate-800 font-medium truncate max-w-[180px]">Morning Croissant Drop</span>
              </div>
              <div className="flex items-center gap-3 text-slate-500">
                <span className="flex items-center gap-1"><Heart className="w-3 h-3 text-rose-600" /> 1.8K</span>
                <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3 text-sky-600" /> 92</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
