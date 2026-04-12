import { neon } from '@neondatabase/serverless';

export function getDb() {
  return neon(import.meta.env.DATABASE_URL);
}
