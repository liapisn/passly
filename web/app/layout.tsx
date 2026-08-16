import type { Metadata } from "next";
import {
  Bricolage_Grotesque,
  Hanken_Grotesk,
  Geist_Mono,
  Manrope,
} from "next/font/google";
import "./globals.css";
import { SITE_URL } from "@/lib/seo";

const display = Bricolage_Grotesque({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

const body = Hanken_Grotesk({
  variable: "--font-body",
  subsets: ["latin"],
});

const mono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

// Neither Bricolage nor Hanken ships Greek glyphs, and the landing copy is
// Greek. Manrope does, so it sits behind both in the stacks (globals.css):
// Latin still comes from the brand faces, Greek from here instead of from
// whatever grotesque the visitor's OS happens to supply.
const greek = Manrope({
  variable: "--font-greek",
  subsets: ["greek"],
});

export const metadata: Metadata = {
  // Absolute base for canonical/OG URLs; pages then declare relative ones.
  metadataBase: new URL(SITE_URL),
  title: "Passly — wallet passes for Greek shops",
  description:
    "Create a branded wallet pass for your shop and let the AI crew write the campaign.",
  openGraph: {
    siteName: "Passly",
    type: "website",
    // The landing copy is Greek; the app pages behind it are English.
    locale: "el_GR",
    alternateLocale: "en_US",
  },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${body.variable} ${mono.variable} ${greek.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
