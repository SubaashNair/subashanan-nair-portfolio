import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { penangFixture } from "@/content/fixtures/penang";

import { ServiceTable } from "./service-table";

describe("ServiceTable", () => {
  it("has a caption, five district rows and three service columns", () => {
    render(<ServiceTable districts={penangFixture.districts} selected="sps" />);
    const table = screen.getByRole("table", { name: /more than 3 km by road from the nearest service/i });
    const [head, ...rows] = within(table).getAllByRole("row");
    expect(within(head).getAllByRole("columnheader").map((c) => c.textContent)).toEqual(["District", "Clinic", "School", "Transit stop"]);
    expect(rows.map((r) => within(r).getByRole("rowheader").textContent)).toEqual(["Timur Laut", "Barat Daya", "SP Utara", "SP Tengah", "SP Selatan"]);
    expect(within(rows[4]).getAllByRole("cell").map((c) => c.textContent)).toEqual(["21%", "11%", "27%"]);
  });

  it("highlights only the selected district", () => {
    const { container } = render(<ServiceTable districts={penangFixture.districts} selected="bd" />);
    const marked = container.querySelectorAll("tbody tr.on");
    expect(marked).toHaveLength(1);
    expect(marked[0]).toHaveAttribute("aria-current", "true");
    expect(within(marked[0] as HTMLElement).getByRole("rowheader")).toHaveTextContent("Barat Daya");
  });
});
