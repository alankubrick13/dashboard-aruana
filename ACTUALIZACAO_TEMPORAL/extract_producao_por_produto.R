# ==============================================================================
# SCRIPT: Extração de Produção Agrícola por Produto — Alimento vs Commodity
# Classificação: Portaria MDS nº 966/2024 (Cesta Básica de Alimentos)
# Fonte: SIDRA 5457 (Produção Agrícola Municipal)
#
# OUTPUTS:
#   1. producao_por_produto.csv  — formato longo (município × produto × ano)
#   2. dados_consolidados_v4.csv — dataset consolidado com novas colunas
#
# DEPENDÊNCIAS: sidrar, dplyr, tidyr, janitor
# ==============================================================================

suppressPackageStartupMessages({
  for (pkg in c("sidrar", "dplyr", "tidyr", "janitor")) {
    if (!require(pkg, character.only = TRUE))
      install.packages(pkg, repos = "https://cran.r-project.org")
  }
  library(sidrar); library(dplyr); library(tidyr); library(janitor)
})

# Definir diretório de trabalho = diretório do script
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
cat("Diretório de trabalho:", getwd(), "\n\n")

cat("=== EXTRAÇÃO: PRODUÇÃO POR PRODUTO — ALIMENTO vs COMMODITY ===\n")
cat("Referência legal: Portaria MDS nº 966, de 6 de março de 2024\n\n")

# -----------------------------------------------------------------------
# 1. TABELA DE CLASSIFICAÇÃO
# -----------------------------------------------------------------------

classificacao <- tibble::tribble(
  ~codigo, ~produto,             ~categoria,  ~grupo_portaria,
  # ── ALIMENTO (46 produtos) ──────────────────────────────────────────
  40129,  "Abacate",             "alimento",  "Frutas",
  40092,  "Abacaxi",             "alimento",  "Frutas",
  45982,  "Açaí",                "alimento",  "Frutas",
  40100,  "Alho",                "alimento",  "Legumes e Verduras",
  40101,  "Amendoim",            "alimento",  "Castanhas e Oleaginosas",
  40102,  "Arroz",               "alimento",  "Cereais",
  40103,  "Aveia",               "alimento",  "Cereais",
  40131,  "Azeitona",            "alimento",  "Óleos e Gorduras",
  40136,  "Banana",              "alimento",  "Frutas",
  40104,  "Batata-doce",         "alimento",  "Raízes e Tubérculos",
  40105,  "Batata-inglesa",      "alimento",  "Raízes e Tubérculos",
  40138,  "Cacau",               "alimento",  "Frutas",
  40139,  "Café Total",          "alimento",  "Café, chá, mate e especiarias",
  40140,  "Café Arábica",        "alimento",  "Café, chá, mate e especiarias",
  40141,  "Café Canephora",      "alimento",  "Café, chá, mate e especiarias",
  40106,  "Cana-de-açúcar",      "alimento",  "Açúcares",
  40142,  "Caqui",               "alimento",  "Frutas",
  40143,  "Castanha de caju",    "alimento",  "Castanhas e Oleaginosas",
  40107,  "Cebola",              "alimento",  "Legumes e Verduras",
  40145,  "Coco-da-baía",        "alimento",  "Frutas",
  40147,  "Erva-mate",           "alimento",  "Café, chá, mate e especiarias",
  40110,  "Ervilha",             "alimento",  "Feijões (leguminosas)",
  40111,  "Fava",                "alimento",  "Feijões (leguminosas)",
  40112,  "Feijão",              "alimento",  "Feijões (leguminosas)",
  40148,  "Figo",                "alimento",  "Frutas",
  40149,  "Goiaba",              "alimento",  "Frutas",
  40150,  "Guaraná",             "alimento",  "Frutas",
  40151,  "Laranja",             "alimento",  "Frutas",
  40152,  "Limão",               "alimento",  "Frutas",
  40260,  "Maçã",                "alimento",  "Frutas",
  40261,  "Mamão",               "alimento",  "Frutas",
  40119,  "Mandioca",            "alimento",  "Raízes e Tubérculos",
  40262,  "Manga",               "alimento",  "Frutas",
  40263,  "Maracujá",            "alimento",  "Frutas",
  40264,  "Marmelo",             "alimento",  "Frutas",
  40120,  "Melancia",            "alimento",  "Frutas",
  40121,  "Melão",               "alimento",  "Frutas",
  40122,  "Milho",               "alimento",  "Cereais",
  40267,  "Pera",                "alimento",  "Frutas",
  40268,  "Pêssego",             "alimento",  "Frutas",
  40269,  "Pimenta-do-reino",    "alimento",  "Café, chá, mate e especiarias",
  40271,  "Tangerina",           "alimento",  "Frutas",
  40126,  "Tomate",              "alimento",  "Legumes e Verduras",
  40127,  "Trigo",               "alimento",  "Cereais",
  40273,  "Urucum",              "alimento",  "Especiarias",
  40274,  "Uva",                 "alimento",  "Frutas",
  # ── COMMODITY (21 produtos ativos) ──────────────────────────────────
  40130,  "Algodão arbóreo",     "commodity", "Fibra têxtil",
  40099,  "Algodão herbáceo",    "commodity", "Fibra têxtil",
  40137,  "Borracha",            "commodity", "Industrial",
  40108,  "Centeio",             "commodity", "Industrial/ração",
  40109,  "Cevada",              "commodity", "Industrial (cerveja)",
  40144,  "Chá-da-índia",        "commodity", "Industrial",
  40146,  "Dendê",               "commodity", "Industrial (biodiesel)",
  40113,  "Fumo",                "commodity", "Tabaco",
  40114,  "Girassol",            "commodity", "Commodity oleaginosa",
  40115,  "Juta",                "commodity", "Fibra",
  40116,  "Linho",               "commodity", "Fibra/industrial",
  40117,  "Malva",               "commodity", "Fibra",
  40118,  "Mamona",              "commodity", "Industrial (ricinoquímica)",
  40265,  "Noz",                 "commodity", "Escala mínima",
  40266,  "Palmito",             "commodity", "Extrativismo",
  40123,  "Rami",                "commodity", "Fibra",
  40270,  "Sisal/agave",         "commodity", "Fibra",
  40124,  "Soja",                "commodity", "Commodity exportação",
  40125,  "Sorgo",               "commodity", "Ração animal",
  40128,  "Triticale",           "commodity", "Ração animal",
  40272,  "Tungue",              "commodity", "Industrial"
)

