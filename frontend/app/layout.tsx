import type { Metadata } from "next";
import { IBM_Plex_Sans_KR, Sora } from "next/font/google";
import "./globals.css";

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
});

const plexSansKr = IBM_Plex_Sans_KR({
  subsets: ["latin"],
  variable: "--font-plex",
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Research Curator",
  description: "AI-powered research curation for focused teams.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${sora.variable} ${plexSansKr.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
