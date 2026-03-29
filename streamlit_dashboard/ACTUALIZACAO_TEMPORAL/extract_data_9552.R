# ==============================================================================
# SCRIPT DE EXTRACAO TEMPORAL - VERSAO FINAL VALIDADA (V13)
# Fonte: SIDRA 9923 (Pop Censo 2022), 5457 (Agro 2024), 9552 (Fome 2023-2024)
# Codes c1 confirmados: 6795=Total, 1=Urbana, 2=Rural
# Codes c12404:
#   109106 = Total
#   109098 = Com seguranca alimentar
#   109099 = Com inseguranca alimentar (total)
#   109100 = Com inseguranca alimentar leve
#   109101 = Com inseguranca alimentar moderada
#   109102 = Com inseguranca alimentar grave
# Variaveis:
#   162   = Domicilios (Mil unidades)
#   5123  = Coeficiente de variacao - Domicilios (%)
#   9784  = Distribuicao percentual dos domicilios (%)
#   9785  = CV - Distribuicao percentual dos domicilios (%)
#   10114 = Moradores em domicilios (Mil pessoas)
#   10116 = CV - Moradores em domicilios (%)
#   10117 = Distribuicao percentual dos moradores (%)
#   10118 = CV - Distribuicao percentual dos moradores (%)
# ==============================================================================

suppressPackageStartupMessages({
  if (!require("sidrar")) install.packages("sidrar", repos="https://cran.r-project.org")
  if (!require("dplyr")) install.packages("dplyr", repos="https://cran.r-project.org")
  if (!require("tidyr")) install.packages("tidyr", repos="https://cran.r-project.org")
  if (!require("geobr")) install.packages("geobr", repos="https://cran.r-project.org")
  if (!require("janitor")) install.packages("janitor", repos="https://cran.r-project.org")
  library(sidrar); library(dplyr); library(tidyr); library(geobr); library(janitor)
})

cat("=== EXTRACAO INICIADA ===\n")

ufs <- c("11","12","13","14","15","16","17",
         "21","22","23","24","25","26","27","28","29",
         "31","32","33","35",
         "41","42","43",
         "50","51","52","53")

# -----------------------------------------------------------------------
# FASE 1: POPULACAO (Tabela 9923, Censo 2022)
# c1: 6795=Total, 1=Urbana, 2=Rural
# -----------------------------------------------------------------------
cat("\n[1/4] Populacao por UF (Tabela 9923)...\n")
pop_list <- list()
for (uf in ufs) {
  cat("  UF", uf, "...")
  r <- tryCatch(
    get_sidra(x=9923, period="2022", variable=93, geo="City",
              geo.filter=list(State=uf),
              classific="c1",
              category=list(c1=c(6795, 1, 2))),
    error=function(e) { cat(" ERRO:", conditionMessage(e), "\n"); NULL }
  )
  if (!is.null(r)) {
    pop_list[[uf]] <- clean_names(r)
    cat(" OK (", nrow(r), ")\n")
  }
}

pop_raw <- bind_rows(pop_list)
cat("Total linhas pop:", nrow(pop_raw), "\n")

pop_wide <- pop_raw |>
  select(code_muni=municipio_codigo, dom=situacao_do_domicilio, val=valor) |>
  mutate(
    code_muni = as.character(code_muni),
    tipo = case_when(
      grepl("Total",  dom, ignore.case=TRUE) ~ "populacao",
      grepl("Urbana", dom, ignore.case=TRUE) ~ "pop_urbana",
      grepl("Rural",  dom, ignore.case=TRUE) ~ "pop_rural",
      TRUE ~ NA_character_
    )
  ) |>
  filter(!is.na(tipo)) |>
  pivot_wider(id_cols=code_muni, names_from=tipo, values_from=val,
              values_fn=sum, values_fill=0) |>
  mutate(
    populacao  = as.numeric(populacao),
    pop_urbana = as.numeric(pop_urbana),
    pop_rural  = as.numeric(pop_rural),
    perc_urbana = if_else(populacao > 0, round(pop_urbana / populacao * 100, 2), NA_real_),
    perc_rural  = if_else(populacao > 0, round(pop_rural  / populacao * 100, 2), NA_real_)
  )
cat("Municipios pop:", nrow(pop_wide), "\n")

