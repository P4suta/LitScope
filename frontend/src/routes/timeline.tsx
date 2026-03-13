import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/timeline")({
  component: Timeline,
});

function Timeline() {
  return (
    <div>
      <h1 className="text-3xl font-bold">Timeline</h1>
      <p className="mt-2 text-text-muted">Vocabulary evolution across publication years.</p>
    </div>
  );
}
