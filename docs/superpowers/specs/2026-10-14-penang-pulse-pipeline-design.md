# Penang Pulse Real-Results Pipeline

> Date: 2026-10-14. Status: draft for review.
> Design agreed with Subashanan in conversation on 2026-10-14 (road distance; clinics are every general-care site, dental excluded; schools and transit shown in a table). Sources were checked by script on 2026-10-14; checksums below are from that check.
> Implementation plan: `docs/superpowers/plans/2026-10-14-penang-pulse-pipeline.md` (to be written after this spec is approved).

## 1. Purpose

Replace the Penang Pulse illustrative fixture with real, reproducible results, so the production site and the CV show numbers that come from one committed results file. Same honesty rules as the Forecasting Lab: no hand-typed numbers, templated prose, a manifest with checksums.

Success means:

- `uv run pytest` in `analysis/` passes offline in CI, on synthetic fixtures only;
- one local command downloads every source, computes road distances for every populated cell in Penang, and writes `apps/web/src/content/results/penang-pulse.json` and a manifest;
- the production build shows Penang Pulse with those numbers, a to-scale map, and the schools and transit table, and fails if the file is malformed;
- the CV's Penang Pulse bullet quotes numbers read from the same file.

## 2. What this changes

| Earlier plan | Where | Replaced by | Why |
|---|---|---|---|
| Facility layers from PeGIS | Study sources, method | Penang State open data CSVs (clinics, schools) and the Rapid Penang GTFS feed | PeGIS layers are not anonymously queryable and carry no open licence; GeoSebar needs a manual request form |
| Population by mukim, from Census 2020 | Sources, method | WorldPop 2020 constrained 100 m grid, rescaled to DOSM's 2020 district totals | No mukim population or complete mukim boundaries are published |
| Bootstrap over mukims for intervals | Method, key number caveat | Sensitivity check with a second population map (Meta 30 m) | The figures cover every resident rather than a sample, so a bootstrap would overstate precision; the real uncertainty is where people live |
| Schematic map and sampled points | Fixture `pointsNote`, geometry | Real district outlines to scale, every facility used | Real data now exists |
| `uv run python -m analysis.penang.build --from-cache` | Reproduce commands | `uv run python -m pulse.cli`, run from `analysis/` | Matches the workspace layout |

## 3. Scope

In scope: a `pulse` package in the existing `analysis/` uv workspace; a results file in the existing `PenangResults` shape plus one new field; a validator; a schools and transit table on the study page; study record copy; CI; the CV bullet.

Out of scope: travel time or public transport service frequency; private clinics; changing the map, tile or panel design beyond the new table and copy; any other study.

## 4. Data

All downloads are cached under `analysis/data/raw/pulse/` (gitignored). Each file's SHA-256 is recorded in the manifest. A checksum different from the one below is logged, not fatal, for the sources that update in place (GTFS, Geofabrik); for the others it is fatal.

