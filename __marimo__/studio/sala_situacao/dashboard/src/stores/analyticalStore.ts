import { writable, derived } from "svelte/store";

export interface FilterState {
  assistencia: string | null;
  contratacao: string | null;
  modalidade: string | null;
  selectedUf: string | null;
  horizonMonths: number;
  geoMetric: "vidas" | "cobertura";
  geoView: "map" | "ranking";
  activeDrawer: string | null;
  isDownloadOpen: boolean;
  operatorSearch: string;
}

function parseUrlParams(): Partial<FilterState> {
  if (typeof window === "undefined" || !window.location) return {};
  try {
    const params = new URLSearchParams(window.location.search);
    const result: Partial<FilterState> = {};
    if (params.has("uf")) result.selectedUf = params.get("uf");
    if (params.has("assistencia")) result.assistencia = params.get("assistencia");
    if (params.has("contratacao")) result.contratacao = params.get("contratacao");
    if (params.has("modalidade")) result.modalidade = params.get("modalidade");
    if (params.has("geoMetric")) {
      const gm = params.get("geoMetric");
      if (gm === "vidas" || gm === "cobertura") result.geoMetric = gm;
    }
    if (params.has("geoView")) {
      const gv = params.get("geoView");
      if (gv === "map" || gv === "ranking") result.geoView = gv;
    }
    if (params.has("search")) result.operatorSearch = params.get("search") || "";
    return result;
  } catch {
    return {};
  }
}

function syncStateToUrl(state: FilterState) {
  if (typeof window === "undefined" || !window.history || !window.location) return;
  try {
    const params = new URLSearchParams();
    if (state.selectedUf) params.set("uf", state.selectedUf);
    if (state.assistencia) params.set("assistencia", state.assistencia);
    if (state.contratacao) params.set("contratacao", state.contratacao);
    if (state.modalidade) params.set("modalidade", state.modalidade);
    if (state.geoMetric && state.geoMetric !== "vidas") params.set("geoMetric", state.geoMetric);
    if (state.geoView && state.geoView !== "map") params.set("geoView", state.geoView);
    if (state.operatorSearch) params.set("search", state.operatorSearch);

    const query = params.toString();
    const newUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
    const currentQuery = window.location.search;
    if (currentQuery !== (query ? `?${query}` : "")) {
      window.history.replaceState(null, "", newUrl);
    }
  } catch {
    // Silently continue in environments without window.history
  }
}

const initialState: FilterState = {
  assistencia: null,
  contratacao: null,
  modalidade: null,
  selectedUf: null,
  horizonMonths: 36,
  geoMetric: "vidas",
  geoView: "map",
  activeDrawer: null,
  isDownloadOpen: false,
  operatorSearch: "",
  ...parseUrlParams(),
};

function createAnalyticalStore() {
  const { subscribe, set, update } = writable<FilterState>(initialState);

  // Escuta navegacao do browser (Back/Forward)
  if (typeof window !== "undefined") {
    window.addEventListener("popstate", () => {
      const fromUrl = parseUrlParams();
      update((s) => ({
        ...s,
        assistencia: fromUrl.assistencia ?? null,
        contratacao: fromUrl.contratacao ?? null,
        modalidade: fromUrl.modalidade ?? null,
        selectedUf: fromUrl.selectedUf ?? null,
        geoMetric: fromUrl.geoMetric ?? "vidas",
        geoView: fromUrl.geoView ?? "map",
        operatorSearch: fromUrl.operatorSearch ?? "",
      }));
    });
  }

  const wrappedUpdate = (fn: (s: FilterState) => FilterState) => {
    update((s) => {
      const next = fn(s);
      syncStateToUrl(next);
      return next;
    });
  };

  return {
    subscribe,
    setAssistencia: (val: string | null) =>
      wrappedUpdate((s) => ({ ...s, assistencia: val === "Todas" ? null : val })),
    setContratacao: (val: string | null) =>
      wrappedUpdate((s) => ({ ...s, contratacao: val === "Todas" ? null : val })),
    setModalidade: (val: string | null) =>
      wrappedUpdate((s) => ({ ...s, modalidade: val === "Todas" ? null : val })),
    setUf: (uf: string | null) =>
      wrappedUpdate((s) => ({ ...s, selectedUf: uf === "Todas" ? null : uf })),
    toggleUf: (uf: string | null) =>
      wrappedUpdate((s) => ({
        ...s,
        selectedUf: s.selectedUf === uf ? null : (uf === "Todas" ? null : uf),
      })),
    toggleContratacao: (val: string | null) =>
      wrappedUpdate((s) => ({
        ...s,
        contratacao: s.contratacao === val ? null : (val === "Todas" ? null : val),
      })),
    toggleModalidade: (val: string | null) =>
      wrappedUpdate((s) => ({
        ...s,
        modalidade: s.modalidade === val ? null : (val === "Todas" ? null : val),
      })),
    clearUf: () => wrappedUpdate((s) => ({ ...s, selectedUf: null })),
    clearAll: () =>
      wrappedUpdate((s) => ({
        ...s,
        assistencia: null,
        contratacao: null,
        modalidade: null,
        selectedUf: null,
        operatorSearch: "",
      })),
    setHorizon: (months: number) =>
      wrappedUpdate((s) => ({ ...s, horizonMonths: months })),
    setGeoMetric: (metric: "vidas" | "cobertura") =>
      wrappedUpdate((s) => ({ ...s, geoMetric: metric })),
    setGeoView: (view: "map" | "ranking") =>
      wrappedUpdate((s) => ({ ...s, geoView: view })),
    openMetadata: (metricId: string) =>
      wrappedUpdate((s) => ({ ...s, activeDrawer: metricId })),
    closeMetadata: () =>
      wrappedUpdate((s) => ({ ...s, activeDrawer: null })),
    setDownloadOpen: (isOpen: boolean) =>
      wrappedUpdate((s) => ({ ...s, isDownloadOpen: isOpen })),
    setOperatorSearch: (term: string) =>
      wrappedUpdate((s) => ({ ...s, operatorSearch: term })),
  };
}

export const analyticalStore = createAnalyticalStore();

export const hasActiveFilters = derived(analyticalStore, ($state) => {
  return Boolean(
    $state.assistencia ||
      $state.contratacao ||
      $state.modalidade ||
      $state.selectedUf
  );
});
