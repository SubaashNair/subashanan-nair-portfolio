"use client";

import { useState } from "react";

import { TabList, tabId } from "@/components/ui/tab-list";
import { ToggleGroup } from "@/components/ui/toggle-group";
import type { ForecastModelId, ForecastResults } from "@/content/types";

import { ForecastChart } from "./forecast-chart";
import { HorizonChart } from "./horizon-chart";
import { MODEL_STYLE } from "./model-style";

const Swatch = ({ id }: { id: ForecastModelId }) => <span className="sw line" style={{ background: MODEL_STYLE[id].colour }} />;

export function ForecastFigure({ data }: { data: ForecastResults }) {
  const [sensorId, setSensorId] = useState(data.sensors[0].id);
  const [visible, setVisible] = useState<ReadonlySet<string>>(new Set(data.models.map((m) => m.id)));
  const sensor = data.sensors.find((s) => s.id === sensorId) ?? data.sensors[0];
  const best = data.horizons.map((_, i) => Math.min(...data.models.map((m) => m.mae[i])));

  return (
    <div>
      <h3 className="sub">Forecasts for the next two hours</h3>
      <p className="intro">Pick a sensor, then switch models on and off. The black line is the traffic that actually arrived. The model toggles also drive the error chart below.</p>
      <div className="controls">
        <span className="label" id="sensor-label">Sensor</span>
        <TabList labelledBy="sensor-label" idPrefix="sensor" panelId="forecast-panel" selected={sensorId} onSelect={setSensorId} items={data.sensors.map((s) => ({ id: s.id, label: s.label }))} />
      </div>
      <ToggleGroup label="Show or hide models" prefix="Models" pressed={visible} onChange={setVisible} items={data.models.map((m) => ({ id: m.id, label: <><Swatch id={m.id} />{m.name}</> }))} />
      <div className="stack">
        <figure className="tile-frame" id="forecast-panel" role="tabpanel" aria-labelledby={tabId("sensor", sensorId)}>
          <ForecastChart sensor={sensor} models={data.models} visible={visible} />
          <figcaption className="figcap">Flow index per {sensor.stepMinutes} minutes, where 100 is the busiest reading in the dataset. The shaded window is the forecast; the persistence line is dashed. Clock times are the dataset&apos;s own. Each sensor is shown at the test window where its flow changed most over two hours, so these windows are harder than average.</figcaption>
          <h4 className="panel-title" id="window-mae-h" style={{ marginTop: 20, fontSize: 17 }}>Mean absolute error in this window</h4>
          <ul className="band-legend mae-list" aria-labelledby="window-mae-h">
            {data.models.map((m) => <li key={m.id}><Swatch id={m.id} />{m.name}<strong>{sensor.windowMae[m.id].toFixed(1)}</strong></li>)}
          </ul>
        </figure>
        <figure className="tile-frame">
          <h4 className="panel-title">Error by horizon</h4>
          <p className="figcap" style={{ margin: "0 0 14px" }}>Mean absolute error on the test window, all sensors, in flow index points. Lower is better.</p>
          <HorizonChart horizons={data.horizons} models={data.models} visible={visible} />
          <div className="table-wrap" role="region" aria-label="Mean absolute error by horizon" tabIndex={0} style={{ marginTop: 18 }}>
            <table>
              <thead>
                <tr><th scope="col">Model</th>{data.horizons.map((hz) => <th key={hz} scope="col" className="num">{hz} min</th>)}</tr>
              </thead>
              <tbody>
                {data.models.map((m) => (
                  <tr key={m.id}>
                    <th scope="row"><span className="model-name"><Swatch id={m.id} />{m.name}</span></th>
                    {m.mae.map((v, i) => <td key={i} className="num">{v === best[i] ? <b>{v.toFixed(2)}</b> : v.toFixed(2)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </figure>
      </div>
    </div>
  );
}
