import Link from "next/link";

import { Tile } from "@/components/tiles/tile";
import type { StudyRecord, StudySlug, StudyStatus } from "@/content/types";
import type { LoadedResults } from "@/lib/study-results";

export const STATUS_LABEL: Readonly<Record<StudyStatus, string>> = { published: "Published", "in-progress": "In progress", planned: "Planned" };

interface StudyCardProps {
  study: StudyRecord;
  results: LoadedResults<StudySlug> | null;
  headingLevel: 2 | 3;
}

export function StudyCard({ study, results, headingLevel }: StudyCardProps) {
  const Heading = headingLevel === 2 ? "h2" : "h3";
  const href = `/work/${study.slug}`;
  const key = results?.data.keyNumbers[0];

  return (
    <article className={`tile-frame study-card ${study.themeClass}`}>
      <div className="card-marks" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => <Tile key={i} spec={study.tile} />)}
      </div>
      <span className={study.status === "planned" ? "tag plan" : "tag"}>{STATUS_LABEL[study.status]}</span>
      <Heading><Link href={href}>{study.title}</Link></Heading>
      <p className="q">{study.question}</p>
      {key ? (
        <p className="key">
          {results?.preview && <span className="preview-flag">Illustrative preview</span>}
          <strong>{key.value}</strong>
          {key.label}
        </p>
      ) : (
        <p className="key pending">Results appear here once the analysis is published.</p>
      )}
      <p className="data">Data: {study.data}</p>
      <Link className="btn ink" href={href}>{study.status === "planned" ? "Read the plan" : `Open ${study.title}`}</Link>
    </article>
  );
}
