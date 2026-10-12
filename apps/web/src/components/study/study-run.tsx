import { studies } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

import { StudyCard } from "./study-card";

export function StudyRun({ headingLevel }: { headingLevel: 2 | 3 }) {
  return (
    <div className="tile-run">
      {studies.map((study) => (
        <StudyCard key={study.slug} study={study} results={getStudyResults(study.slug)} headingLevel={headingLevel} />
      ))}
    </div>
  );
}
