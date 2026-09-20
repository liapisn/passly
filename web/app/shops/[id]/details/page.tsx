"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getShop, updateShopDetails, type ShopDetails, type ShopRecord } from "@/lib/api";

const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const GR_PHONE = /^\+30\s?6\d{2}\s?\d{3}\s?\d{4}$/;
const INSTAGRAM_HANDLE = /^[A-Za-z0-9_.]{1,30}$/;

type Errors = Partial<Record<keyof ShopDetails, string>>;

function detailsOf(shop: ShopRecord): ShopDetails {
  return {
    name: shop.name,
    address: shop.address,
    email: shop.email,
    phone: shop.phone,
    instagram_handle: shop.instagram_handle,
    facebook_page_url: shop.facebook_page_url,
    google_maps_url: shop.google_maps_url,
  };
}

function validate(d: ShopDetails): Errors {
  const errors: Errors = {};
  if (d.name.trim().length < 1 || d.name.length > 100) {
    errors.name = "Όνομα καταστήματος απαραίτητο";
  }
  if (d.address.trim().length < 5 || d.address.length > 200) {
    errors.address = "Διεύθυνση υποχρεωτική (τουλάχιστον 5 χαρακτήρες)";
  }
  if (!EMAIL.test(d.email)) {
    errors.email = "Έγκυρη διεύθυνση email";
  }
  if (d.phone && !GR_PHONE.test(d.phone)) {
    errors.phone = "Έγκυρο ελληνικό νούμερο (π.χ. +30 6XX XXXXXXX)";
  }
  if (d.instagram_handle && !INSTAGRAM_HANDLE.test(d.instagram_handle)) {
    errors.instagram_handle = "Μόνο γράμματα, αριθμοί, underscore (χωρίς @)";
  }
  if (d.facebook_page_url && !d.facebook_page_url.startsWith("https://facebook.com/")) {
    errors.facebook_page_url = "Έγκυρη διεύθυνση Facebook (facebook.com/...)";
  }
  if (
    d.google_maps_url &&
    !d.google_maps_url.includes("google.com/maps") &&
    !d.google_maps_url.includes("goo.gl/maps")
  ) {
    errors.google_maps_url = "Έγκυρη διεύθυνση Google Maps";
  }
  return errors;
}

export default function ShopDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const [shop, setShop] = useState<ShopRecord | null>(null);
  const [form, setForm] = useState<ShopDetails | null>(null);
  const [touched, setTouched] = useState<Partial<Record<keyof ShopDetails, boolean>>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getShop(id)
      .then((s) => {
        setShop(s);
        setForm(detailsOf(s));
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [id]);

  if (!shop || !form) {
    return (
      <main className="mx-auto w-full max-w-2xl px-6 py-10">
        <p className="text-sm text-muted">{error ?? "Loading…"}</p>
      </main>
    );
  }

  const errors = validate(form);
  const valid = Object.keys(errors).length === 0;
  const dirty = JSON.stringify(form) !== JSON.stringify(detailsOf(shop));

  function set<K extends keyof ShopDetails>(key: K, value: ShopDetails[K]) {
    setForm((f) => (f ? { ...f, [key]: value } : f));
    setSaved(false);
  }

  function touch(key: keyof ShopDetails) {
    setTouched((t) => ({ ...t, [key]: true }));
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const updated = await updateShopDetails(id, form!);
      setShop(updated);
      setForm(detailsOf(updated));
      setTouched({});
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
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
          Στοιχεία καταστήματος
        </h1>
        <p className="mt-1 text-sm text-muted">
          Στοιχεία επικοινωνίας και σύνδεσμοι — ξεχωριστά από το design του pass.
        </p>
      </header>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      )}
      {saved && (
        <div className="mb-4 rounded-lg bg-accent-soft px-4 py-3 text-sm text-accent">
          Αποθηκεύτηκε ✓
        </div>
      )}

      <div className="space-y-4">
        <Field label="Όνομα καταστήματος" error={touched.name ? errors.name : undefined}>
          <input
            className={inputCls}
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            onBlur={() => touch("name")}
          />
        </Field>
        <Field label="Διεύθυνση" error={touched.address ? errors.address : undefined}>
          <input
            className={inputCls}
            value={form.address}
            onChange={(e) => set("address", e.target.value)}
            onBlur={() => touch("address")}
          />
        </Field>
        <Field label="Email" error={touched.email ? errors.email : undefined}>
          <input
            className={inputCls}
            type="email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            onBlur={() => touch("email")}
          />
        </Field>
        <Field label="Τηλέφωνο (προαιρετικό)" error={touched.phone ? errors.phone : undefined}>
          <input
            className={inputCls}
            placeholder="+30 6XX XXXXXXX"
            value={form.phone}
            onChange={(e) => set("phone", e.target.value)}
            onBlur={() => touch("phone")}
          />
        </Field>
        <Field
          label="Instagram (προαιρετικό)"
          error={touched.instagram_handle ? errors.instagram_handle : undefined}
        >
          <input
            className={inputCls}
            placeholder="to_palio_cafe"
            value={form.instagram_handle}
            onChange={(e) => set("instagram_handle", e.target.value)}
            onBlur={() => touch("instagram_handle")}
          />
        </Field>
        <Field
          label="Σελίδα Facebook (προαιρετικό)"
          error={touched.facebook_page_url ? errors.facebook_page_url : undefined}
        >
          <input
            className={inputCls}
            placeholder="https://facebook.com/..."
            value={form.facebook_page_url}
            onChange={(e) => set("facebook_page_url", e.target.value)}
            onBlur={() => touch("facebook_page_url")}
          />
        </Field>
        <Field
          label="Google Maps (προαιρετικό)"
          error={touched.google_maps_url ? errors.google_maps_url : undefined}
        >
          <input
            className={inputCls}
            placeholder="https://goo.gl/maps/..."
            value={form.google_maps_url}
            onChange={(e) => set("google_maps_url", e.target.value)}
            onBlur={() => touch("google_maps_url")}
          />
        </Field>
      </div>

      <button
        onClick={save}
        disabled={!dirty || !valid || saving}
        className="mt-8 w-full rounded-xl bg-accent py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50 sm:w-auto sm:px-8"
      >
        {saving ? "Αποθήκευση…" : "Αποθήκευση"}
      </button>
    </main>
  );
}

const inputCls =
  "w-full rounded-lg border border-line bg-card px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent-soft";

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-muted">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}