cat("Classificação:\n")
cat("  Alimento:", sum(classificacao$categoria == "alimento"), "produtos\n")
cat("  Commodity:", sum(classificacao$categoria == "commodity"), "produtos\n\n")

# -----------------------------------------------------------------------
# 2. EXTRAÇÃO SIDRA 5457 — por UF com CHUNKING DINÂMICO
# Variáveis: 8331 (área plantada ha), 214 (qtd produzida ton), 215 (valor produção Mil Reais)
#
# A API do SIDRA tem um limite de 100.000 registros por consulta.
# Para UFs grandes (ex: MG ~853 municípios × 67 produtos × 3 vars × 2 anos = ~343k),
# é necessário dividir os produtos em lotes menores.
# -----------------------------------------------------------------------

ufs <- c("11","12","13","14","15","16","17",
         "21","22","23","24","25","26","27","28","29",
         "31","32","33","35",
         "41","42","43",
         "50","51","52","53")

product_codes <- classificacao$codigo
anos <- c("2023", "2024")
n_vars <- 3   # variáveis: 8331, 214, 215
n_anos <- length(anos)

# Número de municípios por UF (Censo 2022 — IBGE)
munis_por_uf <- c(
  "11" = 52,  "12" = 22,  "13" = 62,  "14" = 15,  "15" = 144, "16" = 16,  "17" = 139,
  "21" = 217, "22" = 224, "23" = 184, "24" = 167, "25" = 223, "26" = 185, "27" = 102,
  "28" = 75,  "29" = 417,
  "31" = 853, "32" = 78,  "33" = 92,  "35" = 645,
  "41" = 399, "42" = 295, "43" = 497,
  "50" = 79,  "51" = 141, "52" = 246, "53" = 1
)

# Limite seguro da API (80% de 50k — limite real confirmado pela API)
LIMITE_SEGURO <- 40000

# Função para dividir produtos em chunks que respeitem o limite
chunk_products <- function(product_codes, n_munis, n_vars, n_anos, limite) {
  registros_por_produto <- n_munis * n_vars * n_anos
  max_produtos_por_chunk <- max(1, floor(limite / registros_por_produto))
  n_chunks <- ceiling(length(product_codes) / max_produtos_por_chunk)
  split(product_codes, ceiling(seq_along(product_codes) / max_produtos_por_chunk))
}

