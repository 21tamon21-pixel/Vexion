import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";
import type { AppConfig, User } from "@/types";

export function useAuth() {
  const q = useQuery({
    queryKey: ["me"],
    queryFn: () => apiGet<User>("/profile/me"),
    retry: false,
    staleTime: 30_000,
  });
  return { user: q.data ?? null, loading: q.isLoading, failed: q.isError };
}

export function useAppConfig() {
  return useQuery({
    queryKey: ["config"],
    queryFn: () => apiGet<AppConfig>("/config"),
    retry: false,
    staleTime: Infinity,
  });
}

export function useEndSession() {
  const qc = useQueryClient();
  return async () => {
    qc.clear();
  };
}
