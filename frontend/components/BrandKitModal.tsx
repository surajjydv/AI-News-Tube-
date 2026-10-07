"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { Palette, Save, CheckCircle2, Sparkles, Hash, MessageSquare } from "lucide-react";

export const BrandKitModal: React.FC = () => {
  const { brandKits, activeAccountId, updateBrandKit, accounts } = useStudioStore();
  const currentKit = brandKits[activeAccountId] || {
    brandName: "My Brand",
    primaryColor: "#E07A5F",
    secondaryColor: "#F4F1DE",
    fontTone: "Warm & Artisanal",
    signatureHashtags: ["#BrandExclusive", "#InstagramAI"],
    ctaText: "Link in bio to shop!",
  };

  const activeAccount = accounts.find((a) => a.id === activeAccountId);

  const [brandName, setBrandName] = useState(currentKit.brandName);
  const [primaryColor, setPrimaryColor] = useState(currentKit.primaryColor);
  const [secondaryColor, setSecondaryColor] = useState(currentKit.secondaryColor);
  const [fontTone, setFontTone] = useState(currentKit.fontTone);
  const [ctaText, setCtaText] = useState(currentKit.ctaText);
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateBrandKit(activeAccountId, {
      brandName,
      primaryColor,
      secondaryColor,
      fontTone,
      ctaText,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Palette className="w-4 h-4 text-pink-400" />
            Brand Kit & AI Personality ({activeAccount?.displayName || "Account"})
          </h2>
          <p className="text-xs text-slate-400">
            Configure design palettes, tone guidelines, and signature signatures applied to every generated reel & post
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-4 max-w-2xl">
        {/* Brand Name */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Brand Identity / Store Name</label>
          <input
            type="text"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-pink-500"
          />
        </div>

        {/* Color Palette */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Primary Brand Color</label>
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-xl p-2">
              <input
                type="color"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="w-7 h-7 rounded border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs text-slate-300 font-mono">{primaryColor}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Secondary Accent Color</label>
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 rounded-xl p-2">
              <input
                type="color"
                value={secondaryColor}
                onChange={(e) => setSecondaryColor(e.target.value)}
                className="w-7 h-7 rounded border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs text-slate-300 font-mono">{secondaryColor}</span>
            </div>
          </div>
        </div>

        {/* Brand Tone */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5">Tone of Voice Engine</label>
          <select
            value={fontTone}
            onChange={(e) => setFontTone(e.target.value as any)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-pink-500 cursor-pointer"
          >
            <option value="Warm & Artisanal">Warm & Artisanal</option>
            <option value="High Energy">High Energy & Viral</option>
            <option value="Luxury">Luxury & Elite</option>
            <option value="Professional">Professional & Authority</option>
            <option value="Minimal">Minimal & Direct</option>
          </select>
        </div>

        {/* Call to Action */}
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-pink-400" />
            Standard Call To Action (Appended to Captions)
          </label>
          <input
            type="text"
            value={ctaText}
            onChange={(e) => setCtaText(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-pink-500"
          />
        </div>

        {/* Save Button */}
        <div className="pt-3">
          <button
            type="submit"
            className="py-2.5 px-6 rounded-xl font-bold text-xs bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 text-white shadow-md shadow-pink-500/20 flex items-center gap-2 transition-all"
          >
            {saved ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Brand Kit Saved!
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Brand Kit Settings
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
