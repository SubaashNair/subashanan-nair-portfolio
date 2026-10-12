export function Hero() {
  return (
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
  );
}