| Source | URL | Checked on 2026-10-14 | Licence |
|---|---|---|---|
| Penang public health facilities 2022 | `https://archive.data.gov.my/data/dataset/20a4c459-5329-450a-8cad-938957f2eefe/resource/95ed70e3-955f-43a8-a99d-072accc49ed0/download/_202310251223490_pusat_kesihatan_awam_2022_p.csv` | 26,373 bytes, SHA-256 `30d7abe1…742f68`, 151 rows | CC BY (portal) |
| Penang schools 2022 | `https://archive.data.gov.my/data/dataset/13d6b29c-2460-4f3e-ba6e-5fb58e407e15/resource/0566082a-6a70-4f2e-9f8c-bd587d2f8cb0/download/_202310251214180_be0010_sekolah_2022_p.csv` | 145,133 bytes, SHA-256 `dc84127b…e734e`, 432 rows | CC BY (portal) |
| Rapid Penang GTFS | `https://api.data.gov.my/gtfs-static/prasarana?category=rapid-bus-penang` (redirects to an S3 zip overwritten in place) | 4,457,025 bytes, SHA-256 `9823a7c7…669c73`, 1,932 stops | CC BY 4.0 (data.gov.my) |
| DOSM population by district | `https://storage.dosm.gov.my/population/population_district.parquet` | 264,746 bytes, SHA-256 `456bca23…024742` | CC BY 4.0 |
| District boundaries | geoBoundaries MYS ADM2 at commit `9469f09592ced973a3448cf66b6100b741b64c0d` (Git LFS media URL) | 1,932,621 bytes, SHA-256 `1a7db3b4…15e550` | CC BY 3.0 |
| Population grid (main) | `https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/MYS/mys_ppp_2020_UNadj_constrained.tif` | 9,789,326 bytes, SHA-256 `b54a9a07…de981c`; EPSG:4326, 3″ (about 100 m) | CC BY 4.0 |
| Population grid (sensitivity) | HDX Meta high-resolution population, `mys_general_2020_geotiff.zip` (HDX resource URL, never the signed S3 redirect) | 42,122,823 bytes, SHA-256 `31317c66…a9250f`; one 17.4 GB uncompressed GeoTIFF, EPSG:4326, 1″ (about 30 m) | CC BY |
| Roads, bridges, town labels | Geofabrik `malaysia-singapore-brunei-YYMMDD.osm.pbf`, a dated daily file chosen at run time and recorded | about 252 MB | ODbL |

Full checksums live in `pulse/sources.py` as constants.

### 4.1 What the files hold

- Health CSV: UTF-8 with BOM. `JENIS` values: KLINIK DESA 60, KLINIK PERGIGIAN 31, KLINIK KESIHATAN 30, KLINIK KOMUNITI 18, HOSPITAL KERAJAAN 6, KLINIK KESIHATAN IBU DAN ANAK 6. `X` is longitude and `Y` latitude (WGS84). `DAERAH` uses codes DTL, DBD, SPU, SPT, SPS. `TARIKH_DATA` dates run from 2013 to 2022.
- Schools CSV: UTF-8 with BOM, same coordinate and district columns. `PERINGKAT` is RENDAH 274, MENENGAH 140, TIADA 18. `JENIS_LABEL` includes SWASTA 32 (private).
- DOSM parquet: `population` is in thousands. The pipeline filters to `state == "Pulau Pinang"`, `date == "2020-01-01"`, `sex == "both"`, `age == "overall"`, `ethnicity == "overall"`. 2020 totals: Barat Daya 237.7, SP Selatan 184.0, SP Tengah 423.0, SP Utara 339.1, Timur Laut 556.6 (thousands).
- geoBoundaries ADM2: `shapeName` matches the DOSM district spellings exactly. There is no state field, so the pipeline selects the 5 names.

## 5. Facilities

- **Clinics:** every row except `JENIS == "KLINIK PERGIGIAN"`, giving 120 general-care sites.
- **Schools:** all 432 rows, as agreed (this includes 32 private schools; the site copy says so).
- **Transit stops:** GTFS `stops.txt` rows whose point lies inside the union of the 5 districts.
- A facility outside every district polygon is kept for distance (a clinic just across a boundary still serves residents) but is logged. A facility row with missing or non-numeric coordinates fails the run.

## 6. Population surface

1. Read the WorldPop raster window covering the Penang districts' bounding box.
2. Keep cells with population above zero whose centre lies inside one of the 5 districts; assign each cell to its district.
3. Rescale each district's cells so they sum to the DOSM 2020 total for that district (`population × 1000`).
4. The sensitivity run repeats steps 1 to 3 with the Meta raster, read in place through GDAL's `/vsizip/` path with a window, so the 17.4 GB file is never extracted.

## 7. Road network and distance

- Parse the Geofabrik PBF with `osmium` (pyosmium), keeping ways inside the Penang bounding box with `highway` in: motorway, trunk, primary, secondary, tertiary, unclassified, residential, living_street, service, road, and the `_link` variants. Ways tagged `access=private` or `access=no` are dropped. Ferries are not roads and are excluded. The two bridges are ordinary motorway and trunk ways and stay in.
- Build an undirected `networkx` graph: nodes are OSM nodes, and edge weights are haversine lengths in metres. Undirected is deliberate, because the study measures distance, not a legal driving route.
- Keep the largest connected component; log how many nodes were dropped.
- Positions use a local equirectangular projection in metres around Penang's centre (error well under 0.1% at this scale), with a `scipy.spatial.cKDTree` for snapping.
- **Distance for a cell to a category:** straight line from the cell centre to its nearest road node, plus the network distance to the nearest facility's road node, plus that facility's straight-line snap. This is implemented as one multi-source Dijkstra per category from a virtual source joined to each facility node by its snap length.
- Bands: under 1,000 m, 1,000 to 3,000 m, over 3,000 m.

