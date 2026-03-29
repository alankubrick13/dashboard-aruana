if (!require("readxl")) install.packages("readxl", repos="https://cran.r-project.org")
library(readxl)

f23 <- "C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2023.xlsx"
f24 <- "C:/Users/alank/Documents/BASE DE DADOS PROJETO/Bolsa familia 2024.xlsx"

cat("=== SHEETS 2023 ===\n")
cat(paste(excel_sheets(f23), collapse=", "), "\n")

d23 <- read_excel(f23, n_max=5)
cat("\nColunas 2023:\n")
print(colnames(d23))
cat("\nAmostra 2023:\n")
print(d23[, 1:min(8, ncol(d23))])
cat("\nTotal sheets / linhas 2023:", nrow(read_excel(f23)), "\n")

cat("\n=== SHEETS 2024 ===\n")
cat(paste(excel_sheets(f24), collapse=", "), "\n")

d24 <- read_excel(f24, n_max=5)
cat("\nColunas 2024:\n")
print(colnames(d24))
cat("\nAmostra 2024:\n")
print(d24[, 1:min(8, ncol(d24))])
cat("\nTotal linhas 2024:", nrow(read_excel(f24)), "\n")
