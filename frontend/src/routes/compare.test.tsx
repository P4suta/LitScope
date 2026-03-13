import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

vi.mock("@/hooks/use-works", () => ({
  useWorks: vi.fn(),
}));

vi.mock("@/hooks/use-compare", () => ({
  useCompare: vi.fn(),
}));

vi.mock("@/components/charts/radar-chart", () => ({
  RadarChart: ({ items }: { items: unknown[] }) => (
    <div data-testid="radar-chart">{items.length} items</div>
  ),
}));

async function getUseWorks() {
  const mod = await import("@/hooks/use-works");
  return mod.useWorks as ReturnType<typeof vi.fn>;
}

async function getUseCompare() {
  const mod = await import("@/hooks/use-compare");
  return mod.useCompare as ReturnType<typeof vi.fn>;
}

async function renderCompare() {
  const mod = await import("./compare");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

describe("Compare route", () => {
  it("renders heading and selection prompt", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: [] }, isLoading: false });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderCompare();

    expect(screen.getByRole("heading", { name: "Compare" })).toBeInTheDocument();
    expect(screen.getByText(/normalized to 0–1/i)).toBeInTheDocument();
    expect(screen.getByText("Select at least 2 works to compare.")).toBeInTheDocument();
  });

  it("renders works loading state", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: undefined, isLoading: true });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderCompare();

    expect(screen.getByText("Loading works…")).toBeInTheDocument();
  });

  it("renders work checkboxes", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({
      data: {
        items: [
          { work_id: "1", title: "Book A", author: "Auth A" },
          { work_id: "2", title: "Book B", author: "Auth B" },
        ],
      },
      isLoading: false,
    });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderCompare();

    expect(screen.getByText("Book A")).toBeInTheDocument();
    expect(screen.getByText("Book B")).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")).toHaveLength(2);
  });

  it("toggles checkbox selection", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({
      data: {
        items: [
          { work_id: "1", title: "Book A", author: "A" },
          { work_id: "2", title: "Book B", author: "B" },
        ],
      },
      isLoading: false,
    });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderCompare();

    const checkboxes = screen.getAllByRole("checkbox");
    await userEvent.click(checkboxes[0]!);
    expect(checkboxes[0]!).toBeChecked();

    // Uncheck
    await userEvent.click(checkboxes[0]!);
    expect(checkboxes[0]!).not.toBeChecked();
  });

  it("renders comparison table and radar chart when data is available", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: [] }, isLoading: false });
    useCompare.mockReturnValue({
      data: [
        { work_id: "1", title: "A", metrics: { ttr: 0.5, mtld: null } },
        { work_id: "2", title: "B", metrics: { ttr: 0.6, mtld: 80 } },
      ],
      isLoading: false,
      error: null,
    });

    await renderCompare();

    expect(screen.getByText("ttr")).toBeInTheDocument();
    expect(screen.getByText("0.5")).toBeInTheDocument();
    expect(screen.getByText("0.6")).toBeInTheDocument();
    expect(screen.getByText("80")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument(); // null metric
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("renders compare loading state", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: [] }, isLoading: false });
    useCompare.mockReturnValue({ data: undefined, isLoading: true, error: null });

    await renderCompare();

    expect(screen.getByText("Comparing…")).toBeInTheDocument();
  });

  it("renders compare error state", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: [] }, isLoading: false });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: new Error("fail") });

    await renderCompare();

    expect(screen.getByText("Failed to load comparison.")).toBeInTheDocument();
  });

  it("caps selection at 5 works", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    const items = Array.from({ length: 6 }, (_, i) => ({
      work_id: String(i + 1),
      title: `Book ${i + 1}`,
      author: `Author ${i + 1}`,
    }));
    useWorks.mockReturnValue({ data: { items }, isLoading: false });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderCompare();

    const checkboxes = screen.getAllByRole("checkbox");
    // Select 5
    for (let i = 0; i < 5; i++) {
      await userEvent.click(checkboxes[i]!);
    }
    expect(checkboxes[4]!).toBeChecked();

    // Try to select 6th — should be ignored
    await userEvent.click(checkboxes[5]!);
    expect(checkboxes[5]!).not.toBeChecked();
  });

  it("renders table with empty metrics", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: [] }, isLoading: false });
    useCompare.mockReturnValue({
      data: [{ work_id: "1", title: "A", metrics: {} }],
      isLoading: false,
      error: null,
    });

    await renderCompare();

    // Table renders but with no metric rows
    expect(screen.getByText("Metric")).toBeInTheDocument();
    expect(screen.getByText("A")).toBeInTheDocument();
  });

  it("renders table header with empty comparison array", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: [] }, isLoading: false });
    useCompare.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    await renderCompare();

    // Table renders with Metric header, no rows since comparison[0] is undefined
    expect(screen.getByText("Metric")).toBeInTheDocument();
  });

  it("renders empty items when works data has no items", async () => {
    const useWorks = await getUseWorks();
    const useCompare = await getUseCompare();
    useWorks.mockReturnValue({ data: { items: undefined }, isLoading: false });
    useCompare.mockReturnValue({ data: undefined, isLoading: false, error: null });

    await renderCompare();

    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });
});
