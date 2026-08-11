// Typed client for the Passly FastAPI service. Mirrors api/app/models.py.

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type PassType = "loyalty" | "coupon";

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

export async function getShop(shopId: string): Promise<ShopRecord> {
  const res = await fetch(`${API_URL}/shops/${shopId}`);
  if (!res.ok) throw new Error(`Shop not found (${res.status})`);
  return res.json();
}

// ── members (customer passes) ──

export type MemberRecord = {
  id: string;
  shop_id: string;
  name: string;
  email: string;
  serial_number: string;
  stamps: number;
  created_at: string;
};

export async function enrollMember(
  shopId: string,
  name: string,
  email: string,
): Promise<MemberRecord> {
  const res = await fetch(`${API_URL}/shops/${shopId}/members`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email }),
  });
  if (!res.ok) throw new Error(`Enrollment failed (${res.status})`);
  return res.json();
}

export function memberPassUrl(memberId: string): string {
  return `${API_URL}/members/${memberId}/pkpass`;
}

// ── campaigns ──

export type CampaignStatus =
  | "drafting"
  | "awaiting_review"
  | "shipped"
  | "killed"
  | "exhausted"
  | "error";

export type ReviewGate = {
  turn: number;
  artifact: string;
  options: string[];
};

export type CampaignState = {
  thread_id: string;
  status: CampaignStatus;
  gate: ReviewGate | null;
  final_artifact: string | null;
  error: string | null;
};

export async function startCampaign(shopId: string): Promise<CampaignState> {
  const res = await fetch(`${API_URL}/shops/${shopId}/campaign`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Could not start campaign (${res.status})`);
  return res.json();
}

export async function getCampaign(threadId: string): Promise<CampaignState> {
  const res = await fetch(`${API_URL}/campaigns/${threadId}`);
  if (!res.ok) throw new Error(`Campaign not found (${res.status})`);
  return res.json();
}

export async function respondCampaign(
  threadId: string,
  action: "approve" | "reject" | "kill",
  feedback?: string,
): Promise<CampaignState> {
  const res = await fetch(`${API_URL}/campaigns/${threadId}/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, feedback: feedback ?? null }),
  });
  if (!res.ok) throw new Error(`Response failed (${res.status})`);
  return res.json();
}

export const defaultDesign: PassDesign = {
  pass_type: "loyalty",
  logo_text: "CHUNKY COOKIE BAR",
  offer_label: "Loyalty",
  offer_value: "Στα 9 cookies, το 10ο κέρασμα",
  secondary_label: "Member",
  secondary_value: "—",
  background_color: "#3B2417",
  foreground_color: "#F5E6C8",
  label_color: "#C9A86A",
  barcode_message: "passly:member:CHUNKY-0001",
};

// The demo shop's real logo (used with their permission), served from /public.
export const demoLogoSrc = "/chunky-logo.svg";
