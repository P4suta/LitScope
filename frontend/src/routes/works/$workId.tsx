import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/works/$workId")({
  component: WorkDetail,
});

function WorkDetail() {
  const { workId } = Route.useParams();

  return (
    <div>
      <h1 className="text-3xl font-bold">Work Detail</h1>
      <p className="mt-2 text-text-muted">Viewing work: {workId}</p>
    </div>
  );
}