cat("[1/4] Extraindo SIDRA 5457 por UF (com chunking dinâmico)...\n")
cat("  ", length(product_codes), "produtos × ", n_vars, " variáveis × ", n_anos, " anos × ", length(ufs), " UFs\n")
cat("  Limite seguro por consulta:", LIMITE_SEGURO, "registros\n\n")

pam_list <- list()
total_linhas <- 0

for (uf in ufs) {
  n_munis <- munis_por_uf[[uf]]
  chunks <- chunk_products(product_codes, n_munis, n_vars, n_anos, LIMITE_SEGURO)
  n_chunks <- length(chunks)

  cat(sprintf("  UF %s (%d munis, %d chunk%s):\n", uf, n_munis, n_chunks,
              ifelse(n_chunks > 1, "s", "")))

  uf_list <- list()
  for (i in seq_along(chunks)) {
    chunk <- chunks[[i]]
    cat(sprintf("    chunk %d/%d (%d produtos)...", i, n_chunks, length(chunk)))

    r <- tryCatch(
      get_sidra(
        x         = 5457,
        period    = anos,
        variable  = c(8331, 214, 215),
        classific = "c782",
        category  = list(c782 = chunk),
        geo       = "City",
        geo.filter = list(State = uf)
      ) |> clean_names(),
      error = function(e) {
        cat(" ERRO:", conditionMessage(e), "\n")
        NULL
      }
    )

    if (!is.null(r) && nrow(r) > 0) {
      uf_list[[i]] <- r
      cat(sprintf(" OK (%d linhas)\n", nrow(r)))
    } else {
      # Retry com pausa maior
      Sys.sleep(5)
      cat(" retry...")
      r2 <- tryCatch(
        get_sidra(
          x         = 5457,
          period    = anos,
          variable  = c(8331, 214, 215),
          classific = "c782",
          category  = list(c782 = chunk),
          geo       = "City",
          geo.filter = list(State = uf)
        ) |> clean_names(),
        error = function(e) { cat(" FALHOU:", conditionMessage(e), "\n"); NULL }
      )
      if (!is.null(r2) && nrow(r2) > 0) {
        uf_list[[i]] <- r2
        cat(sprintf(" OK (%d linhas)\n", nrow(r2)))
      }
    }
    Sys.sleep(2)  # pausa entre chunks para não sobrecarregar a API
  }

  uf_data <- bind_rows(uf_list)
  if (nrow(uf_data) > 0) {
    pam_list[[uf]] <- uf_data
    total_linhas <- total_linhas + nrow(uf_data)
    cat(sprintf("    → UF %s total: %d linhas\n", uf, nrow(uf_data)))
  }
  Sys.sleep(1)  # pausa entre UFs
}

pam_raw <- bind_rows(pam_list)
cat("\nTotal linhas extraídas:", nrow(pam_raw), "\n")

# -----------------------------------------------------------------------
# 3. PROCESSAR E CLASSIFICAR
# -----------------------------------------------------------------------

cat("\n[2/4] Processando e classificando...\n")

# Mapear colunas do SIDRA
col_muni <- grep("municipio_codigo", colnames(pam_raw), value = TRUE)[1]
col_prod <- grep("produto_das_lavouras.*codigo", colnames(pam_raw), value = TRUE)[1]
col_var  <- grep("^variavel_codigo$", colnames(pam_raw), value = TRUE)[1]
col_ano  <- if ("ano_codigo" %in% colnames(pam_raw)) "ano_codigo" else
             grep("^ano", colnames(pam_raw), value = TRUE)[1]
col_val  <- grep("^valor$", colnames(pam_raw), value = TRUE)[1]

cat("  Colunas: muni=", col_muni, " prod=", col_prod,
    " var=", col_var, " ano=", col_ano, " val=", col_val, "\n")

pam_proc <- pam_raw |>
  mutate(
    code_muni   = as.character(.data[[col_muni]]),
    cod_produto = as.integer(.data[[col_prod]]),
    var_codigo  = as.integer(.data[[col_var]]),
    ano         = as.character(.data[[col_ano]]),
    valor       = suppressWarnings(as.numeric(.data[[col_val]]))
  ) |>
  filter(!is.na(valor)) |>
  left_join(classificacao, by = c("cod_produto" = "codigo")) |>
  filter(!is.na(categoria))

