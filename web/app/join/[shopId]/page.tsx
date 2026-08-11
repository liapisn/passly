"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PassPreview } from "@/components/PassPreview";
import {
  demoLogoSrc,
  enrollMember,
  getShop,
  memberPassUrl,
  type MemberRecord,
  type ShopRecord,
} from "@/lib/api";

export default function JoinPage() {
  const { shopId } = useParams<{ shopId: string }>();
  const [shop, setShop] = useState<ShopRecord | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [member, setMember] = useState<MemberRecord | null>(null);
  const [existed, setExisted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getShop(shopId)
      .then(setShop)
      .catch(() => setError("Το κατάστημα δεν βρέθηκε."));
  }, [shopId]);

  async function join() {
    setBusy(true);
    setError(null);
    try {
      const { member: m, existed: e } = await enrollMember(
        shopId,
        name.trim(),
        email.trim(),
      );
      setMember(m);
      setExisted(e);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Κάτι πήγε στραβά");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center gap-8 px-6 py-12">
      {error && !shop && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
      )}

      {shop && (
        <>
          <div className="rise flex flex-col items-center gap-6">
            <PassPreview design={shop.design} logoSrc={demoLogoSrc} />
          </div>

          {!member ? (
            <div className="rise w-full text-center [animation-delay:100ms]">
              <h1 className="font-display text-3xl font-extrabold tracking-tight">
                {shop.name}
              </h1>
              <p className="mt-1 text-sm text-muted">{shop.design.offer_value}</p>
              <p className="mt-2 text-xs text-muted">
                Νέος; γίνε μέλος. Ήδη μέλος; βάλε το email σου και πάρε ξανά την
                κάρτα σου.
              </p>

              <div className="mt-6 space-y-3">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Το όνομά σου"
                  className="w-full rounded-xl border border-line bg-card px-4 py-3 text-center text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
                />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Το email σου"
                  className="w-full rounded-xl border border-line bg-card px-4 py-3 text-center text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
                />
                <button
                  onClick={join}
                  disabled={busy || !name.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)}
                  className="w-full rounded-xl bg-accent py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
                >
                  {busy ? "Εγγραφή…" : "Γίνε μέλος"}
                </button>
                {error && <p className="text-xs text-red-600">{error}</p>}
              </div>
            </div>
          ) : (
            <div className="rise w-full text-center">
              <h1 className="font-display text-2xl font-extrabold tracking-tight">
                {existed ? "Καλώς ήρθες πίσω" : "Καλώς ήρθες"},{" "}
                {member.name || "φίλε"}! 🍪
              </h1>
              <p className="mt-1 text-sm text-muted">
                {existed
                  ? "Ορίστε ξανά η κάρτα σου — με τις τρέχουσες σφραγίδες."
                  : "Η κάρτα σου είναι έτοιμη — μάζεψε σφραγίδες σε κάθε επίσκεψη."}
              </p>
              <a
                href={memberPassUrl(member.id)}
                className="mt-6 block w-full rounded-xl bg-foreground py-3.5 text-sm font-semibold text-background transition hover:opacity-90"
              >
                 Πρόσθεσε στο Apple Wallet
              </a>
              <p className="mt-3 font-mono text-[11px] text-muted">
                {member.serial_number} · Σφραγίδες: {member.stamps}
              </p>
            </div>
          )}
        </>
      )}
    </main>
  );
}
