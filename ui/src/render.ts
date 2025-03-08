// SVG pitch and shot-map rendering. Pure functions that return SVG strings so they
// can be unit-tested without a browser DOM.

import { Point, toSvg } from "./pitch";

export interface ShotMarker {
  location: Point;
  xg: number;
  isGoal: boolean;
  label: string;
  limitedSupport: boolean;
}

export function pitchSvg(width: number, height: number): string {
  const line = `stroke="#cbd5e1" stroke-width="2" fill="none"`;
  const midX = width / 2;
  // halfway line, centre circle, and both penalty boxes (approximate proportions)
  const boxW = width * 0.16;
  const boxH = height * 0.6;
  const boxY = (height - boxH) / 2;
  return [
    `<rect x="0" y="0" width="${width}" height="${height}" fill="#0b3d2e" rx="6"/>`,
    `<line x1="${midX}" y1="0" x2="${midX}" y2="${height}" ${line}/>`,
    `<circle cx="${midX}" cy="${height / 2}" r="${height * 0.12}" ${line}/>`,
    `<rect x="${width - boxW}" y="${boxY}" width="${boxW}" height="${boxH}" ${line}/>`,
    `<rect x="0" y="${boxY}" width="${boxW}" height="${boxH}" ${line}/>`,
  ].join("");
}

export function shotMarkersSvg(
  shots: ShotMarker[],
  width: number,
  height: number
): string {
  return shots
    .map((s) => {
      const p = toSvg(s.location, width, height);
      const r = 4 + s.xg * 14; // marker size scales with xG
      const fill = s.isGoal ? "#f59e0b" : "#38bdf8";
      const stroke = s.limitedSupport ? "#ef4444" : "#0f172a";
      return (
        `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" ` +
        `r="${r.toFixed(1)}" fill="${fill}" fill-opacity="0.75" ` +
        `stroke="${stroke}" stroke-width="2">` +
        `<title>${escapeXml(s.label)} (xG ${s.xg.toFixed(3)}` +
        `${s.limitedSupport ? ", limited support" : ""})</title></circle>`
      );
    })
    .join("");
}

export function escapeXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export interface CoverageBadge {
  competition: string;
  season: string;
  level: "results" | "events" | "tracking";
  matches: number;
}

export function coverageBadgeText(b: CoverageBadge): string {
  const depth = { results: "results only", events: "event data", tracking: "tracking" }[
    b.level
  ];
  return `${b.competition} ${b.season}: ${b.matches} matches, ${depth}`;
}