## 8. Outputs

### 8.1 Results file

`apps/web/src/content/results/penang-pulse.json`, in the existing `PenangResults` shape, with one addition to `District`:

```ts
far: Readonly<Record<ServiceCategory, number>>; // % of residents over 3 km from the nearest clinic, school and transit stop
```

- `districts`: the 5 districts in a fixed order (Timur Laut, Barat Daya, SP Utara, SP Tengah, SP Selatan) with the existing `id` and `short` values. `bands` are clinic shares rounded by largest remainder so each district sums to exactly 100. `population` is the DOSM 2020 total. `far` holds integers, one per category.
- `points`: every facility used, projected into the map's 600 by 500 view box.
- `geometry`: projected and simplified district outlines.
  - `island` is the union of Timur Laut and Barat Daya; `mainland` is the union of the 3 SP districts.
  - `boundaries` are the shared edges between districts on the same land mass.
  - `bridges` are the Penang Bridge and the Sultan Abdul Halim Muadzam Shah Bridge, taken from OSM ways by name. A missing bridge fails the run.
  - `places` are the six existing town labels, positioned from OSM `place` nodes by name. A missing place fails the run.
  - One projection, fitted to all 5 districts with a margin, keeps the map to scale.
- `pointsNote`: "To scale. Every public clinic (dental excluded), school and Rapid Penang stop used. Dashed lines mark district boundaries."

### 8.2 Prose templates

All text is generated from computed numbers by templates in `pulse/export.py`.

- **Answer:** "In {best}, {p}% of residents live within 1 km of a public clinic by road. In {worst}, {q}% live more than 3 km away." Then one sentence naming, for schools and for transit stops, the district with the largest share over 3 km and that share. `best` is the district with the highest clinic share under 1 km; `worst` is the district with the highest clinic share over 3 km. If the Meta run picks a different `worst`, a third sentence says so.
- **Key numbers:**
  1. `{q}%` "of {worst} residents live more than 3 km by road from a public clinic." Caveat: "{q2}% with Meta's 30 m population map instead of WorldPop."
  2. `{n}` "public clinics, schools and Rapid Penang stops mapped." Caveat: "Dental clinics and private clinics are not included; facility records are dated {first year} to {last year}."
  3. `{r}%` "of Penang residents live within 1 km by road of a Rapid Penang stop." Caveat: "Stops from the GTFS feed retrieved on {date}; distance says nothing about how often buses run."
- Numbers in prose are integers; a share that rounds to 0 is written as "under 1%".

### 8.3 Manifest

`analysis/outputs/penang-pulse-manifest.json` holds:

- every source URL, retrieval timestamp, byte size and SHA-256, and the Geofabrik file date;
- facility counts per category and the date range;
- road graph size, and the nodes dropped outside the largest component;
- cell counts per district;
- the full band shares per district and category for both population maps, to one decimal place;
- package versions and the git commit and dirty flag.

## 9. Website changes

- `types.ts`: add `far` to `District`.
- `content/fixtures/penang.ts`: add illustrative `far` values; the fixture stays dev-only.
- New `parsePenangResults(json: unknown): PenangResults`, a hand-written type guard with tests for one valid file and several malformed ones. `content/results/index.ts` sets `published["penang-pulse"]` from the validated JSON.
- New `ServiceTable` component under the district panel. It has rows for the 5 districts and columns for clinic, school and transit stop, showing the % over 3 km. The selected district's row is highlighted, and it uses a real `<table>` with a caption. Rows keep the fixed district order, with no sorting.
- `penang-figure.tsx` caption: "Shares are of residents, by road distance from each populated 100 m cell." This replaces the mukim centroid wording.
- `studies.ts`: status published.
  - Sources: the state open data CSVs, GTFS, DOSM, geoBoundaries, WorldPop, Meta and OpenStreetMap, each with its licence.
  - Method and limitations rewritten from sections 5 to 7.
  - Reproduce: `uv sync`, `uv run python -m pulse.cli`.
  - Limitations:
    - facility records are dated 2013 to 2022 and come from a legacy portal;
    - private clinics are not included, and 32 private schools are;
    - population is modelled at 100 m, not counted;
    - road distance is not travel time and ignores bus frequency;
    - roads are treated as two-way.

