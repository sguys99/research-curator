import type { NextConfig } from "next";

// 환경 변수에서 허용된 개발 origin 목록을 읽어옴 (쉼표로 구분)
const allowedDevOrigins = process.env.ALLOWED_DEV_ORIGINS?.split(",").filter(Boolean) ?? [];

const nextConfig: NextConfig = {
  // 개발 환경에서만 사용되며, 프로덕션에서는 무시됨
  ...(allowedDevOrigins.length > 0 && { allowedDevOrigins }),
  compress: true,
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
