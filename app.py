"""
Instituto Aruanã – Observatório de Segurança Alimentar
Dashboard Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
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
COR_ALIMENTO = "#4CAF50"
COR_COMMODITY = "#FF9800"

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", color="#333333"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=50, b=40),
)

# ---------------------------------------------------------------------------
# Data loading & Filtering
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(__file__),
        "dados_consolidados_v4.csv",
    )
    df = pd.read_csv(csv_path, sep=";", decimal=",", encoding="utf-8")
    return df

DATA = load_data()

# Load per-product data if available
@st.cache_data
def load_producao_produto():
    csv_path = os.path.join(os.path.dirname(__file__), "producao_por_produto.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=";", decimal=",", encoding="utf-8")
        return df
    return None

DATA_PROD = load_producao_produto()

def get_filtered_data():
    """Returns the dataframe filtered by the global sidebar selections."""
    df = DATA.copy()
    
    # 1. Região
    if st.session_state.filtro_regiao != "Todas":
        df = df[df["name_region"] == st.session_state.filtro_regiao]
        
    # 2. UF
    if st.session_state.filtro_uf != "Todas":
        df = df[df["abbrev_state"] == st.session_state.filtro_uf]
        
    # 3. Situação Predominante
    if st.session_state.filtro_situacao == "Predominantemente Urbana":
        df = df[df["pop_urbana"] >= df["pop_rural"]]
    elif st.session_state.filtro_situacao == "Predominantemente Rural":
        df = df[df["pop_rural"] > df["pop_urbana"]]
        
    return df

# Aggregates at state level based on filtered data and selected year
def state_summary(filtered_df, ano):
    """Retorna dados de insegurança alimentar a nível estadual."""
    cols_needed = [
        "abbrev_state", "name_region",
        f"inseg_perc_dom_{ano}", f"inseg_leve_perc_dom_{ano}",
        f"inseg_moderada_perc_dom_{ano}", f"inseg_grave_perc_dom_{ano}",
        "inseg_perc_dom_2023", "inseg_perc_dom_2024" # Manted for comparison in some graphs
    ]
    # Remove duplicates from cols_needed (e.g. if ano == "2023")
    cols_needed = list(dict.fromkeys(cols_needed))
    
    # Check if necessary columns exist (fallback if year column lacks some data)
    cols_present = [c for c in cols_needed if c in filtered_df.columns]
    
    st_df = filtered_df[cols_present].drop_duplicates(subset=["abbrev_state"])
    if f"inseg_perc_dom_{ano}" in st_df.columns:
        st_df = st_df.sort_values(f"inseg_perc_dom_{ano}", ascending=False)
    return st_df


def state_aggregates(filtered_df, ano):
    """Agrega dados numéricos por estado baseados nos dados filtrados."""
    agg_dict = dict(
        populacao=("populacao", "sum"),
        pop_rural=("pop_rural", "sum"),
        area_plantada_ha=("area_plantada_ha", "sum"),
        bf_valor_repassado_media_2023=("bf_valor_repassado_media_2023", "sum"),
        bf_valor_repassado_media_2024=("bf_valor_repassado_media_2024", "sum"),
        bf_qtd_familias_media_2023=("bf_qtd_familias_media_2023", "sum"),
        bf_qtd_familias_media_2024=("bf_qtd_familias_media_2024", "sum"),
        name_region=("name_region", "first"),
        lat=("lat", "mean"),
        lon=("lon", "mean"),
    )
    # Add production classification columns if they exist
    for yr in ["2023", "2024"]:
        for prefix in ["area_ha", "qtd_toneladas", "valor_mil_reais", "n_produtos"]:
            for cat in ["alimento", "commodity"]:
                col = f"{prefix}_{cat}_{yr}"
                if col in filtered_df.columns:
                    agg_dict[col] = (col, "sum")

    agg = filtered_df.groupby("abbrev_state").agg(**agg_dict).reset_index()
    
    # Adicionar colunas dinâmicas para o ano selecionado (facilita acesso nas páginas)
    agg["bf_valor_repassado_media_ano"] = agg[f"bf_valor_repassado_media_{ano}"]
    agg["bf_qtd_familias_media_ano"] = agg[f"bf_qtd_familias_media_{ano}"]
    
    return agg


# ---------------------------------------------------------------------------
# Sidebar & Filters
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
    
    # ---- FILTROS GLOBAIS ----
    st.markdown("**Filtros Globais**")
    
    # Ano
    ano_referencia = st.selectbox(
        "Ano de Referência",
        ["2024", "2023"],
        index=0,
        key="filtro_ano"
    )
    
    # Região
    regioes = ["Todas"] + sorted(DATA["name_region"].dropna().unique().tolist())
    regiao_selecionada = st.selectbox(
        "Região",
        regioes,
        index=0,
        key="filtro_regiao"
    )
    
    # UF
    if regiao_selecionada == "Todas":
        ufs = ["Todas"] + sorted(DATA["abbrev_state"].dropna().unique().tolist())
    else:
        ufs = ["Todas"] + sorted(DATA[DATA["name_region"] == regiao_selecionada]["abbrev_state"].dropna().unique().tolist())
        
    uf_selecionada = st.selectbox(
        "Unidade da Federação",
        ufs,
        index=0,
        key="filtro_uf"
    )
    
    # Situação Predominante
    sit_selecionada = st.selectbox(
        "Situação Predominante",
        ["Todas", "Predominantemente Urbana", "Predominantemente Rural"],
        index=0,
        key="filtro_situacao"
    )

    st.markdown("---")

    # ---- NAVEGAÇÃO ----
    NAV_ITEMS = [
        (":material/home:", "Apresentação"),
        (":material/monitoring:", "Panorama Nacional"),
        (":material/agriculture:", "Produção Agrícola"),
        (":material/eco:", "Alimento vs Commodity"),
        (":material/account_balance_wallet:", "Bolsa Família"),
        (":material/map:", "Análises Regionais"),
        (":material/description:", "Metodologia"),
        (":material/download:", "Download de Dados"),
    ]

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = "Apresentação"

    def set_page(page_name):
        st.session_state.pagina_atual = page_name

    for icon, label in NAV_ITEMS:
        if st.button(
            label,
            key=f"nav_{label}",
            icon=icon,
            use_container_width=True,
            type="tertiary",
        ):
            set_page(label)
            st.rerun()

    pagina = st.session_state.pagina_atual

    st.markdown(
        '<div class="footer-text">2026 Instituto Aruanã</div>',
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

    # Key metrics based on global filters
    st.markdown("---")
    st.markdown(f"### Indicadores gerais ({ano_referencia})")
    
    filtered_df = get_filtered_data()
    
    m1, m2, m3, m4 = st.columns(4)
    total_pop = filtered_df["populacao"].sum()
    total_munis = filtered_df["code_muni"].nunique()
    
    inseg_col = f"inseg_perc_dom_{ano_referencia}"
    inseg_grave_col = f"inseg_grave_perc_dom_{ano_referencia}"
    
    # Use grouped average to not let cities skew the state probability
    state_level = filtered_df[["abbrev_state", inseg_col, inseg_grave_col]].drop_duplicates()
    
    inseg_media_ano = state_level[inseg_col].mean() if not state_level.empty else 0
    inseg_grave_media_ano = state_level[inseg_grave_col].mean() if not state_level.empty else 0

    m1.metric("Municípios Filtrados", f"{total_munis:,}".replace(",", "."))
    m2.metric("População Total (Censo)", f"{total_pop/1e6:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", "."))
    m3.metric("Insegurança Alimentar (média UF)", f"{inseg_media_ano:,.1f}%".replace(".", ","))
    m4.metric("Insegurança Grave (média UF)", f"{inseg_grave_media_ano:,.1f}%".replace(".", ","))


# -------------------------------------------------------------------------
# 2. Panorama Nacional
# -------------------------------------------------------------------------
def pagina_panorama():
    ano = st.session_state.filtro_ano
    st.markdown(f"# Panorama Nacional ({ano})")
    st.markdown(
        '<p class="subtitle">Insegurança alimentar por unidade da federação</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    sdf = state_summary(filtered_df, ano)

    if sdf.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- Bar chart: total food insecurity by state ----------
    st.markdown("### Comparativo Anual por Estado")
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

    c1, c2 = st.columns(2)
    # ---------- Breakdown by severity ----------
    with c1:
        st.markdown(f"### Composição por grau ({ano})")
        fig2 = go.Figure()
        for col, cor, label in [
            (f"inseg_leve_perc_dom_{ano}", COR_LEVE, "Leve"),
            (f"inseg_moderada_perc_dom_{ano}", COR_MODERADA, "Moderada"),
            (f"inseg_grave_perc_dom_{ano}", COR_GRAVE, "Grave"),
        ]:
            if col in sdf.columns:
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

    # ---------- Correlation: Rural Pop vs Insecurity ----------
    with c2:
        st.markdown(f"### Perfil Rural vs Insegurança ({ano})")
        agg_rural = filtered_df.groupby("abbrev_state").agg(
            pop_total=("populacao", "sum"),
            pop_rural=("pop_rural", "sum"),
            inseg_ref=(f"inseg_perc_dom_{ano}", "first")
        ).reset_index()
        agg_rural["perc_rural"] = (agg_rural["pop_rural"] / agg_rural["pop_total"]) * 100

        fig_scatter_pop = px.scatter(
            agg_rural, 
            x="perc_rural", 
            y="inseg_ref",
            text="abbrev_state",
            color_discrete_sequence=[COR_PRIMARIA],
            labels={
                "perc_rural": "% População Rural",
                "inseg_ref": f"Insegurança Alimentar {ano} (%)",
            }
        )
        fig_scatter_pop.update_traces(textposition="top center", marker=dict(size=10))
        fig_scatter_pop.update_layout(
            **PLOTLY_LAYOUT,
            height=450,
        )
        st.plotly_chart(fig_scatter_pop, use_container_width=True)


# -------------------------------------------------------------------------
# 3. Produção Agrícola
# -------------------------------------------------------------------------
def pagina_producao():
    ano = st.session_state.filtro_ano
    st.markdown("# Produção Agrícola")
    st.markdown(
        '<p class="subtitle">Área plantada e sua relação com indicadores sociais</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    agg = state_aggregates(filtered_df, ano)
    
    if agg.empty or agg["area_plantada_ha"].sum() == 0:
        st.warning("Sem dados de produção agrícola disponíveis para os filtros selecionados.")
        return
        
    agg = agg.sort_values("area_plantada_ha", ascending=False)
    
    # ---------- Map: Agricultural Production point cloud ----------
    st.markdown(f"### Mapa de Produção Agrícola por Estado")
    st.markdown("Intensidade concentrada baseada na área plantada agregada.")
    map_data_agri = agg.dropna(subset=["lat", "lon"]).copy()

    if not map_data_agri.empty:
        fig_map_agri = px.scatter_mapbox(
            map_data_agri,
            lat="lat",
            lon="lon",
            color="area_plantada_ha",
            size="area_plantada_ha",
            size_max=40, # Allow bubbles to get bigger since they represent states
            hover_name="abbrev_state",
            hover_data={"populacao": True, "area_plantada_ha": True, "lat": False, "lon": False},
            color_continuous_scale="Greens",
            zoom=3.0,
            center={"lat": -15.78, "lon": -47.92},
            mapbox_style="carto-positron",
            title="Suma da Área Plantada (Estados)"
        )
        fig_map_agri.update_layout(**PLOTLY_LAYOUT)
        fig_map_agri.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            height=550,
            coloraxis_colorbar=dict(title="Área (ha)"),
        )
        st.plotly_chart(fig_map_agri, use_container_width=True)
    else:
        st.info("Municípios insuficientes com dados geográficos ou agrícolas para mapas.")

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- TreeMap: Agricultura by Region and State ----------
    st.markdown("### Composição da Área Plantada (Região e UF)")
    fig_tree = px.treemap(
        agg, 
        path=[px.Constant("Brasil"), "name_region", "abbrev_state"], 
        values="area_plantada_ha",
        color="area_plantada_ha",
        color_continuous_scale="Greens",
        title="Área plantada por hierarquia de região"
    )
    fig_tree.update_layout(**PLOTLY_LAYOUT)
    fig_tree.update_layout(
        margin=dict(t=50, l=10, r=10, b=10),
        height=450,
    )
    fig_tree.update_traces(root_color="lightgrey")
    st.plotly_chart(fig_tree, use_container_width=True)

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

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

    # ---------- ALIMENTO vs COMMODITY ----------
    col_area_alim = f"area_ha_alimento_{ano}"
    col_area_comm = f"area_ha_commodity_{ano}"
    has_classification = col_area_alim in filtered_df.columns and col_area_comm in filtered_df.columns

    if has_classification:
        st.markdown(f"### Alimento vs Commodity ({ano})")
        st.markdown(
            "Classificação baseada na **Portaria MDS nº 966/2024** (Cesta Básica de Alimentos)."
        )

        # Metrics
        total_alim = filtered_df[col_area_alim].sum()
        total_comm = filtered_df[col_area_comm].sum()
        total_area_class = total_alim + total_comm
        perc_alim = (total_alim / total_area_class * 100) if total_area_class > 0 else 0
        perc_comm = (total_comm / total_area_class * 100) if total_area_class > 0 else 0

        ma1, ma2, ma3, ma4 = st.columns(4)
        ma1.metric("Área Alimento", f"{total_alim/1e6:,.2f} mi ha".replace(",", "X").replace(".", ",").replace("X", "."))
        ma2.metric("Área Commodity", f"{total_comm/1e6:,.2f} mi ha".replace(",", "X").replace(".", ",").replace("X", "."))
        ma3.metric("% Alimento", f"{perc_alim:,.1f}%".replace(".", ","))
        ma4.metric("% Commodity", f"{perc_comm:,.1f}%".replace(".", ","))

        # Stacked bar by UF
        agg_uf_class = filtered_df.groupby("abbrev_state").agg(
            alimento=(col_area_alim, "sum"),
            commodity=(col_area_comm, "sum"),
        ).reset_index()
        agg_uf_class["total"] = agg_uf_class["alimento"] + agg_uf_class["commodity"]
        agg_uf_class = agg_uf_class.sort_values("total", ascending=False)

        fig_stack = go.Figure()
        fig_stack.add_trace(go.Bar(
            x=agg_uf_class["abbrev_state"], y=agg_uf_class["alimento"],
            name="Alimento", marker_color=COR_ALIMENTO,
        ))
        fig_stack.add_trace(go.Bar(
            x=agg_uf_class["abbrev_state"], y=agg_uf_class["commodity"],
            name="Commodity", marker_color=COR_COMMODITY,
        ))
        fig_stack.update_layout(
            **PLOTLY_LAYOUT,
            barmode="stack",
            title=f"Área plantada por UF — Alimento vs Commodity ({ano})",
            xaxis_title="UF",
            yaxis_title="Área plantada (ha)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=480,
        )
        st.plotly_chart(fig_stack, use_container_width=True)

        # Treemap and Top products (if detailed data available)
        if DATA_PROD is not None:
            prod_ano = DATA_PROD[DATA_PROD["ano"].astype(str) == str(ano)].copy()

            # Apply filters
            if st.session_state.filtro_regiao != "Todas" or st.session_state.filtro_uf != "Todas":
                muni_codes = filtered_df["code_muni"].astype(str).unique()
                prod_ano = prod_ano[prod_ano["code_muni"].astype(str).isin(muni_codes)]

            if not prod_ano.empty and "area_ha" in prod_ano.columns:
                # TreeMap
                prod_agg = prod_ano.groupby(["categoria", "grupo_portaria", "produto"]).agg(
                    area_ha=("area_ha", "sum")
                ).reset_index()
                prod_agg = prod_agg[prod_agg["area_ha"] > 0]

                if not prod_agg.empty:
                    fig_tree_prod = px.treemap(
                        prod_agg,
                        path=[px.Constant("Brasil"), "categoria", "grupo_portaria", "produto"],
                        values="area_ha",
                        color="categoria",
                        color_discrete_map={"alimento": COR_ALIMENTO, "commodity": COR_COMMODITY},
                        title=f"Composição por produto — Alimento vs Commodity ({ano})",
                    )
                    fig_tree_prod.update_layout(**PLOTLY_LAYOUT)
                    fig_tree_prod.update_layout(
                        margin=dict(t=50, l=10, r=10, b=10),
                        height=500,
                    )
                    fig_tree_prod.update_traces(root_color="lightgrey")
                    st.plotly_chart(fig_tree_prod, use_container_width=True)

                # Top 10 side by side
                st.markdown(f"### Principais Produtos ({ano})")
                t1, t2 = st.columns(2)

                with t1:
                    st.markdown("#### 🥗 Top 10 Alimentos")
                    top_alim = prod_ano[prod_ano["categoria"] == "alimento"].groupby("produto").agg(
                        area_total=("area_ha", "sum")
                    ).reset_index().nlargest(10, "area_total")
                    if not top_alim.empty:
                        top_alim["area_fmt"] = top_alim["area_total"].apply(
                            lambda x: f"{x/1e6:,.2f} mi ha".replace(",", "X").replace(".", ",").replace("X", ".")
                        )
                        st.dataframe(
                            top_alim[["produto", "area_fmt"]].rename(
                                columns={"produto": "Produto", "area_fmt": "Área Plantada"}
                            ),
                            use_container_width=True, hide_index=True,
                        )

                with t2:
                    st.markdown("#### 🏭 Top 10 Commodities")
                    top_comm = prod_ano[prod_ano["categoria"] == "commodity"].groupby("produto").agg(
                        area_total=("area_ha", "sum")
                    ).reset_index().nlargest(10, "area_total")
                    if not top_comm.empty:
                        top_comm["area_fmt"] = top_comm["area_total"].apply(
                            lambda x: f"{x/1e6:,.2f} mi ha".replace(",", "X").replace(".", ",").replace("X", ".")
                        )
                        st.dataframe(
                            top_comm[["produto", "area_fmt"]].rename(
                                columns={"produto": "Produto", "area_fmt": "Área Plantada"}
                            ),
                            use_container_width=True, hide_index=True,
                        )

        st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Correlational graphs
    c1, c2 = st.columns(2)

    with c1:
        # Scatter: area per capita vs food insecurity
        st.markdown(f"### Produção vs Insegurança Alimentar ({ano})")

        sdf = state_summary(filtered_df, ano)
        inseg_col = f"inseg_perc_dom_{ano}"
        
        merged = agg.merge(sdf[["abbrev_state", inseg_col]], on="abbrev_state", how="left")
        merged["area_per_capita"] = merged["area_plantada_ha"] / merged["populacao"]

        fig2 = px.scatter(
            merged, x="area_per_capita", y=inseg_col,
            text="abbrev_state",
            color_discrete_sequence=[COR_PRIMARIA],
            labels={
                "area_per_capita": "Área plantada per capita (ha/hab)",
                inseg_col: f"Inseg. alimentar (% dom., {ano})",
            },
        )
        fig2.update_traces(textposition="top center", marker=dict(size=10))
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            height=400,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with c2:
        # Scatter: Rural Pop vs Planted Area
        st.markdown("### População Rural vs Área Plantada")

        fig3 = px.scatter(
            agg, x="pop_rural", y="area_plantada_ha",
            text="abbrev_state",
            color_discrete_sequence=[COR_SECUNDARIA],
            labels={
                "pop_rural": "População Rural (hab)",
                "area_plantada_ha": "Área Plantada Total (ha)",
            },
        )
        fig3.update_traces(textposition="top center", marker=dict(size=10))
        fig3.update_layout(
            **PLOTLY_LAYOUT,
            height=400,
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown(
        """
