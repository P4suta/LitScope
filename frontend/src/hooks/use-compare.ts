import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export interface CompareResult {
  work_id: string;
  title: string;
  metrics: Record<string, number | null>;
}

export function useCompare(workIds: string[]) {
  return useQuery({
    queryKey: ["compare", workIds],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/compare" as never,
        {
          params: { query: { work_id: workIds } },
        } as never,
      );
      if (error) throw new Error("Failed to fetch comparison");
      return data as CompareResult[];
    },
    enabled: workIds.length >= 2,
  });
}
