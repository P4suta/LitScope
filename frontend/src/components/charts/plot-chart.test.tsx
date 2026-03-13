import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mockPlot = vi.fn(() => {
  const figure = document.createElement("figure");
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  figure.append(svg);
  return figure;
});

vi.mock("@observablehq/plot", () => ({ plot: mockPlot }));

afterEach(() => {
  cleanup();
});

async function renderPlotChart(props: Parameters<typeof import("./plot-chart").PlotChart>[0]) {
  const { PlotChart } = await import("./plot-chart");
  return render(<PlotChart {...props} />);
}

describe("PlotChart", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("mounts a figure with accessible svg", async () => {
    const { container } = await renderPlotChart({
      options: { marks: [] },
      "aria-label": "Test chart",
    });

    const figure = container.querySelector("figure");
    expect(figure).toBeInTheDocument();
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toBe("Test chart");
  });

  it("removes figure on unmount", async () => {
    const { container, unmount } = await renderPlotChart({
      options: { marks: [] },
      "aria-label": "Chart",
    });

    expect(container.querySelector("figure")).toBeInTheDocument();
    unmount();
    expect(container.querySelector("figure")).not.toBeInTheDocument();
  });

  it("replaces figure when options change", async () => {
    const { PlotChart } = await import("./plot-chart");
    const { rerender, container } = render(<PlotChart options={{ marks: [] }} aria-label="V1" />);

    expect(container.querySelector("svg")?.getAttribute("aria-label")).toBe("V1");

    rerender(<PlotChart options={{ marks: [], width: 500 }} aria-label="V2" />);

    expect(container.querySelector("svg")?.getAttribute("aria-label")).toBe("V2");
  });

  it("applies className to container div", async () => {
    const { container } = await renderPlotChart({
      options: { marks: [] },
      "aria-label": "Chart",
      className: "my-chart",
    });

    expect(container.firstElementChild?.classList.contains("my-chart")).toBe(true);
  });
});
