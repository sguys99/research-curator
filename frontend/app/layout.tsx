import type { Metadata } from "next";
import { IBM_Plex_Sans_KR, Sora } from "next/font/google";

import AuthProvider from "@/providers/auth-provider";
import QueryProvider from "@/providers/query-provider";
import ToastProvider from "@/providers/toast-provider";

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
    <html lang="en" suppressHydrationWarning>
      <body className={`${sora.variable} ${plexSansKr.variable} antialiased`}>
        <QueryProvider>
          <AuthProvider>
            <ToastProvider>{children}</ToastProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
