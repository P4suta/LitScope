import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export interface AuthorItem {
  author: string;
  work_count: number;
}

export function useAuthors() {
  return useQuery({
    queryKey: ["authors"],
    queryFn: async () => {
      const { data, error } = await api.GET("/authors" as never);
      if (error) throw new Error("Failed to fetch authors");
      return data as { items: AuthorItem[]; total: number; page: number; page_size: number };
    },
  });
}
