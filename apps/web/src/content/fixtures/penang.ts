import { seeded } from "@/components/figures/chart-utils";

import type { PenangResults, ServiceCategory, ServicePoint } from "../types";

// Illustrative only. Never shown in a production build (see lib/study-results.ts).
const CATEGORIES: readonly ServiceCategory[] = ["clinic", "school", "transit"];
const CLUSTERS: ReadonlyArray<readonly [number, number, number, number]> = [
  [300, 175, 18, 14], [180, 125, 24, 5], [298, 335, 14, 8], [215, 405, 18, 4], [120, 300, 16, 4],
  [425, 165, 24, 10], [540, 110, 30, 4], [500, 260, 34, 9], [470, 420, 40, 6],
];

function points(): readonly ServicePoint[] {
  const rand = seeded(7);
  return CLUSTERS.flatMap(([cx, cy, spread, n]) =>
    Array.from({ length: n }, () => {
      const category = CATEGORIES[Math.floor(rand() * 3)];
      return { category, x: +(cx + (rand() - 0.5) * spread * 2).toFixed(1), y: +(cy + (rand() - 0.5) * spread * 2).toFixed(1) };
    }),
  );
}

export const penangFixture: PenangResults = {
  answer:
    "Most residents of Timur Laut live within a kilometre of a public clinic. In Seberang Perai Selatan, about 1 in 5 live more than 3 km away, and the gap is widest for clinics rather than schools.",
  keyNumbers: [
    { value: "21%", label: "of Seberang Perai Selatan residents live over 3 km from a public clinic.", caveat: "95% interval 18 to 24%, from a mukim bootstrap." },
    { value: "412", label: "public service points mapped across clinics, schools and transit stops.", caveat: "Public facilities only. Private clinics are not included." },
    { value: "5", label: "districts compared on the same distance bands.", caveat: "District averages hide variation inside each mukim." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { PeGIS: "2026-09-28", "Census 2020": "2026-09-28", OpenStreetMap: "2026-09-29" },
  districts: [
    { id: "tl", name: "Timur Laut", short: "Timur Laut", bands: [72, 24, 4], population: 545000 },
    { id: "bd", name: "Barat Daya", short: "Barat Daya", bands: [48, 34, 18], population: 236000 },
    { id: "spu", name: "Seberang Perai Utara", short: "SP Utara", bands: [55, 33, 12], population: 330000 },
    { id: "spt", name: "Seberang Perai Tengah", short: "SP Tengah", bands: [61, 30, 9], population: 402000 },
    { id: "sps", name: "Seberang Perai Selatan", short: "SP Selatan", bands: [41, 38, 21], population: 205000 },
  ],
  points: points(),
  pointsNote: "Schematic, not to scale. Points are an illustrative sample of the 412 public service points mapped. Dashed lines mark district boundaries.",
  geometry: {
    island:
      "M95 120 C130 95 175 100 205 105 C235 110 255 100 280 115 C300 125 318 140 322 160 C326 185 312 205 318 230 C324 260 315 290 322 320 C330 345 318 370 300 395 C285 415 262 432 240 438 C210 445 180 430 160 420 C130 405 110 385 100 360 C85 330 78 300 80 270 C82 240 70 210 75 180 C78 155 82 135 95 120 Z",
    mainland:
      "M380 0 L600 0 L600 500 L395 500 C400 470 385 440 392 410 C398 380 385 350 390 320 C395 290 378 260 385 230 C390 200 375 170 382 140 C388 110 372 80 378 50 C380 30 378 15 380 0 Z",
    districts: [
      { id: "tl", d: "M0 0H345V301L0 215Z", land: "island" },
      { id: "bd", d: "M0 215L345 301V500H0Z", land: "island" },
      { id: "spu", d: "M370 0H600V190H370Z", land: "mainland" },
      { id: "spt", d: "M370 190H600V340H370Z", land: "mainland" },
      { id: "sps", d: "M370 340H600V500H370Z", land: "mainland" },
    ],
    boundaries: ["M0 215L345 301", "M370 190H600", "M370 340H600"],
    bridges: ["M322 300L390 290", "M303 398L393 430"],
    places: [
      { text: "George Town", x: 240, y: 92 }, { text: "Bayan Lepas", x: 200, y: 462 }, { text: "Balik Pulau", x: 150, y: 350 },
      { text: "Butterworth", x: 490, y: 52 }, { text: "Bukit Mertajam", x: 495, y: 320 }, { text: "Nibong Tebal", x: 495, y: 480 },
    ],
    water: { text: "Selat Melaka", x: 22, y: 52 },
  },
};
