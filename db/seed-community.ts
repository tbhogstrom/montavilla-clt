// Run with: node --import tsx/esm db/seed-community.ts
import { neon } from '@neondatabase/serverless';
import { v4 as uuidv4 } from 'uuid';
import * as dotenv from 'dotenv';

dotenv.config();

const sql = neon(process.env.DATABASE_URL || process.env.POSTGRES_URL || '');

const seeds = [
  {
    type: 'update',
    title: 'Welcome to the MCLT Community Forum',
    body: `This is your space. Share your story, ask questions, propose ideas, and connect with neighbors who care about Montavilla's future.\n\nThe steering committee will post updates here as the campaign moves forward. In the meantime — introduce yourself, tell us what the market means to you, and let's build this coalition together.`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'Montavilla',
  },
  {
    type: 'discussion',
    title: 'What does the Montavilla Farmers Market mean to you?',
    body: `For a lot of us, the market on SE Stark isn't just a place to buy vegetables — it's a Saturday ritual, a place where you run into neighbors, where kids grow up watching the seasons change through the vendors' tables.\n\nWe'd love to hear your story. How long have you been coming? What would it mean to lose it?`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'Montavilla',
  },
  {
    type: 'discussion',
    title: 'What should live in the community hub?',
    body: `The vision includes a mass timber building with a commissary kitchen and cold storage for vendors. But what else should be in there?\n\nA community meeting room? A tool library? Space for neighborhood organizations? This is your chance to help design it before it's built.`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'SE Portland',
  },
  {
    type: 'discussion',
    title: 'What would a year-round market actually look like?',
    body: `Portland rain is real. The current setup makes November markets a gamble. The plan includes industrial shade structures and landscape design to make the outdoor market work in any weather.\n\nHave you been to year-round markets in other cities that got it right? What made them work?`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'Montavilla',
  },
  {
    type: 'discussion',
    title: 'Have you seen a Community Land Trust work somewhere else?',
    body: `CLTs have preserved community spaces in cities across the country — from urban farms in Detroit to market halls in Oakland. If you've lived somewhere a CLT protected something worth protecting, we'd love to hear about it.\n\nReal examples help us make the case to funders and skeptics alike.`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'SE Portland',
  },
  {
    type: 'discussion',
    title: 'Who else should be part of this coalition?',
    body: `We need organizations, businesses, and institutions to stand with us publicly. Neighborhood associations, schools, churches, local employers — who in Montavilla and greater SE Portland should we be talking to?\n\nDrop names, introductions, or connections below. Warm introductions move faster than cold outreach.`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'Montavilla',
  },
  {
    type: 'discussion',
    title: 'What skills can you bring to the steering committee?',
    body: `We're actively building out the team. Here's where we have gaps right now:\n\n- **Legal**: nonprofit formation, real estate, land trust bylaws\n- **Finance**: nonprofit accounting, CDFI relationships, grant writing\n- **Design**: site planning, architecture, landscape\n- **Organizing**: outreach, coalition building, event logistics\n- **Communications**: media, social, copywriting\n\nIf any of these fit you — or if you have something else to offer — reply here or email info@montavillalandtrust.org.`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'Montavilla',
  },
  {
    type: 'discussion',
    title: "What's the history of this corner?",
    body: `7700 SE Stark has been a gathering place for almost two decades, but the neighborhood's history runs much deeper. Long-time Montavilla residents — what do you remember about this block and this street before the market?\n\nWe want to tell a full story, not just the last 19 years.`,
    display_name: 'MCLT Steering Committee',
    neighborhood: 'Montavilla',
  },
];

async function seed() {
  await sql`
    CREATE TABLE IF NOT EXISTS posts (
      id           TEXT PRIMARY KEY,
      type         TEXT NOT NULL DEFAULT 'discussion',
      title        TEXT NOT NULL,
      body         TEXT,
      image_url    TEXT,
      display_name TEXT NOT NULL,
      neighborhood TEXT,
      created_at   TIMESTAMPTZ DEFAULT NOW(),
      is_deleted   BOOLEAN DEFAULT FALSE
    )
  `;

  // Check if seeds already exist
  const existing = await sql`SELECT COUNT(*) AS count FROM posts`;
  if (Number(existing[0].count) > 0) {
    console.log(`Skipping seed — ${existing[0].count} post(s) already exist.`);
    process.exit(0);
  }

  for (let i = 0; i < seeds.length; i++) {
    const s = seeds[i];
    const id = uuidv4();
    // Stagger created_at so they sort in the right order (oldest first = index 0 at bottom)
    const createdAt = new Date(Date.now() - (seeds.length - i) * 60_000).toISOString();
    await sql`
      INSERT INTO posts (id, type, title, body, display_name, neighborhood, created_at)
      VALUES (${id}, ${s.type}, ${s.title}, ${s.body}, ${s.display_name}, ${s.neighborhood}, ${createdAt})
    `;
    console.log(`✓ ${s.type.padEnd(10)} "${s.title}"`);
  }

  console.log(`\nSeeded ${seeds.length} posts.`);
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(1); });
