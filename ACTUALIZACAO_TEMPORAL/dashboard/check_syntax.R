setwd("c:/Users/alank/Documents/BASE DE DADOS PROJETO/ACTUALIZACAO_TEMPORAL/dashboard")

# Verificar sintaxe
cat("Verificando global.R...\n")
tryCatch(parse("global.R"), error=function(e) cat("ERRO global.R:", conditionMessage(e), "\n"))

cat("Verificando app.R...\n")
tryCatch(parse("app.R"), error=function(e) cat("ERRO app.R:", conditionMessage(e), "\n"))

cat("Carregando global.R...\n")
tryCatch({
  source("global.R")
  cat("global.R OK! Linhas df:", nrow(df), "| UFs:", nrow(df_uf), "\n")
}, error=function(e) cat("ERRO ao carregar global.R:", conditionMessage(e), "\n"))
