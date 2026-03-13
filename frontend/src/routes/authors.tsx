import { createFileRoute } from "@tanstack/react-router";
import { AuthorWorkCountChart } from "@/components/charts/author-work-count-chart";
import { useAuthors } from "@/hooks/use-authors";

export const Route = createFileRoute("/authors")({
  component: Authors,
});

function Authors() {
  const { data, isLoading, error } = useAuthors();
  const items = data?.items ?? [];

  return (
    <div>
      <h1 className="text-3xl font-bold">Author Space</h1>
      <p className="mt-2 text-text-muted">
        Explore author embeddings via t-SNE / UMAP scatter plot.
      </p>

      {isLoading && <p className="mt-8 text-text-muted">Loading…</p>}
      {error && <p className="mt-8 text-red-500">Failed to load authors.</p>}

      {items.length > 0 && (
        <div className="mt-6">
          <AuthorWorkCountChart authors={items} />
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map((a) => (
          <div key={a.author} className="rounded-xl border border-border bg-surface p-6 shadow-sm">
            <h2 className="text-lg font-semibold">{a.author}</h2>
            <p className="mt-1 text-sm text-text-muted">
              {a.work_count} {a.work_count === 1 ? "work" : "works"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
