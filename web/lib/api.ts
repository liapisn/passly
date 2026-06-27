// Typed client for the Passly FastAPI service. Mirrors api/app/models.py.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PassType = "storeCard" | "coupon";

export type PassDesign = {
  pass_type: PassType;
  logo_text: string;
  offer_label: string;
  offer_value: string;
  secondary_label: string;
  secondary_value: string;
  background_color: string;
  foreground_color: string;
  label_color: string;
  barcode_message: string;
};

export type Shop = {
  name: string;
  city: string;
  design: PassDesign;
};

export type ShopRecord = Shop & { id: string };

export async function createShop(shop: Shop): Promise<ShopRecord> {
  const res = await fetch(`${API_URL}/shops`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(shop),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Save failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export const defaultDesign: PassDesign = {
  pass_type: "storeCard",
  logo_text: "ΚΑΦΕ ΜΑΡΙΑ",
  offer_label: "Loyalty",
  offer_value: "Buy 9, get the 10th free",
  secondary_label: "Member",
  secondary_value: "—",
  background_color: "#0B5D3B",
  foreground_color: "#FFFFFF",
  label_color: "#BFE8D4",
  barcode_message: "passly:demo:karfe-maria",
};
