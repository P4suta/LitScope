import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useUiStore } from "@/stores/ui-store";

vi.mock("@tanstack/react-query", () => ({
  QueryClient: vi.fn(),
}));

vi.mock("@tanstack/react-router", () => ({
  createRootRouteWithContext:
    () =>
    (opts: { component: React.ComponentType }) => opts,
  Outlet: () => <div data-testid="outlet" />,
}));

vi.mock("@/components/layout/header", () => ({
  Header: () => <div data-testid="header" />,
}));

vi.mock("@/components/layout/sidebar", () => ({
  Sidebar: () => <div data-testid="sidebar" />,
}));

describe("RootLayout", () => {
  beforeEach(() => {
    useUiStore.setState({ sidebarOpen: true });
  });

  afterEach(() => {
    cleanup();
  });

  async function getRootComponent() {
    const mod = await import("./__root");
    return (mod.Route as unknown as { component: React.ComponentType }).component;
  }

  it("applies ml-64 when sidebar is open", async () => {
    useUiStore.setState({ sidebarOpen: true });
    const RootLayout = await getRootComponent();
    render(<RootLayout />);
    const contentDiv = screen.getByTestId("header").parentElement;
    expect(contentDiv?.className).toContain("ml-64");
  });

  it("does not apply ml-64 when sidebar is closed", async () => {
    useUiStore.setState({ sidebarOpen: false });
    const RootLayout = await getRootComponent();
    render(<RootLayout />);
    const contentDiv = screen.getByTestId("header").parentElement;
    expect(contentDiv?.className).not.toContain("ml-64");
  });
});