# -----------------------------------------------------------------------
# FASE 2: SEGURANCA ALIMENTAR COMPLETA (Tabela 9552 / C12404)
# 6 categorias x 8 variaveis x 2 anos (2023, 2024)
# -----------------------------------------------------------------------
cat("\n[2/4] Seguranca Alimentar Completa (9552 / C12404)...\n")

# Codigos de categoria -> nome abreviado
cat_codes <- c(109106, 109098, 109099, 109100, 109101, 109102)
cat_names <- c(
  "109106" = "total",
  "109098" = "seg",
  "109099" = "inseg",
  "109100" = "inseg_leve",
  "109101" = "inseg_moderada",
  "109102" = "inseg_grave"
)

# Codigos de variavel -> nome abreviado
var_codes <- c(162, 5123, 9784, 9785, 10114, 10116, 10117, 10118)
var_names <- c(
  "162"   = "dom_mil",
  "5123"  = "cv_dom",
  "9784"  = "perc_dom",
  "9785"  = "cv_perc_dom",
  "10114" = "mor_mil",
  "10116" = "cv_mor",
  "10117" = "perc_mor",
  "10118" = "cv_perc_mor"
)

cat("  Extraindo tabela 9552 (todas variaveis e categorias)...\n")
fome_raw <- tryCatch(
  get_sidra(
    x         = 9552,
    period    = c("2023", "2024"),
    variable  = var_codes,
    classific = "c12404",
    category  = list(c12404 = cat_codes),
    geo       = "State"
  ) |> clean_names(),
  error = function(e) {
    cat("  ERRO na extracao principal:", conditionMessage(e), "\n")
    NULL
  }
)

# Fallback: variavel por variavel
if (is.null(fome_raw) || nrow(fome_raw) == 0) {
  cat("  Tentando extracao variavel por variavel...\n")
  fome_list2 <- list()
  for (vcode in as.character(var_codes)) {
    cat("  Variavel", vcode, "(", var_names[[vcode]], ")...")
    tmp <- tryCatch(
      get_sidra(
        x         = 9552,
        period    = c("2023", "2024"),
        variable  = as.integer(vcode),
        classific = "c12404",
        category  = list(c12404 = cat_codes),
        geo       = "State"
      ) |> clean_names(),
      error = function(e) { cat(" ERRO:", conditionMessage(e), "\n"); NULL }
    )
    if (!is.null(tmp)) {
      fome_list2[[vcode]] <- tmp
      cat(" OK (", nrow(tmp), ")\n")
    }
  }
  fome_raw <- bind_rows(fome_list2)
}

cat("  Linhas extraidas:", nrow(fome_raw), "\n")
cat("  Colunas:\n  ", paste(colnames(fome_raw), collapse=", "), "\n")

# Identificar colunas chave
col_cat <- grep("situacao_de_seguranca.*codigo$|food_security.*code$",
                colnames(fome_raw), value=TRUE)[1]
# Se nao encontrou com _codigo, pegar a coluna numerica da classificacao
if (is.na(col_cat)) {
  col_cat <- grep("situacao_de_seguranca_alimentar.*codigo",
                  colnames(fome_raw), value=TRUE)[1]
}

col_var <- grep("^variavel_codigo$|^variable_code$",
                colnames(fome_raw), value=TRUE)[1]

col_uf  <- grep("^unidade_da_federacao_codigo$|^state_code$",
                colnames(fome_raw), value=TRUE)[1]

# Para o ano: preferir ano_codigo; se nao existir, usar ano
col_ano_raw <- colnames(fome_raw)
if ("ano_codigo" %in% col_ano_raw) {
  col_ano <- "ano_codigo"
} else {
  col_ano <- grep("^ano", col_ano_raw, value=TRUE)[1]
}

col_val <- grep("^valor$", colnames(fome_raw), value=TRUE)[1]

cat("  Mapeamento -> categoria:", col_cat, "| variavel:", col_var,
    "| uf:", col_uf, "| ano:", col_ano, "| valor:", col_val, "\n")

