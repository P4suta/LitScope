import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@tanstack/react-query", () => ({
  QueryClient: vi.fn(() => ({})),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@tanstack/react-router", () => ({
  createRouter: vi.fn(() => ({})),
  RouterProvider: () => <div data-testid="router" />,
}));

vi.mock("./routes/__root", () => ({
  RouterContext: {},
}));

vi.mock("./routeTree.gen", () => ({
  routeTree: {},
}));

describe("App", () => {
  it("renders without crashing", async () => {
    const { App } = await import("./app");
    const { container } = render(<App />);
    expect(container.querySelector('[data-testid="router"]')).toBeInTheDocument();
  });
});
