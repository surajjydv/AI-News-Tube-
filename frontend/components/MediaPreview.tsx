"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { Film, Image as ImageIcon, Music, Layout, Calendar, Send, Copy, Check, Download, RefreshCw } from "lucide-react";

interface Props {
  onOpenScheduler: () => void;
}

export const MediaPreview: React.FC<Props> = ({ onOpenScheduler }) => {
  const { generatedAsset, updateGeneratedAsset, accounts, activeAccountId } = useStudioStore();
  const [activeAssetTab, setActiveAssetTab] = useState<"video" | "image" | "audio" | "thumbnail">("video");
  const [copiedCaption, setCopiedCaption] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState(false);

  const activeAccount = accounts.find((a) => a.id === activeAccountId) || accounts[0];

  if (!generatedAsset) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800 flex flex-col items-center justify-center min-h-[460px]">
        <div className="w-16 h-16 rounded-2xl bg-slate-800/80 flex items-center justify-center text-slate-500 mb-4">
          <Film className="w-8 h-8" />
        </div>
        <h3 className="text-base font-bold text-slate-300">No Media Generated Yet</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Type a prompt on the left and click "Generate Complete Instagram Media Pack" to see your AI Reel, Image, Audio, and Captions.
        </p>
      </div>
    );
  }

  const handleCopyCaption = () => {
    navigator.clipboard.writeText(`${generatedAsset.caption}

${generatedAsset.hashtags.join(" ")}`);
    setCopiedCaption(true);
    setTimeout(() => setCopiedCaption(false), 2000);
  };

  const handlePublishNow = async () => {
    setIsPublishing(true);
    await new Promise((res) => setTimeout(res, 1500));
    setIsPublishing(false);
    setPublishSuccess(true);
    setTimeout(() => setPublishSuccess(false), 3000);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      {/* Header and Asset Type Tabs */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            Generated Media Assets
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
              Ready
            </span>
          </h2>
          <p className="text-xs text-slate-400">Inspect image, video reel, audio track, and customized caption</p>
        </div>

        {/* Preview Selector Tabs */}
        <div className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveAssetTab("video")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeAssetTab === "video"
                ? "bg-pink-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Film className="w-3 h-3" />
            Reel Video
          </button>
          <button
            onClick={() => setActiveAssetTab("image")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeAssetTab === "image"
                ? "bg-pink-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ImageIcon className="w-3 h-3" />
            Image
          </button>
          <button
            onClick={() => setActiveAssetTab("audio")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeAssetTab === "audio"
                ? "bg-pink-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Music className="w-3 h-3" />
            Audio
          </button>
          <button
            onClick={() => setActiveAssetTab("thumbnail")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all ${
              activeAssetTab === "thumbnail"
                ? "bg-pink-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layout className="w-3 h-3" />
            Cover
          </button>
        </div>
      </div>

      {/* Main Preview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Media Player Frame (5 Cols) */}
        <div className="md:col-span-5 flex flex-col items-center justify-center bg-slate-950/80 rounded-2xl p-4 border border-slate-800/80 relative overflow-hidden">
          {activeAssetTab === "video" && (
            <div className="w-full max-w-[240px] aspect-[9/16] rounded-xl overflow-hidden shadow-2xl relative border border-slate-700 bg-black">
              <video
                src={generatedAsset.videoUrl}
                controls
                autoPlay
                loop
                muted
                className="w-full h-full object-cover"
              />
              <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded text-[10px] text-white font-semibold">
                9:16 Reel
              </div>
            </div>
          )}

          {activeAssetTab === "image" && (
            <div className="w-full max-w-[280px] aspect-[4/5] rounded-xl overflow-hidden shadow-2xl relative border border-slate-700">
              <img
                src={generatedAsset.imageUrl}
                alt="AI Generated Asset"
                className="w-full h-full object-cover"
              />
              <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded text-[10px] text-white font-semibold">
                4K Flux Render
              </div>
            </div>
          )}

          {activeAssetTab === "audio" && (
            <div className="w-full p-6 flex flex-col items-center justify-center space-y-4">
              <div className="w-20 h-20 rounded-full bg-pink-500/10 border border-pink-500/20 flex items-center justify-center text-pink-400 animate-pulse">
                <Music className="w-10 h-10" />
              </div>
              <div className="text-center">
                <h4 className="text-sm font-semibold text-white">Neural Voiceover + Ambient Score</h4>
                <p className="text-xs text-slate-400 mt-0.5">Edge-TTS (Natural En-US) + Cafe Ambience</p>
              </div>
              <audio controls src={generatedAsset.audioUrl} className="w-full mt-2" />
            </div>
          )}

          {activeAssetTab === "thumbnail" && (
            <div className="w-full max-w-[260px] aspect-[9/16] rounded-xl overflow-hidden shadow-2xl relative border border-slate-700">
              <img
                src={generatedAsset.thumbnailUrl}
                alt="Thumbnail Cover"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 flex items-end p-3">
                <p className="text-xs font-bold text-white line-clamp-2">
                  {generatedAsset.caption.split("\n")[0]}
                </p>
              </div>
              <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded text-[10px] text-white font-semibold">
                IG Cover Frame
              </div>
            </div>
          )}
        </div>

        {/* Caption, Hashtags & Action Buttons (7 Cols) */}
        <div className="md:col-span-7 flex flex-col justify-between space-y-4">
          {/* Editable Caption */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">Generated Instagram Caption</label>
              <button
                onClick={handleCopyCaption}
                className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
              >
                {copiedCaption ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                {copiedCaption ? "Copied" : "Copy Caption"}
              </button>
            </div>
            <textarea
              rows={6}
              value={generatedAsset.caption}
              onChange={(e) => updateGeneratedAsset({ caption: e.target.value })}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 text-xs text-slate-200 leading-relaxed focus:outline-none focus:border-pink-500 shadow-inner resize-none font-mono"
            />
          </div>

          {/* Hashtag Chips */}
          <div>
            <span className="block text-xs font-semibold text-slate-300 mb-1.5">High-Engagement Hashtags</span>
            <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-1 bg-slate-900/60 rounded-xl border border-slate-800">
              {generatedAsset.hashtags.map((tag, idx) => (
                <span
                  key={idx}
                  className="text-[11px] px-2 py-0.5 rounded-md bg-slate-800 text-pink-400 font-medium border border-slate-700/80"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Publishing & Scheduling Actions */}
          <div className="pt-2 border-t border-slate-800/80 flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={handlePublishNow}
              disabled={isPublishing}
              className="w-full sm:flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 active:scale-[0.99] text-white shadow-md shadow-pink-600/30 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              {isPublishing ? "Publishing to Instagram..." : publishSuccess ? "? Published!" : `Publish Now to @${activeAccount.username}`}
            </button>

            <button
              onClick={onOpenScheduler}
              className="w-full sm:flex-1 py-2.5 px-4 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 active:scale-[0.99] text-slate-200 border border-slate-700 flex items-center justify-center gap-2 transition-all"
            >
              <Calendar className="w-3.5 h-3.5 text-pink-400" />
              Schedule Post / Auto-Pilot
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
