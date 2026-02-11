import streamlit as st
from gerar_dados_dos_candidatos import estados
from requests.utils import quote
import polars as pl
import plotly.express as px



st.set_page_config(page_title='asd', layout='wide')
st.title('Comparativo geral individual do candidato')

col1, col2  = st.columns([1, 1])
anos = [2016, 2018, 2020, 2022, 2024]



def normalize_data(df):
    """Normaliza nomes e cargos no dataframe"""
    return df.with_columns([
        pl.col('Nome do candidato').str.replace('PEDRO DUARTE JR', 'PEDRO DUARTE'),
        pl.col('Cargo').str.to_uppercase()
    ])

@st.cache_data(ttl=26298000, persist='disk')
def read_csv(ano, sigla_estado, columns=None):

    url = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
    df = pl.scan_csv(url)
    
    if columns:
        df = df.select(columns)
    df = df.with_columns(pl.lit(ano).alias('Ano').cast(pl.Int32))
    df = normalize_data(df)
    # Trocar pedro duarte jr para pedro duarte e trocar VEREADOR para Vereador

    return df.collect()
    

@st.cache_data
def read_csv_cached(ano, sigla_estado, columns=None) -> pl.DataFrame:
    with st.spinner('Carregando candidatos...'):
        return read_csv(ano, sigla_estado, columns)
    

@st.cache_data
def read_params_cache(df, param):
    param = df.select(param).unique().to_series().to_list()
    return param


@st.cache_data
def load_all_years(sigla_estado, columns=None):
    dfs = []
    for ano in anos:
        try:
            dfs.append(read_csv(ano, sigla_estado, columns))
        except:
            pass
        
    return normalize_data(pl.concat(dfs))


def groupby_to_charts(df, candidato, columns=None, ascending=None):
    main_cols = ['Nome do candidato', 'Votos', 'Ano']
    df_all = df.select(main_cols + [columns]).filter(pl.col('Nome do candidato')==candidato) if columns else df.select(main_cols).filter(pl.col('Nome do candidato') == candidato)
    df_all_groupby = df_all.group_by(['Ano', columns]).agg(pl.col('Votos').sum()).sort(ascending, descending=True) if ascending else df_all.group_by(['Ano', columns]).agg(pl.col('Votos').sum()).sort('Ano', descending=True)
    return df_all_groupby



sigla_estado = col1.selectbox('Selecione a Sigla do Estado', options=list(estados.keys()), index=list(estados.keys()).index('RJ'))

df_all = load_all_years(sigla_estado)

# municipio = col3.multiselect(label='Selecione o município', options=read_params_cache(df_all, 'Município'))
lista_candidatos = read_params_cache(df_all, 'Nome do candidato')
index_padrao = lista_candidatos.index('PEDRO DUARTE') if 'PEDRO DUARTE' in lista_candidatos else 0

candidato = col2.selectbox(label='Selecione o candidato', options=lista_candidatos, index=index_padrao)

if candidato:
    col_line, col_occupation = st.columns([2, 1.5])
    # Crescimento de cada candidato entre 2016 a 2024
    df_candidate_growth = groupby_to_charts(df_all, candidato)
    df_candidate_growth_line = px.line(df_candidate_growth.to_pandas(), x='Ano', y='Votos', markers=True, text='Votos', title='Evolução de votos')
    df_candidate_growth_line.update_xaxes(ticktext = [str(ano) for ano in anos], tickvals=anos)
    df_candidate_growth_line.update_traces(textposition='top center', texttemplate='%{y:,}')
    df_candidate_growth_line.update_layout(title_font=dict(color='white', size=25))
    col_line.plotly_chart(df_candidate_growth_line, width='stretch')
        
    # 10 Bairros mais votados 
    anos_candidato = df_all.filter(pl.col('Nome do candidato') == candidato).select('Ano').unique().to_series().to_list()

    ano = st.multiselect(
        'Selecione o Ano da Eleição', 
        anos_candidato, 
        default=anos_candidato)

    if len(ano) == 0:
        st.warning('Selecione pelo menos um ano para visualizar os dados')
        st.stop()
    
    col11, col22 = st.columns([1, 1])
    df_candidate_neighborhood = groupby_to_charts(df_all, candidato, 'Bairro')
    df_candidate_neighborhood = df_candidate_neighborhood.filter([pl.col('Ano').is_in(ano)])
    df_candidate_neighborhood = df_candidate_neighborhood.group_by('Bairro').agg(pl.col('Votos').sum()).sort('Votos', descending=True)
    max_votes = df_candidate_neighborhood.head(1)['Votos'].max()
   
    df_candidate_neighborhood_most_voted_bar = px.bar(df_candidate_neighborhood.head(10), y='Bairro', x='Votos', orientation='h', text_auto=True, barmode='group', title='10 Bairros com mais votos')
    df_candidate_neighborhood_most_voted_bar.update_layout(yaxis=dict(autorange="reversed"), title_font=dict(color='white', size=25))
    df_candidate_neighborhood_most_voted_bar.update_traces(textposition='outside', texttemplate='%{x:,}', textfont=dict(color='white', size=18))
    df_candidate_neighborhood_most_voted_bar.update_xaxes(showgrid=False, range=[0, max_votes * 1.15])
    df_candidate_neighborhood_most_voted_bar.update_yaxes(tickfont=dict(color='white', size=16))

    col11.plotly_chart(df_candidate_neighborhood_most_voted_bar)

    # 10 Municípios mais votados
    df_candidate_municipality = groupby_to_charts(df_all, candidato, 'Município')
    df_candidate_municipality = df_candidate_municipality.filter([pl.col('Ano').is_in(ano)])
    df_candidate_municipality = df_candidate_municipality.group_by('Município').agg(pl.col('Votos').sum()).sort('Votos', descending=True)
    max_votes = df_candidate_municipality.head(1)['Votos'].max()
    df_candidate_municipality_most_voted_bar = px.bar(df_candidate_municipality.head(10), y='Município', x='Votos', orientation='h', text_auto=True, barmode='group', title='10 Municípios com mais votos')
    df_candidate_municipality_most_voted_bar.update_traces(texttemplate='%{x:,}', textposition='outside', textfont=dict(color='white', size=18))
    df_candidate_municipality_most_voted_bar.update_layout(yaxis=dict(autorange="reversed"), title_font=dict(color='white', size=25))
    df_candidate_municipality_most_voted_bar.update_xaxes(showgrid=False, range=[0, max_votes * 1.25])
    df_candidate_municipality_most_voted_bar.update_yaxes(tickfont=dict(color='white', size=16))

    col22.plotly_chart(df_candidate_municipality_most_voted_bar)

    
    # Cargos com mais votos
    df_candidates_by_occupation = groupby_to_charts(df_all, candidato, 'Cargo')
    df_candidates_by_occupation = df_candidates_by_occupation.filter([pl.col('Ano').is_in(ano)])
    df_candidates_by_occupation = df_candidates_by_occupation.group_by('Cargo').agg(pl.col('Votos').sum()).sort('Votos', descending=True)
    df_candidates_by_occupation_pie = px.pie(
    df_candidates_by_occupation,
    names='Cargo',
    values='Votos',
    title='Distribuição de votos por cargo'
)

    df_candidates_by_occupation_pie.update_traces(
        textinfo='percent+value',
        texttemplate='%{label}<br>%{value:,} votos<br>(%{percent})',
        textfont=dict(size=14)
    )
    df_candidates_by_occupation_pie.update_layout(title_font=dict(color='white', size=25))

    col_occupation.plotly_chart(df_candidates_by_occupation_pie, width='stretch')









