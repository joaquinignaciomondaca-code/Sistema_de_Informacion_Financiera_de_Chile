import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Instrument_Serif } from "next/font/google";
import "./globals.css";

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plex-sans",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
  display: "swap",
});

const display = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-instrument",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Monitor Financiero Chile — Carteras institucionales y mapa relacional",
  description:
    "Centralizador de datos regulatorios chilenos: cartera de inversiones de la CMF, series del Banco Central y consulta SQL sobre datasets institucionales.",
};

export const viewport: Viewport = {
  themeColor: "#070B0C",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-CL" className={`${sans.variable} ${mono.variable} ${display.variable}`}>
      <body className="min-h-screen bg-ink font-sans text-paper antialiased">{children}</body>
    </html>
  );
}
