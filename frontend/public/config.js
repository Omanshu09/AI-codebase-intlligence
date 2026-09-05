// Runtime config -- loaded as a plain script BEFORE the app bundle, so you
// can change the backend URL by editing this one file and redeploying the
// static site, without needing to touch Vercel's env vars or rebuild with
// a different VITE_API_URL baked in.
window.__API_BASE_URL__ = "https://ai-codebase-intlligence.onrender.com";
