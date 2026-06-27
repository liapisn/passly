"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Health = { status: string; service: string };
type CrewInfo = { framework: string; roles: string[]; role_count: number };

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [crew, setCrew] = useState<CrewInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function ping() {
      try {
        const [h, c] = await Promise.all([
          fetch(`${API_URL}/health`).then((r) => r.json()),
          fetch(`${API_URL}/crew/info`).then((r) => r.json()),
        ]);
        setHealth(h);
        setCrew(c);
      } catch (e) {
        setError(e instanceof Error ? e.message : "API unreachable");
      }
    }
    ping();
  }, []);

  const apiUp = health?.status === "ok";

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-8 p-8 bg-neutral-50 text-neutral-900">
      <div className="text-center">
        <h1 className="text-4xl font-semibold tracking-tight">Passly</h1>
        <p className="mt-2 text-neutral-500">
          Wallet passes + AI marketing for Greek SMBs — thesis demo
        </p>
      </div>

      <div className="w-full max-w-md rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-medium uppercase tracking-wide text-neutral-400">
          P0 · stack wiring
        </h2>

        <ul className="mt-4 space-y-3 text-sm">
          <li className="flex items-center justify-between">
            <span>Next.js UI</span>
            <Badge ok>running</Badge>
          </li>
          <li className="flex items-center justify-between">
            <span>FastAPI</span>
            <Badge ok={apiUp}>{apiUp ? "connected" : "down"}</Badge>
          </li>
          <li className="flex items-center justify-between">
            <span>solo-founder-crew</span>
            <Badge ok={!!crew}>
              {crew ? `${crew.role_count} roles` : "—"}
            </Badge>
          </li>
        </ul>

        {crew && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {crew.roles.map((role) => (
              <span
                key={role}
                className="rounded-full bg-neutral-100 px-2.5 py-1 text-xs text-neutral-600"
              >
                {role}
              </span>
            ))}
          </div>
        )}

        {error && (
          <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">
            API unreachable ({error}). Start it with{" "}
            <code className="font-mono">uvicorn app.main:app --reload</code> in{" "}
            <code className="font-mono">api/</code>.
          </p>
        )}
      </div>

      <p className="text-xs text-neutral-400">
        Next · P1 wallet pass issuance → P2 shop designer → P3 crew + WebHITL
      </p>
    </main>
  );
}

function Badge({ ok, children }: { ok?: boolean; children: React.ReactNode }) {
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
        ok ? "bg-green-100 text-green-700" : "bg-neutral-100 text-neutral-400"
      }`}
    >
      {children}
    </span>
  );
}
