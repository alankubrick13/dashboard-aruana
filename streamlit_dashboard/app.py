"""
Aruanã – Observatório de Segurança Alimentar
Dashboard Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats
import os
import json
import base64
import urllib.request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Aruanã – Observatório de Segurança Alimentar",
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

# Estados da Amazônia Legal
AMAZONIA_LEGAL = {"AC", "AM", "AP", "MA", "MT", "PA", "RO", "RR", "TO"}
COR_AMAZONIA = "#1B813E"  # verde escuro para destaque

# Área territorial por UF (km2) - Fonte: IBGE
AREA_TERRITORIAL_UF = {
    "AC": 164173.433, "AL": 27830.656, "AP": 142470.762, "AM": 1559167.878, 
    "BA": 564722.611, "CE": 148894.444, "DF": 5760.784, "ES": 46074.453, 
    "GO": 340242.855, "MA": 329651.495, "MT": 903207.050, "MS": 357145.836, 
    "MG": 586513.993, "PA": 1245870.704, "PB": 56467.242, "PR": 199314.850, 
    "PE": 98067.881, "PI": 251755.485, "RJ": 43750.425, "RN": 52809.602, 
    "RS": 281707.151, "RO": 237730.865, "RR": 223644.530, "SC": 95730.684, 
    "SP": 248219.481, "SE": 21932.908, "TO": 277466.763
}

# ---------------------------------------------------------------------------
# Data loading & Filtering
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    csv_path = os.path.join(
        os.path.dirname(__file__),
        "dados_consolidados_v5.csv",
    )
    df = pd.read_csv(csv_path, sep=";", decimal=",", encoding="utf-8")
    return df

DATA = load_data()

# Load Brazil states GeoJSON for choropleth maps
@st.cache_data
def load_geojson():
    geojson_path = os.path.join(os.path.dirname(__file__), "br_states.json")
    if os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

BR_STATES_GEOJSON = load_geojson()

@st.cache_data
def load_geojson_mun():
    """Carrega GeoJSON simplificado de municípios brasileiros via URL (tbrugz)."""
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-100-mun.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        # Fallback silencioso ou log se necessário
        return None

BR_MUN_GEOJSON = load_geojson_mun()

# Load per-product data if available
@st.cache_data
def load_producao_produto():
    csv_path = os.path.join(os.path.dirname(__file__), "producao_por_produto.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=";", decimal=",", encoding="utf-8")
        return df
    return None

DATA_PROD = load_producao_produto()

# AdaptaBrasil Data Loading - Relative path for deployment
CLIMA_BASE_DIR = os.path.join(os.path.dirname(__file__), "adaptabrasil_csv")

@st.cache_data
def load_clima_indicator(rel_path):
    """Loads a climate indicator from AdaptaBrasil and joins it with municipal base."""
    abs_path = os.path.join(CLIMA_BASE_DIR, rel_path)
    if not os.path.exists(abs_path):
        return pd.DataFrame()
        
    df_clima = pd.read_csv(abs_path)
    # Standardize bridge key: name_muni + '/' + abbrev_state
    # AdaptaBrasil 'local_nome' is already in this format (e.g. 'Analândia/SP')
    
    # We join with the global DATA (filtered later in UI)
    df_base = DATA[["code_muni", "name_muni", "abbrev_state", "name_region", "populacao", "lat", "lon"]].copy()
    df_base["bridge_key"] = (
        df_base["name_muni"].str.strip().str.lower() + "/" + df_base["abbrev_state"].str.strip().str.lower()
    )
    df_clima["local_nome_lower"] = df_clima["local_nome"].str.strip().str.lower()
    
    df_joined = df_base.merge(
        df_clima[["local_nome", "local_nome_lower", "faixa", "faixa_cor", "valor"]],
        left_on="bridge_key",
        right_on="local_nome_lower",
        how="inner"
    )
    return df_joined

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
        
    # Garante a existência do total_dom_resp em todas as páginas
    if "total_dom_resp" not in df.columns:
        cols_dom = [c for c in df.columns if c.startswith("dom_resp_")]
        if cols_dom:
            df["total_dom_resp"] = df[cols_dom].sum(axis=1)
        
    return df

# Aggregates at state level based on filtered data and selected year
def state_summary(filtered_df, ano):
    """Retorna dados de insegurança alimentar a nível estadual."""
    cols_needed = [
        "abbrev_state", "name_region",
        f"inseg_perc_dom_{ano}", f"inseg_leve_perc_dom_{ano}",
        f"inseg_moderada_perc_dom_{ano}", f"inseg_grave_perc_dom_{ano}",
        "inseg_perc_dom_2023", "inseg_perc_dom_2024",
        "perc_area_alimento_2023", "perc_area_commodity_2023",
        "perc_area_alimento_2024", "perc_area_commodity_2024"
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
        total_dom_resp=("total_dom_resp", "sum"),
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
                 alt="Logo Aruanã"
                 style="width: 120px; margin-bottom: 10px;" />
            <div class="sidebar-subtitle">Observatório de Segurança Alimentar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        (":material/group:", "Gênero e Raça"),
        (":material/agriculture:", "Produção Agrícola"),
        (":material/account_balance_wallet:", "Bolsa Família"),
        (":material/thunderstorm:", "Mudanças Climáticas"),
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
        '<div class="footer-text">2026 Aruanã Instituto Pan-Amazônico</div>',
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
O presente painel reúne dados públicos sobre aspectos sociodemográficos, segurança alimentar e nutricional, produção agropecuária e transferências do Programa Bolsa Família para todo o Brasil. O objetivo é apresentar um retrato analítico e territorial da insegurança alimentar e nutricional no país, caracterizando as populações mais impactadas por este contecto. Os dados abrangem o período de 2023 a 2024 e são provenientes de fontes oficiais: IBGE (PNAD Contínua, Censo 2022 e Produção Agrícola Municipal) e Ministério do Desenvolvimento Social (Bolsa Família). A plataforma foi desenvolvida pelo Aruanã Instituto Pan-Amazônico como parte da Pesquisa de Segurança Alimentar e Nutricional, com a finalidade de subsidiar análises institucionais, relatórios técnicos e o acompanhamento de políticas públicas voltadas à garantia do direito humano à alimentação adequada.
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
    st.markdown(f"### Indicadores gerais do Brasil ({ano_referencia})")
    
    filtered_df = get_filtered_data()
    
    total_pop = filtered_df["populacao"].sum()
    total_munis = filtered_df["code_muni"].nunique()
    
    inseg_col = f"inseg_perc_dom_{ano_referencia}"
    inseg_grave_col = f"inseg_grave_perc_dom_{ano_referencia}"
    
    # Use grouped average to not let cities skew the state probability
    state_level = filtered_df[["abbrev_state", inseg_col, inseg_grave_col]].drop_duplicates()
    
    inseg_media_ano = state_level[inseg_col].mean() if not state_level.empty else 0
    inseg_grave_media_ano = state_level[inseg_grave_col].mean() if not state_level.empty else 0

    # First row
    m1, m2 = st.columns(2)
    m1.metric("Municípios analisados", f"{total_munis:,}".replace(",", "."))
    m2.metric("População Total (Censo)", f"{total_pop/1e6:,.1f} milhões".replace(",", "X").replace(".", ",").replace("X", "."))
    
    # Second row
    m3, m4 = st.columns(2)
    m3.metric("Insegurança alimentar (média por UF)", f"{inseg_media_ano:,.1f}%".replace(".", ","))
    m4.metric("Insegurança alimentar grave (média por UF)", f"{inseg_grave_media_ano:,.1f}%".replace(".", ","))

    st.markdown(
        "<link rel='stylesheet' href='https://cdn.jsdelivr.net/gh/jpswalsh/academicons@1/css/academicons.min.css'>"
        "<div style='text-align: center; margin-top: 3rem;'>"
        "<p style='color: #666; font-size: 0.95em;'>Desenvolvido por: "
        "<a href='https://linktr.ee/alankubrick' target='_blank' style='text-decoration: none; color: #1E3A5F; font-weight: bold;'>"
        "Alan Brito</a>"
        "</p></div>",
        unsafe_allow_html=True
    )


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

    st.markdown(
        """
