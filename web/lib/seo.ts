// Absolute origin for canonical links, OG tags and JSON-LD `@id`s.
//
// Passly is not deployed (docs/demo-runbook.md) — the demo runs from a laptop
// behind a tunnel whose hostname changes on every start, so there is no stable
// public URL to hard-code. Set NEXT_PUBLIC_SITE_URL once a domain exists; the
// localhost default keeps the metadata well-formed until then.
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
