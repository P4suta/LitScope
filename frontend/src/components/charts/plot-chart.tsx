import * as Plot from "@observablehq/plot";
import { useEffect, useRef, useState } from "react";

interface PlotChartProps {
  options: Plot.PlotOptions;
  className?: string;
  "aria-label": string;
}

export function PlotChart({ options, className, "aria-label": ariaLabel }: PlotChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState<number | undefined>(undefined);

  useEffect(() => {
    const container = containerRef.current;
    /* v8 ignore next */
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setWidth(Math.floor(entry.contentRect.width));
    });
    observer.observe(container);

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    /* v8 ignore next */
    if (!container) return;

    const figure = Plot.plot({ ...options, ...(width ? { width } : {}) });
    const svg = figure.querySelector("svg");
    if (svg) {
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", ariaLabel);
    }
    container.append(figure);

    return () => {
      figure.remove();
    };
  }, [options, ariaLabel, width]);

  return <div ref={containerRef} className={`w-full ${className ?? ""}`.trim()} />;
}
