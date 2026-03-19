// API Configuration
// Uses environment variable in production, falls back to localhost in development
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default API_BASE_URL;
