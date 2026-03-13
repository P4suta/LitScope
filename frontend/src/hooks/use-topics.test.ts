import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryWrapper } from "@/test-utils";
import { useTopics } from "./use-topics";

vi.mock("@/api/client", () => ({
  api: {
    GET: vi.fn(),
  },
}));

async function getApiMock() {
  const { api } = await import("@/api/client");
  return api.GET as ReturnType<typeof vi.fn>;
}

describe("useTopics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const topics = [
      { topic_id: 0, label: "Book A", work_id: "1", keywords: [{ lemma: "love", score: 0.9 }] },
    ];
    mock.mockResolvedValueOnce({ data: topics, error: undefined });

    const { result } = renderHook(() => useTopics(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(topics);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useTopics(), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toMatch(/^Failed to fetch topics/);
  });
});
