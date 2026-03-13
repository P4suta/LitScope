import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithQuery } from "@/test-utils";

const mockParams = { workId: "42" };

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: { component: React.ComponentType }) => ({
    ...opts,
    useParams: () => mockParams,
  }),
  Link: ({ children, ...props }: React.PropsWithChildren<{ to: string }>) => (
    <a href={props.to}>{children}</a>
  ),
}));

vi.mock("@/hooks/use-works", () => ({
  useWork: vi.fn(),
}));

vi.mock("@/hooks/use-analysis", () => ({
  useVocabulary: vi.fn(),
  useReadability: vi.fn(),
  useSyntax: vi.fn(),
}));

vi.mock("@/components/charts/word-frequency-chart", () => ({
  WordFrequencyChart: ({ words }: { words: unknown[] }) => (
    <div data-testid="word-freq-chart">{words.length} words</div>
  ),
}));

vi.mock("@/components/charts/zipf-plot", () => ({
  ZipfPlot: ({ intercept }: { intercept: number | null }) => (
    <div data-testid="zipf-plot" data-intercept={intercept} />
  ),
}));

vi.mock("@/components/charts/pos-distribution-chart", () => ({
  POSDistributionChart: () => <div data-testid="pos-chart" />,
}));

async function getUseWork() {
  const mod = await import("@/hooks/use-works");
  return mod.useWork as ReturnType<typeof vi.fn>;
}

async function getAnalysisMocks() {
  const mod = await import("@/hooks/use-analysis");
  return {
    useVocabulary: mod.useVocabulary as ReturnType<typeof vi.fn>,
    useReadability: mod.useReadability as ReturnType<typeof vi.fn>,
    useSyntax: mod.useSyntax as ReturnType<typeof vi.fn>,
  };
}

async function renderWorkDetail() {
  const mod = await import("./$workId");
  const Component = (mod.Route as unknown as { component: React.ComponentType }).component;
  return renderWithQuery(<Component />);
}

const noData = { data: undefined };

describe("WorkDetail route", () => {
  it("shows workId as fallback title when work is undefined", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue(noData);
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue(noData);
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    expect(screen.getByRole("heading", { name: "42" })).toBeInTheDocument();
  });

  it("renders work details and overview stats", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue({
      data: {
        title: "1984",
        author: "Orwell",
        genre: "Dystopian",
        chap_count: 24,
        sent_count: 5000,
        word_count: 88000,
        analyses_run: ["vocab"],
      },
    });
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue(noData);
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    expect(screen.getByRole("heading", { name: "1984" })).toBeInTheDocument();
    expect(screen.getByText(/Orwell/)).toBeInTheDocument();
    expect(screen.getByText(/Dystopian/)).toBeInTheDocument();
    expect(screen.getByText("24")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // analyses count
  });

  it("shows 0 analyses when analyses_run is undefined", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue({
      data: {
        title: "Test",
        author: "Author",
        genre: "Genre",
        chap_count: 1,
        sent_count: 10,
        word_count: 100,
        analyses_run: undefined,
      },
    });
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue(noData);
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders dash for undefined stat values", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue({
      data: {
        title: "Sparse",
        author: "Author",
        genre: "Genre",
        chap_count: undefined,
        sent_count: undefined,
        word_count: undefined,
        analyses_run: [],
      },
    });
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue(noData);
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    // chap_count, sent_count, word_count are all undefined → Stat renders "—"
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(3);
  });

  it("renders vocabulary section with charts and descriptions when data is available", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue(noData);
    mocks.useVocabulary.mockReturnValue({
      data: {
        unique_lemmas: 5000,
        ttr: 0.1234,
        mtld: 85.5,
        hapax_ratio: 0.4567,
        zipf_alpha: 1.5,
        zipf_r_squared: 0.95,
        zipf_intercept: 2.0,
        top_words: [{ lemma: "the", count: 3000 }],
      },
    });
    mocks.useReadability.mockReturnValue(noData);
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    expect(screen.getByText("Vocabulary")).toBeInTheDocument();
    expect(screen.getByText(/vocabulary richness and diversity/i)).toBeInTheDocument();
    expect(screen.getByText("5,000")).toBeInTheDocument();
    expect(screen.getByText("0.1234")).toBeInTheDocument();
    expect(screen.getByTestId("word-freq-chart")).toBeInTheDocument();
    expect(screen.getByTestId("zipf-plot")).toBeInTheDocument();
    // Metric tooltips are present
    expect(screen.getByLabelText(/Info:.*Type-Token Ratio/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Info:.*Textual Lexical Diversity/)).toBeInTheDocument();
  });

  it("renders readability section with description when data is available", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue(noData);
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue({
      data: {
        ari: 8.5,
        mean_sentence_length: 15.3,
        median_sentence_length: 14,
        stdev_sentence_length: 5.2,
        min_sentence_length: 1,
        max_sentence_length: 80,
      },
    });
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    expect(screen.getByText("Readability")).toBeInTheDocument();
    expect(screen.getByText(/readability scores/i)).toBeInTheDocument();
    expect(screen.getByText("8.5")).toBeInTheDocument();
    expect(screen.getByText("15.3")).toBeInTheDocument();
  });

  it("renders readability dashes when ari is null", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue(noData);
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue({
      data: {
        ari: null,
        mean_sentence_length: 10.0,
        median_sentence_length: 9,
        stdev_sentence_length: 3.0,
        min_sentence_length: 1,
        max_sentence_length: 40,
      },
    });
    mocks.useSyntax.mockReturnValue(noData);

    await renderWorkDetail();

    expect(screen.getByText("Readability")).toBeInTheDocument();
    // ARI is null → fmt returns "—"
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(1);
  });

  it("renders syntax section with POS chart and description when data is available", async () => {
    const useWork = await getUseWork();
    const mocks = await getAnalysisMocks();
    useWork.mockReturnValue(noData);
    mocks.useVocabulary.mockReturnValue(noData);
    mocks.useReadability.mockReturnValue(noData);
    mocks.useSyntax.mockReturnValue({
      data: {
        pos_distribution: [{ pos: "NOUN", count: 500, ratio: 0.25 }],
        active_voice_count: 900,
        passive_voice_count: 100,
        passive_ratio: 0.1,
      },
    });

    await renderWorkDetail();

    expect(screen.getByText("Part-of-Speech Distribution")).toBeInTheDocument();
    expect(screen.getByText(/part-of-speech distribution reveals/i)).toBeInTheDocument();
    expect(screen.getByTestId("pos-chart")).toBeInTheDocument();
  });
});
