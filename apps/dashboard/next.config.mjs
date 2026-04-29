/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@fleetpro/db", "@fleetpro/agents"],
};

export default nextConfig;
