import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: async () => {
      const { data, error } = await api.GET("/status" as never);
      if (error) throw new Error("Failed to fetch status");
      return data as {
        works: number;
        chapters: number;
        sentences: number;
        tokens: number;
        analyzers_available: string[];
      };
    },
  });
}
