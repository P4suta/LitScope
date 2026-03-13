import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

vi.mock("@/hooks/use-timeline", () => ({
  useTimeline: vi.fn(),
}));

vi.mock("@/components/charts/timeline-chart", () => ({
  TimelineChart: ({ points }: { points: unknown[] }) => (
    <div data-testid="timeline-chart">{points.length} points</div>
  ),
}));

async function getUseTimeline() {
  const mod = await import("@/hooks/use-timeline");
  return mod.useTimeline as ReturnType<typeof vi.fn>;
}

async function renderTimeline() {
  const mod = await import("./timeline");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

describe("Timeline route", () => {
  it("renders heading and timeline chart when data is available", async () => {
    const useTimeline = await getUseTimeline();
    useTimeline.mockReturnValue({
      data: {
        points: [
          {
            pub_year: 1920,
            work_id: "1",
            title: "A",
            ttr: 0.5,
            mtld: 45,
            hapax_ratio: 0.3,
            unique_lemmas: 100,
          },
        ],
      },
      isLoading: false,
      error: null,
    });

    await renderTimeline();

    expect(screen.getByRole("heading", { name: "Timeline" })).toBeInTheDocument();
    expect(screen.getByTestId("timeline-chart")).toBeInTheDocument();
  });

  it("renders loading state", async () => {
    const useTimeline = await getUseTimeline();
    useTimeline.mockReturnValue({ data: undefined, isLoading: true, error: null });

    await renderTimeline();

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders error state", async () => {
    const useTimeline = await getUseTimeline();
    useTimeline.mockReturnValue({ data: undefined, isLoading: false, error: new Error("fail") });

    await renderTimeline();

    expect(screen.getByText("Failed to load timeline.")).toBeInTheDocument();
  });

  it("renders empty state", async () => {
    const useTimeline = await getUseTimeline();
    useTimeline.mockReturnValue({ data: { points: [] }, isLoading: false, error: null });

    await renderTimeline();

    expect(screen.getByText("No timeline data available.")).toBeInTheDocument();
  });

  it("hides chart when data is undefined", async () => {
    const useTimeline = await getUseTimeline();
    useTimeline.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderTimeline();

    expect(screen.queryByTestId("timeline-chart")).not.toBeInTheDocument();
    expect(screen.queryByText("No timeline data available.")).not.toBeInTheDocument();
  });
});
