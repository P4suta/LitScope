import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryWrapper } from "@/test-utils";
import { useTimeline } from "./use-timeline";

vi.mock("@/api/client", () => ({
  api: {
    GET: vi.fn(),
  },
}));

async function getApiMock() {
  const { api } = await import("@/api/client");
  return api.GET as ReturnType<typeof vi.fn>;
}

describe("useTimeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const timeline = {
      points: [
        {
          pub_year: 1920,
          work_id: "1",
          title: "A",
          ttr: 0.5,
          mtld: 45,
          hapax_ratio: 0.3,
          unique_lemmas: 100,
        },
      ],
    };
    mock.mockResolvedValueOnce({ data: timeline, error: undefined });

    const { result } = renderHook(() => useTimeline(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(timeline);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useTimeline(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toMatch(/^Failed to fetch timeline/);
  });
});
