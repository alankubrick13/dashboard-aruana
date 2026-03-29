# ==============================================================================
# SCRIPT: Integrar Dados do Bolsa Familia ao Dataset Consolidado
# Fonte: Bolsa familia 2023.xlsx e 2024.xlsx
# Chave: codigo_ibge (6 dig) <-> substr(code_muni, 1, 6) (7 dig)
# Logica: media anual dos meses disponiveis por municipio
# Output: dados_consolidados_v3.csv
# ==============================================================================

suppressPackageStartupMessages({
  if (!require("readxl")) install.packages("readxl", repos="https://cran.r-project.org")
  if (!require("dplyr"))  install.packages("dplyr",  repos="https://cran.r-project.org")
  library(readxl); library(dplyr)
})

cat("=== INTEGRACAO BOLSA FAMILIA ===\n")

# -----------------------------------------------------------------------
# Caminhos dos ficheiros
# -----------------------------------------------------------------------
path_bf23  <- "C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2023.xlsx"
path_bf24  <- "C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2024.xlsx"
path_csv   <- "dados_consolidados_v2.csv"
path_out   <- "dados_consolidados_v3.csv"

# -----------------------------------------------------------------------
# Ler o dataset consolidado
# -----------------------------------------------------------------------
cat("\n[1/4] Lendo dataset consolidado...\n")
df <- read.csv2(path_csv, fileEncoding="UTF-8", stringsAsFactors=FALSE)
df$code_muni <- as.character(df$code_muni)
# Criar chave de 6 digitos para join com codigo_ibge do Bolsa Familia
df$ibge6 <- substr(df$code_muni, 1, 6)
cat("  Municipios no dataset:", nrow(df), "\n")
cat("  Colunas actuais:", ncol(df), "\n")

# -----------------------------------------------------------------------
# Funcao: ler, calcular media anual por municipio
# -----------------------------------------------------------------------
calc_media_anual <- function(path, ano_label) {
  cat("\n[*] Lendo:", basename(path), "\n")
  
  raw <- read_excel(path)
  raw$codigo_ibge <- as.character(as.integer(raw$codigo_ibge))
  raw$anomes_s    <- as.character(raw$anomes_s)
  
  # Extrair ano e mes da coluna anomes_s (formato: YYYYMM)
  raw$ano_ext <- substr(raw$anomes_s, 1, 4)
  raw$mes_ext <- as.integer(substr(raw$anomes_s, 5, 6))
  
  meses_disp <- sort(unique(as.integer(raw$anomes_s)))
  cat("  Meses disponiveis:", paste(meses_disp, collapse=", "), "\n")
  cat("  Municipios:", length(unique(raw$codigo_ibge)), "\n")
  cat("  Total linhas:", nrow(raw), "\n")
  
  # Calcular media por municipio (sobre todos os meses disponiveis desse ano)
  media_anual <- raw |>
    group_by(codigo_ibge) |>
    summarise(
      n_meses = n(),  # quantos meses estao disponiveis
      # Quantidades: soma total / n_meses (= media mensal)
      bf_qtd_familias_media  = mean(qtd_familias_beneficiarias_bolsa_familia_s,
                                    na.rm = TRUE),
      # Valor repassado: media mensal
      bf_valor_repassado_media = mean(valor_repassado_bolsa_familia_s,
                                      na.rm = TRUE),
      # Valor medio beneficio: media dos valores medios mensais
      bf_vlr_medio_benef_media = mean(pbf_vlr_medio_benef_f,
                                      na.rm = TRUE),
      # Totais anuais (soma de todos os meses disponiveis)
      bf_qtd_familias_total    = sum(qtd_familias_beneficiarias_bolsa_familia_s,
                                     na.rm = TRUE),
      bf_valor_repassado_total = sum(valor_repassado_bolsa_familia_s,
                                     na.rm = TRUE),
      .groups = "drop"
    )
  
  # Renomear colunas adicionando sufixo do ano
  nomes_antigos <- setdiff(colnames(media_anual), c("codigo_ibge", "n_meses"))
  nomes_novos   <- paste0(nomes_antigos, "_", ano_label)
  media_anual   <- media_anual |>
    rename_with(~ paste0(.x, "_", ano_label), all_of(nomes_antigos)) |>
    rename_with(~ paste0("bf_n_meses_", ano_label), "n_meses")
  
  cat("  Colunas geradas:", paste(setdiff(colnames(media_anual), "codigo_ibge"), collapse=", "), "\n")
  return(media_anual)
}

# -----------------------------------------------------------------------
# [2/4] Processar 2023
# -----------------------------------------------------------------------
cat("\n[2/4] Processando Bolsa Familia 2023...\n")
bf23 <- calc_media_anual(path_bf23, "2023")
cat("  Municipios com dados 2023:", nrow(bf23), "\n")

# -----------------------------------------------------------------------
# [3/4] Processar 2024
# -----------------------------------------------------------------------
cat("\n[3/4] Processando Bolsa Familia 2024...\n")
bf24 <- calc_media_anual(path_bf24, "2024")
cat("  Municipios com dados 2024:", nrow(bf24), "\n")

# -----------------------------------------------------------------------
# [4/4] Join com dataset consolidado
# -----------------------------------------------------------------------
cat("\n[4/4] Fazendo join com dataset consolidado...\n")

# Join 2023
df <- df |>
  left_join(bf23, by=c("ibge6"="codigo_ibge"))
cat("  Apos join 2023:", ncol(df), "colunas\n")

# Join 2024
df <- df |>
  left_join(bf24, by=c("ibge6"="codigo_ibge"))
cat("  Apos join 2024:", ncol(df), "colunas\n")

# Remover coluna auxiliar ibge6
df$ibge6 <- NULL

# Verificar cobertura do join
match_23 <- sum(!is.na(df$bf_qtd_familias_media_2023))
match_24 <- sum(!is.na(df$bf_qtd_familias_media_2024))
cat("\n  Municipios com dados BF 2023:", match_23, "/", nrow(df), "\n")
cat("  Municipios com dados BF 2024:", match_24, "/", nrow(df), "\n")

# Colunas adicionadas
col_bf <- grep("^bf_", colnames(df), value=TRUE)
cat("\n  Colunas do Bolsa Familia adicionadas (", length(col_bf), "):\n")
cat(paste0("    ", col_bf), sep="\n")

# -----------------------------------------------------------------------
# Exportar
# -----------------------------------------------------------------------
cat("\nExportando para:", path_out, "\n")
write.csv2(df, path_out, row.names=FALSE, fileEncoding="UTF-8")
cat("\n=== CONCLUIDO! ===\n")
cat("Dimensoes finais:", nrow(df), "x", ncol(df), "\n")
