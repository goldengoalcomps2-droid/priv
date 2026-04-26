/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
  transpilePackages: ["@fleetpro/db", "@fleetpro/agents"],
};

export default nextConfig;