# Separar variáveis em colunas
pam_long <- pam_proc |>
  mutate(
    var_nome = case_when(
      var_codigo == 8331 ~ "area_ha",
      var_codigo == 214  ~ "qtd_toneladas",
      var_codigo == 215  ~ "valor_mil_reais",
      TRUE ~ paste0("var_", var_codigo)
    )
  ) |>
  select(code_muni, ano, cod_produto, produto, categoria, grupo_portaria,
         var_nome, valor) |>
  pivot_wider(
    id_cols     = c(code_muni, ano, cod_produto, produto, categoria, grupo_portaria),
    names_from  = var_nome,
    values_from = valor,
    values_fn   = sum
  )

cat("  Registos processados:", nrow(pam_long), "\n")
cat("  Municípios:", n_distinct(pam_long$code_muni), "\n")
cat("  Produtos:", n_distinct(pam_long$cod_produto), "\n")
cat("  Alimento:", sum(pam_long$categoria == "alimento"), "registos\n")
cat("  Commodity:", sum(pam_long$categoria == "commodity"), "registos\n")

# -----------------------------------------------------------------------
# 3a. EXPORTAR FORMATO LONGO
# -----------------------------------------------------------------------

cat("\n  Exportando producao_por_produto.csv ...\n")
write.csv2(pam_long, "producao_por_produto.csv", row.names = FALSE, fileEncoding = "UTF-8")
cat("  Salvo:", nrow(pam_long), "linhas\n")

# -----------------------------------------------------------------------
# 4. AGREGAR POR MUNICÍPIO E INTEGRAR NO DATASET
# -----------------------------------------------------------------------

cat("\n[3/4] Agregando por município...\n")

# Agregação por município × ano × categoria
agg_cat <- pam_long |>
  group_by(code_muni, ano, categoria) |>
  summarise(
    area_ha         = sum(area_ha, na.rm = TRUE),
    qtd_toneladas   = sum(qtd_toneladas, na.rm = TRUE),
    valor_mil_reais = sum(valor_mil_reais, na.rm = TRUE),
    n_produtos      = n_distinct(cod_produto),
    .groups = "drop"
  )

# Pivotar para colunas separadas por categoria e ano
agg_wide <- agg_cat |>
  pivot_wider(
    id_cols     = code_muni,
    names_from  = c(categoria, ano),
    values_from = c(area_ha, qtd_toneladas, valor_mil_reais, n_produtos),
    names_sep   = "_",
    values_fill = 0
  )

# Calcular percentuais
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

# Top 3 produtos por município (por área, ano mais recente)
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
# 5. JOIN COM DATASET CONSOLIDADO V3 → V4
# -----------------------------------------------------------------------

cat("\n[4/4] Integrando com dados_consolidados_v3.csv...\n")

path_v3  <- "dados_consolidados_v3.csv"
path_v4  <- "dados_consolidados_v4.csv"

df <- read.csv2(path_v3, fileEncoding = "UTF-8", stringsAsFactors = FALSE)
df$code_muni <- as.character(df$code_muni)
cat("  Dataset v3:", nrow(df), "×", ncol(df), "\n")

df <- df |>
  left_join(agg_final, by = "code_muni")

cat("  Dataset v4:", nrow(df), "×", ncol(df), "\n")

# Verificação
n_com_dados <- sum(!is.na(df$area_ha_alimento_2024))
cat("\n  Municípios com dados de classificação:", n_com_dados, "/", nrow(df), "\n")

# Sanity check: area classificada vs area total original
if ("area_plantada_ha" %in% colnames(df) &&
    "area_ha_alimento_2024" %in% colnames(df) &&
    "area_ha_commodity_2024" %in% colnames(df)) {
  df_check <- df |>
    filter(!is.na(area_plantada_ha), !is.na(area_ha_alimento_2024)) |>
    mutate(
      area_class = area_ha_alimento_2024 + area_ha_commodity_2024,
      diff_pct = abs(area_class - area_plantada_ha) / area_plantada_ha * 100
    )
  cat("  Diferença média área classificada vs total:", round(mean(df_check$diff_pct, na.rm=TRUE), 2), "%\n")
}

# Exportar
write.csv2(df, path_v4, row.names = FALSE, fileEncoding = "UTF-8")
cat("\n=== CONCLUÍDO! ===\n")
cat("  producao_por_produto.csv:", nrow(pam_long), "linhas\n")
cat("  dados_consolidados_v4.csv:", nrow(df), "×", ncol(df), "\n")

# Listar novas colunas
col_novas <- setdiff(colnames(df), colnames(read.csv2(path_v3, nrows=1, fileEncoding="UTF-8")))
cat("\n  Novas colunas adicionadas (", length(col_novas), "):\n")
cat(paste0("    ", col_novas), sep = "\n")
