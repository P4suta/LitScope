import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryWrapper } from "@/test-utils";
import { useCompare } from "./use-compare";

vi.mock("@/api/client", () => ({
  api: {
    GET: vi.fn(),
  },
}));

async function getApiMock() {
  const { api } = await import("@/api/client");
  return api.GET as ReturnType<typeof vi.fn>;
}

describe("useCompare", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const results = [
      { work_id: "1", title: "A", metrics: { ttr: 0.5 } },
      { work_id: "2", title: "B", metrics: { ttr: 0.6 } },
    ];
    mock.mockResolvedValueOnce({ data: results, error: undefined });

    const { result } = renderHook(() => useCompare(["1", "2"]), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(results);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useCompare(["1", "2"]), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch comparison");
  });

  it("does not fetch when fewer than 2 workIds", async () => {
    const mock = await getApiMock();

    const { result } = renderHook(() => useCompare(["1"]), { wrapper: QueryWrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mock).not.toHaveBeenCalled();
  });

  it("does not fetch when workIds is empty", async () => {
    const mock = await getApiMock();

    const { result } = renderHook(() => useCompare([]), { wrapper: QueryWrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mock).not.toHaveBeenCalled();
  });
});
