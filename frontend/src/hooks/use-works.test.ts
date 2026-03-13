import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryWrapper } from "@/test-utils";
import { useWork, useWorks } from "./use-works";

vi.mock("@/api/client", () => ({
  api: {
    GET: vi.fn(),
  },
}));

async function getApiMock() {
  const { api } = await import("@/api/client");
  return api.GET as ReturnType<typeof vi.fn>;
}

describe("useWorks", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: [{ id: "1", title: "Moby Dick" }], error: undefined });

    const { result } = renderHook(() => useWorks(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: "1", title: "Moby Dick" }]);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "Not found" } });

    const { result } = renderHook(() => useWorks(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch works");
  });
});

describe("useWork", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: { id: "42", title: "1984" }, error: undefined });

    const { result } = renderHook(() => useWork("42"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ id: "42", title: "1984" });
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "err" } });

    const { result } = renderHook(() => useWork("42"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch work 42");
  });

  it("does not fetch when workId is empty", async () => {
    const mock = await getApiMock();

    const { result } = renderHook(() => useWork(""), { wrapper: QueryWrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mock).not.toHaveBeenCalled();
  });

  it("fetches when workId is provided", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: { id: "1" }, error: undefined });

    const { result } = renderHook(() => useWork("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mock).toHaveBeenCalledWith("/works/{work_id}", {
      params: { path: { work_id: "1" } },
    });
  });
});
