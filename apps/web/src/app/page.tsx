import { AboutBand } from "@/components/home/about-band";
import { Hero } from "@/components/home/hero";
import { ToolsPreview } from "@/components/home/tools-preview";
import { StudyRun } from "@/components/study/study-run";

export default function Home() {
  return (
    <>
      <main id="main">
        <Hero />
        <section className="block" aria-labelledby="work-h">
          <div className="wrap">
            <h2 id="work-h">Case studies</h2>
            <p className="intro">Three questions, answered with public data. Each one links its sources, code, model versions and known limits.</p>
            <StudyRun headingLevel={3} />
          </div>
        </section>
        <ToolsPreview />
      </main>
      <AboutBand />
    </>
  );
}
