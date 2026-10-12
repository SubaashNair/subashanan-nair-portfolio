import type { MetadataRoute } from "next";

import { profile } from "@/content/profile";
import { studies } from "@/content/studies";

export default function sitemap(): MetadataRoute.Sitemap {
  const paths = ["/", "/work", ...studies.map((s) => `/work/${s.slug}`), "/experiments", "/about"];
  return paths.map((path) => ({ url: `${profile.siteUrl}${path}`, changeFrequency: "monthly" }));
}
