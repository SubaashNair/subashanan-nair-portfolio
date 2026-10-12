import Link from "next/link";

import { Frieze } from "@/components/tiles/frieze";
import { Mosaic } from "@/components/tiles/mosaic";
import { borderTileMarkup, tileMarkup } from "@/components/tiles/tile-geometry";
import type { StudyRecord, StudySlug } from "@/content/types";
import type { LoadedResults } from "@/lib/study-results";

import { AnswerChapter, CheckChapter, EvidenceChapter, MadeChapter } from "./chapters";
import { STATUS_LABEL } from "./study-card";
import { studyThemeStyle } from "./study-theme";

interface StudyPageProps {
  study: StudyRecord;
  results: LoadedResults<StudySlug> | null;
}

export function StudyPage({ study, results }: StudyPageProps) {
  const frieze = [tileMarkup(study.tile), borderTileMarkup(study.tile, study.tint)];
  return (
    <div className={`study-page ${study.themeClass}`} style={studyThemeStyle(study)}>
      <main id="main">
        <div className="top">
          <div className="wrap">
            <div className="page-hero">
              <div>
                <Link className="crumb" href="/work">All case studies</Link>
                <br />
                <span className={study.status === "planned" ? "tag plan" : "tag"}>{STATUS_LABEL[study.status]}</span>
                <h1>{study.title}</h1>
                <p className="lede">{study.question}</p>
              </div>
              <Mosaic pair tiles={[study.tile, study.tile, study.tile, study.tile]} label={`${study.title} tiles. Select a tile to turn it.`} />
            </div>
          </div>
        </div>
        <Frieze markups={frieze} />
        <AnswerChapter study={study} results={results} />
        <Frieze markups={frieze} />
        <EvidenceChapter study={study} results={results} />
        <Frieze markups={frieze} />
        <MadeChapter study={study} results={results} />
        <Frieze markups={frieze} />
        <CheckChapter study={study} results={results} />
      </main>
    </div>
  );
}
