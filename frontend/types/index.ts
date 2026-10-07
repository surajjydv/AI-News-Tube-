export type ContentType = 'post' | 'reel' | 'story' | 'carousel';
export type AspectRatio = '1:1' | '4:5' | '9:16';

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
