import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useUiStore } from "@/stores/ui-store";
import { Header } from "./header";

describe("Header", () => {
  beforeEach(() => {
    useUiStore.setState({ sidebarOpen: true });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders toggle button with accessible label", () => {
    render(<Header />);
    expect(screen.getByRole("button", { name: "Toggle sidebar" })).toBeInTheDocument();
  });

  it("toggles sidebar on click", async () => {
    render(<Header />);
    await userEvent.click(screen.getByRole("button", { name: "Toggle sidebar" }));
    expect(useUiStore.getState().sidebarOpen).toBe(false);
  });
});
