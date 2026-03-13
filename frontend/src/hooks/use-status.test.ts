import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryWrapper } from "@/test-utils";
import { useStatus } from "./use-status";

vi.mock("@/api/client", () => ({
  api: {
    GET: vi.fn(),
  },
}));

async function getApiMock() {
  const { api } = await import("@/api/client");
  return api.GET as ReturnType<typeof vi.fn>;
}

describe("useStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const status = {
      works: 10,
      chapters: 100,
      sentences: 5000,
      tokens: 50000,
      analyzers_available: ["vocab"],
    };
    mock.mockResolvedValueOnce({ data: status, error: undefined });

    const { result } = renderHook(() => useStatus(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(status);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useStatus(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch status");
  });
});
