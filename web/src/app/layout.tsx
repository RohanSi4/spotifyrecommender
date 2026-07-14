import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://signal-recommender.vercel.app"),
  title: "Signal | Find your next song",
  description:
    "Search any real Spotify song or connect your listening history to find music worth playing next.",
  openGraph: {
    title: "Signal | Good taste in. Better songs out.",
    description:
      "Start with any Spotify song and follow real artist connections somewhere new.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Signal | Good taste in. Better songs out.",
    description:
      "Start with any Spotify song and follow real artist connections somewhere new.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body>{children}</body>
    </html>
  );
}
