import { createFileRoute } from "@tanstack/react-router";
import { GenreDistributionChart } from "@/components/charts/genre-distribution-chart";
import { useStatus } from "@/hooks/use-status";
import { useWorks } from "@/hooks/use-works";

export const Route = createFileRoute("/")({
  component: Dashboard,
});

function Dashboard() {
  const { data: status } = useStatus();
  const { data: works } = useWorks();

  const items = works?.items as Array<{ author: string; genre: string }> | undefined;
  const authorCount = items ? new Set(items.map((w) => w.author)).size : undefined;
  const genreCount = items ? new Set(items.map((w) => w.genre)).size : undefined;

  const fmt = (v: number | undefined) => (v != null ? v.toLocaleString() : "—");

  return (
    <div>
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <p className="mt-2 text-text-muted">
        Corpus overview — total works, word counts, authors, and genre distribution.
      </p>
      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Works" value={fmt(status?.works)} />
        <StatCard label="Total Words" value={fmt(status?.tokens)} />
        <StatCard label="Authors" value={fmt(authorCount)} />
        <StatCard label="Genres" value={fmt(genreCount)} />
      </div>
      {items && items.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-4 text-xl font-semibold">Genre Distribution</h2>
          <GenreDistributionChart works={items} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <p className="text-sm text-text-muted">{label}</p>
      <p className="mt-1 text-3xl font-semibold">{value}</p>
    </div>
  );
}
