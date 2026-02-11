import streamlit as st
from gerar_dados_dos_candidatos import estados
from requests.utils import quote
import pandas as pd
import polars as pl
import plotly.express as px

st.set_page_config(layout='wide')
st.title('Comparação de Candidatos por Votos')
st.info('Ferramenta para comparar candidatos por votos em diferentes eleições através de gráficos.')

def normalize_data(df):
    """Normaliza nomes e cargos no dataframe"""
    return df.with_columns([
        pl.col('Nome do candidato').str.replace('PEDRO DUARTE JR', 'PEDRO DUARTE'),
        pl.col('Cargo').str.to_uppercase()
    ])

@st.cache_data
def read_csv(ano, sigla_estado):
    try:
        url = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
        df = pd.read_csv(url)
        df['Ano'] = ano
        return df
    except:
        st.warning(f'{estados[sigla_estado.upper()]} não encontrado nas eleições de {ano}')
        return 

@st.cache_data
def read_csv_cached(ano, sigla_estado):
    with st.spinner('Carregando candidatos...'):
        return read_csv(ano, sigla_estado)
    

col1, col2, col3 = st.columns([1, 1, 1])
con1 = st.container()
col11, col22 = st.columns([1,1])
ano = col1.selectbox('Selecione o Ano da Eleição', [2024, 2022, 2020, 2018, 2016])
sigla_estado = col2.selectbox('Selecione a Sigla do Estado', options=list(estados.keys()), index=list(estados.keys()).index('RJ'))
df = read_csv_cached(ano, sigla_estado)

if isinstance(df, pd.DataFrame):
    candidatos_urna = df['Nome do candidato'].unique()
    candidatos = col3.multiselect('Candidatos para comparação', candidatos_urna, placeholder='Candidatos')
    df_candidates = df[df['Nome do candidato'].isin(candidatos)]
    df_chart = df_candidates.groupby('Nome do candidato')['Votos'].sum().reset_index()
    
    df_chart_plotly = px.bar(df_chart, y='Nome do candidato', x='Votos', text_auto=True, text='Votos', orientation='h', title='Votos gerais por candidato')
    df_chart_plotly.update_traces(texttemplate='%{text:,.0f}')
    col11.plotly_chart(df_chart_plotly)

    df_neighborhood = df_candidates.groupby(['Nome do candidato', 'Bairro'])['Votos'].sum().reset_index().sort_values(by='Votos', ascending=False).head(10)
    df_neighborhood_plotly = px.bar(df_neighborhood, y='Nome do candidato', x='Votos', color='Bairro', text_auto=True, text='Votos', orientation='h', title='10 Bairros mais votados')
    col22.plotly_chart(df_neighborhood_plotly)

    # Partido vs Partido (partido por municipio x bairro) - heatmap

    df_parties = df_candidates.groupby(['Sigla do partido', 'Município'])['Votos'].sum().reset_index()
    top_10_parties = df_parties.groupby('Sigla do partido', as_index=False)['Votos'].sum().nlargest(10, 'Votos')['Sigla do partido']
    top_10_municipiums = df_parties.groupby('Município', as_index=False)['Votos'].sum().nlargest(10, 'Votos')['Município']
    df_top_10_parties = df_parties[(df_parties['Sigla do partido'].isin(top_10_parties)) & (df_parties['Município'].isin(top_10_municipiums))]

    print(df_parties)
    df_parties_heatmap = px.density_heatmap(df_top_10_parties, x='Município', y='Sigla do partido', z='Votos', color_continuous_scale='Reds')

    df_line = px.ecdf(df_top_10_parties, x='Votos', color='Sigla do partido')
    st.plotly_chart(df_parties_heatmap)



    # st.bar_chart(df_chart, x='Nome do candidato', y='Votos', color='Nome do candidato', use_container_width=True, horizontal=True, height=400) 
            
        




# 1 - Desempenho eleitoral
# Votos por municipio

# Votos por bairro


# Votos por candidato



