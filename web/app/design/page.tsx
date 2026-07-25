"use client";

import { useState } from "react";
import Link from "next/link";
import { PassPreview } from "@/components/PassPreview";
import {
  createShop,
  defaultDesign,
  type PassDesign,
  type PassType,
  type ShopRecord,
} from "@/lib/api";

export default function DesignPage() {
  const [name, setName] = useState("Καφέ Μαρία");
  const [city, setCity] = useState("Σύρος");
  const [design, setDesign] = useState<PassDesign>(defaultDesign);
  const [saved, setSaved] = useState<ShopRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function set<K extends keyof PassDesign>(key: K, value: PassDesign[K]) {
    setDesign((d) => ({ ...d, [key]: value }));
    setSaved(null);
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const record = await createShop({ name, city, design });
      setSaved(record);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-6 py-10">
      <header className="mb-10 flex items-end justify-between border-b border-line pb-6">
        <div>
          <Link
            href="/"
            className="text-xs font-medium uppercase tracking-[0.18em] text-muted hover:text-accent"
          >
            ← Passly
          </Link>
          <h1 className="font-display mt-2 text-3xl font-extrabold tracking-tight">
            Design your shop&rsquo;s pass
          </h1>
          <p className="mt-1 text-sm text-muted">
            Shape the card on the right. The AI crew writes the launch campaign
            next.
          </p>
        </div>
      </header>

      <div className="grid gap-12 lg:grid-cols-[1fr_360px]">
        {/* ── form ───────────────────────────────────────────── */}
        <div className="space-y-8">
          <Section title="Shop">
            <Field label="Shop name">
              <input
                className={inputCls}
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setSaved(null);
                }}
              />
            </Field>
            <Field label="City">
              <input
                className={inputCls}
                value={city}
                onChange={(e) => {
                  setCity(e.target.value);
                  setSaved(null);
                }}
              />
            </Field>
          </Section>

          <Section title="Pass">
            <Field label="Pass type">
              <div className="flex gap-2">
                {(["storeCard", "coupon"] as PassType[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => set("pass_type", t)}
                    className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
                      design.pass_type === t
                        ? "border-accent bg-accent text-white"
                        : "border-line bg-card text-muted hover:border-accent"
                    }`}
                  >
                    {t === "storeCard" ? "Loyalty card" : "Coupon"}
                  </button>
                ))}
              </div>
            </Field>
            <Field label="Logo text">
              <input
                className={inputCls}
                value={design.logo_text}
                maxLength={40}
                onChange={(e) => set("logo_text", e.target.value)}
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Offer label">
                <input
                  className={inputCls}
                  value={design.offer_label}
                  onChange={(e) => set("offer_label", e.target.value)}
                />
              </Field>
              <Field label="Offer value">
                <input
                  className={inputCls}
                  value={design.offer_value}
                  onChange={(e) => set("offer_value", e.target.value)}
                />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Secondary label">
                <input
                  className={inputCls}
                  value={design.secondary_label}
                  onChange={(e) => set("secondary_label", e.target.value)}
                />
              </Field>
              <Field label="Secondary value">
                <input
                  className={inputCls}
                  value={design.secondary_value}
                  onChange={(e) => set("secondary_value", e.target.value)}
                />
              </Field>
            </div>
            <Field label="Barcode message">
              <input
                className={`${inputCls} font-mono text-xs`}
                value={design.barcode_message}
                onChange={(e) => set("barcode_message", e.target.value)}
              />
            </Field>
          </Section>

          <Section title="Colours">
            <div className="grid grid-cols-3 gap-3">
              <ColorField
                label="Background"
                value={design.background_color}
                onChange={(v) => set("background_color", v)}
              />
              <ColorField
                label="Text"
                value={design.foreground_color}
                onChange={(v) => set("foreground_color", v)}
              />
              <ColorField
                label="Label"
                value={design.label_color}
                onChange={(v) => set("label_color", v)}
              />
            </div>
          </Section>
        </div>

        {/* ── live preview ───────────────────────────────────── */}
        <div className="lg:sticky lg:top-10 lg:self-start">
          <div className="flex flex-col items-center gap-6">
            <PassPreview design={design} />

            <button
              onClick={save}
              disabled={saving}
              className="w-[330px] rounded-xl bg-foreground py-3 text-sm font-semibold text-background transition hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save pass"}
            </button>

            <button
              disabled
              title="Real .pkpass signing lands in P1 (needs Apple cert)"
              className="w-[330px] cursor-not-allowed rounded-xl border border-line bg-card py-3 text-sm font-medium text-muted"
            >
               Add to Apple Wallet · P1
            </button>

            {saved && (
              <Link
                href={`/shops/${saved.id}/campaign`}
                className="block w-[330px] rounded-xl bg-accent py-3 text-center text-sm font-semibold text-white transition hover:opacity-90"
              >
                Let the crew draft the campaign →
              </Link>
            )}
            {error && (
              <p className="w-[330px] rounded-lg bg-red-50 px-3 py-2 text-center text-xs text-red-600">
                {error}
              </p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

const inputCls =
  "w-full rounded-lg border border-line bg-card px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h2 className="font-display mb-3 text-xs font-bold uppercase tracking-[0.18em] text-muted">
        {title}
      </h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-muted">{label}</span>
      {children}
    </label>
  );
}

function ColorField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-muted">{label}</span>
      <div className="flex items-center gap-2 rounded-lg border border-line bg-card px-2 py-1.5">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value.toUpperCase())}
          className="h-7 w-7 cursor-pointer rounded border-0 bg-transparent p-0"
        />
        <span className="font-mono text-xs uppercase text-muted">{value}</span>
      </div>
    </label>
  );
}
