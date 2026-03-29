# Analisador de Segurança Alimentar e Mudanças Climáticas — Municípios Brasileiros

Dataset consolidado de municípios brasileiros integrando segurança alimentar, produção agrícola, dados socioeconômicos e riscos climáticos.

**Arquivo final:** `dados_consolidados_v5.csv`  
**Dimensões:** 5.570 municípios × ~150 colunas  
**Última atualização:** 17/03/2026  
**Scripts:** `extract_data_9552.R` · `add_bolsa_familia.R` · `app.py` (Processamento Clima/Gênero/Raça)

---

## Visão Geral

O dataset consolida, ao nível municipal, informações de **seis fontes de dados oficiais** para os anos de referência de 2022 a 2024:

| # | Fonte | Tabela/Arquivo | Cobertura |
|---|-------|----------------|-----------|
| 1 | IBGE — Censo Demográfico 2022 | SIDRA 9923 | Todos os municípios |
| 2 | IBGE — PNAD Contínua (Seg. Alimentar) | SIDRA 9552 | Por UF (27 unidades) |
| 3 | IBGE — Produção Agrícola Municipal | SIDRA 5457 / PAM | Todos os municípios |
| 4 | MDS — Bolsa Família | Excel (2023 e 2024) | Todos os municípios |
| 5 | IBGE — Censo / PNAD (Gênero/Raça) | SIDRA 9880 | Todos os municípios |
| 6 | AdaptaBrasil MCTI / INPE | Indicadores de Risco | Todos os municípios |

As geometrias e metadados municipais foram obtidos via pacote R `geobr` (IBGE 2022).

---

## Fontes e Variáveis

### 1 · População — Censo Demográfico 2022 (SIDRA 9923)

- **Variável SIDRA:** `93` (População residente)
- **Classificação:** `c1` — Situação do domicílio
  - `6795` = Total
  - `1` = Urbana
  - `2` = Rural
- **Granularidade:** Municipal
- **Colunas geradas:**

| Coluna | Descrição |
|--------|-----------|
| `populacao` | População total residente |
| `pop_urbana` | População residente em área urbana |
| `pop_rural` | População residente em área rural |
| `perc_urbana` | % da população em área urbana |
| `perc_rural` | % da população em área rural |

---

### 2 · Segurança Alimentar — PNAD Contínua (SIDRA 9552 / C12404)

- **Granularidade:** Estadual (27 UFs) — replicada para todos os municípios da UF via `left_join`
- **Anos:** 2023 e 2024
- **Classificação C12404 — Situação de Segurança Alimentar:**

| Código | Categoria | Nome no dataset |
|--------|-----------|-----------------|
| 109106 | Total | `total` |
| 109098 | Com segurança alimentar | `seg` |
| 109099 | Com insegurança alimentar | `inseg` |
| 109100 | Com insegurança alimentar leve | `inseg_leve` |
| 109101 | Com insegurança alimentar moderada | `inseg_moderada` |
| 109102 | Com insegurança alimentar grave | `inseg_grave` |

- **Variáveis extraídas (8 por categoria):**

| Código | Variável | Nome no dataset |
|--------|----------|-----------------|
| 162 | Domicílios (Mil unidades) | `dom_mil` |
| 5123 | CV — Domicílios (%) | `cv_dom` |
| 9784 | Distribuição % dos domicílios | `perc_dom` |
| 9785 | CV — Distribuição % dos domicílios | `cv_perc_dom` |
| 10114 | Moradores em domicílios (Mil pessoas) | `mor_mil` |
| 10116 | CV — Moradores em domicílios (%) | `cv_mor` |
| 10117 | Distribuição % dos moradores | `perc_mor` |
| 10118 | CV — Distribuição % dos moradores (%) | `cv_perc_mor` |

- **Convenção de nomenclatura das colunas:** `<categoria>_<variável>_<ano>`  
  Exemplo: `inseg_grave_perc_dom_2024`

- **Total de colunas de segurança alimentar:** **96** (6 categorias × 8 variáveis × 2 anos)

