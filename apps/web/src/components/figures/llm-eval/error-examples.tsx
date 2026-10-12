import type { ErrorExample } from "@/content/types";

export function ErrorExamples({ examples }: { examples: readonly ErrorExample[] }) {
  return (
    <>
      <h3 className="sub">Error examples</h3>
      <p className="intro">Three items from the Manglish sentiment set, picked to show where models slip.</p>
      <div className="examples">
        {examples.map((e) => (
          <article key={e.input} className="tile-frame">
            <span className={e.correct ? "verdict ok" : "verdict miss"}>{e.correct ? "Correct" : "Missed"}</span>
            <blockquote>&ldquo;{e.input}&rdquo;</blockquote>
            <dl>
              <dt>Expected</dt><dd>{e.expected}</dd>
              <dt>Model</dt><dd>{e.model}</dd>
              <dt>Output</dt><dd>{e.output}</dd>
              <dt>Note</dt><dd>{e.note}</dd>
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}
