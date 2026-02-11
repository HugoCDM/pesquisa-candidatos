import streamlit as st
from requests.utils import quote
from io import BytesIO
import polars as pl

st.set_page_config(layout='wide')
st.title('Gerar dados dos Candidatos')
st.info('Ferramenta para gerar dados a partir dos filtro selecionados')
col1, col2 = st.columns([1, 1])
col11, col22, col33, col44 = st.columns([1, 1, 1, 1])
col111, col222 = st.columns([2, 1])


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
def load_data(ano, sigla_estado, bairro: list ='', municipio: list ='', candidato: list ='', partido: list ='', columns=''):
    
    link = f'https://raw.githubusercontent.com/HugoCDM/candidatos/main/Elei%C3%A7%C3%B5es%20{ano}%20-%20{quote(estados[sigla_estado.upper()])}.csv.gz'
    df = pl.scan_csv(link)

    if columns:
        df = df.select(columns)

    # df['Ano'] = ano
    df = df.with_columns(pl.lit(ano).alias('Ano'))

    if bairro:
        df = df.filter(pl.col('Bairro').is_in(bairro))

    if partido:
        df = df.filter(pl.col('Sigla do partido').is_in(partido))

    if candidato:
        df = df.filter(pl.col('Nome do candidato').is_in(candidato))

    if municipio:
        df = df.filter(pl.col('Município').is_in(municipio))

    return df.collect()


@st.cache_data
def generate_filename(ano, sigla_estado, bairro='', municipio='', candidato='', partido=''):
    params = []

    if ano:
        ano_list = ' e '.join(ano)

    if bairro:
        params.append(' e '.join(bairro))

    if municipio:
        params.append(' e '.join(municipio))

    if candidato:
        params.append(' e '.join(candidato))

    if partido:
        params.append('(' + ' e '.join(partido) + ')')
    
    filename = f'ELEIÇÕES {ano_list} {sigla_estado}'
    if params:
        filename += ' ' + f"{' - '.join(params)}"
    filename += '.xlsx'

    return filename


@st.cache_data
def generate_excel(df):
    buffer = BytesIO()    
    df.write_excel(buffer)
    buffer.seek(0)  
    return buffer   


@st.cache_data
def load_filter_options(anos_select, sigla_estado):
    try:
        bairros_municipios = []
        for ano in anos_select:
            df_bairros_municipios = load_data(ano, sigla_estado, columns=['Bairro', 'Município', 'Sigla do partido', 'Nome do candidato'])
            df_bairros_municipios = df_bairros_municipios.select(pl.col(['Bairro', 'Município', 'Sigla do partido', 'Nome do candidato']))
            # df_bairros_municipios = df_bairros_municipios[['Bairro', 'Município']]
            # print(df_bairros_municipios)
            bairros_municipios.append(df_bairros_municipios)
            
        bairros_municipios_df = pl.concat(bairros_municipios)   

        bairros = sorted(bairros_municipios_df.select(pl.col('Bairro')).unique().to_series())
        municipios = sorted(bairros_municipios_df.select(pl.col('Município')).unique().to_series())
        partidos = sorted(bairros_municipios_df.select(pl.col('Sigla do partido')).unique().to_series())
        candidatos = sorted(bairros_municipios_df.select(pl.col('Nome do candidato')).unique().to_series())

        return bairros, municipios, partidos, candidatos
    except:
        return



anos = [str(i) for i in range(2024, 2015, -2)]

# ano = st.text_input('Ano', placeholder='ex.: 2020 ou 2020, 2022')
anos_select = col1.multiselect('Ano*', options=anos, placeholder='Selecione o(s) ano(s)')
# sigla_estado = st.text_input('Sigla do Estado', placeholder='ex.: RJ')
sigla_estado = col2.selectbox('Sigla da Unidade Federativa (UF)*', options=estados.keys(), placeholder='Selecione a(s) unidade(s) federativa(s)', index=list(estados.keys()).index('RJ'))

try:
    bairros, municipios, partidos, candidatos = load_filter_options(anos_select, sigla_estado)
    bairro_input = municipio_input = candidato_input = partido_input = ''
    bairro = col11.checkbox('Bairro(s)')
    if bairro:
        bairro_input = col11.multiselect('Bairro', placeholder='Selecione o(s) bairro(s)', options=bairros, label_visibility='collapsed')

    municipio = col22.checkbox('Município(s)')
    if municipio:
        municipio_input = col22.multiselect('Município(s)', placeholder='Selecione o(s) município(s)', options=municipios, label_visibility='collapsed')

    candidato = col33.checkbox('Candidato(s)')
    if candidato:
        candidato_input = col33.multiselect('Candidato(s)', placeholder='Selecione o(s) candidato(s)', options=candidatos, label_visibility='collapsed')

    partido = col44.checkbox('Partido(s)')
    if partido:
        partido_input = col44.multiselect('Partido(s)', placeholder='Selecione o(s) partido(s)', options=partidos, label_visibility='collapsed')
except:
    pass


if col111.button('Carregar dados'):
    if not anos_select or not sigla_estado:
        st.warning('Preencha todos os campos obrigatórios (Ano e Sigla do Estado)')
    else:
        with st.spinner('Carregando dados!'):
            try:
                dfs = []
                anos_select = sorted(anos_select)
                for ano in anos_select:
                    df = load_data(ano, sigla_estado, bairro=bairro_input, municipio=municipio_input, candidato=candidato_input, partido=partido_input)
                    dfs.append(df)
                    
                filename = generate_filename(anos_select, sigla_estado, bairro=bairro_input, municipio=municipio_input, candidato=candidato_input, partido=partido_input)
                new_df = pl.concat(dfs)
                
                
                st.dataframe(new_df, hide_index=True, use_container_width=True)

                # votes_sum = new_df['Votos'].sum()
                votes_sum = new_df.select(pl.sum('Votos')).item()
                col222.success(f'A quantidade total de votos foi: {votes_sum:,}'.replace(',', '.'))
                with st.spinner('Carregando botão para Download'):
                    buffer = generate_excel(new_df)
                    st.download_button(
                        label='Baixar os dados como Excel',
                        data=buffer,
                        file_name=filename,
                        mime='application/vnd.ms-excel'
                        )
                
        
            except Exception as e:
                st.error(f'Error ao carregar os dados. {e}')

      
        

        

        
        

    
