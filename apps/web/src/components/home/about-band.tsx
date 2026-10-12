import Link from "next/link";

import { profile } from "@/content/profile";

/** Contact buttons. A missing contact value hides its button; GitHub is always available. */
export function ContactButtons({ tone }: { tone: "dark" | "light" }) {
  const quiet = tone === "dark" ? "btn quiet" : "btn ink";
  const { email, linkedin, cv } = profile.contact;
  return (
    <div className="actions">
      {email && <a className="btn primary" href={`mailto:${email}`}>Email me</a>}
      {linkedin && <a className={quiet} href={linkedin}>LinkedIn</a>}
      {cv && <a className={quiet} href={cv}>Download CV</a>}
      <a className={email ? quiet : "btn primary"} href={profile.githubUrl}>Find me on GitHub</a>
    </div>
  );
}

export function AboutBand() {
  return (
    <div className="about-band">
      <section className="block wrap about" aria-labelledby="about-h">
        <h2 id="about-h">About</h2>
        <div>
          <p>{profile.intro}</p>
          <p>{profile.openTo}</p>
          <ContactButtons tone="dark" />
          <p style={{ marginTop: 16 }}><Link href="/about">More about me</Link></p>
        </div>
      </section>
    </div>
  );
}
