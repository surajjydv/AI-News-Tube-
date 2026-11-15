"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  Key,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Eye,
  EyeOff,
  Zap,
  Send,
  Save,
  Check,
  ShieldCheck,
  Globe,
} from "lucide-react";

const InstagramLogo: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="1" ry="1"></rect>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
  </svg>
);

const YouTubeLogo: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
);

export const PlatformSettings: React.FC = () => {
  const [platforms, setPlatforms] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [savingPlatform, setSavingPlatform] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<Record<string, boolean>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});

  // Inputs state
  const [groqKey, setGroqKey] = useState("");
  const [igToken, setIgToken] = useState("");
  const [igPageId, setIgPageId] = useState("");
  const [ytStreamKey, setYtStreamKey] = useState("");
  const [tgToken, setTgToken] = useState("");
  const [tgChannel, setTgChannel] = useState("");
  const [twApiKey, setTwApiKey] = useState("");
  const [twApiSecret, setTwApiSecret] = useState("");
  const [twAccessToken, setTwAccessToken] = useState("");
  const [twTokenSecret, setTwTokenSecret] = useState("");
  const [fbToken, setFbToken] = useState("");
  const [fbPageId, setFbPageId] = useState("");

  const loadPlatformsData = async () => {
    setLoading(true);
    try {
      const data = await api.getPlatforms();
      setPlatforms(data);

      if (data.groq) {
        setGroqKey(data.groq.api_key || "");
      }
      if (data.instagram) {
        setIgToken(data.instagram.token || "");
        setIgPageId(data.instagram.page_id || "");
      }
      if (data.youtube) {
        setYtStreamKey(data.youtube.stream_key || "");
      }
      if (data.telegram) {
        setTgToken(data.telegram.bot_token || "");
        setTgChannel(data.telegram.channel_id || "");
      }
      if (data.twitter) {
        setTwApiKey(data.twitter.api_key || "");
        setTwApiSecret(data.twitter.api_secret || "");
        setTwAccessToken(data.twitter.access_token || "");
        setTwTokenSecret(data.twitter.access_token_secret || "");
      }
      if (data.facebook) {
        setFbToken(data.facebook.token || "");
        setFbPageId(data.facebook.page_id || "");
      }
    } catch (err) {
      console.warn("Could not load platforms from backend:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlatformsData();
  }, []);

  const handleSave = async (platform: string, credentials: Record<string, any>) => {
    setSavingPlatform(platform);
    try {
      const res = await api.connectPlatform(platform, credentials);
      if (res.status === "success") {
        setSaveSuccess((prev) => ({ ...prev, [platform]: true }));
        setTimeout(() => {
          setSaveSuccess((prev) => ({ ...prev, [platform]: false }));
        }, 3000);
        await loadPlatformsData();
      }
    } catch (err) {
      console.error(`Failed to save ${platform}:`, err);
    } finally {
      setSavingPlatform(null);
    }
  };

  const handleToggle = async (platform: string, enabled: boolean) => {
    try {
      await api.togglePlatform(platform, enabled);
      setPlatforms((prev) => ({
        ...prev,
        [platform]: { ...prev[platform], enabled },
      }));
    } catch (err) {
      console.error(`Failed to toggle ${platform}:`, err);
    }
  };

  const toggleShowKey = (field: string) => {
    setShowKeys((prev) => ({ ...prev, [field]: !prev[field] }));
  };

  const connectedCount = Object.values(platforms).filter((p: any) => p?.connected).length;
  const totalCount = Object.keys(platforms).length || 6;

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-sm p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="p-2 rounded-sm bg-rose-50 border border-rose-200 text-rose-600">
              <Key className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">API Keys & Automation</h1>
          </div>
          <p className="text-xs text-slate-500">
            Paste your account credentials once to automate publishing across all platforms.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs font-semibold text-slate-700 block">
              {connectedCount} of {totalCount} Connected
            </span>
            <span className="text-[11px] text-slate-400">All tokens encrypted locally</span>
          </div>
          <button
            onClick={loadPlatformsData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 border border-slate-300 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-rose-600" : ""}`} />
            Sync
          </button>
        </div>
      </div>

      {/* Grid of Platform Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* 1. Groq AI Brain */}
        <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-sm bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center font-bold text-sm">
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Groq AI Brain</h3>
                  <p className="text-[11px] text-slate-500">Powers script generation & fact checking</p>
                </div>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold border ${
                  platforms.groq?.connected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {platforms.groq?.connected ? "Ready" : "Not Set"}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Groq API Key</label>
                <div className="relative">
                  <input
                    type={showKeys["groq"] ? "text" : "password"}
                    value={groqKey}
                    onChange={(e) => setGroqKey(e.target.value)}
                    placeholder="gsk_..."
                    className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 pr-9 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey("groq")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showKeys["groq"] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Get free key from console.groq.com</p>
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSave("groq", { api_key: groqKey })}
            disabled={savingPlatform === "groq"}
            className="w-full py-2 px-3 rounded-sm text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white flex items-center justify-center gap-1.5 transition-colors shadow-xs"
          >
            {savingPlatform === "groq" ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : saveSuccess["groq"] ? (
              <Check className="w-3.5 h-3.5 text-emerald-200" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saveSuccess["groq"] ? "Saved Successfully" : "Save Groq Key"}
          </button>
        </div>

        {/* 2. Instagram */}
        <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-sm bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center font-bold text-sm">
                  <InstagramLogo className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Instagram Meta API</h3>
                  <p className="text-[11px] text-slate-500">Auto-publish 9:16 Reels and photos</p>
                </div>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold border ${
                  platforms.instagram?.connected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {platforms.instagram?.connected ? "Connected" : "Not Set"}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">User / Graph Access Token</label>
                <div className="relative">
                  <input
                    type={showKeys["ig"] ? "text" : "password"}
                    value={igToken}
                    onChange={(e) => setIgToken(e.target.value)}
                    placeholder="EAABw..."
                    className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 pr-9 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey("ig")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showKeys["ig"] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Instagram Business Account ID</label>
                <input
                  type="text"
                  value={igPageId}
                  onChange={(e) => setIgPageId(e.target.value)}
                  placeholder="178414..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-rose-500 focus:bg-white"
                />
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSave("instagram", { token: igToken, page_id: igPageId })}
            disabled={savingPlatform === "instagram"}
            className="w-full py-2 px-3 rounded-sm text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white flex items-center justify-center gap-1.5 transition-colors shadow-xs"
          >
            {savingPlatform === "instagram" ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : saveSuccess["instagram"] ? (
              <Check className="w-3.5 h-3.5 text-emerald-200" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saveSuccess["instagram"] ? "Saved Successfully" : "Save Instagram Keys"}
          </button>
        </div>

        {/* 3. YouTube */}
        <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-sm bg-red-50 border border-red-200 text-red-600 flex items-center justify-center font-bold text-sm">
                  <YouTubeLogo className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">YouTube Studio & RTMP</h3>
                  <p className="text-[11px] text-slate-500">Video uploads and 24/7 RTMP stream</p>
                </div>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold border ${
                  platforms.youtube?.connected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {platforms.youtube?.connected ? "Ready" : "Not Set"}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">YouTube Live Stream Key</label>
                <div className="relative">
                  <input
                    type={showKeys["yt"] ? "text" : "password"}
                    value={ytStreamKey}
                    onChange={(e) => setYtStreamKey(e.target.value)}
                    placeholder="xxxx-xxxx-xxxx-xxxx-xxxx"
                    className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 pr-9 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey("yt")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showKeys["yt"] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">Copy from YouTube Live Studio Desk</p>
              </div>

              <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-sm text-[11px] text-slate-600 flex items-center justify-between">
                <span>OAuth VOD Upload (`data/token.json`):</span>
                <span className="font-semibold text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Synchronized
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSave("youtube", { stream_key: ytStreamKey })}
            disabled={savingPlatform === "youtube"}
            className="w-full py-2 px-3 rounded-sm text-xs font-semibold bg-red-600 hover:bg-red-700 text-white flex items-center justify-center gap-1.5 transition-colors shadow-xs"
          >
            {savingPlatform === "youtube" ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : saveSuccess["youtube"] ? (
              <Check className="w-3.5 h-3.5 text-emerald-200" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saveSuccess["youtube"] ? "Saved Successfully" : "Save YouTube Stream Key"}
          </button>
        </div>

        {/* 4. Telegram */}
        <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-sm bg-sky-50 border border-sky-200 text-sky-600 flex items-center justify-center font-bold text-sm">
                  <Send className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Telegram Channel Bot</h3>
                  <p className="text-[11px] text-slate-500">Auto-broadcast news bulletins to channel</p>
                </div>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold border ${
                  platforms.telegram?.connected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {platforms.telegram?.connected ? "Verified" : "Not Set"}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Telegram Bot Token</label>
                <div className="relative">
                  <input
                    type={showKeys["tg"] ? "text" : "password"}
                    value={tgToken}
                    onChange={(e) => setTgToken(e.target.value)}
                    placeholder="123456789:ABCdefGHIjkLMNopQRstUVwxyZ"
                    className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 pr-9 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey("tg")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showKeys["tg"] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Channel ID / Username</label>
                <input
                  type="text"
                  value={tgChannel}
                  onChange={(e) => setTgChannel(e.target.value)}
                  placeholder="@YourChannel or -100123456789"
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white"
                />
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSave("telegram", { bot_token: tgToken, channel_id: tgChannel })}
            disabled={savingPlatform === "telegram"}
            className="w-full py-2 px-3 rounded-sm text-xs font-semibold bg-sky-600 hover:bg-sky-700 text-white flex items-center justify-center gap-1.5 transition-colors shadow-xs"
          >
            {savingPlatform === "telegram" ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : saveSuccess["telegram"] ? (
              <Check className="w-3.5 h-3.5 text-emerald-200" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saveSuccess["telegram"] ? "Verified & Saved" : "Save & Verify Telegram"}
          </button>
        </div>

        {/* 5. Twitter / X */}
        <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-sm bg-slate-100 border border-slate-300 text-slate-900 flex items-center justify-center font-bold text-sm">
                  𝕏
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Twitter / X API v2</h3>
                  <p className="text-[11px] text-slate-500">Auto-post breaking tweets & video clips</p>
                </div>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold border ${
                  platforms.twitter?.connected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {platforms.twitter?.connected ? "Connected" : "Not Set"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">API Key</label>
                <input
                  type="password"
                  value={twApiKey}
                  onChange={(e) => setTwApiKey(e.target.value)}
                  placeholder="Consumer Key"
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-1.5 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-800"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">API Secret</label>
                <input
                  type="password"
                  value={twApiSecret}
                  onChange={(e) => setTwApiSecret(e.target.value)}
                  placeholder="Consumer Secret"
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-1.5 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-800"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Access Token</label>
                <input
                  type="password"
                  value={twAccessToken}
                  onChange={(e) => setTwAccessToken(e.target.value)}
                  placeholder="User Token"
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-1.5 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-800"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-700 mb-1">Token Secret</label>
                <input
                  type="password"
                  value={twTokenSecret}
                  onChange={(e) => setTwTokenSecret(e.target.value)}
                  placeholder="User Secret"
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-1.5 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-800"
                />
              </div>
            </div>
          </div>

          <button
            onClick={() =>
              handleSave("twitter", {
                api_key: twApiKey,
                api_secret: twApiSecret,
                access_token: twAccessToken,
                access_token_secret: twTokenSecret,
              })
            }
            disabled={savingPlatform === "twitter"}
            className="w-full py-2 px-3 rounded-sm text-xs font-semibold bg-slate-900 hover:bg-black text-white flex items-center justify-center gap-1.5 transition-colors shadow-xs"
          >
            {savingPlatform === "twitter" ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : saveSuccess["twitter"] ? (
              <Check className="w-3.5 h-3.5 text-emerald-200" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saveSuccess["twitter"] ? "Saved Successfully" : "Save Twitter Credentials"}
          </button>
        </div>

        {/* 6. Facebook */}
        <div className="bg-white rounded-sm p-5 border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-sm bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center font-bold text-sm">
                  <Globe className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Facebook Page API</h3>
                  <p className="text-[11px] text-slate-500">Auto-publish updates to Facebook page</p>
                </div>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold border ${
                  platforms.facebook?.connected
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {platforms.facebook?.connected ? "Connected" : "Not Set"}
              </span>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Page Access Token</label>
                <div className="relative">
                  <input
                    type={showKeys["fb"] ? "text" : "password"}
                    value={fbToken}
                    onChange={(e) => setFbToken(e.target.value)}
                    placeholder="EAABw..."
                    className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 pr-9 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey("fb")}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showKeys["fb"] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Facebook Page ID</label>
                <input
                  type="text"
                  value={fbPageId}
                  onChange={(e) => setFbPageId(e.target.value)}
                  placeholder="10583729..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-sm p-2 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white"
                />
              </div>
            </div>
          </div>

          <button
            onClick={() => handleSave("facebook", { token: fbToken, page_id: fbPageId })}
            disabled={savingPlatform === "facebook"}
            className="w-full py-2 px-3 rounded-sm text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-1.5 transition-colors shadow-xs"
          >
            {savingPlatform === "facebook" ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : saveSuccess["facebook"] ? (
              <Check className="w-3.5 h-3.5 text-emerald-200" />
            ) : (
              <Save className="w-3.5 h-3.5" />
            )}
            {saveSuccess["facebook"] ? "Saved Successfully" : "Save Facebook Keys"}
          </button>
        </div>
      </div>
    </div>
  );
};