> **Nota:** CV = Coeficiente de Variação; indica a precisão estatística da estimativa.

---

### 3 · Área Plantada — Produção Agrícola Municipal (SIDRA 5457)

- **Variável SIDRA:** `8331` (Área plantada ou destinada à colheita — ha)
- **Classificação:** `c782 = 0` (Total de culturas)
- **Ano de referência:** 2024
- **Granularidade:** Municipal

| Coluna | Descrição |
|--------|-----------|
| `area_plantada_ha` | Área plantada total em hectares (2024) |

---

### 4 · Bolsa Família (MDS, 2023 e 2024)

- **Fontes:** `Bolsa familia 2023.xlsx` e `Bolsa familia 2024.xlsx`
- **Granularidade original:** Mensal por município
- **Chave de join:** `codigo_ibge` (6 dígitos) nos Excel ↔ primeiros 6 dígitos do `code_muni` (7 dígitos com dígito verificador)

#### Tratamento temporal — Média anual

Os dados originais têm uma linha por mês por município. Para compatibilizar com o dataset anual, calculou-se a **média mensal** e a **soma anual** de cada variável:

| Coluna | Cálculo | Descrição |
|--------|---------|-----------|
| `bf_n_meses_<ano>` | `n()` | Número de meses disponíveis |
| `bf_qtd_familias_media_<ano>` | `mean()` | Média mensal de famílias beneficiárias |
| `bf_valor_repassado_media_<ano>` | `mean()` | Média mensal do valor repassado (R$) |
| `bf_vlr_medio_benef_media_<ano>` | `mean()` | Média mensal do valor médio por benefício (R$) |
| `bf_qtd_familias_total_<ano>` | `sum()` | Total de famílias acumulado no ano |
| `bf_valor_repassado_total_<ano>` | `sum()` | Total do valor repassado no ano (R$) |

> **Atenção — 2023 tem apenas 10 meses** (março a dezembro; os meses de janeiro e fevereiro não estavam disponíveis no ficheiro fornecido). A coluna `bf_n_meses_2023 = 10` documenta isso. As médias são calculadas sobre os meses disponíveis.  
> **2024 tem 12 meses** completos (`bf_n_meses_2024 = 12`).

---

### 5 · Gênero e Raça — Censo / SIDRA 9880

- **Fonte:** IBGE SIDRA, Tabela 9880 (População residente por cor ou raça e sexo).
- **Indicadores:** Focados em chefia domiciliar e vulnerabilidade de rendimentos.
- **Colunas principais:**
  - `dom_resp_fem_preta_parda`: Domicílios com responsabilidade feminina (preta/parda).
  - `rend_media_...`: Rendimento médio mensal domiciliar por grupo étnico-racial.

---

### 6 · Produção: Alimento vs Commodity (Portaria MDS 966)

- **Lógica de classificação:** Baseada na Portaria MDS nº 966/2023, separando culturas destinadas ao consumo humano local (alimento) de culturas voltadas para exportação/indústria (commodity).
- **Colunas geradas:**
  - `area_ha_alimento`: Soma das áreas de culturas classificadas como alimento.
  - `area_ha_commodity`: Soma das áreas de culturas classificadas como commodity.
  - `perc_alimento`: Proporção da área total destinada a alimentos.

---

### 7 · Mudanças Climáticas (AdaptaBrasil MCTI)

- **Fonte:** Plataforma AdaptaBrasil MCTI / INPE.
- **Indicadores integrados (2015/2020):**
  - Escassez Hídrica
  - Estresse Hídrico
  - Balanço Hídrico Agropecuário
  - Inundações, Enxurradas e Alagamentos
  - Capacidade Adaptativa
- **Tratamento:** Join via `bridge_key` (nome_muni/UF) garantindo 100% de cobertura.

---

## Estrutura do Dataset Final

### Colunas de Identificação e Metadados (6)

| Coluna | Descrição |
|--------|-----------|
| `code_muni` | Código IBGE municipal (7 dígitos) |
| `name_muni` | Nome do município |
| `abbrev_state` | Sigla da UF |
| `name_region` | Nome da região geográfica |
| `lat` | Latitude do centróide municipal |
| `lon` | Longitude do centróide municipal |

