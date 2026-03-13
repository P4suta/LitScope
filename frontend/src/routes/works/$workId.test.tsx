import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

let mockParams = { workId: "42" };

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => ({
    ...opts,
    useParams: () => mockParams,
  }),
}));

describe("WorkDetail route", () => {
  async function renderWorkDetail() {
    const mod = await import("./$workId");
    const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
    return render(<Component />);
  }

  it("renders heading", async () => {
    await renderWorkDetail();
    expect(screen.getByRole("heading", { name: "Work Detail" })).toBeInTheDocument();
  });

  it("displays workId from params", async () => {
    mockParams = { workId: "abc-123" };
    await renderWorkDetail();
    expect(screen.getByText("Viewing work: abc-123")).toBeInTheDocument();
  });
});
