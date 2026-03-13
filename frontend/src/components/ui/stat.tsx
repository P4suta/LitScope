import { InfoTooltip } from "@/components/ui/info-tooltip";
import { METRIC_GLOSSARY } from "@/lib/metric-glossary";

export function Stat({
  label,
  value,
  metricKey,
}: {
  label: string;
  value: string | number | undefined;
  metricKey?: string;
}) {
  const explanation = metricKey ? METRIC_GLOSSARY[metricKey] : undefined;

  return (
    <div>
      <p className="text-xs text-text-muted">
        {label}
        {explanation && <InfoTooltip label={explanation.short} interpret={explanation.interpret} />}
      </p>
      <p className="text-lg font-semibold">{value ?? "—"}</p>
    </div>
  );
}

export function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <p className="text-sm text-text-muted">{label}</p>
      <p className="mt-1 text-3xl font-semibold">{value}</p>
    </div>
  );
}
