import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

vi.mock("@/hooks/use-authors", () => ({
  useAuthors: vi.fn(),
}));

vi.mock("@/components/charts/author-work-count-chart", () => ({
  AuthorWorkCountChart: ({ authors }: { authors: unknown[] }) => (
    <div data-testid="author-chart">{authors.length} authors</div>
  ),
}));

async function getUseAuthors() {
  const mod = await import("@/hooks/use-authors");
  return mod.useAuthors as ReturnType<typeof vi.fn>;
}

async function renderAuthors() {
  const mod = await import("./authors");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

describe("Authors route", () => {
  it("renders heading, author cards, and chart", async () => {
    const useAuthors = await getUseAuthors();
    useAuthors.mockReturnValue({
      data: {
        items: [
          { author: "Dickens", work_count: 5 },
          { author: "Austen", work_count: 1 },
        ],
      },
      isLoading: false,
      error: null,
    });

    await renderAuthors();

    expect(screen.getByRole("heading", { name: "Author Space" })).toBeInTheDocument();
    expect(screen.getByText("Dickens")).toBeInTheDocument();
    expect(screen.getByText("5 works")).toBeInTheDocument();
    expect(screen.getByText("Austen")).toBeInTheDocument();
    expect(screen.getByText("1 work")).toBeInTheDocument();
    expect(screen.getByTestId("author-chart")).toBeInTheDocument();
  });

  it("renders loading state", async () => {
    const useAuthors = await getUseAuthors();
    useAuthors.mockReturnValue({ data: undefined, isLoading: true, error: null });

    await renderAuthors();

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders error state", async () => {
    const useAuthors = await getUseAuthors();
    useAuthors.mockReturnValue({ data: undefined, isLoading: false, error: new Error("fail") });

    await renderAuthors();

    expect(screen.getByText("Failed to load authors.")).toBeInTheDocument();
  });

  it("renders empty list when items is undefined", async () => {
    const useAuthors = await getUseAuthors();
    useAuthors.mockReturnValue({ data: { items: undefined }, isLoading: false, error: null });

    await renderAuthors();

    expect(screen.getByRole("heading", { name: "Author Space" })).toBeInTheDocument();
    expect(screen.queryByText("Dickens")).not.toBeInTheDocument();
    expect(screen.queryByTestId("author-chart")).not.toBeInTheDocument();
  });

  it("hides chart when items is empty array", async () => {
    const useAuthors = await getUseAuthors();
    useAuthors.mockReturnValue({ data: { items: [] }, isLoading: false, error: null });

    await renderAuthors();

    expect(screen.queryByTestId("author-chart")).not.toBeInTheDocument();
  });
});
