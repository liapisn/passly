# SEO keyword map

The landing page (`web/app/page.tsx`) is written for a shop owner searching in
Greek, so the map below goes from what they type to what the page says back.
Each query has one place that answers it — if a row has no home on the page,
the copy is missing, not the keyword.

**No volumes here on purpose.** Nothing in this repo talks to a keyword tool,
and invented numbers would be worse than none. These are hypotheses to validate
once the page is served from a real domain and Search Console has data.

| Query | What they are really asking | Where the page answers it |
|-------|------------------------------|---------------------------|
| προσφορές κινητού χωρίς εφαρμογή | «Θα πρέπει να κατεβάσει κάτι ο πελάτης μου;» | Hero subheading + the objection «Πρέπει ο πελάτης να κατεβάσει εφαρμογή;» (also `FAQPage`) |
| κάρτα πιστότητας Apple Wallet | Knows the category, wants the Wallet version | `<title>`, meta description, `SoftwareApplication.description` |
| loyalty program Apple Wallet Ελλάδα | Same, phrased half in English — common for owners who read the Apple docs | Title + `areaServed: Greece` on both schema nodes |
| email marketing για καφετέρια | Channel + vertical, one specific shop type | The καφετέρια and κομμωτήριο scenarios (the reminder email the crew drafts) |
| ψηφιακό πάσο καταστήματος | The local word — Greek owners say «πάσο», not «wallet pass» | Hero eyebrow, "Πώς μοιάζει στην πράξη" |
| πρόγραμμα πιστότητας για μικρές επιχειρήσεις | Category head term, no product in mind yet | `SoftwareApplication.audience`, the three scenarios |

## Deliberately not targeted

- **Pricing queries** («κόστος», «τιμές») — there is no billing to describe.
- **SMS marketing** — in the venture scope, not in the build. Copy that ranks
  for it would be a promise the demo cannot keep.
- **Location / near-me queries** — Passly is software sold to shops, not a shop.
  That is also why the homepage carries `SoftwareApplication` + `Organization`
  and **not** `LocalBusiness`: the Greek targeting rides on `areaServed` and
  `inLanguage` instead of on a business type the product does not have.

## Measurement

Bounce rate, scroll depth and CTA click-through are the numbers that would tell
us whether the problem-first hero beats the feature-first one. None of them can
be read today — no analytics is installed and the app is not deployed
(`docs/demo-runbook.md`). That measurement is a separate decision, not part of
this page.
