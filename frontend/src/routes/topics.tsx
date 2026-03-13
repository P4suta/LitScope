import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/topics")({
  component: Topics,
});

function Topics() {
  return (
    <div>
      <h1 className="text-3xl font-bold">Topics</h1>
      <p className="mt-2 text-text-muted">Explore topic clusters and their associated works.</p>
    </div>
  );
}
