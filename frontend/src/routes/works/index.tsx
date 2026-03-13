import { createFileRoute, Link } from "@tanstack/react-router";
import { useWorks } from "@/hooks/use-works";

export const Route = createFileRoute("/works/")({
  component: WorkList,
});

interface Work {
  work_id: string;
  title: string;
  author: string;
  genre: string;
  word_count: number;
  sent_count: number;
  chap_count: number;
}

function WorkList() {
  const { data, isLoading, error } = useWorks();
  const items = (data?.items ?? []) as Work[];

  return (
    <div>
      <h1 className="text-3xl font-bold">Works</h1>
      <p className="mt-2 text-text-muted">Browse and search the corpus.</p>

      {isLoading && <p className="mt-8 text-text-muted">Loading…</p>}
      {error && <p className="mt-8 text-red-500">Failed to load works.</p>}

      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {items.map((w) => (
          <Link
            key={w.work_id}
            to="/works/$workId"
            params={{ workId: w.work_id }}
            className="group rounded-xl border border-border bg-surface p-6 shadow-sm transition-colors hover:border-primary"
          >
            <h2 className="text-lg font-semibold group-hover:text-primary">{w.title}</h2>
            <p className="mt-1 text-sm text-text-muted">{w.author}</p>
            <p className="mt-0.5 text-xs text-text-muted">{w.genre}</p>
            <div className="mt-4 flex gap-4 text-xs text-text-muted">
              <span>{w.word_count.toLocaleString()} words</span>
              <span>{w.sent_count.toLocaleString()} sentences</span>
              <span>{w.chap_count} chapters</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
