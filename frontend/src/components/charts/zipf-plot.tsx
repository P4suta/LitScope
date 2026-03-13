import * as Plot from "@observablehq/plot";
import { useMemo } from "react";
import { PlotChart } from "./plot-chart";

interface ZipfPlotProps {
  words: Array<{ lemma: string; count: number }>;
  alpha: number | null;
  rSquared: number | null;
  intercept: number | null;
}

export function ZipfPlot({ words, alpha, rSquared, intercept }: ZipfPlotProps) {
  const options = useMemo((): Plot.PlotOptions => {
    const ranked = words
      .toSorted((a, b) => b.count - a.count)
      .map((w, i) => ({
        ...w,
        rank: i + 1,
        logRank: Math.log(i + 1),
        logCount: Math.log(w.count),
      }));

    const marks: Plot.Markish[] = [
      Plot.dot(ranked, {
        x: "logRank",
        y: "logCount",
        fill: "var(--color-primary, steelblue)",
        r: 3,
      }),
    ];

    if (alpha != null && ranked.length > 0) {
      const yIntercept = intercept ?? ranked[0].logCount;
      const line = ranked.map((d) => ({
        logRank: d.logRank,
        predicted: yIntercept + alpha * d.logRank,
      }));
      marks.push(
        Plot.line(line, {
          x: "logRank",
          y: "predicted",
          stroke: "var(--color-red, red)",
          strokeDasharray: "4,4",
        }),
      );
    }

    return {
      x: { label: "ln(rank)" },
      y: { label: "ln(frequency)" },
      marks,
    };
  }, [words, alpha, intercept]);

  const label =
    alpha != null
      ? `Zipf plot (α=${alpha.toFixed(2)}${rSquared != null ? `, R²=${rSquared.toFixed(3)}` : ""})`
      : "Zipf plot";

  return words.length === 0 ? (
    <p className="text-text-muted">No data</p>
  ) : (
    <PlotChart options={options} aria-label={label} />
  );
}
