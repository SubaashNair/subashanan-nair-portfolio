"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Tile } from "@/components/tiles/tile";
import { mixedTile } from "@/components/tiles/tile-geometry";
import { profile } from "@/content/profile";

const LINKS = [
  { href: "/work", label: "Work" },
  { href: "/experiments", label: "Experiments" },
  { href: "/about", label: "About" },
] as const;

export function SiteHeader() {
  const pathname = usePathname() ?? "/";
  const isCurrent = (href: string): boolean => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <div className="top">
      <div className="wrap">
        <header className="site">
          <Link className="wordmark" href="/" aria-current={pathname === "/" ? "page" : undefined}>
            <Tile spec={mixedTile(0)} />
            {profile.name}
          </Link>
          <nav className="primary" aria-label="Primary">
            {LINKS.map((link) => (
              <Link key={link.href} href={link.href} aria-current={isCurrent(link.href) ? "page" : undefined}>
                {link.label}
              </Link>
            ))}
            <a className="gh" href={profile.githubUrl}>GitHub</a>
          </nav>
        </header>
      </div>
    </div>
  );
}
