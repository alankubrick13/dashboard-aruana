# ==============================================================================
# global.R — Dados, geometrias e funções auxiliares
# Dashboard: Observatório da Fome | ONG Aruana
# ==============================================================================

suppressPackageStartupMessages({
  pkgs <- c("shiny","bslib","dplyr","ggplot2","plotly","leaflet",
            "sf","geobr","scales","DT","tidyr","tibble","bsicons")
  for (p in pkgs) {
    if (!require(p, character.only=TRUE, quietly=TRUE))
      install.packages(p, repos="https://cran.r-project.org", quiet=TRUE)
    library(p, character.only=TRUE, quietly=TRUE)
  }
})

# ── Cores ──────────────────────────────────────────────────────────────────────
COR_ROXO   <- "#7237cb"
COR_ROXO2  <- "#9b6de0"
COR_CREME  <- "#fd722cff"
COR_VERDE  <- "#4c734c"
COR_VERDE2 <- "#6fa06f"
COR_DARK   <- "#1e1e2e"
COR_WARN   <- "#e07b3a"
COR_PERIGO <- "#c0392b"
COR_GRID   <- "#e8e3f5"

CORES_REGIOES <- c(
  "Norte"        = "#7237cb",
  "Nordeste"     = "#c0392b",
  "Centro-Oeste" = "#e07b3a",
  "Sudeste"      = "#27ae60",
  "Sul"          = "#2980b9"
)

# ── Carregar dados ─────────────────────────────────────────────────────────────
csv_path <- file.path(dirname(getwd()), "dados_consolidados_v3.csv")
if (!file.exists(csv_path))
  csv_path <- "dados_consolidados_v3.csv"

df <- read.csv2(csv_path, fileEncoding="UTF-8", stringsAsFactors=FALSE) |>
  mutate(
    code_muni        = as.character(code_muni),
    populacao        = as.numeric(populacao),
    pop_urbana       = as.numeric(pop_urbana),
    pop_rural        = as.numeric(pop_rural),
    perc_urbana      = as.numeric(perc_urbana),
    perc_rural       = as.numeric(perc_rural),
    area_plantada_ha = as.numeric(area_plantada_ha),
    lat              = as.numeric(lat),
    lon              = as.numeric(lon),
    across(starts_with("total_") | starts_with("seg_") |
           starts_with("inseg_") | starts_with("bf_"), as.numeric)
  )

# ── Agregação por UF ───────────────────────────────────────────────────────────
df_uf <- df |>
  group_by(abbrev_state, name_region) |>
  summarise(
    n_municipios         = n(),
    populacao            = sum(populacao, na.rm=TRUE),
    pop_urbana           = sum(pop_urbana, na.rm=TRUE),
    pop_rural            = sum(pop_rural, na.rm=TRUE),
    area_plantada_ha     = sum(area_plantada_ha, na.rm=TRUE),
    bf_familias_2023     = sum(bf_qtd_familias_media_2023, na.rm=TRUE),
    bf_familias_2024     = sum(bf_qtd_familias_media_2024, na.rm=TRUE),
    bf_valor_2023        = sum(bf_valor_repassado_media_2023, na.rm=TRUE),
    bf_valor_2024        = sum(bf_valor_repassado_media_2024, na.rm=TRUE),
    bf_vlr_medio_2023    = mean(bf_vlr_medio_benef_media_2023, na.rm=TRUE),
    bf_vlr_medio_2024    = mean(bf_vlr_medio_benef_media_2024, na.rm=TRUE),
    across(c(seg_perc_dom_2023, seg_perc_dom_2024,
             inseg_perc_dom_2023, inseg_perc_dom_2024,
             inseg_leve_perc_dom_2023, inseg_leve_perc_dom_2024,
             inseg_moderada_perc_dom_2023, inseg_moderada_perc_dom_2024,
             inseg_grave_perc_dom_2023, inseg_grave_perc_dom_2024,
             inseg_grave_mor_mil_2023, inseg_grave_mor_mil_2024,
             inseg_mor_mil_2023, inseg_mor_mil_2024,
             inseg_leve_dom_mil_2023, inseg_leve_dom_mil_2024,
             inseg_moderada_dom_mil_2023, inseg_moderada_dom_mil_2024,
             inseg_grave_dom_mil_2023, inseg_grave_dom_mil_2024,
             seg_dom_mil_2023, seg_dom_mil_2024,
             inseg_dom_mil_2023, inseg_dom_mil_2024,
             inseg_leve_mor_mil_2023, inseg_leve_mor_mil_2024,
             inseg_moderada_mor_mil_2023, inseg_moderada_mor_mil_2024,
             seg_mor_mil_2023, seg_mor_mil_2024,
             total_dom_mil_2023, total_dom_mil_2024), first),
    .groups = "drop"
  ) |>
  mutate(
    perc_rural_uf      = pop_rural / populacao * 100,
    perc_urbana_uf     = pop_urbana / populacao * 100,
    area_per_capita    = area_plantada_ha / populacao,
    bf_cobertura_2024  = bf_familias_2024 / populacao * 1000,
    bf_cobertura_2023  = bf_familias_2023 / populacao * 1000,
    delta_inseg_grave  = inseg_grave_perc_dom_2024 - inseg_grave_perc_dom_2023,
    delta_inseg        = inseg_perc_dom_2024 - inseg_perc_dom_2023
  )

