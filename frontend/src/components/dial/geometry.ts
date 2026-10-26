/**
 * Dial geometry shared by every chronograph-style control. Angles are
 * measured the way a watch reads them: 0 at twelve o'clock, increasing
 * clockwise, expressed as a 0..1 fraction of a full turn.
 */

export interface Point {
  x: number;
  y: number;
}

/** Point on a circle of radius `r` around (cx, cy) at turn fraction `t` (0 = 12 o'clock). */
export function polar(cx: number, cy: number, r: number, t: number): Point {
  const angle = t * Math.PI * 2 - Math.PI / 2;
  return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
}

/** Turn fraction (0..1, clockwise from 12 o'clock) of `point` relative to `center`. */
export function turnFromPoint(center: Point, point: Point): number {
  const angle = Math.atan2(point.y - center.y, point.x - center.x) + Math.PI / 2;
  const turn = angle / (Math.PI * 2);
  return turn < 0 ? turn + 1 : turn;
}

/** SVG arc path from turn `from` to turn `to` (clockwise) on radius `r`. */
export function arcPath(cx: number, cy: number, r: number, from: number, to: number): string {
  const span = Math.max(0, Math.min(0.9999, to - from));
  const start = polar(cx, cy, r, from);
  const end = polar(cx, cy, r, from + span);
  const largeArc = span > 0.5 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

export function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

/** Roman numerals for chapter indices on the dial (I, II, III...). */
export function toRoman(value: number): string {
  const table: Array<[number, string]> = [
    [10, "X"],
    [9, "IX"],
    [5, "V"],
    [4, "IV"],
    [1, "I"],
  ];
  let remaining = Math.max(1, Math.floor(value));
  let out = "";
  if (remaining > 39) return String(remaining);
  for (const [n, numeral] of table) {
    while (remaining >= n) {
      out += numeral;
      remaining -= n;
    }
  }
  return out;
}
