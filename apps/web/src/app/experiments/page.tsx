import type { Metadata } from "next";

import { ExperimentList } from "@/components/experiments/experiment-list";

export const metadata: Metadata = { title: "Tools and experiments", description: "Libraries, agents and apps Subashanan Nair has shipped. All open source." };

export default function ExperimentsPage() {
  return (
    <>
      <div className="top">
        <div className="wrap">
          <div className="page-hero solo">
            <div>
              <h1>Tools and experiments</h1>
              <p className="lede">Smaller things I have shipped: libraries, agents and apps. All open source, each with its own tile.</p>
            </div>
          </div>
        </div>
      </div>
      <main id="main">
        <div className="wrap page-end">
          <section className="part" aria-labelledby="list-h">
            <h2 id="list-h" className="sr">All tools</h2>
            <ExperimentList />
          </section>
        </div>
      </main>
    </>
  );
}
