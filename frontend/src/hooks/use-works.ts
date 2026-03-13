import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

// TODO: Replace `as never` casts after running `bun run generate:api` with the backend running.
// Once schema.d.ts is generated and the typed client is used, these paths will be fully type-safe.

export function useWorks() {
  return useQuery({
    queryKey: ["works"],
    queryFn: async () => {
      const { data, error } = await api.GET("/works" as never);
      if (error) throw new Error("Failed to fetch works");
      return data;
    },
  });
}

export function useWork(workId: string) {
  return useQuery({
    queryKey: ["works", workId],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/works/{work_id}" as never,
        {
          params: { path: { work_id: workId } },
        } as never,
      );
      if (error) throw new Error(`Failed to fetch work ${workId}`);
      return data;
    },
    enabled: !!workId,
  });
}
