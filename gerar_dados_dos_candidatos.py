import streamlit as st
import pandas as pd
from requests.utils import quote
from unidecode import unidecode
from io import BytesIO
import polars as pl

st.title('Gerar dados dos Candidatos')
st.write('Ferramenta para gerar dados a partir dos filtro selecionados')

estados = {
        'AC': 'Acre',
        'AL': 'Alagoas',
        'AP': 'Amapá',
        'AM': 'Amazonas',
        'BA': 'Bahia',
        'CE': 'Ceará',
        'DF': 'Distrito Federal',
        'ES': 'Espírito Santo',
        'GO': 'Goiás',
        'MA': 'Maranhão',
        'MT': 'Mato Grosso',
        'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais',
        'PA': 'Pará',
        'PB': 'Paraiba',
        'PR': 'Paraná',
        'PE': 'Pernambuco',
        'PI': 'Piauí',
        'RJ': 'Rio de Janeiro',
        'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul',
        'RO': 'Rondônia',
        'RR': 'Roraima',
        'SC': 'Santa Catarina',
        'SP': 'São Paulo',
        'SE': 'Sergipe',
        'TO': 'Tocantins'
}


@st.cache_data
def load_data(ano, sigla_estado, bairro: list ='', municipio: list ='', candidato: list ='', partido: list =''):
    
    link = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
    df = pd.read_csv(link)
    df['Ano'] = ano

    if len(bairro) > 0:
        bairro = [bairro.upper().strip() for bairro in bairro.split(',')]
        df = df[df['Bairro'].str.contains('|'.join([p for p in bairro]))]

    if len(partido) > 0:
        partido = [partido.upper().strip() for partido in partido.split(',')]
        df = df[df['Sigla do partido'].str.contains('|'.join([p for p in partido]))]

    if len(candidato) > 0:
        candidato = [candidato.upper().strip() for candidato in candidato.split(',')]
        df = df[
            df['Nome do candidato'].str.contains('|'.join([c for c in candidato]))]

    if len(municipio) > 0:
        municipio = [unidecode(municipio.upper()).strip() for municipio in municipio.split(',')] # ['RIO DE JANEIRO', 'DUQUE DE CAXIAS']
        df = df[df['Município'].apply(lambda x: unidecode(str(x).upper()) in municipio)]

    return df


@st.cache_data
def generate_filename(ano, sigla_estado, bairro='', municipio='', candidato='', partido=''):
    params = []

    if ano:
        ano_list = ' e '.join(ano)


    if bairro:
        bairro_list = [bairro.upper().strip() for bairro in bairro.split(',')]
        params.append(' e '.join(bairro_list))

    if municipio:
        municipio_list = [municipio.upper().strip() for municipio in municipio.split(',')]
        params.append(' e '.join(municipio_list))

    if candidato:
        candidato_list = [candidato.upper().strip() for candidato in candidato.split(',')]
        params.append(' e '.join(candidato_list))

    if partido:
        partido_list = [partido.upper().strip() for partido in partido.split(',')]
        params.append('(' + ' e '.join(partido_list) + ')')
    
    filename = f'ELEIÇÕES {ano_list} {sigla_estado}'
    if params:
        filename += ' ' + f"{' - '.join(params)}"
    filename += '.xlsx'

    return filename


@st.cache_data
def generate_excel(df):
    buffer = BytesIO()
    df_polars = pl.from_pandas(df)
    df_polars.write_excel(buffer)
    buffer.seek(0)
    return buffer


anos = [str(i) for i in range(2024, 2015, -2)]
dfs = []

# ano = st.text_input('Ano', placeholder='ex.: 2020 ou 2020, 2022')
anos_select = st.multiselect('Ano*', options=anos, placeholder='Selecione o(s) ano(s)')
# sigla_estado = st.text_input('Sigla do Estado', placeholder='ex.: RJ')
sigla_estado = st.selectbox('Sigla da Unidade Federativa (UF)*', options=estados.keys(), placeholder='Selecione a(s) unidade(s) federativa(s)', index=list(estados.keys()).index('RJ'))

bairro_input = municipio_input = candidato_input = partido_input = ''
bairro = st.checkbox('Bairro(s)')
if bairro:
    bairro_input = st.text_input('Bairro', placeholder='ex.: OLARIA ou OLARIA, VAZ LOBO', label_visibility='collapsed')

municipio = st.checkbox('Município(s)')
if municipio:
    municipio_input = st.text_input('Município(s)', placeholder='ex.: RIO DE JANEIRO ou RIO DE JANEIRO, SÃO JOÃO DE MERITI', label_visibility='collapsed')

candidato = st.checkbox('Candidato(s)')
if candidato:
    candidato_input = st.text_input('Candidato(s)', placeholder='ex.: PEDRO DUARTE ou PEDRO DUARTE, EDUARDO PAES', label_visibility='collapsed')

partido = st.checkbox('Partido(s)')
if partido:
    partido_input = st.text_input('Partido(s)', placeholder='ex.: PSD ou PSD, NOVO', label_visibility='collapsed')

if st.button('Carregar dados'):
    if not anos_select or not sigla_estado:
        st.warning('Preencha todos os campos obrigatórios (Ano e Sigla do Estado)')
    else:
        with st.spinner('Carregando dados!'):
            try:
                anos_select = sorted(anos_select)
                for ano in anos_select:
                    df = load_data(ano, sigla_estado, bairro=bairro_input, municipio=municipio_input, candidato=candidato_input, partido=partido_input)
                    dfs.append(df)
                    
                filename = generate_filename(anos_select, sigla_estado, bairro=bairro_input, municipio=municipio_input, candidato=candidato_input, partido=partido_input)
                new_df = pd.concat(dfs)
                st.dataframe(new_df, hide_index=True)
                
        
            except Exception as e:
                st.error(f'Error ao carregar os dados. {e}')

        with st.spinner('Carregando botão para Download'):
                    buffer = generate_excel(new_df)
                    st.download_button(
                        label='Baixar os dados como Excel',
                        data=buffer,
                        file_name=filename,
                        mime='application/vnd.ms-excel'
                    )
        

    
