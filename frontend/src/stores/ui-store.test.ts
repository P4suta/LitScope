import { beforeEach, describe, expect, it } from "vitest";
import { useUiStore } from "./ui-store";

describe("useUiStore", () => {
  beforeEach(() => {
    useUiStore.setState({ sidebarOpen: true });
  });

  it("has sidebarOpen true by default", () => {
    expect(useUiStore.getState().sidebarOpen).toBe(true);
  });

  it("toggles sidebarOpen to false", () => {
    useUiStore.getState().toggleSidebar();
    expect(useUiStore.getState().sidebarOpen).toBe(false);
  });

  it("toggles sidebarOpen back to true", () => {
    useUiStore.getState().toggleSidebar();
    useUiStore.getState().toggleSidebar();
    expect(useUiStore.getState().sidebarOpen).toBe(true);
  });
});
