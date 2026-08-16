// The public pitch, in Greek — the language the customer-facing pages already
// speak. Three steps that answer "τι πρέπει να κάνω;" before the shop owner
// has to ask, and that lead with the outcome rather than the stack.
export function HowItWorks() {
  return (
    <section id="how-it-works" lang="el" className="border-t border-line py-16">
      <h2 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
        Πώς δουλεύει — σε τρία βήματα
      </h2>
      <p className="mt-3 max-w-md text-base text-muted">
        Καμία εμπειρία στο marketing. Καμία εγκατάσταση για τους πελάτες.
      </p>

      <ol className="mt-10 grid gap-6 sm:grid-cols-3">
        {STEPS.map((step, i) => (
          <li
            key={step.title}
            className="rounded-2xl border border-line bg-card p-6"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-accent">
              {step.icon}
            </span>
            <h3 className="font-display mt-4 text-lg font-bold tracking-tight">
              {i + 1}. {step.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">
              {step.body}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}

// The icons repeat what the heading beside them already says, so they are
// decorative — hidden from screen readers rather than given a label to read
// twice.
const iconCls = "h-5 w-5";
const iconProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  className: iconCls,
  "aria-hidden": true,
};

const STEPS = [
  {
    title: "Συνδέστε τους πελάτες σας",
    body:
      "Μια φορά: πείτε τους να σκανάρουν ένα QR ή να κάνουν κλικ σε έναν " +
      "σύνδεσμο. Ή φορτώστε τη λίστα σας (email ή τηλέφωνο).",
    icon: (
      <svg {...iconProps}>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <path d="M14 14h3v3h-3zM20.5 14v3M14 20.5h7" />
      </svg>
    ),
  },
  {
    title: "Ο AI προτείνει. Εσείς αποφασίζετε.",
    body:
      "Πείτε στο Passly τι θέλετε: «Δώσε 20% σε πρώτη επίσκεψη» ή «50% στον " +
      "καφέ αύριο». Ο AI γράφει το μήνυμα. Εσείς κάνετε κλικ ναι ή όχι.",
    icon: (
      <svg {...iconProps}>
        <path d="M11 3.5l1.7 4.6 4.6 1.7-4.6 1.7L11 16.1 9.3 11.5 4.7 9.8l4.6-1.7z" />
        <path d="M18 15l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z" />
      </svg>
    ),
  },
  {
    title: "Εμφανίζεται στο Wallet",
    body:
      "Το πάσο εμφανίζεται στο Apple Wallet ή στο Google Wallet του πελάτη — " +
      "δεν χρειάζεται app. Με ένα κλικ, στείλτε και SMS ή email, αν θέλετε.",
    icon: (
      <svg {...iconProps}>
        <rect x="3" y="6" width="18" height="13" rx="2.5" />
        <path d="M3 10.5h18" />
        <circle cx="17" cy="14.75" r="1.25" />
      </svg>
    ),
  },
];