# ── Geometrias dos estados ─────────────────────────────────────────────────────
rds_path <- file.path(tempdir(), "estados_sf.rds")
if (file.exists(rds_path)) {
  estados_sf <- readRDS(rds_path)
} else {
  estados_sf <- geobr::read_state(year=2020, showProgress=FALSE)
  saveRDS(estados_sf, rds_path)
}
estados_sf <- estados_sf |>
  left_join(df_uf, by="abbrev_state")

# ── Indicadores nacionais ──────────────────────────────────────────────────────
pop_total_br     <- sum(df_uf$populacao, na.rm=TRUE)
inseg_grave_br24 <- weighted.mean(df_uf$inseg_grave_perc_dom_2024,
                                   df_uf$total_dom_mil_2024, na.rm=TRUE)
inseg_grave_br23 <- weighted.mean(df_uf$inseg_grave_perc_dom_2023,
                                   df_uf$total_dom_mil_2023, na.rm=TRUE)
inseg_total_br24 <- weighted.mean(df_uf$inseg_perc_dom_2024,
                                   df_uf$total_dom_mil_2024, na.rm=TRUE)
mor_fome_br24    <- sum(df_uf$inseg_grave_mor_mil_2024, na.rm=TRUE) * 1000
bf_familias_br24 <- sum(df_uf$bf_familias_2024, na.rm=TRUE)
bf_familias_br23 <- sum(df_uf$bf_familias_2023, na.rm=TRUE)
bf_valor_br24    <- sum(df_uf$bf_valor_2024, na.rm=TRUE)
bf_vlr_medio_br24 <- mean(df_uf$bf_vlr_medio_2024, na.rm=TRUE)

# ── Helper: layout plotly ────────────────────────────────────────────────────
plotly_layout <- function(p, ...) {
  p |> layout(
    paper_bgcolor = COR_CREME,
    plot_bgcolor  = COR_CREME,
    font   = list(family="Inter, sans-serif", color=COR_DARK),
    margin = list(l=10, r=10, t=30, b=10),
    ...
  )
}

# ── Helper: mapa coroplético por UF ──────────────────────────────────────────
mapa_uf <- function(coluna, titulo, pal_low=COR_CREME, pal_high=COR_ROXO,
                    sufixo="", fmt="%.1f", na_cor="#cccccc") {
  dados <- estados_sf
  dados$VAR <- dados[[coluna]]

  p <- ggplot(dados) +
    geom_sf(
      aes(fill=VAR,
          text=paste0("<b>", abbrev_state, "</b><br>",
                      titulo, ": ", sprintf(fmt, VAR), sufixo)),
      color="white", linewidth=0.4
    ) +
    scale_fill_gradient(low=pal_low, high=pal_high,
                        name=titulo, na.value=na_cor,
                        labels=function(x) paste0(sprintf(fmt, x), sufixo)) +
    theme_void() +
    theme(
      legend.position  = "bottom",
      legend.title     = element_text(size=9, color=COR_DARK),
      legend.text      = element_text(size=8),
      plot.background  = element_rect(fill=COR_CREME, color=NA),
      legend.background = element_rect(fill=COR_CREME, color=NA),
      legend.key.height = unit(0.4, "cm")
    )

  ggplotly(p, tooltip="text") |>
    plotly_layout(legend=list(orientation="h", y=-0.08, x=0.1))
}

# ── Helper: scatter plot por UF ───────────────────────────────────────────────
scatter_uf <- function(x_col, y_col, x_lab, y_lab,
                       x_suf="", y_suf="", x_fmt="%.1f", y_fmt="%.1f") {
  d <- df_uf |>
    mutate(X=.data[[x_col]], Y=.data[[y_col]]) |>
    filter(!is.na(X), !is.na(Y))

  plot_ly(d,
    x=~X, y=~Y,
    text=~abbrev_state,
    color=~name_region,
    colors=CORES_REGIOES,
    type="scatter", mode="markers+text",
    textposition="top center",
    marker=list(size=12, opacity=0.85,
                line=list(color="white", width=1.5)),
    hovertemplate=paste0(
      "<b>%{text}</b><br>",
      x_lab, ": ", x_fmt, x_suf, "<br>",
      y_lab, ": ", y_fmt, y_suf,
      "<extra></extra>"
    )
  ) |>
    plotly_layout(
      xaxis=list(title=paste0(x_lab, if_else(x_suf!="", paste0(" (", x_suf, ")"), "")),
                 gridcolor=COR_GRID),
      yaxis=list(title=paste0(y_lab, if_else(y_suf!="", paste0(" (", y_suf, ")"), "")),
                 gridcolor=COR_GRID),
      legend=list(title=list(text="Região"), orientation="v",
                  font=list(size=10))
    )
}

# ── Tema bslib ─────────────────────────────────────────────────────────────────
tema_app <- bs_theme(
  version      = 5,
  bg           = COR_CREME,
  fg           = "#1a1a2e",
  primary      = COR_ROXO,
  secondary    = COR_VERDE,
  success      = COR_VERDE,
  warning      = COR_WARN,
  danger       = COR_PERIGO,
  base_font    = font_google("Inter"),
  heading_font = font_google("Inter"),
  "navbar-bg"  = COR_DARK,
  "card-border-radius" = "12px",
  "card-cap-bg" = "white"
)
