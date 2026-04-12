import { neon } from '@neondatabase/serverless';

export function getDb() {
  // Vercel's Neon integration may inject either name depending on setup method
  const url =
    import.meta.env.DATABASE_URL ||
    import.meta.env.POSTGRES_URL;

  if (!url) throw new Error('No DATABASE_URL or POSTGRES_URL env var found.');
  return neon(url);
}
