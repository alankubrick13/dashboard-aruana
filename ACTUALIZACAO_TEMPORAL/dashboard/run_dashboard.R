setwd("c:/Users/alank/Documents/BASE DE DADOS PROJETO/ACTUALIZACAO_TEMPORAL/dashboard")
source("global.R")
cat("--- global.R OK ---\n")
shiny::runApp(".", port=7777, launch.browser=TRUE)
