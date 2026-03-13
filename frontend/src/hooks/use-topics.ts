import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export interface TopicKeyword {
  lemma: string;
  score: number;
}

export interface TopicSummary {
  topic_id: number;
  label: string;
  work_id: string;
  keywords: TopicKeyword[];
}

export function useTopics() {
  return useQuery({
    queryKey: ["topics"],
    queryFn: async () => {
      const { data, error } = await api.GET("/topics" as never);
      if (error) {
        const detail =
          typeof error === "object" && error != null && "detail" in error
            ? (error as { detail?: string }).detail
            : undefined;
        throw new Error(detail ? `Failed to fetch topics: ${detail}` : "Failed to fetch topics");
      }
      return data as TopicSummary[];
    },
  });
}
