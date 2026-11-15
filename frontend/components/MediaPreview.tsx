"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { Film, Image as ImageIcon, Music, Layout, Calendar, Send, Copy, Check } from "lucide-react";

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
      <div className="bg-white rounded-sm p-12 text-center border border-slate-200 flex flex-col items-center justify-center min-h-[460px] shadow-xs">
        <div className="w-12 h-12 rounded-sm bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 mb-4">
          <Film className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-700">No Media Generated Yet</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Enter a prompt and generate media assets to view your reel, image, audio, and captions.
        </p>
      </div>
    );
  }

  const handleCopyCaption = () => {
    navigator.clipboard.writeText(`${generatedAsset.caption}\n\n${generatedAsset.hashtags.join(" ")}`);
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
    <div className="bg-white rounded-sm p-5 border border-slate-200 space-y-6 shadow-xs">
      {/* Header and Asset Type Tabs */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            Generated Media Assets
          </h2>
          <p className="text-xs text-slate-500">Inspect image, video reel, audio track, and caption</p>
        </div>

        {/* Preview Selector Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-sm border border-slate-200">
          <button
            onClick={() => setActiveAssetTab("video")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeAssetTab === "video"
                ? "bg-rose-600 text-white"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Film className="w-3 h-3" />
            Reel Video
          </button>
          <button
            onClick={() => setActiveAssetTab("image")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeAssetTab === "image"
                ? "bg-rose-600 text-white"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <ImageIcon className="w-3 h-3" />
            Image
          </button>
          <button
            onClick={() => setActiveAssetTab("audio")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeAssetTab === "audio"
                ? "bg-rose-600 text-white"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Music className="w-3 h-3" />
            Audio
          </button>
          <button
            onClick={() => setActiveAssetTab("thumbnail")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-sm transition-colors ${
              activeAssetTab === "thumbnail"
                ? "bg-rose-600 text-white"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Layout className="w-3 h-3" />
            Cover
          </button>
        </div>
      </div>

      {/* Main Preview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Media Player Frame */}
        <div className="md:col-span-5 flex flex-col items-center justify-center bg-slate-100 rounded-sm p-4 border border-slate-200 relative overflow-hidden">
          {activeAssetTab === "video" && (
            <div className="w-full max-w-[240px] aspect-[9/16] rounded-sm overflow-hidden relative border border-slate-300 bg-black">
              <video
                src={generatedAsset.videoUrl}
                controls
                autoPlay
                loop
                muted
                className="w-full h-full object-cover"
              />
              <div className="absolute top-2 left-2 bg-black/80 px-2 py-0.5 rounded-none text-[10px] text-white font-medium">
                9:16 Reel
              </div>
            </div>
          )}

          {activeAssetTab === "image" && (
            <div className="w-full max-w-[280px] aspect-[4/5] rounded-sm overflow-hidden relative border border-slate-300">
              <img
                src={generatedAsset.imageUrl}
                alt="Generated Media"
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {activeAssetTab === "audio" && (
            <div className="w-full p-6 flex flex-col items-center justify-center space-y-4">
              <div className="w-14 h-14 rounded-sm bg-white border border-slate-200 flex items-center justify-center text-rose-600 shadow-xs">
                <Music className="w-7 h-7" />
              </div>
              <div className="text-center">
                <h4 className="text-sm font-semibold text-slate-800">Neural Voiceover + Ambient Score</h4>
                <p className="text-xs text-slate-500 mt-0.5">Edge-TTS Narration</p>
              </div>
              <audio controls src={generatedAsset.audioUrl} className="w-full mt-2" />
            </div>
          )}

          {activeAssetTab === "thumbnail" && (
            <div className="w-full max-w-[260px] aspect-[9/16] rounded-sm overflow-hidden relative border border-slate-300">
              <img
                src={generatedAsset.thumbnailUrl}
                alt="Thumbnail Cover"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-black/75 flex items-end p-3">
                <p className="text-xs font-bold text-white line-clamp-2">
                  {generatedAsset.caption.split("\n")[0]}
                </p>
              </div>
              <div className="absolute top-2 left-2 bg-black/80 px-2 py-0.5 rounded-none text-[10px] text-white font-medium">
                Cover Frame
              </div>
            </div>
          )}
        </div>

        {/* Caption, Hashtags & Action Buttons */}
        <div className="md:col-span-7 flex flex-col justify-between space-y-4">
          {/* Editable Caption */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-700">Generated Caption</label>
              <button
                onClick={handleCopyCaption}
                className="text-[11px] text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
              >
                {copiedCaption ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                {copiedCaption ? "Copied" : "Copy Caption"}
              </button>
            </div>
            <textarea
              rows={6}
              value={generatedAsset.caption}
              onChange={(e) => updateGeneratedAsset({ caption: e.target.value })}
              className="w-full bg-slate-50 border border-slate-300 rounded-sm p-3 text-xs text-slate-800 leading-relaxed focus:outline-none focus:border-rose-500 focus:bg-white resize-none font-mono"
            />
          </div>

          {/* Hashtag Chips */}
          <div>
            <span className="block text-xs font-semibold text-slate-700 mb-1.5">Hashtags</span>
            <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-2 bg-slate-50 rounded-sm border border-slate-200">
              {generatedAsset.hashtags.map((tag, idx) => (
                <span
                  key={idx}
                  className="text-[11px] px-2 py-0.5 rounded-sm bg-white text-rose-600 font-medium border border-slate-200 shadow-2xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Publishing & Scheduling Actions */}
          <div className="pt-2 border-t border-slate-200 flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={handlePublishNow}
              disabled={isPublishing}
              className="w-full sm:flex-1 py-2 px-4 rounded-sm text-xs font-semibold bg-rose-600 hover:bg-rose-700 active:scale-[0.99] text-white flex items-center justify-center gap-2 transition-colors disabled:opacity-50 shadow-xs"
            >
              <Send className="w-3.5 h-3.5" />
              {isPublishing ? "Publishing..." : publishSuccess ? "Published" : `Publish to @${activeAccount.username}`}
            </button>

            <button
              onClick={onOpenScheduler}
              className="w-full sm:flex-1 py-2 px-4 rounded-sm text-xs font-semibold bg-slate-100 hover:bg-slate-200 active:scale-[0.99] text-slate-700 border border-slate-300 flex items-center justify-center gap-2 transition-colors"
            >
              <Calendar className="w-3.5 h-3.5 text-rose-600" />
              Schedule Post
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
