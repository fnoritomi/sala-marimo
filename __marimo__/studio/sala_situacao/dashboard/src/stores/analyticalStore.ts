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
};

function createAnalyticalStore() {
  const { subscribe, set, update } = writable<FilterState>(initialState);

  return {
    subscribe,
    setAssistencia: (val: string | null) =>
      update((s) => ({ ...s, assistencia: val === "Todas" ? null : val })),
    setContratacao: (val: string | null) =>
      update((s) => ({ ...s, contratacao: val === "Todas" ? null : val })),
    setModalidade: (val: string | null) =>
      update((s) => ({ ...s, modalidade: val === "Todas" ? null : val })),
    setUf: (uf: string | null) =>
      update((s) => ({ ...s, selectedUf: uf === "Todas" ? null : uf })),
    toggleUf: (uf: string | null) =>
      update((s) => ({
        ...s,
        selectedUf: s.selectedUf === uf ? null : (uf === "Todas" ? null : uf),
      })),
    toggleContratacao: (val: string | null) =>
      update((s) => ({
        ...s,
        contratacao: s.contratacao === val ? null : (val === "Todas" ? null : val),
      })),
    toggleModalidade: (val: string | null) =>
      update((s) => ({
        ...s,
        modalidade: s.modalidade === val ? null : (val === "Todas" ? null : val),
      })),
    clearUf: () => update((s) => ({ ...s, selectedUf: null })),
    clearAll: () =>
      update((s) => ({
        ...s,
        assistencia: null,
        contratacao: null,
        modalidade: null,
        selectedUf: null,
        operatorSearch: "",
      })),
    setHorizon: (months: number) =>
      update((s) => ({ ...s, horizonMonths: months })),
    setGeoMetric: (metric: "vidas" | "cobertura") =>
      update((s) => ({ ...s, geoMetric: metric })),
    setGeoView: (view: "map" | "ranking") =>
      update((s) => ({ ...s, geoView: view })),
    openMetadata: (metricId: string) =>
      update((s) => ({ ...s, activeDrawer: metricId })),
    closeMetadata: () =>
      update((s) => ({ ...s, activeDrawer: null })),
    setDownloadOpen: (isOpen: boolean) =>
      update((s) => ({ ...s, isDownloadOpen: isOpen })),
    setOperatorSearch: (term: string) =>
      update((s) => ({ ...s, operatorSearch: term })),
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
