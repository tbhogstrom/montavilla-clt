import sharp from 'sharp';
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, '../public/og-clt-map.png');

// ── Ternary math ──
const W = 1200, H = 630;
const PAD = 80;

// Triangle vertices (within the 1200x630 canvas)
const Hv = { x: W / 2,        y: PAD + 20 };          // Housing — top center
const Av = { x: PAD + 20,     y: H - PAD - 10 };       // Agriculture — bottom left
const Cv = { x: W - PAD - 20, y: H - PAD - 10 };       // Commercial — bottom right

function toXY(h, a, c) {
  const s = h + a + c || 100;
  return {
    x: (h * Hv.x + a * Av.x + c * Cv.x) / s,
    y: (h * Hv.y + a * Av.y + c * Cv.y) / s,
  };
}

// ── CLT data ──
const CLTS = [
  { h: 94, a: 3,  c: 3  }, { h: 92, a: 3,  c: 5  }, { h: 94, a: 4,  c: 2  },
  { h: 93, a: 3,  c: 4  }, { h: 92, a: 5,  c: 3  }, { h: 93, a: 5,  c: 2  },
  { h: 94, a: 4,  c: 2  }, { h: 94, a: 3,  c: 3  }, { h: 93, a: 4,  c: 3  },
  { h: 91, a: 6,  c: 3  }, { h: 87, a: 3,  c: 10 }, { h: 94, a: 2,  c: 4  },
  { h: 78, a: 5,  c: 17 }, { h: 72, a: 3,  c: 25 }, { h: 70, a: 3,  c: 27 },
  { h: 63, a: 2,  c: 35 }, { h: 55, a: 42, c: 3  }, { h: 45, a: 40, c: 15 },
  { h: 38, a: 47, c: 15 }, { h: 35, a: 58, c: 7  }, { h: 12, a: 85, c: 3  },
  { h: 5,  a: 92, c: 3  }, { h: 42, a: 5,  c: 53 }, { h: 32, a: 5,  c: 63 },
  { h: 55, a: 3,  c: 42 }, { h: 5,  a: 5,  c: 90 }, { h: 52, a: 22, c: 26 },
  { h: 42, a: 25, c: 33 }, { h: 15, a: 82, c: 3  }, { h: 5,  a: 92, c: 3  },
  { h: 25, a: 52, c: 23 },
];

function dotColor(h, a, c) {
  const max = Math.max(h, a, c);
  if (h === max) return '#7A9E7E';
  if (a === max) return '#A88B5A';
  return '#C8872A';
}

// ── Gridlines at 50% ──
function midpoint(p1, p2) {
  return { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
}
const mHA = midpoint(Hv, Av);
const mHC = midpoint(Hv, Cv);
const mAC = midpoint(Av, Cv);

// ── Build SVG ──
const dotsSVG = CLTS.map(({ h, a, c }) => {
  const { x, y } = toXY(h, a, c);
  return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="9" fill="${dotColor(h, a, c)}" opacity="0.8"/>`;
}).join('\n  ');

const mclt = toXY(10, 30, 60);

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <!-- Background -->
  <rect width="${W}" height="${H}" fill="#08140E"/>

  <!-- Subtle gradient -->
  <defs>
    <radialGradient id="bg-glow" cx="75%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#C8872A" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#08140E" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="${W}" height="${H}" fill="url(#bg-glow)"/>

  <!-- 50% gridlines -->
  <line x1="${mHA.x.toFixed(1)}" y1="${mHA.y.toFixed(1)}" x2="${mHC.x.toFixed(1)}" y2="${mHC.y.toFixed(1)}"
    stroke="rgba(122,158,126,0.12)" stroke-width="1" stroke-dasharray="8,6"/>
  <line x1="${mHA.x.toFixed(1)}" y1="${mHA.y.toFixed(1)}" x2="${mAC.x.toFixed(1)}" y2="${mAC.y.toFixed(1)}"
    stroke="rgba(122,158,126,0.12)" stroke-width="1" stroke-dasharray="8,6"/>
  <line x1="${mHC.x.toFixed(1)}" y1="${mHC.y.toFixed(1)}" x2="${mAC.x.toFixed(1)}" y2="${mAC.y.toFixed(1)}"
    stroke="rgba(122,158,126,0.12)" stroke-width="1" stroke-dasharray="8,6"/>

  <!-- Triangle -->
  <polygon points="${Hv.x},${Hv.y} ${Av.x},${Av.y} ${Cv.x},${Cv.y}"
    fill="none" stroke="rgba(122,158,126,0.45)" stroke-width="2"/>

  <!-- CLT dots -->
  ${dotsSVG}

  <!-- MCLT pulse ring -->
  <circle cx="${mclt.x.toFixed(1)}" cy="${mclt.y.toFixed(1)}" r="28"
    fill="none" stroke="#E8A832" stroke-width="2" opacity="0.35"/>
  <circle cx="${mclt.x.toFixed(1)}" cy="${mclt.y.toFixed(1)}" r="20"
    fill="none" stroke="#E8A832" stroke-width="1.5" opacity="0.55"/>

  <!-- MCLT dot -->
  <circle cx="${mclt.x.toFixed(1)}" cy="${mclt.y.toFixed(1)}" r="13"
    fill="#E8A832" stroke="white" stroke-width="2.5"/>

  <!-- Vertex labels -->
  <text x="${Hv.x}" y="${Hv.y - 22}" text-anchor="middle"
    font-family="Arial Black, sans-serif" font-weight="900"
    font-size="28" letter-spacing="4" fill="rgba(245,238,216,0.85)">HOUSING</text>

  <text x="${Av.x}" y="${Av.y + 42}" text-anchor="middle"
    font-family="Arial Black, sans-serif" font-weight="900"
    font-size="26" letter-spacing="3" fill="rgba(245,238,216,0.85)">AGRICULTURE</text>

  <text x="${Cv.x}" y="${Cv.y + 42}" text-anchor="middle"
    font-family="Arial Black, sans-serif" font-weight="900"
    font-size="26" letter-spacing="3" fill="rgba(245,238,216,0.85)">COMMERCIAL</text>

  <!-- MCLT label -->
  <text x="${(mclt.x + 18).toFixed(1)}" y="${(mclt.y + 6).toFixed(1)}"
    font-family="Arial Black, sans-serif" font-weight="900"
    font-size="22" fill="#E8A832" letter-spacing="2">MCLT</text>

  <!-- Housing cluster annotation -->
  <text x="${Hv.x}" y="${(Hv.y + 80).toFixed(1)}" text-anchor="middle"
    font-family="Arial, sans-serif" font-size="17" fill="rgba(122,158,126,0.55)">308+ CLTs cluster here</text>

  <!-- Top-left title -->
  <text x="48" y="54"
    font-family="Arial Black, sans-serif" font-weight="900"
    font-size="22" letter-spacing="2" fill="rgba(245,238,216,0.5)">MONTAVILLA COMMUNITY LAND TRUST</text>
  <text x="48" y="80"
    font-family="Arial, sans-serif" font-size="17"
    fill="rgba(122,158,126,0.5)">montavillalandtrust.org/clt-map</text>
</svg>`;

// ── Render to PNG via sharp ──
sharp(Buffer.from(svg))
  .png()
  .toFile(OUT)
  .then(() => console.log(`✓ OG image written to ${OUT}`))
  .catch(err => { console.error(err); process.exit(1); });
