import type { Metadata } from "next";
import { Bricolage_Grotesque } from "next/font/google";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/shell/site-footer";
import { SiteHeader } from "@/components/shell/site-header";
import { profile } from "@/content/profile";

import "./globals.css";
import "./site.css";

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  axes: ["opsz", "wdth"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(profile.siteUrl),
  title: { default: "Subashanan Nair, data scientist in Penang", template: "%s | Subashanan Nair" },
  description: "Reproducible ML and LLM case studies on public data, mostly Malaysian, with sources, code and limits for every result.",
  openGraph: { type: "website", siteName: "Subashanan Nair" },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={bricolage.variable}>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
