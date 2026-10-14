import { describe, expect, it } from "vitest";

import { penangFixture } from "../fixtures/penang";
import { parsePenangResults } from "./parse-penang";

// The fixture, as plain JSON, is a valid file. Each malformed case changes one thing in a copy.
const valid = JSON.parse(JSON.stringify(penangFixture));
const district = valid.districts[0];
const withDistrict = (changes: object) => ({ ...valid, districts: [{ ...district, ...changes }, ...valid.districts.slice(1)] });
const withGeometry = (changes: object) => ({ ...valid, geometry: { ...valid.geometry, ...changes } });

describe("parsePenangResults", () => {
  it("accepts a valid file and returns its data", () => {
    const parsed = parsePenangResults(valid);
    expect(parsed.districts.map((d) => d.id)).toEqual(["tl", "bd", "spu", "spt", "sps"]);
    expect(parsed.districts[4].far).toEqual({ clinic: 21, school: 11, transit: 27 });
    expect(parsed.points).toHaveLength(penangFixture.points.length);
  });

  it.each([
    ["not an object", null, /file must be an object/],
    ["a missing answer", { ...valid, answer: "" }, /answer must be a non-empty string/],
    ["four districts", { ...valid, districts: valid.districts.slice(1) }, /districts must have 5 items/],
    ["districts out of order", { ...valid, districts: [valid.districts[1], valid.districts[0], ...valid.districts.slice(2)] }, /districts\[0\]\.id must be tl/],
    ["bands that do not sum to 100", withDistrict({ bands: [72, 24, 5] }), /districts\[0\]\.bands must sum to 100/],
    ["a fractional band", withDistrict({ bands: [71.5, 24.5, 4] }), /districts\[0\]\.bands\[0\] must be a whole number/],
    ["a missing far value", withDistrict({ far: { clinic: 4, school: 2 } }), /districts\[0\]\.far\.transit/],
    ["a far clinic share that disagrees with the bands", withDistrict({ far: { ...district.far, clinic: 5 } }), /far\.clinic must equal the over 3 km band/],
    ["a population of zero", withDistrict({ population: 0 }), /districts\[0\]\.population/],
    ["no points", { ...valid, points: [] }, /points must have at least one point/],
    ["a point with an unknown category", { ...valid, points: [{ category: "hospital", x: 1, y: 1 }] }, /points\[0\]\.category/],
    ["one bridge", withGeometry({ bridges: valid.geometry.bridges.slice(1) }), /geometry\.bridges must have 2 items/],
    ["five places", withGeometry({ places: valid.geometry.places.slice(1) }), /geometry\.places must have 6 items/],
    ["an island outline that is not a path", withGeometry({ island: "Z" }), /geometry\.island must be an SVG path/],
    ["a district outline on unknown land", withGeometry({ districts: [{ ...valid.geometry.districts[0], land: "sea" }, ...valid.geometry.districts.slice(1)] }), /geometry\.districts\[0\]\.land/],
  ])("rejects %s", (_name, input, message) => {
    expect(() => parsePenangResults(input)).toThrow(message);
  });
});
