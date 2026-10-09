const configured =
  import.meta.env.VITE_BACKEND_BASE_URL ?? import.meta.env.VITE_API_BASE_URL;

// In local development fall back to the FastAPI default. A production build
// (e.g. GitHub Pages) without a configured backend must NOT silently point at
// the visitor's own localhost — the UI shows "backend not configured" instead.
export const BACKEND_BASE_URL: string | null =
  configured || (import.meta.env.DEV ? 'http://localhost:8000' : null);

export const BACKEND_CONFIGURED = BACKEND_BASE_URL !== null;
