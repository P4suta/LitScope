import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export interface TimelinePoint {
  pub_year: number;
  work_id: string;
  title: string;
  ttr: number | null;
  mtld: number | null;
  hapax_ratio: number | null;
  unique_lemmas: number | null;
}

export interface VocabularyTimeline {
  points: TimelinePoint[];
}

export function useTimeline() {
  return useQuery({
    queryKey: ["timeline", "vocabulary"],
    queryFn: async () => {
      const { data, error } = await api.GET("/timeline/vocabulary" as never);
      if (error) {
        const detail =
          typeof error === "object" && error != null && "detail" in error
            ? (error as { detail?: string }).detail
            : undefined;
        throw new Error(
          detail ? `Failed to fetch timeline: ${detail}` : "Failed to fetch timeline",
        );
      }
      return data as VocabularyTimeline;
    },
  });
}
