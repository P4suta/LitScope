import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

describe("Dashboard route", () => {
  async function renderDashboard() {
    const mod = await import("./index");
    const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
    return render(<Component />);
  }

  it("renders heading and stat cards", async () => {
    await renderDashboard();
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Total Words")).toBeInTheDocument();
    expect(screen.getByText("Authors")).toBeInTheDocument();
    expect(screen.getByText("Genres")).toBeInTheDocument();
  });
});
