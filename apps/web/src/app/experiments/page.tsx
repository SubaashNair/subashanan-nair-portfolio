import type { Metadata } from "next";

import { ExperimentList } from "@/components/experiments/experiment-list";

export const metadata: Metadata = { title: "Tools and experiments", description: "Libraries, agents and apps Subashanan Nair has shipped. Most are open source." };

export default function ExperimentsPage() {
  return (
    <>
      <main id="main">
        <div className="top">
          <div className="wrap">
            <div className="page-hero solo">
              <div>
                <h1>Tools and experiments</h1>
                <p className="lede">Smaller things I have shipped: libraries, agents and apps. Most are open source, and each has its own tile.</p>
              </div>
            </div>
          </div>
        </div>
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