## 10. CI

The `analysis` job is unchanged in shape. The new dependencies install from wheels: `rasterio`, `shapely`, `networkx`, `osmium`, `pyarrow`. Tests build their fixtures in a temporary directory:

- a 6 by 6 GeoTIFF;
- a small `.osm` XML road grid with two named bridge ways and place nodes;
- two square districts;
- tiny CSVs and a GTFS zip.

## 11. CV

The final task extends `tools/update_cv.py` to replace the "In progress:" Penang Pulse bullet with templated wording read from `penang-pulse.json`, for example: "Road distance from every populated 100 m cell in Penang to the nearest public clinic, school and bus stop; {q}% of {worst} residents live over 3 km from a clinic." The fallback wordings must fit the bullet's existing lines. Both PDFs are rendered and checked, and only the web copy is committed.

## 12. Error handling

- **Fail the run on:**
  - a checksum mismatch for a fixed source;
  - a missing district, bridge or place;
  - a facility with bad coordinates;
  - a district with zero populated cells;
  - a cell whose distance cannot be computed after component filtering. Such a cell is snapped to the largest component, so this should not happen; if it does, it is a bug.
- **Log and continue:** facilities outside every district, nodes dropped from small components, GTFS or Geofabrik checksum drift.
- Progress uses stdlib `logging`, as in `forecasting.cli`.

## 13. Testing

- **Unit:**
  - band rounding sums to 100;
  - distance equals snap plus network plus snap on a hand-made graph;
  - a facility on the far side of a "bridge" is reached only over the bridge;
  - district rescaling hits the totals exactly;
  - the projection keeps the aspect ratio;
  - the templates handle ties and an under-1% share.
- **Integration:** run the pipeline end to end on the synthetic fixtures and validate the output with the same rules as the TypeScript validator (shape checks mirrored in a Python test).
- **Web:**
  - `parsePenangResults` accepts a valid file and rejects malformed ones;
  - `ServiceTable` renders 5 rows and 3 columns and highlights the selected district;
  - existing Penang figure tests still pass.

## 14. Decisions this spec makes that the conversation did not

1. WorldPop's constrained UN-adjusted 2020 grid is the main surface, rather than the unconstrained one: it puts people only in built-up cells, and its 9.8 MB download is reliable where the 190 MB file is not.
2. Geofabrik PBF instead of Overpass, because live Overpass counts varied between runs.
3. pyosmium plus networkx instead of OSMnx, because OSMnx cannot read a PBF; this keeps the graph build to about 60 lines and avoids geopandas.
4. Roads are undirected, and footpaths are excluded.
5. Schools include the 32 private schools, per the agreed "all 432"; this can be flipped to public only by filtering `JENIS_LABEL != "SWASTA"`.

## 15. Build order (outline for the plan)

1. Site: `far` field, fixture, `ServiceTable`, caption.
2. Site: `parsePenangResults` and its tests.
3. Analysis: dependencies, `pulse/sources.py` fetch and checksums, loaders for the CSVs, GTFS, parquet and boundaries.
4. Analysis: population surface (WorldPop, rescale; Meta via `/vsizip/`).
5. Analysis: PBF road graph, bridges and places.
6. Analysis: snapping and multi-source distances, bands.
7. Analysis: geometry projection and simplification for the map.
8. Analysis: export templates, manifest, CLI with progress logging.
9. Run locally, commit the results file and manifest, publish on the site and update the study record.
10. CV bullet, then final checks and the PR.
