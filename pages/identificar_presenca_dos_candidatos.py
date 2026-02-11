import streamlit as st
import polars as pl
from requests.utils import quote
from gerar_dados_dos_candidatos import estados
from concurrent.futures import ThreadPoolExecutor

st.title('Identificar a presença dos candidatos nas urnas')
st.info('Ferramenta para identificar os candidatos pela nome aproximado e se eles estão presentes nas urnas do ano de 2016 a 2024')


anos = [2016, 2018, 2020, 2022, 2024]

def colorir_sim_nao(val):
    val = str(val).strip()
    if val == 'Sim':
        return 'background-color: #c6efce; color: #006100'  # verde
    elif val == 'Não':
        return 'background-color: #ffc7ce; color: #9c0006'  # vermelho
    return 


def normalize_data(df):
    """Normaliza nomes e cargos no dataframe"""
    return df.with_columns([
        pl.col('Nome do candidato').str.replace('PEDRO DUARTE JR', 'PEDRO DUARTE')])

@st.cache_data(ttl=26298000, persist='disk')
def detectar_candidatos(ano, sigla_estado, nome_urna=None, columns=None): 
    url = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
    candidatos = pl.scan_csv(url, low_memory=True, infer_schema_length=0)

    if columns:
        candidatos = candidatos.select(columns)
    if nome_urna:
        candidatos = candidatos.filter(
            pl.col('Nome do candidato') == nome_urna)
    
    
    candidatos = normalize_data(candidatos)
    
    candidatos = candidatos.with_columns([pl.lit(ano).alias('Anos'), pl.lit('Sim').alias('Status')]).select(['Nome do candidato', 'Anos', 'Status']).collect()

    return candidatos


@st.cache_data
def cache_candidatos(sigla_estado): 
    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(lambda ano: detectar_candidatos(ano, sigla_estado, columns=['Nome do candidato']), anos))
    
    candidatos = normalize_data(pl.concat(resultados))
    candidatos = sorted(candidatos.select(pl.col('Nome do candidato')).unique().to_series())

    return candidatos
    

@st.cache_data
def procurar_candidato(nome_urna:str, sigla_estado):
    '''
    Buscar nome do candidato no arquivo de cada ano.
    '''
    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(lambda ano: detectar_candidatos(ano, sigla_estado, nome_urna), anos))
    
    df_final = normalize_data(pl.concat(resultados))
    df_pivot = df_final.pivot(
        index='Nome do candidato',
        on='Anos',
        values='Status',
        aggregate_function='max'
    ).fill_null('Não')

    # df_pivot.columns.name = None
    # df_pivot.index.name = None    

    # Verificar se em todas as colunas que estão com os anos selecionados, se não tiver aparecendo uma a qual deveria aparecer, o status é NÃO
    # Verificar se a coluna do pivot tem os mesmos anos 1: 
    try:
        
        set_anos_c = set(anos)
        colunas_pivot = set(int(ano) for ano in df_pivot.columns[1:])   
            
        if colunas_pivot != set_anos_c: 
            diferenca = set_anos_c.difference(colunas_pivot)
            for diferente in diferenca:
                df_pivot = df_pivot.with_columns(pl.lit('Não').alias(str(diferente)))

    except Exception as e:
        print(e)

    
    cols = ['Nome do candidato'] + sorted([c for c in df_pivot.columns if c != 'Nome do candidato'])
    df_pivot = df_pivot.select(cols)

    st.dataframe(df_pivot.to_pandas().style.map(colorir_sim_nao), width='stretch', hide_index=True)


sigla_estado = st.selectbox('Sigla da Unidade Federativa (UF)*', options=estados.keys(), placeholder='Selecione a unidade federativa', index=list(estados.keys()).index('RJ'), key='sigla')
candidatos = cache_candidatos(sigla_estado)


nome_urna = st.selectbox('Nome do candidato na Urna*', placeholder='Selecione o candidato', options=['Selecione um candidato'] + candidatos)
with st.spinner('Verificando candidato...'):
    procurar_candidato(nome_urna, sigla_estado)

            