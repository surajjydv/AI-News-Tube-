"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { ContentType, AspectRatio } from "@/types";
import { Sparkles, Wand2, Film, Image as ImageIcon, Layers, Sliders, PlayCircle, Loader2 } from "lucide-react";

const PROMPT_IDEAS = [
  "Promote my bakery's weekend Alphonso Mango Cake with luxurious slow-mo glaze",
  "High-octane CrossFit workout reel introducing morning 6 AM batch with gym beat",
  "New botanical vitamin C serum product launch with morning sun flare aesthetic",
  "Client review showcase: how our artisan sourdough gained 500 loyal weekly fans",
];

export const PromptStudio: React.FC = () => {
  const { isGenerating, generationStep, generationPercent, generateContent } = useStudioStore();
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
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-pink-500/10 border border-pink-500/20 text-pink-400">
            <Wand2 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">AI Media Generation Engine</h2>
            <p className="text-xs text-slate-400">Enter 1 prompt ? get 4K Image, 9:16 Reel, Neural Voice, & Thumbnail</p>
          </div>
        </div>
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          Flux 1.1 + Edge-TTS + FFmpeg
        </span>
      </div>

      <form onSubmit={handleGenerate} className="space-y-4">
        {/* Prompt Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">
            Campaign Prompt / Creative Brief
          </label>
          <div className="relative">
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Launching our seasonal strawberry croissant this Friday, 20% off for first 30 walk-ins..."
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-pink-500 transition-colors shadow-inner resize-none"
            />
          </div>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-slate-400 mr-1 font-medium">Try ideas:</span>
          {PROMPT_IDEAS.map((idea, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(idea)}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/70 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors truncate max-w-[280px]"
            >
              {idea}
            </button>
          ))}
        </div>

        {/* Content Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          {/* Format */}
          <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <span className="block text-[11px] font-semibold text-slate-400 mb-2">Content Format</span>
            <div className="grid grid-cols-2 gap-1.5">
              <button
                type="button"
                onClick={() => { setContentType("reel"); setAspectRatio("9:16"); }}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  contentType === "reel"
                    ? "bg-pink-600 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                }`}
              >
                <Film className="w-3 h-3" />
                Reel / Video
              </button>
              <button
                type="button"
                onClick={() => { setContentType("post"); setAspectRatio("4:5"); }}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  contentType === "post"
                    ? "bg-pink-600 text-white shadow-sm"
                    : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                }`}
              >
                <ImageIcon className="w-3 h-3" />
                Single Post
              </button>
            </div>
          </div>

          {/* Aspect Ratio */}
          <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <span className="block text-[11px] font-semibold text-slate-400 mb-2">Aspect Ratio</span>
            <div className="grid grid-cols-3 gap-1.5">
              {(['9:16', '4:5', '1:1'] as AspectRatio[]).map((ratio) => (
                <button
                  key={ratio}
                  type="button"
                  onClick={() => setAspectRatio(ratio)}
                  className={`px-2 py-1.5 rounded-lg text-xs font-medium transition-all text-center ${
                    aspectRatio === ratio
                      ? "bg-pink-600 text-white shadow-sm"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {ratio}
                </button>
              ))}
            </div>
          </div>

          {/* Brand Voice / Tone */}
          <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <span className="block text-[11px] font-semibold text-slate-400 mb-2">Tone of Voice</span>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-slate-800 text-xs text-slate-200 rounded-lg p-2 border border-slate-700 outline-none cursor-pointer"
            >
              <option value="Warm & Artisanal">Warm & Artisanal</option>
              <option value="High Energy & Fitness">High Energy & Viral</option>
              <option value="Luxury & Minimalist">Luxury & Minimalist</option>
              <option value="Educational & Authority">Educational & Authority</option>
            </select>
          </div>
        </div>

        {/* Generate Button & Progress */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isGenerating || !prompt.trim()}
            className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-gradient-to-r from-pink-500 via-rose-500 to-amber-500 hover:opacity-95 active:scale-[0.99] text-white shadow-lg shadow-pink-500/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating Complete Media Pack...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Complete Instagram Media Pack
              </>
            )}
          </button>
        </div>

        {/* Progress Pipeline Indicator */}
        {isGenerating && (
          <div className="bg-slate-900/80 p-3 rounded-xl border border-pink-500/30 space-y-2 animate-pulse">
            <div className="flex items-center justify-between text-xs">
              <span className="text-pink-400 font-medium flex items-center gap-1.5">
                <Loader2 className="w-3 h-3 animate-spin" />
                {generationStep}
              </span>
              <span className="text-slate-400 font-bold">{generationPercent}%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-pink-500 to-amber-400 h-full transition-all duration-300 ease-out"
                style={{ width: `${generationPercent}%` }}
              />
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
