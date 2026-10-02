/**
 * Utilitários de formatação numérica, monetária e temporal em padrão brasileiro (pt-BR).
 */

export function formatNumber(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return "-";
  return new Intl.NumberFormat("pt-BR").format(val);
}

export function formatCompact(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return "-";
  const abs = Math.abs(val);
  if (abs >= 1_000_000_000) {
    return (val / 1_000_000_000).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " bi";
  }
  if (abs >= 1_000_000) {
    return (val / 1_000_000).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " mi";
  }
  if (abs >= 1_000) {
    return (val / 1_000).toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " mil";
  }
  return formatNumber(val);
}

export function formatCurrency(val: number | null | undefined, compact = true): string {
  if (val === null || val === undefined || isNaN(val)) return "R$ -";
  if (compact) {
    return "R$ " + formatCompact(val);
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(val);
}

export function formatPercent(val: number | null | undefined, includeSign = false): string {
  if (val === null || val === undefined || isNaN(val)) return "-";
  const formatted = val.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }) + "%";
  if (includeSign && val > 0) {
    return "+" + formatted;
  }
  return formatted;
}

export function formatCompetence(dateStr: string): string {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length < 2) return dateStr;
  const meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  const mIdx = parseInt(parts[1], 10) - 1;
  return `${meses[mIdx]}/${parts[0]}`;
}
