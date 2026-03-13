import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
  Link: ({ children, ...props }: React.PropsWithChildren<{ to: string }>) => (
    <a href={props.to}>{children}</a>
  ),
}));

vi.mock("@/hooks/use-works", () => ({
  useWorks: vi.fn(),
}));

async function getUseWorks() {
  const mod = await import("@/hooks/use-works");
  return mod.useWorks as ReturnType<typeof vi.fn>;
}

async function renderWorkList() {
  const mod = await import("./index");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

describe("WorkList route", () => {
  it("renders heading and work cards", async () => {
    const useWorks = await getUseWorks();
    useWorks.mockReturnValue({
      data: {
        items: [
          {
            work_id: "1",
            title: "Moby Dick",
            author: "Melville",
            genre: "Fiction",
            word_count: 200000,
            sent_count: 10000,
            chap_count: 135,
          },
        ],
      },
      isLoading: false,
      error: null,
    });

    await renderWorkList();

    expect(screen.getByRole("heading", { name: "Works" })).toBeInTheDocument();
    expect(screen.getByText("Moby Dick")).toBeInTheDocument();
    expect(screen.getByText("Melville")).toBeInTheDocument();
  });

  it("renders loading state", async () => {
    const useWorks = await getUseWorks();
    useWorks.mockReturnValue({ data: undefined, isLoading: true, error: null });

    await renderWorkList();

    expect(screen.getByText("Loading…")).toBeInTheDocument();
  });

  it("renders error state", async () => {
    const useWorks = await getUseWorks();
    useWorks.mockReturnValue({ data: undefined, isLoading: false, error: new Error("fail") });

    await renderWorkList();

    expect(screen.getByText("Failed to load works.")).toBeInTheDocument();
  });

  it("renders empty list when items is undefined", async () => {
    const useWorks = await getUseWorks();
    useWorks.mockReturnValue({ data: { items: undefined }, isLoading: false, error: null });

    await renderWorkList();

    expect(screen.getByRole("heading", { name: "Works" })).toBeInTheDocument();
    expect(screen.queryByText("Moby Dick")).not.toBeInTheDocument();
  });
});
