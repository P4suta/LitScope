import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RadarChart } from "./radar-chart";

const items = [
  { label: "Work A", values: { ttr: 0.5, mtld: 80 } },
  { label: "Work B", values: { ttr: 0.6, mtld: 90 } },
];
const metrics = ["ttr", "mtld"];

describe("RadarChart", () => {
  it("renders SVG with aria-label", () => {
    const { container } = render(
      <RadarChart items={items} metrics={metrics} aria-label="Comparison radar" />,
    );
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg?.getAttribute("aria-label")).toBe("Comparison radar");
  });

  it("renders one polygon path per item", () => {
    const { container } = render(<RadarChart items={items} metrics={metrics} />);
    const paths = container.querySelectorAll(".radar-polygon");
    expect(paths.length).toBe(2);
  });

  it("shows 'No data' for empty items", () => {
    render(<RadarChart items={[]} metrics={metrics} />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("handles null metric values", () => {
    const { container } = render(
      <RadarChart items={[{ label: "X", values: { ttr: 0.5, mtld: null } }]} metrics={metrics} />,
    );
    expect(container.querySelector(".radar-polygon")).toBeInTheDocument();
  });

  it("handles single item with identical min/max", () => {
    const { container } = render(
      <RadarChart items={[{ label: "A", values: { ttr: 0.5 } }]} metrics={["ttr"]} />,
    );
    expect(container.querySelector(".radar-polygon")).toBeInTheDocument();
  });

  it("handles empty metrics", () => {
    const { container } = render(<RadarChart items={items} metrics={[]} />);
    expect(container.querySelector("svg")).not.toBeInTheDocument();
  });
});
