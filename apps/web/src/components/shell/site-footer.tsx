import { profile } from "@/content/profile";

export function SiteFooter() {
  return (
    <div className="about-band foot-only">
      <div className="wrap">
        <footer className="site">
          <span>{profile.name}, {profile.place}</span>
          <span className="actions">
            <a href={profile.githubUrl}>GitHub</a>
            <a href={profile.sourceUrl}>Source for this site</a>
          </span>
        </footer>
      </div>
    </div>
  );
}
