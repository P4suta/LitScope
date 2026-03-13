import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@observablehq/plot", () => ({
  plot: vi.fn(() => {
    const figure = document.createElement("figure");
    figure.append(document.createElementNS("http://www.w3.org/2000/svg", "svg"));
    return figure;
  }),
  barX: vi.fn(() => ({})),
  ruleX: vi.fn(() => ({})),
}));

async function renderChart(authors: Array<{ author: string; work_count: number }>) {
  const { AuthorWorkCountChart } = await import("./author-work-count-chart");
  return render(<AuthorWorkCountChart authors={authors} />);
}

describe("AuthorWorkCountChart", () => {
  it("shows 'No data' for empty array", async () => {
    await renderChart([]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders chart for non-empty data", async () => {
    const { container } = await renderChart([
      { author: "Dickens", work_count: 5 },
      { author: "Austen", work_count: 3 },
    ]);
    expect(container.querySelector("figure")).toBeInTheDocument();
  });
});
