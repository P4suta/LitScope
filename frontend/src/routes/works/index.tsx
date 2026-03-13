import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/works/")({
  component: WorkList,
});

function WorkList() {
  return (
    <div>
      <h1 className="text-3xl font-bold">Works</h1>
      <p className="mt-2 text-text-muted">Browse and search the corpus.</p>
    </div>
  );
}
