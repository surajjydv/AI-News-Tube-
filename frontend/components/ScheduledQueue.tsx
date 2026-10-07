"use client";

import React from "react";
import { useStudioStore } from "@/lib/store";
import { Calendar, Clock, Trash2, Send, CheckCircle2, RefreshCw } from "lucide-react";

export const ScheduledQueue: React.FC = () => {
  const { scheduledPosts, removeScheduledPost, publishNow, accounts } = useStudioStore();

  const getAccountName = (accId: string) => {
    const acc = accounts.find((a) => a.id === accId);
    return acc ? `@${acc.username}` : "@account";
  };

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 shadow-xl space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Calendar className="w-4 h-4 text-pink-400" />
            Automated Publishing Schedule & Queue
          </h2>
          <p className="text-xs text-slate-400">Monitor queued AI media items and manage automated delivery slots</p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
          {scheduledPosts.length} Posts in Queue
        </span>
      </div>

      {scheduledPosts.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
          <Clock className="w-10 h-10 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-400 font-semibold">Queue is empty</p>
          <p className="text-xs text-slate-500 mt-0.5">Use the AI Studio to generate and schedule your next content drop.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scheduledPosts.map((post) => {
            const dateObj = new Date(post.scheduledTime);
            const formattedDate = dateObj.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            });

            return (
              <div
                key={post.id}
                className="bg-slate-900/80 rounded-xl p-4 border border-slate-800/90 flex gap-4 hover:border-slate-700 transition-colors shadow-md"
              >
                {/* Media Thumbnail */}
                <div className="w-24 h-24 rounded-lg overflow-hidden shrink-0 relative bg-black border border-slate-700">
                  <img
                    src={post.asset.thumbnailUrl || post.asset.imageUrl}
                    alt="Thumbnail"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-1 right-1 bg-black/70 backdrop-blur-sm px-1.5 py-0.5 rounded text-[9px] text-white font-medium">
                    {post.asset.contentType.toUpperCase()}
                  </div>
                </div>

                {/* Details */}
                <div className="flex-1 flex flex-col justify-between overflow-hidden">
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-xs font-bold text-pink-400 truncate">
                        {getAccountName(post.accountId)}
                      </span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${
                          post.status === "published"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : post.status === "publishing"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : "bg-sky-500/10 text-sky-400 border-sky-500/20"
                        }`}
                      >
                        {post.status.toUpperCase()}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 line-clamp-2 leading-snug">
                      {post.asset.caption}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-pink-400" />
                      <span>{formattedDate}</span>
                      {post.recurrence !== "none" && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          {post.recurrence}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {post.status === "scheduled" && (
                        <button
                          onClick={() => publishNow(post.id)}
                          className="p-1 text-slate-400 hover:text-pink-400 transition-colors"
                          title="Trigger Publish Now"
                        >
                          <Send className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => removeScheduledPost(post.id)}
                        className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                        title="Delete from Queue"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
