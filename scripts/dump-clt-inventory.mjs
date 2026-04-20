#!/usr/bin/env node
/**
 * Dumps inv_clts from Neon into src/data/clt-inventory.json.
 * Run before `astro build` so the inventory page has fresh data.
 * Emails are intentionally never included — inv_emails is internal-only.
 */
import { neon } from "@neondatabase/serverless";
import "dotenv/config";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = resolve(ROOT, "src/data/clt-inventory.json");

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  console.error("DATABASE_URL not set — skipping inventory dump.");
  // Write an empty fallback so astro build can still complete in dev.
  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(
    OUT,
    JSON.stringify({ generated_at: new Date().toISOString(), rows: [] }, null, 2) + "\n",
  );
  process.exit(0);
}

const sql = neon(databaseUrl);

const rows = await sql`
  SELECT id, name, city, state, url, status
  FROM inv_clts
  ORDER BY state NULLS LAST, name
`;

const payload = {
  generated_at: new Date().toISOString(),
  rows: rows.map((r) => ({
    id: r.id,
    name: r.name,
    city: r.city,
    state: r.state,
    url: r.url,
    status: r.status,
  })),
};

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(payload, null, 2) + "\n");
console.log(`Wrote ${payload.rows.length} rows to ${OUT}`);
