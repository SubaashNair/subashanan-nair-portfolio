import Link from "next/link";

export default function NotFound() {
  return (
    <main id="main" className="chapter">
      <div className="wrap">
        <div className="tile-frame" style={{ maxWidth: 640 }}>
          <h1 className="chapter-title">Page not found</h1>
          <p>This page does not exist. It may have moved when the site was redesigned.</p>
          <div className="actions">
            <Link className="btn ink" href="/">Go to the home page</Link>
            <Link className="btn ink" href="/work">See the case studies</Link>
          </div>
        </div>
      </div>
    </main>
  );
}
