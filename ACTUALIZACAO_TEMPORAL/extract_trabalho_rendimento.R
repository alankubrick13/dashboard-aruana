# ==============================================================================
# SCRIPT: Extracao de Rendimento do Trabalho (Genero e Raca) - API VERSION
# Fonte: SIDRA 10281 (PNAD Continua)
# ==============================================================================

suppressPackageStartupMessages({
  library(sidrar)
  library(dplyr)
  library(tidyr)
  library(janitor)
})

cat("=== EXTRAÇÃO RENDIMENTO TRABALHO (10281) ===\n")

# Usando API string para evitar erro
# /t/10281/p/2022/v/13536,13537/n3/all/c2/4,5/c86/2776,2777,2779/c1568/120704/c526/15349
api_path <- "/t/10281/p/2022/v/13536,13537/n3/all/c2/4,5/c86/2776,2777,2779/c1568/120704/c526/15349"

raw_10281 <- get_sidra(api = api_path) |> clean_names()

cat("Linhas extraidas:", nrow(raw_10281), "\n")

# Processamento
rend_perfil <- raw_10281 |>
  mutate(
    uf_code = as.character(unidade_da_federacao_codigo),
    var_tipo = case_when(
      grepl("médio", variavel) ~ "media",
      grepl("mediano", variavel) ~ "mediana",
      TRUE ~ "valor"
    ),
    sexo = case_when(
      grepl("Homens", sexo) ~ "h",
      grepl("Mulheres", sexo) ~ "m",
      TRUE ~ "total"
    ),
    raca = case_when(
      grepl("Branca", cor_ou_raca) ~ "branca",
      grepl("Preta", cor_ou_raca) ~ "preta",
      grepl("Parda", cor_ou_raca) ~ "parda",
      TRUE ~ "outra"
    )
  ) |>
  pivot_wider(
    id_cols = uf_code,
    names_from = c(var_tipo, sexo, raca),
    values_from = valor,
    names_prefix = "rend_"
  )

write.csv2(rend_perfil, "rendimento_trabalho_10281.csv", row.names = FALSE)
cat("Concluido! Arquivo salvo: rendimento_trabalho_10281.csv\n")
