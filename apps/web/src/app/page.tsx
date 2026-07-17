import Link from "next/link";

export default function Home() {
  return (
    <main>
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-grid" aria-hidden="true" />
        <div className="hero-copy">
          <p className="eyebrow">Data scientist × AI builder</p>
          <h1 id="hero-title">I turn complex data into living intelligence.</h1>
          <p className="hero-intro">
            Explore the systems, experiments, and spatial stories behind my work in machine learning and applied AI.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="#signals">
              Enter the observatory <span aria-hidden="true">→</span>
            </a>
            <a className="text-action" href="https://github.com/SubaashNair">
              View source <span aria-hidden="true">↗</span>
            </a>
          </div>
        </div>

        <div className="observatory-visual" aria-hidden="true">
          <div className="world">
            <div className="world-latitude" />
            <div className="world-longitude" />
            <span className="world-point point-one" />
            <span className="world-point point-two" />
            <span className="world-point point-three" />
          </div>
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="signal-readout">
            <span>OBSERVATORY / LIVE</span>
            <strong>2</strong>
            <span>active studies</span>
          </div>
        </div>

        <div className="hero-footnote" aria-label="Experience sequence">
          <span>01 Observe</span>
          <span>02 Discover</span>
          <span>03 Dive</span>
          <span>04 Understand</span>
        </div>
      </section>

      <section className="signals section-shell" id="signals" aria-labelledby="signals-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Selected signals</p>
            <h2 id="signals-title">Two systems. One connected story.</h2>
          </div>
          <p>
            Move from the geography of public services to the dynamics of traffic forecasting. Every finding includes
            provenance, methods, uncertainty, and reproducible code.
          </p>
        </div>

        <div className="study-grid">
          <article className="study-card penang-card">
            <div className="study-index">01 / Spatial intelligence</div>
            <div className="map-mark" aria-hidden="true">
              <span /><span /><span /><span /><span />
            </div>
            <div className="study-card-copy">
              <p className="source-label">PeGIS · DOSM · OpenStreetMap</p>
              <h3>Penang Pulse</h3>
              <p>How evenly are essential services distributed across Penang?</p>
              <Link href="/work/penang-pulse">Explore Penang Pulse <span aria-hidden="true">→</span></Link>
            </div>
          </article>

          <article className="study-card forecast-card">
            <div className="study-index">02 / Predictive systems</div>
            <div className="neural-mark" aria-hidden="true">
              <span className="n n1" /><span className="n n2" /><span className="n n3" />
              <span className="n n4" /><span className="n n5" /><span className="n n6" />
              <i className="connector c1" /><i className="connector c2" /><i className="connector c3" />
            </div>
            <div className="study-card-copy">
              <p className="source-label">UCI ML Repository · Dataset 608</p>
              <h3>Forecasting Lab</h3>
              <p>Compare baselines, tree models, and neural forecasts across a connected traffic network.</p>
              <Link href="/work/forecasting-lab">Enter Forecasting Lab <span aria-hidden="true">→</span></Link>
            </div>
          </article>
        </div>

        <div className="next-signal">
          <div><span className="pulse-dot" /> NASA signal · Earth observation and environmental change · coming next</div>
        </div>
      </section>
    </main>
  );
}
