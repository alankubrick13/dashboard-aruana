# ==============================================================================
# SCRIPT: Integracao de Dados de Genero e Raca (v5)
# Fontes: perfil_domiciliar_9880.csv e rendimento_trabalho_10281.csv
# Output: dados_consolidados_v5.csv
# ==============================================================================

suppressPackageStartupMessages({
  library(dplyr)
})

cat("=== CONSOLIDAÇÃO V5 (GÊNERO E RAÇA) ===\n")

# Ler bases
df_v4 <- read.csv2("dados_consolidados_v4.csv", fileEncoding="UTF-8", stringsAsFactors=FALSE)
perfil <- read.csv2("perfil_domiciliar_9880.csv", fileEncoding="UTF-8", stringsAsFactors=FALSE)
rendimento <- read.csv2("rendimento_trabalho_10281.csv", fileEncoding="UTF-8", stringsAsFactors=FALSE)

cat("Base original v4:", nrow(df_v4), "municípios,", ncol(df_v4), "colunas\n")

# Garantir tipos
df_v4$code_muni <- as.character(df_v4$code_muni)
perfil$code_muni <- as.character(perfil$code_muni)
rendimento$uf_code <- as.character(rendimento$uf_code)

# Integrar Perfil Domiciliar (Municipal)
df_v5 <- df_v4 |>
  left_join(perfil, by = "code_muni")

cat("Após join perfil:", ncol(df_v5), "colunas\n")

# Integrar Rendimento (Estadual)
# Precisamos do uf_code na base principal (primeiros 2 digitos de code_muni)
df_v5$uf_code_tmp <- substr(df_v5$code_muni, 1, 2)

df_v5 <- df_v5 |>
  left_join(rendimento, by = c("uf_code_tmp" = "uf_code")) |>
  select(-uf_code_tmp)

cat("Após join rendimento:", ncol(df_v5), "colunas\n")

# Exportar
write.csv2(df_v5, "dados_consolidados_v5.csv", row.names = FALSE, fileEncoding = "UTF-8")
cat("=== SUCESSO! Arquivo salvo: dados_consolidados_v5.csv ===\n")
