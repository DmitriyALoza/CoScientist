import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow backend API calls during server-side rendering in Docker
  experimental: {
    serverActions: { allowedOrigins: ["localhost:3000", "frontend:3000"] },
  },
};

export default nextConfig;
