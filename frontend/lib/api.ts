import axios from "axios";
import { Account, BrandKit, ContentType, AspectRatio, MediaAsset, ScheduledPost, YouTubeChannel, YouTubeVideo, YouTubeStreamInfo } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/studio";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  // Accounts
  async getAccounts(): Promise<Account[]> {
    const res = await apiClient.get<Account[]>("/accounts");
    return res.data;
  },

  async toggleAccount(accountId: string): Promise<{ id: string; isConnected: boolean }> {
    const res = await apiClient.post(`/accounts/${accountId}/toggle`);
    return res.data;
  },

  // Generate Media Pack
  async getLatestAsset(): Promise<MediaAsset | null> {
    try {
      const res = await apiClient.get<MediaAsset | null>("/latest");
      return res.data;
    } catch {
      return null;
    }
  },

  async generateMedia(payload: {
    prompt: string;
    contentType: ContentType;
    aspectRatio: AspectRatio;
    tone: string;
    accountId: string;
  }): Promise<MediaAsset> {
    const res = await apiClient.post<MediaAsset>("/generate", payload);
    return res.data;
  },

  // Scheduling Queue
  async getSchedule(): Promise<ScheduledPost[]> {
    const res = await apiClient.get<ScheduledPost[]>("/schedule");
    return res.data;
  },

  async schedulePost(payload: {
    accountId: string;
    asset: MediaAsset;
    scheduledTime: string;
    recurrence: string;
  }): Promise<{ status: string; id: string }> {
    const res = await apiClient.post("/schedule", payload);
    return res.data;
  },

  async deleteSchedule(postId: string): Promise<{ status: string }> {
    const res = await apiClient.delete(`/schedule/${postId}`);
    return res.data;
  },

  async publishPost(postId: string): Promise<{ status: string }> {
    const res = await apiClient.post(`/publish/${postId}`);
    return res.data;
  },

  // Brand Kit
  async getBrandKit(accountId: string): Promise<BrandKit> {
    const res = await apiClient.get<BrandKit>(`/brandkit/${accountId}`);
    return res.data;
  },

  async saveBrandKit(accountId: string, brandKit: BrandKit): Promise<void> {
    await apiClient.post(`/brandkit/${accountId}`, brandKit);
  },

  // Real YouTube Data API Methods
  async getYouTubeChannel(): Promise<YouTubeChannel> {
    const res = await axios.get<YouTubeChannel>("http://127.0.0.1:8000/api/youtube/channel");
    return res.data;
  },

  async getYouTubeVideos(maxResults: number = 24): Promise<{ videos: YouTubeVideo[]; total: number }> {
    const res = await axios.get<{ videos: YouTubeVideo[]; total: number }>(`http://127.0.0.1:8000/api/youtube/videos?max_results=${maxResults}`);
    return res.data;
  },

  async getYouTubeStream(): Promise<YouTubeStreamInfo> {
    const res = await axios.get<YouTubeStreamInfo>("http://127.0.0.1:8000/api/youtube/stream");
    return res.data;
  },
};
