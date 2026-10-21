import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // The analysis charts are served by the FastAPI backend, whose URL is
    // only known at runtime through NEXT_PUBLIC_BACKEND_URL. Skipping the
    // image optimizer avoids having to enumerate every host it may run on.
    unoptimized: true,
  },
};

export default nextConfig;
