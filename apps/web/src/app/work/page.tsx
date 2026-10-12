import type { Metadata } from "next";

import { StudyRun } from "@/components/study/study-run";
import { Frieze } from "@/components/tiles/frieze";
import { Tile } from "@/components/tiles/tile";
import { tileMarkup } from "@/components/tiles/tile-geometry";
import { studies } from "@/content/studies";

export const metadata: Metadata = { title: "Case studies", description: "Three questions about Malaysia, answered with public data." };

export default function WorkIndex() {
  return (
    <>
      <div className="top">
        <div className="wrap">
          <div className="page-hero">
            <div>
              <h1>Case studies</h1>
              <p className="lede">Three questions about Malaysia, answered with public data. Each one links its sources, code, model versions and known limits.</p>
            </div>
            <div className="hero-side">
              <div className="marks-row" aria-hidden="true">{studies.map((s) => <Tile key={s.slug} spec={s.tile} />)}</div>
              <p className="mosaic-note">One tile per study. You will find it on every page of that study.</p>
            </div>
          </div>
        </div>
      </div>
      <Frieze markups={studies.map((s) => tileMarkup(s.tile))} />
      <main id="main" className="chapter">
        <div className="wrap"><StudyRun headingLevel={2} /></div>
      </main>
    </>
  );
}
