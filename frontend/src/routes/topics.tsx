import { createFileRoute } from "@tanstack/react-router";
import { useTopics } from "@/hooks/use-topics";
import { SECTION_GLOSSARY } from "@/lib/metric-glossary";

export const Route = createFileRoute("/topics")({
  component: Topics,
});

function Topics() {
  const { data: topics, isLoading, error } = useTopics();

  return (
    <div>
      <h1 className="text-3xl font-bold">Topics</h1>
      <p className="mt-2 text-text-muted">{SECTION_GLOSSARY.topics?.description}</p>

      {isLoading && <p className="mt-8 text-text-muted">Loading…</p>}
      {error && <p className="mt-8 text-red-500">Failed to load topics.</p>}

      {topics && topics.length === 0 && (
        <p className="mt-8 text-text-muted">No topics available.</p>
      )}

      {topics && topics.length > 0 && (
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {topics.map((t) => (
            <div
              key={t.work_id}
              className="rounded-xl border border-border bg-surface p-6 shadow-sm"
            >
              <h2 className="text-lg font-semibold">{t.label}</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {t.keywords.map((kw) => (
                  <span
                    key={kw.lemma}
                    className="inline-block rounded-full bg-primary/10 px-3 py-1 text-primary"
                    style={{ fontSize: `${Math.max(0.75, Math.min(1.5, kw.score * 1.5))}rem` }}
                  >
                    {kw.lemma}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
