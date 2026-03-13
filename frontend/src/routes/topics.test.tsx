import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => opts,
}));

describe("Topics route", () => {
  it("renders heading", async () => {
    const mod = await import("./topics");
    const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
    render(<Component />);
    expect(screen.getByRole("heading", { name: "Topics" })).toBeInTheDocument();
  });
});
