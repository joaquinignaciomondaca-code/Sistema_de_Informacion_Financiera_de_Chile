import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-jb",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MFC · Monitor Financiero Chile — catálogo y consultas gobernadas",
  description:
    "Workbench de datos centralizado para carteras institucionales: catálogo versionado, mapa relacional auto-derivado, consola SQL de sólo lectura con timeout, cache y auditoría.",
};

export const viewport: Viewport = {
  themeColor: "#191e29",
};

const themeInit = `(function(){try{var t=localStorage.getItem('mfc.theme')||'swissborg';document.documentElement.dataset.theme=t;}catch(e){}})();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es" className={`${inter.variable} ${mono.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
