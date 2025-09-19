import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Dashboard KPIs - Gestão de Frotas",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🚛 Dashboard de KPIs - Gestão de Frotas")
st.markdown("---")

# Carregar dados
@st.cache_data
def load_data():
    df = pd.read_csv('kpis_frota_ficticios.csv')
    df['Data'] = pd.to_datetime(df['Data'])
    return df

df = load_data()

# Sidebar com filtros
st.sidebar.header("🔧 Filtros")

# Filtro por período
min_date = df['Data'].min()
max_date = df['Data'].max()
date_range = st.sidebar.date_input(
    "Período:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtro por modelo
modelos_disponiveis = ['Todos'] + list(df['Modelo'].unique())
modelo_selecionado = st.sidebar.selectbox("Modelo:", modelos_disponiveis)

# Filtro por veículo
veiculos_disponiveis = ['Todos'] + list(df['ID_Veiculo'].unique())
veiculo_selecionado = st.sidebar.selectbox("Veículo:", veiculos_disponiveis)

# Aplicar filtros
df_filtrado = df.copy()

# Filtro de data
if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtrado = df_filtrado[
        (df_filtrado['Data'] >= pd.to_datetime(start_date)) & 
        (df_filtrado['Data'] <= pd.to_datetime(end_date))
    ]

# Filtro de modelo
if modelo_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Modelo'] == modelo_selecionado]

# Filtro de veículo
if veiculo_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['ID_Veiculo'] == veiculo_selecionado]

# Calcular KPIs principais
df_operacional = df_filtrado[df_filtrado['KM_Rodado'] > 0]

# Métricas principais
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    km_total = df_operacional['KM_Rodado'].sum()
    st.metric("KM Total", f"{km_total:,.0f}")

with col2:
    consumo_medio = df_operacional['Media_Consumo_KML'].mean()
    st.metric("Consumo Médio", f"{consumo_medio:.2f} KM/L")

with col3:
    custo_total = (df_filtrado['Custo_Combustivel'] + 
                   df_filtrado['Custo_Manutencao'] + 
                   df_filtrado['Custo_Multas']).sum()
    st.metric("Custo Total", f"R$ {custo_total:,.2f}")

with col4:
    cpk = custo_total / km_total if km_total > 0 else 0
    st.metric("Custo por KM", f"R$ {cpk:.2f}")

with col5:
    acidentes_total = df_filtrado['Acidentes'].sum()
    st.metric("Total de Acidentes", f"{acidentes_total}")

st.markdown("---")

# Tabs para diferentes categorias de KPIs
tab1, tab2, tab3, tab4 = st.tabs(["💰 Custos", "⚙️ Operações", "🔧 Manutenção", "🛡️ Segurança"])

