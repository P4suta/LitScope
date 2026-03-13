import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

vi.mock("@/hooks/use-status", () => ({
  useStatus: vi.fn(),
}));

vi.mock("@/hooks/use-works", () => ({
  useWorks: vi.fn(),
}));

vi.mock("@/components/charts/genre-distribution-chart", () => ({
  GenreDistributionChart: ({ works }: { works: unknown[] }) => (
    <div data-testid="genre-chart">{works.length} genres</div>
  ),
}));

async function getUseStatus() {
  const mod = await import("@/hooks/use-status");
  return mod.useStatus as ReturnType<typeof vi.fn>;
}

async function getUseWorks() {
  const mod = await import("@/hooks/use-works");
  return mod.useWorks as ReturnType<typeof vi.fn>;
}

async function renderDashboard() {
  const mod = await import("./index");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

describe("Dashboard route", () => {
  it("renders stat cards with data and genre chart", async () => {
    const useStatus = await getUseStatus();
    const useWorks = await getUseWorks();
    useStatus.mockReturnValue({ data: { works: 42, tokens: 100000 } });
    useWorks.mockReturnValue({
      data: {
        items: [
          { author: "Dickens", genre: "Fiction" },
          { author: "Austen", genre: "Romance" },
          { author: "Dickens", genre: "Gothic" },
        ],
      },
    });

    await renderDashboard();

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Works")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("100,000")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // 2 unique authors
    expect(screen.getByText("3")).toBeInTheDocument(); // 3 unique genres
    expect(screen.getByText("Total Words")).toBeInTheDocument();
    expect(screen.getByText("Authors")).toBeInTheDocument();
    expect(screen.getByText("Genres")).toBeInTheDocument();
    expect(screen.getByTestId("genre-chart")).toBeInTheDocument();
    expect(screen.getByText(/distribution of genres/i)).toBeInTheDocument();
  });

  it("renders dashes when data is undefined", async () => {
    const useStatus = await getUseStatus();
    const useWorks = await getUseWorks();
    useStatus.mockReturnValue({ data: undefined });
    useWorks.mockReturnValue({ data: undefined });

    await renderDashboard();

    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBe(4);
    expect(screen.queryByTestId("genre-chart")).not.toBeInTheDocument();
  });

  it("renders dashes when items is undefined", async () => {
    const useStatus = await getUseStatus();
    const useWorks = await getUseWorks();
    useStatus.mockReturnValue({ data: { works: 5, tokens: 1000 } });
    useWorks.mockReturnValue({ data: { items: undefined } });

    await renderDashboard();

    // works and tokens render, but authors/genres show dashes
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("1,000")).toBeInTheDocument();
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBe(2);
    expect(screen.queryByTestId("genre-chart")).not.toBeInTheDocument();
  });

  it("hides genre chart when items is empty", async () => {
    const useStatus = await getUseStatus();
    const useWorks = await getUseWorks();
    useStatus.mockReturnValue({ data: { works: 0, tokens: 0 } });
    useWorks.mockReturnValue({ data: { items: [] } });

    await renderDashboard();

    expect(screen.queryByTestId("genre-chart")).not.toBeInTheDocument();
  });
});
