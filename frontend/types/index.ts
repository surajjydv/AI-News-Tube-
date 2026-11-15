export type ContentType = 'post' | 'reel' | 'story' | 'carousel' | 'video';
export type AspectRatio = '1:1' | '4:5' | '9:16' | '16:9';
export type ActiveTab = 'studio' | 'schedule' | 'analytics' | 'brandkit' | 'youtube' | 'platforms';

export interface Account {
  id: string;
  username: string;
  displayName: string;
  avatarUrl: string;
  followers: number;
  category: string;
  isConnected: boolean;
}

export interface MediaAsset {
  imageUrl: string;
  videoUrl: string;
  audioUrl: string;
  thumbnailUrl: string;
  caption: string;
  hashtags: string[];
  aspectRatio: AspectRatio;
  contentType: ContentType;
  prompt: string;
  createdAt: string;
}

export interface ScheduledPost {
  id: string;
  accountId: string;
  asset: MediaAsset;
  scheduledTime: string;
  status: 'scheduled' | 'publishing' | 'published' | 'failed';
  recurrence: 'none' | 'daily' | 'weekly' | 'monthly';
}

export interface BrandKit {
  brandName: string;
  primaryColor: string;
  secondaryColor: string;
  fontTone: string;
  logoUrl?: string;
  signatureHashtags: string[];
  ctaText: string;
}

export interface MetricItem {
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
}

export interface YouTubeChannel {
  id: string;
  title: string;
  description: string;
  customUrl: string;
  avatarUrl: string;
  subscriberCount: number;
  viewCount: number;
  videoCount: number;
  country: string;
  publishedAt: string;
}

export interface YouTubeVideo {
  id: string;
  title: string;
  description: string;
  publishedAt: string;
  thumbnailUrl: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  duration: string;
  youtubeUrl: string;
  embedUrl: string;
  isShort: boolean;
}

export interface YouTubeStreamInfo {
  rtmpUrl: string;
  streamKeyMasked: string;
  hasKey: boolean;
  targetResolution: string;
  audioCodec: string;
  videoCodec: string;
  activeStreamEntry: string;
}

export interface PlatformConfig {
  name: string;
  icon: string;
  color: string;
  enabled: boolean;
  connected: boolean;
  content_types?: string[];
  interval_hours?: number;
  api_key?: string;
  api_secret?: string;
  access_token?: string;
  access_token_secret?: string;
  bearer_token?: string;
  bot_token?: string;
  channel_id?: string;
  token?: string;
  page_id?: string;
  stream_key?: string;
}
