/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  readonly DATABASE_URL:   string; // set manually
  readonly POSTGRES_URL:   string; // injected by Vercel's Neon integration
  readonly RESEND_API_KEY: string;
  readonly FROM_EMAIL:     string;
  readonly ADMIN_EMAIL:    string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
