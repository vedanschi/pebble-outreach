module.exports = {
  reactStrictMode: true,
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000', // Backend API URL
  },
  images: {
    domains: ['your-image-domain.com'], // Add your image domains here
  },
};