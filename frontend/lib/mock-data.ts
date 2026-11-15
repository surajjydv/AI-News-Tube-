import { Account, BrandKit, MediaAsset, MetricItem, ScheduledPost } from "@/types";

export const MOCK_ACCOUNTS: Account[] = [
  {
    id: "acc_1",
    username: "SRJUNDERRATED",
    displayName: "SRJ UNDERRATED",
    avatarUrl: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200&h=200&fit=crop",
    followers: 3,
    category: "YouTube & Live Broadcast",
    isConnected: true,
  },
  {
    id: "acc_2",
    username: "srj_underrated",
    displayName: "SRJ Underrated Reels",
    avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&h=200&fit=crop",
    followers: 105,
    category: "Instagram Reels & Shorts",
    isConnected: true,
  },
  {
    id: "acc_3",
    username: "newstube_wire",
    displayName: "NewsTube Breaking Wire",
    avatarUrl: "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=200&h=200&fit=crop",
    followers: 1091,
    category: "Telegram & News Wires",
    isConnected: true,
  },
];

export const MOCK_BRAND_KITS: Record<string, BrandKit> = {
  acc_1: {
    brandName: "SRJ UNDERRATED",
    primaryColor: "#E11D48",
    secondaryColor: "#F59E0B",
    fontTone: "Prime-Time News & Documentary",
    signatureHashtags: ["#TodayNews", "#BreakingNews", "#HindiNews", "#SRJUNDERRATED", "#2MinNews"],
    ctaText: "Subscribe to SRJ UNDERRATED for real-time 24/7 verified breaking updates & ground reports!",
  },
  acc_2: {
    brandName: "SRJ Underrated Reels",
    primaryColor: "#8B5CF6",
    secondaryColor: "#EC4899",
    fontTone: "High Impact Viral Shorts",
    signatureHashtags: ["#ViralReels", "#Shorts", "#TrendingNews", "#InstaNews"],
    ctaText: "Follow @srj_underrated for instant 30-second breaking reels!",
  },
  acc_3: {
    brandName: "NewsTube Breaking Wire",
    primaryColor: "#0284C7",
    secondaryColor: "#38BDF8",
    fontTone: "Instant Editorial Wire",
    signatureHashtags: ["#NewsAlert", "#Breaking", "#IndiaUpdates"],
    ctaText: "Join our Telegram channel for fast ground dispatches & documents.",
  },
};

export const INITIAL_GENERATED_ASSET: MediaAsset = {
  imageUrl: "/thumbnails/story_2m_thumbnail.jpg",
  videoUrl: "/videos/story_2m_video.mp4",
  audioUrl: "/assets/story_2m_audio.mp3",
  thumbnailUrl: "/thumbnails/story_2m_thumbnail.jpg",
  caption: "🔴 बड़ी ख़बर: पश्चिम बंगाल के शांतिनिकेतन में पुलिस मुठभेड़ पर विशेष प्राइम-टाइम रिपोर्ट। 1080p 2.5D ब्रॉडकास्ट ग्राफिक्स एवं सत्यापित ऑन-ग्राउंड प्रेस कवरेज।\n\n👉 24/7 लाइव ब्रॉडकास्ट और ताजा अपडेट्स के लिए SRJ UNDERRATED को सब्सक्राइब करें।",
  hashtags: ["#TodayNews", "#BreakingNews", "#HindiNews", "#SRJUNDERRATED", "#2MinNews"],
  aspectRatio: "16:9",
  contentType: "video",
  prompt: "Man accused of opening fire at cop in Bengal Santiniketan 2-minute special report",
  createdAt: new Date().toISOString(),
};

export const INITIAL_SCHEDULED_POSTS: ScheduledPost[] = [
  {
    id: "sch_1",
    accountId: "acc_1",
    asset: INITIAL_GENERATED_ASSET,
    scheduledTime: new Date(Date.now() + 1000 * 60 * 15).toISOString(),
    status: "scheduled",
    recurrence: "none",
  },
];

export const MOCK_METRICS: MetricItem[] = [
  { label: "Total YouTube Views", value: "1,091", change: "+24.8%", isPositive: true },
  { label: "Published Bulletins", value: "105", change: "+12 this week", isPositive: true },
  { label: "Channel Subscribers", value: "3", change: "Verified API", isPositive: true },
  { label: "Autopublisher Cadence", value: "15 Min", change: "24/7 Active", isPositive: true },
];
