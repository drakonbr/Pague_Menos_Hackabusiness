import { useEffect, useState } from "react";

/** Carrega dados de um serviço; descarta respostas antigas se as dependências mudarem. */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): { data: T | null; error: string | null; loading: boolean } {
  const [state, set] = useState<{ data: T | null; error: string | null; loading: boolean }>({ data: null, error: null, loading: true });
  useEffect(() => {
    let alive = true;
    set((s) => ({ ...s, loading: true, error: null }));
    fn().then(
      (data) => alive && set({ data, error: null, loading: false }),
      (e: unknown) => alive && set({ data: null, error: e instanceof Error ? e.message : "Falha ao carregar.", loading: false }),
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}
