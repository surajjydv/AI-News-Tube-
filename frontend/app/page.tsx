"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { PromptStudio } from "@/components/PromptStudio";
import { MediaPreview } from "@/components/MediaPreview";
import { SchedulerModal } from "@/components/SchedulerModal";
import { ScheduledQueue } from "@/components/ScheduledQueue";
import { BrandKitModal } from "@/components/BrandKitModal";
import { AnalyticsDashboard } from "@/components/AnalyticsDashboard";
import { useStudioStore } from "@/lib/store";

export default function Home() {
  const { activeTab, initBackendData } = useStudioStore();
  const [schedulerOpen, setSchedulerOpen] = useState(false);

  useEffect(() => {
    initBackendData();
  }, [initBackendData]);

  return (
    <div className="min-h-screen bg-[#090A0F] text-slate-100 flex flex-col font-sans selection:bg-pink-500/30 selection:text-pink-300">
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

        {activeTab === "schedule" && <ScheduledQueue />}

        {activeTab === "analytics" && <AnalyticsDashboard />}

        {activeTab === "brandkit" && <BrandKitModal />}
      </main>

      {/* Scheduler Modal */}
      <SchedulerModal isOpen={schedulerOpen} onClose={() => setSchedulerOpen(false)} />

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        AutoInsta B2B AI Studio ? Powered by Neon Database & S3 Storage ? Instagram Automation
      </footer>
    </div>
  );
}
