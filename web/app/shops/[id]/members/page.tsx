"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  addStamp,
  getShop,
  listMembers,
  type MemberRecord,
  type ShopRecord,
} from "@/lib/api";

export default function MembersPage() {
  const { id } = useParams<{ id: string }>();
  const [shop, setShop] = useState<ShopRecord | null>(null);
  const [members, setMembers] = useState<MemberRecord[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getShop(id), listMembers(id)])
      .then(([s, m]) => {
        setShop(s);
        setMembers(m);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [id]);

  const goal = shop?.design.stamps_goal ?? 10;

  async function stamp(memberId: string) {
    setBusy(memberId);
    setError(null);
    try {
      const updated = await addStamp(memberId);
      setMembers((list) => list.map((m) => (m.id === updated.id ? updated : m)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stamp failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="mx-auto w-full max-w-2xl px-6 py-10">
      <header className="mb-8 border-b border-line pb-6">
        <Link
          href="/design"
          className="text-xs font-medium uppercase tracking-[0.18em] text-muted hover:text-accent"
        >
          ← Designer
        </Link>
        <h1 className="font-display mt-2 text-3xl font-extrabold tracking-tight">
          Members &amp; stamps
        </h1>
        <p className="mt-1 text-sm text-muted">
          {shop ? (
            <>
              {shop.name} · reward every <b>{goal}</b> stamps
            </>
          ) : (
            "Loading…"
          )}
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {shop && members.length === 0 && (
        <p className="rounded-xl border border-line bg-card px-4 py-8 text-center text-sm text-muted">
          Κανένα μέλος ακόμα. Μοιράσου το{" "}
          <Link href={`/join/${id}`} className="font-medium text-accent hover:underline">
            join link
          </Link>
          .
        </p>
      )}

      <ul className="space-y-3">
        {members.map((m) => (
          <li
            key={m.id}
            className="flex items-center justify-between rounded-xl border border-line bg-card px-4 py-3"
          >
            <div className="min-w-0">
              <div className="truncate font-medium">{m.name || "—"}</div>
              <div className="truncate text-xs text-muted">{m.email}</div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="font-display text-lg font-bold tabular-nums">
                  {m.stamps}
                  <span className="text-sm font-medium text-muted">/{goal}</span>
                </div>
                {m.rewards > 0 && (
                  <div className="text-[11px] text-spark">🎁 {m.rewards} reward{m.rewards > 1 ? "s" : ""}</div>
                )}
              </div>
              <button
                onClick={() => stamp(m.id)}
                disabled={busy === m.id}
                className="rounded-lg bg-accent px-3 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
              >
                +1 σφραγίδα
              </button>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