**Nota interpretativa:** Uma correlação negativa no primeiro gráfico sugere que estados com maior produção
agrícola per capita tendem a apresentar menor proporção de domicílios em insegurança
alimentar. O segundo gráfico contrasta o contingente rural absoluto com a extensão da área produtiva. 
Os dados de produção referem-se à tabela 5457 / SIDRA (IBGE).
        """
    )


# -------------------------------------------------------------------------
# 4. Bolsa Família
# -------------------------------------------------------------------------
def pagina_bolsa_familia():
    ano = st.session_state.filtro_ano
    st.markdown(f"# Bolsa Família ({ano})")
    st.markdown(
        '<p class="subtitle">Cobertura e evolução das transferências do Programa Bolsa Família</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    agg = state_aggregates(filtered_df, ano)
    sdf = state_summary(filtered_df, ano)

    if agg.empty:
        st.warning("Sem dados do Bolsa Família disponíveis para os filtros selecionados.")
        return

    # Metrics
    c1, c2, c3 = st.columns(3)
    total_fam_ano = agg["bf_qtd_familias_media_ano"].sum()
    total_val_ano = agg["bf_valor_repassado_media_ano"].sum()
    total_val_2023 = agg["bf_valor_repassado_media_2023"].sum()
    
    # variacao só faz sentido visualmente contra o ano anterior se for 2024
    if ano == "2024" and total_val_2023:
        variacao = ((total_val_ano - total_val_2023) / total_val_2023 * 100)
    else:
        variacao = 0

    c1.metric(f"Famílias beneficiárias (média mensal {ano})", f"{total_fam_ano/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", "."))
    c2.metric(f"Repasse médio mensal {ano}", f"R$ {total_val_ano/1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", "."))
    if ano == "2024":
        c3.metric("Variação 2023 → 2024", f"{variacao:+.1f}%".replace(".", ","))

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    
    # ---------- Map: Bolsa Familia Municipal ----------
    st.markdown(f"### Mapa de Transferência de Renda ({ano})")
    st.markdown("Intensidade e cobertura do programa nos municípios. O tamanho representa a quantidade de famílias, a cor representa o valor do repasse municipal.")
    
    val_repassado_col = f"bf_valor_repassado_media_{ano}"
    familias_media_col = f"bf_qtd_familias_media_{ano}"
    
    map_data_bf = filtered_df.dropna(subset=["lat", "lon", val_repassado_col, familias_media_col]).copy()
    
    if not map_data_bf.empty:
        fig_map_bf = px.scatter_mapbox(
            map_data_bf,
            lat="lat",
            lon="lon",
            color=val_repassado_col,
            size=familias_media_col,
            hover_name="name_muni",
            hover_data={"abbrev_state": True, familias_media_col: True, val_repassado_col: True, "lat": False, "lon": False},
            color_continuous_scale="Viridis",
            zoom=3.0,
            center={"lat": -15.78, "lon": -47.92},
            mapbox_style="carto-positron",
            title=f"Distribuição municipal - Bolsa Família ({ano})"
        )
        fig_map_bf.update_layout(**PLOTLY_LAYOUT)
        fig_map_bf.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            height=550,
            coloraxis_colorbar=dict(title="Média Repasse (R$)"),
        )
        st.plotly_chart(fig_map_bf, use_container_width=True)
    else:
        st.info("Dados municipais insuficientes ou sem localização registrada.")

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

    # Distribution and Correlation
    c_box, c_scat = st.columns(2)

    val_repassado_col = f"bf_valor_repassado_media_{ano}"
    
    with c_box:
        st.markdown(f"### Distribuição de Repasse por Região ({ano})")
        # Ensure we have region in the data for boxplot
        data_box = filtered_df.dropna(subset=[val_repassado_col, "name_region"]).copy()
        
        if not data_box.empty:
            fig_box = px.box(
                data_box, 
                x="name_region", 
                y=val_repassado_col,
                color="name_region",
                title=f"Distribuição do repasse municipal ({ano})",
                labels={"name_region": "Região", val_repassado_col: "Repasse (R$)"}
            )
            # Using a log scale for Y could be good because SP capital vs small town
            fig_box.update_layout(
                **PLOTLY_LAYOUT, 
                yaxis_type="log",
                showlegend=False,
                height=450
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Dados insuficientes para este gráfico de distribuição.")

    with c_scat:
        st.markdown(f"### Cobertura BF vs Insegurança Alimentar ({ano})")
        inseg_col = f"inseg_perc_dom_{ano}"
        merged = agg.merge(sdf[["abbrev_state", inseg_col]], on="abbrev_state", how="left")
        merged["bf_cobertura_per_capita"] = merged["bf_qtd_familias_media_ano"] / merged["populacao"]

        fig2 = px.scatter(
            merged, x="bf_cobertura_per_capita", y=inseg_col,
            text="abbrev_state",
            color_discrete_sequence=[COR_PRIMARIA],
            labels={
                "bf_cobertura_per_capita": "Famílias BF / População",
                inseg_col: f"Inseg. alimentar (% dom., {ano})",
            },
        )
        fig2.update_traces(textposition="top center", marker=dict(size=10))
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            height=450,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        """
**Nota:** A distribuição logarítmica evidencia como o volume de repasses tem variância 
significativa dentro de regiões com grandes metrópoles. A correlação positiva entre 
cobertura do Bolsa Família e insegurança alimentar é esperada, uma vez que o programa 
direciona transferências a áreas de maior vulnerabilidade social.
        """
    )


# -------------------------------------------------------------------------
# 5. Análises Regionais
# -------------------------------------------------------------------------
def pagina_regionais():
    ano = st.session_state.filtro_ano
    st.markdown("# Análises Regionais")
    st.markdown(
        '<p class="subtitle">Visualização a nível municipal por unidade da federação</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    states = sorted(filtered_df["abbrev_state"].dropna().unique())

    if not states:
        st.warning("Nenhum estado disponível com os filtros atuais selecionados.")
        return

    # To respect the global filter logic if "Todas" is selected it gives a dropdown. 
    # If a specific UF is selected globally, we can lock it or default to it.
    if st.session_state.filtro_uf != "Todas":
        selected_state = st.session_state.filtro_uf
        st.info(f"O filtro global de UF ({selected_state}) está ativo.")
    else:
        selected_state = st.selectbox("Selecione a UF para análise detalhada", states, index=0)

    state_data = filtered_df[filtered_df["abbrev_state"] == selected_state].copy()

    # Key metrics for the state
    inseg_col = f"inseg_perc_dom_{ano}"
    st.markdown(f"### Indicadores – {selected_state} ({ano})")
    c1, c2, c3, c4 = st.columns(4)
    n_munis = state_data.shape[0]
    pop_total = state_data["populacao"].sum()
    inseg_uf = state_data[inseg_col].iloc[0] if (not state_data.empty and inseg_col in state_data.columns) else 0
    area_total = state_data["area_plantada_ha"].sum()

    c1.metric("Municípios Filtrados", f"{n_munis}")
    c2.metric("População", f"{pop_total/1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", "."))
    c3.metric(f"Inseg. alimentar ({ano})", f"{inseg_uf:,.1f}%".replace(".", ","))
    c4.metric("Área plantada", f"{area_total/1e3:,.0f} mil ha".replace(",", "."))

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Top 15 municipalities by population
    top_munis = state_data.nlargest(15, "populacao")

    # Top 15 municipalities charts
    tab1, tab2, tab3 = st.tabs([
        "Bolsa Família por município", 
        "Produção agrícola por município",
        "Dispersão: População vs Bolsa Família"
    ])

    val_repassado_col = f"bf_valor_repassado_media_{ano}"
    familias_media_col = f"bf_qtd_familias_media_{ano}"

    with tab1:
        if val_repassado_col in top_munis.columns:
            fig = px.bar(
                top_munis.sort_values(val_repassado_col, ascending=True),
                y="name_muni", x=val_repassado_col,
                orientation="h",
                color_discrete_sequence=[COR_PRIMARIA],
                labels={
                    "name_muni": "Município",
                    val_repassado_col: f"Repasse médio mensal BF {ano} (R$)",
                },
            )
            fig.update_layout(
                **PLOTLY_LAYOUT,
                title=f"Top 15 municípios por Repasse Bolsa Família ({selected_state} - {ano})",
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        top_area = state_data.nlargest(15, "area_plantada_ha")
        if not top_area.empty and top_area["area_plantada_ha"].sum() > 0:
            # Use a Treemap instead of bar chart here to highlight proportions differently
            fig_tree = px.treemap(
                top_area,
                path=[px.Constant("Top 15 Municípios"), "name_muni"],
                values="area_plantada_ha",
                color="area_plantada_ha",
                color_continuous_scale="Greens",
                title=f"Composição Top 15 - Área plantada ({selected_state})"
            )
            fig_tree.update_layout(**PLOTLY_LAYOUT)
            fig_tree.update_layout(
                height=500,
                margin=dict(t=40, l=10, r=10, b=10)
            )
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Sem dados de produção agrícola suficientes para estes municípios.")
        
    with tab3:
        # Scatter for municipalities
        if familias_media_col in state_data.columns:
            clean_state_data = state_data.dropna(subset=["populacao", familias_media_col])
            
            if not clean_state_data.empty:
                fig_scat2 = px.scatter(
                    clean_state_data, 
                    x="populacao", 
                    y=familias_media_col,
                    hover_name="name_muni",
                    color_discrete_sequence=[COR_SECUNDARIA],
                    labels={
                        "populacao": "População Total",
                        familias_media_col: f"Famílias BF (Média {ano})",
                    },
                    title=f"Correlação intraestadual: População vs Beneficiários ({ano})"
                )
                fig_scat2.update_layout(**PLOTLY_LAYOUT, height=500)
                st.plotly_chart(fig_scat2, use_container_width=True)
            else:
                st.info("Municípios insuficientes com dados de Bolsa Família reportados para dispersão.")

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Data table
    st.markdown("### Tabela de dados municipais")
    display_cols = [
        "name_muni", "populacao", "area_plantada_ha",
        familias_media_col, val_repassado_col,
    ]
    
    # Filter only available columns
    available_cols = [col for col in display_cols if col in state_data.columns]
    
    display_labels = {
        "name_muni": "Município",
        "populacao": "População",
        "area_plantada_ha": "Área plantada (ha)",
        familias_media_col: f"Famílias BF (média mensal {ano})",
        val_repassado_col: f"Repasse BF (R$ média mensal {ano})",
    }
    
    st.dataframe(
        state_data[available_cols].rename(columns=display_labels).sort_values(
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

# -------------------------------------------------------------------------
# 8. Alimento vs Commodity — ANÁLISE COMPLETA
# -------------------------------------------------------------------------
def _fmt_br(val, suffix=""):
    """Formata número no padrão brasileiro."""
    s = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s}{suffix}"

def pagina_alimento_commodity():
    ano = st.session_state.filtro_ano
    st.markdown(f"# Alimento vs Commodity ({ano})")
    st.markdown(
        '<p class="subtitle">Análise completa da produção agrícola municipal — alimentos da cesta básica vs commodities de exportação</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Classificação baseada na **Portaria MDS nº 966/2024**, que define os alimentos "
        "aptos a compor a Cesta Básica de Alimentos. Produtos de uso predominantemente "
        "industrial, fibra, combustível ou ração foram classificados como commodity."
    )

    # --- Column aliases ---
    col_area_alim = f"area_ha_alimento_{ano}"
    col_area_comm = f"area_ha_commodity_{ano}"
    col_ton_alim = f"qtd_toneladas_alimento_{ano}"
    col_ton_comm = f"qtd_toneladas_commodity_{ano}"
    col_val_alim = f"valor_mil_reais_alimento_{ano}"
    col_val_comm = f"valor_mil_reais_commodity_{ano}"
    col_perc_alim = f"perc_area_alimento_{ano}"
    col_n_alim = f"n_produtos_alimento_{ano}"
    inseg_col = f"inseg_perc_dom_{ano}"
    inseg_grave_col = f"inseg_grave_perc_dom_{ano}"

    has_class = col_area_alim in DATA.columns and col_area_comm in DATA.columns

    if not has_class:
        st.warning(
            "Os dados de classificação alimento/commodity ainda não foram gerados. "
            "Execute o script R `extract_producao_por_produto.R` e copie os arquivos para esta pasta."
        )
        return

    filtered_df = get_filtered_data()
    if filtered_df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    agg = state_aggregates(filtered_df, ano)
    sdf = state_summary(filtered_df, ano)

    # =====================================================================
    # SEÇÃO 1 — MÉTRICAS GERAIS
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown("### Indicadores Gerais")

    total_alim_area = filtered_df[col_area_alim].sum()
    total_comm_area = filtered_df[col_area_comm].sum()
    total_area = total_alim_area + total_comm_area
    p_alim = (total_alim_area / total_area * 100) if total_area > 0 else 0
    p_comm = (total_comm_area / total_area * 100) if total_area > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Área Alimento", f"{_fmt_br(total_alim_area/1e6)} mi ha")
    m2.metric("Área Commodity", f"{_fmt_br(total_comm_area/1e6)} mi ha")
    m3.metric("% Alimento", f"{p_alim:.1f}%".replace(".", ","))
    m4.metric("% Commodity", f"{p_comm:.1f}%".replace(".", ","))

    # Value and tonnage metrics
    has_val = col_val_alim in filtered_df.columns and col_val_comm in filtered_df.columns
    has_ton = col_ton_alim in filtered_df.columns and col_ton_comm in filtered_df.columns

    if has_val:
        val_a = filtered_df[col_val_alim].sum()
        val_c = filtered_df[col_val_comm].sum()
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Valor Alimento", f"R$ {_fmt_br(val_a/1e6)} bi")
        v2.metric("Valor Commodity", f"R$ {_fmt_br(val_c/1e6)} bi")
        if has_ton:
            ton_a = filtered_df[col_ton_alim].sum()
            ton_c = filtered_df[col_ton_comm].sum()
            v3.metric("Toneladas Alimento", f"{_fmt_br(ton_a/1e6)} mi t")
            v4.metric("Toneladas Commodity", f"{_fmt_br(ton_c/1e6)} mi t")

    st.markdown(
        "**Leitura:** Os indicadores resumem a produção agrícola classificada entre "
        "alimentos (destinados ao consumo humano direto, conforme a Portaria MDS nº 966) e "
        "commodities (uso industrial, fibra, exportação). A área plantada, o valor da "
        "produção e a quantidade produzida são exibidos para comparação direta."
    )

    # =====================================================================
    # SEÇÃO 2 — MAPA MUNICIPAL: PROPORÇÃO ALIMENTO
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown("### Mapa Municipal — Proporção de Produção Alimentar")

    map_df = filtered_df.dropna(subset=["lat", "lon"]).copy()
    if col_perc_alim in map_df.columns and not map_df.empty:
        map_df["area_total_class"] = map_df[col_area_alim].fillna(0) + map_df[col_area_comm].fillna(0)
        map_df = map_df[map_df["area_total_class"] > 0]

        if not map_df.empty:
            fig_map = px.scatter_mapbox(
                map_df,
                lat="lat", lon="lon",
                color=col_perc_alim,
                size="area_total_class",
                size_max=20,
                hover_name="name_muni",
                hover_data={"abbrev_state": True, col_perc_alim: ":.1f", "area_total_class": ":,.0f", "lat": False, "lon": False},
                color_continuous_scale=["#FF9800", "#FFEB3B", "#4CAF50"],
                range_color=[0, 100],
                zoom=3.0,
                center={"lat": -15.78, "lon": -47.92},
                mapbox_style="carto-positron",
            )
            fig_map.update_layout(**PLOTLY_LAYOUT)
            fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=550,
                                  coloraxis_colorbar=dict(title="% Alimento"))
            st.plotly_chart(fig_map, use_container_width=True)

    st.markdown(
        "**Leitura:** Cada ponto representa um município. A **cor** indica a proporção da "
        "área plantada dedicada a alimentos (verde = mais alimento, laranja = mais commodity). "
        "O **tamanho** representa a área total classificada. Municípios sem produção registrada "
        "não são exibidos."
    )

    # =====================================================================
    # SEÇÃO 3 — BARRAS EMPILHADAS POR UF (ÁREA + VALOR)
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown(f"### Área Plantada e Valor por UF ({ano})")

    agg_uf = filtered_df.groupby("abbrev_state").agg(
        alim_area=(col_area_alim, "sum"),
        comm_area=(col_area_comm, "sum"),
    ).reset_index()
    agg_uf["total"] = agg_uf["alim_area"] + agg_uf["comm_area"]
    agg_uf = agg_uf.sort_values("total", ascending=False)

    c_bar1, c_bar2 = st.columns(2)

    with c_bar1:
        fig_area = go.Figure()
        fig_area.add_trace(go.Bar(x=agg_uf["abbrev_state"], y=agg_uf["alim_area"], name="Alimento", marker_color=COR_ALIMENTO))
        fig_area.add_trace(go.Bar(x=agg_uf["abbrev_state"], y=agg_uf["comm_area"], name="Commodity", marker_color=COR_COMMODITY))
        fig_area.update_layout(**PLOTLY_LAYOUT, barmode="stack", title="Área plantada (ha)",
                               xaxis_title="UF", yaxis_title="ha",
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=450)
        st.plotly_chart(fig_area, use_container_width=True)

    if has_val:
        with c_bar2:
            agg_uf_val = filtered_df.groupby("abbrev_state").agg(
                alim_val=(col_val_alim, "sum"), comm_val=(col_val_comm, "sum"),
            ).reset_index()
            agg_uf_val["total"] = agg_uf_val["alim_val"] + agg_uf_val["comm_val"]
            agg_uf_val = agg_uf_val.sort_values("total", ascending=False)

            fig_val = go.Figure()
            fig_val.add_trace(go.Bar(x=agg_uf_val["abbrev_state"], y=agg_uf_val["alim_val"], name="Alimento", marker_color=COR_ALIMENTO))
            fig_val.add_trace(go.Bar(x=agg_uf_val["abbrev_state"], y=agg_uf_val["comm_val"], name="Commodity", marker_color=COR_COMMODITY))
            fig_val.update_layout(**PLOTLY_LAYOUT, barmode="stack", title="Valor da produção (Mil R$)",
                                   xaxis_title="UF", yaxis_title="Mil R$",
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=450)
            st.plotly_chart(fig_val, use_container_width=True)

    st.markdown(
        "**Leitura:** A composição da produção varia substancialmente entre UFs. "
        "Estados como MT e MS apresentam forte predominância de commodities (soja, algodão), "
        "enquanto estados do Nordeste e Sul tendem a maior participação de alimentos."
    )

    # =====================================================================
    # SEÇÃO 4 — PROPORÇÃO % ALIMENTO POR UF
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    c_perc, c_evol = st.columns(2)

    with c_perc:
        st.markdown(f"### Proporção de Alimento (%) por UF")
        agg_uf["perc_alim"] = (agg_uf["alim_area"] / agg_uf["total"] * 100).fillna(0)
        agg_uf_s = agg_uf.sort_values("perc_alim", ascending=True)

        fig_perc = px.bar(agg_uf_s, y="abbrev_state", x="perc_alim", orientation="h",
                          color_discrete_sequence=[COR_ALIMENTO],
                          labels={"abbrev_state": "UF", "perc_alim": "% Alimento"})
        fig_perc.update_layout(**PLOTLY_LAYOUT, height=500, xaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_perc, use_container_width=True)

    # =====================================================================
    # SEÇÃO 5 — EVOLUÇÃO 2023 → 2024
    # =====================================================================
    with c_evol:
        st.markdown("### Evolução 2023 → 2024")
        col_a23 = "area_ha_alimento_2023"
        col_c23 = "area_ha_commodity_2023"
        col_a24 = "area_ha_alimento_2024"
        col_c24 = "area_ha_commodity_2024"

        if all(c in filtered_df.columns for c in [col_a23, col_c23, col_a24, col_c24]):
            evol = pd.DataFrame({
                "Categoria": ["Alimento", "Commodity", "Alimento", "Commodity"],
                "Ano": ["2023", "2023", "2024", "2024"],
                "Área (ha)": [
                    filtered_df[col_a23].sum(), filtered_df[col_c23].sum(),
                    filtered_df[col_a24].sum(), filtered_df[col_c24].sum(),
                ],
            })
            fig_evol = px.bar(evol, x="Ano", y="Área (ha)", color="Categoria", barmode="group",
                              color_discrete_map={"Alimento": COR_ALIMENTO, "Commodity": COR_COMMODITY})
            fig_evol.update_layout(**PLOTLY_LAYOUT, height=500,
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_evol, use_container_width=True)
        else:
            st.info("Dados de 2023 e/ou 2024 indisponíveis para esta comparação.")

    st.markdown(
        "**Leitura:** O gráfico à esquerda mostra a proporção da área plantada dedicada a "
        "alimentos em cada UF. O gráfico à direita compara a evolução da área plantada total "
        "entre 2023 e 2024, para alimentos e commodities."
    )

    # =====================================================================
    # SEÇÃO 6 — CORRELAÇÕES
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown("### Correlações: Produção, Insegurança e Políticas Públicas")

    # 6a: % Alimento vs Insegurança
    st.markdown("#### % Alimento vs Insegurança")
    if inseg_col in filtered_df.columns:
        inseg_map = sdf.set_index("abbrev_state")[inseg_col].to_dict() if inseg_col in sdf.columns else {}
        agg_uf["inseg"] = agg_uf["abbrev_state"].map(inseg_map)
        plot_df = agg_uf.dropna(subset=["inseg", "perc_alim"])
        if not plot_df.empty:
            fig_s1 = px.scatter(plot_df, x="perc_alim", y="inseg", text="abbrev_state",
                                color_discrete_sequence=[COR_PRIMARIA],
                                labels={"perc_alim": "% Área Alimento", "inseg": f"Inseg. ({ano} %)"})
            fig_s1.update_traces(textposition="top center", marker=dict(size=10))
            fig_s1.update_layout(**PLOTLY_LAYOUT, height=450)
            st.plotly_chart(fig_s1, use_container_width=True)

    # 6b: Valor Alimento per capita vs Insegurança Grave
    st.markdown("#### Valor Alim. per capita vs Inseg. Grave")
    if has_val and inseg_grave_col in sdf.columns:
        inseg_g_map = sdf.set_index("abbrev_state")[inseg_grave_col].to_dict()
        if col_val_alim in agg.columns:
            agg_sc = agg.copy()
            agg_sc["val_alim_pc"] = agg_sc[col_val_alim] / agg_sc["populacao"] * 1000
            agg_sc["inseg_grave"] = agg_sc["abbrev_state"].map(inseg_g_map)
            plot_df2 = agg_sc.dropna(subset=["val_alim_pc", "inseg_grave"])
            if not plot_df2.empty:
                fig_s2 = px.scatter(plot_df2, x="val_alim_pc", y="inseg_grave", text="abbrev_state",
                                    color_discrete_sequence=[COR_GRAVE],
                                    labels={"val_alim_pc": "Valor Alim. per capita (R$/hab)", "inseg_grave": f"Inseg. Grave ({ano} %)"})
                fig_s2.update_traces(textposition="top center", marker=dict(size=10))
                fig_s2.update_layout(**PLOTLY_LAYOUT, height=450)
                st.plotly_chart(fig_s2, use_container_width=True)

    # 6c: % Commodity vs BF per capita
    st.markdown("#### % Commodity vs BF per capita")
    bf_col = f"bf_valor_repassado_media_{ano}"
    if bf_col in agg.columns:
        agg_sc3 = agg.copy()
        agg_sc3["bf_pc"] = agg_sc3[bf_col] / agg_sc3["populacao"] * 1000
        if col_area_comm in agg_sc3.columns and col_area_alim in agg_sc3.columns:
            agg_sc3["perc_comm_uf"] = (agg_sc3[col_area_comm] / (agg_sc3[col_area_alim] + agg_sc3[col_area_comm]) * 100).fillna(0)
            plot_df3 = agg_sc3.dropna(subset=["perc_comm_uf", "bf_pc"])
            if not plot_df3.empty:
                fig_s3 = px.scatter(plot_df3, x="perc_comm_uf", y="bf_pc", text="abbrev_state",
                                    color_discrete_sequence=[COR_SECUNDARIA],
                                    labels={"perc_comm_uf": "% Área Commodity", "bf_pc": f"BF per capita (R$/hab, {ano})"})
                fig_s3.update_traces(textposition="top center", marker=dict(size=10))
                fig_s3.update_layout(**PLOTLY_LAYOUT, height=450)
                st.plotly_chart(fig_s3, use_container_width=True)

    st.markdown(
        "**Leitura dos gráficos de correlação:**\n"
        "- **Primeiro:** Avalia se estados com maior proporção de área dedicada a alimentos apresentam menor insegurança alimentar.\n"
        "- **Segundo:** Relaciona o valor da produção alimentar per capita com a prevalência de insegurança grave.\n"
        "- **Terceiro:** Investiga se estados com maior proporção de commodities dependem mais do Bolsa Família per capita."
    )

    # =====================================================================
    # SEÇÃO 7 — MAPA: VALOR PRODUÇÃO ALIMENTAR
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown("### Mapa Municipal — Valor da Produção Alimentar")

    if has_val and has_ton:
        map_val = filtered_df.dropna(subset=["lat", "lon"]).copy()
        map_val = map_val[map_val[col_val_alim] > 0]
        if not map_val.empty:
            fig_mapv = px.scatter_mapbox(
                map_val, lat="lat", lon="lon",
                color=col_val_alim, size=col_ton_alim, size_max=18,
                hover_name="name_muni",
                hover_data={"abbrev_state": True, col_val_alim: ":,.0f", col_ton_alim: ":,.0f", "lat": False, "lon": False},
                color_continuous_scale="Greens",
                zoom=3.0, center={"lat": -15.78, "lon": -47.92},
                mapbox_style="carto-positron",
            )
            fig_mapv.update_layout(**PLOTLY_LAYOUT)
            fig_mapv.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=500,
                                   coloraxis_colorbar=dict(title="Valor (Mil R$)"))
            st.plotly_chart(fig_mapv, use_container_width=True)

        st.markdown(
            "**Leitura:** A **cor** indica o valor da produção alimentar municipal (em Mil R$) "
            "e o **tamanho** a quantidade produzida em toneladas. Polos em verde intenso concentram "
            "maior geração de valor a partir de culturas alimentares."
        )

    # =====================================================================
    # SEÇÃO 8 — DIVERSIDADE PRODUTIVA
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown("### Diversidade Produtiva vs Insegurança Alimentar")

    if col_n_alim in agg.columns and inseg_col in sdf.columns:
        inseg_map_div = sdf.set_index("abbrev_state")[inseg_col].to_dict()
        agg_div = agg.copy()
        agg_div["inseg_div"] = agg_div["abbrev_state"].map(inseg_map_div)
        agg_div["n_prod_medio"] = agg_div[col_n_alim] / agg_div["populacao"] * 10000  # per 10k hab
        plot_div = agg_div.dropna(subset=["inseg_div"])

        if not plot_div.empty:
            c_div1, c_div2 = st.columns(2)
            with c_div1:
                fig_div = px.scatter(plot_div, x=col_n_alim, y="inseg_div", text="abbrev_state",
                                     size="populacao", size_max=30,
                                     color_discrete_sequence=[COR_ALIMENTO],
                                     labels={col_n_alim: "Nº Produtos Alimento (soma munis)", "inseg_div": f"Inseg. Alimentar ({ano} %)"})
                fig_div.update_traces(textposition="top center")
                fig_div.update_layout(**PLOTLY_LAYOUT, height=420)
                st.plotly_chart(fig_div, use_container_width=True)

            with c_div2:
                # Bar chart: average n_products by region
                agg_div_reg = filtered_df.groupby("name_region").agg(
                    n_prod_medio=(col_n_alim, "mean")
                ).reset_index().sort_values("n_prod_medio", ascending=False)

                fig_div_bar = px.bar(agg_div_reg, x="name_region", y="n_prod_medio",
                                     color_discrete_sequence=[COR_ALIMENTO],
                                     labels={"name_region": "Região", "n_prod_medio": "Nº Médio de Produtos Alimento"})
                fig_div_bar.update_layout(**PLOTLY_LAYOUT, height=420)
                st.plotly_chart(fig_div_bar, use_container_width=True)

        st.markdown(
            "**Leitura:** A diversidade produtiva (número de produtos alimentares cultivados) "
            "pode indicar maior resiliência contra a insegurança alimentar. O gráfico à esquerda "
            "avalia essa relação por UF (tamanho = população). O gráfico à direita mostra a "
            "diversidade média por região."
        )

    # =====================================================================
    # SEÇÃO 9 — TOP PRODUTOS (BARRAS)
    # =====================================================================
    if DATA_PROD is not None:
        st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
        st.markdown(f"### Principais Produtos ({ano})")

        prod_ano = DATA_PROD[DATA_PROD["ano"].astype(str) == str(ano)].copy()
        if st.session_state.filtro_regiao != "Todas" or st.session_state.filtro_uf != "Todas":
            muni_codes = filtered_df["code_muni"].astype(str).unique()
            prod_ano = prod_ano[prod_ano["code_muni"].astype(str).isin(muni_codes)]

        if not prod_ano.empty and "area_ha" in prod_ano.columns:
            t1, t2 = st.columns(2)

            with t1:
                st.markdown("#### Top 10 Alimentos")
                top_a = prod_ano[prod_ano["categoria"] == "alimento"].groupby("produto").agg(
                    area_total=("area_ha", "sum")).reset_index().nlargest(10, "area_total")
                if not top_a.empty:
                    top_a = top_a.sort_values("area_total", ascending=True)
                    fig_ta = px.bar(top_a, y="produto", x="area_total", orientation="h",
                                    color_discrete_sequence=[COR_ALIMENTO],
                                    labels={"produto": "", "area_total": "Área plantada (ha)"})
                    fig_ta.update_layout(**PLOTLY_LAYOUT, height=400)
                    st.plotly_chart(fig_ta, use_container_width=True)

            with t2:
                st.markdown("#### Top 10 Commodities")
                top_c = prod_ano[prod_ano["categoria"] == "commodity"].groupby("produto").agg(
                    area_total=("area_ha", "sum")).reset_index().nlargest(10, "area_total")
                if not top_c.empty:
                    top_c = top_c.sort_values("area_total", ascending=True)
                    fig_tc = px.bar(top_c, y="produto", x="area_total", orientation="h",
                                    color_discrete_sequence=[COR_COMMODITY],
                                    labels={"produto": "", "area_total": "Área plantada (ha)"})
                    fig_tc.update_layout(**PLOTLY_LAYOUT, height=400)
                    st.plotly_chart(fig_tc, use_container_width=True)

            st.markdown(
                "**Leitura:** Os 10 produtos com maior área plantada em cada categoria. "
                "No Brasil, a soja lidera amplamente entre commodities, enquanto milho, "
                "cana-de-açúcar e feijão figuram entre os alimentos mais plantados."
            )

            # =============================================================
            # SEÇÃO 10 — TREEMAP POR PRODUTO
            # =============================================================
            st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
            st.markdown(f"### Composição da Produção por Produto ({ano})")

            prod_agg = prod_ano.groupby(["categoria", "grupo_portaria", "produto"]).agg(
                area_ha=("area_ha", "sum")).reset_index()
            prod_agg = prod_agg[prod_agg["area_ha"] > 0]

            if not prod_agg.empty:
                fig_tree = px.treemap(
                    prod_agg,
                    path=[px.Constant("Brasil"), "categoria", "grupo_portaria", "produto"],
                    values="area_ha", color="categoria",
                    color_discrete_map={"alimento": COR_ALIMENTO, "commodity": COR_COMMODITY},
                )
                fig_tree.update_layout(**PLOTLY_LAYOUT)
                fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=550)
                fig_tree.update_traces(root_color="lightgrey")
                st.plotly_chart(fig_tree, use_container_width=True)

            st.markdown(
                "**Leitura:** O treemap mostra a hierarquia da produção por categoria, grupo "
                "da Portaria e produto individual. O tamanho de cada bloco é proporcional à "
                "área plantada. Clique em um bloco para explorar os níveis inferiores."
            )

    # =====================================================================
    # SEÇÃO 11 — NOTA METODOLÓGICA
    # =====================================================================
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown(
        """
**Nota metodológica:** A classificação segue a Portaria MDS nº 966/2024, que define a
relação de alimentos aptos a compor a Cesta Básica de Alimentos. Produtos cujo uso
primário é industrial, fibra, combustível ou ração animal foram classificados como
commodity. Casos especiais: a **soja** é classificada como commodity (exportação
predominante, apesar do óleo de soja constar na Portaria); a **cana-de-açúcar** é
classificada como alimento (açúcar na cesta básica); o **milho** é classificado como
alimento (fubá, farinha de milho na cesta básica). Dados: SIDRA/IBGE, tabela 5457
(Produção Agrícola Municipal).
        """
    )



# =========================================================================
#  Router
# =========================================================================
PAGES = {
    "Apresentação": pagina_apresentacao,
    "Panorama Nacional": pagina_panorama,
    "Produção Agrícola": pagina_producao,
    "Alimento vs Commodity": pagina_alimento_commodity,
    "Bolsa Família": pagina_bolsa_familia,
    "Análises Regionais": pagina_regionais,
    "Metodologia": pagina_metodologia,
    "Download de Dados": pagina_download,
}

PAGES[pagina]()
