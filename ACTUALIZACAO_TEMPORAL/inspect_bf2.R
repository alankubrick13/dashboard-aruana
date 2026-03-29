library(readxl)
library(dplyr)

# Verificar codigo_ibge vs code_muni
d23 <- read_excel("C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2023.xlsx", n_max=10)
cat("codigo_ibge (primeiros 5):", paste(head(d23$codigo_ibge, 5), collapse=", "), "\n")
cat("nchar:", unique(nchar(as.character(head(d23$codigo_ibge, 20)))), "\n")

# Ver code_muni do CSV consolidado
csv <- read.csv2("dados_consolidados_v2.csv", nrows=5, fileEncoding="UTF-8")
cat("code_muni (primeiros 5):", paste(head(csv$code_muni, 5), collapse=", "), "\n")
cat("nchar:", unique(nchar(as.character(head(csv$code_muni, 20)))), "\n")

# Meses disponiveis em cada ficheiro
all23 <- read_excel("C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2023.xlsx")
all24 <- read_excel("C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2024.xlsx")
cat("\nMeses 2023:", paste(sort(unique(all23$anomes_s)), collapse=", "), "\n")
cat("Meses 2024:", paste(sort(unique(all24$anomes_s)), collapse=", "), "\n")
cat("Municipios 2023:", length(unique(all23$codigo_ibge)), "\n")
cat("Municipios 2024:", length(unique(all24$codigo_ibge)), "\n")