### Colunas de População (5)
`populacao`, `pop_urbana`, `pop_rural`, `perc_urbana`, `perc_rural`

### Área Agrícola e Classificação (4)
`area_plantada_ha`, `area_ha_alimento`, `area_ha_commodity`, `perc_alimento`

### Gênero e Raça (Variável)
Colunas iniciadas com `dom_resp_`, `rend_media_` e `rend_mediana_`.

### Riscos Climáticos (Variável)
Integrados sob demanda na página de visualização via arquivos CSV específicos localizados na pasta `adaptabrasil_csv`.

### Segurança Alimentar (96)
Formato: `<categoria>_<variável>_<ano>` — ver tabelas acima.

### Bolsa Família (12)
6 colunas por ano (`_2023` e `_2024`) — ver tabela acima.

---

## Fluxo de Processamento

```
SIDRA 9923           SIDRA 9552          SIDRA 5457 (PAM)    SIDRA 9880
(Censo 2022)     (PNAD Cont. 23/24)   (Classif. MDS 966)    (Gênero/Raça)
     │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼
  pop_wide          fome_wide          pam_classif        gen_raca_wide
  (municipal)        (estadual)         (municipal)         (municipal)
     │                  │                  │                  │
     └──────────┬───────┴──────────┬───────┘                  │
                ▼                 ▼                           │
           muni_meta ◄───────── geobr                         │
           (metadados)                                        │
                │                                             │
                ▼                                             │
           left_join ────────────────────────────────────────►│
           (code_muni)                                        │
                │◄─────────────────────────────────────────────
                ▼
        dados_consolidados_v5.csv
        (5570 × ~150)   ← FICHEIRO FINAL ATUALIZADO
```

---

## Scripts

| Script | Função |
|--------|--------|
| [extract_data_9552.R](streamlit_dashboard/ACTUALIZACAO_TEMPORAL/extract_data_9552.R) | Extrai e consolida dados de população, segurança alimentar e agricultura via API SIDRA |
| [add_bolsa_familia.R](streamlit_dashboard/ACTUALIZACAO_TEMPORAL/add_bolsa_familia.R) | Lê os Excel do Bolsa Família, calcula médias anuais e faz join com o dataset consolidado |
| `app.py` | Dashboard Streamlit que integra os riscos climáticos e indicadores de gênero/raça para visualização |

### Pacotes R utilizados

| Pacote | Função |
|--------|--------|
| `sidrar` | Acesso à API SIDRA/IBGE |
| `dplyr` | Manipulação de dados |
| `tidyr` | Pivot e reestruturação |
| `geobr` | Metadados e geometrias municipais |
| `janitor` | Normalização de nomes de colunas (`clean_names`) |
| `readxl` | Leitura de ficheiros Excel |

---

## Considerações Metodológicas

1. **Segurança alimentar ao nível estadual:** Os dados da PNAD Contínua (SIDRA 9552) têm representatividade estadual, não municipal. Todos os municípios de uma UF recebem o mesmo valor estadual. Isso deve ser considerado ao interpretar variações entre municípios dentro do mesmo estado.

2. **Média anual do Bolsa Família:** A média mensal é preferível às totais anuais para comparações entre 2023 (10 meses) e 2024 (12 meses), pois elimina o viés do número de meses disponíveis. Use `bf_qtd_familias_media_<ano>` para comparações interanuais.

3. **Dígito verificador IBGE:** O código municipal no dataset (`code_muni`) tem 7 dígitos enquanto o código nos ficheiros do Bolsa Família (`codigo_ibge`) tem 6. O join é feito truncando os primeiros 6 dígitos: `substr(code_muni, 1, 6)`.

4. **Área agrícola:** Representa o total de todas as culturas temporárias e permanentes. A classificação de **Alimento vs Commodity** segue os critérios da Portaria MDS 966 para análise do nexo segurança alimentar.
