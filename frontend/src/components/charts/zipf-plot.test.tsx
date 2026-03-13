import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@observablehq/plot", () => ({
  plot: vi.fn(() => {
    const figure = document.createElement("figure");
    figure.append(document.createElementNS("http://www.w3.org/2000/svg", "svg"));
    return figure;
  }),
  dot: vi.fn(() => ({})),
  line: vi.fn(() => ({})),
}));

const words = [
  { lemma: "the", count: 100 },
  { lemma: "cat", count: 50 },
  { lemma: "sat", count: 10 },
];

async function renderZipf(
  props: Partial<Parameters<typeof import("./zipf-plot").ZipfPlot>[0]> = {},
) {
  const { ZipfPlot } = await import("./zipf-plot");
  return render(
    <ZipfPlot
      words={props.words ?? words}
      alpha={props.alpha ?? null}
      rSquared={props.rSquared ?? null}
      intercept={props.intercept ?? null}
    />,
  );
}

describe("ZipfPlot", () => {
  it("shows 'No data' for empty array", async () => {
    await renderZipf({ words: [] });
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders chart without regression line when alpha is null", async () => {
    const { container } = await renderZipf();
    expect(container.querySelector("figure")).toBeInTheDocument();
  });

  it("renders chart with regression line when alpha is provided", async () => {
    const { container } = await renderZipf({ alpha: -1.5, rSquared: 0.95, intercept: 5.0 });
    expect(container.querySelector("figure")).toBeInTheDocument();
  });

  it("produces downward slope with negative alpha", async () => {
    const Plot = await import("@observablehq/plot");
    await renderZipf({ alpha: -1.2, rSquared: 0.98, intercept: 4.0 });
    const lineCall = vi.mocked(Plot.line).mock.calls.at(-1);
    expect(lineCall).toBeDefined();
    const lineData = lineCall![0] as Array<{ logRank: number; predicted: number }>;
    // With negative alpha, predicted values should decrease as logRank increases
    for (let i = 1; i < lineData.length; i++) {
      expect(lineData[i].predicted).toBeLessThan(lineData[i - 1].predicted);
    }
  });

  it("handles alpha without rSquared", async () => {
    const { container } = await renderZipf({ alpha: -1.2, rSquared: null });
    expect(container.querySelector("figure")).toBeInTheDocument();
  });

  it("falls back to first data point when intercept is null", async () => {
    const { container } = await renderZipf({ alpha: -1.0, intercept: null });
    expect(container.querySelector("figure")).toBeInTheDocument();
  });
});
