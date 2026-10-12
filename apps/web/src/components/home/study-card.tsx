import Link from "next/link";

interface StudyCardProps {
  index: string;
  variant: "penang" | "forecast";
  sourceLabel: string;
  title: string;
  description: string;
  href: string;
  cta: string;
}

export function StudyCard({ index, variant, sourceLabel, title, description, href, cta }: StudyCardProps) {
  return (
    <article className={`study-card ${variant === "penang" ? "penang-card" : "forecast-card"}`}>
      <div className="study-index">{index}</div>
      {variant === "penang" ? (
        <div className="map-mark" aria-hidden="true">
          <span /><span /><span /><span /><span />
        </div>
      ) : (
        <div className="neural-mark" aria-hidden="true">
          <span className="n n1" /><span className="n n2" /><span className="n n3" />
          <span className="n n4" /><span className="n n5" /><span className="n n6" />
          <i className="connector c1" /><i className="connector c2" /><i className="connector c3" />
        </div>
      )}
      <div className="study-card-copy">
        <p className="source-label">{sourceLabel}</p>
        <h3>{title}</h3>
        <p>{description}</p>
        <Link href={href}>{cta} <span aria-hidden="true">→</span></Link>
      </div>
    </article>
  );
}
