import type { Metadata } from "next";
import { Inter, Noto_Sans_KR } from "next/font/google";

import AuthProvider from "@/providers/auth-provider";
import QueryProvider from "@/providers/query-provider";
import ToastProvider from "@/providers/toast-provider";

import "./globals.css";

// 영문 폰트: UI/웹에 최적화된 모던한 산세리프체
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

// 한글 폰트: Google & Adobe 협업, 깔끔한 한글 렌더링
const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  variable: "--font-noto",
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Research Curator",
  description: "AI-powered research curation for focused teams.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${notoSansKr.variable} font-sans antialiased`}>
        <QueryProvider>
          <AuthProvider>
            <ToastProvider>{children}</ToastProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
