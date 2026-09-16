import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  async rewrites() {
    // Local Next.js proxies only the V2 namespace to the separate Python server.
    // Vercel routes this namespace to api/index.py via vercel.json instead.
    return process.env.VERCEL ? [] : [
      { source: "/api/v2/:path*", destination: "http://127.0.0.1:8100/api/v2/:path*" },
    ];
  },
};

export default nextConfig;
