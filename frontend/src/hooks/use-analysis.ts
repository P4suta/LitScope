import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

function useAnalysis<T>(workId: string, endpoint: string) {
  return useQuery({
    queryKey: ["works", workId, endpoint],
    queryFn: async () => {
      const { data, error } = await api.GET(
        `/works/{work_id}/${endpoint}` as never,
        { params: { path: { work_id: workId } } } as never,
      );
      if (error) throw new Error(`Failed to fetch ${endpoint}`);
      return data as T;
    },
    enabled: !!workId,
  });
}

export interface VocabularyData {
  work_id: string;
  total_tokens: number;
  unique_lemmas: number;
  ttr: number;
  hapax_ratio: number;
  mtld: number;
  zipf_alpha: number;
  zipf_r_squared: number;
  zipf_intercept: number | null;
  top_words: Array<{ lemma: string; count: number; tf: number }>;
}

export interface ReadabilityData {
  work_id: string;
  ari: number | null;
  flesch_kincaid_grade: number | null;
  coleman_liau_index: number | null;
  mean_sentence_length: number;
  median_sentence_length: number;
  stdev_sentence_length: number;
  min_sentence_length: number;
  max_sentence_length: number;
}

export interface SyntaxData {
  work_id: string;
  pos_distribution: Array<{ pos: string; count: number; ratio: number }>;
  active_voice_count: number;
  passive_voice_count: number;
  passive_ratio: number;
  sentence_openings: Array<{ pos: string; count: number; ratio: number }> | null;
}

export const useVocabulary = (workId: string) => useAnalysis<VocabularyData>(workId, "vocabulary");

export const useReadability = (workId: string) =>
  useAnalysis<ReadabilityData>(workId, "readability");

export const useSyntax = (workId: string) => useAnalysis<SyntaxData>(workId, "syntax");
