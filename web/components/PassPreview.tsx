import type { PassDesign } from "@/lib/api";

// A faithful Apple-Wallet-style card that re-renders live as the design
// changes. The hero of the designer — it is what the founder is really
// shaping, and what P1 will sign into a real .pkpass.
export function PassPreview({ design }: { design: PassDesign }) {
  const {
    logo_text,
    offer_label,
    offer_value,
    secondary_label,
    secondary_value,
    background_color,
    foreground_color,
    label_color,
    pass_type,
  } = design;

  return (
    <div
      className="w-[330px] rounded-[20px] p-5 shadow-2xl ring-1 ring-black/10 transition-colors duration-300"
      style={{
        background: `linear-gradient(160deg, ${background_color}, ${shade(
          background_color,
          -18
        )})`,
        color: foreground_color,
      }}
    >
      {/* header: logo text + pass kind */}
      <div className="flex items-center justify-between">
        <span className="font-display text-sm font-bold uppercase tracking-[0.14em]">
          {logo_text || "YOUR SHOP"}
        </span>
        <span
          className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
          style={{ background: hexA(foreground_color, 0.16), color: foreground_color }}
        >
          {pass_type === "coupon" ? "Coupon" : "Loyalty"}
        </span>
      </div>

      {/* primary field — the offer */}
      <div className="mt-8">
        <div
          className="text-[10px] font-semibold uppercase tracking-[0.18em]"
          style={{ color: label_color }}
        >
          {offer_label || "Offer"}
        </div>
        <div className="mt-1 font-display text-2xl font-extrabold leading-tight">
          {offer_value || "Your offer here"}
        </div>
      </div>

      {/* secondary field */}
      {(secondary_label || secondary_value) && (
        <div className="mt-6">
          <div
            className="text-[10px] font-semibold uppercase tracking-[0.18em]"
            style={{ color: label_color }}
          >
            {secondary_label || " "}
          </div>
          <div className="mt-0.5 text-sm font-medium">
            {secondary_value || " "}
          </div>
        </div>
      )}

      {/* barcode strip */}
      <div className="mt-7 rounded-lg bg-white p-2.5">
        <div className="flex h-12 items-end justify-center gap-[2px] overflow-hidden">
          {BAR_PATTERN.map((h, i) => (
            <span
              key={i}
              className="w-[2px] bg-neutral-900"
              style={{ height: `${h}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// A fixed, pleasant-looking bar pattern (deterministic — no Math.random so it
// stays stable across renders).
const BAR_PATTERN = [
  90, 40, 70, 100, 55, 80, 35, 95, 60, 45, 85, 50, 100, 30, 75, 65, 90, 40, 80,
  55, 70, 100, 45, 60, 95, 35, 85, 50, 75, 40, 90, 65,
];

// Darken/lighten a hex colour by a percentage for the card gradient.
function shade(hex: string, percent: number): string {
  const { r, g, b } = toRgb(hex);
  const adj = (c: number) =>
    Math.max(0, Math.min(255, Math.round(c + (percent / 100) * 255)));
  return `rgb(${adj(r)}, ${adj(g)}, ${adj(b)})`;
}

function hexA(hex: string, alpha: number): string {
  const { r, g, b } = toRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function toRgb(hex: string): { r: number; g: number; b: number } {
  let h = hex.replace("#", "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  const n = parseInt(h || "000000", 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}
