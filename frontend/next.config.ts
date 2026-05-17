import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Strict React mode — catches lifecycle issues early
  reactStrictMode: true,

  // Required for Docker multi-stage build (copies minimal server into .next/standalone)
  output: 'standalone',

  // Disable powered-by header (minor security hardening)
  poweredByHeader: false,

  // Security headers for all pages
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        ],
      },
    ];
  },

  // API proxy rewrites — all /api calls route through Next.js to the backend
  // This hides the backend URL from the browser (no CORS headers needed on backend from browser)
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.BACKEND_URL ?? 'http://localhost:8000'}/api/v1/:path*`,
      },
    ];
  },

  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.financialmodelingprep.com',
        pathname: '/symbol/**',
      },
    ],
  },

  // Bundle pages router dependencies (stable in Next.js 15)
  ...(process.env.ANALYZE === 'true' && {
    bundlePagesRouterDependencies: true,
  }),
};

export default nextConfig;
