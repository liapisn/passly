"use client";

import { useState } from "react";
import Link from "next/link";

// The objections a Greek shop owner raises before they will try anything —
// answered in plain words, and only about what Passly actually does today.
// Questions and answers are plain strings so the accordion and the FAQPage
// rich result render from the same source and can never drift apart.
const FAQ = [
  {
    q: "Τι είναι ακριβώς το «πάσο»;",
    a:
      "Μια κάρτα πιστότητας που ζει στο Wallet του κινητού: το λογότυπό σας, " +
      "η προσφορά σας και οι σφραγίδες του πελάτη. Σε κάθε επίσκεψη προσθέτετε " +
      "μια σφραγίδα· όταν φτάσει τον στόχο, κερδίζει το δώρο και η κάρτα " +
      "ξεκινάει από την αρχή.",
  },
  {
    q: "Χρειάζεται να κατεβάσουν οι πελάτες μου εφαρμογή;",
    a:
      "Όχι. Το πάσο μπαίνει στο Wallet του κινητού τους — εκεί που έχουν ήδη " +
      "τις κάρτες και τα εισιτήριά τους. Σκανάρουν ένα QR ή ανοίγουν έναν " +
      "σύνδεσμο και τελείωσε.",
  },
  {
    q: "Χρειάζομαι εμπειρία στο marketing;",
    a:
      "Όχι. Λέτε στο Passly τι θέλετε να προσφέρετε και ο AI γράφει το μήνυμα. " +
      "Εσείς το εγκρίνετε, το διορθώνετε ή το απορρίπτετε.",
  },
  {
    q: "Πόσο χρόνο θέλει για να ξεκινήσω;",
    a:
      "Το πρώτο πάσο φτιάχνεται σε λίγα λεπτά: όνομα καταστήματος, χρώματα, " +
      "η προσφορά σας. Δεν χρειάζεται εγκατάσταση, ούτε αλλαγή στον τρόπο που " +
      "δουλεύετε στο μαγαζί.",
  },
  {
    q: "Είναι εντάξει με το GDPR να στέλνω μηνύματα στους πελάτες μου;",
    a:
      "Το Passly γράφει πελάτες μόνο όταν εγγράφονται μόνοι τους — σκανάρουν " +
      "το QR ή ανοίγουν τον σύνδεσμό σας και δίνουν τα στοιχεία τους. Καμία " +
      "αγορασμένη λίστα. Και κανένα μήνυμα δεν φεύγει αυτόματα: κάθε καμπάνια " +
      "περνάει πρώτα από τη δική σας έγκριση.",
  },
  {
    q: "Τι κοστίζει;",
    a:
      "Ετοιμάζουμε την τιμολόγηση. Μέχρι τότε μπορείτε να φτιάξετε ένα πάσο " +
      "και να το δείτε στο κινητό σας.",
  },
];

// Escaped per the Next.js JSON-LD guide: `<` becomes its unicode equivalent so
// no string in the payload can close the script tag.
const faqJsonLd = JSON.stringify({
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQ.map(({ q, a }) => ({
    "@type": "Question",
    name: q,
    acceptedAnswer: { "@type": "Answer", text: a },
  })),
}).replace(/</g, "\\u003c");

export function Faq() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section id="faq" lang="el" className="border-t border-line py-16">
      <h2 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
        Συχνές ερωτήσεις
      </h2>

      <dl className="mt-8 max-w-3xl divide-y divide-line border-y border-line">
        {FAQ.map((item, i) => {
          const isOpen = open === i;
          return (
            <div key={item.q}>
              <dt>
                <button
                  type="button"
                  id={`faq-q-${i}`}
                  aria-expanded={isOpen}
                  aria-controls={`faq-a-${i}`}
                  onClick={() => setOpen(isOpen ? null : i)}
                  className="flex w-full items-center justify-between gap-4 py-5 text-left transition hover:text-accent"
                >
                  <span className="font-display text-base font-bold tracking-tight">
                    {item.q}
                  </span>
                  <span
                    aria-hidden="true"
                    className={`text-xl leading-none text-accent transition-transform ${
                      isOpen ? "rotate-45" : ""
                    }`}
                  >
                    +
                  </span>
                </button>
              </dt>
              {/* Kept in the DOM when collapsed — the answers are the page's
                  substance, and hiding them with display:none still leaves
                  them readable to crawlers. */}
              <dd
                id={`faq-a-${i}`}
                role="region"
                aria-labelledby={`faq-q-${i}`}
                className={`max-w-2xl pb-5 text-sm leading-relaxed text-muted ${
                  isOpen ? "" : "hidden"
                }`}
              >
                {item.a}
              </dd>
            </div>
          );
        })}
      </dl>

      <p className="mt-8 text-sm text-muted">
        Κάτι άλλο;{" "}
        <Link
          href="/design"
          className="font-medium text-accent underline underline-offset-4"
        >
          Φτιάξτε ένα πάσο και δείτε το στο κινητό σας →
        </Link>
      </p>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: faqJsonLd }}
      />
    </section>
  );
}
