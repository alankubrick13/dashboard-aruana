# ==============================================================================
# app.R — Observatório da Fome no Brasil | ONG Aruana
# Abas: Sobre · Panorama · Segurança Alimentar · Bolsa Família · Produção · Correlações
# ==============================================================================

# ── Auxiliar: bloco de secção ──────────────────────────────────────────────────
section_header <- function(titulo, subtitulo=NULL) {
  tagList(
    tags$div(class="section-header",
      tags$h5(class="section-title", titulo),
      if (!is.null(subtitulo)) tags$p(class="section-sub", subtitulo)
    )
  )
}

# ── UI ─────────────────────────────────────────────────────────────────────────
ui <- page_navbar(
  title = tags$div(
    style="display:flex;align-items:center;gap:12px;",
    tags$img(src="logo_aruana.svg", height="32px",
             style="filter:brightness(0) invert(1);opacity:0.95;"),
    tags$div(
      tags$span("Observatório da Fome",
                style="font-weight:700;color:#f9f7f6;font-size:0.97rem;display:block;line-height:1.1;"),
      tags$span("Brasil · 2023–2024",
                style="font-weight:300;color:#b0aac0;font-size:0.73rem;")
    )
  ),
  theme        = tema_app,
  window_title = "Observatório da Fome — ONG Aruana",
  fillable     = FALSE,
  header = tags$head(
    tags$link(rel="stylesheet", href="styles.css"),
    tags$link(rel="icon", href="logo_aruana.svg")
  ),

  # ── TAB 0: Sobre a Plataforma ───────────────────────────────────────────────
  nav_panel("Sobre",
    div(class="sobre-hero",
      div(class="sobre-hero-inner",
        tags$img(src="logo_aruana.svg", height="56px", class="sobre-logo"),
        tags$h1("Observatório da Fome no Brasil", class="sobre-titulo"),
        tags$p("Uma plataforma analítica da ONG Aruana para monitoramento da insegurança alimentar,
                cobertura de política social e produção agrícola nos 5.570 municípios brasileiros.",
               class="sobre-subtitulo")
      )
    ),
    br(),
    layout_columns(col_widths=c(4,4,4), gap="1rem",
      card(class="sobre-card",
        card_header("A Plataforma"),
        card_body(
          tags$p("O Observatório da Fome integra dados públicos de múltiplas fontes oficiais para
                  construir uma visão territorial abrangente da segurança alimentar no Brasil.",
                 style="font-size:0.88rem;line-height:1.7;color:#3a3a4a;"),
          tags$p("As análises são organizadas em cinco módulos — Panorama Nacional, Segurança Alimentar,
                  Bolsa Família, Produção Agrícola e Correlações —, permitindo explorar tanto o quadro
                  nacional quanto os perfis estaduais.",
                 style="font-size:0.88rem;line-height:1.7;color:#3a3a4a;")
        )
      ),
      card(class="sobre-card",
        card_header("Fontes de Dados"),
        card_body(
          tags$table(class="sobre-table",
            tags$thead(tags$tr(tags$th("Fonte"), tags$th("Cobertura"))),
            tags$tbody(
              tags$tr(tags$td("PNAD Contínua — IBGE"), tags$td("Segurança Alimentar · Estadual · 2023 e 2024")),
              tags$tr(tags$td("Censo Demográfico — IBGE"), tags$td("População e urbanização · Municipal · 2022")),
              tags$tr(tags$td("Pesquisa Agrícola Municipal — IBGE"), tags$td("Área plantada · Municipal · 2022")),
              tags$tr(tags$td("MDS — Bolsa Família"), tags$td("Beneficiários e valores · Municipal · 2023–2024"))
            )
          )
        )
      ),
      card(class="sobre-card",
        card_header("Notas Metodológicas"),
        card_body(
          tags$ul(class="sobre-list",
            tags$li(tags$b("Insegurança alimentar:"),
              " medida em quatro categorias (segurança, leve, moderada e grave) com base na
                Escala Brasileira de Insegurança Alimentar (EBIA), aplicada pela PNAD Contínua.
                Os dados têm representatividade estadual e são replicados para os municípios da mesma UF."),
            tags$li(tags$b("Bolsa Família — 2023:"),
              " cobre apenas 10 meses (março–dezembro). As médias mensais foram calculadas sobre os
                meses disponíveis. A soma anual reflete o período efetivo."),
            tags$li(tags$b("Código IBGE:"),
              " o join entre fontes utiliza os 6 primeiros dígitos do código de 7 dígitos do IBGE,
                descartando o dígito verificador.")
          )
        )
      )
    ),
    br(),
    layout_columns(col_widths=c(3,3,3,3), gap="1rem",
      card(class="sobre-stat-card",
        card_body(class="sobre-stat-body",
          tags$div(class="sobre-stat-num", "5.570"),
          tags$div(class="sobre-stat-lab", "Municípios mapeados")
        )
      ),
      card(class="sobre-stat-card",
        card_body(class="sobre-stat-body",
          tags$div(class="sobre-stat-num", "120"),
          tags$div(class="sobre-stat-lab", "Variáveis no dataset")
        )
      ),
      card(class="sobre-stat-card",
        card_body(class="sobre-stat-body",
          tags$div(class="sobre-stat-num", "4"),
          tags$div(class="sobre-stat-lab", "Fontes de dados integradas")
        )
      ),
      card(class="sobre-stat-card",
        card_body(class="sobre-stat-body",
          tags$div(class="sobre-stat-num", "2023–24"),
          tags$div(class="sobre-stat-lab", "Período de cobertura")
        )
      )
    ),
    tags$div(class="rodape",
      "ONG Aruana · Dados públicos oficiais · IBGE · MDS · Última atualização: fevereiro de 2026")
  ),

  # ── TAB 1: Panorama Nacional ────────────────────────────────────────────────
  nav_panel("Panorama Nacional",
    layout_columns(col_widths=c(2,2,2,2,2,2), gap="0.8rem",
      value_box("População Total", textOutput("kpi_pop"),
                showcase=bsicons::bs_icon("people-fill"), class="vb-branco"),
      value_box("Inseg. Alimentar 2024", textOutput("kpi_inseg_total"),
                showcase=bsicons::bs_icon("exclamation-triangle-fill"), class="vb-warn"),
      value_box("Inseg. Grave 2024", textOutput("kpi_inseg_grave"),
                showcase=bsicons::bs_icon("heartbreak-fill"), class="vb-perigo"),
      value_box("Pessoas em Situação de Fome", textOutput("kpi_mor_fome"),
                showcase=bsicons::bs_icon("person-x-fill"), class="vb-perigo"),
      value_box("Famílias no Bolsa Família 2024", textOutput("kpi_bf_fam"),
                showcase=bsicons::bs_icon("house-heart-fill"), class="vb-verde"),
      value_box("Bolsa Família — Repasse Mensal", textOutput("kpi_bf_val"),
                showcase=bsicons::bs_icon("currency-dollar"), class="vb-roxo")
    ),
    br(),
    layout_columns(col_widths=c(7,5), gap="1rem",
      card(card_header("Insegurança Grave por Estado — % Domicílios (2024)"),
           plotlyOutput("mapa_inseg", height="400px")),
      card(card_header("Ranking dos 27 Estados — Insegurança Grave 2024"),
           plotlyOutput("bar_ranking", height="400px"))
    ),
    br(),
    layout_columns(col_widths=c(6,6), gap="1rem",
      card(card_header("Variação da Inseg. Grave 2023 para 2024 (pontos percentuais)"),
           plotlyOutput("bar_variacao", height="300px")),
      card(card_header("Composição Nacional — Segurança Alimentar 2024"),
           plotlyOutput("donut_br", height="300px"))
    ),
    tags$div(class="rodape",
      "Fontes: IBGE Censo 2022 · PNAD Contínua 2023/2024 · MDS/Bolsa Família 2023/2024 · ONG Aruana")
  ),

  # ── TAB 2: Segurança Alimentar ──────────────────────────────────────────────
  nav_panel("Segurança Alimentar",
    layout_columns(col_widths=c(3,9), gap="1rem",
      card(
        card_header("Filtros"),
        card_body(
          selectInput("uf_sa", "Estado:", choices=sort(unique(df_uf$abbrev_state)),
                      selected="MA"),
          radioButtons("ano_sa", "Ano de referência:", choices=c("2023","2024"),
                       selected="2024", inline=TRUE),
          hr(),
          tags$p(class="text-muted small",
            "Os dados de insegurança alimentar têm representatividade estadual (PNAD Contínua)
             e são atribuídos igualmente a todos os municípios da UF selecionada.")
        )
      ),
      div(style="display:flex; flex-direction:column; gap:1rem;",
        layout_columns(col_widths=c(5,7), gap="1rem",
          card(card_header("Composição por Categoria"),
               card_body(plotlyOutput("donut_uf", height="280px"))),
          card(card_header("Domicílios e Moradores por Categoria (mil)"),
               card_body(plotlyOutput("bar_dom_mor", height="280px")))
        ),
        card(card_header("Comparativo 2023 vs. 2024 — % Domicílios por Categoria"),
             card_body(plotlyOutput("bar_anos", height="260px")))
      )
    ),
    br(),
    card(
      card_header("Ranking Completo — % Domicílios com Insegurança Alimentar por Estado"),
      card_body(DTOutput("tabela_sa"))
    )
  ),

  # ── TAB 3: Bolsa Família ────────────────────────────────────────────────────
  nav_panel("Bolsa Família",
    layout_columns(col_widths=c(4,4,4), gap="0.8rem",
      value_box("Famílias Beneficiárias (média mensal 2024)",
                textOutput("kpi_bf2_fam"), class="vb-verde",
                showcase=bsicons::bs_icon("house-heart-fill")),
      value_box("Valor Médio por Benefício — 2024",
                textOutput("kpi_bf2_vlr"), class="vb-roxo",
                showcase=bsicons::bs_icon("cash-coin")),
      value_box("Variação de Famílias 2023 para 2024",
                textOutput("kpi_bf2_var"), class="vb-branco",
                showcase=bsicons::bs_icon("graph-up-arrow"))
    ),
    br(),
    layout_columns(col_widths=c(6,6), gap="1rem",
      card(card_header("Cobertura — Famílias Beneficiárias por 1.000 Habitantes (2024)"),
           plotlyOutput("mapa_bf_cob", height="380px")),
      card(card_header("Total Repassado por Estado — R$ médio mensal (2024)"),
           plotlyOutput("bar_bf_val", height="380px"))
    ),
    br(),
    layout_columns(col_widths=c(6,6), gap="1rem",
      card(card_header("Cobertura do Bolsa Família vs. Insegurança Grave por Estado (2024)"),
           plotlyOutput("scatter_bf_inseg", height="340px")),
      card(card_header("Valor Médio do Benefício por Estado (R$, 2024)"),
           plotlyOutput("mapa_bf_vlr", height="340px"))
    )
  ),

  # ── TAB 4: Produção & Território ────────────────────────────────────────────
  nav_panel("Producao e Territorio",
    layout_columns(col_widths=c(4,4,4), gap="0.8rem",
      value_box("Area Total Plantada", textOutput("kpi_area"),
                class="vb-verde", showcase=bsicons::bs_icon("tree-fill")),
      value_box("% Pop. Rural (ponderada)", textOutput("kpi_rural"),
                class="vb-branco", showcase=bsicons::bs_icon("house-fill")),
      value_box("Municipios sem area registrada", textOutput("kpi_sem_area"),
                class="vb-branco", showcase=bsicons::bs_icon("question-circle"))
    ),
    br(),
    layout_columns(col_widths=c(6,6), gap="1rem",
      card(card_header("Area Plantada per Capita por Estado (ha/hab)"),
           plotlyOutput("mapa_area", height="380px")),
      card(card_header("Paradoxo: Area Plantada per Capita vs. Inseguranca Grave"),
           plotlyOutput("scatter_area", height="380px"))
    ),
    br(),
    layout_columns(col_widths=c(7,5), gap="1rem",
      card(card_header("Urbanizacao vs. Ruralidade por Estado (%)"),
           plotlyOutput("bar_urb_rural", height="320px")),
      card(card_header("Populacao Rural por Estado (%)"),
           plotlyOutput("mapa_rural", height="320px"))
    )
  ),

  # ── TAB 5: Correlações ──────────────────────────────────────────────────────
  nav_panel("Correlacoes",
    layout_columns(col_widths=c(6,6), gap="1rem",
      card(card_header("Ruralidade vs. Inseguranca Grave (2024)"),
           plotlyOutput("sc_rural_inseg", height="330px")),
      card(card_header("Cobertura Bolsa Familia vs. Inseguranca Grave (2024)"),
           plotlyOutput("sc_bf_inseg", height="330px"))
    ),
    br(),
    layout_columns(col_widths=c(6,6), gap="1rem",
      card(card_header("Valor Medio do Beneficio vs. Inseguranca Grave (2024)"),
           plotlyOutput("sc_vlr_inseg", height="330px")),
      card(card_header("Area Plantada per Capita vs. Inseguranca Grave"),
           plotlyOutput("sc_area_inseg", height="330px"))
    ),
    br(),
    card(
      card_header("Tabela Completa de Indicadores por Estado"),
      card_body(DTOutput("tabela_full"))
    )
  )
)

# ── SERVER ─────────────────────────────────────────────────────────────────────
server <- function(input, output, session) {

  ## ── KPIs Tab 1 ──────────────────────────────────────────────────────────────
  output$kpi_pop       <- renderText(format(pop_total_br, big.mark=".", decimal.mark=","))
  output$kpi_inseg_total <- renderText(paste0(round(inseg_total_br24, 1), "%"))
  output$kpi_inseg_grave <- renderText(paste0(round(inseg_grave_br24, 1), "%"))
  output$kpi_mor_fome  <- renderText(paste0(round(mor_fome_br24/1e6, 1), " milhoes"))
  output$kpi_bf_fam    <- renderText(
    paste0(format(round(bf_familias_br24/1e6, 2), nsmall=2, decimal.mark=","), " mi"))
  output$kpi_bf_val    <- renderText(
    paste0("R$ ", format(round(bf_valor_br24/1e9, 2), nsmall=2, decimal.mark=","), " bi"))

  ## ── KPIs Tab 3 ──────────────────────────────────────────────────────────────
  output$kpi_bf2_fam   <- renderText(
    paste0(format(round(bf_familias_br24/1e6, 2), nsmall=2, decimal.mark=","), " mi"))
  output$kpi_bf2_vlr   <- renderText(
    paste0("R$ ", format(round(bf_vlr_medio_br24, 2), nsmall=2, big.mark=".", decimal.mark=",")))
  output$kpi_bf2_var   <- renderText({
    v <- (bf_familias_br24 - bf_familias_br23) / bf_familias_br23 * 100
    paste0(sprintf("%+.1f", v), "%")
  })

  ## ── KPIs Tab 4 ──────────────────────────────────────────────────────────────
  output$kpi_area      <- renderText(
    paste0(format(round(sum(df$area_plantada_ha, na.rm=TRUE)/1e6, 1), decimal.mark=","), " M ha"))
  output$kpi_rural     <- renderText(
    paste0(round(weighted.mean(df_uf$perc_rural_uf, df_uf$populacao, na.rm=TRUE), 1), "%"))
  output$kpi_sem_area  <- renderText(
    format(sum(is.na(df$area_plantada_ha)), big.mark="."))

  ## ── Tab 1: Mapas e graficos nacionais ────────────────────────────────────────
  output$mapa_inseg <- renderPlotly({
    mapa_uf("inseg_grave_perc_dom_2024", "Inseg. Grave (%)",
            pal_low="#f5eefd", pal_high=COR_ROXO, sufixo="%")
  })

  output$bar_ranking <- renderPlotly({
    d <- df_uf |>
      arrange(inseg_grave_perc_dom_2024) |>
      mutate(cor=if_else(inseg_grave_perc_dom_2024 >=
                           quantile(inseg_grave_perc_dom_2024, 0.66, na.rm=TRUE),
                         COR_PERIGO, COR_ROXO2))
    plot_ly(d,
      y=~reorder(abbrev_state, inseg_grave_perc_dom_2024),
      x=~inseg_grave_perc_dom_2024, type="bar", orientation="h",
      marker=list(color=d$cor),
      hovertemplate="<b>%{y}</b><br>Inseg. Grave: %{x:.1f}%<extra></extra>"
    ) |> plotly_layout(
      xaxis=list(title="% Domicilios", ticksuffix="%", gridcolor=COR_GRID),
      yaxis=list(title="", tickfont=list(size=10)),
      showlegend=FALSE
    )
  })

  output$bar_variacao <- renderPlotly({
    d <- df_uf |>
      arrange(delta_inseg_grave) |>
      mutate(cor=if_else(delta_inseg_grave > 0, COR_PERIGO, COR_VERDE))
    plot_ly(d,
      x=~reorder(abbrev_state, delta_inseg_grave),
      y=~delta_inseg_grave, type="bar",
      marker=list(color=d$cor),
      hovertemplate="<b>%{x}</b><br>Variacao: %{y:+.1f} p.p.<extra></extra>"
    ) |> plotly_layout(
      xaxis=list(title=""),
      yaxis=list(title="Variacao (p.p.)", gridcolor=COR_GRID,
                 zeroline=TRUE, zerolinecolor="#999", zerolinewidth=1.5),
      showlegend=FALSE
    )
  })

  output$donut_br <- renderPlotly({
    cats <- tibble(
      label=c("Com Seguranca Alimentar","Inseg. Leve","Inseg. Moderada","Inseg. Grave"),
      valor=c(
        weighted.mean(df_uf$seg_perc_dom_2024, df_uf$total_dom_mil_2024, na.rm=TRUE),
        weighted.mean(df_uf$inseg_leve_perc_dom_2024, df_uf$total_dom_mil_2024, na.rm=TRUE),
        weighted.mean(df_uf$inseg_moderada_perc_dom_2024, df_uf$total_dom_mil_2024, na.rm=TRUE),
        weighted.mean(df_uf$inseg_grave_perc_dom_2024, df_uf$total_dom_mil_2024, na.rm=TRUE)
      ),
      cor=c(COR_VERDE, COR_ROXO2, COR_WARN, COR_PERIGO)
    )
    plot_ly(cats, labels=~label, values=~valor, type="pie", hole=0.55,
      marker=list(colors=cats$cor, line=list(color="white", width=2)),
      textinfo="label+percent", textfont=list(size=10),
      hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>"
    ) |> plotly_layout(
      showlegend=FALSE,
      annotations=list(list(text="Brasil<br>2024", x=0.5, y=0.5,
        font=list(size=13, color=COR_DARK), showarrow=FALSE))
    )
  })

  ## ── Tab 2: Seguranca Alimentar ────────────────────────────────────────────────
  d_uf_sa <- reactive({ df_uf |> filter(abbrev_state == input$uf_sa) })
  ano_r   <- reactive({ input$ano_sa })

  output$donut_uf <- renderPlotly({
    d <- d_uf_sa(); ano <- ano_r()
    cats <- tibble(
      label=c("Com Seguranca","Inseg. Leve","Inseg. Moderada","Inseg. Grave"),
      valor=c(d[[paste0("seg_perc_dom_",ano)]], d[[paste0("inseg_leve_perc_dom_",ano)]],
              d[[paste0("inseg_moderada_perc_dom_",ano)]], d[[paste0("inseg_grave_perc_dom_",ano)]]),
      cor=c(COR_VERDE, COR_ROXO2, COR_WARN, COR_PERIGO)
    )
    plot_ly(cats, labels=~label, values=~valor, type="pie", hole=0.55,
      marker=list(colors=cats$cor, line=list(color="white", width=2)),
      textinfo="percent", textfont=list(size=11),
      hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>"
    ) |> plotly_layout(
      showlegend=FALSE,
      annotations=list(list(text=paste0(input$uf_sa,"<br>",ano),
        x=0.5, y=0.5, font=list(size=13, color=COR_DARK), showarrow=FALSE))
    )
  })

  output$bar_dom_mor <- renderPlotly({
    d <- d_uf_sa(); ano <- ano_r()
    cats <- c("seg","inseg_leve","inseg_moderada","inseg_grave")
    labs <- c("Com Seguranca","Inseg. Leve","Inseg. Moderada","Inseg. Grave")
    dom <- sapply(cats, \(c) d[[paste0(c,"_dom_mil_",ano)]] %||% NA_real_)
    mor <- sapply(cats, \(c) d[[paste0(c,"_mor_mil_",ano)]] %||% NA_real_)
    plot_ly(x=labs, y=dom, type="bar", name="Domicilios (mil)",
            marker=list(color=COR_ROXO),
            hovertemplate="<b>%{x}</b><br>%{y:.0f} mil domicilios<extra></extra>") |>
      add_trace(y=mor, name="Moradores (mil)", marker=list(color=COR_VERDE),
                hovertemplate="<b>%{x}</b><br>%{y:.0f} mil moradores<extra></extra>") |>
      plotly_layout(
        barmode="group",
        xaxis=list(title=""),
        yaxis=list(title="Mil", gridcolor=COR_GRID),
        legend=list(orientation="h", y=-0.2)
      )
  })

  output$bar_anos <- renderPlotly({
    d <- d_uf_sa()
    cats <- c("seg","inseg_leve","inseg_moderada","inseg_grave")
    labs <- c("Com Seguranca","Inseg. Leve","Inseg. Moderada","Inseg. Grave")
    v23  <- sapply(cats, \(c) d[[paste0(c,"_perc_dom_2023")]] %||% NA_real_)
    v24  <- sapply(cats, \(c) d[[paste0(c,"_perc_dom_2024")]] %||% NA_real_)
    plot_ly(x=labs, y=v23, type="bar", name="2023",
            marker=list(color=COR_ROXO2),
            hovertemplate="<b>%{x}</b><br>2023: %{y:.1f}%<extra></extra>") |>
      add_trace(y=v24, name="2024", marker=list(color=COR_ROXO),
                hovertemplate="<b>%{x}</b><br>2024: %{y:.1f}%<extra></extra>") |>
      plotly_layout(
        barmode="group", xaxis=list(title=""),
        yaxis=list(title="% Domicilios", ticksuffix="%", gridcolor=COR_GRID),
        legend=list(orientation="h", y=-0.25)
      )
  })

  output$tabela_sa <- renderDT({
    df_uf |>
      select(Estado=abbrev_state, Regiao=name_region,
             `Inseg.Grave 2023 (%)`=inseg_grave_perc_dom_2023,
             `Inseg.Grave 2024 (%)`=inseg_grave_perc_dom_2024,
             `Variacao (p.p.)`=delta_inseg_grave,
             `Inseg.Total 2024 (%)`=inseg_perc_dom_2024,
             `Com Seguranca 2024 (%)`=seg_perc_dom_2024) |>
      arrange(desc(`Inseg.Grave 2024 (%)`)) |>
      datatable(options=list(pageLength=10, dom="ftp",
                             language=list(url="//cdn.datatables.net/plug-ins/1.10.21/i18n/Portuguese-Brasil.json")),
                rownames=FALSE, class="compact hover") |>
      formatRound(3:7, digits=1) |>
      formatStyle("Inseg.Grave 2024 (%)",
                  background=styleColorBar(c(0, max(df_uf$inseg_grave_perc_dom_2024, na.rm=TRUE)),
                                            "#f5eefd"),
                  backgroundSize="100% 80%", backgroundRepeat="no-repeat",
                  backgroundPosition="center") |>
      formatStyle("Variacao (p.p.)",
                  color=styleInterval(0, c(COR_VERDE, COR_PERIGO)),
                  fontWeight="bold")
  })

  ## ── Tab 3: Bolsa Familia ──────────────────────────────────────────────────────
  output$mapa_bf_cob <- renderPlotly({
    mapa_uf("bf_cobertura_2024", "Familias/1.000 hab",
            pal_low=COR_CREME, pal_high=COR_VERDE, sufixo="")
  })

  output$bar_bf_val <- renderPlotly({
    d <- df_uf |> arrange(bf_valor_2024) |>
      mutate(val_mi=bf_valor_2024/1e6)
    plot_ly(d,
      y=~reorder(abbrev_state, val_mi), x=~val_mi,
      type="bar", orientation="h",
      marker=list(color=COR_VERDE, opacity=0.85),
      hovertemplate="<b>%{y}</b><br>R$ %{x:.1f} mi/mes<extra></extra>"
    ) |> plotly_layout(
      xaxis=list(title="R$ Milhoes (media mensal)", gridcolor=COR_GRID),
      yaxis=list(title="", tickfont=list(size=10)),
      showlegend=FALSE
    )
  })

  output$scatter_bf_inseg <- renderPlotly({
    scatter_uf("bf_cobertura_2024", "inseg_grave_perc_dom_2024",
               "Cobertura BF (fam./1.000 hab)", "Inseg. Grave (%)",
               y_suf="%")
  })

  output$mapa_bf_vlr <- renderPlotly({
    mapa_uf("bf_vlr_medio_2024", "Valor medio (R$)",
            pal_low=COR_CREME, pal_high=COR_VERDE,
            sufixo="", fmt="R$ %.0f")
  })

  ## ── Tab 4: Producao e Territorio ──────────────────────────────────────────────
  output$mapa_area <- renderPlotly({
    mapa_uf("area_per_capita", "ha por habitante",
            pal_low=COR_CREME, pal_high=COR_VERDE2,
            sufixo=" ha/hab", fmt="%.4f")
  })

  output$scatter_area <- renderPlotly({
    scatter_uf("area_per_capita", "inseg_grave_perc_dom_2024",
               "Area plantada per capita (ha/hab)", "Inseg. Grave (%)",
               y_suf="%", x_fmt="%.4f")
  })

  output$bar_urb_rural <- renderPlotly({
    d <- df_uf |>
      select(abbrev_state, name_region, perc_urbana_uf, perc_rural_uf) |>
      arrange(perc_rural_uf)
    plot_ly(d, x=~reorder(abbrev_state, perc_rural_uf),
            y=~perc_urbana_uf, type="bar", name="Urbana",
            marker=list(color=COR_ROXO),
            hovertemplate="<b>%{x}</b><br>Urbana: %{y:.1f}%<extra></extra>") |>
      add_trace(y=~perc_rural_uf, name="Rural",
                marker=list(color=COR_VERDE),
                hovertemplate="<b>%{x}</b><br>Rural: %{y:.1f}%<extra></extra>") |>
      plotly_layout(
        barmode="stack", xaxis=list(title="", tickfont=list(size=10)),
        yaxis=list(title="% da populacao", ticksuffix="%", gridcolor=COR_GRID),
        legend=list(orientation="h", y=-0.2)
      )
  })

  output$mapa_rural <- renderPlotly({
    mapa_uf("perc_rural_uf", "% Pop. Rural",
            pal_low=COR_CREME, pal_high=COR_VERDE, sufixo="%")
  })

  ## ── Tab 5: Correlacoes ────────────────────────────────────────────────────────
  output$sc_rural_inseg <- renderPlotly({
    scatter_uf("perc_rural_uf","inseg_grave_perc_dom_2024",
               "% Pop. Rural","Inseg. Grave (%)", x_suf="%", y_suf="%")
  })
  output$sc_bf_inseg <- renderPlotly({
    scatter_uf("bf_cobertura_2024","inseg_grave_perc_dom_2024",
               "Cobertura BF (fam./1.000 hab)","Inseg. Grave (%)", y_suf="%")
  })
  output$sc_vlr_inseg <- renderPlotly({
    scatter_uf("bf_vlr_medio_2024","inseg_grave_perc_dom_2024",
               "Valor Medio BF (R$)","Inseg. Grave (%)", y_suf="%", x_fmt="R$ %.0f")
  })
  output$sc_area_inseg <- renderPlotly({
    scatter_uf("area_per_capita","inseg_grave_perc_dom_2024",
               "Area Plantada per Capita (ha/hab)","Inseg. Grave (%)",
               y_suf="%", x_fmt="%.4f")
  })

  output$tabela_full <- renderDT({
    df_uf |>
      transmute(
        Estado        = abbrev_state,
        Regiao        = name_region,
        `Pop. (mil)`  = round(populacao/1e3),
        `% Rural`     = round(perc_rural_uf, 1),
        `Inseg.Grave 24 (%)` = round(inseg_grave_perc_dom_2024, 1),
        `Inseg.Total 24 (%)` = round(inseg_perc_dom_2024, 1),
        `Var. Inseg.Grave (p.p.)` = round(delta_inseg_grave, 1),
        `BF Fam/1.000 hab` = round(bf_cobertura_2024, 1),
        `BF Vlr.Medio (R$)` = round(bf_vlr_medio_2024),
        `Area/hab (ha)` = round(area_per_capita, 4)
      ) |>
      arrange(desc(`Inseg.Grave 24 (%)`)) |>
      datatable(
        rownames=FALSE, class="compact hover",
        options=list(pageLength=27, dom="ft",
                     language=list(url="//cdn.datatables.net/plug-ins/1.10.21/i18n/Portuguese-Brasil.json"))
      ) |>
      formatStyle("Inseg.Grave 24 (%)",
                  background=styleColorBar(c(0, max(df_uf$inseg_grave_perc_dom_2024, na.rm=TRUE)), "#f5eefd"),
                  backgroundSize="100% 80%", backgroundRepeat="no-repeat",
                  backgroundPosition="center") |>
      formatStyle("Var. Inseg.Grave (p.p.)",
                  color=styleInterval(0, c(COR_VERDE, COR_PERIGO)), fontWeight="bold")
  })
}

shinyApp(ui, server)
