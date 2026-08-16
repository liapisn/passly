import type { Metadata } from "next";
import Link from "next/link";
import { PassPreview } from "@/components/PassPreview";
import { HowItWorks } from "@/components/HowItWorks";
import { Faq } from "@/components/Faq";
import { API_URL, defaultDesign, demoLogoSrc } from "@/lib/api";
import { StackStatus } from "@/components/StackStatus";
import { defaultDesign, demoLogoSrc } from "@/lib/api";
import { SITE_URL } from "@/lib/seo";

// The landing page is Greek-first — the reader is a shop owner in Greece —
// with an English gloss under each block for the (English) thesis. Only the
// liveness dot needs the browser, so the page itself stays a server component
// and ships its copy, metadata and JSON-LD in the initial HTML.
export const metadata: Metadata = {
  title: "Κάρτα πιστότητας στο κινητό, χωρίς εφαρμογή — Passly",
  description:
    "Κάρτα πιστότητας ή κουπόνι στο Apple Wallet για το μαγαζί σας — χωρίς εφαρμογή για τον πελάτη. Η ομάδα AI γράφει την καμπάνια· εσείς εγκρίνετε κάθε λέξη.",
  keywords: [
    "προσφορές κινητού χωρίς εφαρμογή",
    "κάρτα πιστότητας Apple Wallet",
    "loyalty program Apple Wallet Ελλάδα",
    "email marketing για καφετέρια",
    "πρόγραμμα πιστότητας για μικρές επιχειρήσεις",
    "ψηφιακό πάσο καταστήματος",
  ],
  alternates: { canonical: "/" },
  openGraph: {
    title: "Κάρτα πιστότητας στο κινητό, χωρίς εφαρμογή — Passly",
    description:
      "Κάρτα πιστότητας ή κουπόνι στο Apple Wallet για το μαγαζί σας. Η ομάδα AI γράφει την καμπάνια· εσείς εγκρίνετε κάθε λέξη.",
    url: "/",
  },
};

// Three shops, three jobs to be done. Written from the owner's complaint, not
// from the feature list — and kept to what Passly actually does today (pass +
// email), so nothing here outruns the demo.
const SCENARIOS = [
  {
    shop: "Καφετέρια",
    shopEn: "Coffee shop",
    title: "Ο δέκατος καφές",
    job: "«Οι ίδιοι πελάτες περνούν κάθε πρωί. Δεν έχω τρόπο να τους ανταμείψω χωρίς χαρτάκια και σφραγίδες.»",
    how: "Το πάσο μετράει τις επισκέψεις. Στη δέκατη έρχεται το κέρασμα και η κάρτα ξεκινάει από την αρχή.",
    howEn: "The pass counts visits; the tenth is on the house.",
  },
  {
    shop: "Κομμωτήριο",
    shopEn: "Hair salon",
    title: "Το ραντεβού που δεν κλείστηκε",
    job: "«Περνούν τρεις μήνες, ο πελάτης δεν ξαναήρθε, κι εγώ δεν θυμάμαι ποιον να πάρω τηλέφωνο.»",
    how: "Ο κατάλογος πελατών χτίζεται μόνος του με κάθε πάσο. Την υπενθύμιση τη γράφει η ομάδα AI και τη στέλνετε εσείς.",
    howEn: "Every pass adds a customer; the crew drafts the reminder.",
  },
  {
    shop: "Κατάστημα ρούχων",
    shopEn: "Clothing shop",
    title: "Η προσφορά που δεν χάθηκε",
    job: "«Τυπώνω φυλλάδια για τις εκπτώσεις και καταλήγουν στον κάδο πριν φύγει ο πελάτης από το τετράγωνο.»",
    how: "Το κουπόνι κάθεται στο Wallet, δίπλα στα εισιτήρια και τις κάρτες επιβίβασης. Δεν χάνεται σε κανένα inbox.",
    howEn: "The coupon lives in Wallet, not in a paper flyer.",
  },
];

// The three objections a shop owner raises before anything else. They are also
// the FAQPage below — one source, so the copy and the markup cannot drift.
const OBJECTIONS = [
  {
    question: "Δεν έχω χρόνο για μάρκετινγκ.",
    answer:
      "Το πάσο στήνεται σε λίγα λεπτά από μία σελίδα. Την πρώτη καμπάνια τη γράφει η ομάδα AI· εσείς τη διαβάζετε και λέτε ναι, όχι, ή «ξαναγράψ’ το».",
  },
  {
    question: "Πρέπει ο πελάτης να κατεβάσει εφαρμογή;",
    answer:
      "Όχι. Ανοίγει ένα link και το πάσο μπαίνει στο Apple Wallet που έχει ήδη το κινητό του. Εφαρμογή Passly δεν υπάρχει.",
  },
  {
    question: "Θα γίνω spam στους πελάτες μου;",
    answer:
      "Τίποτα δεν φεύγει χωρίς την έγκρισή σας. Κάθε κείμενο περνάει από εσάς πριν σταλεί — η ομάδα AI προτείνει, δεν στέλνει.",
  },
];

