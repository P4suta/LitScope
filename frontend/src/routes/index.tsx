import { createFileRoute } from "@tanstack/react-router";
import { GenreDistributionChart } from "@/components/charts/genre-distribution-chart";
import { Section } from "@/components/ui/section";
import { StatCard } from "@/components/ui/stat";
import { useStatus } from "@/hooks/use-status";
import { useWorks } from "@/hooks/use-works";

export const Route = createFileRoute("/")({
  component: Dashboard,
});

function Dashboard() {
  const { data: status } = useStatus();
  const { data: works } = useWorks();

  const items = (works as { items?: Array<{ author: string; genre: string }> } | undefined)?.items;
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
          <Section title="Genre Distribution" sectionKey="genre_distribution">
            <GenreDistributionChart works={items} />
          </Section>
        </div>
      )}
    </div>
  );
}
