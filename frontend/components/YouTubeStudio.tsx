"use client";

import React, { useState, useEffect } from "react";
import { YouTubeChannel, YouTubeVideo, YouTubeStreamInfo } from "@/types";
import {
  Film,
  Eye,
  ThumbsUp,
  Radio,
  Search,
  ExternalLink,
  RefreshCw,
  Copy,
  Check,
  Play,
  X,
  Share2,
  Wand2,
  Flame,
  CheckCircle2,
  AlertCircle,
  Video,
  Square,
} from "lucide-react";

export const YouTubeStudio: React.FC = () => {
  const [channel, setChannel] = useState<YouTubeChannel | null>(null);
  const [videos, setVideos] = useState<YouTubeVideo[]>([]);
  const [streamInfo, setStreamInfo] = useState<YouTubeStreamInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "videos" | "shorts">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [revealKey, setRevealKey] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<YouTubeVideo | null>(null);

  // Manual generation state
  const [customTopic, setCustomTopic] = useState("");
  const [videoFormat, setVideoFormat] = useState("16:9 Breaking");
  const [voiceId, setVoiceId] = useState("hi-IN-MadhurNeural");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationMsg, setGenerationMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [isLiveStreamActive, setIsLiveStreamActive] = useState(false);
  const [liveStreamLoading, setLiveStreamLoading] = useState(false);
  const [liveStreamUptime, setLiveStreamUptime] = useState(0);
  const [liveMsg, setLiveMsg] = useState<string | null>(null);

  const fetchRealData = async () => {
    setLoading(true);
    try {
      const [chanRes, vidsRes, streamRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/youtube/channel"),
        fetch("http://127.0.0.1:8000/api/youtube/videos?max_results=50"),
        fetch("http://127.0.0.1:8000/api/youtube/stream"),
      ]);

      if (chanRes.ok) {
        const cData = await chanRes.json();
        setChannel(cData);
      }
      if (vidsRes.ok) {
        const vData = await vidsRes.json();
        setVideos(vData.videos || []);
      }
      if (streamRes.ok) {
        const sData = await streamRes.json();
        setStreamInfo(sData);
      }
    } catch (err) {
      console.warn("Failed fetching live YouTube data from FastAPI:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLiveStatus = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/live/status");
      if (res.ok) {
        const data = await res.json();
        setIsLiveStreamActive(!!data.isLive);
        setLiveStreamUptime(data.uptimeSeconds || 0);
      }
    } catch (err) {
      // ignore
    }
  };

  const handleStartLiveStream = async () => {
    setLiveStreamLoading(true);
    setLiveMsg(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/live/start", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setIsLiveStreamActive(true);
        setLiveMsg("24/7 Live Stream active! Rotating videos to YouTube RTMP.");
      } else {
        setLiveMsg(data.message || "Failed to start live stream.");
      }
    } catch (err) {
      setLiveMsg("Error contacting live stream service.");
    } finally {
      setLiveStreamLoading(false);
      fetchLiveStatus();
    }
  };

  const handleStopLiveStream = async () => {
    setLiveStreamLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/live/stop", { method: "POST" });
      const data = await res.json();
      setIsLiveStreamActive(false);
      setLiveMsg("Live stream stopped.");
    } catch (err) {
      setLiveMsg("Error stopping live stream.");
    } finally {
      setLiveStreamLoading(false);
      fetchLiveStatus();
    }
  };

  useEffect(() => {
    fetchRealData();
    fetchLiveStatus();
    const interval = setInterval(fetchLiveStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleManualGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customTopic.trim() || isGenerating) return;

    setIsGenerating(true);
    setGenerationMsg(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/generate/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: customTopic.trim(),
          video_format: videoFormat,
          voice_id: voiceId,
          target_minutes: videoFormat.includes("Shorts") ? 1.0 : 2.5,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setGenerationMsg({
          type: "success",
          text: `Production started for "${customTopic}". Rendering 1080p broadcast video in background. It will appear below once ready.`,
        });
        setCustomTopic("");
        // Refresh videos after 5 seconds
        setTimeout(() => fetchRealData(), 5000);
      } else {
        setGenerationMsg({
          type: "error",
          text: data.detail || "Generation request failed. Please check backend.",
        });
      }
    } catch (err: any) {
      setGenerationMsg({
        type: "error",
        text: err?.message || "Failed to reach backend server on port 8000.",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTriggerTrending = async () => {
    if (isGenerating) return;
    setIsGenerating(true);
    setGenerationMsg(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/generate/trending", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      if (res.ok) {
        setGenerationMsg({
          type: "success",
          text: "1-Click Trending Video production triggered. Story research, scriptwriting, and FFmpeg encoding active.",
        });
        setTimeout(() => fetchRealData(), 6000);
      } else {
        setGenerationMsg({
          type: "error",
          text: data.detail || "Trending generation failed.",
        });
      }
    } catch (err: any) {
      setGenerationMsg({
        type: "error",
        text: err?.message || "Backend error triggering trending cycle.",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const filteredVideos = videos.filter((v) => {
    const matchesFilter =
      filter === "all" ? true : filter === "shorts" ? v.isShort : !v.isShort;
    const matchesSearch =
      searchQuery === "" ||
      v.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const QUICK_TOPICS = [
    "Delhi Air Quality Crisis: Supreme Court Imposes Emergency Action",
    "Ramayana Movie Official Release Update: Ranbir Kapoor & Yash",
    "Bengal Santiniketan Police Encounter: Ground Investigation",
    "Union Budget 2026: Tax Slabs & Infrastructure Key Highlights",
  ];

  return (
    <div className="space-y-6 pb-10">
      {/* Studio Command Banner */}
      <div className="relative bg-white border border-slate-200 rounded-sm p-6 md:p-8 shadow-xs">
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          {/* Identity & Avatar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="relative shrink-0">
              {channel?.avatarUrl ? (
                <img
                  src={channel.avatarUrl}
                  alt={channel.title}
                  className="w-16 h-16 md:w-20 md:h-20 rounded-sm border border-slate-200 object-cover"
                />
              ) : (
                <div className="w-16 h-16 md:w-20 md:h-20 rounded-sm bg-red-600 flex items-center justify-center text-white font-bold text-xl">
                  SRJ
                </div>
              )}
              <span className="absolute -bottom-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-sm bg-emerald-500 ring-2 ring-white">
                <span className="h-1.5 w-1.5 rounded-sm bg-white" />
              </span>
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
                  {channel?.title || "SRJ UNDERRATED"}
                </h1>
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  LIVE
                </span>
                <span className="px-2 py-0.5 rounded-sm bg-slate-100 text-slate-600 text-xs font-medium border border-slate-200">
                  {channel?.customUrl || "@SRJUNDERRATED"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-xl">
                {channel?.description || "24/7 AI-NewsTube Live & Automated Broadcasts"}
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto justify-end">
            <button
              onClick={fetchRealData}
              disabled={loading}
              className="px-3.5 py-2 rounded-sm bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 border border-slate-200 transition-colors flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-red-600" : ""}`} />
              Refresh Data
            </button>
            <a
              href="https://studio.youtube.com"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3.5 py-2 rounded-sm bg-red-600 hover:bg-red-700 text-xs font-semibold text-white transition-colors flex items-center gap-2 shadow-xs"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open YouTube Studio
            </a>
          </div>
        </div>

        {/* Live Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-200">
          <div className="bg-slate-50 p-4 rounded-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1.5 font-medium">
              <span>Total Uploads</span>
              <Film className="w-4 h-4 text-red-600" />
            </div>
            <span className="text-2xl font-black text-slate-900 tracking-tight">
              {channel?.videoCount || 105}
            </span>
          </div>

          <div className="bg-slate-50 p-4 rounded-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1.5 font-medium">
              <span>Channel Views</span>
              <Eye className="w-4 h-4 text-red-600" />
            </div>
            <span className="text-2xl font-black text-slate-900 tracking-tight">
              {channel?.viewCount?.toLocaleString() || "1,091"}
            </span>
          </div>

          <div className="bg-slate-50 p-4 rounded-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1.5 font-medium">
              <span>Subscribers</span>
              <UsersIcon className="w-4 h-4 text-red-600" />
            </div>
            <span className="text-2xl font-black text-slate-900 tracking-tight">
              {channel?.subscriberCount || 3}
            </span>
          </div>

          <div className="bg-slate-50 p-4 rounded-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1.5 font-medium">
              <span>Live Broadcast</span>
              <Radio className="w-4 h-4 text-emerald-600" />
            </div>
            <span className="text-sm font-bold text-emerald-600 tracking-tight flex items-center gap-1.5">
              RTMP Ready
            </span>
          </div>
        </div>
      </div>

      {/* Manual Video Production & Instant Broadcast Desk */}
      <div className="bg-white rounded-sm p-6 border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-sm bg-red-600 text-white shadow-xs">
              <Wand2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Manual Video Production Desk</h3>
              <p className="text-xs text-slate-500">Generate and publish a 1080p full-HD broadcast video or vertical short on demand</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleTriggerTrending}
            disabled={isGenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 text-xs font-bold transition-colors shadow-2xs"
          >
            <Flame className="w-3.5 h-3.5 text-amber-600" />
            1-Click Auto Trending Video
          </button>
        </div>

        {generationMsg && (
          <div
            className={`p-3 rounded-sm border text-xs flex items-start gap-2 ${
              generationMsg.type === "success"
                ? "bg-emerald-50 border-emerald-300 text-emerald-800"
                : "bg-red-50 border-red-300 text-red-800"
            }`}
          >
            {generationMsg.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span>{generationMsg.text}</span>
              {generationMsg.type === "success" && (
                <button
                  onClick={fetchRealData}
                  className="block mt-1 font-bold underline hover:text-emerald-900 cursor-pointer"
                >
                  Click to Refresh Uploads Feed →
                </button>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleManualGenerate} className="space-y-3.5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Topic Headline / Breaking News Prompt:
            </label>
            <input
              type="text"
              value={customTopic}
              onChange={(e) => setCustomTopic(e.target.value)}
              placeholder="e.g. Delhi Air Quality Crisis: Supreme Court Imposes Emergency Action"
              className="w-full bg-white border border-slate-300 rounded-sm px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-colors"
            />
          </div>

          {/* Quick Idea Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-slate-500 mr-1 font-medium">Quick Ideas:</span>
            {QUICK_TOPICS.map((topic, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setCustomTopic(topic)}
                className="text-[11px] px-2.5 py-1 rounded-sm bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors truncate max-w-[280px]"
              >
                {topic}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Video Format</label>
              <select
                value={videoFormat}
                onChange={(e) => setVideoFormat(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-sm p-2 text-xs font-medium text-slate-800 outline-none"
              >
                <option value="16:9 Breaking">16:9 Full Broadcast Bulletin</option>
                <option value="9:16 Shorts">9:16 Vertical News Short</option>
                <option value="16:9 Documentary">16:9 Documentary Explainer</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Narrator Voice</label>
              <select
                value={voiceId}
                onChange={(e) => setVoiceId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-sm p-2 text-xs font-medium text-slate-800 outline-none"
              >
                <option value="hi-IN-MadhurNeural">hi-IN-MadhurNeural (Male Prime-Time)</option>
                <option value="hi-IN-SwaraNeural">hi-IN-SwaraNeural (Female Expressive)</option>
                <option value="en-IN-PrabhatNeural">en-IN-PrabhatNeural (English Male)</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={isGenerating || !customTopic.trim()}
                className="w-full py-2.5 px-4 rounded-sm bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-xs font-bold transition-colors flex items-center justify-center gap-2 shadow-xs cursor-pointer"
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Producing Broadcast...
                  </>
                ) : (
                  <>
                    <Video className="w-3.5 h-3.5" />
                    ⚡ Generate & Broadcast Now
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* RTMP Broadcast Controller Card */}
      <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-sm bg-slate-100 border border-slate-200 text-red-600 shrink-0">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">24/7 Continuous Live Stream Hub</h3>
              {isLiveStreamActive ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px] font-bold border border-red-200 animate-pulse">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>
                  STREAMING LIVE (VIDEO ROTATION QUEUE)
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-semibold border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                  READY TO STREAM
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed max-w-2xl">
              Server URL: <code className="text-red-700 bg-slate-100 px-1.5 py-0.5 rounded-none border border-slate-200 font-mono text-[11px]">{streamInfo?.rtmpUrl || "rtmp://a.rtmp.youtube.com/live2"}</code>
              <span className="mx-2 text-slate-300">|</span>
              Stream Key: <code className="text-slate-800 bg-slate-100 px-1.5 py-0.5 rounded-none border border-slate-200 font-mono text-[11px]">{revealKey ? "011y-69ku-2w6b-seq4-6vyq" : streamInfo?.streamKeyMasked || "011y-****-****-6vyq"}</code>
            </p>
            {liveMsg && (
              <p className="text-[11px] font-semibold text-emerald-600 mt-1.5 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                {liveMsg}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto justify-end">
          {isLiveStreamActive ? (
            <button
              onClick={handleStopLiveStream}
              disabled={liveStreamLoading}
              className="px-4 py-2 rounded-sm bg-red-600 hover:bg-red-700 text-xs text-white font-bold transition-all flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              {liveStreamLoading ? "Stopping..." : "Stop Live Stream"}
            </button>
          ) : (
            <button
              onClick={handleStartLiveStream}
              disabled={liveStreamLoading}
              className="px-4 py-2 rounded-sm bg-emerald-600 hover:bg-emerald-700 text-xs text-white font-bold transition-all flex items-center gap-2 shadow-xs cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              {liveStreamLoading ? "Starting Engine..." : "Start 24/7 Live Stream"}
            </button>
          )}

          <button
            onClick={() => setRevealKey(!revealKey)}
            className="px-3 py-1.5 rounded-sm bg-slate-100 hover:bg-slate-200 text-xs text-slate-700 font-semibold border border-slate-300 transition-colors"
          >
            {revealKey ? "Hide Key" : "Reveal Key"}
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText("rtmp://a.rtmp.youtube.com/live2");
              setCopiedKey(true);
              setTimeout(() => setCopiedKey(false), 2000);
            }}
            className="px-3.5 py-1.5 rounded-sm bg-slate-800 hover:bg-slate-900 text-xs text-white font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
          >
            {copiedKey ? <Check className="w-3.5 h-3.5 text-emerald-200" /> : <Copy className="w-3.5 h-3.5" />}
            {copiedKey ? "Copied RTMP!" : "Copy Endpoint"}
          </button>
        </div>
      </div>

      {/* Control Toolbar: Search + Filter Chips */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 pt-1">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search uploads..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-sm pl-10 pr-4 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-colors"
          />
        </div>

        {/* Filter Segmented Controls */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-sm border border-slate-200 shrink-0">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-sm text-xs font-semibold transition-colors ${
              filter === "all"
                ? "bg-red-600 text-white"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            All Uploads ({videos.length})
          </button>
          <button
            onClick={() => setFilter("videos")}
            className={`px-3 py-1.5 rounded-sm text-xs font-semibold transition-colors ${
              filter === "videos"
                ? "bg-red-600 text-white"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            Long Form (16:9)
          </button>
          <button
            onClick={() => setFilter("shorts")}
            className={`px-3 py-1.5 rounded-sm text-xs font-semibold transition-colors ${
              filter === "shorts"
                ? "bg-red-600 text-white"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/80"
            }`}
          >
            Shorts ({videos.filter((v) => v.isShort).length})
          </button>
        </div>
      </div>

      {/* Videos Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="bg-slate-100 animate-pulse rounded-sm aspect-video" />
          ))}
        </div>
      ) : filteredVideos.length === 0 ? (
        <div className="bg-white rounded-sm p-12 text-center border border-slate-200">
          <Film className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm font-semibold text-slate-700">No videos matching criteria</p>
          <p className="text-xs text-slate-400 mt-1">Try clearing your search query or refreshing data.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredVideos.map((vid) => {
            const dateStr = vid.publishedAt
              ? new Date(vid.publishedAt).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "Live";

            return (
              <div
                key={vid.id}
                onClick={() => setSelectedVideo(vid)}
                className="group relative bg-white border border-slate-200 hover:border-slate-300 rounded-sm overflow-hidden flex flex-col cursor-pointer transition-all shadow-2xs hover:shadow-sm"
              >
                {/* Thumbnail Viewport */}
                <div className="relative aspect-video w-full bg-slate-100 overflow-hidden">
                  <img
                    src={vid.thumbnailUrl}
                    alt={vid.title}
                    className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-300"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-black/10 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                    <div className="w-10 h-10 rounded-sm bg-red-600/90 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity transform scale-90 group-hover:scale-100 shadow-md">
                      <Play className="w-4 h-4 fill-white ml-0.5" />
                    </div>
                  </div>

                  {vid.isShort && (
                    <span className="absolute top-2 right-2 px-1.5 py-0.5 rounded-none bg-red-600 text-white font-bold text-[10px] tracking-wider uppercase shadow-xs">
                      Shorts
                    </span>
                  )}
                  {vid.id.startsWith("local_") && (
                    <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded-none bg-emerald-600 text-white font-bold text-[10px] tracking-wider uppercase shadow-xs">
                      Local Ready
                    </span>
                  )}
                </div>

                {/* Video Info */}
                <div className="p-3.5 flex flex-col flex-1 justify-between gap-3">
                  <h4 className="text-xs font-bold text-slate-900 group-hover:text-red-600 line-clamp-2 transition-colors leading-snug">
                    {vid.title}
                  </h4>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 font-medium text-slate-700">
                        <Eye className="w-3 h-3 text-red-600" />
                        {vid.viewCount.toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1 font-medium text-slate-700">
                        <ThumbsUp className="w-3 h-3 text-red-600" />
                        {vid.likeCount}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-400">{dateStr}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Interactive Theater Player Modal */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/50 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white w-full max-w-4xl rounded-sm border border-slate-200 shadow-2xl overflow-hidden relative">
            {/* Close */}
            <button
              onClick={() => setSelectedVideo(null)}
              className="absolute top-3 right-3 z-20 p-2 rounded-sm bg-black/80 text-white hover:bg-red-600 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Video Player */}
            <div className="aspect-video w-full bg-black flex items-center justify-center">
              {selectedVideo.embedUrl.endsWith(".mp4") ? (
                <video
                  src={selectedVideo.embedUrl}
                  controls
                  autoPlay
                  className="w-full h-full object-contain"
                />
              ) : (
                <iframe
                  src={`${selectedVideo.embedUrl}?autoplay=1&rel=0`}
                  title={selectedVideo.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="w-full h-full border-none"
                />
              )}
            </div>

            {/* Video Meta & Controls */}
            <div className="p-5 space-y-4 bg-white">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-slate-900 leading-snug">{selectedVideo.title}</h3>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1.5 text-red-600 font-semibold">
                      <Eye className="w-3.5 h-3.5" />
                      {selectedVideo.viewCount} Views
                    </span>
                    <span className="flex items-center gap-1.5 text-slate-700 font-medium">
                      <ThumbsUp className="w-3.5 h-3.5 text-red-600" />
                      {selectedVideo.likeCount} Likes
                    </span>
                    <span className="text-slate-400">
                      Uploaded: {new Date(selectedVideo.publishedAt).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 shrink-0">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(selectedVideo.youtubeUrl);
                      setCopiedLink(true);
                      setTimeout(() => setCopiedLink(false), 2000);
                    }}
                    className="px-3 py-1.5 rounded-sm bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 border border-slate-300 transition-colors flex items-center gap-1.5"
                  >
                    {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Share2 className="w-3.5 h-3.5" />}
                    {copiedLink ? "Link Copied" : "Share Link"}
                  </button>
                  <a
                    href={selectedVideo.youtubeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-sm bg-red-600 hover:bg-red-700 text-xs font-semibold text-white transition-colors shadow-xs"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    {selectedVideo.id.startsWith("local_") ? "Open Video" : "Watch on YouTube"}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const UsersIcon: React.FC<{ className?: string }> = ({ className = "w-4 h-4" }) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);