# Processar
fome_proc <- fome_raw |>
  mutate(
    uf_code   = as.character(.data[[col_uf]]),
    ano_ext   = as.character(.data[[col_ano]]),
    var_code  = as.character(.data[[col_var]]),
    valor_ext = suppressWarnings(as.numeric(.data[[col_val]])),
    # Mapear codigo da categoria para nome abreviado (codigo numerico)
    cat_code_str = as.character(.data[[col_cat]]),
    categoria = dplyr::recode(cat_code_str, !!!cat_names, .default = "outro"),
    # Mapear codigo da variavel para nome abreviado
    var_nome  = dplyr::recode(var_code, !!!var_names, .default = paste0("var_", var_code))
  )

cat("  Categorias encontradas:", paste(unique(fome_proc$categoria), collapse=", "), "\n")
cat("  Variaveis encontradas:", paste(unique(fome_proc$var_nome), collapse=", "), "\n")
cat("  Anos encontrados:", paste(unique(fome_proc$ano_ext), collapse=", "), "\n")

# Pivotar: nome da coluna = <categoria>_<var_nome>_<ano>
fome_wide <- fome_proc |>
  filter(categoria != "outro") |>
  select(uf_code, ano_ext, categoria, var_nome, valor_ext) |>
  pivot_wider(
    id_cols     = uf_code,
    names_from  = c(categoria, var_nome, ano_ext),
    values_from = valor_ext,
    names_sep   = "_"
  )

cat("UFs fome:", nrow(fome_wide), "\n")
cat("Colunas fome_wide (", ncol(fome_wide)-1, "variaveis de seguranca):\n")
cat(paste0("  ", setdiff(colnames(fome_wide), "uf_code")), sep="\n")

# -----------------------------------------------------------------------
# FASE 3: AGRICULTURA (Tabela 5457)
# -----------------------------------------------------------------------
cat("\n[3/4] Agricultura (5457)...\n")
pam_clean <- get_sidra(x=5457, period="2024", variable=8331,
                       classific="c782", category=list(c782=0), geo="City") |>
  clean_names() |>
  mutate(code_muni=as.character(municipio_codigo)) |>
  select(code_muni, area_plantada_ha=valor)
cat("Municipios agro:", nrow(pam_clean), "\n")

# -----------------------------------------------------------------------
# FASE 4: METADADOS E COORDENADAS (geobr)
# -----------------------------------------------------------------------
cat("\n[4/4] Metadados geobr...\n")
muni_sf <- read_municipality(year=2022, showProgress=FALSE)
muni_meta <- as.data.frame(muni_sf) |>
  mutate(code_muni=as.character(code_muni)) |>
  select(code_muni, name_muni, abbrev_state, name_region)

muni_coords <- muni_sf |>
  sf::st_centroid() |>
  sf::st_coordinates() |>
  as.data.frame() |>
  rename(lon=X, lat=Y) |>
  mutate(code_muni=as.character(muni_sf$code_muni))

# -----------------------------------------------------------------------
# CONSOLIDACAO FINAL
# -----------------------------------------------------------------------
cat("\nConsolidando...\n")
df_final <- muni_meta |>
  left_join(pop_wide,    by="code_muni") |>
  left_join(pam_clean,   by="code_muni") |>
  mutate(uf_code=substr(code_muni, 1, 2)) |>
  left_join(fome_wide,   by="uf_code") |>
  left_join(muni_coords, by="code_muni")

# Selecionar e ordenar colunas finais
col_base <- c("code_muni","name_muni","abbrev_state","name_region",
              "populacao","pop_urbana","pop_rural","perc_urbana","perc_rural",
              "area_plantada_ha","lat","lon")

# Todas as colunas de seguranca alimentar (tudo exceto col_base e uf_code)
col_seg <- setdiff(colnames(df_final), c(col_base, "uf_code"))

df_export <- df_final |> select(all_of(c(col_base, col_seg)))

cat("Municipios finais:", nrow(df_export), "\n")
cat("Total colunas:", ncol(df_export), "\n")
cat("Colunas de seguranca alimentar (", length(col_seg), "):\n")
cat(paste0("  ", col_seg), sep="\n")

# -----------------------------------------------------------------------
# EXPORTACAO
# -----------------------------------------------------------------------
output_path <- "dados_consolidados_v2.csv"
write.csv2(df_export, output_path, row.names=FALSE, fileEncoding="UTF-8")
cat("\n=== CONCLUIDO! Arquivo salvo:", output_path, "===\n")
cat("Dimensoes finais:", nrow(df_export), "x", ncol(df_export), "\n")
