import type { District, ServiceCategory } from "@/content/types";

const COLUMNS: ReadonlyArray<{ id: ServiceCategory; label: string }> = [
  { id: "clinic", label: "Clinic" },
  { id: "school", label: "School" },
  { id: "transit", label: "Transit stop" },
];

// Share of each district's residents more than 3 km by road from each service. Rows keep the fixed district order.
export function ServiceTable({ districts, selected }: { districts: readonly District[]; selected: string }) {
  return (
    <div className="table-wrap service-table" role="region" aria-labelledby="service-caption" tabIndex={0}>
      <table>
        <caption id="service-caption">Share of residents more than 3 km by road from the nearest service</caption>
        <thead>
          <tr>
            <th scope="col">District</th>
            {COLUMNS.map((c) => <th key={c.id} scope="col" className="num">{c.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {districts.map((d) => (
            <tr key={d.id} className={d.id === selected ? "on" : undefined} aria-current={d.id === selected ? "true" : undefined}>
              <th scope="row">{d.short}</th>
              {COLUMNS.map((c) => <td key={c.id} className="num">{d.far[c.id]}%</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
