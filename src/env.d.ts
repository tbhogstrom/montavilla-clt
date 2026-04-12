/// <reference path="../.astro/types.d.ts" />

interface ImportMetaEnv {
  readonly DATABASE_URL:  string;
  readonly RESEND_API_KEY: string;
  readonly FROM_EMAIL:    string;
  readonly ADMIN_EMAIL:   string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
