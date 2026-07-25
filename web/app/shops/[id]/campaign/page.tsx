"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  type CampaignState,
  getCampaign,
  getShop,
  respondCampaign,
  startCampaign,
} from "@/lib/api";

const ROLES = ["marketing", "product", "engineering"];
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function CampaignPage() {
  const { id } = useParams<{ id: string }>();
  const [shopName, setShopName] = useState<string>("");
  const [campaign, setCampaign] = useState<CampaignState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const alive = useRef(true);

  // Poll while the crew is drafting; stop at a gate or a terminal state.
  const pollUntilSettled = useCallback(async (threadId: string) => {
    for (let i = 0; i < 120; i++) {
      if (!alive.current) return;
      const state = await getCampaign(threadId);
      setCampaign(state);
      if (state.status !== "drafting") return;
      await sleep(1000);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    (async () => {
      try {
        const shop = await getShop(id);
        setShopName(shop.name);
        const started = await startCampaign(id);
        setCampaign(started);
        if (started.status === "drafting") await pollUntilSettled(started.thread_id);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Something went wrong");
      }
    })();
    return () => {
      alive.current = false;
    };
  }, [id, pollUntilSettled]);

  async function respond(action: "approve" | "reject" | "kill") {
    if (!campaign) return;
    setBusy(true);
    setError(null);
    try {
      const next = await respondCampaign(
        campaign.thread_id,
        action,
        action === "reject" ? feedback : undefined,
      );
      setCampaign(next);
      setFeedbackOpen(false);
      setFeedback("");
      if (next.status === "drafting") await pollUntilSettled(next.thread_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Response failed");
    } finally {
      setBusy(false);
    }
  }

  const status = campaign?.status;

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
          Launch campaign
        </h1>
        <p className="mt-1 text-sm text-muted">
          {shopName ? (
            <>
              The AI crew drafts the announcement for{" "}
              <span className="font-medium text-foreground">{shopName}</span> —
              you have the final say.
            </>
          ) : (
            "Loading…"
          )}
        </p>
      </header>

      {error && (
        <div className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {(status === "drafting" || (!campaign && !error)) && <Drafting />}

      {status === "awaiting_review" && campaign?.gate && (
        <div className="rise space-y-5">
          <div className="flex items-center gap-2 text-xs text-muted">
            <Dot className="bg-spark" />
            Awaiting your review · draft {campaign.gate.turn}
          </div>
          <DraftCard text={campaign.gate.artifact} />

          {!feedbackOpen ? (
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => respond("approve")}
                disabled={busy}
                className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
              >
                Approve &amp; publish
              </button>
              <button
                onClick={() => setFeedbackOpen(true)}
                disabled={busy}
                className="rounded-xl border border-line bg-card px-5 py-2.5 text-sm font-medium transition hover:border-accent disabled:opacity-50"
              >
                Send back with notes
              </button>
              <button
                onClick={() => respond("kill")}
                disabled={busy}
                className="rounded-xl px-5 py-2.5 text-sm font-medium text-red-500 transition hover:bg-red-50 disabled:opacity-50"
              >
                Discard
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="e.g. Ζέστανε το άνοιγμα, πρόσθεσε ένα ελληνικό tagline…"
                rows={3}
                className="w-full rounded-lg border border-line bg-card px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft"
              />
              <div className="flex gap-3">
                <button
                  onClick={() => respond("reject")}
                  disabled={busy || !feedback.trim()}
                  className="rounded-xl bg-foreground px-5 py-2.5 text-sm font-semibold text-background transition hover:opacity-90 disabled:opacity-50"
                >
                  Send back to the crew
                </button>
                <button
                  onClick={() => setFeedbackOpen(false)}
                  disabled={busy}
                  className="rounded-xl px-5 py-2.5 text-sm font-medium text-muted hover:text-foreground"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {status === "shipped" && (
        <div className="rise space-y-5">
          <div className="flex items-center gap-2 rounded-lg bg-accent-soft px-4 py-3 text-sm font-medium text-accent">
            <Dot className="bg-accent" /> Published — the campaign is live.
          </div>
          <DraftCard text={campaign?.final_artifact ?? ""} />
          <Link
            href="/design"
            className="inline-block rounded-xl border border-line bg-card px-5 py-2.5 text-sm font-medium transition hover:border-accent"
          >
            ← Back to the designer
          </Link>
        </div>
      )}

      {(status === "killed" || status === "exhausted") && (
        <div className="rise rounded-lg border border-line bg-card px-4 py-6 text-center text-sm text-muted">
          {status === "killed"
            ? "Campaign discarded. Nothing was published."
            : "Revision budget spent — no version was approved."}
          <div className="mt-4">
            <Link href="/design" className="font-medium text-accent hover:underline">
              Back to the designer
            </Link>
          </div>
        </div>
      )}
    </main>
  );
}

function Drafting() {
  return (
    <div className="rounded-xl border border-line bg-card px-6 py-10 text-center">
      <div className="mb-4 flex justify-center gap-1.5">
        {ROLES.map((r, i) => (
          <span
            key={r}
            className="h-2 w-2 animate-pulse rounded-full bg-accent"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
      <p className="text-sm text-muted">The marketing crew is drafting…</p>
    </div>
  );
}

function DraftCard({ text }: { text: string }) {
  return (
    <article className="whitespace-pre-wrap rounded-xl border border-line bg-card p-6 text-[15px] leading-relaxed">
      {text}
    </article>
  );
}

function Dot({ className }: { className: string }) {
  return <span className={`h-1.5 w-1.5 rounded-full ${className}`} />;
}