// Product, publisher and the objections as a FAQ. Deliberately no
// LocalBusiness: Passly is software, not a shop with an address — the Greek
// targeting is carried by `areaServed` and `inLanguage` instead.
const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: "Passly",
      url: SITE_URL,
      description:
        "Wallet passes and AI-drafted marketing campaigns for small shops in Greece.",
      areaServed: { "@type": "Country", name: "Greece" },
    },
    {
      "@type": "SoftwareApplication",
      "@id": `${SITE_URL}/#software`,
      name: "Passly",
      url: SITE_URL,
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      description:
        "Κάρτα πιστότητας ή κουπόνι στο Apple Wallet για μικρές επιχειρήσεις στην Ελλάδα, με καμπάνιες που γράφει μια ομάδα AI και εγκρίνει ο ιδιοκτήτης.",
      inLanguage: ["el", "en"],
      areaServed: { "@type": "Country", name: "Greece" },
      audience: {
        "@type": "BusinessAudience",
        audienceType: "Μικρές επιχειρήσεις λιανικής και υπηρεσιών στην Ελλάδα",
      },
      featureList: [
        "Σχεδιασμός κάρτας πιστότητας ή κουπονιού για Apple Wallet",
        "Εγγραφή πελατών από το κινητό, χωρίς εφαρμογή",
        "Μέτρηση επισκέψεων με σφραγίδες και ανταμοιβή στον στόχο",
        "Καμπάνια που γράφει η ομάδα AI και εγκρίνει ο ιδιοκτήτης",
      ],
      publisher: { "@id": `${SITE_URL}/#organization` },
    },
    {
      "@type": "FAQPage",
      "@id": `${SITE_URL}/#faq`,
      inLanguage: "el",
      mainEntity: OBJECTIONS.map((o) => ({
        "@type": "Question",
        name: o.question,
        acceptedAnswer: { "@type": "Answer", text: o.answer },
      })),
    },
  ],
};


export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6">
      {/* Structured data goes in the body per the Next.js JSON-LD guide. */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />

      <nav className="flex items-center justify-between py-6">
        <span className="font-display text-lg font-extrabold tracking-tight">
          Passly
        </span>
        <StackStatus />
      </nav>

      {/* ── hero: the owner's problem first, the product second ──────── */}
      <div className="grid flex-1 items-center gap-12 py-10 lg:grid-cols-2">
        <div className="rise" lang="el">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">
            Πάσο στο Apple Wallet · καμπάνιες με έγκρισή σας
          </p>
          <h1 className="font-display mt-4 text-5xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
            Ο πελάτης ήρθε
            <br />
            μία φορά. Πώς θα
            <br />
            <span className="text-accent">τον ξαναφέρετε;</span>
          </h1>
          <p className="mt-5 max-w-md text-base text-muted">
            Με μια κάρτα πιστότητας στο κινητό του — μέσα στο Apple Wallet, χωρίς
            εφαρμογή να κατεβάσει. Τη φτιάχνετε σε λίγα λεπτά και η ομάδα AI
            γράφει την πρώτη καμπάνια· εσείς εγκρίνετε κάθε λέξη.
          </p>
          <p className="mt-3 max-w-md text-sm text-muted/80" lang="en">
            They came once. Bringing them back should not need an app — a
            loyalty pass in their wallet, and a campaign you approve.
          </p>
          <div className="mt-8 flex items-center gap-4">
            <Link
              href="/design"
              className="rounded-xl bg-foreground px-6 py-3 text-sm font-semibold text-background transition hover:opacity-90"
            >
              Φτιάξτε το πάσο σας →
            </Link>
            <span className="text-xs text-muted" lang="en">
              Demo · synthetic data
            </span>
          </div>
        </div>

        <div className="flex justify-center lg:justify-end">
          <div className="rise [animation-delay:120ms] rotate-3 transition-transform hover:rotate-0">
            <PassPreview design={defaultDesign} logoSrc={demoLogoSrc} />
          </div>
        </div>
      </div>


      <HowItWorks />
      <Faq />
    </main>
  );
}

function StackStatus() {
  const [ok, setOk] = useState<boolean | null>(null);

      {/* ── three shops, three jobs ──────────────────────────────────── */}
      <section className="border-t border-line py-14" lang="el">
        <h2 className="font-display text-xs font-bold uppercase tracking-[0.18em] text-muted">
          Πώς μοιάζει στην πράξη
        </h2>
        <div className="mt-6 grid gap-5 md:grid-cols-3">
          {SCENARIOS.map((s) => (
            <article
              key={s.title}
              className="rounded-2xl border border-line bg-card p-6"
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">
                {s.shop}
              </p>
              <h3 className="font-display mt-2 text-xl font-bold tracking-tight">
                {s.title}
              </h3>
              <p className="mt-3 text-sm italic text-muted">{s.job}</p>
              <p className="mt-3 text-sm">{s.how}</p>
              <p className="mt-3 text-xs text-muted/80" lang="en">
                {s.shopEn} — {s.howEn}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* ── the objections, answered ─────────────────────────────────── */}
      <section className="border-t border-line py-14" lang="el">
        <h2 className="font-display text-xs font-bold uppercase tracking-[0.18em] text-muted">
          «Ναι, αλλά…»
        </h2>
        <dl className="mt-6 grid gap-8 md:grid-cols-3">
          {OBJECTIONS.map((o) => (
            <div key={o.question}>
              <dt className="font-display text-base font-bold tracking-tight">
                {o.question}
              </dt>
              <dd className="mt-2 text-sm text-muted">{o.answer}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-10 flex items-center gap-4">
          <Link
            href="/design"
            className="rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:opacity-90"
          >
            Ξεκινήστε από το πάσο →
          </Link>
          <span className="text-xs text-muted">
            Δοκιμαστική έκδοση · εικονικά δεδομένα.
          </span>
        </div>
      </section>
    </main>
  );
}
