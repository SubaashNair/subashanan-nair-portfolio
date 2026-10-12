import { StudyCard } from "./study-card";

export function SignalsSection() {
  return (
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
        <StudyCard
          index="01 / Spatial intelligence"
          variant="penang"
          sourceLabel="PeGIS · DOSM · OpenStreetMap"
          title="Penang Pulse"
          description="How evenly are essential services distributed across Penang?"
          href="/work/penang-pulse"
          cta="Explore Penang Pulse"
        />
        <StudyCard
          index="02 / Predictive systems"
          variant="forecast"
          sourceLabel="UCI ML Repository · Dataset 608"
          title="Forecasting Lab"
          description="Compare baselines, tree models, and neural forecasts across a connected traffic network."
          href="/work/forecasting-lab"
          cta="Enter Forecasting Lab"
        />
      </div>

      <div className="next-signal">
        <div><span className="pulse-dot" /> NASA signal · Earth observation and environmental change · coming next</div>
      </div>
    </section>
  );
}
