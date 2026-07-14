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
  title: "Signal | Explainable music recommendations",
  description:
    "Pick a song or mood and see transparent recommendations from a deterministic audio-feature ranking engine.",
  openGraph: {
    title: "Signal | Find music by feel",
    description:
      "A credential-free, explainable music recommendation demo by Rohan Singh.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Signal | Find music by feel",
    description:
      "A credential-free, explainable music recommendation demo by Rohan Singh.",
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
