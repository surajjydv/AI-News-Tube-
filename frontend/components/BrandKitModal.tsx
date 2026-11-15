"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import { Palette, Save, CheckCircle2, MessageSquare } from "lucide-react";

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
    <div className="bg-white rounded-sm p-5 border border-slate-200 space-y-6 shadow-xs">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Palette className="w-4 h-4 text-rose-600" />
            Brand Kit & Personality ({activeAccount?.displayName || "Account"})
          </h2>
          <p className="text-xs text-slate-500">
            Configure design palettes, tone guidelines, and signature signatures applied to every generated asset
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-4 max-w-2xl">
        {/* Brand Name */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">Brand Identity / Store Name</label>
          <input
            type="text"
            value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-sm p-2.5 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
          />
        </div>

        {/* Color Palette */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Primary Brand Color</label>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-sm p-2">
              <input
                type="color"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="w-6 h-6 rounded-none border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs text-slate-700 font-mono">{primaryColor}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Secondary Accent Color</label>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-300 rounded-sm p-2">
              <input
                type="color"
                value={secondaryColor}
                onChange={(e) => setSecondaryColor(e.target.value)}
                className="w-6 h-6 rounded-none border-none cursor-pointer bg-transparent"
              />
              <span className="text-xs text-slate-700 font-mono">{secondaryColor}</span>
            </div>
          </div>
        </div>

        {/* Brand Tone */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">Tone of Voice Engine</label>
          <select
            value={fontTone}
            onChange={(e) => setFontTone(e.target.value as any)}
            className="w-full bg-white border border-slate-300 rounded-sm p-2.5 text-xs text-slate-800 focus:outline-none focus:border-rose-500 cursor-pointer"
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
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-rose-600" />
            Standard Call To Action
          </label>
          <input
            type="text"
            value={ctaText}
            onChange={(e) => setCtaText(e.target.value)}
            className="w-full bg-white border border-slate-300 rounded-sm p-2.5 text-xs text-slate-800 focus:outline-none focus:border-rose-500"
          />
        </div>

        {/* Save Button */}
        <div className="pt-2">
          <button
            type="submit"
            className="py-2 px-5 rounded-sm font-semibold text-xs bg-rose-600 hover:bg-rose-700 text-white flex items-center gap-2 transition-colors shadow-xs"
          >
            {saved ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-200" />
                Brand Kit Saved
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                Save Brand Kit Settings
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
