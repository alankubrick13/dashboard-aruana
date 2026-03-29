# Documentação do Projeto: Observatório de Segurança Alimentar (Instituto Aruanã)

## 1. Visão Geral
O **Observatório de Segurança Alimentar** é uma plataforma analítica de alta performance desenvolvida em **Streamlit (Python)**. O projeto monitora a intersecção entre produção agrícola, vulnerabilidade socioeconômica (Gênero e Raça) e a prevalência de quadros de fome no Brasil em nível municipal e estadual.

## 2. Arquitetura do Software e Design
O dashboard adota uma estética **premium e institucional**, inspirada no padrão *Reuters Graphics*, focando em sobriedade técnica e clareza de dados.

### Componentes Principais:
- **Frontend/UI:** Desenvolvido em Streamlit com customização profunda via `style.css`.
- **Motor Gráfico:** Utiliza `Plotly Express` para visualizações dinâmicas e `Mapbox` para mapas municipais de alta resolução.
- **Estruturação:** Organizado em módulos de páginas vinculados a um roteador central no `app.py`.

## 3. Pipeline de Dados (ETL)
A base de dados é gerada por um pipeline híbrido que integra dados oficiais do **IBGE (SIDRA)** e **Ministério do Desenvolvimento Social (MDS)**.

### Fontes Integradas:
- **Demografia (Censo 2022):** Tabelas de população e estrutura de chefia domiciliar (Tabelas 9923, 9880).
- **Insegurança Alimentar (PNAD Contínua):** Estimativas estaduais de segurança alimentar (2023-2024).
- **Rendimento (PNAD Contínua):** Dados de renda média segmentados por perfil interseccional (Tabela 10281).
- **Agricultura (PAM):** Área plantada municipal (Tabela 5457).
- **Assistência Social (MDS):** Repasses e cobertura do Bolsa Família.

### Scripts de Processamento (R):
Localizados em `ACTUALIZACAO_TEMPORAL/`, os scripts em R realizam a extração via API e a consolidação final no arquivo `dados_consolidados_v5.csv`.

## 4. Camada Analítica e Indicadores Originais
O diferencial do projeto reside na criação de indicadores sintéticos que evidenciam a "Geografia da Fome":
- **ICV (Índice de Vulnerabilidade Composta):** Sobreposição de vulnerabilidades de gênero e raça.
- **IVFG (Índice de Vulnerabilidade à Fome por Gênero):** Clusterização municipal da intersecção entre chefia feminina e fome grave.
- **Análise de Correlação (OLS):** Modelos estatísticos que validam o nexo causal entre desigualdade econômica e insegurança alimentar.

## 5. Como Executar
1. Instale as dependências:
   ```bash
   pip install -r streamlit_dashboard/requirements.txt
   ```
2. Execute o servidor:
   ```bash
   cd streamlit_dashboard
   streamlit run app.py
   ```

---
*Documentação atualizada em Março de 2026 para refletir a conclusão da Camada Interseccional.*
