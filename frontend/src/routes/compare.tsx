import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/compare")({
  component: Compare,
});

function Compare() {
  return (
    <div>
      <h1 className="text-3xl font-bold">Compare</h1>
      <p className="mt-2 text-text-muted">Select up to 5 works for side-by-side comparison.</p>
    </div>
  );
}
