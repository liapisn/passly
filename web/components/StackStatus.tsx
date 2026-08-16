"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

// Liveness dot in the landing nav. Client-side on purpose: the check runs in
// the visitor's browser, so it reports the API the visitor can actually reach
// (the tunnel hostname during a demo), not the one the server saw at build.
export function StackStatus() {
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