> **Definição do IBGE:** Considera-se domicílio em situação de insegurança alimentar aquele
> em que seus moradores, nos últimos três meses, passaram por ao menos uma das seguintes
> situações: tiveram a preocupação de que os alimentos acabassem antes de poderem comprar
> ou receber mais comida, lhes faltaram alimentos antes que tivessem dinheiro para comprar
> mais comida, ficaram sem dinheiro para terem uma alimentação saudável e variada, e comeram
> apenas alguns poucos tipos de alimentos que ainda tinham porque o dinheiro acabou.
> A insegurança alimentar pode ser classificada como leve, moderada ou grave, de acordo
> com a restrição na qualidade e na quantidade de alimentos consumidos pelos moradores.
        """
    )

    # ---------- Bubble map: food insecurity by state ----------
    st.markdown(f"### Mapa de Insegurança Alimentar por UF ({ano})")
    inseg_col_map = f"inseg_perc_dom_{ano}"
    map_sdf = sdf.copy()
    # Compute average lat/lon per state for map
    state_coords = filtered_df.groupby("abbrev_state").agg(
        lat=("lat", "mean"), lon=("lon", "mean")
    ).reset_index()
    map_sdf = map_sdf.merge(state_coords, on="abbrev_state", how="left")
    map_sdf["amazonia_legal"] = map_sdf["abbrev_state"].apply(
        lambda x: "Amazônia Legal" if x in AMAZONIA_LEGAL else "Demais estados"
    )
    map_sdf = map_sdf.dropna(subset=["lat", "lon", inseg_col_map])

    if not map_sdf.empty:
        fig_map = px.choropleth_mapbox(
            map_sdf,
            geojson=BR_STATES_GEOJSON,
            locations="abbrev_state",
            featureidkey="properties.sigla",
            color=inseg_col_map,
            color_continuous_scale="Reds", # Tons de vermelho para alerta
            hover_name="abbrev_state",
            hover_data={inseg_col_map: ":.1f", "abbrev_state": False},
            zoom=3.0,
            center={"lat": -15.78, "lon": -47.92},
            mapbox_style="carto-positron",
            labels={inseg_col_map: "Domicílios em insegurança (% em 2024)"}
        )
        fig_map.update_layout(**PLOTLY_LAYOUT)
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=500,
            coloraxis_colorbar=dict(title="%"),
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown(
            "**Nota interpretativa:** A gradação de cor indica o percentual de domicílios em situação de "
            "insegurança alimentar em 2024. Estados com tons mais escuros possuem maior prevalência."
        )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- Bar chart: total food insecurity by state ----------
    st.markdown("### Panorama Nacional — Insegurança alimentar por unidade da federação (2023 e 2024)")
    
    # Ordenamos os dados do menor para o maior para exibição no gráfico de barras horizontais
    # de forma que o maior valor fique no topo listado
    sdf_sorted = sdf.sort_values(f"inseg_perc_dom_{ano}", ascending=True)

    # Define marker colors to highlight Amazônia Legal in 2024
    colors_2024 = [
        COR_AMAZONIA if uf in AMAZONIA_LEGAL else COR_PRIMARIA
        for uf in sdf_sorted["abbrev_state"]
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=sdf_sorted["abbrev_state"],
        x=sdf_sorted["inseg_perc_dom_2023"],
        orientation="h",
        name="2023",
        marker_color=COR_SECUNDARIA,
        text=sdf_sorted["inseg_perc_dom_2023"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        textfont=dict(size=16, weight="bold"),
        cliponaxis=False
    ))
    fig.add_trace(go.Bar(
        y=sdf_sorted["abbrev_state"],
        x=sdf_sorted["inseg_perc_dom_2024"],
        orientation="h",
        name="2024",
        marker_color=colors_2024,
        text=sdf_sorted["inseg_perc_dom_2024"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        textfont=dict(size=16, weight="bold"),
        cliponaxis=False
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Insegurança alimentar total (% domicílios) por UF",
        barmode="group",
        xaxis_title="% domicílios",
        yaxis_title="UF",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=1200
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
    st.markdown("**Composição por grau (2024)**")
    st.markdown(
        '<p style="font-size: 0.9em; color: #666;">As colunas do gráfico abaixo refletem a proporção de domicílios em insegurança alimentar no ano de 2024. '
        'O valor agregado do gráfico anterior é apresentado aqui com cores indicando a gravidade da insegurança alimentar nos domicílios brasileiros.</p>',
        unsafe_allow_html=True
    )
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
        xaxis=dict(tickangle=0) # Corrigir rotação das siglas (deixar horizontal como os demais)
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        """
> **Graus de insegurança alimentar (IBGE):**
> - **Leve:** preocupação ou incerteza quanto ao acesso a alimentos no futuro e/ou
>   comprometimento da qualidade da alimentação para não faltar.
> - **Moderada:** redução quantitativa de alimentos entre os adultos do domicílio
>   e/ou ruptura nos padrões de alimentação.
> - **Grave:** redução quantitativa de alimentos também entre crianças e/ou
>   situação de fome (ficar um dia inteiro sem comer por falta de dinheiro).
        """
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- Correlation: Rural Pop vs Insecurity ----------
    st.markdown(f"### Perfil Rural vs Insegurança ({ano})")
    agg_rural = filtered_df.groupby("abbrev_state").agg(
        pop_total=("populacao", "sum"),
        pop_rural=("pop_rural", "sum"),
        inseg_ref=(f"inseg_perc_dom_{ano}", "first")
    ).reset_index()
    agg_rural["perc_rural"] = (agg_rural["pop_rural"] / agg_rural["pop_total"]) * 100

    fig_scatter_pop = px.scatter(
        agg_rural, 
        x="inseg_ref", 
        y="perc_rural",
        text="abbrev_state",
        color_discrete_sequence=[COR_PRIMARIA],
        labels={
            "perc_rural": "% População Rural",
            "inseg_ref": "Insegurança Alimentar (%)",
            "abbrev_state": "UF"
        }
    )
    fig_scatter_pop.update_traces(textposition="top center", marker=dict(size=10))
    fig_scatter_pop.update_layout(
        **PLOTLY_LAYOUT,
        height=450,
    )
    st.plotly_chart(fig_scatter_pop, use_container_width=True)
    st.markdown(
        "**Nota interpretativa:** O gráfico de dispersão revela uma tendência de correlação positiva entre o percentual "
        "de população rural e a insegurança alimentar. Estados localizados no quadrante superior direito possuem maior "
        "ruralidade e maiores índices de insegurança alimentar, sugerindo que a vulnerabilidade alimentar é mais "
        "acentuada em contextos rurais no território brasileiro."
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    
    # ---------- Teste Estatístico: Insegurança vs Perfil Rural/Urbano ----------
    st.markdown("### Insegurança alimentar é mais alta em estados com maior população rural")
    # ... (código existente do teste t) ...
    mediana_rural = agg_rural["perc_rural"].median()
    agg_rural["perfil"] = agg_rural["perc_rural"].apply(
        lambda x: "Mais Rural" if x >= mediana_rural else "Mais Urbano"
    )
    
    grupo_urbano = agg_rural[agg_rural["perfil"] == "Mais Urbano"]["inseg_ref"].dropna()
    grupo_rural = agg_rural[agg_rural["perfil"] == "Mais Rural"]["inseg_ref"].dropna()
    
    if len(grupo_urbano) > 0 and len(grupo_rural) > 0:
        t_stat, p_valor = stats.ttest_ind(grupo_urbano, grupo_rural, equal_var=False)
        
        col_stats_left, col_stats_right = st.columns([2, 1])
        
        with col_stats_left:
            sub1, sub2 = st.columns(2)
            sub1.metric("Média de insegurança alimentar (Estados mais urbanos)", f"{grupo_urbano.mean():.1f}%")
            sub2.metric("Média de insegurança alimentar (Estados mais rurais)", f"{grupo_rural.mean():.1f}%")
            
            st.markdown(
                f"""
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 5px solid {COR_PRIMARIA};">
                    <strong>Nota explicativa:</strong> Os estados foram divididos em dois grupos com base na mediana da população rural ({mediana_rural:.1f}%). 
                    Foram comparados {len(grupo_urbano)} estados abaixo da mediana e {len(grupo_rural)} estados acima. 
                    Em termos práticos, o resultado mostra uma associação estatística entre maior ruralidade e maior insegurança alimentar.
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_stats_right:
            st.markdown("#### Resultado da comparação")
            if p_valor < 0.05:
                st.success("A diferença observada entre os dois grupos é estatisticamente significativa.")
                st.markdown("Isso indica que existe efetivamente uma maior insegurança alimentar nos estados mais rurais.")
            else:
                st.warning("A diferença não atingiu significância estatística (p > 0.05).")
    else:
        st.warning("Não há dados suficientes ou variação de perfis (Urbano/Rural) para realizar o teste t.")

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- NOVOS GRÁFICOS: VARIAÇÃO E MAGNITUDE ---
    st.markdown("### Dinâmica e Escala da Insegurança Alimentar")
    
    c_extra1, c_extra2 = st.columns(2)
    
    with c_extra1:
        st.markdown("#### Variação do Índice (2023 → 2024)")
        sdf["variacao"] = sdf["inseg_perc_dom_2024"] - sdf["inseg_perc_dom_2023"]
        sdf_var = sdf.sort_values("variacao", ascending=True)
        
        fig_var = px.bar(
            sdf_var, x="variacao", y="abbrev_state",
            orientation="h",
            color="variacao",
            color_continuous_scale=["#2E5E4E", "#f9f9f9", "#C00000"], # Verde para melhora, Vermelho para piora
            color_continuous_midpoint=0,
            labels={"variacao": "Diferença (p.p.)", "abbrev_state": "UF"}
        )
        fig_var.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
        st.plotly_chart(fig_var, use_container_width=True)
        
        st.markdown(
            """
            <div class="interpretative-note">
                <strong>Nota interpretativa:</strong> Este gráfico mostra a velocidade da mudança. Barras à esquerda (verdes) indicam estados que conseguiram reduzir a insegurança alimentar em pontos percentuais. Barras à direita (vermelhas) sinalizam onde o problema se agravou no último ano, demandando atenção prioritária.
            </div>
            """, unsafe_allow_html=True
        )

    with c_extra2:
        st.markdown("#### Concentração Regional da Insegurança")
        # Ponderar a insegurança pela população para mostrar magnitude
        agg_magnitude = filtered_df.groupby("name_region").agg({
            "populacao": "sum",
            f"inseg_perc_dom_{ano}": "mean"
        }).reset_index()
        
        fig_tree = px.treemap(
            agg_magnitude, path=["name_region"], values="populacao",
            color=f"inseg_perc_dom_{ano}",
            color_continuous_scale="Reds",
            labels={f"inseg_perc_dom_{ano}": "Insegurança (%)", "populacao": "População Total", "name_region": "Região"}
        )
        fig_tree.update_layout(**PLOTLY_LAYOUT, height=500)
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.markdown(
            """
            <div class="interpretative-note">
                <strong>Nota interpretativa:</strong> O tamanho dos blocos representa a população total de cada região, enquanto a cor indica a intensidade da insegurança alimentar. Isso permite identificar onde o desafio é maior não apenas em percentual, mas em número absoluto de cidadãos potencialmente afetados.
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)


# -------------------------------------------------------------------------
# 3. Produção Agrícola
# -------------------------------------------------------------------------
def pagina_producao():
    ano = st.session_state.filtro_ano
    st.markdown("# Produção Agrícola")
    st.markdown(
        '<p class="subtitle">Este módulo analisa o uso do território para fins produtivos e sua relação com a segurança alimentar, '
        'distinguindo entre cultivos voltados ao abastecimento interno (alimentos) e ao mercado externo (commodities).</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    agg = state_aggregates(filtered_df, ano)
    
    if agg.empty or agg["area_plantada_ha"].sum() == 0:
        st.warning("Sem dados de produção agrícola disponíveis para os filtros selecionados.")
        return
        
    agg = agg.sort_values("area_plantada_ha", ascending=False)
    
    # ---------- Map: Agricultural Production relative area ----------
    st.markdown("### Mapa de Produção Agrícola por Estado")
    st.markdown("Cores mais escuras apontam estados que dedicam as maiores parcelas de seu território à produção agrícola.")
    
    map_data_agri = agg.dropna(subset=["lat", "lon"]).copy()
    # Calcular proporção relativa à área do estado
    map_data_agri["area_uf_ha"] = map_data_agri["abbrev_state"].map(AREA_TERRITORIAL_UF) * 100
    map_data_agri["perc_territorio_agri"] = (map_data_agri["area_plantada_ha"] / map_data_agri["area_uf_ha"]) * 100

    if not map_data_agri.empty:
        fig_map_agri = px.choropleth_mapbox(
            map_data_agri,
            geojson=BR_STATES_GEOJSON,
            locations="abbrev_state",
            featureidkey="properties.sigla",
            color="perc_territorio_agri",
            hover_name="abbrev_state",
            hover_data={"populacao": True, "perc_territorio_agri": ":.1f%", "abbrev_state": False},
            color_continuous_scale="Greens",
            zoom=3.0,
            center={"lat": -15.78, "lon": -47.92},
            mapbox_style="carto-positron",
            labels={
                "perc_territorio_agri": "Área do estado de produção agrícola (%)",
                "populacao": "População"
            }
        )
        fig_map_agri.update_layout(**PLOTLY_LAYOUT)
        fig_map_agri.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            height=550,
            coloraxis_colorbar=dict(title="%"),
        )
        st.plotly_chart(fig_map_agri, use_container_width=True)
    else:
        st.info("Municípios insuficientes com dados geográficos ou agrícolas para mapas.")

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- Bar Chart: Agricultura by Region and State ----------
    st.markdown("### Composição da Área Plantada (Região e UF)")
    st.markdown(
        "Este gráfico mostra como a área plantada se distribui entre as grandes regiões e unidades da federação. "
        "O tamanho de cada coluna representa a área cultivada, permitindo identificar onde a produção agrícola está mais concentrada no território nacional.<br><br>"
        "A área plantada no Brasil se concentra fortemente em poucos estados, com destaque para o Centro-Oeste e o Sul. "
        "Esse padrão revela uma distribuição territorial desigual da produção agrícola, marcada pelo peso de polos regionais específicos.",
        unsafe_allow_html=True
    )
    
    fig_region = px.bar(
        agg.sort_values(["name_region", "area_plantada_ha"], ascending=[True, False]),
        x="name_region", y="area_plantada_ha",
        color="name_region",
        text="abbrev_state",
        labels={"name_region": "Região", "area_plantada_ha": "Área Plantada (ha)", "abbrev_state": "UF"},
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_region.update_layout(**PLOTLY_LAYOUT, height=500, showlegend=False)
    fig_region.update_traces(textposition="outside")
    st.plotly_chart(fig_region, use_container_width=True)

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
            "Este gráfico compara a área plantada classificada como alimento e como commodity nas unidades da federação em 2024, com base na Portaria MDS nº 966/2024. "
            "No agregado nacional, observa-se um quadro de relativo equilíbrio entre os dois grupos, com leve predominância das commodities: 50,72 milhões de hectares, ou 51,1% da área total, "
            "frente a 48,56 milhões de hectares destinados a alimentos, equivalentes a 48,9%."
        )

        # Metrics layout: 2 per line
        total_alim = filtered_df[col_area_alim].sum()
        total_comm = filtered_df[col_area_comm].sum()
        total_area_class = total_alim + total_comm
        perc_alim = (total_alim / total_area_class * 100) if total_area_class > 0 else 0
        perc_comm = (total_comm / total_area_class * 100) if total_area_class > 0 else 0

        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Área destinada a Alimentos", f"{total_alim/1e6:,.2f} milhões de hectares".replace(",", "X").replace(".", ",").replace("X", "."))
        c_m2.metric("Área destinada a Commodities", f"{total_comm/1e6:,.2f} milhões de hectares".replace(",", "X").replace(".", ",").replace("X", "."))
        
        c_m3, c_m4 = st.columns(2)
        c_m3.metric("Proporção Alimento (%)", f"{perc_alim:,.1f}%".replace(".", ","))
        c_m4.metric("Proporção Commodity (%)", f"{perc_comm:,.1f}%".replace(".", ","))

        # Value and tonnage (from deleted page)
        val_alim_col = f"valor_mil_reais_alimento_{ano}"
        val_comm_col = f"valor_mil_reais_commodity_{ano}"
        ton_alim_col = f"qtd_toneladas_alimento_{ano}"
        ton_comm_col = f"qtd_toneladas_commodity_{ano}"
        
        if all(c in filtered_df.columns for c in [val_alim_col, val_comm_col]):
            val_a = filtered_df[val_alim_col].sum()
            val_c = filtered_df[val_comm_col].sum()
            st.markdown(
                f"""
                <div style="background-color: #f0f7f2; padding: 15px; border-radius: 5px; border-left: 5px solid {COR_ALIMENTO}; margin-bottom: 20px;">
                    <strong>Destaque Econômico:</strong> Embora os alimentos ocupem menos área plantada do que as commodities (48,9% contra 51,1%), eles geram maior valor agregado. 
                    Mesmo com menor volume em toneladas, a produção de alimentos alcança <strong>R$ {val_a/1e6:,.2f} bilhões</strong>, 
                    acima dos <strong>R$ {val_c/1e6:,.2f} bilhões</strong> das commodities.
                </div>
                """,
                unsafe_allow_html=True
            )
            v1, v2 = st.columns(2)
            v1.metric("Valor total alimentos", f"R$ {val_a/1e6:,.2f} bilhões".replace(",", "X").replace(".", ",").replace("X", "."))
            v2.metric("Valor total commodities", f"R$ {val_c/1e6:,.2f} bilhões".replace(",", "X").replace(".", ",").replace("X", "."))
            
            if all(c in filtered_df.columns for c in [ton_alim_col, ton_comm_col]):
                ton_a = filtered_df[ton_alim_col].sum()
                ton_c = filtered_df[ton_comm_col].sum()
                v3, v4 = st.columns(2)
                v3.metric("Volume produzido (Alimentos)", f"{ton_a/1e6:,.2f} milhões de toneladas".replace(",", "X").replace(".", ",").replace("X", "."))
                v4.metric("Volume produzido (Commodities)", f"{ton_c/1e6:,.2f} milhões de toneladas".replace(",", "X").replace(".", ",").replace("X", "."))

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
            name="Alimento", marker_color=COR_PRIMARIA,
        ))
        fig_stack.add_trace(go.Bar(
            x=agg_uf_class["abbrev_state"], y=agg_uf_class["commodity"],
            name="Commodity", marker_color=COR_GRAVE,
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
        
        st.markdown(
            "**Análise:** Estados com grande peso na produção agrícola, como Mato Grosso, Paraná e Rio Grande do Sul, concentram parcelas expressivas da área plantada e, "
            "em vários casos, apresentam forte participação de commodities, o que influencia o resultado nacional. Em contraste, outras UFs exibem composição mais equilibrada "
            "ou maior presença relativa de cultivos voltados à alimentação.<br><br>"
            "Entre os estados que concentram a maior área plantada do país, predomina a produção voltada às commodities de exportação, o que aprofunda as tensões "
            "entre o modelo agroexportador, o abastecimento interno e a segurança alimentar.",
            unsafe_allow_html=True
        )

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
                    st.markdown("#### Detalhamento da Produção por Categoria")
                    # Tabela em vez de Treemap para melhor leitura
                    prod_table = prod_agg.groupby(["categoria", "produto"]).agg(area_ha=("area_ha", "sum")).reset_index()
                    # Adicionar coluna de % dentro da categoria
                    total_cat = prod_table.groupby("categoria")["area_ha"].transform("sum")
                    prod_table["percentual_categoria"] = (prod_table["area_ha"] / total_cat) * 100
                    
                    # Formatar colunas
                    prod_table["Área plantada (em milhões de hectares)"] = prod_table["area_ha"].apply(lambda x: f"{x/1e6:.2f}")
                    prod_table["Participação na categoria (%)"] = prod_table["percentual_categoria"].apply(lambda x: f"{x:.1f}%")
                    
                    st.dataframe(
                        prod_table[["categoria", "produto", "Área plantada (em milhões de hectares)", "Participação na categoria (%)"]],
                        use_container_width=True, hide_index=True
                    )

                # Top 10 side by side
                st.markdown(f"### Principais Produtos ({ano})")
                t1, t2 = st.columns(2)

                with t1:
                    st.markdown("#### Top 10 Alimentos")
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
                    st.markdown("#### Top 10 Commodities")
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
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    st.markdown("### Relação entre produção e Insegurança Alimentar")
    
    sdf = state_summary(filtered_df, ano)
    inseg_col_scat = f"inseg_perc_dom_{ano}"
    
    merged = agg.merge(sdf[["abbrev_state", inseg_col_scat]], on="abbrev_state", how="left")
    merged["area_territorial_ha"] = merged["abbrev_state"].map(AREA_TERRITORIAL_UF) * 100
    merged["proporcao_area_plantada"] = (merged["area_plantada_ha"] / merged["area_territorial_ha"]) * 100
    merged["amazonia_legal"] = merged["abbrev_state"].apply(
        lambda x: "Amazônia Legal" if x in AMAZONIA_LEGAL else "Demais estados"
    )

    fig2 = px.scatter(
        merged, x=inseg_col_scat, y="proporcao_area_plantada",
        text="abbrev_state",
        color="amazonia_legal",
        color_discrete_map={
            "Amazônia Legal": COR_AMAZONIA,
            "Demais estados": "#607D8B", # Cor mais neutra para destaque da Amazônia
        },
        labels={
            inseg_col_scat: "Domicílios em insegurança alimentar (%)",
            "proporcao_area_plantada": "Área do estado de produção agrícola (%)",
            "amazonia_legal": "Região",
            "abbrev_state": "UF"
        },
    )
    fig2.update_traces(textposition="top center", marker=dict(size=12))
    fig2.update_layout(
        **PLOTLY_LAYOUT,
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown(
        "**Análise:** Os dados mostram que produção agrícola e segurança alimentar não caminham necessariamente juntas. "
        "Embora alguns estados com maior proporção de área cultivada apresentem níveis relativamente menores de insegurança alimentar, "
        "o padrão geral é heterogêneo e revela que o volume produzido, isoladamente, não explica o acesso da população à alimentação adequada.<br><br>"
        "A segurança alimentar da população depende menos da produção em si e mais da articulação entre modelo produtivo, distribuição territorial, renda e acesso efetivo aos alimentos.",
        unsafe_allow_html=True
    )

    # ---------- Map Selector and Visualization ----------
    st.markdown("### Mapa de Produção de Alimentos")
    st.markdown(
        "Utilize o seletor abaixo para alternar entre a visão consolidada por **Estado** ou detalhada por **Município**. "
        "O mapa utiliza uma escala coroplética onde tons de verde mais escuros indicam maiores áreas destinadas ao cultivo de alimentos."
    )
    
    nivel_detalhe = st.radio(
        "Nível de detalhamento do mapa:",
        ["Estado", "Município"],
        horizontal=True,
        key="mapa_producao_nivel"
    )

    col_map_alim = f"area_ha_alimento_{ano}"

    if nivel_detalhe == "Estado":
        # Agregação por Estado
        agg_state = state_aggregates(filtered_df, ano)
        if not agg_state.empty and col_map_alim in agg_state.columns:
            fig_map_alim = px.choropleth_mapbox(
                agg_state,
                geojson=BR_STATES_GEOJSON,
                locations="abbrev_state",
                featureidkey="properties.sigla",
                color=col_map_alim,
                hover_name="abbrev_state",
                hover_data={col_map_alim: ":,.0f", "abbrev_state": False},
                color_continuous_scale="YlGn",
                zoom=3, center={"lat": -15.78, "lon": -47.92},
                mapbox_style="carto-positron",
                labels={col_map_alim: "Área Alimento (ha)", "abbrev_state": "UF"}
            )
            fig_map_alim.update_layout(**PLOTLY_LAYOUT)
            fig_map_alim.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=550)
            st.plotly_chart(fig_map_alim, use_container_width=True)
    else:
        # Visão por Município
        if BR_MUN_GEOJSON is None:
            st.error("Não foi possível carregar os dados geográficos dos municípios. Exibindo visão por pontos como alternativa.")
            # Fallback for municipalities if GeoJSON fails
            map_df_alim = filtered_df.dropna(subset=["lat", "lon", col_map_alim]).copy()
            if not map_df_alim.empty:
                fig_map_alim = px.scatter_mapbox(
                    map_df_alim, lat="lat", lon="lon", color=col_map_alim, size=col_map_alim,
                    size_max=15, color_continuous_scale="YlGn",
                    hover_name="name_muni",
                    hover_data={"abbrev_state": True, col_map_alim: ":,.0f"},
                    zoom=3, center={"lat": -15.78, "lon": -47.92}, mapbox_style="carto-positron",
                    labels={col_map_alim: "Área Alimento (ha)", "abbrev_state": "UF"}
                )
                fig_map_alim.update_layout(**PLOTLY_LAYOUT)
                fig_map_alim.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=550)
                st.plotly_chart(fig_map_alim, use_container_width=True)
        else:
            # Choropleth Municipal
            map_df_alim = filtered_df.dropna(subset=[col_map_alim]).copy()
            # Garante que code_muni seja string limpa (removendo .0 se for float)
            map_df_alim["code_muni_str"] = map_df_alim["code_muni"].apply(
                lambda x: str(int(float(x))) if pd.notnull(x) else None
            )
            
            fig_map_alim = px.choropleth_mapbox(
                map_df_alim,
                geojson=BR_MUN_GEOJSON,
                locations="code_muni_str",
                featureidkey="properties.id", # Ajustado para properties.id conforme estrutura do GeoJSON
                color=col_map_alim,
                hover_name="name_muni",
                hover_data={"abbrev_state": True, col_map_alim: ":,.0f", "code_muni_str": False},
                color_continuous_scale="YlGn",
                zoom=3, center={"lat": -15.78, "lon": -47.92},
                mapbox_style="carto-positron",
                labels={col_map_alim: "Área Alimento (ha)", "abbrev_state": "UF"}
            )
            fig_map_alim.update_layout(**PLOTLY_LAYOUT)
            fig_map_alim.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=550)
            st.plotly_chart(fig_map_alim, use_container_width=True)
    
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    
    # ---------- Proportion Food by UF ----------
    st.markdown("### Participação dos Alimentos na Área Plantada por Estado")
    st.markdown(
        "O gráfico abaixo apresenta o percentual da área total cultivada que é dedicado a alimentos em cada estado. "
        "Valores próximos a 100% indicam estados onde quase toda a produção agrícola se volta ao consumo interno, "
        "enquanto valores baixos revelam o predomínio de commodities de exportação."
    )
    
    col_perc_alim = f"perc_area_alimento_{ano}"
    sdf_perc = state_summary(filtered_df, ano)
    sdf_perc = sdf_perc.sort_values(col_perc_alim, ascending=False)
    
    colors_alim = [COR_AMAZONIA if uf in AMAZONIA_LEGAL else COR_ALIMENTO for uf in sdf_perc["abbrev_state"]]
    
    fig_perc_alim = px.bar(
        sdf_perc, x=col_perc_alim, y="abbrev_state",
        orientation="h",
        text=sdf_perc[col_perc_alim].apply(lambda x: f"{x:.1f}%"),
        color_discrete_sequence=[COR_ALIMENTO],
        labels={col_perc_alim: "% Área destinada a Alimentos", "abbrev_state": "UF"}
    )
    fig_perc_alim.update_traces(marker_color=colors_alim, textposition="outside")
    fig_perc_alim.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(range=[0, 110]), # Para caber o label
        height=600
    )
    st.plotly_chart(fig_perc_alim, use_container_width=True)
    
    st.markdown(
        "**Análise:** Os estados da Amazônia Legal (em verde) apresentam, em geral, uma composição mais equilibrada ou majoritariamente voltada a alimentos, "
        "em comparação aos grandes polos do agronegócio exportador. Isso reforça o papel estratégico dessas regiões para a soberania alimentar local, "
        "apesar dos desafios logísticos e ambientais."
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # ---------- Diversity vs IA ----------
    st.markdown("### Diversidade Agrícola e Segurança Alimentar")
    st.markdown(
        "A diversidade agrícola municipal, medida como o número de diferentes tipos de alimentos cultivados, "
        "é um fator protetivo importante contra a insegurança alimentar. Territórios com produção variada tendem a ser "
        "mais resilientes a choques climáticos e flutuações de mercado, garantindo maior oferta local de alimentos."
    )

    col_div = f"n_produtos_alimento_{ano}"
    inseg_col_div = f"inseg_perc_dom_{ano}"
    
    fig_div_scat = px.scatter(
        filtered_df, x=col_div, y=inseg_col_div,
        color="abbrev_state",
        labels={col_div: "Nº de variedades produzidas", inseg_col_div: "Insegurança alimentar (%)", "abbrev_state": "UF"},
        opacity=0.6
    )
    fig_div_scat.update_layout(**PLOTLY_LAYOUT, height=450, showlegend=True)
    st.plotly_chart(fig_div_scat, use_container_width=True)

    st.markdown(
        "**Correlação:** À medida que a diversidade de produtos alimentares aumenta, observa-se uma tendência de redução nos níveis médios "
        "de insegurança alimentar nos municípios. Municípios com alta diversidade (mais de 10 variedades) raramente apresentam taxas extremas de fome."
    )

    # State average diversity bar
    st.markdown("#### Média de diversidade agrícola por estado")
    div_state = filtered_df.groupby("abbrev_state")[col_div].mean().sort_values(ascending=False).reset_index()
    
    fig_div_bar = px.bar(
        div_state, x="abbrev_state", y=col_div,
        text=div_state[col_div].apply(lambda x: f"{x:.1f}"),
        color_discrete_sequence=[COR_PRIMARIA],
        labels={"abbrev_state": "UF", col_div: "Média de variedades"}
    )
    fig_div_bar.update_traces(textposition="outside")
    fig_div_bar.update_layout(**PLOTLY_LAYOUT, height=400, yaxis=dict(range=[0, div_state[col_div].max() * 1.2]))
    st.plotly_chart(fig_div_bar, use_container_width=True)

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # Seção de Evolução 2023 → 2024
    st.markdown("### Evolução da Área Plantada: 2023 → 2024")
    if all(c in filtered_df.columns for c in ["area_ha_alimento_2023", "area_ha_commodity_2023", "area_ha_alimento_2024", "area_ha_commodity_2024"]):
        evol = pd.DataFrame({
            "Categoria": ["Alimentos", "Commodities", "Alimentos", "Commodities"],
            "Ano": ["2023", "2023", "2024", "2024"],
            "Área (ha)": [
                filtered_df["area_ha_alimento_2023"].sum(), filtered_df["area_ha_commodity_2023"].sum(),
                filtered_df["area_ha_alimento_2024"].sum(), filtered_df["area_ha_commodity_2024"].sum(),
            ],
        })
        
        # Cores solicitadas: Verde (COR_PRIMARIA) e Vermelho (COR_GRAVE)
        fig_evol = px.bar(evol, x="Ano", y="Área (ha)", color="Categoria", barmode="group",
                           color_discrete_map={"Alimentos": COR_PRIMARIA, "Commodities": COR_GRAVE})
        fig_evol.update_layout(**PLOTLY_LAYOUT, height=500,
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_evol, use_container_width=True)
        
        st.markdown(
            """
            <div class="interpretative-note">
                <strong>Nota interpretativa:</strong> A comparação entre 2023 e 2024 revela a dinâmica de uso do solo no país. 
                A variação nas barras indica se houve expansão da fronteira agrícola ou substituição de culturas. 
                Manter o equilíbrio entre o crescimento das commodities e a preservação das áreas de alimentos é fundamental para estabilizar os preços internos e garantir a segurança alimentar da população.
            </div>
            """, unsafe_allow_html=True
        )
    else:
        st.info("Séries históricas comparativas para 2023/24 não encontradas.")

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)


# -------------------------------------------------------------------------
# 4. Bolsa Família
# -------------------------------------------------------------------------
def pagina_bolsa_familia():
    ano = st.session_state.filtro_ano
    st.markdown("# Bolsa Família e Segurança Alimentar")
    st.markdown(
        '<p class="subtitle">Análise do impacto das transferências de renda na mitigação da fome e na proteção social do território brasileiro.</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    col_familias = f"bf_qtd_familias_media_{ano}"
    col_valor = f"bf_valor_repassado_media_{ano}"
    inseg_col = f"inseg_perc_dom_{ano}"
    inseg_grave_col = f"inseg_grave_perc_dom_{ano}"

    # Cálculos de Impacto (Convertendo de Anual para Mensal)
    total_familias = filtered_df[col_familias].sum()
    valor_anual_total = filtered_df[col_valor].sum()
    total_dom = filtered_df["total_dom_resp"].sum()
    
    investimento_mensal = valor_anual_total / 12
    repasse_medio_mensal = (valor_anual_total / total_familias / 12) if total_familias > 0 else 0
    cobertura_nacional = (total_familias / total_dom * 100) if total_dom > 0 else 0

    # --- BLOCO DE KPIs ---
    st.markdown("### Indicadores de Desempenho do Programa (Médias Mensais)")
    
    k_row1_1, k_row1_2 = st.columns(2)
    with k_row1_1:
        st.metric("Famílias Atendidas", f"{total_familias/1e6:,.1f} Mi".replace(",", "."))
    with k_row1_2:
        st.metric("Investimento Mensal Total", f"R$ {investimento_mensal/1e6:,.1f} Mi".replace(",", "X").replace(".", ",").replace("X", "."))
    
    k_row2_1, k_row2_2 = st.columns(2)
    with k_row2_1:
        st.metric("Benefício Médio Mensal", f"R$ {repasse_medio_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with k_row2_2:
        st.metric("Cobertura de Domicílios", f"{cobertura_nacional:.1f}%".replace(".", ","))

    st.markdown(
        f"""
        <div class="interpretative-note">
            <strong>Nota interpretativa:</strong> Estes indicadores mostram a escala do programa no território selecionado. 
            A <strong>Cobertura de Domicílios</strong> ({cobertura_nacional:.1f}%) é um dado essencial: ele indica qual parcela da população depende diretamente desse repasse para compor sua renda mensal e acessar alimentos básicos.
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- SEÇÃO DE MAPAS ---
    st.markdown("### Análise Territorial: Investimento e Necessidade")
    
    c_map1, c_map2 = st.columns(2)
    
    state_agg_bf = filtered_df.groupby("abbrev_state").agg({
        col_valor: "sum",
        col_familias: "sum",
        "total_dom_resp": "sum",
        inseg_grave_col: "first"
    }).reset_index()
    
    state_agg_bf["cobertura"] = (state_agg_bf[col_familias] / state_agg_bf["total_dom_resp"]) * 100

    with c_map1:
        st.markdown("#### Cobertura do Programa por Estado")
        fig_map_cov = px.choropleth_mapbox(
            state_agg_bf, geojson=BR_STATES_GEOJSON, locations="abbrev_state", featureidkey="properties.sigla",
            color="cobertura", color_continuous_scale="Blues",
            zoom=2.5, center={"lat": -15.78, "lon": -47.92}, mapbox_style="carto-positron"
        )
        fig_map_cov.update_layout(**PLOTLY_LAYOUT)
        fig_map_cov.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=400)
        st.plotly_chart(fig_map_cov, use_container_width=True)
        st.markdown(
            """
            <div class="interpretative-note">
                <strong>Nota interpretativa:</strong> Tons mais escuros indicam estados onde o Bolsa Família chega a uma fatia maior da população. 
                Isso geralmente ocorre em regiões onde o mercado de trabalho formal é menos dinâmico.
            </div>
            """, unsafe_allow_html=True
        )

    with c_map2:
        st.markdown("#### Insegurança Alimentar Grave (Fome)")
        fig_map_fome = px.choropleth_mapbox(
            state_agg_bf, geojson=BR_STATES_GEOJSON, locations="abbrev_state", featureidkey="properties.sigla",
            color=inseg_grave_col, color_continuous_scale="Reds",
            zoom=2.5, center={"lat": -15.78, "lon": -47.92}, mapbox_style="carto-positron"
        )
        fig_map_fome.update_layout(**PLOTLY_LAYOUT)
        fig_map_fome.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=400)
        st.plotly_chart(fig_map_fome, use_container_width=True)
        st.markdown(
            """
            <div class="interpretative-note">
                <strong>Nota interpretativa:</strong> Este mapa identifica as áreas de maior urgência. Ao comparar com o mapa ao lado, é possível verificar se o programa está conseguindo cobrir as áreas onde a fome é mais prevalente.
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- SEÇÃO DE CORRELAÇÃO ---
    st.markdown("### Relação entre Transferência de Renda e Segurança Alimentar")
    
    fig_corr = px.scatter(
        state_agg_bf, x="cobertura", y=inseg_grave_col,
        text="abbrev_state", trendline="ols",
        labels={"cobertura": "Cobertura do Bolsa Família (%)", inseg_grave_col: "Fome - Insegurança Grave (%)"},
        color_discrete_sequence=[COR_PRIMARIA]
    )
    fig_corr.update_traces(textposition="top center", marker=dict(size=12))
    fig_corr.update_layout(**PLOTLY_LAYOUT, height=500)
    st.plotly_chart(fig_corr, use_container_width=True)
    
    st.markdown(
        f"""
        <div class="interpretative-note">
            <strong>Nota interpretativa:</strong> O gráfico mostra que existe uma forte ligação entre a cobertura do programa e a necessidade social. 
            A linha de tendência ascendente confirma que o Bolsa Família está concentrado exatamente onde a fome é maior. Isso valida a <strong>focalização do programa</strong>: o recurso está chegando aos territórios que mais precisam de suporte para garantir a alimentação básica.
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- RANKING DE PRIORIDADE ---
    st.markdown("### Ranking de Dependência e Necessidade por Estado")
    
    state_agg_bf["indice_prioridade"] = (state_agg_bf["cobertura"] + state_agg_bf[inseg_grave_col]) / 2
    state_agg_bf = state_agg_bf.sort_values("indice_prioridade", ascending=True)
    
    fig_rank = px.bar(
        state_agg_bf, x="indice_prioridade", y="abbrev_state",
        orientation="h",
        color="indice_prioridade", color_continuous_scale="Reds",
        labels={"indice_prioridade": "Índice de Necessidade Combinada", "abbrev_state": "Estado"}
    )
    fig_rank.update_layout(**PLOTLY_LAYOUT, height=600, showlegend=False)
    st.plotly_chart(fig_rank, use_container_width=True)
    
    st.markdown(
        """
        <div class="interpretative-note">
            <strong>Nota interpretativa:</strong> Este ranking combina a cobertura do programa com o índice de fome. 
            Estados no topo da lista possuem o maior nexo de dependência: neles, o Bolsa Família é o principal pilar que evita um agravamento ainda maior da insegurança alimentar. 
            São territórios onde qualquer interrupção no fluxo de pagamentos teria efeitos imediatos e severos na saúde nutricional da população.
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)



# -------------------------------------------------------------------------
# 5. Gênero e Raça
# -------------------------------------------------------------------------
def pagina_genero_raca():
    ano = st.session_state.filtro_ano
    inseg_col = f"inseg_perc_dom_{ano}"
    inseg_grave_col = f"inseg_grave_perc_dom_{ano}"
    st.markdown("# Gênero e Raça")
    st.markdown(
        '<p class="subtitle">Esta página reúne evidências sobre como gênero, raça, renda e território se cruzam na produção das desigualdades sociais no Brasil. '
        'A partir de indicadores de chefia domiciliar, rendimento do trabalho e distribuição espacial da vulnerabilidade, mostramos que a exposição à insegurança alimentar é resultado de fatores demográficos e territoriais que se reforçam mutuamente.<br><br>'
        'Os dados revelam que perfis historicamente mais vulnerabilizados se concentram em territórios também marcados por maiores níveis de pobreza e insegurança alimentar. '
        'Assim, a análise interseccional permite identificar onde as desigualdades se acumulam e onde políticas públicas focalizadas podem produzir maior impacto.</p>',
        unsafe_allow_html=True,
    )

    filtered_df = get_filtered_data()
    
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- DADOS GLOBAIS DA PÁGINA ---
    cols_dom = [c for c in filtered_df.columns if c.startswith("dom_resp_")]
    cols_rend = [c for c in filtered_df.columns if c.startswith("rend_media_")]
    
    # Cálculos de variáveis derivadas
    filtered_df["total_dom_resp"] = filtered_df[cols_dom].sum(axis=1)
    filtered_df["perc_chefe_mulher"] = (
        (filtered_df["dom_resp_m_branca"] + filtered_df["dom_resp_m_preta"] + 
         filtered_df["dom_resp_m_parda"] + filtered_df["dom_resp_m_amarela"] + 
         filtered_df["dom_resp_m_indigena"]) / 
        filtered_df["total_dom_resp"].replace(0, np.nan) * 100
    )
    filtered_df["perc_chefe_negro"] = (
        (filtered_df["dom_resp_h_preta"] + filtered_df["dom_resp_m_preta"] + 
         filtered_df["dom_resp_h_parda"] + filtered_df["dom_resp_m_parda"]) / 
        filtered_df["total_dom_resp"].replace(0, np.nan) * 100
    )

    # --- SEÇÃO 1: PERFIL E RENDIMENTOS ---
    st.markdown("### Perfil Sociodemográfico e Econômico")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Chefia Domiciliar (Censo 2022)")
        if not cols_dom:
            st.warning("Dados de perfil domiciliar não encontrados.")
        else:
            dom_data = filtered_df[cols_dom].sum().reset_index()
            dom_data.columns = ["perfil", "total"]
            dom_data["sexo"] = dom_data["perfil"].apply(lambda x: "Mulheres" if "_m_" in x else "Homens")
            dom_data["raca"] = dom_data["perfil"].apply(lambda x: x.split("_")[-1].capitalize())
            
            fig_dom = px.bar(
                dom_data, x="raca", y="total", color="sexo",
                barmode="group",
                labels={"raca": "Cor ou Raça", "total": "Nº de Domicílios", "sexo": "Sexo"},
                color_discrete_map={"Homens": "#5C6BC0", "Mulheres": "#AB47BC"}
            )
            fig_dom.update_layout(**PLOTLY_LAYOUT, height=400)
            st.plotly_chart(fig_dom, use_container_width=True)

    with c2:
        st.markdown("#### Rendimento Médio do Trabalho (PNAD 2022)")
        if not cols_rend:
            st.warning("Dados de rendimento não encontrados.")
        else:
            rend_data = filtered_df[["abbrev_state"] + cols_rend].drop_duplicates()
            rend_agg = rend_data[cols_rend].mean().reset_index()
            rend_agg.columns = ["perfil", "valor"]
            rend_agg["sexo"] = rend_agg["perfil"].apply(lambda x: "Mulheres" if "_m_" in x else "Homens")
            rend_agg["raca"] = rend_agg["perfil"].apply(lambda x: x.split("_")[-1].capitalize())
            
            fig_rend = px.bar(
                rend_agg, x="raca", y="valor", color="sexo",
                barmode="group",
                labels={"raca": "Cor ou Raça", "valor": "Rendimento Médio (R$)", "sexo": "Sexo"},
                color_discrete_map={"Homens": "#5C6BC0", "Mulheres": "#AB47BC"}
            )
            fig_rend.update_layout(**PLOTLY_LAYOUT, height=400)
            st.plotly_chart(fig_rend, use_container_width=True)

    st.markdown(
        f"""
**Análise Técnica:**
A observação dos dados aponta para disparidades estruturais significativas. Enquanto o Censo 2022 registra uma diversidade na composição da chefia domiciliar, os dados de rendimento (PNAD 2022) 
evidenciam uma profunda desigualdade na distribuição de recursos. Grupos historicamente marginalizados, notadamente mulheres pretas e pardas, apresentam os menores índices de rendimento 
nominal médio, o que constitui um determinante central na prevalência da vulnerabilidade alimentar nessas populações.
        """
    )
    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- SEÇÃO 2: DISTRIBUIÇÃO TERRITORIAL (MAPAS AGREGADOS POR UF) ---
    st.markdown("### Distribuição Territorial da Vulnerabilidade")
    st.markdown("Acompanhamento da concentração de perfis demográficos com maior exposição a riscos socioeconômicos (médias estaduais).")

    cm1, cm2 = st.columns(2)
    state_agg_vuln = filtered_df.groupby("abbrev_state").agg({
        "perc_chefe_mulher": "mean",
        "perc_chefe_negro": "mean",
        "total_dom_resp": "sum"
    }).reset_index()

    with cm1:
        st.markdown("#### % Domicílios com Chefia Feminina")
        fig_map_mulher = px.choropleth_mapbox(
            state_agg_vuln, geojson=BR_STATES_GEOJSON, locations="abbrev_state", featureidkey="properties.sigla",
            color="perc_chefe_mulher", color_continuous_scale="Purples",
            hover_name="abbrev_state", hover_data={"perc_chefe_mulher": ":.1f%", "total_dom_resp": ":,.0f", "abbrev_state": False},
            zoom=3, center={"lat": -15.78, "lon": -47.92}, mapbox_style="carto-positron",
            labels={"perc_chefe_mulher": "Chefia Feminina (%)"}
        )
        fig_map_mulher.update_layout(**PLOTLY_LAYOUT)
        fig_map_mulher.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=500)
        st.plotly_chart(fig_map_mulher, use_container_width=True)

    with cm2:
        st.markdown("#### % Domicílios com Chefia Negra ou Parda")
        fig_map_negro = px.choropleth_mapbox(
            state_agg_vuln, geojson=BR_STATES_GEOJSON, locations="abbrev_state", featureidkey="properties.sigla",
            color="perc_chefe_negro", color_continuous_scale="Oranges",
            hover_name="abbrev_state", hover_data={"perc_chefe_negro": ":.1f%", "total_dom_resp": ":,.0f", "abbrev_state": False},
            zoom=3, center={"lat": -15.78, "lon": -47.92}, mapbox_style="carto-positron",
            labels={"perc_chefe_negro": "Chefia Negra/Parda (%)"}
        )
        fig_map_negro.update_layout(**PLOTLY_LAYOUT)
        fig_map_negro.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=500)
        st.plotly_chart(fig_map_negro, use_container_width=True)

    st.markdown(
        """
**Nota Interpretativa sobre Territorialidade:**
A distribuição dos perfis de chefia domiciliar não se apresenta de forma homogênea no território nacional. Observa-se maior concentração de chefia por pessoas pretas e pardas em regiões 
em estados com indicadores históricos de desigualdade. A sobreposição dessa geografia com as áreas de maior insegurança alimentar sugere que o fenômeno da fome no Brasil 
possui componentes territoriais e demográficos indissociáveis.
        """
    )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)

    # --- SEÇÃO 3: CORRELAÇÕES ---
    st.markdown("### O Nexo entre Desigualdade e Insegurança Alimentar")
    
    c_corr1, c_corr2 = st.columns(2)
    with c_corr1:
        st.markdown("#### Chefia Feminina vs Insegurança Alimentar")
        df_corr = filtered_df.groupby("abbrev_state").agg({"perc_chefe_mulher": "mean", inseg_col: "first"}).reset_index()
        fig_corr = px.scatter(df_corr, x="perc_chefe_mulher", y=inseg_col, text="abbrev_state",
                              labels={"perc_chefe_mulher": "% Domicílios Chefe Mulher", inseg_col: f"Inseg. Alimentar (%)"},
                              color_discrete_sequence=[COR_PRIMARIA], trendline="ols")
        fig_corr.update_traces(textposition="top center", marker=dict(size=12))
        fig_corr.update_layout(**PLOTLY_LAYOUT, height=450)
        st.plotly_chart(fig_corr, use_container_width=True)

    with c_corr2:
        st.markdown("#### Chefia Negra/Parda vs Insegurança Grave (Fome)")
        df_corr_r = filtered_df.groupby("abbrev_state").agg({"perc_chefe_negro": "mean", inseg_grave_col: "first"}).reset_index()
        fig_corr_r = px.scatter(df_corr_r, x="perc_chefe_negro", y=inseg_grave_col, text="abbrev_state",
                                labels={"perc_chefe_negro": "% Domicílios Chefe Negro/Pardo", inseg_grave_col: f"Inseg. Grave (%)"},
                                color_discrete_sequence=[COR_GRAVE], trendline="ols")
        fig_corr_r.update_traces(textposition="top center", marker=dict(size=12))
        fig_corr_r.update_layout(**PLOTLY_LAYOUT, height=450)
        st.plotly_chart(fig_corr_r, use_container_width=True)

    st.markdown(
        f"""
**Análise de Correlação:**
A aplicação de modelos de regressão linear confirms a existência de uma correlação estatística positiva entre a incidência de domicílios chefiados por mulheres ou pessoas negras 
e os índices de insegurança alimentar. Este nexo evidencia que a insegurança alimentar grave (fome) atinge de forma desproporcional os estratos da população sujeitos a vulnerabilidades interseccionais.
        """
    )


# -------------------------------------------------------------------------
# 6. Mudanças Climáticas
# -------------------------------------------------------------------------
@st.cache_data
def load_adaptabrasil_table(file_path):
    abs_path = os.path.join(os.path.dirname(__file__), "adaptabrasil_csv", file_path)
    if os.path.exists(abs_path):
        return pd.read_csv(abs_path)
    return pd.DataFrame()

def pagina_clima():
    st.markdown("# Mudanças Climáticas e Insegurança Alimentar")
    st.markdown(
        '<p class="subtitle">Análise dos riscos climáticos e sua sobreposição com a vulnerabilidade social e alimentar no Brasil.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Esta seção integra dados do **AdaptaBrasil (MCTI/INPE)** para identificar municípios onde o risco climático — "
        "como escassez hídrica, estresse hídrico e desastres geo-hidrológicos — agrava a insegurança alimentar persistente."
    )

    filtered_df = get_filtered_data()
    ano = st.session_state.filtro_ano
    inseg_grave_col = f"inseg_grave_perc_dom_{ano}"

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)
    
    st.markdown("### Indicadores Climáticos (AdaptaBrasil)")
    st.markdown(
        "Selecione uma das dimensões abaixo para explorar o cruzamento de riscos geo-hidrológicos "
        "com a vulnerabilidade social e alimentar. Fonte: AdaptaBrasil MCTI."
    )
    
    if "chave_join" not in filtered_df.columns:
        filtered_df["chave_join"] = filtered_df["name_muni"] + "/" + filtered_df["abbrev_state"]

    agregacao_geo = st.radio(
        "Nível de Agregação Geográfica",
        ["Unidade da Federação", "Amazônia Legal vs Demais Estados", "Município"],
        horizontal=True
    )

    tabs = st.tabs([
        "Escassez Hídrica", 
        "Estresse Hídrico", 
        "Balanço Hídrico Agro", 
        "Inundações e Alagamentos", 
        "Capacidade Adaptativa"
    ])
    
    def render_mapa_aba(path_csv, col_name, label_name, colorscale, agregacao, nota_interpretativa, nota_ranking):
        df_csv = load_adaptabrasil_table(path_csv)
        if not df_csv.empty:
            df_sub = df_csv[["local_nome", "valor", "faixa"]].rename(columns={"valor": col_name, "faixa": "Faixa de Risco"})
            df_merged = filtered_df.merge(df_sub, left_on="chave_join", right_on="local_nome", how="inner")
            
            if not df_merged.empty:
                if agregacao == "Município":
                    st.markdown(f"**{label_name} vs Insegurança Alimentar Grave (%) — Municípios**")
                    fig_map = px.scatter_mapbox(
                        df_merged.dropna(subset=[col_name]), lat="lat", lon="lon", 
                        color=col_name, size=inseg_grave_col,
                        color_continuous_scale=colorscale, size_max=15, zoom=3, mapbox_style="carto-positron",
                        hover_name="name_muni", hover_data={"abbrev_state": True, inseg_grave_col: ":.1f%", "Faixa de Risco": True}
                    )
                else:
                    if agregacao == "Unidade da Federação":
                        st.markdown(f"**Média de {label_name} vs Insegurança Alimentar Grave (%) — Estados**")
                        df_agg = df_merged.groupby("abbrev_state").agg({
                            col_name: "mean",
                            inseg_grave_col: "mean"
                        }).reset_index()
                        color_col = col_name
                        hover_name_col = "abbrev_state"
                    else:
                        st.markdown(f"**Média de {label_name} vs Insegurança Alimentar Grave (%) — Macrorregiões**")
                        df_merged["Regiao"] = df_merged["abbrev_state"].apply(lambda x: "Amazônia Legal" if x in AMAZONIA_LEGAL else "Demais Estados")
                        df_reg = df_merged.groupby("Regiao").agg({
                            col_name: "mean",
                            inseg_grave_col: "mean"
                        }).reset_index()
                        
                        df_agg = df_merged.groupby(["abbrev_state", "Regiao"]).first().reset_index()
                        df_agg[col_name] = df_agg.apply(lambda row: df_reg.loc[df_reg['Regiao'] == row['Regiao'], col_name].values[0], axis=1)
                        df_agg[inseg_grave_col] = df_agg.apply(lambda row: df_reg.loc[df_reg['Regiao'] == row['Regiao'], inseg_grave_col].values[0], axis=1)
                        
                        color_col = col_name
                        hover_name_col = "Regiao"

                    fig_map = px.choropleth_mapbox(
                        df_agg.dropna(subset=[color_col]),
                        geojson=BR_STATES_GEOJSON,
                        locations="abbrev_state",
                        featureidkey="properties.sigla",
                        color=color_col,
                        color_continuous_scale=colorscale,
                        hover_name=hover_name_col,
                        hover_data={color_col: ":.2f", inseg_grave_col: ":.1f%", "abbrev_state": False},
                        zoom=3, center={"lat": -15.78, "lon": -47.92},
                        mapbox_style="carto-positron"
                    )

                fig_map.update_layout(**PLOTLY_LAYOUT)
                fig_map.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=500)
                st.plotly_chart(fig_map, use_container_width=True)

                st.markdown(
                    f'''
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; font-size: 0.9em; margin-top: 10px; margin-bottom: 20px;">
                        <strong>Nota Interpretativa:</strong> {nota_interpretativa}
                    </div>
                    ''', 
                    unsafe_allow_html=True
                )

                # --- NOVOS GRÁFICOS ANALÍTICOS SIMPLIFICADOS (EMPILHADOS) ---
                st.markdown("---")
                st.markdown(f"### Análise de Vulnerabilidade: {label_name}")
                
                # Gráfico 1: Distribuição
                st.markdown("#### Distribuição do Nível de Risco")
                faixa_counts = df_merged["Faixa de Risco"].value_counts().reset_index()
                faixa_counts.columns = ["Risco", "Municípios"]
                
                fig_donut = px.pie(
                    faixa_counts, values="Municípios", names="Risco",
                    hole=0.5,
                    color="Risco",
                    color_discrete_map={
                        "Baixo": "#A5D6A7", "Médio": "#FFF59D", 
                        "Alto": "#FFCC80", "Muito Alto": "#EF9A9A",
                        "Crítico": "#B71C1C"
                    },
                    category_orders={"Risco": ["Baixo", "Médio", "Alto", "Muito Alto", "Crítico"]}
                )
                fig_donut.update_layout(**PLOTLY_LAYOUT)
                fig_donut.update_layout(height=400, margin=dict(t=30, b=30, l=0, r=0))
                st.plotly_chart(fig_donut, use_container_width=True)
                
                st.markdown(
                    f"""
                    <div class="interpretative-note">
                        <strong>Nota interpretativa:</strong> Ele mostra a proporção de municípios brasileiros classificados em cada nível de risco para <strong>{label_name.lower()}</strong>. 
                        Quanto maior a fatia de cores quentes (laranja e vermelho), maior é a urgência de intervenção nessas localidades para evitar crises de abastecimento.
                    </div>
                    """, unsafe_allow_html=True
                )
                
                st.markdown("<br>", unsafe_allow_html=True)

                # Gráfico 2: Comparação Regional
                st.markdown("#### Comparação Regional (Média de Risco)")
                reg_risk = df_merged.groupby("name_region")[col_name].mean().sort_values().reset_index()
                media_nacional = df_merged[col_name].mean()
                
                fig_reg_bar = px.bar(
                    reg_risk, x=col_name, y="name_region",
                    orientation="h",
                    labels={col_name: "Índice Médio", "name_region": ""},
                    color_discrete_sequence=[COR_PRIMARIA]
                )
                fig_reg_bar.add_vline(x=media_nacional, line_dash="dash", line_color="red", 
                                     annotation_text="Média Nacional", annotation_position="top right")
                
                fig_reg_bar.update_layout(**PLOTLY_LAYOUT)
                fig_reg_bar.update_layout(height=400, margin=dict(t=30, b=30, l=0, r=0))
                st.plotly_chart(fig_reg_bar, use_container_width=True)
                
                st.markdown(
                    f"""
                    <div class="interpretative-note">
                        <strong>Nota interpretativa:</strong> Comparamos o risco médio de cada região com a média de todo o Brasil (linha vermelha). 
                        Regiões cujas barras ultrapassam a linha tracejada são as que sofrem maior pressão climática de <strong>{label_name.lower()}</strong> neste momento.
                    </div>
                    """, unsafe_allow_html=True
                )

                st.markdown("---")

                st.markdown(f"#### Ranking Analítico: {label_name}")
                if agregacao == "Município":
                    df_top = df_merged.sort_values(by=col_name, ascending=False).head(15)
                    df_top = df_top.iloc[::-1]
                    fig_chart = px.bar(
                        df_top, x=col_name, y="name_muni", orientation='h',
                        color=inseg_grave_col, color_continuous_scale="Reds",
                        labels={col_name: "Índice de Risco Climático", "name_muni": "", inseg_grave_col: "Fome (%)"},
                        text_auto='.2f',
                        title="Top 15 Municípios de Maior Risco Climático"
                    )
                    fig_chart.update_layout(**PLOTLY_LAYOUT, height=600)
                    st.plotly_chart(fig_chart, use_container_width=True)

                elif agregacao == "Unidade da Federação":
                    df_top = df_agg.sort_values(by=col_name, ascending=False)
                    df_top = df_top.iloc[::-1]
                    fig_chart = px.bar(
                        df_top, x=col_name, y="abbrev_state", orientation='h',
                        color=inseg_grave_col, color_continuous_scale="Reds",
                        labels={col_name: "Média de Risco", "abbrev_state": "", inseg_grave_col: "Fome Média (%)"},
                        text_auto='.2f',
                        title="Ranking Estadual de Risco Climático"
                    )
                    fig_chart.update_layout(**PLOTLY_LAYOUT, height=700)
                    st.plotly_chart(fig_chart, use_container_width=True)

                else:
                    d_chart = pd.DataFrame({
                        "Macrorregião": df_reg["Regiao"].tolist() + df_reg["Regiao"].tolist(),
                        "Valor": df_reg[inseg_grave_col].tolist() + (df_reg[col_name] * 100).tolist(),
                        "Indicador": ["Fome (%)"] * len(df_reg) + ["Risco Climático (*100)"] * len(df_reg)
                    })
                    fig_chart = px.bar(
                        d_chart, x="Macrorregião", y="Valor", color="Indicador", barmode="group",
                        color_discrete_map={"Fome (%)": COR_GRAVE, "Risco Climático (*100)": COR_PRIMARIA},
                        text_auto='.1f'
                    )
                    fig_chart.update_layout(**PLOTLY_LAYOUT, height=450,
                                            legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_chart, use_container_width=True)

                st.markdown(
                    f'''
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; font-size: 0.9em; margin-top: 10px; margin-bottom: 20px;">
                        <strong>Nota interpretativa:</strong> {nota_ranking}
                    </div>
                    ''', 
                    unsafe_allow_html=True
                )
            else:
                st.info("Não foi possível cruzar os dados para este indicador no ano selecionado.")
        else:
            st.error(f"Base de dados não encontrada: {path_csv}")

    with tabs[0]:
        render_mapa_aba(
            "recursos-hidricos/00005_ameaca-de-escassez-hidrica_2020_presente.csv", 
            "indice_escassez", "Ameaça de Escassez Hídrica", "Oranges", agregacao_geo,
            "O mapa destaca o 'Nexus Água-Alimento': municípios com alta vulnerabilidade alimentar que também enfrentam riscos elevados de escassez ou estresse hídrico. A convergência dessas crises sugere que a segurança alimentar nestes territórios é extremamente dependente da variabilidade climática, exigindo políticas de adaptação urgente.",
            "A priorização orçamentária (emendas, repasses ou PAC) deve focar imediatamente no topo deste ranking, onde o colapso estrutural da água converte-se velozmente em fome local e bloqueia qualquer iniciativa de segurança alimentar de longo prazo."
        )
        
    with tabs[1]:
        render_mapa_aba(
            "recursos-hidricos/00002_risco-de-estresse-hidrico_2020_presente.csv", 
            "indice_estresse", "Risco de Estresse Hídrico", "Reds", agregacao_geo,
            "Diferente da escassez prolongada, o Estresse Hídrico mede a densidade da competição imediata por água superficial e subterrânea. Territórios afetados sinalizam locais onde a rápida expansão urbana ou o consumo massivo por certas indústrias agravam diretamente a disponibilidade hídrica para a agricultura de pequena escala, um vetor crítico da soberania alimentar.",
            "O mapeamento destaca os territórios que demandam revisão urgente nos marcos de regulação do uso conjunto de bacias hidrológicas. O avanço imediato de políticas de proteção é mandatório para resguardar o acesso à água pelas matrizes de agricultura familiar perante o avanço da demanda urbana e agroindustrial."
        )
        
    with tabs[2]:
        render_mapa_aba(
            "recursos-hidricos/00022_balanco-hidrico-para-agropecuaria_2020_presente.csv", 
            "indice_balanco_agro", "Balanço Hídrico", "YlOrBr", agregacao_geo,
            "O Balanço Hídrico correlaciona diretamente a sobra ou o déficit de água no solo especificamente para as práticas de plantio. Zonas vermelhas severas indicam a propensão de falência antecipada das safras de sustento, empurrando a demografia rural para subíndices alarmantes de deficiência alimentar durante quebras contínuas de colheita.",
            "A antecipação governamental é estritamente necessária nas instâncias listadas. É recomendável a liberação orçamentária prévia voltada à execução de fundos de contingência ('seguro defeso' agrícola) antes que o indicador agrometeorológico consolide a falha sistêmica das safras de subsistência anuais."
        )
        
    with tabs[3]:
        render_mapa_aba(
            "desastres-geo-hidrologicos/60041_inundacoes-enxurradas-e-alagamentos_2015_presente.csv", 
            "indice_inundacao", "Risco de Inundações", "Blues", agregacao_geo,
            "O Risco Geo-hidrológico rastreia a vulnerabilidade infraestrutural perante anomalias agudas (chuvas e descargas extremas). Em áreas com altos índices históricos de fome, um alagamento destrói vertiginosamente o banco genético de sementes e rompe corredores logísticos, configurando um risco mortal não só de perdas agrárias, mas de bloqueio absoluto a suprimentos.",
            "Estes territórios concentram grau acentuado de propensão ao estrangulamento logístico precoce. O aporte unificado de crédito e de intervenções corretivas na infraestrutura civil, essencialmente na viabilização e manutenção de vias de escoamento rápido, é indispensável para evitar o colapso alimentar da malha."
        )
        
    with tabs[4]:
        render_mapa_aba(
            "recursos-hidricos/00007_capacidade-adaptativa_2020_presente.csv", 
            "indice_cap_adaptativa", "Capacidade Adaptativa", "Greens", agregacao_geo,
            "Este indicador elenca os 'colchões' socioeconômicos e de infraestrutura tangível (engenharia rural e rede de suporte) para absorver choques climáticos. Municípios com Capacidade Adaptativa muito baixa em contraste a alta Insegurança Alimentar representam as zonas zero do país: domínios sem amortecedores de longo prazo contra eventos climáticos severos.",
            "As jurisdições listadas denunciam grande ausência elementar de uma arquitetura sociogovernamental resiliente. Seu isolamento logístico e técnico carece fundamentalmente de articulação macrorregional executiva que incorpore linhas de saneamento contínuo, fomento e extensão rural para consolidação humana a longo prazo."
        )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)


# -------------------------------------------------------------------------
# 7. Metodologia
# -------------------------------------------------------------------------
def pagina_metodologia():
    st.markdown("# Metodologia Técnica")
    st.markdown(
        """
<div class="technical-note">
Este dashboard foi desenvolvido pelo <b>Aruanã Instituto Pan-Amazônico</b> como uma ferramenta de transparência 
e análise territorial. A metodologia baseia-se na integração de múltiplas bases de dados oficiais, 
processadas para permitir a comparabilidade entre diferentes dimensões da vulnerabilidade social e alimentar.

### 1. Fontes de Dados
- **Insegurança Alimentar:** Estimativas baseadas na PNAD Contínua (IBGE, 2023-2024), utilizando a Escala Brasileira de Insegurança Alimentar (EBIA).
- **Dados Sociodemográficos:** Censo Demográfico 2022 (IBGE), incluindo a Tabela 9880 para indicadores de Gênero e Raça.
- **Produção Agrícola:** Produção Agrícola Municipal (PAM/IBGE, 2023-2024), classificada segundo a Portaria MDS nº 966/2024.
- **Políticas Públicas:** Microdados e transferências do Programa Bolsa Família (Ministério do Desenvolvimento e Assistência Social, Família e Combate à Fome).
- **Riscos Climáticos:** Indicadores de ameaça e vulnerabilidade do portal AdaptaBrasil (MCTI/INPE).

### 2. Processamento e Glossário
- **ICV (Índice de Vulnerabilidade Composta):** Média aritmética da proporção de domicílios com chefia feminina e chefia negra/parda por estado.
- **IVFG (Índice de Vulnerabilidade à Fome por Gênero):** Produto entre a porcentagem de chefia feminina e o índice de insegurança alimentar grave, normalizado para identificar zonas de sobreposição crítica.
- **Alimento vs Commodity:** Classificação binária baseada na aptidão para compor a Cesta Básica de Alimentos, distinguindo produção para consumo humano direto de culturas de uso industrial ou exportação.

### 3. Limitações e Sigilo
- Os dados de insegurança alimentar são representativos em nível estadual; as aplicações municipais seguem o perfil da Unidade da Federação correspondente.
- Toda a estrutura de dados respeita o sigilo estatístico, utilizando agregados que impedem a identificação individual.
</div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------------------------------
# 8. Download de Dados
# -------------------------------------------------------------------------
def pagina_download():
    st.markdown("# Download de Dados")
    st.markdown(
        '<p class="subtitle">Acesse e exporte as bases de dados oficiais e consolidadas que alimentam este observatório.</p>',
        unsafe_allow_html=True,
    )

    # 1. Base Consolidada
    st.markdown("### 1. Base Municipal Consolidada (2023-2024)")
    st.markdown(
        """
        Esta é a tabela principal do projeto. Ela reúne informações de mais de 5.500 municípios brasileiros, 
        integrando dados do Censo 2022, estimativas de Insegurança Alimentar da PNAD Contínua (2023 e 2024), 
        além de métricas de cobertura do Bolsa Família e perfil de Gênero e Raça da chefia domiciliar.
        """
    )
    csv_consolidado = DATA.to_csv(sep=";", decimal=",", index=False, encoding="utf-8")
    st.download_button(
        label="Baixar Base Consolidada (CSV)",
        data=csv_consolidado,
        file_name="aruana_base_municipal_consolidada.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # 2. Produção Agrícola
    st.markdown("### 2. Produção Agrícola Detalhada por Produto")
    st.markdown(
        """
        Contém o detalhamento da Produção Agrícola Municipal (PAM) do IBGE. Os dados permitem analisar a área plantada, 
        o volume produzido e o valor da produção para cada cultura específica, além de incluir a classificação 
        institucional entre Alimentos e Commodities de exportação.
        """
    )
    if DATA_PROD is not None:
        csv_prod = DATA_PROD.to_csv(sep=";", decimal=",", index=False, encoding="utf-8")
        st.download_button(
            label="Baixar Produção por Produto (CSV)",
            data=csv_prod,
            file_name="aruana_producao_agricola_detalhada.csv",
            mime="text/csv",
        )
    else:
        st.info("A base de produção detalhada não está disponível no momento.")

    st.markdown("---")

    # 3. Riscos Climáticos (Simplificado/Exemplo)
    st.markdown("### 3. Indicadores de Risco Climático (AdaptaBrasil)")
    st.markdown(
        """
        Esta tabela consolida os principais indicadores de risco e vulnerabilidade climática do portal AdaptaBrasil (MCTI/INPE), 
        focados em recursos hídricos e desastres geo-hidrológicos. Os índices variam de 0 a 1 e indicam o nível de ameaça 
        para cada município brasileiro no cenário presente.
        """
    )
    
    # Vamos oferecer o download dos 5 indicadores principais que usamos na aba de clima
    indicadores_clima = [
        ("recursos-hidricos/00005_ameaca-de-escassez-hidrica_2020_presente.csv", "Escassez Hídrica"),
        ("recursos-hidricos/00002_risco-de-estresse-hidrico_2020_presente.csv", "Estresse Hídrico"),
        ("recursos-hidricos/00022_balanco-hidrico-para-agropecuaria_2020_presente.csv", "Balanço Hídrico Agro"),
        ("desastres-geo-hidrologicos/60041_inundacoes-enxurradas-e-alagamentos_2015_presente.csv", "Inundações"),
        ("recursos-hidricos/00007_capacidade-adaptativa_2020_presente.csv", "Capacidade Adaptativa")
    ]
    
    for path, label in indicadores_clima:
        df_clima_dl = load_adaptabrasil_table(path)
        if not df_clima_dl.empty:
            csv_clima = df_clima_dl.to_csv(sep=";", decimal=",", index=False, encoding="utf-8")
            st.download_button(
                label=f"Baixar Dados: {label} (CSV)",
                data=csv_clima,
                file_name=f"aruana_clima_{label.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                key=f"dl_{label}"
            )

    st.markdown('<hr class="hr-institutional">', unsafe_allow_html=True)



# -------------------------------------------------------------------------
# Router e Inicialização
# -------------------------------------------------------------------------
PAGES = {
    "Apresentação": pagina_apresentacao,
    "Panorama Nacional": pagina_panorama,
    "Gênero e Raça": pagina_genero_raca,
    "Produção Agrícola": pagina_producao,
    "Bolsa Família": pagina_bolsa_familia,
    "Mudanças Climáticas": pagina_clima,
    "Metodologia": pagina_metodologia,
    "Download de Dados": pagina_download,
}

if pagina in PAGES:
    PAGES[pagina]()
else:
    st.error("Página não encontrada.")

# Espaçamento final
st.markdown("<br><br>", unsafe_allow_html=True)
