import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <nav aria-label="Primary" className="site-nav">
        <Link className="brand" href="/" aria-label="AI Observatory home">
          <span className="brand-mark" aria-hidden="true" />
          <span>AI Observatory</span>
        </Link>
        <div className="nav-links">
          <Link href="/work">Work</Link>
          <Link href="/experiments">Experiments</Link>
          <Link href="/about">About</Link>
          <a className="nav-github" href="https://github.com/SubaashNair">
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </div>
      </nav>
    </header>
  );
}
