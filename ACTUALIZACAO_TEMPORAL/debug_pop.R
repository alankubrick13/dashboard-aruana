library(sidrar); library(janitor); library(dplyr); library(tidyr)
options(warn=1)

ufs <- c("11","12","13","14","15","16","17",
         "21","22","23","24","25","26","27","28","29",
         "31","32","33","35",
         "41","42","43",
         "50","51","52","53")

pop_list <- list()
for(uf in ufs) {
  cat("UF", uf, "...")
  r <- tryCatch(
    get_sidra(x=9923, period="2022", variable=93, geo="City",
              geo.filter=list(State=uf), classific="c1", category=list(c1=c(1,2,3))),
    error=function(e) { cat(" ERRO:", conditionMessage(e), "\n"); NULL }
  )
  if (!is.null(r)) {
    pop_list[[uf]] <- clean_names(r)
    cat(" OK (", nrow(r), ")\n")
  }
}

pop_raw <- bind_rows(pop_list)
cat("Total linhas:", nrow(pop_raw), "\n")

pop_tidy <- pop_raw |>
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
  filter(!is.na(tipo))

cat("Tipos únicos:", paste(unique(pop_tidy$tipo), collapse=", "), "\n")
cat("Linhas após filtro:", nrow(pop_tidy), "\n")

pop_wide <- pop_tidy |>
  pivot_wider(id_cols=code_muni, names_from=tipo, values_from=val, 
             values_fn=list(val=sum), values_fill=list(val=0))

cat("Colunas pivot:", paste(colnames(pop_wide), collapse=", "), "\n")
cat("Municípios:", nrow(pop_wide), "\n")
cat("class populacao:", class(pop_wide$populacao), "\n")
