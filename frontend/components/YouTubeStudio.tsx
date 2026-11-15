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

  useEffect(() => {
    fetchRealData();
  }, []);

  const filteredVideos = videos.filter((v) => {
    const matchesFilter =
      filter === "all" ? true : filter === "shorts" ? v.isShort : !v.isShort;
    const matchesSearch =
      searchQuery === "" ||
      v.title.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

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
              </div>
              <p className="text-xs text-slate-500 font-medium mt-1 flex items-center gap-2">
                <span className="text-red-600 font-semibold">{channel?.customUrl || "@SRJUNDERRATED"}</span>
                <span className="text-slate-300">|</span>
                <span>OAuth 2.0 Connected</span>
                <span className="text-slate-300">|</span>
                <span className="text-emerald-600 font-semibold">Synchronized</span>
              </p>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            <button
              onClick={fetchRealData}
              disabled={loading}
              className="flex items-center gap-2 px-3.5 py-2 rounded-sm bg-slate-100 hover:bg-slate-200 text-xs text-slate-700 font-semibold border border-slate-300 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-red-600" : ""}`} />
              Sync YouTube API
            </button>
            <a
              href="https://studio.youtube.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-sm bg-red-600 hover:bg-red-700 active:scale-[0.99] text-xs text-white font-semibold transition-colors shadow-xs"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Open YouTube Studio
            </a>
          </div>
        </div>

        {/* Live Metrics Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-200">
          <div className="bg-slate-50 p-4 rounded-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1.5 font-medium">
              <span>Total Uploads</span>
              <Film className="w-4 h-4 text-red-600" />
            </div>
            <span className="text-2xl font-black text-slate-900 tracking-tight">
              {channel?.videoCount || videos.length || 105}
            </span>
          </div>

          <div className="bg-slate-50 p-4 rounded-sm border border-slate-200">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1.5 font-medium">
              <span>Total Channel Views</span>
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

      {/* RTMP Broadcast Controller Card */}
      <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="p-2.5 rounded-sm bg-slate-100 border border-slate-200 text-red-600 shrink-0">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">24/7 RTMP Streaming Hub</h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed max-w-2xl">
              Server URL: <code className="text-red-700 bg-slate-100 px-1.5 py-0.5 rounded-none border border-slate-200 font-mono text-[11px]">{streamInfo?.rtmpUrl || "rtmp://a.rtmp.youtube.com/live2"}</code>
              <span className="mx-2 text-slate-300">|</span>
              Stream Key: <code className="text-slate-800 bg-slate-100 px-1.5 py-0.5 rounded-none border border-slate-200 font-mono text-[11px]">{revealKey ? "011y-69ku-2w6b-seq4-6vyq" : streamInfo?.streamKeyMasked || "011y-****-****-6vyq"}</code>
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto justify-end">
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
            className="px-3.5 py-1.5 rounded-sm bg-red-600 hover:bg-red-700 text-xs text-white font-semibold transition-colors flex items-center gap-1.5 shadow-xs"
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-white rounded-sm p-3 border border-slate-200 animate-pulse space-y-3 shadow-xs">
              <div className="aspect-video bg-slate-100 rounded-sm" />
              <div className="h-4 bg-slate-200 rounded-sm w-3/4" />
              <div className="h-3 bg-slate-100 rounded-sm w-1/2" />
            </div>
          ))}
        </div>
      ) : filteredVideos.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-slate-300 rounded-sm bg-white">
          <Film className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700">No matching videos found</h3>
          <p className="text-xs text-slate-500 mt-1">Try adjusting your search query or filter selection.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredVideos.map((vid) => {
            const dateStr = new Date(vid.publishedAt).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              year: "numeric",
            });

            return (
              <div
                key={vid.id}
                className="group relative bg-white rounded-sm overflow-hidden border border-slate-200 hover:border-slate-300 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between"
              >
                {/* 16:9 Thumbnail Cover */}
                <div
                  className="relative aspect-video bg-black overflow-hidden cursor-pointer"
                  onClick={() => setSelectedVideo(vid)}
                >
                  <img
                    src={vid.thumbnailUrl}
                    alt={vid.title}
                    className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-300"
                  />
                  {/* Play Button Overlay */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                    <div className="w-10 h-10 rounded-sm bg-red-600 text-white flex items-center justify-center shadow-md">
                      <Play className="w-4 h-4 fill-white ml-0.5" />
                    </div>
                  </div>

                  {vid.isShort && (
                    <span className="absolute top-2 right-2 bg-red-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-none shadow-xs">
                      Shorts
                    </span>
                  )}
                </div>

                {/* Details Card */}
                <div className="p-3.5 space-y-2.5 flex-1 flex flex-col justify-between">
                  <div>
                    <h3
                      onClick={() => setSelectedVideo(vid)}
                      className="text-xs font-semibold text-slate-900 line-clamp-2 hover:text-red-600 cursor-pointer transition-colors leading-snug"
                      title={vid.title}
                    >
                      {vid.title}
                    </h3>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 font-medium text-slate-700">
                        <Eye className="w-3.5 h-3.5 text-red-600" />
                        {vid.viewCount}
                      </span>
                      <span className="flex items-center gap-1 font-medium text-slate-700">
                        <ThumbsUp className="w-3.5 h-3.5 text-red-600" />
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
            <div className="aspect-video w-full bg-black">
              <iframe
                src={`${selectedVideo.embedUrl}?autoplay=1&rel=0`}
                title={selectedVideo.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="w-full h-full border-none"
              />
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
                    Watch on YouTube
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
