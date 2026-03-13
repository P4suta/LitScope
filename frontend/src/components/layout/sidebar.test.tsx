import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useUiStore } from "@/stores/ui-store";

vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    to,
    activeProps: _activeProps,
    activeOptions: _activeOptions,
    ...rest
  }: {
    children: React.ReactNode;
    to: string;
    activeProps?: Record<string, unknown>;
    activeOptions?: Record<string, unknown>;
    className?: string;
  }) => (
    <a href={to} {...rest}>
      {children}
    </a>
  ),
}));

describe("Sidebar", () => {
  beforeEach(() => {
    useUiStore.setState({ sidebarOpen: true });
  });

  afterEach(() => {
    cleanup();
  });

  async function renderSidebar() {
    const { Sidebar } = await import("./sidebar");
    return render(<Sidebar />);
  }

  it("renders nothing when sidebarOpen is false", async () => {
    useUiStore.setState({ sidebarOpen: false });
    const { container } = await renderSidebar();
    expect(container.innerHTML).toBe("");
  });

  it("renders sidebar with all navigation items when open", async () => {
    await renderSidebar();
    expect(screen.getByText("LitScope")).toBeInTheDocument();
    for (const label of ["Dashboard", "Works", "Compare", "Authors", "Timeline", "Topics"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("renders correct href for Dashboard link", async () => {
    await renderSidebar();
    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink).toHaveAttribute("href", "/");
  });

  it("renders correct href for Works link", async () => {
    await renderSidebar();
    const worksLink = screen.getByText("Works").closest("a");
    expect(worksLink).toHaveAttribute("href", "/works");
  });
});
