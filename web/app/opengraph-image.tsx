import { ImageResponse } from "next/og";

// The social preview, drawn from the same palette as globals.css: warm paper,
// pine-green pass. Generated rather than shipped as a file so the copy stays
// editable in one place — a link to Passly should say what Passly is.
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt =
  "Passly — κάρτα πιστότητας στο Apple Wallet, χωρίς εφαρμογή";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#f6f3ec",
          color: "#1a1c1a",
          padding: 72,
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", fontSize: 30, fontWeight: 700 }}>
          Passly
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 40, color: "#0b5d3b", letterSpacing: 2 }}>
            ΚΑΡΤΑ ΠΙΣΤΟΤΗΤΑΣ ΣΤΟ APPLE WALLET
          </div>
          <div style={{ fontSize: 76, lineHeight: 1.1, marginTop: 16 }}>
            Ο πελάτης ήρθε μία φορά.
          </div>
          <div style={{ fontSize: 76, lineHeight: 1.1, color: "#0b5d3b" }}>
            Πώς θα τον ξαναφέρετε;
          </div>
        </div>
        <div style={{ display: "flex", fontSize: 30, color: "#6b6f68" }}>
          Χωρίς εφαρμογή για τον πελάτη · καμπάνιες με έγκρισή σας
        </div>
      </div>
    ),
    size,
  );
}
