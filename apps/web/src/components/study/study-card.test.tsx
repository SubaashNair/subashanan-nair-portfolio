import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { findStudy } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

import { StudyCard } from "./study-card";

const pulse = findStudy("penang-pulse")!;

describe("StudyCard", () => {
  it("shows a visible preview label above the key number in a preview", () => {
    const { container } = render(<StudyCard study={pulse} results={getStudyResults("penang-pulse", "development")} headingLevel={3} />);
    const flag = screen.getByText("Illustrative preview");
    expect(flag).toHaveClass("preview-flag");
    expect(flag).not.toHaveClass("sr");
    const key = container.querySelector(".key")!;
    expect(flag.compareDocumentPosition(key.querySelector("strong")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("shows a pending line and no key number without results", () => {
    const { container } = render(<StudyCard study={pulse} results={null} headingLevel={3} />);
    expect(container.querySelector(".key.pending")).toHaveTextContent("Results appear here once the analysis is published.");
    expect(container.querySelector(".key strong")).toBeNull();
    expect(screen.queryByText("Illustrative preview")).not.toBeInTheDocument();
  });
});
