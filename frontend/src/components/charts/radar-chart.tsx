import * as d3 from "d3";
import { useEffect, useRef } from "react";

interface RadarChartProps {
  items: Array<{ label: string; values: Record<string, number | null> }>;
  metrics: string[];
  "aria-label"?: string;
}

const COLORS = ["steelblue", "#e45756", "#54a24b", "#f58518", "#b279a2"];

export function RadarChart({
  items,
  metrics,
  "aria-label": ariaLabel = "Radar chart",
}: RadarChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || items.length === 0 || metrics.length === 0) return;

    const width = 400;
    const height = 400;
    const margin = 60;
    const radius = Math.min(width, height) / 2 - margin;
    const angleSlice = (2 * Math.PI) / metrics.length;

    // Normalize values to [0, 1]
    const ranges = metrics.map((m) => {
      const vals = items.map((item) => item.values[m]).filter((v): v is number => v != null);
      const min = vals.length > 0 ? Math.min(...vals) : 0;
      const max = vals.length > 0 ? Math.max(...vals) : 1;
      return { min, max: max === min ? max + 1 : max };
    });

    const normalize = (value: number | null, i: number) => {
      const range = ranges[i];
      return value != null && range ? (value - range.min) / (range.max - range.min) : 0;
    };

    const svg = d3
      .select(container)
      .append("svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("role", "img")
      .attr("aria-label", ariaLabel)
      .append("g")
      .attr("transform", `translate(${width / 2},${height / 2})`);

    // Grid circles
    const levels = 5;
    for (let level = 1; level <= levels; level++) {
      svg
        .append("circle")
        .attr("r", (radius / levels) * level)
        .attr("fill", "none")
        .attr("stroke", "#ddd")
        .attr("stroke-dasharray", "2,2");
    }

    // Axes
    for (let i = 0; i < metrics.length; i++) {
      const angle = angleSlice * i - Math.PI / 2;
      svg
        .append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", radius * Math.cos(angle))
        .attr("y2", radius * Math.sin(angle))
        .attr("stroke", "#ddd");

      svg
        .append("text")
        .attr("x", (radius + 15) * Math.cos(angle))
        .attr("y", (radius + 15) * Math.sin(angle))
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .attr("font-size", "10px")
        .text(metrics[i]?.split(".").at(-1) ?? "");
    }

    // Polygons
    const lineRadial = d3
      .lineRadial<number>()
      .angle((_, i) => angleSlice * i - Math.PI / 2)
      .radius((d) => d * radius)
      .curve(d3.curveLinearClosed);

    for (let idx = 0; idx < items.length; idx++) {
      const item = items[idx]!;
      const color = COLORS[idx % COLORS.length]!;
      const values = metrics.map((m, i) => normalize(item.values[m] ?? null, i));
      svg
        .append("path")
        .datum(values)
        .attr("d", lineRadial)
        .attr("fill", color)
        .attr("fill-opacity", 0.15)
        .attr("stroke", color)
        .attr("stroke-width", 2)
        .attr("class", "radar-polygon");
    }

    // Legend
    const legend = svg
      .append("g")
      .attr("transform", `translate(${-width / 2 + 10},${height / 2 - 20 * items.length})`);
    for (let idx = 0; idx < items.length; idx++) {
      const g = legend.append("g").attr("transform", `translate(0,${idx * 18})`);
      g.append("rect")
        .attr("width", 12)
        .attr("height", 12)
        .attr("fill", COLORS[idx % COLORS.length]!);
      g.append("text")
        .attr("x", 16)
        .attr("y", 10)
        .attr("font-size", "11px")
        .text(items[idx]!.label);
    }

    return () => {
      container.innerHTML = "";
    };
  }, [items, metrics, ariaLabel]);

  return items.length === 0 ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <div ref={containerRef} className="max-w-md mx-auto w-full" />
  );
}
