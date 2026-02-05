import streamlit as st
from requests.utils import quote
from gerar_dados_dos_candidatos import estados
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor

@st.cache_data
def verificar_ano(ano, nome_urna, sigla_estado):
    try:
        url = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
        candidatos = pd.read_csv(url)
        candidatos = candidatos[
        candidatos['Nome do candidato'].str.contains(nome_urna)]

        return (ano, len(candidatos) > 0)
    except:
        return (ano, False)


@st.cache_data
def detectar_candidato_eleicao(nome_urna: str, sigla_estado: str ='rj'):
    
    anos = [2016, 2018, 2020, 2022, 2024]
    nome_urna = nome_urna.upper()
    presente_urna, ausente_urna = list(), list()

    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(lambda ano: verificar_ano(ano, nome_urna, sigla_estado), anos))

    for ano, encontrado in resultados:
        if encontrado:
            presente_urna.append(ano)
        else:
            ausente_urna.append(ano)
    

    if len(presente_urna) > 0:
    # print(f'\033[m\033[1;32mO candidato {nome_urna.title()} está presente no ano {ano}\033[m')
        st.success(f'Candidato presente no(s) ano(s): {", ".join(str(presente) for presente in presente_urna)}')
    if len(ausente_urna) > 0:
    # print(f'\033[m\033[1;31mO candidato {nome_urna.title()} não está presente no ano {ano}\033[m')
        st.error(f'Candidato ausente no(s) ano(s): {", ".join(str(ausente) for ausente in ausente_urna)}')

    
st.title('Candidato presente na urna')
st.text('Verificar a presença de candidatos nos anos 2016, 2018, 2020, 2022, 2024')

nome_urna = st.text_input('Nome do candidato na Urna*', placeholder='ex.: PEDRO DUARTE')
sigla_estado = st.text_input('Sigla do Estado*', placeholder='ex.: RJ')
if st.button('Verificar'):
    if not nome_urna or not sigla_estado:
        st.warning('Preencha todos os campos obrigatórios (Nome do candidato na Urna e Sigla do Estado) *')
    else:
        with st.spinner('Verificando candidato...'):
            start = time.time()
            detectar_candidato_eleicao(nome_urna, sigla_estado)
            print(time.time() - start)
  
  