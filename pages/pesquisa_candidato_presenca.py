import streamlit as st
import pandas as pd
from requests.utils import quote
from gerar_dados_dos_candidatos import estados
from concurrent.futures import ThreadPoolExecutor

st.title('Identificar presença dos candidatos nas urnas')
st.write('Ferramenta para identificar os candidatos pela nome aproximado e se eles estão presentes nas urnas do ano de 2016 a 2024')


anos = [2016, 2018, 2020, 2022, 2024]

def colorir_sim_nao(val):
    val = str(val).strip()
    if val == 'Sim':
        return 'background-color: #c6efce; color: #006100'  # verde
    elif val == 'Não':
        return 'background-color: #ffc7ce; color: #9c0006'  # vermelho
    return ''



@st.cache_data
def detectar_candidatos(ano, sigla_estado, nome_urna): 
    try:
        url = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
        candidatos = pd.read_csv(url)
        candidatos['Anos'] = ano

        candidatos = candidatos[
        candidatos['Nome do candidato'].str.contains(nome_urna)]

        candidatos['Status'] = 'Sim'

        return candidatos[['Nome do candidato', 'Anos', 'Status']]

    except:
        print('nao achou')
        return pd.DataFrame(columns=['Nome do candidato', 'Anos', 'Status'])
    
@st.cache_data
def procurar_candidato(nome_urna:str, sigla_estado):
    '''
    Buscar nome do candidato no arquivo de cada ano.
    '''
    nome_urna = nome_urna.upper()

    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(lambda ano: detectar_candidatos(ano, sigla_estado, nome_urna), anos))
    
    df_final = pd.concat(resultados)
    df_pivot = df_final.pivot_table(
        index='Nome do candidato',
        columns='Anos',
        values='Status',
        aggfunc='max'
    ).reset_index().fillna('Não')

    df_pivot.columns.name = None
    df_pivot.index.name = None

    

    # Verificar se em todas as colunas que estão com os anos selecionados, se não tiver aparecendo uma a qual deveria aparecer, o status é NÃO
    # Verificar se a coluna do pivot tem os mesmos anos 1: 
    try:
        colunas_pivot = set(df_pivot.columns[1:])
        anos_set = set(anos)
        # print('lista pivot', list(df_pivot.columns[1:]))
        # print('lista anos', anos)
        if colunas_pivot != anos_set: 
            
            diferenca = anos_set.difference(colunas_pivot)
            for diferente in diferenca:
              
                df_pivot[diferente] = 'Não'
            
            
    except Exception as e:
        print('nao', e)

    
    
    first_col = df_pivot.columns[0]
    other_cols = sorted(df_pivot.columns[1:])
    df_pivot = df_pivot[[first_col] + other_cols]

    st.dataframe(df_pivot.style.map(colorir_sim_nao))


nome_urna = st.text_input('Nome do candidato na Urna*', placeholder='ex.: PEDRO DUARTE')
sigla_estado = st.selectbox('Sigla da Unidade Federativa (UF)*', options=estados.keys(), placeholder='Selecione a(s) unidade(s) federativa(s)', index=list(estados.keys()).index('RJ'), key='sigla')
# sigla_estado = st.text_input('Sigla do Estado', placeholder='ex.: RJ')
if st.button('Verificar nomes próximos'):
    if not nome_urna or not sigla_estado:
        st.warning('Preencha todos os campos obrigatórios (Nome do candidato na Urna e Sigla do Estado) *')
    else:
        with st.spinner('Verificando candidato...'):
            procurar_candidato(nome_urna, sigla_estado)
            