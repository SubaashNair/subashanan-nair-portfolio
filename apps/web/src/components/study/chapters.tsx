import Link from "next/link";
import type { ComponentType } from "react";

import { figures } from "@/components/figures/registry";
import { Tile } from "@/components/tiles/tile";
import { profile } from "@/content/profile";
import { neighbours } from "@/content/studies";
import type { StudyRecord, StudyResultsBySlug, StudySlug } from "@/content/types";
import type { LoadedResults } from "@/lib/study-results";

import { FigurePending } from "./figure-pending";

type Results = LoadedResults<StudySlug> | null;

function ChapterTitle({ id, study, children }: { id: string; study: StudyRecord; children: string }) {
  return (
    <h2 className="chapter-title" id={id}>
      <Tile spec={study.tile} />
      {children}
    </h2>
  );
}

function PreviewFlag({ results }: { results: Results }) {
  return results?.preview ? <p className="preview-flag">Preview with illustrative data. These are not results.</p> : null;
}

export function AnswerChapter({ study, results }: { study: StudyRecord; results: Results }) {
  return (
    <section className="chapter" aria-labelledby="ch-answer">
      <div className="wrap">
        <ChapterTitle id="ch-answer" study={study}>The answer</ChapterTitle>
        <PreviewFlag results={results} />
        <p className="short-answer">{results ? results.data.answer : study.plannedAnswer}</p>
        {results && (
          <>
            <h3 className="sub">Key numbers</h3>
            <div className="num-run">
              {results.data.keyNumbers.map((n) => (
                <div key={n.value} className="tile-frame num-tile">
                  <strong>{n.value}</strong>
                  <p>{n.label}</p>
                  <p className="caveat">{n.caveat}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export function EvidenceChapter({ study, results }: { study: StudyRecord; results: Results }) {
  const Figure = figures[study.slug] as ComponentType<{ data: StudyResultsBySlug[StudySlug] }> | undefined;
  return (
    <section className="chapter dark" aria-labelledby="ch-evidence">
      <div className="wrap">
        <ChapterTitle id="ch-evidence" study={study}>The evidence</ChapterTitle>
        <PreviewFlag results={results} />
        {results && Figure ? <Figure data={results.data} /> : <FigurePending study={study} />}
      </div>
    </section>
  );
}

export function MadeChapter({ study, results }: { study: StudyRecord; results: Results }) {
  return (
    <section className="chapter" aria-labelledby="ch-made">
      <div className="wrap">
        <ChapterTitle id="ch-made" study={study}>How it was made</ChapterTitle>
        <div>
          <h3 className="sub" id="sources-h">Data sources</h3>
          <div className="table-wrap" role="region" aria-labelledby="sources-h" tabIndex={0}>
            <table>
              <thead>
                <tr><th scope="col">Source</th><th scope="col">Publisher</th><th scope="col">What we used</th><th scope="col">Licence</th><th scope="col">Retrieved</th></tr>
              </thead>
              <tbody>
                {study.sources.map((s) => (
                  <tr key={s.name}>
                    <th scope="row">{s.name}</th>
                    <td>{s.publisher}</td>
                    <td>{s.used}</td>
                    <td>{s.licence}</td>
                    <td>{results?.data.retrieved[s.name] ?? "Not yet retrieved"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h3 className="sub">Method</h3>
          <ol className="steps">{study.method.map((step) => <li key={step}><span>{step}</span></li>)}</ol>
        </div>
        <div>
          <h3 className="sub">Limitations</h3>
          <ul className="limits">{study.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
        </div>
      </div>
    </section>
  );
}

export function CheckChapter({ study, results }: { study: StudyRecord; results: Results }) {
  const { prev, next } = neighbours(study.slug);
  const run = results?.data.run;
  return (
    <section className="chapter deep" aria-labelledby="ch-check">
      <div className="wrap">
        <ChapterTitle id="ch-check" study={study}>Check it yourself</ChapterTitle>
        <div className="check-grid">
          <div>
            <h3 className="sub">Reproduce</h3>
            {run ? (
              <>
                <pre className="code" tabIndex={0}><code>{study.reproduce.commands.join("\n")}</code></pre>
                <dl className="run-meta">
                  <div><dt>Commit</dt><dd><code>{run.commit}</code></dd></div>
                  <div><dt>Manifest</dt><dd><code>{run.manifest}</code></dd></div>
                  <div><dt>Python</dt><dd>{run.python}</dd></div>
                  <div><dt>Last run</dt><dd>{run.lastRun}</dd></div>
                </dl>
                {study.reproduce.note && <p className="note">{study.reproduce.note}</p>}
              </>
            ) : (
              <p className="note">Reproduction steps appear here with the first published run.</p>
            )}
          </div>
          <div>
            <h3 className="sub">Discuss</h3>
            <p className="note">{study.discussNote}</p>
            <p><a className="btn quiet" href={profile.discussUrl}>Discuss this study on GitHub</a></p>
          </div>
        </div>
        <nav className="pager" aria-label="More case studies">
          <Link className={`tile-frame ${prev.themeClass}`} href={`/work/${prev.slug}`}>
            <Tile spec={prev.tile} />
            <span><small>Previous study</small> <b>{prev.title}</b></span>
          </Link>
          <Link className={`tile-frame next ${next.themeClass}`} href={`/work/${next.slug}`}>
            <span><small>Next study</small> <b>{next.title}</b></span>
            <Tile spec={next.tile} />
          </Link>
        </nav>
      </div>
    </section>
  );
}
