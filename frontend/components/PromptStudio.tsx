"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { ContentType, AspectRatio } from "@/types";
import { Wand2, Film, Image as ImageIcon, Loader2, Key, Video } from "lucide-react";

const PROMPT_IDEAS = [
  "Today Cricket Match: Virat Kohli & Team India Update",
  "Delhi Air Quality Crisis: Supreme Court Imposes Emergency Action",
  "Ramayana Movie Official Release Update: Ranbir Kapoor & Yash",
  "Union Budget 2026: Tax Slabs & Infrastructure Key Highlights",
];

export const PromptStudio: React.FC = () => {
  const { isGenerating, generationStep, generationPercent, generateContent, setActiveTab } = useStudioStore();
  const [prompt, setPrompt] = useState(
    "Today Cricket Match: Virat Kohli & Team India Update"
  );
  const [contentType, setContentType] = useState<ContentType>("reel");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("9:16");
  const [tone, setTone] = useState("Prime-Time News & Documentary");

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isGenerating) return;
    await generateContent(prompt, contentType, aspectRatio, tone);
  };

  return (
    <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs space-y-4">
      {/* Quick Setup Banner */}
      <div className="flex items-center justify-between p-2.5 rounded-sm bg-slate-50 border border-slate-200 text-xs">
        <div className="flex items-center gap-2 text-slate-700">
          <Key className="w-3.5 h-3.5 text-amber-600" />
          <span>Auto-publish to YouTube, Instagram, Telegram & Twitter/X</span>
        </div>
        <button
          type="button"
          onClick={() => setActiveTab("platforms")}
          className="text-[11px] font-semibold text-red-600 hover:text-red-700 underline cursor-pointer"
        >
          Configure Keys →
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-sm bg-slate-100 border border-slate-200 text-red-600">
            <Wand2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Broadcast Content Generator</h2>
            <p className="text-xs text-slate-500">Retrieves verified real editorial photos, synthesizes neural voiceover, and renders video</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleGenerate} className="space-y-4">
        {/* Prompt Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Broadcast Topic / Headline Prompt
          </label>
          <div className="relative">
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Today Cricket Match: Virat Kohli batting performance, live score and key milestones..."
              className="w-full bg-white border border-slate-300 rounded-sm p-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-colors resize-none"
            />
          </div>
        </div>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-slate-500 mr-1 font-medium">Quick Ideas:</span>
          {PROMPT_IDEAS.map((idea, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(idea)}
              className="text-[11px] px-2.5 py-1 rounded-sm bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors truncate max-w-[280px]"
            >
              {idea}
            </button>
          ))}
        </div>

        {/* Content Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          {/* Format */}
          <div className="bg-slate-50 p-3 rounded-sm border border-slate-200">
            <span className="block text-[11px] font-semibold text-slate-600 mb-2">Content Format</span>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                type="button"
                onClick={() => { setContentType("reel"); setAspectRatio("9:16"); }}
                className={`flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-sm text-xs font-medium transition-colors ${
                  contentType === "reel"
                    ? "bg-red-600 text-white"
                    : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                }`}
              >
                <Film className="w-3 h-3" />
                Short / Reel
              </button>
              <button
                type="button"
                onClick={() => { setContentType("video"); setAspectRatio("16:9"); }}
                className={`flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-sm text-xs font-medium transition-colors ${
                  contentType === "video"
                    ? "bg-red-600 text-white"
                    : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                }`}
              >
                <Video className="w-3 h-3" />
                16:9 Broadcast
              </button>
            </div>
          </div>

          {/* Aspect Ratio */}
          <div className="bg-slate-50 p-3 rounded-sm border border-slate-200">
            <span className="block text-[11px] font-semibold text-slate-600 mb-2">Aspect Ratio</span>
            <div className="grid grid-cols-4 gap-1">
              {(['16:9', '9:16', '4:5', '1:1'] as AspectRatio[]).map((ratio) => (
                <button
                  key={ratio}
                  type="button"
                  onClick={() => setAspectRatio(ratio)}
                  className={`px-1.5 py-1.5 rounded-sm text-xs font-medium transition-colors text-center ${
                    aspectRatio === ratio
                      ? "bg-red-600 text-white font-bold"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {ratio}
                </button>
              ))}
            </div>
          </div>

          {/* Tone */}
          <div className="bg-slate-50 p-3 rounded-sm border border-slate-200">
            <span className="block text-[11px] font-semibold text-slate-600 mb-2">Narrative Style / Tone</span>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-white text-xs text-slate-800 rounded-sm p-2 border border-slate-300 outline-none cursor-pointer"
            >
              <option value="Prime-Time News & Documentary">Prime-Time News & Documentary</option>
              <option value="Breaking News Alert (Urgent)">Breaking News Alert (Urgent)</option>
              <option value="Sports & Cricket Commentary (Hindi/English)">Sports & Cricket Commentary</option>
              <option value="Viral Investigative Report">Viral Investigative Report</option>
              <option value="Business & Market Analysis">Business & Market Analysis</option>
            </select>
          </div>
        </div>

        {/* Generate Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isGenerating || !prompt.trim()}
            className="w-full py-2.5 px-4 rounded-sm font-semibold text-sm bg-red-600 hover:bg-red-700 active:scale-[0.99] text-white flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-xs cursor-pointer"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{generationStep || "Generating Broadcast Media..."}</span>
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4" />
                <span>⚡ Generate Broadcast Media Pack</span>
              </>
            )}
          </button>
        </div>

        {/* Progress bar */}
        {isGenerating && (
          <div className="space-y-1.5 pt-1 animate-in fade-in duration-200">
            <div className="flex justify-between text-xs text-slate-600">
              <span className="font-medium text-slate-700">{generationStep}</span>
              <span className="font-bold text-red-600">{generationPercent}%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-none overflow-hidden">
              <div
                className="bg-red-600 h-full transition-all duration-300 ease-out rounded-none"
                style={{ width: `${generationPercent}%` }}
              />
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
