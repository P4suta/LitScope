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

async function renderChart(works: Array<{ genre: string }>) {
  const { GenreDistributionChart } = await import("./genre-distribution-chart");
  return render(<GenreDistributionChart works={works} />);
}

describe("GenreDistributionChart", () => {
  it("shows 'No data' for empty array", async () => {
    await renderChart([]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders chart for non-empty data", async () => {
    const { container } = await renderChart([
      { genre: "Fiction" },
      { genre: "Fiction" },
      { genre: "Poetry" },
    ]);
    expect(container.querySelector("figure")).toBeInTheDocument();
  });
});
