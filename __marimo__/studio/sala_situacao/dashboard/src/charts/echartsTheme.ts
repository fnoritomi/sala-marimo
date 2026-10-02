/**
 * Tema oficial e paleta de cores para os gráficos Apache ECharts da Sala de Situação da ANS.
 * Prioriza acessibilidade, contraste adequado e sobriedade institucional.
 */

export const THEME_COLORS = {
  primary: "#1a365d",     // Azul Marinho Profundo
  secondary: "#2b6cb0",   // Azul Real
  accentTeal: "#0d9488",  // Verde-Água / Odontologia
  accentAmber: "#d97706", // Âmbar / Alerta Sinistralidade
  accentRed: "#dc2626",   // Vermelho / Queda / Despesa
  accentGreen: "#16a34a", // Verde / Crescimento / Superávit
  textMain: "#1e293b",    // Texto escuro (alto contraste)
  textMuted: "#64748b",   // Texto secundário
  gridLine: "#e2e8f0",    // Linhas de grade suaves
  surface: "#ffffff",     // Superfície dos cards
  highlight: "#3b82f6",   // Cor de seleção / cross-filter
};

export const COMMON_CHART_OPTIONS = {
  textStyle: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    fontSize: 12,
    color: THEME_COLORS.textMain,
  },
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(15, 23, 42, 0.92)",
    borderColor: "#334155",
    borderWidth: 1,
    padding: [10, 14],
    textStyle: {
      color: "#f8fafc",
      fontSize: 12,
    },
    axisPointer: {
      type: "cross",
      crossStyle: {
        color: "#94a3b8",
      },
      lineStyle: {
        color: "#94a3b8",
        width: 1,
        type: "dashed",
      },
    },
  },
  grid: {
    top: 36,
    left: 16,
    right: 20,
    bottom: 24,
    containLabel: true,
  },
};
