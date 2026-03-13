import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryWrapper } from "@/test-utils";
import { useReadability, useSyntax, useVocabulary } from "./use-analysis";

vi.mock("@/api/client", () => ({
  api: {
    GET: vi.fn(),
  },
}));

async function getApiMock() {
  const { api } = await import("@/api/client");
  return api.GET as ReturnType<typeof vi.fn>;
}

describe("useVocabulary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const vocab = { work_id: "1", total_tokens: 100, unique_lemmas: 50, ttr: 0.5 };
    mock.mockResolvedValueOnce({ data: vocab, error: undefined });

    const { result } = renderHook(() => useVocabulary("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(vocab);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useVocabulary("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch vocabulary");
  });

  it("does not fetch when workId is empty", async () => {
    const mock = await getApiMock();

    const { result } = renderHook(() => useVocabulary(""), { wrapper: QueryWrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mock).not.toHaveBeenCalled();
  });
});

describe("useReadability", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const readability = { work_id: "1", ari: 8.5, mean_sentence_length: 15 };
    mock.mockResolvedValueOnce({ data: readability, error: undefined });

    const { result } = renderHook(() => useReadability("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(readability);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useReadability("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch readability");
  });

  it("does not fetch when workId is empty", async () => {
    const mock = await getApiMock();

    const { result } = renderHook(() => useReadability(""), { wrapper: QueryWrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mock).not.toHaveBeenCalled();
  });
});

describe("useSyntax", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns data on success", async () => {
    const mock = await getApiMock();
    const syntax = {
      work_id: "1",
      passive_ratio: 0.1,
      active_voice_count: 90,
      passive_voice_count: 10,
    };
    mock.mockResolvedValueOnce({ data: syntax, error: undefined });

    const { result } = renderHook(() => useSyntax("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(syntax);
  });

  it("throws on error response", async () => {
    const mock = await getApiMock();
    mock.mockResolvedValueOnce({ data: undefined, error: { message: "fail" } });

    const { result } = renderHook(() => useSyntax("1"), { wrapper: QueryWrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.message).toBe("Failed to fetch syntax");
  });

  it("does not fetch when workId is empty", async () => {
    const mock = await getApiMock();

    const { result } = renderHook(() => useSyntax(""), { wrapper: QueryWrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mock).not.toHaveBeenCalled();
  });
});
