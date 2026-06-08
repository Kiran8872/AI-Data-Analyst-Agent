import type { NextConfig } from "next";

const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "https://ai-data-analyst-agent-backend.onrender.com").replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/datasets/:path*",
        destination: `${apiUrl}/datasets/:path*`,
      },
      {
        source: "/chat/:path*",
        destination: `${apiUrl}/chat/:path*`,
      },
      {
        source: "/admin/:path*",
        destination: `${apiUrl}/admin/:path*`,
      },
      {
        source: "/users/:path*",
        destination: `${apiUrl}/users/:path*`,
      },
      {
        source: "/token",
        destination: `${apiUrl}/token`,
      },
    ];
  },
};

export default nextConfig;
