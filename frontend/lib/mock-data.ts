import { Account, BrandKit, MediaAsset, MetricItem, ScheduledPost } from "@/types";

export const MOCK_ACCOUNTS: Account[] = [
  {
    id: "acc_1",
    username: "artisan_bakery_nyc",
    displayName: "Artisan Bakery NYC",
    avatarUrl: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=150&auto=format&fit=crop&q=80",
    followers: 24800,
    category: "Food & Beverage",
    isConnected: true,
  },
  {
    id: "acc_2",
    username: "apex_fitness_club",
    displayName: "Apex Fitness Club",
    avatarUrl: "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=150&auto=format&fit=crop&q=80",
    followers: 61200,
    category: "Health & Fitness",
    isConnected: true,
  },
  {
    id: "acc_3",
    username: "lumina_skincare",
    displayName: "Lumina Organic Skincare",
    avatarUrl: "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=150&auto=format&fit=crop&q=80",
    followers: 43500,
    category: "Beauty & Wellness",
    isConnected: false,
  },
];

export const MOCK_BRAND_KITS: Record<string, BrandKit> = {
  acc_1: {
    brandName: "Artisan Bakery NYC",
    primaryColor: "#E07A5F",
    secondaryColor: "#F4F1DE",
    fontTone: "Warm & Artisanal",
    signatureHashtags: ["#NYCBakery", "#FreshSourdough", "#ArtisanBread", "#PastryLovers"],
    ctaText: "Order freshly baked treats now via link in bio!",
  },
  acc_2: {
    brandName: "Apex Fitness Club",
    primaryColor: "#3D405B",
    secondaryColor: "#81B29A",
    fontTone: "High Energy",
    signatureHashtags: ["#ApexFitness", "#FitFam", "#WorkoutMotivation", "#StrengthTraining"],
    ctaText: "Book your 7-day free trial today!",
  },
  acc_3: {
    brandName: "Lumina Skincare",
    primaryColor: "#81B29A",
    secondaryColor: "#F2CC8F",
    fontTone: "Luxury",
    signatureHashtags: ["#CleanBeauty", "#GlowRoutine", "#OrganicSkinCare"],
    ctaText: "Experience pure botanicals ? shop 20% off today.",
  },
};

export const INITIAL_GENERATED_ASSET: MediaAsset = {
  imageUrl: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=1080&auto=format&fit=crop&q=80",
  videoUrl: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
  audioUrl: "https://actions.google.com/sounds/v1/ambiences/coffee_shop.ogg",
  thumbnailUrl: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&auto=format&fit=crop&q=80",
  caption: `Weekend Special: Handcrafted Alphonso Mango Gateau!

Indulge in layers of light vanilla sponge, pure mango compote, and delicate white chocolate chantilly cream. Limited 50 batches baked every Saturday morning.

Reserve yours before it sells out! Link in bio.`,
  hashtags: ["#MangoCake", "#ArtisanBaking", "#WeekendSpecials", "#NYCFoodie", "#BakeryLife", "#DessertGoals"],
  aspectRatio: "4:5",
  contentType: "reel",
  prompt: "Promote my bakery new Alphonso mango cake for weekend with irresistible gourmet vibe",
  createdAt: new Date().toISOString(),
};

export const INITIAL_SCHEDULED_POSTS: ScheduledPost[] = [
  {
    id: "sch_1",
    accountId: "acc_1",
    asset: INITIAL_GENERATED_ASSET,
    scheduledTime: new Date(Date.now() + 1000 * 60 * 60 * 4).toISOString(),
    status: "scheduled",
    recurrence: "none",
  },
  {
    id: "sch_2",
    accountId: "acc_1",
    asset: {
      imageUrl: "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=1080&auto=format&fit=crop&q=80",
      videoUrl: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
      audioUrl: "https://actions.google.com/sounds/v1/ambiences/coffee_shop.ogg",
      thumbnailUrl: "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400&auto=format&fit=crop&q=80",
      caption: `Morning Fresh: Hot Butter Croissants straight from the oven at 7:00 AM.`,
      hashtags: ["#CroissantLove", "#BreakfastNYC", "#FreshBakes"],
      aspectRatio: "1:1",
      contentType: "post",
      prompt: "Golden crispy flaky morning croissants fresh from oven promo",
      createdAt: new Date().toISOString(),
    },
    scheduledTime: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    status: "scheduled",
    recurrence: "daily",
  },
];

export const MOCK_METRICS: MetricItem[] = [
  { label: "Total IG Reach", value: "184.2K", change: "+24.8%", isPositive: true },
  { label: "Content Engagement", value: "8.6%", change: "+3.2%", isPositive: true },
  { label: "Auto-Posts Published", value: "42", change: "+12 this week", isPositive: true },
  { label: "Average Reel Views", value: "12.4K", change: "+18.5%", isPositive: true },
];
