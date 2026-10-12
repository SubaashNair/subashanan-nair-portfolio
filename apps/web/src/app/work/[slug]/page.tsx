import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { StudyPage } from "@/components/study/study-page";
import { findStudy, studies } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

export const dynamicParams = false;

export async function generateStaticParams(): Promise<Array<{ slug: string }>> {
  return studies.map((s) => ({ slug: s.slug }));
}

interface RouteProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: RouteProps): Promise<Metadata> {
  const study = findStudy((await params).slug);
  return study ? { title: `${study.title}, a case study`, description: study.question } : {};
}

export default async function StudyRoute({ params }: RouteProps) {
  const study = findStudy((await params).slug);
  if (!study) notFound();
  return <StudyPage study={study} results={getStudyResults(study.slug)} />;
}
