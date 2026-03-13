import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

vi.mock("@/hooks/use-topics", () => ({
  useTopics: vi.fn(),
}));

async function getUseTopics() {
  const mod = await import("@/hooks/use-topics");
  return mod.useTopics as ReturnType<typeof vi.fn>;
}

async function renderTopics() {
  const mod = await import("./topics");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

describe("Topics route", () => {
  it("renders heading and topic cards with keywords", async () => {
    const useTopics = await getUseTopics();
    useTopics.mockReturnValue({
      data: [
        {
          topic_id: 0,
          label: "Test Title",
          work_id: "1",
          keywords: [
            { lemma: "love", score: 0.9 },
            { lemma: "heart", score: 0.7 },
          ],
        },
      ],
      isLoading: false,
      error: null,
    });

    await renderTopics();

    expect(screen.getByRole("heading", { name: "Topics" })).toBeInTheDocument();
    expect(screen.getByText("Test Title")).toBeInTheDocument();
    expect(screen.getByText("love")).toBeInTheDocument();
    expect(screen.getByText("heart")).toBeInTheDocument();
  });

  it("renders loading state", async () => {
    const useTopics = await getUseTopics();
    useTopics.mockReturnValue({ data: undefined, isLoading: true, error: null });

    await renderTopics();

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders error state", async () => {
    const useTopics = await getUseTopics();
    useTopics.mockReturnValue({ data: undefined, isLoading: false, error: new Error("fail") });

    await renderTopics();

    expect(screen.getByText("Failed to load topics.")).toBeInTheDocument();
  });

  it("renders empty state", async () => {
    const useTopics = await getUseTopics();
    useTopics.mockReturnValue({ data: [], isLoading: false, error: null });

    await renderTopics();

    expect(screen.getByText("No topics available.")).toBeInTheDocument();
  });
});
