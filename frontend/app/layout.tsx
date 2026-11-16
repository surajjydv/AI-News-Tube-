import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NewsTube Studio | 24/7 AI Broadcast & YouTube Distribution",
  description: "Autonomous Broadcast Newsroom, 24/7 Continuous YouTube Live Engine & Multi-Platform Distribution",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased font-sans"
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
