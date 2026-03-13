import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@observablehq/plot", () => ({
  plot: vi.fn(() => {
    const figure = document.createElement("figure");
    figure.append(document.createElementNS("http://www.w3.org/2000/svg", "svg"));
    return figure;
  }),
  barX: vi.fn(() => ({})),
  text: vi.fn(() => ({})),
  ruleX: vi.fn(() => ({})),
}));

const distribution = [
  { pos: "NOUN", count: 500, ratio: 0.25 },
  { pos: "VERB", count: 300, ratio: 0.15 },
];

async function renderChart(data = distribution) {
  const { POSDistributionChart } = await import("./pos-distribution-chart");
  return render(<POSDistributionChart distribution={data} />);
}

describe("POSDistributionChart", () => {
  it("shows 'No data' for empty array", async () => {
    await renderChart([]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders chart for non-empty data", async () => {
    const { container } = await renderChart();
    expect(container.querySelector("figure")).toBeInTheDocument();
    expect(screen.queryByText("No data")).not.toBeInTheDocument();
  });
});
