"use client";

import React from "react";
import { useStudioStore } from "@/lib/store";
import { Calendar, Clock, Trash2, Send } from "lucide-react";

export const ScheduledQueue: React.FC = () => {
  const { scheduledPosts, removeScheduledPost, publishNow, accounts } = useStudioStore();

  const getAccountName = (accId: string) => {
    const acc = accounts.find((a) => a.id === accId);
    return acc ? `@${acc.username}` : "@account";
  };

  return (
    <div className="bg-white rounded-sm p-5 border border-slate-200 space-y-6 shadow-xs">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-rose-600" />
            Publishing Schedule & Queue
          </h2>
          <p className="text-xs text-slate-500">Monitor queued media items and manage automated delivery slots</p>
        </div>
        <span className="text-xs text-slate-500 font-medium">
          {scheduledPosts.length} posts in queue
        </span>
      </div>

      {scheduledPosts.length === 0 ? (
        <div className="text-center py-12 border border-dashed border-slate-300 rounded-sm bg-slate-50">
          <Clock className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <p className="text-sm text-slate-700 font-semibold">Queue is empty</p>
          <p className="text-xs text-slate-500 mt-0.5">Use the Studio to generate and schedule your next content drop.</p>
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
                className="bg-white rounded-sm p-3.5 border border-slate-200 flex gap-4 hover:border-slate-300 shadow-xs transition-colors"
              >
                {/* Media Thumbnail */}
                <div className="w-20 h-20 rounded-sm overflow-hidden shrink-0 relative bg-black border border-slate-200">
                  <img
                    src={post.asset.thumbnailUrl || post.asset.imageUrl}
                    alt="Thumbnail"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-1 right-1 bg-black/80 px-1 py-0.5 rounded-none text-[9px] text-white font-medium">
                    {post.asset.contentType.toUpperCase()}
                  </div>
                </div>

                {/* Details */}
                <div className="flex-1 flex flex-col justify-between overflow-hidden">
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-xs font-semibold text-rose-600 truncate">
                        {getAccountName(post.accountId)}
                      </span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded-sm font-medium border ${
                          post.status === "published"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                            : post.status === "publishing"
                            ? "bg-amber-50 text-amber-700 border-amber-300"
                            : "bg-sky-50 text-sky-700 border-sky-300"
                        }`}
                      >
                        {post.status.toUpperCase()}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 line-clamp-2 leading-snug">
                      {post.asset.caption}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-rose-600" />
                      <span>{formattedDate}</span>
                      {post.recurrence !== "none" && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-sm bg-purple-50 text-purple-700 border border-purple-200">
                          {post.recurrence}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {post.status === "scheduled" && (
                        <button
                          onClick={() => publishNow(post.id)}
                          className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                          title="Trigger Publish Now"
                        >
                          <Send className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => removeScheduledPost(post.id)}
                        className="p-1 text-slate-400 hover:text-red-600 transition-colors"
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
