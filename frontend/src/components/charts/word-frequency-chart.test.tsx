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

async function renderChart(words: Array<{ lemma: string; count: number }>) {
  const { WordFrequencyChart } = await import("./word-frequency-chart");
  return render(<WordFrequencyChart words={words} />);
}

describe("WordFrequencyChart", () => {
  it("shows 'No data' for empty array", async () => {
    await renderChart([]);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders chart for non-empty data", async () => {
    const { container } = await renderChart([
      { lemma: "the", count: 100 },
      { lemma: "cat", count: 50 },
    ]);
    expect(container.querySelector("figure")).toBeInTheDocument();
    expect(screen.queryByText("No data")).not.toBeInTheDocument();
  });
});
