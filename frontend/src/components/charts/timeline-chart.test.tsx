import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@observablehq/plot", () => ({
  plot: vi.fn(() => {
    const figure = document.createElement("figure");
    figure.append(document.createElementNS("http://www.w3.org/2000/svg", "svg"));
    return figure;
  }),
  dot: vi.fn(() => ({})),
  text: vi.fn(() => ({})),
}));

const points: Array<{ pub_year: number; title: string; ttr: number | null }> = [
  { pub_year: 1920, title: "Book A", ttr: 0.5 },
  { pub_year: 1930, title: "Book B", ttr: 0.6 },
];

async function renderChart(data = points) {
  const { TimelineChart } = await import("./timeline-chart");
  return render(<TimelineChart points={data} />);
}

describe("TimelineChart", () => {
  it("shows 'No data' when all ttr values are null", async () => {
    await renderChart([{ pub_year: 1920, title: "A", ttr: null }]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("shows 'No data' for empty array", async () => {
    await renderChart([]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders chart when data has non-null ttr", async () => {
    const { container } = await renderChart();
    expect(container.querySelector("figure")).toBeInTheDocument();
  });
});
