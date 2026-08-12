import type { NextConfig } from "next";

// The API is proxied under /api rather than called on its own origin.
//
// Every page here is a client component, so API calls happen in the visitor's
// browser — including on a customer's phone during the demo. Same-origin means
// one public URL to share, no CORS, and no rebuilding the app when a tunnel
// hands out a new hostname (NEXT_PUBLIC_API_URL stays the literal "/api").
//
// API_ORIGIN is server-side only and never reaches the browser.
const apiOrigin = process.env.API_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // NOTE: do not set `turbopack.root` here. It silences the "inferred your
  // workspace root" warning caused by a stray ~/package-lock.json, but it also
  // changes module ids enough to break the React client manifest — dynamic
  // routes like /join/[shopId] then 500 with "Could not find the module ... in
  // the React Client Manifest". The warning is cosmetic; deleting the stray
  // lockfile is the real fix.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiOrigin}/:path*` }];
  },
};

export default nextConfig;
