"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { PromptStudio } from "@/components/PromptStudio";
import { MediaPreview } from "@/components/MediaPreview";
import { SchedulerModal } from "@/components/SchedulerModal";
import { ScheduledQueue } from "@/components/ScheduledQueue";
import { BrandKitModal } from "@/components/BrandKitModal";
import { AnalyticsDashboard } from "@/components/AnalyticsDashboard";
import { YouTubeStudio } from "@/components/YouTubeStudio";
import { PlatformSettings } from "@/components/PlatformSettings";
import { useStudioStore } from "@/lib/store";

export default function Home() {
  const { activeTab, initBackendData } = useStudioStore();
  const [schedulerOpen, setSchedulerOpen] = useState(false);

  useEffect(() => {
    initBackendData();
  }, [initBackendData]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-rose-100 selection:text-rose-700">
      {/* Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-8 space-y-6">
        {activeTab === "studio" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Prompt Studio Input (5 Columns on Large) */}
            <div className="lg:col-span-5 space-y-6">
              <PromptStudio />
            </div>

            {/* Generated Media Preview (7 Columns on Large) */}
            <div className="lg:col-span-7 space-y-6">
              <MediaPreview onOpenScheduler={() => setSchedulerOpen(true)} />
            </div>
          </div>
        )}

        {activeTab === "platforms" && <PlatformSettings />}

        {activeTab === "youtube" && <YouTubeStudio />}

        {activeTab === "schedule" && <ScheduledQueue />}

        {activeTab === "analytics" && <AnalyticsDashboard />}

        {activeTab === "brandkit" && <BrandKitModal />}
      </main>

      {/* Scheduler Modal */}
      <SchedulerModal isOpen={schedulerOpen} onClose={() => setSchedulerOpen(false)} />

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        NewsTube & OmniBlast Studio • Automated Multi-Platform Distribution (YouTube, Instagram, Telegram, Twitter, Facebook)
      </footer>
    </div>
  );
}
