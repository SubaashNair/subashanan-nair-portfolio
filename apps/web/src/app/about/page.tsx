import type { Metadata } from "next";

import { ContactButtons } from "@/components/home/about-band";
import { profile } from "@/content/profile";

export const metadata: Metadata = { title: "About", description: profile.intro };

export default function About() {
  return (
    <>
      <main id="main">
        <div className="top">
          <div className="wrap">
            <div className="page-hero solo">
              <div>
                <h1>About</h1>
                <p className="lede">{profile.intro}</p>
              </div>
            </div>
          </div>
        </div>
        <div className="wrap">
          <div className="cols part">
            <section className="frame" aria-labelledby="what-h">
              <h2 id="what-h">What I work on</h2>
              <ul>{profile.workOn.map((x) => <li key={x}>{x}</li>)}</ul>
            </section>
            <section className="frame" aria-labelledby="how-h">
              <h2 id="how-h">How I work</h2>
              <ul>{profile.howIWork.map((x) => <li key={x}>{x}</li>)}</ul>
            </section>
          </div>
          <section className="part" aria-labelledby="kit-h">
            <h2 id="kit-h">Toolkit</h2>
            <ul className="toolkit">{profile.toolkit.map((x) => <li key={x}>{x}</li>)}</ul>
          </section>
          <section className="part page-end" id="contact" aria-labelledby="contact-h">
            <h2 id="contact-h">Contact</h2>
            <p className="intro">{profile.openTo}</p>
            <ContactButtons tone="light" />
          </section>
        </div>
      </main>
    </>
  );
}
