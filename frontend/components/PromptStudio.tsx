"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { ContentType, AspectRatio } from "@/types";
import { Wand2, Film, Image as ImageIcon, Loader2, Key } from "lucide-react";

const PROMPT_IDEAS = [
  "Promote my bakery's weekend Alphonso Mango Cake with luxurious slow-mo glaze",
  "High-octane CrossFit workout reel introducing morning 6 AM batch with gym beat",
  "New botanical vitamin C serum product launch with morning sun flare aesthetic",
  "Client review showcase: how our artisan sourdough gained 500 loyal weekly fans",
];

export const PromptStudio: React.FC = () => {
  const { isGenerating, generationStep, generationPercent, generateContent, setActiveTab } = useStudioStore();
  const [prompt, setPrompt] = useState(
    "Promote my bakery's new mango cake for weekends with irresistible gourmet vibe"
  );
  const [contentType, setContentType] = useState<ContentType>("reel");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("9:16");
  const [tone, setTone] = useState("Warm & Artisanal");

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
          <span>Auto-publish to Instagram, YouTube & Telegram</span>
        </div>
        <button
          type="button"
          onClick={() => setActiveTab("platforms")}
          className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 underline cursor-pointer"
        >
          Configure Keys →
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-sm bg-slate-100 border border-slate-200 text-rose-600">
            <Wand2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Media Generation Engine</h2>
            <p className="text-xs text-slate-500">Produce image, 9:16 reel, voiceover, and thumbnail from a single prompt</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleGenerate} className="space-y-4">
        {/* Prompt Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Campaign Prompt / Creative Brief
          </label>
          <div className="relative">
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Launching our seasonal strawberry croissant this Friday, 20% off for first 30 walk-ins..."
              className="w-full bg-white border border-slate-300 rounded-sm p-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:ring-1 focus:ring-rose-500 transition-colors resize-none"
            />
          </div>
        </div>

        {/* Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-slate-500 mr-1 font-medium">Ideas:</span>
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
                    ? "bg-rose-600 text-white"
                    : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                }`}
              >
                <Film className="w-3 h-3" />
                Reel Video
              </button>
              <button
                type="button"
                onClick={() => { setContentType("post"); setAspectRatio("4:5"); }}
                className={`flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-sm text-xs font-medium transition-colors ${
                  contentType === "post"
                    ? "bg-rose-600 text-white"
                    : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                }`}
              >
                <ImageIcon className="w-3 h-3" />
                Single Post
              </button>
            </div>
          </div>

          {/* Aspect Ratio */}
          <div className="bg-slate-50 p-3 rounded-sm border border-slate-200">
            <span className="block text-[11px] font-semibold text-slate-600 mb-2">Aspect Ratio</span>
            <div className="grid grid-cols-3 gap-1.5">
              {(['9:16', '4:5', '1:1'] as AspectRatio[]).map((ratio) => (
                <button
                  key={ratio}
                  type="button"
                  onClick={() => setAspectRatio(ratio)}
                  className={`px-2 py-1.5 rounded-sm text-xs font-medium transition-colors text-center ${
                    aspectRatio === ratio
                      ? "bg-rose-600 text-white"
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
            <span className="block text-[11px] font-semibold text-slate-600 mb-2">Tone of Voice</span>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-white text-xs text-slate-800 rounded-sm p-2 border border-slate-300 outline-none cursor-pointer"
            >
              <option value="Warm & Artisanal">Warm & Artisanal</option>
              <option value="High Energy & Fitness">High Energy & Viral</option>
              <option value="Luxury & Minimalist">Luxury & Minimalist</option>
              <option value="Educational & Authority">Educational & Authority</option>
            </select>
          </div>
        </div>

        {/* Generate Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isGenerating || !prompt.trim()}
            className="w-full py-2.5 px-4 rounded-sm font-semibold text-sm bg-rose-600 hover:bg-rose-700 active:scale-[0.99] text-white flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating Media Assets...
              </>
            ) : (
              <>
                <Wand2 className="w-4 h-4" />
                Generate Media Pack
              </>
            )}
          </button>
        </div>

        {/* Progress */}
        {isGenerating && (
          <div className="bg-slate-50 p-3 rounded-sm border border-slate-200 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-rose-600 font-medium flex items-center gap-1.5">
                <Loader2 className="w-3 h-3 animate-spin" />
                {generationStep}
              </span>
              <span className="text-slate-600 font-bold">{generationPercent}%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-none overflow-hidden">
              <div
                className="bg-rose-600 h-full transition-all duration-300 ease-out"
                style={{ width: `${generationPercent}%` }}
              />
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