with tab1:
    st.subheader("📊 Análise de Custos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de custos por categoria
        custos_categoria = pd.DataFrame({
            'Categoria': ['Combustível', 'Manutenção', 'Multas'],
            'Valor': [
                df_filtrado['Custo_Combustivel'].sum(),
                df_filtrado['Custo_Manutencao'].sum(),
                df_filtrado['Custo_Multas'].sum()
            ]
        })
        
        fig_custos = px.pie(
            custos_categoria, 
            values='Valor', 
            names='Categoria',
            title="Distribuição de Custos por Categoria"
        )
        st.plotly_chart(fig_custos, use_container_width=True)
    
    with col2:
        # Evolução dos custos ao longo do tempo
        custos_tempo = df_filtrado.groupby('Data').agg({
            'Custo_Combustivel': 'sum',
            'Custo_Manutencao': 'sum',
            'Custo_Multas': 'sum'
        }).reset_index()
        
        fig_evolucao = go.Figure()
        fig_evolucao.add_trace(go.Scatter(
            x=custos_tempo['Data'], 
            y=custos_tempo['Custo_Combustivel'],
            mode='lines+markers',
            name='Combustível'
        ))
        fig_evolucao.add_trace(go.Scatter(
            x=custos_tempo['Data'], 
            y=custos_tempo['Custo_Manutencao'],
            mode='lines+markers',
            name='Manutenção'
        ))
        fig_evolucao.add_trace(go.Scatter(
            x=custos_tempo['Data'], 
            y=custos_tempo['Custo_Multas'],
            mode='lines+markers',
            name='Multas'
        ))
        fig_evolucao.update_layout(title="Evolução dos Custos ao Longo do Tempo")
        st.plotly_chart(fig_evolucao, use_container_width=True)
    
    # Ranking de custos por veículo
    st.subheader("🏆 Ranking de Custos por Veículo")
    custos_veiculo = df_filtrado.groupby('ID_Veiculo').agg({
        'Custo_Combustivel': 'sum',
        'Custo_Manutencao': 'sum',
        'Custo_Multas': 'sum'
    }).reset_index()
    custos_veiculo['Custo_Total'] = (custos_veiculo['Custo_Combustivel'] + 
                                     custos_veiculo['Custo_Manutencao'] + 
                                     custos_veiculo['Custo_Multas'])
    custos_veiculo = custos_veiculo.sort_values('Custo_Total', ascending=False).head(10)
    
    fig_ranking = px.bar(
        custos_veiculo, 
        x='ID_Veiculo', 
        y='Custo_Total',
        title="Top 10 Veículos com Maiores Custos"
    )
    st.plotly_chart(fig_ranking, use_container_width=True)

with tab2:
    st.subheader("⚙️ Análise Operacional")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Consumo médio por modelo
        consumo_modelo = df_operacional.groupby('Modelo')['Media_Consumo_KML'].mean().reset_index()
        consumo_modelo = consumo_modelo.sort_values('Media_Consumo_KML', ascending=False)
        
        fig_consumo = px.bar(
            consumo_modelo,
            x='Modelo',
            y='Media_Consumo_KML',
            title="Consumo Médio por Modelo",
            labels={'Media_Consumo_KML': 'Consumo (KM/L)'}
        )
        st.plotly_chart(fig_consumo, use_container_width=True)
    
    with col2:
        # Utilização da frota (KM rodados por veículo)
        utilizacao_frota = df_operacional.groupby('ID_Veiculo')['KM_Rodado'].sum().reset_index()
        utilizacao_frota = utilizacao_frota.sort_values('KM_Rodado', ascending=False).head(10)
        
        fig_utilizacao = px.bar(
            utilizacao_frota,
            x='ID_Veiculo',
            y='KM_Rodado',
            title="Top 10 Veículos Mais Utilizados",
            labels={'KM_Rodado': 'KM Rodados'}
        )
        st.plotly_chart(fig_utilizacao, use_container_width=True)
    
    # Análise temporal da operação
    st.subheader("📈 Análise Temporal da Operação")
    operacao_tempo = df_operacional.groupby('Data').agg({
        'KM_Rodado': 'sum',
        'Litros_Consumidos': 'sum'
    }).reset_index()
    operacao_tempo['Consumo_Diario'] = operacao_tempo['KM_Rodado'] / operacao_tempo['Litros_Consumidos']
    
    fig_temporal = make_subplots(
        rows=2, cols=1,
        subplot_titles=('KM Rodados por Dia', 'Consumo Médio Diário'),
        vertical_spacing=0.1
    )
    
    fig_temporal.add_trace(
        go.Scatter(x=operacao_tempo['Data'], y=operacao_tempo['KM_Rodado'], name='KM Rodados'),
        row=1, col=1
    )
    
    fig_temporal.add_trace(
        go.Scatter(x=operacao_tempo['Data'], y=operacao_tempo['Consumo_Diario'], name='Consumo (KM/L)'),
        row=2, col=1
    )
    
    fig_temporal.update_layout(height=600, title_text="Análise Temporal da Operação")
    st.plotly_chart(fig_temporal, use_container_width=True)

with tab3:
    st.subheader("🔧 Análise de Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Custos de manutenção por modelo
        manutencao_modelo = df_filtrado.groupby('Modelo')['Custo_Manutencao'].sum().reset_index()
        manutencao_modelo = manutencao_modelo.sort_values('Custo_Manutencao', ascending=False)
        
        fig_manutencao = px.bar(
            manutencao_modelo,
            x='Modelo',
            y='Custo_Manutencao',
            title="Custos de Manutenção por Modelo"
        )
        st.plotly_chart(fig_manutencao, use_container_width=True)
    
    with col2:
        # Tempo de parada por manutenção
        parada_veiculo = df_filtrado.groupby('ID_Veiculo')['Tempo_Parada_Manutencao_Horas'].sum().reset_index()
        parada_veiculo = parada_veiculo.sort_values('Tempo_Parada_Manutencao_Horas', ascending=False).head(10)
        
        fig_parada = px.bar(
            parada_veiculo,
            x='ID_Veiculo',
            y='Tempo_Parada_Manutencao_Horas',
            title="Top 10 Veículos com Maior Tempo de Parada"
        )
        st.plotly_chart(fig_parada, use_container_width=True)
    
    # Disponibilidade da frota
    st.subheader("📊 Disponibilidade da Frota")
    
    # Calcular disponibilidade (assumindo 24h por dia como tempo total possível)
    disponibilidade_data = []
    for veiculo in df_filtrado['ID_Veiculo'].unique():
        df_veiculo = df_filtrado[df_filtrado['ID_Veiculo'] == veiculo]
        tempo_total_possivel = len(df_veiculo) * 24  # 24 horas por dia
        tempo_parada = df_veiculo['Tempo_Parada_Manutencao_Horas'].sum()
        disponibilidade = ((tempo_total_possivel - tempo_parada) / tempo_total_possivel) * 100
        
        disponibilidade_data.append({
            'Veiculo': veiculo,
            'Disponibilidade': disponibilidade
        })
    
    df_disponibilidade = pd.DataFrame(disponibilidade_data)
    df_disponibilidade = df_disponibilidade.sort_values('Disponibilidade', ascending=True).head(10)
    
    fig_disponibilidade = px.bar(
        df_disponibilidade,
        x='Disponibilidade',
        y='Veiculo',
        orientation='h',
        title="Disponibilidade da Frota (%)",
        labels={'Disponibilidade': 'Disponibilidade (%)'}
    )
    st.plotly_chart(fig_disponibilidade, use_container_width=True)

with tab4:
    st.subheader("🛡️ Análise de Segurança")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Acidentes por modelo
        acidentes_modelo = df_filtrado.groupby('Modelo')['Acidentes'].sum().reset_index()
        acidentes_modelo = acidentes_modelo.sort_values('Acidentes', ascending=False)
        
        fig_acidentes = px.bar(
            acidentes_modelo,
            x='Modelo',
            y='Acidentes',
            title="Acidentes por Modelo"
        )
        st.plotly_chart(fig_acidentes, use_container_width=True)
    
    with col2:
        # Multas por modelo
        multas_modelo = df_filtrado.groupby('Modelo')['Custo_Multas'].sum().reset_index()
        multas_modelo = multas_modelo.sort_values('Custo_Multas', ascending=False)
        
        fig_multas = px.bar(
            multas_modelo,
            x='Modelo',
            y='Custo_Multas',
            title="Custos com Multas por Modelo"
        )
        st.plotly_chart(fig_multas, use_container_width=True)
    
    # Índice de acidentes por KM
    st.subheader("📈 Índice de Segurança")
    
    seguranca_data = []
    for modelo in df_filtrado['Modelo'].unique():
        df_modelo = df_filtrado[df_filtrado['Modelo'] == modelo]
        km_total_modelo = df_modelo['KM_Rodado'].sum()
        acidentes_total_modelo = df_modelo['Acidentes'].sum()
        
        if km_total_modelo > 0:
            indice_acidentes = (acidentes_total_modelo / km_total_modelo) * 1000000  # Por milhão de KM
        else:
            indice_acidentes = 0
        
        seguranca_data.append({
            'Modelo': modelo,
            'Indice_Acidentes_por_Milhao_KM': indice_acidentes
        })
    
    df_seguranca = pd.DataFrame(seguranca_data)
    df_seguranca = df_seguranca.sort_values('Indice_Acidentes_por_Milhao_KM', ascending=False)
    
    fig_indice = px.bar(
        df_seguranca,
        x='Modelo',
        y='Indice_Acidentes_por_Milhao_KM',
        title="Índice de Acidentes por Milhão de KM"
    )
    st.plotly_chart(fig_indice, use_container_width=True)

# Seção de dados brutos
st.markdown("---")
st.subheader("📋 Dados Brutos")

# Opção para baixar dados
csv = df_filtrado.to_csv(index=False)
st.download_button(
    label="📥 Baixar dados filtrados como CSV",
    data=csv,
    file_name='kpis_frota_filtrados.csv',
    mime='text/csv'
)

# Mostrar tabela
st.dataframe(df_filtrado, use_container_width=True)

# Rodapé
st.markdown("---")
st.markdown("**Dashboard KPIs de Gestão de Frotas** | Desenvolvido com Streamlit e Plotly")
