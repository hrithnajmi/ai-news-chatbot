import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Apple-like font setup
const inter = Inter({ 
  subsets: ["latin"],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-inter'
});

export const metadata: Metadata = {
  title: "AI News Aggregator",
  description: "Get AI-powered news summaries on any topic",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>{children}</body>
    </html>
  );
}
