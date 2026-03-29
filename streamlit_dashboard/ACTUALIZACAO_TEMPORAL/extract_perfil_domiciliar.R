# ==============================================================================
# SCRIPT: Extracao de Perfil Domiciliar (Genero e Raca) - UF LOOP VERSION
# Fonte: SIDRA 9880 (Censo 2022)
# ==============================================================================

suppressPackageStartupMessages({
  library(sidrar)
  library(dplyr)
  library(tidyr)
  library(janitor)
})

cat("=== EXTRAÇÃO PERFIL DOMICILIAR (9880) ===\n")

ufs <- c("11","12","13","14","15","16","17",
         "21","22","23","24","25","26","27","28","29",
         "31","32","33","35","41","42","43","50","51","52","53")

perfil_list <- list()

for (uf in ufs) {
  cat("Processando UF:", uf, "...")
  
  # Usando API string para evitar erro de vetor no get_sidra
  # /t/9880/p/2022/v/800/n6/all/c11561/100680,100681/c12237/104571,104572,104573,104574,104575/c125/2932/c68/9902/c11562/72593
  api_path <- paste0("/t/9880/p/2022/v/800/n6/in%20n3%20", uf, 
                     "/c11561/100680,100681/c12237/104571,104572,104573,104574,104575",
                     "/c125/2932/c68/9902/c11562/72593")
                     
  res <- tryCatch(
    get_sidra(api = api_path) |> clean_names(),
    error = function(e) { cat(" ERRO:", conditionMessage(e), "\n"); NULL }
  )
  
  if (!is.null(res)) {
    perfil_list[[uf]] <- res
    cat(" OK (", nrow(res), " linhas)\n")
  }
}

raw_9880 <- bind_rows(perfil_list)
cat("Total linhas extraidas:", nrow(raw_9880), "\n")

# Processamento
dom_perfil <- raw_9880 |>
  mutate(
    code_muni = as.character(municipio_codigo),
    sexo = case_when(
      grepl("Homens", sexo_da_pessoa_responsavel_pelo_domicilio) ~ "h",
      grepl("Mulheres", sexo_da_pessoa_responsavel_pelo_domicilio) ~ "m",
      TRUE ~ "total"
    ),
    raca = case_when(
      grepl("Branca", cor_ou_raca_da_pessoa_responsavel_pelo_domicilio) ~ "branca",
      grepl("Preta", cor_ou_raca_da_pessoa_responsavel_pelo_domicilio) ~ "preta",
      grepl("Amarela", cor_ou_raca_da_pessoa_responsavel_pelo_domicilio) ~ "amarela",
      grepl("Parda", cor_ou_raca_da_pessoa_responsavel_pelo_domicilio) ~ "parda",
      grepl("Indígena", cor_ou_raca_da_pessoa_responsavel_pelo_domicilio) ~ "indigena",
      TRUE ~ "outra"
    )
  ) |>
  pivot_wider(
    id_cols = code_muni,
    names_from = c(sexo, raca),
    values_from = valor,
    names_prefix = "dom_resp_"
  )

write.csv2(dom_perfil, "perfil_domiciliar_9880.csv", row.names = FALSE)
cat("Concluido! Arquivo salvo: perfil_domiciliar_9880.csv\n")
