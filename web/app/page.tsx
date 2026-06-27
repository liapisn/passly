"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PassPreview } from "@/components/PassPreview";
import { API_URL, defaultDesign } from "@/lib/api";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6">
      <nav className="flex items-center justify-between py-6">
        <span className="font-display text-lg font-extrabold tracking-tight">
          Passly
        </span>
        <StackStatus />
      </nav>

      <div className="grid flex-1 items-center gap-12 py-10 lg:grid-cols-2">
        <div className="rise">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
            Wallet passes · AI marketing
          </p>
          <h1 className="font-display mt-4 text-5xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
            A loyalty card
            <br />
            for your shop,
            <br />
            <span className="text-accent">in minutes.</span>
          </h1>
          <p className="mt-5 max-w-md text-base text-muted">
            Design a branded wallet pass for your Greek shop, then let the AI
            crew draft the launch campaign — you approve every word.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Link
              href="/design"
              className="rounded-xl bg-foreground px-6 py-3 text-sm font-semibold text-background transition hover:opacity-90"
            >
              Create a pass →
            </Link>
            <span className="text-xs text-muted">
              Demo · synthetic data
            </span>
          </div>
        </div>

        <div className="flex justify-center lg:justify-end">
          <div className="rise [animation-delay:120ms] rotate-3 transition-transform hover:rotate-0">
            <PassPreview design={defaultDesign} />
          </div>
        </div>
      </div>
    </main>
  );
}

function StackStatus() {
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then((h) => setOk(h.status === "ok"))
      .catch(() => setOk(false));
  }, []);

  const color =
    ok === null ? "bg-neutral-300" : ok ? "bg-accent" : "bg-red-400";
  const label = ok === null ? "checking" : ok ? "API live" : "API down";

  return (
    <span className="flex items-center gap-2 text-xs text-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${color}`} />
      {label}
    </span>
  );
}
