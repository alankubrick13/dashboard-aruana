# ==============================================================================
# SCRIPT: Integração producao_por_produto.csv → dados_consolidados_v4.csv
# Usa o arquivo já extraído para gerar o dataset consolidado v4
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr); library(tidyr); library(janitor)
})

# Diretório de trabalho
script_dir <- tryCatch({
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    normalizePath(dirname(sub("--file=", "", file_arg)))
  } else {
    normalizePath(dirname(sys.frame(1)$ofile))
  }
}, error = function(e) {
  "/home/alankubrick/Documentos/BASE DE DADOS PROJETO/ACTUALIZACAO_TEMPORAL"
})
setwd(script_dir)
cat("Diretório:", getwd(), "\n\n")

# -----------------------------------------------------------------------
# 1. CARREGAR DADOS JÁ EXTRAÍDOS
# -----------------------------------------------------------------------

cat("[1/3] Carregando producao_por_produto.csv...\n")
pam_long <- read.csv2("producao_por_produto.csv", fileEncoding = "UTF-8", stringsAsFactors = FALSE)
pam_long$code_muni <- as.character(pam_long$code_muni)
cat("  Linhas:", nrow(pam_long), "\n")
cat("  Municípios:", length(unique(pam_long$code_muni)), "\n")

anos <- unique(pam_long$ano)
cat("  Anos:", paste(anos, collapse = ", "), "\n")

# -----------------------------------------------------------------------
# 2. AGREGAR POR MUNICÍPIO
# -----------------------------------------------------------------------

cat("\n[2/3] Agregando por município...\n")

agg_cat <- pam_long |>
  group_by(code_muni, ano, categoria) |>
  summarise(
    area_ha         = sum(area_ha, na.rm = TRUE),
    qtd_toneladas   = sum(qtd_toneladas, na.rm = TRUE),
    valor_mil_reais = sum(valor_mil_reais, na.rm = TRUE),
    n_produtos      = n_distinct(cod_produto),
    .groups = "drop"
  )

agg_wide <- agg_cat |>
  pivot_wider(
    id_cols     = code_muni,
    names_from  = c(categoria, ano),
    values_from = c(area_ha, qtd_toneladas, valor_mil_reais, n_produtos),
    names_sep   = "_",
    values_fill = 0
  )

# Percentuais
for (a in anos) {
  col_alim <- paste0("area_ha_alimento_", a)
  col_comm <- paste0("area_ha_commodity_", a)
  col_perc_a <- paste0("perc_area_alimento_", a)
  col_perc_c <- paste0("perc_area_commodity_", a)

  if (col_alim %in% colnames(agg_wide) && col_comm %in% colnames(agg_wide)) {
    total <- agg_wide[[col_alim]] + agg_wide[[col_comm]]
    agg_wide[[col_perc_a]] <- round(ifelse(total > 0, agg_wide[[col_alim]] / total * 100, NA_real_), 2)
    agg_wide[[col_perc_c]] <- round(ifelse(total > 0, agg_wide[[col_comm]] / total * 100, NA_real_), 2)
  }
}

# Top 3 produtos
top3 <- pam_long |>
  filter(ano == "2024", !is.na(area_ha), area_ha > 0) |>
  group_by(code_muni, categoria) |>
  arrange(desc(area_ha)) |>
  slice_head(n = 3) |>
  summarise(
    top3 = paste(produto, collapse = "; "),
    .groups = "drop"
  ) |>
  pivot_wider(
    id_cols    = code_muni,
    names_from = categoria,
    values_from = top3,
    names_prefix = "top3_2024_"
  )

agg_final <- agg_wide |>
  left_join(top3, by = "code_muni")

cat("  Municípios agregados:", nrow(agg_final), "\n")
cat("  Colunas novas:", ncol(agg_final) - 1, "\n")

# -----------------------------------------------------------------------
# 3. JOIN COM V3 → V4
# -----------------------------------------------------------------------

cat("\n[3/3] Integrando com dados_consolidados_v3.csv...\n")

path_v3 <- "dados_consolidados_v3.csv"
path_v4 <- "dados_consolidados_v4.csv"

df <- read.csv2(path_v3, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
df$code_muni <- as.character(df$code_muni)
cat("  Dataset v3:", nrow(df), "×", ncol(df), "\n")

df <- df |>
  left_join(agg_final, by = "code_muni")

cat("  Dataset v4:", nrow(df), "×", ncol(df), "\n")

n_com_dados <- sum(!is.na(df$area_ha_alimento_2024))
cat("  Municípios com dados de classificação:", n_com_dados, "/", nrow(df), "\n")

# Exportar
write.csv2(df, path_v4, row.names = FALSE, fileEncoding = "UTF-8")
cat("\n=== CONCLUÍDO! ===\n")
cat("  dados_consolidados_v4.csv:", nrow(df), "×", ncol(df), "\n")

col_novas <- setdiff(colnames(df), colnames(read.csv2(path_v3, nrows=1, fileEncoding="UTF-8")))
cat("\n  Novas colunas adicionadas (", length(col_novas), "):\n")
cat(paste0("    ", col_novas), sep = "\n")
