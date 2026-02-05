import streamlit as st
import pandas as pd
from requests.utils import quote
from gerar_dados_dos_candidatos import estados
from concurrent.futures import ThreadPoolExecutor

st.title('Identificar nomes dos candidatos')
st.write('Ferramenta para identificar os candidatos pela nome aproximado')


anos = [2016, 2018, 2020, 2022, 2024]

@st.cache_data
def detectar_candidatos(ano, sigla_estado, nome_urna): 
    try:
        url = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
        candidatos = pd.read_csv(url)
        candidatos['Anos'] = ano

        candidatos = candidatos[
        candidatos['Nome do candidato'].str.contains(nome_urna)]

        
        # novos_candidatos = candidatos.groupby(['Nome do candidato', 'Ano'])['Votos'].sum().reset_index().sort_values(by='Nome do candidato', ascending=True)
        

        return candidatos[['Nome do candidato', 'Anos']]

    except:
        return pd.DataFrame(columns=['Nome do candidato', 'Anos'])
    
@st.cache_data
def procurar_candidato(nome_urna:str, sigla_estado):
    '''
    Buscar nome do candidato no arquivo de cada ano.
    '''
    nome_urna = nome_urna.upper()

    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(lambda ano: detectar_candidatos(ano, sigla_estado, nome_urna), anos))
    
    df_final = pd.concat(resultados, ignore_index=True)
    df_final = df_final.groupby('Nome do candidato')['Anos'].apply(lambda x: ', '.join(map(str, sorted(x.unique())))).reset_index()
    
    st.dataframe(df_final)


nome_urna = st.text_input('Nome do candidato na Urna*', placeholder='ex.: PEDRO DUARTE')
sigla_estado = st.selectbox('Sigla da Unidade Federativa (UF)*', options=estados.keys(), placeholder='Selecione a(s) unidade(s) federativa(s)', index=list(estados.keys()).index('RJ'), key='sigla')
anos_select = st.multiselect('Ano*', options=anos, placeholder='Selecione o(s) ano(s)', key='year')
# sigla_estado = st.text_input('Sigla do Estado', placeholder='ex.: RJ')
if st.button('Verificar nomes próximos'):
    if not nome_urna or not sigla_estado:
        st.warning('Preencha todos os campos obrigatórios (Nome do candidato na Urna e Sigla do Estado) *')
    else:
        with st.spinner('Verificando candidato...'):
            procurar_candidato(nome_urna, sigla_estado)
            