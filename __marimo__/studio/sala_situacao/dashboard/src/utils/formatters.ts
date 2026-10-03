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

export function downloadCsv(filename: string, headers: string[], rows: (string | number)[][]) {
  const sanitize = (val: string | number | null | undefined): string => {
    if (val === null || val === undefined) return "";
    const str = String(val);
    if (str.includes(";") || str.includes('"') || str.includes("\n")) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const csvRows = [
    headers.map(sanitize).join(";"),
    ...rows.map((row) => row.map(sanitize).join(";")),
  ];
  // UTF-8 BOM para garantir compatibilidade com Microsoft Excel e acentuação brasileira
  const csvContent = "\uFEFF" + csvRows.join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
