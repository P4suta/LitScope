import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/authors")({
  component: Authors,
});

function Authors() {
  return (
    <div>
      <h1 className="text-3xl font-bold">Author Space</h1>
      <p className="mt-2 text-text-muted">
        Explore author embeddings via t-SNE / UMAP scatter plot.
      </p>
    </div>
  );
}
